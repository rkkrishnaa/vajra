#!/bin/bash
rm -rf /opt/cdh_autoscaling
rm -rf /var/spool/cron/root
git clone https://username:password@bitbucket.org/accountname/repo.git /opt/cdh_autoscaling
chmod +x /opt/cdh_autoscaling
/bin/touch /var/spool/cron/root

(crontab -l && echo "*/10 * * * * /bin/python /opt/cdh_autoscaling/cdh_autoscaling_scalein.py") | crontab -
(crontab -l && echo "*/1 * * * * /bin/python /opt/cdh_autoscaling/check_memory.py") | crontab -
(crontab -l && echo "*/5 * * * * /bin/bash /opt/cdh_autoscaling/kill_jupyterhub_process.sh") | crontab -
(crontab -l && echo "0 * * * * sync; echo 1 > /proc/sys/vm/drop_caches") | crontab -

/etc/init.d/cloudera-scm-agent stop
rm -rf /var/lib/cloudera-scm-agent/uuid
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/hostname)
echo $HOSTNAME >> /var/lib/cloudera-scm-agent/uuid	
hostname $HOSTNAME

/sbin/service supervisord restart

scm_admin_user='username'
scm_admin_pass='password'
scm_protocol='https'
scm_host='clouderamanager.organization.com'
scm_port='7180'
scm_api='v16'
cluster_name='cluster001'
scm_role='gn'

/etc/init.d/cloudera-scm-agent start
sleep 60
#add hosts to the cluster
curl -X POST \
	-u "$scm_admin_user:$scm_admin_pass" \
	-i -H "content-type:application/json" \
	-d '{"items": [{"hostId" : "'$HOSTNAME'"}]}' \
	$scm_protocol://$scm_host:$scm_port/api/$scm_api/clusters/$cluster_name/hosts

sleep 600
#apply host template
curl -X POST \
	-u "$scm_admin_user:$scm_admin_pass" \
	-i -H "content-type:application/json" \
	-d '{"items": [{"hostId" : "'$HOSTNAME'"}]}' \
	$scm_protocol://$scm_host:$scm_port/api/$scm_api/clusters/$cluster_name/hostTemplates/$scm_role/commands/applyHostTemplate

sleep 10
#start roles on host
curl -X POST \
	-u "$scm_admin_user:$scm_admin_pass" \
	-i -H "content-type:application/json" \
	-d '{"items" : ["'$HOSTNAME'"]}' \
	$scm_protocol://$scm_host:$scm_port/api/$scm_api/cm/commands/hostsStartRoles

sleep 60
#refresh cluster configuration
curl -X POST \
	-u "$scm_admin_user:$scm_admin_pass" \
	-i -H "content-type:application/json" \
	$scm_protocol://$scm_host:$scm_port/api/$scm_api/clusters/$cluster_name/commands/refresh

sleep 60
#deploy client configuration
curl -X POST \
	-u "$scm_admin_user:$scm_admin_pass" \
	-i -H "content-type:application/json" \
	$scm_protocol://$scm_host:$scm_port/api/$scm_api/clusters/$cluster_name/commands/deployClientConfig

export PATH=/usr/local/anaconda/python3/bin:/usr/local/sbin:/sbin:/bin:/usr/sbin:/usr/bin:/root/bin
nohup jupyterhub --no-ssl --debug --log-level=0 --log-file=/var/log/jupyterhub/jupyter.log --db=/etc/jupyterhub/jupyterhub.sqlite --config=/etc/jupyterhub/jupyterhub_config.py &
