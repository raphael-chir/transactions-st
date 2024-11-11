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
