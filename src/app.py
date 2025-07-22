import os
import json
# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# print(project_root)
# os.environ["HADOOP_HOME"] = os.path.join(project_root, "hadoop")#"hadoop" if os.name == 'nt' else "hadoop"
# os.environ["JAVA_HOME"] = os.path.join(project_root, "Java/jdk-17")#"Java\\jdk-17" if os.name == 'nt' else "Java/jdk-17"
import yaml
import pandas as pd
import numpy as np
from kafka import KafkaProducer
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
from sklearn.ensemble import RandomForestRegressor
import joblib
import logging
import snowflake.connector

# Load configuration
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Verify checkpoint directory exists
checkpoint_dir = config['spark']['checkpoint_location']
if not os.path.exists(checkpoint_dir):
    os.makedirs(checkpoint_dir)
    logger.info(f"Created checkpoint directory: {checkpoint_dir}")
else:
    logger.info(f"Using existing checkpoint directory: {checkpoint_dir}")

# Select bootstrap servers based on environment
IN_DOCKER = os.getenv('IN_DOCKER', 'false').lower() == 'true'
kafka_bootstrap_servers = config['kafka']['bootstrap_servers_container'] if IN_DOCKER else config['kafka']['bootstrap_servers_host']
logger.info(f"Using Kafka bootstrap servers: {kafka_bootstrap_servers}")

# Initialize Spark session
spark = SparkSession.builder \
    .appName("RealTimeStockPrediction") \
    .config("spark.streaming.stopGracefullyOnShutdown", "true") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.apache.kafka:kafka-clients:2.6.0") \
    .getOrCreate()
spark.sparkContext.setLogLevel("INFO")

# Define stock data schema
schema = StructType([
    StructField("timestamp", StringType(), False),
    StructField("stock_symbol", StringType(), False),
    StructField("open", DoubleType(), False),
    StructField("high", DoubleType(), False),
    StructField("low", DoubleType(), False),
    StructField("close", DoubleType(), False),
    StructField("volume", DoubleType(), False),
    StructField("returns", DoubleType(), False),
    StructField("volatility", DoubleType(), False),
    StructField("bid_price", DoubleType(), False),
    StructField("ask_price", DoubleType(), False),
    StructField("rsi", DoubleType(), False),
    StructField("ma_5", DoubleType(), False),
    StructField("market_sentiment", DoubleType(), False)
])

# Load pre-trained model
def load_model():
    """Load the pre-trained stock prediction model."""
    try:
        model = joblib.load("models/stock_model.pkl")
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

# # Save predictions to Snowflake
# def save_to_snowflake(df, table_name):
#     """Save DataFrame to Snowflake."""
#     try:
#         conn = snowflake.connector.connect(**config['snowflake'])
#         df.toPandas().to_sql(table_name, conn, index=False, if_exists='append')
#         logger.info(f"Saved {df.count()} records to Snowflake table {table_name}")
#         conn.close()
#     except Exception as e:
#         logger.error(f"Error saving to Snowflake: {e}")

def process_batch(batch_df, batch_id):
    """Process a batch of stock data to predict prices."""
    model = load_model()
    if not model:
        logger.error("Model not loaded. Skipping batch.")
        return

    rows = batch_df.collect()
    results = []
    # Define feature names as used during model training
    feature_names = ['open', 'high', 'low', 'volume', 'returns', 'volatility', 
                     'bid_price', 'ask_price', 'rsi', 'ma_5', 'market_sentiment']
    
    for row in rows:
        try:
            # Create a pandas DataFrame with feature names
            features = pd.DataFrame(
                [[row.open, row.high, row.low, row.volume, row.returns, row.volatility, 
                  row.bid_price, row.ask_price, row.rsi, row.ma_5, row.market_sentiment]],
                columns=feature_names
            )
            predicted_price = float(model.predict(features)[0])
            results.append({
                "timestamp": row.timestamp,
                "stock_symbol": row.stock_symbol,
                "predicted_price": predicted_price,
                "actual_price": row.close
            })
            logger.info(f"Predicted {row.stock_symbol} price: {predicted_price:.2f}, Actual: {row.close:.2f}")
        except Exception as e:
            logger.error(f"Error processing row {row.timestamp}: {e}")

    if results:
        result_schema = StructType([
            StructField("timestamp", StringType(), False),
            StructField("stock_symbol", StringType(), False),
            StructField("predicted_price", DoubleType(), False),
            StructField("actual_price", DoubleType(), False)
        ])
        result_df = spark.createDataFrame(results, result_schema)
        result_df.show()
        try:
            result_df.selectExpr("to_json(struct(*)) AS value") \
                .write \
                .format("kafka") \
                .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
                .option("topic", "stock-predictions") \
                .mode("append") \
                .save()
            logger.info(f"Processed batch {batch_id} with {len(results)} predictions")
        except Exception as e:
            logger.error(f"Error writing to Kafka topic stock-predictions: {e}")
        # save_to_snowflake(result_df, "STOCK_PREDICTIONS")

def main():
    """Main function for real-time stock prediction."""
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    for i in range(10):
        close = np.random.normal(100, 10)
        transaction = {
            "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "stock_symbol": np.random.choice(['AAPL', 'MSFT', 'GOOGL']),
            "open": float(np.random.normal(close, 1)),
            "high": float(np.random.uniform(close, close * 1.02)),
            "low": float(np.random.uniform(close * 0.98, close)),
            "close": float(close),
            "volume": float(np.random.randint(1000, 20000)),
            "returns": float(np.random.normal(0, 0.01)),
            "volatility": float(np.random.uniform(0, 0.05)),
            "bid_price": float(close * np.random.uniform(0.98, 0.99)),
            "ask_price": float(close * np.random.uniform(1.01, 1.02)),
            "rsi": float(np.random.uniform(0, 100)),
            "ma_5": float(np.random.normal(close, 2)),
            "market_sentiment": float(np.random.uniform(-1, 1))
        }
        producer.send('stock-data', transaction)
        producer.flush()
        logger.info(f"Sent transaction: {transaction}")

    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", "stock-data") \
        .load()

    df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    query = df.writeStream \
        .option("checkpointLocation", config['spark']['checkpoint_location']) \
        .foreachBatch(process_batch) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully")
        spark.stop()