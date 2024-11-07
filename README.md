# osm-airflow
Use Apache Airflow to perform ETL of OSM data

Airflow setup for local Mac development:

1. Set this value in your .zshrc file:

```bash
export AIRFLOW_HOME=~/airflow
```

or whatever suits your fancy.

From here down run commands in this directory after having run
```bash
source ./venv/bin/activate
```

2. Run the following commands just once:

```bash
airflow db init
airflow users create --username admin --password <password> --firstname <yourfirstname> --lastname <yourlastname> --role Admin --email <youremail>
```

3. Run these to actually start the airflow webserver and scheduler (any non-conflicting port is fine):

```bash
airflow webserver --port 8090 > webserver.log 2>&1 &
airflow scheduler > scheduler.log 2>&1 &
```
