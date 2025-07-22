#!/bin/bash
   /usr/bin/kafka-topics --create --topic stock-data --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists
   /usr/bin/kafka-topics --create --topic stock-predictions --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists
   /usr/bin/kafka-topics --list --bootstrap-server kafka:9092