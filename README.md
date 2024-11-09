[![Generic badge](https://img.shields.io/badge/Version-1.0-<COLOR>.svg)](https://shields.io/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
![Maintainer](https://img.shields.io/badge/maintainer-raphael.chir@gmail.com-blue)

# Transactions ST
## Use case
- Ingest transactions from Kafka to SingleStore Helios
- Perform real-time analysis with SingleStore queries
- Visualize the results in Grafana
## Architecture
We use terraform to setup an ec2 instance reachable from internet.  
This instance contains a Kafka broker with Zookeeper and Grafana  
All is described in a docker-compose.yml to facilitate this demo : 
```yml
version: '3'
services:
  zookeeper:
    image: bitnami/zookeeper:latest
    environment:
      - ZOO_MY_ID=1
      - ZOO_PORT=2181
      - ZOO_SERVERS=0.0.0.0:2888:3888
      - ALLOW_ANONYMOUS_LOGIN=yes
    ports:
      - "2181:2181"

  kafka:
    image: bitnami/kafka:latest
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://${EC2_DNS}:9092
      - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT
      - ALLOW_PLAINTEXT_LISTENER=yes
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
```
The objective is now to integrate SingleStore Cloud to a Kafka topic and connect Grafana to SingleStore.  
Note that we use an environment variable to set your dns instance to Kafka, so that you can produce and consume messages externally from this ec2 instance.
## Setup
Go to kafka-setup folder where Terraform modules are ready to be used to launch an EC2. This will provision an instance with ubuntu.
Then init.sh will be execute to : 
- Install docker, docker-compose, 
- Clone the git repository 
- Launch the container
You need to wait few minutes for the environment to be ready. 

### Kafka usage tests
Install in your local environment kcat tool to produce and or consume messages from a topic.
But at this point we only test that kafka is reachable.
```
kcat -b <Your EC2_DNS Instance>:9092 -L
```
Test if you can reach out to test topics to consume a message (no messages for now)
```
kcat -C -b <Your EC2_DNS Instance>:9092 -t test
```
You can use this command to produce message on topic test, that will be covered later
```
echo "msg0"| kcat -P -b <Your EC2_DNS Instance>:9092 -t test
```
### Grafana tests

- Go to http://\<Your EC2_DNS Instance>:3000 to test Grafana setup
- Go to SingleStore Cloud/home and click on Connect to database to get the connection String. Warn : Select your workspace and database. (Note that for the purpose of the demo we will not manage security aspects to be concentrated on the use case - However this can be done easily in a next step). Use the parameters connexion provided :  
  - Host: \<Your SingleStore Cloud Host>
  - Port: 3306
  - Username: admin 
  - Password: \<your password>   
  - Database: demo
- Create a Datasource connexion in Grafana, using mysql connectors and fill the previous information. Let TLS/SSL options deactivated and Tests and save your datasource, it should be successful.

Nota : To get a near realtime dashboard (from the 5s default grafana to 250 ms)
```
docker exec -u 0 -it transactions-st-grafana-1 /bin/bash
```
Modify min_refresh_interval in conf/defaults.ini
```
#################################### Dashboards ##################

[dashboards]                                                                   
# Number dashboard versions to keep (per dashboard). Default: 20, Minimum: 1
versions_to_keep = 20
                                        
# Minimum dashboard refresh interval. When set, this will restrict users to set the refresh interval of a dashboard lower than given interval. Per default this is 5 seconds.
# The interval string is a possibly signed sequence of decimal numbers, followed by a unit suffix (ms, s, m, h, d), e.g. 30s or 1m.
min_refresh_interval = 250ms                                          
                      
# Path to the default home dashboard. If this value is empty, then Grafana uses StaticRootPath + "dashboards/home.json"
default_home_dashboard_path =     
```       
So now environment is ready to be used, and we will concentrate us on SingleStore Cloud

## SingleStoreDB Cloud
### Create an environment
Go to https://www.singlestore.com/  
Click on start free link, create an account and follow instructions.
You will benefit from a shared tiers offer containing a starter-workspace containing one database. It can be usefull to test the different shared note books. Take time to discover the UI.

To access to more features we will create a demo-workspace, and we will benefits from a set of credits offered by ST. Great. We start here now.

### Create a database, table and pipeline

Create a database from UI (Deployments link)
- Select your Workspace
- Click on Create Database (on the right above Databases blocks)
- On the left inside Workspace block, select connect and SQL Editor

Create tables
```sql
CREATE TABLE messages (id text);
```

Create a pipeline, follow the step to test integration :
This will integrate the pipeline definition with your kafka instances. At this point we just expect that the pipeline can read kafka topic metadata and it is ready to consume messages
```sql
CREATE PIPELINE kafka_msg_consumer AS LOAD DATA KAFKA '<Your EC2_DNS Instance>/test' INTO TABLE messages;
```
Send a message to your kafka instance with kcat : 
```
echo "msg0"| kcat -P -b <Your EC2_DNS Instance>:9092 -t test
```
Test that this message is read by the pipeline, but not ingested at this point
```
TEST PIPELINE kafka_msg_consumer LIMIT 1;
```
Here is an example of starting and directly stop a consumptions
```
START PIPELINE kafka_msg_consumer FOREGROUND LIMIT 1 BATCHES;
```
You can start your pipeline to permanently listen to the topic
```
START PIPELINE kafka_msg_consumer;
```
You will see that the pipeline remains in running status.

### Query your data
## Realtime Analysis
### Grafana
We can use our previously Datasource Connector to begin to build a dashboard.
Let's start by a very simple table panel to display all the data of a specific table, here the table messages is a good example to test the raw table data vizualisation.
### Test #1
### Test #2
