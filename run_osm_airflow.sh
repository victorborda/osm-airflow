#!/bin/bash

# start_airflow.sh
./activate.sh

# Start webserver in background
airflow webserver --port 8090 > webserver.log 2>&1 &

# Start scheduler in background
airflow scheduler > scheduler.log 2>&1 &

echo "Airflow webserver and scheduler started. See logs in webserver.log and scheduler.log."
echo "You can access the Airflow UI at http://localhost:8090"
