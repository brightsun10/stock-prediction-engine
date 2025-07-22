# Real-Time Stock Prediction Engine Architecture

## Overview
A scalable system to predict stock prices in real time using Kafka, Spark Streaming, and Random Forest, deployed on AWS EC2 with Docker.

## Architecture
1. **Kafka**: Ingests stock data (OHLC, volume, returns, volatility, bid/ask, RSI, moving average, sentiment) into `stock-data`.
2. **Spark Streaming**: Processes streams, applies Random Forest model, outputs to `stock-predictions` and Snowflake.
3. **Random Forest**: Predicts next-minute close price using 11 features.
4. **Snowflake**: Stores predictions for analytics.
5. **AWS EC2**: Hosts Docker containers with auto-scaling.

## Data Flow
1. Producer sends stock data to Kafka.
2. Spark Streaming processes micro-batches, applies model.
3. Predictions saved to Kafka and Snowflake.

## Deployment
- Dockerized for portability.
- Deployed on EC2 with monitoring.
- Configurable via `config.yaml`.

## Metrics
- MAE: ~3.2% on test data.
- Latency: <1 second per prediction.