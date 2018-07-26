#!/usr/bin/python
import httplib2
import os
import requests
import json
import boto3
import time
from requests.auth import HTTPBasicAuth

headers = {'content-type': 'application/json'}
req = requests.get(url='http://169.254.169.254/latest/meta-data/iam/security-credentials/ec2_full_access', headers=headers)
res = json.loads(req.text)

AccessKeyId = res['AccessKeyId']
SecretAccessKey = res['SecretAccessKey']
Token = res['Token']
Region = "ap-south-1"

os.environ["AWS_ACCESS_KEY_ID"] = AccessKeyId
os.environ["AWS_SECRET_ACCESS_KEY"] = SecretAccessKey
os.environ["AWS_SESSION_TOKEN"] = Token
os.environ["AWS_DEFAULT_REGION"] = Region

metadata = requests.get(url='http://169.254.169.254/latest/meta-data/instance-id')
instance_id = metadata.text
host = requests.get(url='http://169.254.169.254/latest/meta-data/hostname')
host_id = host.text

username='username'
password='password'
cluster_name='cluster001'
scm_protocol='https'
scm_host='clouderamanager.organization.com'
scm_port='7180'
scm_api='v16'

client = boto3.client('autoscaling')
ec2 = boto3.client('autoscaling', region_name=Region)

response = client.describe_auto_scaling_instances(InstanceIds=[instance_id,])
state =  response['AutoScalingInstances'][0]['LifecycleState']
print "vm is in " + state 
if state == 'Terminating:Wait':
	print "host decommision started"
 	##decommission host
	service_url = scm_protocol + '://' +  scm_host + ':'  +  scm_port + '/api/' + scm_api + '/cm/commands/hostsDecommission'
	
	#service_url = scm_protocol + '://' +  scm_host + ':'  +  scm_port + '/api/' + scm_api + '/cm/hostsRecommission'
	#service_url = scm_protocol + '://' +  scm_host + ':'  +  scm_port + '/api/' + scm_api + '/cm/commands/hostsStartRoles'


	print service_url
	headers = {'content-type': 'application/json'}
	req_body = { "items":[ host_id ]}
	print req_body
	req = requests.post(url=service_url, auth=HTTPBasicAuth(username, password), data=json.dumps(req_body), headers=headers)
	print req.text
	time.sleep(120)			

	##delete roles in a host
	api_url = scm_protocol + '://' + scm_host + ':' + scm_port + '/api/' + scm_api + '/hosts/' + host_id
	req = requests.get(api_url, auth=HTTPBasicAuth(username, password))
	a = json.loads(req.content)
	
	for i in a['roleRefs']:
		scm_uri='/api/' + scm_api + '/clusters/' + cluster_name + '/services/'+i['serviceName']+'/roles/'+i['roleName']
		scm_url = scm_protocol + '://' +  scm_host + ':'  +  scm_port + scm_uri
		print scm_url
		req = requests.delete(scm_url, auth=HTTPBasicAuth(username, password))
		print req.text
		time.sleep(10)
	
	##remove host from cluster
	service_url = scm_protocol + '://' +  scm_host + ':'  +  scm_port + '/api/' + scm_api + '/clusters/' + cluster_name + '/hosts/' + host_id
	print service_url
	req = requests.delete(service_url, auth=HTTPBasicAuth(username, password))
	time.sleep(10)
	
	##remove host from cloudera manager
	os.system("/etc/init.d/cloudera-scm-agent stop")	
	service_url = scm_protocol + '://' +  scm_host + ':'  +  scm_port + '/api/' + scm_api + '/hosts/' + host_id
	print service_url
	req = requests.delete(service_url, auth=HTTPBasicAuth(username, password))
	print req.text
	time.sleep(10)

	##refresh cluster configuration
	service_url = scm_protocol + '://' +  scm_host + ':'  +  scm_port + '/api/' + scm_api + '/clusters/' + 'commands/refresh'
	print service_url
	req = requests.post(service_url, auth=HTTPBasicAuth(username, password))
	print req.text
	time.sleep(10)

	##deploy client configuration
	service_url = scm_protocol + '://' +  scm_host + ':'  +  scm_port + '/api/' + scm_api + '/clusters/' + 'commands/deployClientConfig'
	print service_url
	req = requests.post(service_url, auth=HTTPBasicAuth(username, password))
	print req.text
	time.sleep(10)
	
	#stop vm before termination
	client = boto3.client('ec2')
	client.stop_instances(InstanceIds=[instance_id,])
