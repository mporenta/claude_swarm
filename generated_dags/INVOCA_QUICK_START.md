# Invoca Migration - Quick Start Guide

**Read this first**: 5-minute overview of what needs to happen

---

## What's the Issue?

The legacy Invoca DAG uses deprecated Airflow 1.0 patterns:
- Old import paths (`python_operator` → `python`)
- Legacy hooks from `plugins/` → modern hooks in `common/`
- No type hints
- Weak error handling (infinite rate limit retries)

## What Needs to Change?

### 1. Directory Structure (Create New)
```
/home/dev/airflow/data-airflow/dags/invoca_to_snowflake/
├── src/
│   ├── __init__.py
│   ├── main.py              # Config & task definitions
│   ├── invoca_api.py        # API calling functions
│   └── invoca_processor.py  # S3 upload & table operations
└── hourly.py                # DAG definition
```

### 2. Import Changes (Find & Replace)

**In hourly.py DAG file:**
```python
# OLD → NEW

from airflow.operators.python_operator import PythonOperator
→ from airflow.operators.python import PythonOperator

from plugins.operators.snowflake_execute_query import SnowflakeExecuteQueryOperator
→ from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

from plugins.operators.on_failure_callback import on_failure_callback
from plugins.operators.on_success_callback import on_success_callback
→ from common.custom_callbacks.custom_callbacks import AirflowCallback
```

**In src/invoca_processor.py:**
```python
# OLD → NEW

from plugins.hooks.s3_upload_hook import S3UploadHook
→ from common.custom_hooks.custom_s3_hook import CustomS3Hook

from plugins.hooks.snowflake_custom import SnowflakeCheckTableExists, SnowflakeCreateTable
→ from common.custom_hooks.custom_snowflake_hook import CustomSnowflakeHook
```

### 3. Function Extraction (Where to Move Code)

**Move to `src/invoca_api.py`**:
- `get_conn(endpoint)` - No changes needed, just add type hints
- `fetch_transactions(...)` - Add `max_retries=3` for rate limiting
- `fetch_data(...)` - Dispatcher function

**Move to `src/invoca_processor.py`**:
- `ensure_table_exists(...)` - Use `CustomSnowflakeHook().ensure_table_exists()`
- `load_to_s3(...)` - Use `CustomS3Hook(...).upload_file()`

**Keep in `hourly.py`**:
- DAG definition
- Task instantiation loop
- Configuration

### 4. Error Handling Fix (Critical)

In `src/invoca_api.py`, update rate limit handling:

**OLD** (infinite retries):
```python
if response.status_code == 429:
    time.sleep(30)
    # tries again indefinitely
```

**NEW** (with ceiling):
```python
max_retries = 3
retry_count = 0

if response.status_code == 429:
    if retry_count < max_retries:
        retry_after = int(response.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        retry_count += 1
    else:
        raise Exception("Max retries exceeded after rate limiting")
```

### 5. Type Hints (Add to Every Function)

**OLD**:
```python
def fetch_transactions(base_url, headers, base_params, task_name):
```

**NEW**:
```python
from typing import Dict, List, Any

def fetch_transactions(
    base_url: str,
    headers: Dict[str, str],
    base_params: Dict[str, Any],
    task_name: str
) -> List[Dict[str, Any]]:
```

### 6. Hook Usage Changes

**OLD** - Manual S3 upload:
```python
from plugins.hooks.s3_upload_hook import S3UploadHook

S3UploadHook(
    s3_client=...,
    s3_prefix=...,
    data=...,
    file_type="json"
).upload_file()
```

**NEW** - Modern hook:
```python
from common.custom_hooks.custom_s3_hook import CustomS3Hook

CustomS3Hook(
    s3_prefix="invoca/transactions",
    data=transactions,
    file_type="json"
).upload_file()
```

### 7. Table Operations Changes

**OLD** - Separate hooks:
```python
from plugins.hooks.snowflake_custom import SnowflakeCheckTableExists, SnowflakeCreateTable

SnowflakeCheckTableExists(...)
SnowflakeCreateTable(...)
```

**NEW** - Unified hook:
```python
from common.custom_hooks.custom_snowflake_hook import CustomSnowflakeHook

hook = CustomSnowflakeHook()
hook.ensure_table_exists(schema='invoca', table='transactions')
```

### 8. Callback Changes

**OLD** - In default_args:
```python
from plugins.operators.on_failure_callback import on_failure_callback
from plugins.operators.on_success_callback import on_success_callback

default_args = {
    "on_success_callback": on_success_callback,
    "on_failure_callback": on_failure_callback,
}
```

**NEW** - Using class instance:
```python
from common.custom_callbacks.custom_callbacks import AirflowCallback

cb = AirflowCallback()
default_args = {
    "on_success_callback": [cb.on_success_callback],
    "on_failure_callback": [cb.on_failure_callback],
}
```

---

## What Stays the Same?

✅ Variable names: `invoca_transactions_last_id`, `env`
✅ Connection ID: `invoca`
✅ S3 Stage: `@STAGE.S3_STRATEGY_DATA_LAKE/invoca/transactions`
✅ Snowflake database: `RAW_STAGING` (staging), `RAW` (prod)
✅ Data flow: API → S3 → Snowflake
✅ 3-task structure: ensure → fetch → copy

---

## Testing Checklist Before Production

1. **Local Testing**
   - [ ] Run with `env=local`
   - [ ] Verify S3 upload works
   - [ ] Verify Snowflake COPY works

2. **Data Validation**
   - [ ] Compare row counts with Legacy DAG
   - [ ] Verify no duplicates
   - [ ] Spot-check data values

3. **Staging Testing**
   - [ ] Run 3+ hourly cycles
   - [ ] Check execution times
   - [ ] Verify pagination tracking (last_id variable)

4. **Performance Check**
   - [ ] Compare timing: Legacy vs. Airflow 2
   - [ ] Check S3 upload speed
   - [ ] Check Snowflake query speed

---

## File Locations (Reference)

**Modern Hooks** (use these):
- `/home/dev/airflow/data-airflow/dags/common/custom_hooks/custom_s3_hook.py`
- `/home/dev/airflow/data-airflow/dags/common/custom_hooks/custom_snowflake_hook.py`
- `/home/dev/airflow/data-airflow/dags/common/custom_callbacks/custom_callbacks.py`

**Legacy DAG** (reference only):
- `/home/dev/airflow/data-airflow-legacy/dags/invoca_to_snowflake.py`

**Target Location** (create new):
- `/home/dev/airflow/data-airflow/dags/invoca_to_snowflake/`

---

## Common Mistakes to Avoid

❌ **Don't**: Leave old hook imports (will fail at runtime)
✅ **Do**: Replace ALL import statements from `plugins/`

❌ **Don't**: Keep rate limiting without max_retries (infinite loop risk)
✅ **Do**: Add `max_retries=3` ceiling

❌ **Don't**: Skip type hints (reduces code quality)
✅ **Do**: Add type hints to every function

❌ **Don't**: Mix DAG logic with task functions
✅ **Do**: Keep DAG definition clean, move logic to `src/`

❌ **Don't**: Use old callback functions directly
✅ **Do**: Create `AirflowCallback()` instance and use class methods

---

## Quick Command Reference

```bash
# Verify no stray plugins imports
grep -r "from plugins" /home/dev/airflow/data-airflow/dags/invoca_to_snowflake/

# Check Python syntax
python3 -m py_compile /home/dev/airflow/data-airflow/dags/invoca_to_snowflake/**/*.py

# Run flake8 (required before merge)
flake8 /home/dev/airflow/data-airflow/dags/invoca_to_snowflake/

# Local test (if airflow installed)
# cd /home/dev/airflow && AIRFLOW__CORE__DAGS_FOLDER=/home/dev/airflow/data-airflow/dags airflow dags test invoca_to_snowflake
```

---

## When to Call Owner (zak.browning@goaptive.com)

✓ After local testing completes (ready to move to staging)
✓ If any data discrepancies found
✓ Before production deployment
✓ To confirm acceptable execution times

---

## Next Steps

1. **Create new directory structure** (5 min)
2. **Move and refactor functions** (1 hour)
3. **Update imports** (30 min)
4. **Add type hints** (30 min)
5. **Fix error handling** (15 min)
6. **Local testing** (1-2 hours)
7. **Staging validation** (2-4 hours)
8. **Production readiness** (1 hour)

**Total**: 6-10 hours of development + testing time

---

**Questions?** Refer to full analysis in `INVOCA_MIGRATION_ANALYSIS.md`
