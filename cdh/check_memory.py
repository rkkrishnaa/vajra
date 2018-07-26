#!/usr/bin/python
import psutil
import requests
import json
import os
import boto3

get_memory = psutil.virtual_memory()
free_memory = get_memory.free/(1024*1024*1024)
print "Free Memory: ", free_memory, "GB"

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

namespace = 'Edgenode Metrics'
Dimension = 'Organization'


cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
MetricData=[
{
        'MetricName': 'Free Memory',
        'Dimensions': [
                        {
                                        'Name': 'Dimension',
                                        'Value': Dimension
                                },
                        ],
                        'Unit': 'Gigabytes',
                        'Value': free_memory
                },
                ],
                Namespace=namespace
		)
