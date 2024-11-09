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

-> Go to http://\<Your EC2_DNS Instance>:3000 to test Grafana setup

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
So now environment is ready to be used, and we will concentrate us on SingleStore Cloud  

## SingleStoreDB Cloud
### Create a table
### Create a pipeline
### Query your data
## Realtime Analysis
### Grafana
### Test #1
### Test #2
