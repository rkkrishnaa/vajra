#!/bin/bash
rm -rf /opt/cdh_autoscaling
rm -rf /var/spool/cron/root
git clone https://github.com/rkkrishnaa/vajra.git /opt/cdh_autoscaling
chmod +x /opt/cdh_autoscaling
/bin/touch /var/spool/cron/root

(crontab -l && echo "*/10 * * * * /bin/python /opt/cdh_autoscaling/cdh/cdh_autoscaling_scalein.py") | crontab -

/etc/init.d/cloudera-scm-agent stop
rm -rf /var/lib/cloudera-scm-agent/uuid
HOSTNAME=$(curl http://169.254.169.254/latest/meta-data/hostname)
echo $HOSTNAME >> /var/lib/cloudera-scm-agent/uuid	
hostname $HOSTNAME

scm_admin_user='username'
scm_admin_pass='password'
scm_protocol='https'
scm_host='clouderamanager.organization.com'
scm_port='7180'
scm_api='v16'
cluster_name='cluster001'
scm_role='wn'

/etc/init.d/cloudera-scm-agent start
sleep 60
#add hosts to the cluster
curl -X POST \
	-u "$scm_admin_user:$scm_admin_pass" \
	-i -H "content-type:application/json" \
	-d '{"items": [{"hostId" : "'$HOSTNAME'"}]}' \
	$scm_protocol://$scm_host:$scm_port/api/$scm_api/clusters/$cluster_name/hosts

sleep 60
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

mkdir /r-library
mkdir /usr/local/anaconda
mount -t nfs efs-r.organization:/r-library /r-library
mount -t nfs efs-python.organization.com:/usr/local/anaconda /usr/local/anaconda
