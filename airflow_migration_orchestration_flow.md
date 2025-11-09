# Airflow 1.x to 2.x Migration Guide for Claude Agents

## Core Concept
Migrate from operator-based patterns to TaskFlow API (`@dag`/`@task` decorators). Templates at `/home/dev/claude_dev/airflow/data-airflow/dags/`: `_dag_taskflow_template/` (pure Python) and `_dag_template/` (multi-operator).

## Template Selection
- **TaskFlow** (`_dag_taskflow_template/`): Python-only workflows, auto XCom, cleaner syntax
- **Traditional** (`_dag_template/`): Multiple operators (Bash, Snowflake, custom), explicit dependencies

**Common Pattern**: Business logic in `src/main.py` with `Main` class + `execute()` method. Import from `common/` for hooks/operators/callbacks.

---

## 🚨 CRITICAL: DRY (Don't Repeat Yourself) Enforcement

### Absolute Requirement: Use Existing Common Components

**NEVER create custom operators, hooks, or utilities at the DAG level when they exist in `/common/`.**

**🔧 USE THE SKILL**: Before writing ANY custom code, execute the `check-common-components` skill:
```
/check-common-components
```

This skill will:
1. Search `/home/dev/claude_dev/airflow/data-airflow/dags/common/` for existing implementations
2. Review available operators, hooks, and callbacks
3. Provide a decision matrix: USE | EXTEND | CREATE
4. Generate a report documenting your research

### Available Common Components

**Custom Operators** (`common/custom_operators/`):
- `SFTPToSnowflakeOperator` - SFTP → S3 → Snowflake pipeline (supports manifest/Snowflake filtering)
- `CustomSheetsToSnowflakeOperator` - Google Sheets → Snowflake
- `CrossDbOperator` - Cross-database operations
- `SnowflakeToS3StageOperator` - Snowflake → S3 staging
- `SnowflakeToPestroutesOperator` - Snowflake → PestRoutes
- `SnowflakeExternalTableOperator` - External table creation
- `CustomSparkKubernetesOperator` - Spark on K8s
- `TriggerDbtJobOperator` - dbt Cloud job triggering
- `CustomPestRoutesToS3Operator` - PestRoutes API → S3 (20+ entity types)

**Custom Hooks** (`common/custom_hooks/`):
- `CustomSnowflakeHook` - Enhanced Snowflake operations
- `CustomExternalTableHook` - External table management
- `CustomS3Hook` - S3 operations with prefix support
- `S3ToSnowflakeHook` - S3 → Snowflake data loading
- `S3ToSnowflakeInsertHook` - S3 → Snowflake inserts
- `CustomPestRoutesHook` - PestRoutes API integration
- `CustomGoogleSheetsHook` - Google Sheets API

**Custom Callbacks** (`common/custom_callbacks/`):
- `AirflowCallback` - Standard success/failure callbacks (Slack, logging)

### Anti-Pattern Example: DO NOT DO THIS

**❌ WRONG** - The `cresta` DAG created custom SFTP implementation:
```python
# cresta/src/sftp_operations.py - 407 lines of REDUNDANT code
class SFTPClient:  # Custom SFTP client
    def __init__(self, host, username, password=None, private_key=None): ...
    def connect(self): ...
    def download_file(self, file_name): ...

def parse_ssh_key(private_key): ...  # Custom SSH parsing
def execute_sftp_to_snowflake_pipeline(...): ...  # Entire pipeline reimplemented
```

**✅ CORRECT** - Use existing `SFTPToSnowflakeOperator`:
```python
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

@dag(...)
def cresta_dag():
    sftp_task = SFTPToSnowflakeOperator(
        task_id="sftp_to_snowflake",
        sftp_conn_id="cresta_sftp",
        directory="/incoming",
        s3_prefix="cresta/data",
        snowflake_query="SELECT date FROM dates WHERE active = true",
        use_flat_structure=True,
        determination_method="snowflake",  # or "manifest"
    )
```

### Verification Checklist Before Writing Code

Before creating ANY custom operator/hook/utility:
- [ ] Searched `common/custom_operators/` for existing operators
- [ ] Searched `common/custom_hooks/` for existing hooks
- [ ] Reviewed existing operator parameters for extensibility
- [ ] Confirmed functionality doesn't exist OR genuinely requires extension
- [ ] If extending, used inheritance: `class MyOperator(ExistingOperator)`

### When Extension is Needed

If existing component needs modification, extend via inheritance:

```python
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

class CustomCrestaOperator(SFTPToSnowflakeOperator):
    """Extended operator for Cresta-specific processing."""

    def __init__(self, custom_param: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_param = custom_param

    def execute(self, context):
        # Custom pre-processing
        self.log.info(f"Custom processing: {self.custom_param}")
        # Call parent implementation
        return super().execute(context)
```

### Import Pattern: Always from `common`

```python
# ✅ CORRECT imports
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator
from common.custom_hooks.custom_snowflake_hook import CustomSnowflakeHook
from common.custom_callbacks.custom_callbacks import AirflowCallback

# ❌ WRONG - Creating duplicates
from my_dag.src.sftp_client import SFTPClient  # NO!
from my_dag.src.custom_hook import MySnowflakeHook  # NO!
```

### Cost of Duplication

Duplicating existing code creates:
- **Maintenance Burden**: Bug fixes needed in multiple places
- **Inconsistency**: Different implementations with different behaviors
- **Technical Debt**: 407+ lines of redundant code (cresta example)
- **Testing Overhead**: Must test multiple implementations
- **Code Review Waste**: Reviewing already-solved problems

**Rule**: If it exists in `common/`, USE IT. Period.

---

## Critical Breaking Changes

| Component | Legacy (1.x) | Modern (2.x) | Notes |
|-----------|--------------|--------------|-------|
| **DAG Definition** | `with DAG(..., schedule_interval=...)` | `@dag(..., schedule=...)` + call function | Must instantiate decorated function |
| **Parameters** | `concurrency`, `default_args['start_date']` | `max_active_tasks`, `start_date` (decorator param) | Move start_date out of default_args |
| **Task Definition** | `PythonOperator(python_callable=func, provide_context=True)` | `@task` decorator on function | Auto context access, no `provide_context` |
| **Dependencies** | `task1 >> task2` (explicit only) | Data flow `task2(task1())` or explicit `>>` | Data flow creates automatic deps |
| **XCom** | Manual: `ti.xcom_push(key, value)` | Automatic: `return value` | Return values auto-pushed |
| **Dynamic Tasks** | Loop with `PythonOperator(task_id=...)` | Use `task.override(task_id=...)(args)` | Required for unique IDs in loops |
| **Imports** | `airflow.operators.python_operator` | `airflow.decorators import dag, task` | Legacy operators removed |

**Critical**: Always call decorated DAG function: `dag_instance = my_dag()`

---

## Migration Steps

1. **Assessment**: Inventory operators, providers, hooks, dependencies, XCom patterns
2. **Structure**: Create modular structure (`my_dag/main.py`, `src/tasks.py`, `src/config.py`)
3. **Refactor**:
   - Replace `DAG()` with `@dag`, move `start_date` to decorator, rename params
   - Replace `PythonOperator` with `@task`, remove `provide_context`, add type hints
   - Update imports to `airflow.decorators`
4. **Test**:
   ```bash
   airflow dags list-import-errors
   airflow dags test my_dag 2024-01-01
   airflow tasks test my_dag task_id 2024-01-01
   ```

## Key Patterns

**Dependencies**: Data flow `task2(task1())` auto-creates deps vs explicit `task1 >> task2`

**Branching**: Use `@task.branch` returning task_id string

**XCom**: Return values auto-pushed (no manual `xcom_push`)

**Dynamic Tasks**: Use `task.override(task_id=f"task_{item}")(item)` in loops

**Context**: Auto-injected - use `get_current_context()` or named params (`ti=None, dag_run=None`)

---

## Validation Checklist

Before deployment:
- [ ] `PythonOperator` → `@task`, `DAG()` → `@dag`, DAG function called
- [ ] Removed: `provide_context`, `dag=` param; Updated: `schedule_interval` → `schedule`, `concurrency` → `max_active_tasks`
- [ ] Added: type hints, imports from `airflow.decorators`
- [ ] Dynamic tasks use `.override(task_id=...)`
- [ ] Tests pass: `airflow dags list-import-errors`, `airflow dags test`, `airflow tasks test`

## Common Pitfalls

1. **Not calling DAG function**: `@dag def my_dag(): ...` needs `my_dag()` at end
2. **Task ID collisions**: Use `.override(task_id=f"task_{item}")` in loops
3. **Mixing patterns**: Don't mix `@task` with `PythonOperator` in same DAG
4. **Context usage**: Remove `provide_context=True`, use `get_current_context()` or named params

## Example: Before & After

**Legacy (43 lines):**
```python
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

default_args = {'start_date': datetime(2023, 1, 1), 'retries': 2}
dag = DAG('my_dag', default_args=default_args, schedule_interval='@daily', concurrency=5)

def extract_data(**context):
    return {"data": "extracted"}

def transform_data(**context):
    data = context['ti'].xcom_pull(task_ids='extract')
    return {"data": "transformed"}

extract = PythonOperator(task_id='extract', python_callable=extract_data, provide_context=True, dag=dag)
transform = PythonOperator(task_id='transform', python_callable=transform_data, provide_context=True, dag=dag)
extract >> transform
```

**Modern (27 lines, 37% reduction):**
```python
from airflow.decorators import dag, task
from pendulum import datetime

@dag(schedule='@daily', start_date=datetime(2023, 1, 1), catchup=False,
     max_active_tasks=5, default_args={'retries': 2}, tags=['etl'])
def my_dag():
    @task
    def extract() -> dict:
        return {"data": "extracted"}

    @task
    def transform(data: dict) -> dict:
        return {"data": "transformed"}

    transform(extract())

my_dag()
```

---

**References**: [Airflow 2.0 Migration](https://airflow.apache.org/docs/apache-airflow/stable/upgrading-to-2.html) | [TaskFlow Tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html)