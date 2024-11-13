[![Generic badge](https://img.shields.io/badge/Version-1.0-<COLOR>.svg)](https://shields.io/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
![Maintainer](https://img.shields.io/badge/maintainer-raphael.chir@gmail.com-blue)

# Table of Contents

- [Transactions ST](#transactions-st)
  - [Use case](#use-case)
  - [Architecture](#architecture)
  - [Setup](#setup)
    - [Kafka usage tests](#kafka-usage-tests)
    - [SingleStoreDB Cloud](#singlestoredb-cloud)
      - [Create an environment](#create-an-environment)
    - [Grafana tests](#grafana-tests)
      - [Quick test integration (can be skipped)](#quick-test-integration-can-be-skipped)
  - [Realtime Store transactions analysis](#realtime-store-transactions-analysis)
    - [The pain](#the-pain)
    - [See the pain in action](#see-the-pain-in-action)
      - [Create a dedicated topic on Kafka](#create-a-dedicated-topic-on-kafka)
      - [Ingest data to SingleStore](#ingest-data-to-singlestore)
      - [Query your data](#query-your-data)
        - [Count the number of donation for the current campaign](#1---count-the-number-of-donation-for-the-current-campaign)
        - [Get total amount of donations for the current campaign](#2---get-total-amount-of-donations-for-the-current-campaign)
        - [Get Best city, organisation donation](#3---get-best-city-organisation-donation)
        - [Amount of donations per geo loc city](#4---amount-of-donations-per-geo-loc-city)
        - [Total amount of donations per organization](#5---total-amount-of-donations-per-organization)
        - [Last 35s of total amount of donations per city](#6---last-35s-of-total-amount-of-donations-per-city)
        - [Last 28s of total amount of donations per organization](#7---last-28s-of-total-amount-of-donations-per-organization)
    - [Realtime Analysis](#realtime-analysis)
      - [Grafana](#grafana)
      - [SingleStore](#singlestore)
      - [Optimization](#optimization)
      - [Demo](#demo)

# Transactions ST
![Dash](donations_dash.gif "Donations")

## Use case
This project is about the management of N campaigns to collect donation for 4 aids associations in 4 selected towns in France choosen among a list of 20 cities. Each campaign has a start time and a end time. The results is that we fill the database with millions of data.

Technically :
- Ingest transactions from Kafka to SingleStore Helios
- Perform real-time analysis with SingleStore queries
- Visualize the results in Grafana

The aim of this demo is to optimized queries latencies with the usage of an adapted SHARD KEY AND SORT KEY, depending of which kind of analyze are the most relevant.

## Architecture
We use terraform to setup an ec2 instance reachable from internet.  
This instance contains a Kafka broker with Zookeeper and Grafana
Note that I didn't use Confluent stack that is too loud for this use case.  
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
      - KAFKA_CREATE_TOPICS= "donations"
      - KAFKA_LOG_RETENTION_MS=300000
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    dns:
      - 8.8.8.8
```
The objective is now to integrate SingleStore Cloud to a Kafka topic and connect Grafana to SingleStore.  
Note that we use an environment variable to set your dns instance to Kafka, so that you can produce and consume messages externally from this ec2 instance.
## Setup
Go to kafka-setup folder in your IDE where Terraform modules are ready to be used to launch an EC2. This will provision an instance with ubuntu.
Then kafka-setup/scripts/init.sh will be execute to : 
- Install docker, docker-compose, 
- Clone the git repository 
- Launch the container
You need to wait few minutes for the environment to be ready. 

### Kafka usage tests
Install in your local environment kcat tool (See https://github.com/edenhill/kcat) to produce and or consume messages from a topic.
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
kcat -b <Your EC2_DNS Instance>:9092 -t test-topic -P
```
Test if you can reach out to test topics to consume a message (no messages for now)
```
kcat -C -b <Your EC2_DNS Instance>:9092 -t test
```
You can use this command to produce message on topic test, that will be covered later
```
echo "msg0"| kcat -P -b <Your EC2_DNS Instance>:9092 -t test
```

### SingleStoreDB Cloud
#### Create an environment
Go to https://www.singlestore.com/  
Click on start free link, create an account and follow instructions.
You will benefit from a shared tiers offer containing a starter-workspace containing one database. It can be usefull to test the different shared note books. Take time to discover the UI.

To access to more features we will create a demo-workspace, and we will benefits from a set of credits offered by ST. Great. We start here now.

### Grafana tests

- Go to http://\<Your EC2_DNS Instance>:3000 to test Grafana setup
- Go to your SingleStore Cloud account (Cloud/home) and click on Connect to database to get the connection String. Warn : Select your workspace and database. (Note that for the purpose of the demo we will not manage security aspects to be concentrated on the use case - However this can be done easily in a next step). Use the parameters connexion provided :  
  - Host: \<Your SingleStore Cloud Host>
  - Port: 3306
  - Username: admin 
  - Password: \<your password>   
  - Database: demo
- Create a Datasource connexion in Grafana, using mysql connectors and fill the previous information. Let TLS/SSL options deactivated and Tests and save your datasource, it should be successful.

Nota : To get a near realtime dashboard (from the 5s default grafana to 250 ms) :
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

#### Quick test integration (can be skipped)

Create a database from SingleStore Cloud UI (Deployments link)
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
I have built a grafana real-time analysis dashboard. Everything will go well until I will reach out to a significant number of transactions, because : 
- My refresh rate on Grafana will be slower than the analytic SQL requests time execution and the dash is stucked !
- Transaction insertions become more and more slower

## See the pain in action

### Create a dedicated topic on Kafka
Create a topic on the broker with 
```
kafka-topics.sh --create --topic donations --bootstrap-server <Your EC2_DNS Instance>:9092 --partitions 1 --replica
tion-factor 1
```

### Ingest data to SingleStore 
We start with a simple table, without any specific optimisations regarding indexation and data distribution on Singlestore nodes
```sql
CREATE DATABASE IF NOT EXISTS donations;
USE donations;
```
```sql
CREATE TABLE donation_transactions (
    transaction_id INT NOT NULL,
    city VARCHAR(50) NOT NULL,
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    organization VARCHAR(50),
    transaction_date DATETIME NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    campaign_id INT NOT NULL,
    is_campaign_active tinyint(1) DEFAULT 0,
    PRIMARY KEY (transaction_id)
);
```
We create a pipeline, that ingest json data from a kafka topic. No mapping is needed with the JSON message (see https://docs.singlestore.com/cloud/reference/sql-reference/pipelines-commands/create-pipeline/) as we map all fields to the related columns.

```sql
CREATE PIPELINE donations_kafka_consumer AS LOAD DATA KAFKA '<Your EC2_DNS Instance>:9092/retails' SKIP DUPLICATE KEY ERRORS INTO TABLE donation_transactions FORMAT JSON;
```
Now we produce transaction messages into the kafka broker with a Python script :

```python
mport mysql.connector
from confluent_kafka import Producer
import json
import random
import time
import signal
import sys

# Kafka configuration
conf = {
    'bootstrap.servers': 'ec2-15-237-193-135.eu-west-3.compute.amazonaws.com:9092',
    'batch.num.messages': 1000,
    'queue.buffering.max.messages': 100000,
    'linger.ms': 10
}

producer = Producer(conf)
topic = "donations"

# SingleStore connection configuration
singlestore_conf = {
    'user': 'admin',
    'password': 'Password!',
    'host': 'svc-9d1b91c8-6b61-45a8-bce6-2961fb731bd0-dml.aws-virginia-6.svc.singlestore.com',
    'database': 'donations'
}

# Set all previous campaigns as inactive
def deactivate_previous_campaigns():
    connection = mysql.connector.connect(**singlestore_conf)
    cursor = connection.cursor()
    cursor.execute("UPDATE donation_transactions SET is_campaign_active = 0")
    connection.commit()
    cursor.close()
    connection.close()

# Errors handler
def acked(err, msg):
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# Sample cities list
cities = [
    {"city": "Amiens", "latitude": 49.8941, "longitude": 2.3022},
    {"city": "Moulins", "latitude": 46.5644, "longitude": 3.3347},
    {"city": "Béziers", "latitude": 43.3442, "longitude": 3.2150},
    {"city": "Brest", "latitude": 48.3904, "longitude": -4.4861},
    {"city": "Angers", "latitude": 47.4784, "longitude": -0.5632},
    {"city": "Caen", "latitude": 49.1829, "longitude": -0.3707},
    {"city": "Perpignan", "latitude": 42.6887, "longitude": 2.8948},
    {"city": "Nîmes", "latitude": 43.8367, "longitude": 4.3601},
    {"city": "La Rochelle", "latitude": 46.1603, "longitude": -1.1511},
    {"city": "Bayonne", "latitude": 43.4929, "longitude": -1.4748},
    {"city": "Rouen", "latitude": 49.4432, "longitude": 1.0993},
    {"city": "Pau", "latitude": 43.2951, "longitude": -0.3708},
    {"city": "Versailles", "latitude": 48.8014, "longitude": 2.1301},
    {"city": "Orléans", "latitude": 47.9029, "longitude": 1.9093},
    {"city": "Limoges", "latitude": 45.8336, "longitude": 1.2611},
    {"city": "Tours", "latitude": 47.3941, "longitude": 0.6848},
    {"city": "Besançon", "latitude": 47.2378, "longitude": 6.0241},
    {"city": "Clermont-Ferrand", "latitude": 45.7772, "longitude": 3.0870},
    {"city": "Mulhouse", "latitude": 47.7508, "longitude": 7.3359},
    {"city": "Avignon", "latitude": 43.9493, "longitude": 4.8055}
]

org = [
    {"name": "SmileFund"},
    {"name": "WarmHearts"},
    {"name": "PureJoy"},
    {"name": "SunriseAid"}
]

# Message producer
def produce_messages(batch_size=10, pause=1):
    deactivate_previous_campaigns()  # Set previous campaigns to inactive
    campaign_id = random.randint(1, 1000000)
    selected_cities = random.sample(cities, 4)  # Choisir 4 villes aléatoirement
    print("Selected cities:", [city['city'] for city in selected_cities])
    while True:
        batch = []  # Messages tab for batch insertion
        
        for _ in range(batch_size):
            city = random.choice(selected_cities)
            organization = random.choice(org)

            message = {
                "transaction_id": random.randint(1, 100000000),
                "city": city["city"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "organization": organization["name"],
                "transaction_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_amount": round(random.uniform(1.0, 10.0)),
                "campaign_id": campaign_id,
                "is_campaign_active": 1
            }
            print(message)
            batch.append(message)

        # Send batch messages to the producer
        for message in batch:
            producer.produce(topic, key=str(message["transaction_id"]), value=json.dumps(message), callback=acked)

        producer.flush()
        print(f"{batch_size} sent messages.")
        time.sleep(pause)

# Ctrl + C Signal handler
def signal_handler(sig, frame):
    print('Kafka production message stopping ...')
    producer.flush()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Execution
print("Start sending batch messages. Press Ctrl + C to stop.")
produce_messages(batch_size=5, pause=1) # Configure here the traffic produced (batch_size=1000, pause=0.1) to enforced data insertions

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
python3 donations-prod.py
```
CTL+C to stop the production, it means stop the campaign

### Query your data

**1 - Count the number of donation for the current campaign**
```sql
SELECT COUNT(*) FROM donations.donation_transactions
WHERE is_campaign_active=1
```
Create directly an index to optimize performance at scale
```sql
CREATE INDEX idx_campaign_active_campaign_id 
ON donations.donation_transactions (is_campaign_active, campaign_id);
```

**2 - Get total amount of donations for the current campaign**
```sql
SELECT 
    SUM(total_amount) AS total_donation_amount
FROM 
    donation_transactions
WHERE is_campaign_active=1;
```
Create directly an index to optimize performance at scale
```sql
CREATE INDEX idx_is_campaign_active 
ON donation_transactions (is_campaign_active)
```

**3 - Get Best city, organisation donation**
```sql
SELECT 
    city,
    organization,
    SUM(total_amount) AS total_donation_amount
FROM 
    donation_transactions
WHERE is_campaign_active=1
GROUP BY 
    city,organization
ORDER BY 
    total_donation_amount DESC
LIMIT 1;
```
At this stage we can think about the possibility of SHARD KEY and SORT KEY
Possible index
```sql
CREATE INDEX idx_campaign_city_org 
ON donation_transactions (is_campaign_active, city, organization);
```

**4 - Amount of donations per geo loc city**
```sql
SELECT 
    city,
    organization,
    SUM(total_amount) AS total_donation_amount
FROM 
    donation_transactions
WHERE is_campaign_active=1
GROUP BY 
    city,organization
ORDER BY 
    total_donation_amount DESC
LIMIT 1;
```
At this stage we can think about the possibility of SHARD KEY and SORT KEY
Possible index
```sql
CREATE INDEX idx_campaign_city_total 
ON donation_transactions (is_campaign_active, city, total_amount);
```
**5 - Total amount of donations per organization**
```sql
SELECT 
    organization,
    SUM(total_amount) AS total_donation_amount
FROM 
    donation_transactions
WHERE is_campaign_active=1
GROUP BY 
    organization
ORDER BY 
    total_donation_amount DESC;
```
Possible index
```sql
CREATE INDEX idx_campaign_org_total 
ON donation_transactions (is_campaign_active, organization, total_amount);
```

**6 - Last 35s of total amount of donations per city**
```sql
SELECT 
    city,
    SUM(total_amount) AS total_donation_amount
FROM 
    donation_transactions
WHERE 
    transaction_date > CONVERT_TZ(NOW(), 'UTC', 'Europe/Paris') - INTERVAL 35 SECOND
    AND is_campaign_active=1
GROUP BY 
    city
ORDER BY city ASC;
```
At this stage we can think about the possibility of SHARD KEY and SORT KEY
Possible index
```sql
CREATE INDEX idx_campaign_date_city ON donation_transactions (is_campaign_active, transaction_date, city);
```

**7 - Last 28s of total amount of donations per organization**
```sql
SELECT 
    organization,
    SUM(total_amount) AS total_donation_amount
FROM 
    donation_transactions
WHERE 
    transaction_date > CONVERT_TZ(NOW(), 'UTC', 'Europe/Paris') - INTERVAL 28 SECOND
    AND is_campaign_active=1
GROUP BY 
    organization
```
At this stage we can think about the possibility of SHARD KEY and SORT KEY
Possible index
```sql
CREATE INDEX idx_campaign_date_org ON donation_transactions (is_campaign_active, transaction_date, organization);
```

Execute each request on the query editor of Single Store and perform a Vizualisation Explain Profile. As there is not a lot of data, no significant impact are identified.

## Realtime Analysis
### Grafana
We can use our previously Datasource Connector to begin to build a dashboard. 
Import the dashboard provided (*Donations-1731526356608.json*). And start your script.
Setup the refresh rate to 250 ms, and observe the pain, then setup 500ms, ...
More data, more performance pain, try to modify index but it seems that we need to define a Hash key and a Sort Key.

We figure out that there is 2 main analytics perpective :
- Are we interest by cities donations collect ?
- Or are we interest by association donations collect ?

### SingleStore
On SingleStore Cloud, we can perform a Vizualisation Explain. Now let's discover Query history feature that store by default queries that execution time exceed 1s.
I want to decrease this execution time parameter to see queries exceeded 200ms for instance.
```sql
DROP EVENT TRACE Query_completion;
CREATE EVENT TRACE Query_completion WITH (Query_text = on, Duration_threshold_ms = 200);
```
Launch a new aggressive campaign and wait a moment to capture request execution time that exceed 200ms. Wait a moment to see it in Query History.
You can perform a query profiling with vizual explain in the sql editor, you could easily track one exceeded 200ms.
### Optimization
I figure out that when I created the table, I didn't used a SHARD KEY and SORT KEY and it seems that if we change the distribution of our data we can collect directly our analytics data related partitions, we could get better performance on accessing data.

Note that in a OLTP perspective an even distribution is more appropriate. Generally we shard with a high cardinality column.  
In OLAP perspective we **slightly** desequilibrate the distribution to let the queries perform efficiently.

**Final Recommendations**  
1 - Shard Key:  
If you often filter or aggregate by city, a SHARD KEY on city is a good approach, but the combination SHARD KEY (city, transaction_id) might better distribute the data.  
2 - Sort Key:  
If the table is often used to analyze transactions by city, you can adjust the SORT KEY using city, campaign_id, or transaction_date depending on the most frequent queries.
For example: SORT KEY (city, transaction_date) might be useful if the queries use GROUP BY city and sort the data by date.
Here is a modified example that might improve performance, depending on the query use cases:


```sql
DROP PIPELINE donations_kafka_consumer;
DROP TABLE donation_transactions;

CREATE TABLE donation_transactions (
    transaction_id INT NOT NULL,
    city VARCHAR(50) NOT NULL,
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    organization VARCHAR(50),
    transaction_date DATETIME NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    campaign_id INT NOT NULL,
    is_campaign_active TINYINT(1) DEFAULT 0,
    PRIMARY KEY (transaction_id, city),
    SHARD KEY (city, transaction_id),
    SORT KEY (city, transaction_date)
);

CREATE PIPELINE donations_kafka_consumer AS LOAD DATA KAFKA '<Your EC2_DNS Instance>:9092/donations' SKIP DUPLICATE KEY ERRORS INTO TABLE donation_transactions FORMAT JSON;

-- Keep in mind that messages retention in the topic is 5mn !!
START PIPELINE donations_kafka_consumer; 
```

## Demo
View a specific panel in the grafana dashboard and observe the latencies, capture the requests in the Query History that exceed 200ms. Are your SHARD KEY AND SORT KEY RELEVANT ?

Choose the panel you want to enphasize or create a new one.
Enjoy !