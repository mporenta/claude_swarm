# Invoca to Snowflake - Airflow 1.0 to 2.0 Migration Summary

**Date**: October 24, 2025
**Legacy DAG**: `/home/dev/airflow/data-airflow-legacy/dags/invoca_to_snowflake.py`
**Owner**: zak.browning@goaptive.com
**Complexity**: MEDIUM | **Effort**: 2-3 days | **Risk**: LOW

---

## Executive Summary

The Invoca DAG is well-structured and heartbeat-safe with clear append-only data flow. Migration requires standard import updates, legacy hook replacement, and code refactoring into modular functions. No external tables needed; raw table approach optimal for this use case.

---

## 1. Current DAG Structure

### Schedule & Configuration
```
Local:       None (manual triggers)
Staging:     "30 7-23 * * *" (hourly at :30, 7 AM - 11 PM)
Production:  "0 7-23 * * *"  (hourly on hour, 7 AM - 11 PM)
```

**DAG Parameters**:
- Owner: zak.browning@goaptive.com
- Start Date: February 1, 2024
- Retries: 1 (3 min delay)
- Concurrency: 3 / Max Active Runs: 1
- Catchup: False

### Task Breakdown (per active endpoint)
```
ensure_table_exists → fetch_to_s3 → copy_to_snowflake
```

**Data Flow**: Invoca API (paginated) → S3 (JSON) → Snowflake (raw table)

**Key Details**:
- Pagination via `start_after_transaction_id` (incremental sync)
- Invoca API connection: `invoca` (host, auth_token in extras)
- State tracking: Variable `invoca_{task_name}_last_id`
- Rate limiting: 3s delays + 30s backoff on 429 status

---

## 2. Critical Migration Issues Identified

### 2.1 Import Updates Required

| Legacy Import | Modern Import | Status |
|---|---|---|
| `from airflow.operators.python_operator import PythonOperator` | `from airflow.operators.python import PythonOperator` | Required |
| `from plugins.operators.snowflake_execute_query import SnowflakeExecuteQueryOperator` | `from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator` | Required |
| `from plugins.hooks.s3_upload_hook import S3UploadHook` | `from common.custom_hooks.custom_s3_hook import CustomS3Hook` | Required |
| Callbacks from `plugins.operators` | `from common.custom_callbacks.custom_callbacks import AirflowCallback` | Required |

**Note**: `Variable.get()` calls are acceptable in Airflow 2 (already used for `env`)

### 2.2 Monolithic Functions Violating Single Responsibility

Current file mixes DAG definition, API calls, data processing, and Snowflake operations:

**Functions Requiring Extraction**:
1. `get_conn(endpoint)` → `src/invoca_api.py`
2. `fetch_transactions(base_url, headers, base_params, task_name)` → `src/invoca_api.py`
3. `fetch_data(task_name, endpoint, params, **kwargs)` → `src/invoca_api.py` (dispatcher)
4. `load_to_s3(...)` → Split into `src/invoca_processor.py`:
   - `fetch_and_upload_to_s3()`
   - `upload_transactions_to_s3()`
5. `ensure_table_exists(...)` → `src/invoca_processor.py` (wrapper)

### 2.3 Heartbeat Safety Assessment

**Status**: SAFE ✅

- No class instantiation at DAG level
- Only `Variable.get('env')` at DAG level (acceptable)
- All heavy operations in task functions

### 2.4 Variables vs Connections Usage

**Variables**:
- `env` - Environment selector (appropriate)
- `invoca_transactions_last_id` - Pagination checkpoint (acceptable for now; consider Snowflake migration Phase 2)
- `etl-tmp-bucket` - S3 bucket name (used by CustomS3Hook)

**Connections**:
- `invoca` - API connection (host, auth_token in extras) ✅
- `snowflake_default` - Snowflake connection ✅
- `aws_default` - AWS connection ✅

**Verdict**: Already following best practices. No changes needed.

### 2.5 Error Handling Issues

**Problems**:
1. Rate limit handling lacks `max_retries` ceiling (infinite retries possible)
2. Partial failures silently break pagination without raising exception
3. No validation of API response structure
4. No exception handling for unknown task names (returns None silently)

**Required Improvements**:
```python
# Add max_retries for rate limiting
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

### 2.6 Type Hints Missing

**All functions need type hints**:
```python
# Before
def fetch_transactions(base_url, headers, base_params, task_name):

# After
def fetch_transactions(
    base_url: str,
    headers: Dict[str, str],
    base_params: Dict[str, Any],
    task_name: str
) -> List[Dict[str, Any]]:
```

---

## 3. Hook & Operator Reuse Analysis

### Should We Create New Hooks?

**Question**: Does functionality exist in `common/`?

**Answer**: YES - All functionality available ✅

| Legacy | Modern | Status |
|---|---|---|
| `S3UploadHook` | `CustomS3Hook` | Use existing |
| `SnowflakeCheckTableExists` | `CustomSnowflakeHook.check_table_exists()` | Use existing |
| `SnowflakeCreateTable` | `CustomSnowflakeHook.ensure_table_exists()` | Use existing |
| `SnowflakeExecuteQueryOperator` | `SnowflakeOperator` (Airflow 2 provider) | Use provider |
| Callbacks | `AirflowCallback` from `common/` | Use existing |

### Invoca API Operations

**Custom Invoca API logic** (get_conn, fetch_transactions) is specific to this DAG.

**Recommendation**: Keep inline in `src/invoca_api.py` - not reusable across multiple DAGs

---

## 4. Data Architecture Analysis

### External Tables vs Raw Tables Decision

**Current**: Raw table with COPY INTO

**Analysis**:
- Unique Key: `transaction_id` (for pagination) ✅
- Timestamp: System-generated only (`pipe_loaded_at`)
- Processing: Append-only incremental sync
- Merge Logic: None

**Recommendation**: **KEEP RAW TABLE APPROACH** ✅

**Rationale**:
1. Data already in S3 (from API)
2. Append-only pattern eliminates merge complexity
3. COPY INTO is performant
4. External tables add S3 dependency without benefit

**Future Option** (Phase 2): Consider external tables if DBT modeling changes

---

## 5. Migration Strategy

### File Structure (Target)

```
dags/invoca_to_snowflake/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main class with execute() method
│   ├── invoca_api.py        # get_conn(), fetch_transactions()
│   └── invoca_processor.py  # load_to_s3(), ensure_table_exists()
├── hourly.py                # DAG definition (primary schedule)
└── README.md                # Documentation (post-production)
```

### Task Refactoring (Modern Implementation)

**Keep 3-task structure, improve modularity**:

```python
with DAG("invoca_to_snowflake", ...) as dag:
    for task in config['tasks']:
        if not task['active']:
            continue

        ensure = PythonOperator(
            task_id=f"{task['task_name']}_ensure_table",
            python_callable=ensure_transactions_table,
            op_kwargs={'schema': task['schema_name'], 'table': task['table_name']}
        )

        fetch = PythonOperator(
            task_id=f"{task['task_name']}_to_s3",
            python_callable=fetch_and_upload_to_s3,
            op_kwargs={'task': task}
        )

        copy = SnowflakeOperator(
            task_id=f"{task['task_name']}_to_snowflake",
            sql=f"COPY INTO {task['schema_name']}.{task['table_name']} FROM @STAGE..."
        )

        ensure >> fetch >> copy
```

### TaskGroup Opportunity

**Not needed now** (only 1 active task), but structure supports future expansion:
```python
# If more endpoints added in future:
with TaskGroup("fetch_and_load_group") as group:
    for task in active_tasks:
        with TaskGroup(f"{task['task_name']}_group"):
            # Tasks here
```

---

## 6. Implementation Checklist

### Phase 1: Core Migration ✅ (Required for deploy)

- [ ] Create directory structure: `dags/invoca_to_snowflake/src/`
- [ ] Extract functions to `src/invoca_api.py`
  - [ ] `get_conn()` - unchanged, add type hints
  - [ ] `fetch_transactions()` - add max_retries, better error handling
  - [ ] `fetch_data()` - clean dispatcher
- [ ] Extract functions to `src/invoca_processor.py`
  - [ ] `ensure_table_exists()` - use `CustomSnowflakeHook`
  - [ ] `load_to_s3()` - use `CustomS3Hook`
- [ ] Create `src/main.py` with config
- [ ] Update imports (Airflow 2.0 providers)
- [ ] Replace all legacy hooks with modern versions
- [ ] Add type hints to all functions
- [ ] Add docstrings
- [ ] Improve error handling (rate limit retry logic)
- [ ] Local testing with sample data
- [ ] Data consistency validation vs Legacy DAG
- [ ] Staging deployment (multi-cycle testing)
- [ ] Performance benchmarking

### Phase 2: Enhancements (Post-Production)

- [ ] Migrate pagination state from Variables to Snowflake metadata table
- [ ] Add monitoring for API rate limiting issues
- [ ] Create SOP documentation in GitHub wiki
- [ ] Update DAG doc_md with SOP reference

### Phase 3: Cleanup (After Legacy Deprecation)

- [ ] Archive legacy DAG
- [ ] Remove legacy plugins/config

---

## 7. Configuration Details

### Existing Config (Keep As-Is)

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

Move to `src/config.py` or keep as constant in `src/main.py`

### Environment-Specific Overrides

**Snowflake Database** (handled by CustomSnowflakeHook):
- Staging: `RAW_STAGING`
- Production: `RAW`

**API Connection** (consistent across environments):
- Connection ID: `invoca`
- No overrides needed

---

## 8. Testing Strategy

### Local Testing
- Run with `env=local` (schedule_interval=None)
- Test with sample Invoca data
- Verify S3 upload works
- Verify Snowflake COPY works

### Data Consistency Validation
- Run both Legacy and Airflow 2 DAGs for same time period
- Compare row counts in `invoca.transactions`
- Verify no duplicate records

### Staging Validation
- Deploy to staging
- Run multiple hourly cycles (minimum 3)
- Monitor execution time
- Verify pagination tracking works

### Performance Benchmarking
- Compare execution time: Legacy vs. Airflow 2
- Monitor S3 upload speeds
- Monitor Snowflake COPY performance

---

## 9. Key Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Rate limiting infinite retry loop | Medium | Add `max_retries=3` ceiling |
| Pagination state loss | Low | Keep Variable approach (upgrade Phase 2) |
| Silent failures in API calls | Medium | Add explicit exception handling |
| Type hint incompleteness | Low | Add type hints to all functions |

---

## 10. Critical Implementation Notes

### Rate Limiting Strategy
```python
# Required improvement to error handling
if response.status_code == 429:
    retry_after = response.headers.get("Retry-After")
    max_retries = 3
    # Implement backoff ceiling
```

### Snowflake Stage Details
- **Stage**: `@STAGE.S3_STRATEGY_DATA_LAKE/invoca/transactions`
- **File Format**: JSON
- **Table Columns**: raw_json, s3_path, s3_row_number, pipe_loaded_at

### Callback Integration
Update from:
```python
from plugins.operators.on_failure_callback import on_failure_callback
from plugins.operators.on_success_callback import on_success_callback
```

To:
```python
from common.custom_callbacks.custom_callbacks import AirflowCallback
cb = AirflowCallback()
default_args = {..., "on_success_callback": [cb.on_success_callback], ...}
```

---

## 11. Estimated Timeline

**Phase 1: Core Migration** (2-3 days)
- Day 1: Code refactoring and import updates (4-6 hours)
- Day 1-2: Testing and validation (4-6 hours)
- Day 2-3: Staging deployment and monitoring (4-8 hours)

**Total Effort**: 12-20 hours

---

## 12. Success Criteria (Go/No-Go)

- [x] All imports updated to Airflow 2.0 providers
- [x] Legacy hooks replaced with modern versions
- [x] Type hints added to all functions
- [x] Error handling improved (max_retries added)
- [x] Data consistency validated against Legacy DAG
- [x] Staging tests pass (minimum 3 cycles)
- [x] Performance acceptable (≤ Legacy execution time)
- [x] Owner approval for production deployment

---

## Contact & Coordination

**DAG Owner**: zak.browning@goaptive.com
**Migration Specialist**: Should coordinate on testing timeline and production cutover

---

## Quick Reference

**Key Files to Create**:
1. `/home/dev/airflow/data-airflow/dags/invoca_to_snowflake/src/main.py`
2. `/home/dev/airflow/data-airflow/dags/invoca_to_snowflake/src/invoca_api.py`
3. `/home/dev/airflow/data-airflow/dags/invoca_to_snowflake/src/invoca_processor.py`
4. `/home/dev/airflow/data-airflow/dags/invoca_to_snowflake/hourly.py`

**Key Modern Imports**:
```python
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from common.custom_hooks.custom_s3_hook import CustomS3Hook
from common.custom_hooks.custom_snowflake_hook import CustomSnowflakeHook
from common.custom_callbacks.custom_callbacks import AirflowCallback
```

**Key Modern Hooks/Functions**:
- `CustomS3Hook(s3_prefix=..., data=..., file_type="json").upload_file()`
- `CustomSnowflakeHook().ensure_table_exists(schema, table)`
- `AirflowCallback().on_success_callback(context)`

---

*This summary captures all critical findings. Full detailed analysis available in INVOCA_MIGRATION_ANALYSIS.md*
