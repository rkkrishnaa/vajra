#!/usr/bin/python
import psutil
import requests
import json
import subprocess
import os
import xmlrpclib
import socket
import boto3
import httplib2
import subprocess
import time
from requests.auth import HTTPBasicAuth
from flask import Flask
from flask import request
from flask import jsonify

host='0.0.0.0'
port=50001
debug=False
supervisor_host='localhost'
supervisor_rpc_port='9001'
disks = [ '/mnt/home', '/usr/local/anaconda', '/r-library' ]
memory_threshold = 6

app = Flask(__name__)

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

#blue-green deployment
target_group_arn='arn:aws:elasticloadbalancing:region:accountnumber:targetgroup/jupyterhub/3c3f72e70a783c7d'
target='instance-id'

def register_targets(target_group_arn,target):    
    client = boto3.client('elbv2')
    response = client.register_targets(
    TargetGroupArn=target_group_arn,
    Targets=[
        {
            'Id': target,
        },
    ],
    )
    return(response)

def deregister_targets(target_group_arn,target):    
    client = boto3.client('elbv2')
    response = client.deregister_targets(
    TargetGroupArn=target_group_arn,
    Targets=[
        {
            'Id': target,
        },
    ],
    )
    return(response)

#health check
@app.route('/api/help', methods = ['GET'])
def help():
    """Print available functions."""
    func_list = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = app.view_functions[rule.endpoint].__doc__
    return jsonify(func_list)

@app.route('/check-memory')
def check_memory():
	get_memory = psutil.virtual_memory()
	free_memory = get_memory.free/(1024*1024*1024)
  	print free_memory	
	if free_memory > memory_threshold:
		return str(free_memory), 200 
	else:
		return str(free_memory), 500

def getmount(path):
	path = os.path.abspath(path)
	while path != os.path.sep:
		if os.path.ismount(path):
			return path
		path = os.path.abspath(os.path.join(path, os.pardir))
	return path

@app.route('/check-disk')
def check_disk():
	count = 0
	for i in range(len(disks)):
		if getmount(disks[i]) == disks[i]:
			count = count + 1
	if str(count) == str(len(disks)):
		return str(count), 200
	else:
		return str(count), 500

#jupyter
@app.route('/check-jupyter')
def check_jupyter():
	api_url='http://localhost:8000/hub/api'
	req = requests.get(api_url)
	res_code=str(req.status_code)
	return res_code

@app.route('/elb-check-jupyter')
def elb_check_jupyter():
	mem = check_memory()
	disk = check_disk()
	jupyter = check_jupyter()
	print str(disk[1])
	if str(mem[1]) == '200' and str(disk[1]) == '200' and jupyter == '200':
                response=register_targets(target_group_arn,target)
                print "status is not 500"
                print response 
	 	return "service is in healthy state", 200
	else:   
                response=deregister_targets(target_group_arn,target)
                print "status is 500"
                print response
                subprocess.call(['service', 'supervisord', 'restart'])
                print "supervisor restarted"
		return "service is in unhealthy state", 500

#hue
@app.route('/check-hue')
def check_hue():
	addr = socket.gethostbyname(socket.gethostname())
	api_url = "https://"+addr+":8888/accounts/login/?next=/"
	req = requests.get(api_url,verify=False)
	res_code=str(req.status_code)
	print res_code
	return res_code

@app.route('/elb-check-hue')
def elb_check_hue():
	mem = check_memory()
	hue = check_hue()
	print str(mem[1])
	print hue
	if str(mem[1]) == '200' and hue == '200':
		return "service is in healthy state", 200
	else:
		return "service is in unhealthy state", 500
	
#webconsole
@app.route('/check-webconsole')
def check_webconsole():
	api_url = "http://localhost:42000"
	req = requests.get(api_url)
	res_code=str(req.status_code)
	return res_code

@app.route('/elb-check-webconsole')
def elb_check_webconsole():
	mem = check_memory()
	disk = check_disk()
	webconsole = check_webconsole()
	print str(mem[1]) + str(disk[1]) + webconsole
	if str(mem[1]) == '200' and str(disk[1]) == '200' and webconsole == '200':
		return "service is in healthy state", 200
  	else:
		return "service is in unhealthy state", 500

#r-studio
@app.route('/check-rstudio')
def check_rstudio():
	api_url = "http://localhost:8787/auth-sign-in"
	req = requests.get(api_url)
	res_code=str(req.status_code)
	return res_code

@app.route('/elb-check-rstudio')
def elb_check_rstudio():
	mem = check_memory()
	disk = check_disk()
	rstudio = check_rstudio()
	if str(mem[1]) == '200' and str(disk[1]) == '200' and rstudio == '200':
		return "service is in healthy state", 200
	else:
		return "service is in unhealthy state", 500

#ftp
@app.route('/check-ftp')
def check_ftp():
	api_url = "http://localhost"
	req = requests.get(api_url)
	res_code=str(req.status_code)
	return res_code

@app.route('/elb-check-ftp')
def elb_check_ftp():
	mem = check_memory()
	disk = check_disk()
	ftp = check_ftp()
	if str(mem[1]) == '200' and str(disk[1]) == '200' and ftp == '200':
		return "service is in healthy state", 200
	else:
		return "service is in unhealthy state", 500

@app.route('/check-nfs')
def nfssize():
    digDict = {}
    with open("tmpOut", "w") as file:
    	 subprocess.call("cd /mnt/home && du -sh *| awk '{print $2,$1}' ", shell=True, stdout=file)

    with open("tmpOut") as infile:
        for line in infile:
            digDict[line.split()[0]] = line.split()[1]
    os.remove("tmpOut")
    return (json.dumps(digDict, sort_keys=True, indent=4))

if __name__ == '__main__':
   app.run(host, port, debug)
