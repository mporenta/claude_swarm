# Compare DAG Configs Skill

## Purpose
Compare legacy `default_args` and DAG parameters with modern `@dag` decorator parameters, mapping deprecated settings to their Airflow 2.x equivalents.

## When to Use
**MANDATORY** during migration:
- Before converting DAG() to @dag decorator
- When analyzing legacy DAG configuration
- To ensure all settings are properly migrated
- To identify deprecated parameters

## Execution Steps

### 1. Extract Legacy default_args
```bash
# Find default_args dictionary
grep -A 20 "default_args\s*=" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Extract just the dictionary content
sed -n '/default_args\s*=/,/^}/p' /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 2. Extract Legacy DAG Parameters
```bash
# Find DAG instantiation
grep -A 15 "DAG(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Extract specific parameters
grep "schedule_interval" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep "concurrency" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep "max_active_runs" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep "catchup" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 3. Check for Deprecated Parameters
```bash
# Find provide_context (removed in 2.x)
grep "provide_context" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find task_concurrency (renamed)
grep "task_concurrency" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find execution_date (changed to logical_date)
grep "execution_date" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 4. Extract Callbacks
```bash
# Find callback functions
grep "on_failure_callback\|on_success_callback\|on_retry_callback" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Check if AirflowCallback is used
grep "AirflowCallback" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 5. Extract Email Settings
```bash
# Find email configurations
grep "email\|email_on_failure\|email_on_retry" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 6. Check Tags and Documentation
```bash
# Find tags
grep "tags" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find description
grep "description" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find doc_md
grep "doc_md" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

## Parameter Migration Map

### Critical Parameter Changes

| Legacy Parameter | Modern Parameter | Location | Notes |
|------------------|------------------|----------|-------|
| `schedule_interval='@daily'` | `schedule='@daily'` | @dag decorator | Renamed |
| `concurrency=5` | `max_active_tasks=5` | @dag decorator | Renamed |
| `default_args['start_date']` | `start_date=datetime(...)` | @dag decorator | Move out of default_args |
| `task_concurrency=3` | `max_active_tis_per_dag=3` | @dag decorator | Renamed |
| `provide_context=True` | *(remove)* | N/A | Auto-provided in TaskFlow |
| `dag=dag_instance` | *(remove)* | N/A | Not needed with @dag |
| `execution_date` | `logical_date` | Context | Renamed in context |

### default_args That Stay in default_args

Keep these in `default_args` dict:
- `retries`
- `retry_delay`
- `email`
- `email_on_failure`
- `email_on_retry`
- `on_failure_callback`
- `on_success_callback`
- `owner`
- `depends_on_past`

### Parameters That Move to @dag Decorator

Move these OUT of `default_args`:
- `start_date` → @dag parameter
- `end_date` → @dag parameter
- `tags` → @dag parameter

## Output Report Format

After executing this skill, provide:

```markdown
## DAG Configuration Migration Report: [dag_name]

### Legacy Configuration

**DAG Definition** (Lines X-Y):
```python
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email': ['team@example.com'],
    'email_on_failure': True,
    'on_failure_callback': slack_alert,
}

dag = DAG(
    'my_dag',
    default_args=default_args,
    schedule_interval='@daily',
    concurrency=5,
    max_active_runs=3,
    catchup=False,
    tags=['production', 'etl'],
    description='Legacy DAG description'
)
```

---

### Modern Configuration

```python
from airflow.decorators import dag
from pendulum import datetime
from datetime import timedelta

@dag(
    dag_id='my_dag',
    schedule='@daily',  # ✓ Renamed from schedule_interval
    start_date=datetime(2023, 1, 1),  # ✓ Moved out of default_args
    catchup=False,
    max_active_tasks=5,  # ✓ Renamed from concurrency
    max_active_runs=3,
    tags=['production', 'etl'],
    description='Legacy DAG description',
    default_args={
        'owner': 'airflow',
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
        'email': ['team@example.com'],
        'email_on_failure': True,
        'on_failure_callback': slack_alert,
    }
)
def my_dag():
    # Task definitions here
    pass

my_dag()  # ✓ Must call the decorated function
```

---

### Migration Map

| Parameter | Legacy Value | Modern Value | Action |
|-----------|--------------|--------------|--------|
| **schedule_interval** | `'@daily'` | `schedule='@daily'` | ✅ RENAME parameter |
| **concurrency** | `5` | `max_active_tasks=5` | ✅ RENAME parameter |
| **start_date** | In default_args | `start_date=datetime(2023,1,1)` | ✅ MOVE to decorator |
| **max_active_runs** | `3` | `max_active_runs=3` | ✅ KEEP (no change) |
| **catchup** | `False` | `catchup=False` | ✅ KEEP (no change) |
| **tags** | `['production', 'etl']` | `tags=['production', 'etl']` | ✅ KEEP (no change) |
| **owner** | In default_args | Keep in default_args | ✅ KEEP in default_args |
| **retries** | In default_args | Keep in default_args | ✅ KEEP in default_args |
| **retry_delay** | In default_args | Keep in default_args | ✅ KEEP in default_args |
| **email** | In default_args | Keep in default_args | ✅ KEEP in default_args |
| **on_failure_callback** | In default_args | Keep in default_args | ✅ KEEP in default_args |

---

### Deprecated Parameters Found

#### ❌ provide_context=True
**Location**: PythonOperator definitions
**Action**: REMOVE - Context is automatically provided in TaskFlow
```python
# Legacy
task = PythonOperator(
    task_id='my_task',
    python_callable=my_func,
    provide_context=True  # ❌ REMOVE THIS
)

# Modern
@task
def my_task():
    # Context automatically available
    pass
```

#### ⚠️ execution_date References
**Location**: Functions using `context['execution_date']`
**Action**: UPDATE to `context['logical_date']` or use `data_interval_start`
```python
# Legacy
def my_func(**context):
    exec_date = context['execution_date']  # ❌ Deprecated

# Modern
@task
def my_func():
    from airflow.operators.python import get_current_context
    context = get_current_context()
    logical_date = context['logical_date']  # ✅ Use this
    # OR
    data_interval_start = context['data_interval_start']  # ✅ Or this
```

---

### Callbacks Analysis

**Current Callbacks**:
- `on_failure_callback`: slack_alert (Line 45)

**Recommendation**:
```python
# Check if common callback exists
from common.custom_callbacks.custom_callbacks import AirflowCallback

# If yes, use it:
default_args = {
    'on_failure_callback': AirflowCallback.failure_callback,
    'on_success_callback': AirflowCallback.success_callback,
}
```

---

### Import Updates

**Legacy Imports**:
```python
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
```

**Modern Imports**:
```python
from airflow.decorators import dag, task
from pendulum import datetime  # Recommended over datetime.datetime
from datetime import timedelta
```

---

### Summary

**Parameters Changed**: 3
- schedule_interval → schedule
- concurrency → max_active_tasks
- start_date moved to decorator

**Parameters Removed**: 1
- provide_context (no longer needed)

**Parameters Unchanged**: 8
- owner, retries, retry_delay, email, email_on_failure, catchup, tags, description

**Callbacks**: ✓ Compatible (consider using AirflowCallback from common/)

**Complexity**: ⚠️ MEDIUM (some refactoring needed)

### Migration Checklist

- [ ] Rename `schedule_interval` → `schedule`
- [ ] Rename `concurrency` → `max_active_tasks`
- [ ] Move `start_date` out of default_args to @dag decorator
- [ ] Remove `provide_context=True` from all operators
- [ ] Update `execution_date` → `logical_date` in functions
- [ ] Keep retries, retry_delay, email settings in default_args
- [ ] Import from `airflow.decorators` instead of `airflow`
- [ ] Call decorated function at end: `my_dag()`
- [ ] Consider using common/AirflowCallback for standardized alerts
```

## Enforcement

This skill MUST be executed:
- Before converting DAG() to @dag decorator
- To ensure proper parameter migration
- To identify deprecated settings
- For configuration validation

**Proper configuration migration prevents runtime errors and ensures Airflow 2.x compatibility.**
