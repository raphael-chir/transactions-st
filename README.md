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
## Kafka Broker
### Launch an EC2 Instances
Go to kafka-setup folder where Terraform modules are ready to be used to launch an EC2 with Ubuntu OS, docker and docker-compose.
### Install docker and docker-compose
### Install Kafka
### External Test with kcat
## SingleStoreDB Cloud
### Create a table
### Create a pipeline
### Query your data
## Realtime Analysis
### Grafana
### Test #1
### Test #2
