Vajra - Scale your hadoop cluster based on top of aws infrastructure in less than 5minutes
------------------------------------------------------------------------------------------

![vajra](vajra-hadoop.png?raw=true)

* Vajra(diamond) is a powerful weapon which symbolizes indestructibility and a thunderbolt. Here vajra is a tool which is written in python which helps to scale your hadoop cluster based on demand.
* CDH is Cloudera's 100% open source platform distribution, including Apache Hadoop and built specifically to meet enterprise demands. Cloudera manager is a cluster management tool for managing CDH cluster. It provides an end to end solution from provisioing, configuring, managing and monitoring cluster nodes.

Why Vajra?
----------
![vajra](vajra-aws.png?raw=true)

* We can create infrastructure using provisioning tools in cloud and provision cluster using cloudera manager using its web interface or api easily. But no framework adresses the scalabilty of cluster nodes. Recently, Cloudera director addressed the scalability problem in CDH cluster. But it is bit difficult to use in some aspects. We have to maintain consistency between clouera manager and cloudera director. 
* Cloud vendors like AWS offers hadoop service as Elastic Map Reduce(EMR), Microsoft Azure offers HD Insight to offer hadoop service and Openstack has launched a project called Sahara - Dataprocessing as a service to address hadoop use cases.
* Here I have documented the steps to create a hadoop cluster on top of aws and configure autoscaling of worker nodes and edge nodes based on demand.
* I have included some scripts to cleanup you hadoop cluster on hourly basis or upto your choice. A single user can spoil the entire hadoop cluster if the hadoop cluster is misconfigured or any previleged user executes a long running mapreduce or spark jobs.

Hardware and Software Requirements:
-----------------------------------
1. AWS account with sufficient quota to launch ec2 instances and other resources
2. Provision your cluster resources based on your architecture pattern. 
3. Install the packages and manage its configuration thrugh cloudera manager.
4. Create two host templates in cloudera manager say wn(worker nodes) and gn(gateway or edge nodes) with necessary roles. Which will be used by autoscaling group while creating vm.
5. Host template worker node should have roles such as node manager and data node and spark gateway configuration if you use spark on YARN cluster. Host template gateway node should have roles such as hue and configuration of all hadoop components such as hdfs, mapreduce, spark, hive, impala and spark.
6. Create a repo in code commit or github and keep the code.
7. Prepare a golden image for your gateway and worker nodes.
8. Create launch configuration/ launch template from the above golden image and configure other things related to your deployment. use the contents of cdh_autoscaling_scaleout_gn.sh and cdh_autoscaling_scaleout_gn.sh as user data for gateway node and worker node respectively.
9. Create autoscaling group for on demand instances and spot instances for worker node autoscaling. Worker node can withstand ec2 instan ce failure, Jobs will be rescheduled to a healthy host in the cluster. We can decommission the roles and migrate the required data before the termination of nodes.
10. Create a lambda function and deploy the cleanup script and autoscaling script.
11. Create a cloudwatch event to invoke the lambda function to perform cluster health check.
12. Configure cloudwatch alarm to perfrom scale in and scale out of your cluster nodes.

How Vajra works?
----------------
* Vajra uses cloudera manager REST API and AWS autoscaling to provision edge node and worker node dynamically. YARN Cluster exposes REST API to track the metrics like total memory, available memory, total core, available core, number of mapreduce/spark jobs running, number of jobs in pending, resources consumed by an individual job. Our lambda function contains the steps to compute the available memory, available core and number of running and pending jobs. It will update the metrics to cloudwatach with interval of every 1minute. Lambda function is invoked by cloudwatch event.
* We can access the metrics from lambda function through api gateway.
* We have alarm to create threshhold to perform scale in and scale out of ec2 instances based on the above metrics and we can define the limits of maximum instances in an autoscaling group.
* Userdata plays a major role in injecting the script while launching instances from autoscaling. This script contains the steps to install packages and registering as a node in cdh cluster. Once it is successfully registered as a host, we can apply host templates to assign a required roles on the host.
* We can refresh the cluster configuration without restarting any existing roles throgh API and deploy the latest client configuration against the nodes.
* Autoscaling instances has life cycle which helps us to perform some actity against the instance before launching and before termination of instances. Scalein script will be executed every minute to check the lifecycle status of the host. Whenever autoscaling updates the group to perform scalein activity, life cycle status of an ec2 instance will be changed. During that time, we will decommission the hosts and move the copy of the data to s3 or any shared storage. 
* We stop the roles and delete the host from the cluster. Later we do configuration refresh to remove the stale configs. 
* Finally, we will stop the instance programmatically and it will be terminated by autoscaling group after the lifecycle state of the instance changed from termination:Wait to termination:Proceed.
* While scaling edge node, we push the system memory to cloudwatch for autoscaling.
* Worker nodes are resilent to termination of nodes, so we can add it to autoscaling group of spot instances which leverages the lifecycle hook of autoscaling.

Future Work:
------------
* It is bit difficult to use spot fleet for edge nodes, Since edge node is the point of contact of end users to run hadoop jobs. Spot instances does not provide gaurentee for running instances. So end users will be impacted if they run a long running spark jobs and application load balancer takes more time to drain the connection. To address the above case, I am creating a lambda function which emulates edge node. It can be accessed thru a light weight web client integrated with api gateway. So that we do not need to run a dedicated edge node to access linux terminal. 

Please let me know if you have any queries:

email: radhakrishnancloud@gmail.com
