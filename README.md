[![Generic badge](https://img.shields.io/badge/Version-1.0-<COLOR>.svg)](https://shields.io/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
![Maintainer](https://img.shields.io/badge/maintainer-raphael.chir@gmail.com-blue)

# Transactions ST

1. [Transactions ST](#transactions-st)
   - [Use case](#use-case)
   - [Architecture](#architecture)
   - [Setup](#setup)
     - [Kafka usage tests](#kafka-usage-tests)
     - [Grafana tests](#grafana-tests)
   - [SingleStoreDB Cloud](#singlestoredb-cloud)
     - [Create an environment](#create-an-environment)
     - [Quick test integration](#quick-test-integration)
2. [Realtime Store transactions analysis](#realtime-store-transactions-analysis)
   - [The pain](#the-pain)
   - [See the pain in action](#scenario-1---see-the-pain-in-action)
     - [Create a dedicated topic on Kafka](#create-a-dedicated-topic-on-kafka)
     - [Ingest data to SingleStore](#ingest-data-to-singlestore)
     - [Query your data](#query-your-data)
   - [Realtime Analysis](#realtime-analysis)
     - [Grafana](#grafana)
     - [Test #1](#test-1)
     - [Test #2](#test-2)

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
Create a topic on the broker with 
```
kafka-topics.sh --create --topic test --bootstrap-server <Your EC2_DNS Instance>:9092 --partitions 1 --replica
tion-factor 1
```
or
```
kcat -b ec2-15-237-193-135.eu-west-3.compute.amazonaws.com:9092 -t test-topic -P
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

### SingleStoreDB Cloud
#### Create an environment
Go to https://www.singlestore.com/  
Click on start free link, create an account and follow instructions.
You will benefit from a shared tiers offer containing a starter-workspace containing one database. It can be usefull to test the different shared note books. Take time to discover the UI.

To access to more features we will create a demo-workspace, and we will benefits from a set of credits offered by ST. Great. We start here now.

#### Quick test integration

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

Here is a permanent message production example that can be used in your local terminal : 
```
while true; do date | kcat -P -b <Your EC2_DNS Instance>:9092 -t test; sleep 1; done
```
You will see your message in your Single Store table. In Grafana, note that we can use our previously Datasource Connector to begin to build a dashboard.
Let's start by a very simple table panel to display all the data of a specific table, here the table messages is a good example to test the raw table data vizualisation.

# Realtime Store transactions analysis.

## The pain
I have built a grafana real-time analysis dashboard. Everything is going well until I reach out to a significant number of transaction, because : 
- My refresh rate on Grafana is lower than the analytic SQL requests time execution and the dash is stucked !
- Transaction insertions become slower

## See the pain in action

### Create a dedicated topic on Kafka
Create a topic on the broker with 
```
kafka-topics.sh --create --topic retails --bootstrap-server <Your EC2_DNS Instance>:9092 --partitions 1 --replica
tion-factor 1
```

### Ingest data to SingleStore 
We start with a simple table, without any specific optimisations regarding indexation and data distribution on Singlestore nodes
```sql
CREATE DATABASE IF NOT EXISTS demo_retails;
USE demo_retails;
```
```sql
CREATE TABLE product_transactions (
    transaction_id INT NOT NULL,
    store_id INT NOT NULL,
    city VARCHAR(50) NOT NULL,  
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    product_name VARCHAR(50) NOT NULL, 
    brand VARCHAR(50),
    transaction_date DATETIME NOT NULL,
    quantity INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    customer_id int(11) NOT NULL,
    payment_type varchar(50) NOT NULL,
    PRIMARY KEY (transaction_id)
);
```
We create a pipeline, that ingest json data from a kafka topic. No mapping needed with the JSON message (see https://docs.singlestore.com/cloud/reference/sql-reference/pipelines-commands/create-pipeline/)

```sql
CREATE PIPELINE retails_kafka_consumer AS LOAD DATA KAFKA '<Your EC2_DNS Instance>:9092/retails' SKIP DUPLICATE KEY ERRORS INTO TABLE product_transactions FORMAT JSON;
```
Now we produce transaction messages into the kafka broker with a Python script :

```python
from confluent_kafka import Producer
import json
import random
import time
import signal
import sys

# Kafka configuration
conf = {
    'bootstrap.servers': '<Your EC2_DNS Instance>:9092',
    'batch.num.messages': 1000,
    'queue.buffering.max.messages': 100000,
    'linger.ms': 10
}

producer = Producer(conf)
topic = "retails"

# Errors handler
def acked(err, msg):
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# French town referential
stores = [
    {"store_id": 1, "city": "Paris", "latitude": 48.8566, "longitude": 2.3522},
    {"store_id": 2, "city": "Lyon", "latitude": 45.7640, "longitude": 4.8357},
    {"store_id": 3, "city": "Marseille", "latitude": 43.2965, "longitude": 5.3698},
    {"store_id": 4, "city": "Toulouse", "latitude": 43.6047, "longitude": 1.4442},
    {"store_id": 5, "city": "Rennes", "latitude": 48.1147, "longitude": -1.6791},
    {"store_id": 6, "city": "Lille", "latitude": 50.6292, "longitude": 3.0573},
    {"store_id": 7, "city": "Strasbourg", "latitude": 48.5734, "longitude": 7.7521}
]

# Brand and product reference
products = [
    {"product_name": "Laptop", "brand": "TechCorp"},
    {"product_name": "Smartphone", "brand": "PhoneMaster"},
    {"product_name": "Headphones", "brand": "SoundMax"},
    {"product_name": "Tablet", "brand": "TabWorld"},
    {"product_name": "Camera", "brand": "PicPerfect"}
]

# Message producer
def produce_messages(batch_size=10, pause=1):
    while True:
        batch = []  # Messages tab for batch insertion
        
        # Fill the batch tab
        for _ in range(batch_size):
            store = random.choice(stores)
            product = random.choice(products)

            message = {
                "transaction_id": random.randint(1, 1000000),
                "store_id": store["store_id"],
                "city": store["city"],
                "latitude": store["latitude"],
                "longitude": store["longitude"],
                "product_name": product["product_name"],
                "brand": product["brand"],
                "transaction_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "quantity": random.randint(1, 5),
                "total_amount": round(random.uniform(5.0, 500.0), 2),
                "customer_id": random.randint(1, 5000),
                "payment_type": random.choice(["CASH", "CARD"])
            }

            batch.append(message)

        # Send batch messages to the producer
        for message in batch:
            producer.produce(topic, key=str(message["transaction_id"]), value=json.dumps(message), callback=acked)

        producer.flush() 

        print(f"{batch_size} sent messages.")
        time.sleep(pause)  # Pause between batch

# Ctrl + C Signal handler
def signal_handler(sig, frame):
    print('Kafka production message stopping ...')
    producer.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Execution the production
print("Start sending batch messages. Press Ctrl + C to stop.")
produce_messages(batch_size=10000, pause=0.25)

```
This setting produces messages at a brisk rate, but configuring batch.num.messages and linger.ms could result in more frequent sending with smaller batches (up to 1000 messages at a time), which could affect throughput if all 10,000 messages are not transmitted in one batch. To improve this, you might consider increasing the value of batch.num.messages to be in line with batch_size, if your broker can support such a load :

Init your python environement
```
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

Start the script
```
python3 tx-producer.py
```
CTL+C to stop the production

### Query your data
Get the revenue earned the last 60s per city (1 store per city)
```sql
SELECT 
    city,
    SUM(total_amount) AS total_revenue
FROM 
    product_transactions
WHERE 
    transaction_date > CONVERT_TZ(NOW(), 'UTC', 'Europe/Paris') - INTERVAL 60 SECOND
GROUP BY 
    city
ORDER BY total_revenue desc;
```
Get the number of transactions per stores aggregates per city.
```sql
SELECT
  city,
  latitude,
  longitude,
  COUNT(*) AS transaction_count
FROM product_transactions
GROUP BY city, latitude, longitude
ORDER BY transaction_count DESC
```
Execute each request on the query editor of Single Store and perform a Vizualisation Explain. As there is not a lot of data, no significant impact are identified.

## Realtime Analysis
### Grafana
We can use our previously Datasource Connector to begin to build a dashboard. 
Import the dashboard provided. And start your script.
A gauge indicate the number of transactions, setup the refresh rate to 250 ms, and observe the pain, then setup 500ms.
It is time to optimize our queries !

### Test #1
### Test #2
