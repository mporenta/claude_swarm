"""
Invoca to Snowflake - Hourly DAG (Airflow 2.0).

This DAG fetches transaction data from the Invoca API, uploads it to S3,
and loads it into a Snowflake raw table via COPY INTO.

Schedule:
- Local: None (manual triggers only)
- Staging: 30 * * 7-23 * * (hourly at :30 minute, 7 AM - 11 PM)
- Production: 0 * 7-23 * * (hourly on hour, 7 AM - 11 PM)

Data Flow: Invoca API (paginated) -> S3 (JSON) -> Snowflake (raw table)
"""

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

from common.custom_callbacks.custom_callbacks import AirflowCallback
from src.main import Main
from src.invoca_processor import (
    ensure_transactions_table,
    fetch_and_upload_to_s3
)

# DAG configuration
DAG_ID = "invoca_to_snowflake"
DEFAULT_VIEW = "graph"
OWNER = "zak.browning@goaptive.com"

# Environment configuration
ENV = Variable.get('env', default_var='local')

# Schedule interval configuration
if ENV == 'local':
    SCHEDULE_INTERVAL = None
elif ENV == 'staging':
    SCHEDULE_INTERVAL = "30 7-23 * * *"  # Hourly at :30 minute, 7 AM - 11 PM
elif ENV == 'prod':
    SCHEDULE_INTERVAL = "0 7-23 * * *"   # Hourly on hour, 7 AM - 11 PM
else:
    SCHEDULE_INTERVAL = None

# Default DAG arguments
default_args = {
    "owner": OWNER,
    "depends_on_past": False,
    "start_date": pendulum.datetime(year=2024, month=2, day=1, tz="America/Denver"),
    "email": [],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

# Add callbacks
# Note: AirflowCallback is heartbeat-safe (lightweight __init__ with no DB/API calls)
cb = AirflowCallback()
default_args["on_success_callback"] = [cb.on_success_callback]
default_args["on_failure_callback"] = [cb.on_failure_callback]

# DAG tags
tags = [
    "Invoca",
    "Snowflake",
    "S3",
    "MigratedToAF2"
]

# Create DAG
with DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    schedule_interval=SCHEDULE_INTERVAL,
    concurrency=3,
    max_active_runs=1,
    catchup=False,
    tags=tags,
    description=(
        "Fetch Invoca transaction data, upload to S3, and load into Snowflake. "
        "Uses paginated API calls with state tracking via Airflow Variables."
    ),
) as dag:

    # Get task configuration
    main = Main()
    tasks_config = main.get_active_tasks()

    # Create start marker task
    start_task = EmptyOperator(task_id="start")

    # Create end marker task
    end_task = EmptyOperator(task_id="end", trigger_rule="none_failed_min_one_success")

    # Create tasks for each active endpoint
    for task_config in tasks_config:
        task_name = task_config['task_name']
        endpoint = task_config['endpoint']
        params = task_config['params']
        schema_name = task_config['schema_name']
        table_name = task_config['table_name']

        # Task 1: Ensure table exists
        ensure_table_task = PythonOperator(
            task_id=f"{task_name}_ensure_table_exists",
            python_callable=ensure_transactions_table,
            op_kwargs={
                'schema_name': schema_name,
                'table_name': table_name
            },
            doc="Ensure the Snowflake table exists before loading data"
        )

        # Task 2: Fetch from API and upload to S3
        fetch_and_load_task = PythonOperator(
            task_id=f"{task_name}_to_s3",
            python_callable=fetch_and_upload_to_s3,
            op_kwargs={
                'task_name': task_name,
                'endpoint': endpoint,
                'params': params,
                'schema_name': schema_name,
                'table_name': table_name
            },
            doc="Fetch transactions from Invoca API and upload to S3"
        )

        # Task 3: Copy from S3 to Snowflake
        copy_to_snowflake_task = SnowflakeOperator(
            task_id=f"{task_name}_to_snowflake",
            snowflake_conn_id="snowflake_default",
            sql=f"""
                COPY INTO {schema_name}.{table_name}
                FROM (
                    SELECT
                        $1                           AS raw_json
                        , metadata$filename           AS s3_path
                        , metadata$file_row_number    AS s3_row_number
                        , CURRENT_TIMESTAMP::TIMESTAMP AS pipe_loaded_at
                    FROM @STAGE.S3_STRATEGY_DATA_LAKE/{schema_name}/{table_name}
                        (file_format => stage.json_format)
                )
            """,
            doc="Copy JSON data from S3 to Snowflake raw table"
        )

        # Set task dependencies
        start_task >> ensure_table_task >> fetch_and_load_task >> copy_to_snowflake_task >> end_task
