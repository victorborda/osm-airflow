from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.hooks.base import BaseHook
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable

# useful strings for the bash commands
pgosm_conn = BaseHook.get_connection('pgosm_postgres_conn')
pgosm_password = pgosm_conn.password
pgosm_user = pgosm_conn.login
pgosm_port = pgosm_conn.port
pgosm_date = "2024-07-25"
local_src_data_dir = Variable.get("pgosm_data_dir")
pgosm_auth = f"-e POSTGRES_PASSWORD={pgosm_password} -e POSTGRES_USER={pgosm_user}"
container_name = "pgosm"
flex_cmd = f"{container_name} python3 docker/pgosm_flex.py"
docker_exec = f"docker exec -it {pgosm_auth} {flex_cmd} --ram=8"

us_states = [
    {"region": "north-america/us", "subregion": "colorado"},
 #   {"region": "north-america/us", "subregion": "oregon"},
#    {"region": "north-america/us", "subregion": "washington"}
]

eu_countries = [
    {"region": "eu", "subregion": "spain"}
]

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id="osm_dag",
    default_args=default_args,
    description='OpenStreetMap ETL Pipeline',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@weekly',
    catchup=False,
    tags=['osm', 'etl'],
) as dag:

    # starts a disposable container with PgOsmFlex + PostGIS + Osm2Pgsql
    # this will perform the ET part of the pipeline
    # at the end we dump it out and then load it into the target real PostGIS database
    # note that, the pgosm container does not have any initial data at this point unless we take specific steps
    # we have two choices - one is to let the ET process download the files from geofabrik.de while performing the task
    # which is fine, but also a bit slow, or if the files are available locally place them in the local_src_data_dir prior to running airflow
    # note that local_src_data_dir must be an absolute path - don't try using aliases etc
    run_pgosm = BashOperator(
        task_id="run_pgosm",
        bash_command=f"docker run --platform linux/amd64 \
                                  --name {container_name} \
                                  -v {local_src_data_dir}:/app/output \
                                  -v /etc/localtime:/etc/localtime:ro \
                                  -e POSTGRES_PASSWORD={pgosm_password} \
                                  -p {pgosm_port}:5432 \
                                  -d rustprooflabs/pgosm-flex:0.4.5"
    )

    # US States
    with TaskGroup(group_id="etl_us_states_osm") as etl_us_states_osm:
        for us_state in us_states:
            options = f"--region={us_state['region']} --subregion={us_state['subregion']} --pgosm-date={pgosm_date}"
            cmd = f"{docker_exec} {options}"
            BashOperator(
                    task_id=f"etl_{us_state['subregion']}_osm",
                    bash_command=f"{cmd} > /Users/victorborda/airflow/logs/pgosm_output.log"
                )

    # EU Countries
    with TaskGroup(group_id="etl_eu_countries_osm") as etl_eu_countries_osm:
        for eu_country in eu_countries:
            options = f"--region={eu_country['region']} --subregion={eu_country['subregion']} --pgosm-date={pgosm_date}"
            BashOperator(
                task_id=f"etl_{eu_country['subregion']}_osm",
                bash_command=f"{docker_exec} {options}"
            )

    # Write db dump file out to the shared storage
    dump_osm_db_to_file = BashOperator(
        task_id="dump_osm_db_to_file",
        bash_command=f"{docker_exec} pg_dump -U postgres -d osm -f {local_src_data_dir}/osm-postetl-{pgosm_date}.sql"
    )

run_pgosm >> etl_us_states_osm >> etl_eu_countries_osm >> dump_osm_db_to_file 