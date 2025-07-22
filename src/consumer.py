from kafka import KafkaConsumer
import json
import logging
import os
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Select bootstrap servers based on environment
IN_DOCKER = os.getenv('IN_DOCKER', 'false').lower() == 'true'
kafka_bootstrap_servers = config['kafka']['bootstrap_servers_container'] if IN_DOCKER else config['kafka']['bootstrap_servers_host']
logger.info(f"Using Kafka bootstrap servers: {kafka_bootstrap_servers}")

consumer = KafkaConsumer(
    config['kafka']['output_topic'],
    bootstrap_servers=kafka_bootstrap_servers,
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='stock-predictions-consumer'
)

for message in consumer:
    data = message.value
    logger.info(f"Received prediction: {data}")