import mysql.connector
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
produce_messages(batch_size=5, pause=1)
