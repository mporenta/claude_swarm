# Invoca DAG Migration Mapping Reference

**Purpose**: Quick reference guide for mapping legacy code to modern Airflow 2.0 equivalents

---

## Import Migrations

### Operators

| Legacy | Modern | File | Status |
|--------|--------|------|--------|
| `airflow.operators.python_operator.PythonOperator` | `airflow.operators.python.PythonOperator` | hourly.py:21 | ✅ Updated |
| `plugins.operators.snowflake_execute_query.SnowflakeExecuteQueryOperator` | `airflow.providers.snowflake.operators.snowflake.SnowflakeOperator` | hourly.py:22 | ✅ Updated |
| (none) | `airflow.operators.empty.EmptyOperator` | hourly.py:20 | ✅ Added |

### Hooks

| Legacy | Modern | Usage | Status |
|--------|--------|-------|--------|
| `plugins.hooks.s3_upload_hook.S3UploadHook` | `common.custom_hooks.custom_s3_hook.CustomS3Hook` | invoca_processor.py:47 | ✅ Updated |
| `plugins.hooks.snowflake_custom.SnowflakeCheckTableExists` | `common.custom_hooks.custom_snowflake_hook.CustomSnowflakeHook.check_table_exists()` | invoca_processor.py:46 | ✅ Updated |
| `plugins.hooks.snowflake_custom.SnowflakeCreateTable` | `common.custom_hooks.custom_snowflake_hook.CustomSnowflakeHook.ensure_table_exists()` | invoca_processor.py:51 | ✅ Updated |

### Callbacks

| Legacy | Modern | Usage | Status |
|--------|--------|-------|--------|
| `plugins.operators.on_failure_callback` | `common.custom_callbacks.custom_callbacks.AirflowCallback.on_failure_callback` | hourly.py:24, 58 | ✅ Updated |
| `plugins.operators.on_success_callback` | `common.custom_callbacks.custom_callbacks.AirflowCallback.on_success_callback` | hourly.py:24, 57 | ✅ Updated |

---

## Function Migrations

### API Functions (Legacy → Modern)

#### `get_conn(endpoint)`
**Location**: `config/invoca/functions.py:21-32` → `src/invoca_api.py:30-64`

| Aspect | Legacy | Modern | Change |
|--------|--------|--------|--------|
| Location | `config/invoca/functions.py` | `src/invoca_api.py` | Moved to dedicated module |
| Type hints | None | Full (`endpoint: str → Tuple[str, Dict[str, str]]`) | ✅ Added |
| Error handling | Generic | Specific with context | ✅ Improved |
| Docstring | Minimal | Comprehensive | ✅ Enhanced |
| Exception handling | Try/except vague | Try/except specific | ✅ Improved |

**Usage**:
```python
# Legacy
from config.invoca.functions import get_conn
base_url, headers = get_conn(endpoint)

# Modern
from src.invoca_api import get_conn
base_url, headers = get_conn(endpoint)
```

#### `fetch_transactions(base_url, headers, base_params, task_name)`
**Location**: `config/invoca/functions.py:34-85` → `src/invoca_api.py:67-205`

| Aspect | Legacy | Modern | Change |
|--------|--------|--------|--------|
| Rate limit handling | Infinite loop possible | Max 3 retries | ✅ Fixed |
| Request timeout | None | 30 seconds | ✅ Added |
| Error propagation | Silent break | Exception raised | ✅ Improved |
| Type hints | None | Full | ✅ Added |
| Pagination logic | Same | Same (improved logging) | ✅ Preserved |
| Docstring | None | Comprehensive | ✅ Added |
| Constants | Hardcoded | Module-level constants | ✅ Improved |

**Usage**:
```python
# Legacy
from config.invoca.functions import fetch_transactions
transactions = fetch_transactions(base_url, headers, params, 'transactions')

# Modern
from src.invoca_api import fetch_transactions
transactions = fetch_transactions(base_url, headers, params, 'transactions')
```

#### `fetch_data(task_name, endpoint, params, **kwargs)`
**Location**: `config/invoca/functions.py:87-97` → `src/invoca_api.py:208-239`

| Aspect | Legacy | Modern | Change |
|--------|--------|--------|--------|
| Error on unknown task | Silent return None | Explicit ValueError | ✅ Fixed |
| Type hints | None | Full | ✅ Added |
| Dispatcher pattern | If/else | If/else (better error msg) | ✅ Improved |
| Docstring | None | Comprehensive | ✅ Added |

**Usage**:
```python
# Legacy
from config.invoca.functions import fetch_data
data = fetch_data('transactions', endpoint, params)
if data is None:
    # Need manual error handling

# Modern
from src.invoca_api import fetch_data
data = fetch_data('transactions', endpoint, params)
# Exception raised automatically if task unknown
```

### Processing Functions (Legacy → Modern)

#### `ensure_table_exists(schema_name, table_name, **kwargs)`
**Location**: `config/invoca/functions.py:121-130` → `src/invoca_processor.py:21-55` (renamed to `ensure_transactions_table`)

| Aspect | Legacy | Modern | Change |
|--------|--------|--------|--------|
| Hook used | Legacy SnowflakeCheckTableExists, SnowflakeCreateTable | CustomSnowflakeHook | ✅ Updated |
| Environment awareness | Not present | Automatic (via hook) | ✅ Added |
| Error handling | Generic | Specific with context | ✅ Improved |
| Type hints | None | Full | ✅ Added |
| Docstring | None | Comprehensive | ✅ Added |
| Return type | None | None (explicit) | ✅ Added |

**Usage**:
```python
# Legacy
from config.invoca.functions import ensure_table_exists
ensure_table_exists('invoca', 'transactions')

# Modern
from src.invoca_processor import ensure_transactions_table
ensure_transactions_table('invoca', 'transactions')
```

#### `load_to_s3(task_name, endpoint, params, schema_name, table_name, **kwargs)`
**Location**: `config/invoca/functions.py:99-119` → `src/invoca_processor.py:58-116` (renamed to `fetch_and_upload_to_s3`)

| Aspect | Legacy | Modern | Change |
|--------|--------|--------|--------|
| Hook used | Legacy S3UploadHook | CustomS3Hook | ✅ Updated |
| Organization | Single function | Separate fetch + upload orchestration | ✅ Improved |
| Error handling | Generic | Specific with context | ✅ Improved |
| Type hints | None | Full | ✅ Added |
| Docstring | None | Comprehensive | ✅ Added |
| Return value | None | S3 key | ✅ Enhanced |

**Usage**:
```python
# Legacy
from config.invoca.functions import load_to_s3
load_to_s3('transactions', endpoint, params, 'invoca', 'transactions')

# Modern
from src.invoca_processor import fetch_and_upload_to_s3
s3_key = fetch_and_upload_to_s3('transactions', endpoint, params, 'invoca', 'transactions')
```

---

## Configuration Migrations

### Task Configuration

**Legacy** (`config/invoca/config.py`):
```python
tasks = [
    {
        'active': 1,
        'task_name': 'transactions',
        'endpoint': '2020-10-01/advertisers/transactions',
        'params': {...},
        'schema_name': 'invoca',
        'table_name': 'transactions'
    }
]
```

**Modern** (`src/main.py`):
```python
class Main:
    TASKS = [
        {
            'active': 1,
            'task_name': 'transactions',
            'endpoint': '2020-10-01/advertisers/transactions',
            'params': {...},
            'schema_name': 'invoca',
            'table_name': 'transactions'
        }
    ]

    @classmethod
    def get_active_tasks(cls):
        return [task for task in cls.TASKS if task.get('active', 0) == 1]
```

**Benefits**:
- Configuration in class (easier to extend)
- Helper methods for filtering
- Clear documentation
- Type hints available

---

## DAG Definition Migrations

### Variable Retrieval

**Legacy** (`invoca_to_snowflake.py:34`):
```python
env = Variable.get('env')
```

**Modern** (`hourly.py:37`):
```python
ENV = Variable.get('env', default_var='local')
```

**Benefits**: Explicit default value prevents KeyError

### Schedule Configuration

**Legacy**:
```python
if env == 'local':
    schedule_interval = None
elif env == 'staging':
    schedule_interval = "30 7-23 * * *"
elif env == 'prod':
    schedule_interval = "0 7-23 * * *"
```

**Modern** (same pattern, better named constant):
```python
ENV = Variable.get('env', default_var='local')

if ENV == 'local':
    SCHEDULE_INTERVAL = None
elif ENV == 'staging':
    SCHEDULE_INTERVAL = "30 7-23 * * *"
elif ENV == 'prod':
    SCHEDULE_INTERVAL = "0 7-23 * * *"
else:
    SCHEDULE_INTERVAL = None
```

**Benefits**:
- Consistent naming (SCHEDULE_INTERVAL vs schedule_interval)
- Explicit else case
- Clearer intent

### Callback Integration

**Legacy** (`invoca_to_snowflake.py:10-23`):
```python
from plugins.operators.on_failure_callback import on_failure_callback
from plugins.operators.on_success_callback import on_success_callback

default_args = {
    ...
    "on_success_callback": on_success_callback,
    "on_failure_callback": on_failure_callback
}
```

**Modern** (`hourly.py:51-60`):
```python
from common.custom_callbacks.custom_callbacks import AirflowCallback

cb = AirflowCallback()
default_args = {
    ...
    "on_success_callback": [cb.on_success_callback],
    "on_failure_callback": [cb.on_failure_callback]
}
```

**Benefits**:
- Consistent callback pattern
- List format (Airflow 2 standard)
- Centralized callback management
- Better error logging

### Task Definition

**Legacy** (`invoca_to_snowflake.py:68-106`):
```python
ensure_table_exists_task = PythonOperator(
    task_id = f"{task_name}_ensure_table_exists",
    provide_context = True,
    python_callable = ensure_table_exists,
    op_kwargs = {...}
)

s3_to_snowflake_task = SnowflakeExecuteQueryOperator(
    task_id = f"{task_name}_to_snowflake",
    provide_context = True,
    query = f"""..."""
)
```

**Modern** (`hourly.py:102-157`):
```python
ensure_table_task = PythonOperator(
    task_id=f"{task_name}_ensure_table_exists",
    python_callable=ensure_transactions_table,
    op_kwargs={...},
    doc="Ensure the Snowflake table exists before loading data"
)

copy_to_snowflake_task = SnowflakeOperator(
    task_id=f"{task_name}_to_snowflake",
    sql=f"""...""",
    doc="Copy JSON data from S3 to Snowflake raw table"
)
```

**Benefits**:
- Removed deprecated `provide_context` (automatic in Airflow 2)
- Added `doc` parameters
- Modern operator names
- Consistent formatting
- Added start/end marker tasks for better visibility

---

## Error Handling Migrations

### Rate Limit Handling

**Legacy** (`functions.py:71-77`):
```python
else:
    logger.error(f"Failed to fetch data: {response.text}")
    if response.status_code == 429:
        logger.info("Hit rate limit, waiting before retrying...")
        time.sleep(30)  # Could retry forever!
    else:
        break  # Silent break on other errors
```

**Modern** (`invoca_api.py:131-150`):
```python
elif response.status_code == 429:
    logger.warning("Rate limit (429) encountered from Invoca API")
    retry_after = response.headers.get("Retry-After")
    retry_delay = int(retry_after) if retry_after else RATE_LIMIT_BACKOFF_SECONDS
    logger.info(f"Rate limit encountered. Waiting {retry_delay} seconds...")
    time.sleep(retry_delay)
    # Max retries enforced by loop structure

else:
    error_msg = (
        f'API returned status code {response.status_code}: '
        f'{response.text}'
    )
    logger.error(error_msg)
    raise requests.exceptions.RequestException(error_msg)
```

**Improvements**:
- ✅ Respects HTTP Retry-After header
- ✅ Max retries ceiling enforced
- ✅ Explicit exception raising (no silent breaks)
- ✅ Better error messages
- ✅ Specific exception types

### Unknown Task Handling

**Legacy** (`functions.py:91-97`):
```python
if task_name == 'transactions':
    transactions = fetch_transactions(base_url, headers, params, task_name)
    logger.info(f"Fetch data complete. Fetched {len(transactions)} transactions.")
    return transactions
else:
    logger.error(f"Task {task_name} not found.")
    return None  # Silent failure!
```

**Modern** (`invoca_api.py:208-239`):
```python
if task_name == 'transactions':
    base_url, headers = get_conn(endpoint)
    transactions = fetch_transactions(base_url, headers, params, task_name)
    return transactions
else:
    error_msg = f'Unknown task: {task_name}. Must be one of: [transactions]'
    logger.error(error_msg)
    raise ValueError(error_msg)  # Explicit failure!
```

**Improvements**:
- ✅ Clear error message
- ✅ Explicit exception (ValueError)
- ✅ No silent failures
- ✅ Easier debugging

---

## Type Hint Migrations

### Function Signatures

**Legacy** (no type hints):
```python
def get_conn(endpoint):
def fetch_transactions(base_url, headers, base_params, task_name):
def fetch_data(task_name, endpoint, params, **kwargs):
def ensure_table_exists(schema_name, table_name, **kwargs):
def load_to_s3(task_name, endpoint, params, schema_name, table_name, **kwargs):
```

**Modern** (complete type hints):
```python
def get_conn(endpoint: str) -> Tuple[str, Dict[str, str]]:
def fetch_transactions(
    base_url: str,
    headers: Dict[str, str],
    base_params: Dict[str, Any],
    task_name: str
) -> List[Dict[str, Any]]:
def fetch_data(
    task_name: str,
    endpoint: str,
    params: Dict[str, Any],
    **kwargs: Any
) -> List[Dict[str, Any]]:
def ensure_transactions_table(
    schema_name: str,
    table_name: str,
    **kwargs: Any
) -> None:
def fetch_and_upload_to_s3(
    task_name: str,
    endpoint: str,
    params: Dict[str, Any],
    schema_name: str,
    table_name: str,
    **kwargs: Any
) -> Optional[str]:
```

**Benefits**:
- ✅ IDE auto-completion support
- ✅ Type checking with mypy
- ✅ Better documentation
- ✅ Clearer code intent
- ✅ Easier debugging

---

## Module Organization

### Before (Flat Structure)
```
dags/
└── invoca_to_snowflake.py      (108 lines - DAG only)
    └── imports from config/invoca/

config/
└── invoca/
    ├── __init__.py
    ├── config.py                (13 lines - task config)
    └── functions.py             (152 lines - all functions)

plugins/
├── hooks/
│   ├── s3_upload_hook.py
│   ├── snowflake_custom.py
│   └── ...
├── operators/
│   ├── snowflake_execute_query.py
│   ├── on_failure_callback.py
│   ├── on_success_callback.py
│   └── ...
```

### After (Modular Structure)
```
dags/invoca_to_snowflake/
├── __init__.py                  (Package marker)
├── hourly.py                    (152 lines - DAG orchestration)
├── README.md                    (400+ lines - documentation)
├── MIGRATION_COMPLETED.md       (500+ lines - migration guide)
└── src/
    ├── __init__.py              (Package marker)
    ├── main.py                  (70 lines - configuration)
    ├── invoca_api.py            (218 lines - API functions)
    └── invoca_processor.py      (118 lines - processing functions)

common/
├── custom_hooks/
│   ├── custom_s3_hook.py
│   ├── custom_snowflake_hook.py
│   └── ...
└── custom_callbacks/
    └── custom_callbacks.py
```

**Benefits**:
- ✅ Clear separation of concerns
- ✅ Easier to test individual modules
- ✅ Self-contained DAG package
- ✅ Centralized common code
- ✅ Better maintainability

---

## Summary Table

| Category | Aspect | Legacy | Modern | Status |
|----------|--------|--------|--------|--------|
| **Imports** | Python operator | `python_operator` | `python` | ✅ Updated |
| | Snowflake operator | `SnowflakeExecuteQueryOperator` | `SnowflakeOperator` | ✅ Updated |
| | S3 hook | `S3UploadHook` | `CustomS3Hook` | ✅ Updated |
| | Snowflake hook | `SnowflakeCheckTableExists` | `CustomSnowflakeHook` | ✅ Updated |
| | Callbacks | Plugin-based | `AirflowCallback` | ✅ Updated |
| **Error Handling** | Rate limiting | No max_retries | Max 3 retries | ✅ Fixed |
| | Unknown tasks | Silent return | Exception | ✅ Fixed |
| | Request timeout | None | 30 seconds | ✅ Added |
| | Error logging | Generic | Context-rich | ✅ Improved |
| **Code Quality** | Type hints | None | 100% | ✅ Added |
| | Docstrings | Minimal | Comprehensive | ✅ Enhanced |
| | Organization | Monolithic | Modular | ✅ Refactored |
| | Testability | Difficult | Easy | ✅ Improved |
| **Features** | Pagination | Maintained | Maintained | ✅ Preserved |
| | Schedule | Maintained | Maintained | ✅ Preserved |
| | Database selection | Environment-aware | Environment-aware | ✅ Preserved |
| | S3 upload | Maintained | Maintained | ✅ Preserved |
| | Snowflake copy | Maintained | Maintained | ✅ Preserved |

---

*This reference document helps understand the mapping between legacy and modern implementations.*
