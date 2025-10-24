# CLAUDE.md

Self-managed Apache Airflow 2 deployment on AWS EKS. DAG migration guide from Airflow Legacy to Airflow 2.

## Quick Start
```bash
# AWS Login
python3 infrastructure/scripts/update_aws_sso_creds.py data-staging

# Local Setup
bash scripts/create_override_file.sh
docker build -t docker-airflow-2 . && docker compose up -d
python3 scripts/refresh_pg_db.py
python3 scripts/load_aws_to_airflow.py

# Common Commands
docker build -t docker-airflow-2 .                           # Build
docker compose up -d                                          # Run
pip install flake8 && flake8                                  # Lint (required)
bash scripts/push_image_to_ecr.sh                            # Deploy
bash scripts/health_check.sh                                 # Health check
AUTO_FIX=true bash scripts/health_check.sh                   # Auto-fix pods
```

## Architecture

### Data Pipeline Pattern
1. **Airflow 2**: Fetch from source → Load to S3
2. **DBT**: Fetch from S3 (usually JSON) → Normalize via external tables

**External Tables (Preferred)**: DBT uses `raw.external_tables` schema, models in `models/raw/{source}/`
**Direct Load (Alternative)**: Airflow loads to S3 AND raw Snowflake tables, DBT models in `models/clean/{source}/`

### Directory Structure
```
dags/
├── {pipeline_name}/
│   ├── src/
│   │   ├── main.py          # Main class with execute() method
│   │   └── sql/
│   ├── daily.py             # DAG file named by schedule
│   └── intraday.py
├── common/
│   ├── custom_operators/     # Reusable operators
│   └── custom_hooks/         # Reusable connection handlers
```

**Templates**: Use `_dag_template/` or `_dag_taskflow_template/` for new DAGs

### Components
- **Hooks**: `common/custom_hooks/` - CustomS3Hook, CustomSnowflakeHook, CustomPestRoutesHook, etc.
- **Operators**: `common/custom_operators/` - SheetsToSnowflakeOperator, SnowflakeExternalTableOperator, etc.
- **Callbacks**: `common/custom_callbacks/` - Standard success/failure handlers
- **Infrastructure**: EKS cluster with scheduler/webserver, worker, and optional GPU node groups
- **Batch Size**: Default 250,000 records (configurable via `batch_size` parameter)

## Code Standards (MANDATORY)

### Type Hints (Required)
```python
from typing import Optional, List, Dict, Union

def example_function(param1: int, param2: Optional[str]) -> Union[str, None]:
    """
    Comprehensive docstrings required.
    
    :param param1: Description
    :param param2: Description
    :return: Description
    """
    pass
```

### Heartbeat-Safe Code (CRITICAL)
**❌ NEVER in DAG-level code** (runs on Airflow heartbeat):
- Database connections
- API calls
- File I/O
- Heavy `__init__` methods

**✅ ALLOWED in DAG-level code**:
- `Variable.get()` (for env config)
- Lightweight assignments
- Imports

**Pattern**:
```python
# ✅ Preferred: Pass params to execute()
class DataProcessor:
    def execute(self, schema: str, table: str, **kwargs):
        # All initialization happens here
        connection = create_db_connection()
        # Task logic
        
# ✅ Even better: Use functions
def process_data(schema: str, table: str, **kwargs):
    connection = create_db_connection()
    # Task logic
```

### Class vs Function
**Use Classes**: Shared state, complex business logic, multiple related methods
**Use Functions**: Simple transformations, single-purpose tasks

### Clean Code
- Meaningful names, small focused functions
- flake8 compliant (mandatory for deployment)
- DRY principle, single responsibility
- Always leave newline at end of Python files

## Airflow 2 Migration Patterns

### Import Updates
```python
# Operators
from airflow.operators.python import PythonOperator  # Not python_operator
from airflow.operators.bash import BashOperator

# Hooks  
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

# Utils
from airflow.utils.task_group import TaskGroup
```

### DAG Definition
```python
from airflow import DAG
from airflow.models import Variable

env = Variable.get("environment", default_var="local")

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id=f'{env}_my_dag',
    default_args=default_args,
    schedule_interval='0 1 * * *' if env == 'prod' else None,
    catchup=False,
    tags=['source_name', 'category'],
) as dag:
    # Tasks here
```

### TaskGroups (Preferred over SubDAGs)
```python
from airflow.utils.task_group import TaskGroup

with TaskGroup("extract_group") as extract:
    task1 = PythonOperator(...)
    task2 = PythonOperator(...)
    task1 >> task2

start >> extract >> process
```

### Standard Task Pattern
```python
task = PythonOperator(
    task_id='descriptive_task_name',
    python_callable=MyClass().execute,  # or function_name
    op_kwargs={'param1': value1, 'param2': value2},
    dag=dag,
)
```

## Common Patterns

### Batching Large Datasets
```python
def batch_process(records: List[Dict], batch_size: int = 250_000) -> None:
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        process_batch(batch)
        logging.info(f"Processed batch {i//batch_size + 1}")
```

### Rate Limiting
```python
if response.status_code == 429:
    retry_after = response.headers.get("Retry-After")
    time.sleep(int(retry_after) if retry_after else exponential_backoff_delay)
```

### XCom vs S3
```python
# ❌ Avoid: Large data in XCom
return large_dataset

# ✅ Use S3 for large data
s3_key = upload_to_s3(large_dataset)
return s3_key
```

### Environment Configuration
```python
if env == "local":
    schedule_interval = None
    max_records = 50_000
elif env == "staging":
    schedule_interval = None
    max_records = None
elif env == "prod":
    schedule_interval = '0 1 * * *'
    max_records = None
```

### Connection vs Variable
```python
# ✅ Preferred: Consolidate into connection
conn = BaseHook.get_connection('api_connection')
base_url = conn.host
api_key = conn.password

# ❌ Avoid: Separate variables
base_url = Variable.get('api-url')
api_key = Variable.get('secret-api-key')
```

## Troubleshooting

### Import Errors
Update to Airflow 2 provider-based imports (see Migration Patterns above)

### External Table Issues
- Verify S3 path matches external table location
- Check Snowflake stage permissions
- Validate file format (usually JSON)

### Large Function Timeouts
- Break into smaller focused functions
- Implement batching for large datasets
- Add progress logging

### Pod/EKS Issues
```bash
bash scripts/health_check.sh                    # Check status
AUTO_FIX=true bash scripts/health_check.sh      # Auto-fix common issues
```

## File Locations
- **common/**: Rarely changed, highly reusable hooks/operators
- **dags/{pipeline}/src/**: Pipeline-specific code with `main.py` entry point
- **infrastructure/**: Terraform/Kubernetes configs
- **scripts/**: Deployment and utility scripts