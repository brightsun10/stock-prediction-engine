from kafka import KafkaProducer
import json
import pandas as pd
import numpy as np
import logging
import yaml
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)


# Select bootstrap servers based on environment
IN_DOCKER = os.getenv('IN_DOCKER', 'false').lower() == 'true'
kafka_bootstrap_servers = config['kafka']['bootstrap_servers_container'] if IN_DOCKER else config['kafka']['bootstrap_servers_host']
logger.info(f"Using Kafka bootstrap servers: {kafka_bootstrap_servers}")

producer = KafkaProducer(
    bootstrap_servers=kafka_bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
for i in range(10):
    close = np.random.normal(100, 10)
    transaction = {
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stock_symbol': np.random.choice(['AAPL', 'MSFT', 'GOOGL']),
        'open': float(np.random.normal(close, 1)),
        'high': float(np.random.uniform(close, close * 1.02)),
        'low': float(np.random.uniform(close * 0.98, close)),
        'close': float(close),
        'volume': float(np.random.randint(1000, 20000)),
        'returns': float(np.random.normal(0, 0.01)),
        'volatility': float(np.random.uniform(0, 0.05)),
        'bid_price': float(close * np.random.uniform(0.98, 0.99)),
        'ask_price': float(close * np.random.uniform(1.01, 1.02)),
        'rsi': float(np.random.uniform(0, 100)),
        'ma_5': float(np.random.normal(close, 2)),
        'market_sentiment': float(np.random.uniform(-1, 1))
    }
    producer.send('stock-data', transaction)
    producer.flush()
    logger.info(f"Sent transaction: {transaction}")