# Invoca to Snowflake - Airflow 1.0 to 2.0 Migration Analysis

**Date**: October 24, 2025
**Scope**: Migrate `/home/dev/airflow/data-airflow-legacy/dags/invoca_to_snowflake.py`
**Owner**: zak.browning@goaptive.com

---

## 1. CURRENT STRUCTURE ASSESSMENT

### 1.1 DAG Configuration

**File**: `invoca_to_snowflake.py` (108 lines)

**Schedule Configuration:**
```
Local:   schedule_interval = None
Staging: schedule_interval = "30 7-23 * * *" (hourly at minute 30 between 7 AM - 11 PM)
Production: schedule_interval = "0 7-23 * * *" (hourly between 7 AM - 11 PM)
```

**DAG Parameters:**
- Owner: `zak.browning@goaptive.com`
- Start Date: February 1, 2024
- Retries: 1 with 3-minute delay
- Concurrency: 3
- Max Active Runs: 1
- Catchup: False
- Tags: `["Invoca", "Snowflake", "S3", 'MigratedToAF2']` (NOTE: Already tagged as 'MigratedToAF2' despite being Legacy)

**Documentation**: References legacy wiki SOP

### 1.2 Task Breakdown and Dependencies

Current DAG generates tasks dynamically from configuration:

```
tasks = [
  {
    'active': 1,
    'task_name': 'transactions',
    'endpoint': '2020-10-01/advertisers/transactions',
    'schema_name': 'invoca',
    'table_name': 'transactions'
  }
]
```

**Current Task Chain (for each enabled task):**
```
ensure_table_exists → data_to_s3 → s3_to_snowflake
```

**Tasks Generated Per Endpoint:**
1. `{task_name}_ensure_table_exists` - PythonOperator
2. `{task_name}_to_s3` - PythonOperator
3. `{task_name}_to_snowflake` - SnowflakeExecuteQueryOperator

Currently only 1 active task (transactions), but structure supports multiple.

### 1.3 Data Flow and Processing Logic

**Data Pipeline:**

```
Invoca API (pagination-based)
  ↓
fetch_transactions() [Pagination with rate limiting]
  ↓
S3 Upload (JSON format)
  ↓
S3 COPY into Snowflake (raw table)
```

**Key Processing Details:**

1. **API Fetching** (`fetch_transactions()`):
   - Pagination uses `start_after_transaction_id` parameter
   - Incremental sync via Airflow Variable: `invoca_{task_name}_last_id`
   - Handles rate limiting (429 status code) with 30-second backoff
   - Normal requests have 3-second delays
   - Default start date: 2024-02-01 (only used if no variable set)

2. **S3 Upload** (`load_to_s3()`):
   - Uses `S3UploadHook` from plugins
   - Uploads as JSON format
   - S3 prefix: `{schema_name}/{table_name}` = `invoca/transactions`

3. **Snowflake Loading** (SnowflakeExecuteQueryOperator):
   - COPY INTO raw table from S3 stage
   - Loads: `raw_json`, `s3_path`, `s3_row_number`, `pipe_loaded_at`
   - Stage: `@STAGE.S3_STRATEGY_DATA_LAKE/invoca/transactions`
   - File format: JSON

### 1.4 Custom Hooks/Operators Used

**Deprecated Imports:**
```python
from plugins.operators.snowflake_execute_query import SnowflakeExecuteQueryOperator
from plugins.hooks.s3_upload_hook import S3UploadHook
from plugins.hooks.snowflake_custom import (
    SnowflakeCheckTableExists,
    SnowflakeCreateTable,
    SnowflakeGetMaxTimestamp
)
from plugins.operators.on_failure_callback import on_failure_callback
from plugins.operators.on_success_callback import on_success_callback
```

**Status of Legacy Hooks:**
- `S3UploadHook`: Custom legacy implementation (will be replaced with `CustomS3Hook`)
- `SnowflakeCheckTableExists`: Legacy custom implementation
- `SnowflakeCreateTable`: Legacy custom implementation
- Callbacks: Legacy callback system (will use modern `CustomCallbacks`)

---

## 2. PRE-MIGRATION ASSESSMENT CHECKLIST

### 2.1 Hook and Operator Analysis

**Does a new hook need to be created?**
- **NO** - All functionality is available in existing custom hooks
  - `CustomS3Hook` (in modern codebase) replaces `S3UploadHook`
  - `CustomSnowflakeHook.ensure_table_exists()` replaces legacy Snowflake hooks
  - Invoca API operations are specific enough to keep inline

**Does an existing Legacy hook need modification?**
- **NO** - The modern custom hooks are production-ready and compatible

**Should existing custom hooks/operators be reused?**
- **YES**
  - `CustomS3Hook` - Use instead of legacy `S3UploadHook`
  - `CustomSnowflakeHook` - Use instead of legacy Snowflake hooks
  - Custom callbacks from `common/custom_callbacks/`

**Are connections/variables different between environments?**
- **YES - Snowflake database differs:**
  - Local/Staging: `RAW_STAGING`
  - Production: `RAW`
  - **Action**: This is already handled by `CustomSnowflakeHook` (checks `env` variable)

- **NO - API Connection is consistent:**
  - Connection ID: `invoca` (same across environments)
  - Stores: `host`, `account_number`, `auth_token` in extras

- **YES - Pagination tracking differs:**
  - Stored in Variable: `invoca_{task_name}_last_id`
  - **Recommendation**: Consider storing in Snowflake instead for better versioning

### 2.2 Data and Modeling

**Is data already modeled in DBT?**
- **UNKNOWN** - Need to verify if Invoca data exists in DBT models
  - Likely: `models/raw/invoca/` or similar
  - Should verify before migration

**What are the unique key and timestamp fields?**
- **Unique Key**: `transaction_id` (used for pagination)
- **Timestamp**: Appears to be `pipe_loaded_at` (when loaded to Snowflake)
- **Data Age**: Tracked via `start_after_transaction_id` variable

**Does this require incremental loads, full reloads, or both?**
- **INCREMENTAL ONLY**
  - Uses `start_after_transaction_id` for pagination
  - Never does full reloads (respects last sync point)
  - Best practice: Good for this type of API

### 2.3 API Performance Analysis

**Does it make many API calls that could be async?**
- **PARTIALLY**
  - Single sequence of paginated calls (not ideal for async)
  - Could batch multiple endpoints if more were active
  - Currently only 1 active task (transactions)
  - **Recommendation**: Current implementation is acceptable. Async would add complexity without much benefit for single pagination sequence.

**Does it run slowly relative to schedule?**
- **YES - Potential Performance Concern**
  - Hourly schedule (7 AM - 11 PM = 16 hours × 60 min = 960 requests/day)
  - Built-in delays: 3 seconds per paginated request
  - With large result sets, could approach schedule interval
  - **Recommendation**: Monitor execution time. Consider adding batch size limits if needed.

---

## 3. REQUIRED CHANGES IDENTIFICATION

### 3.1 Import Updates (Airflow 2.0 Providers)

| Legacy Import | Modern Import | Notes |
|---|---|---|
| `from airflow.operators.python_operator import PythonOperator` | `from airflow.operators.python import PythonOperator` | Simplified path |
| `from airflow.models import Variable` | `from airflow.models import Variable` | No change (still valid in AF2) |
| `from plugins.operators.snowflake_execute_query import SnowflakeExecuteQueryOperator` | `from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator` | Use standard provider |
| `from plugins.hooks.s3_upload_hook import S3UploadHook` | `from common.custom_hooks.custom_s3_hook import CustomS3Hook` | Use modern custom hook |
| `from plugins.hooks.snowflake_custom import *` | `from common.custom_hooks.custom_snowflake_hook import CustomSnowflakeHook` | Modern centralized hooks |
| Callbacks from plugins | `from common.custom_callbacks.custom_callbacks import CustomCallbacks` | Modern callback system |

### 3.2 Monolithic Functions to Refactor

**File Structure:**
- Current: All code mixed in single file + config imports
- Target: Proper directory structure with modular functions

**Functions to Extract:**

1. **`get_conn(endpoint)` → Extract to `src/invoca_api.py`**
   - Clean, no changes needed beyond type hints

2. **`fetch_transactions(base_url, headers, base_params, task_name)` → Extract to `src/invoca_api.py`**
   - Add proper error handling for edge cases
   - Consider rate limit retry logic improvements
   - Add type hints throughout

3. **`fetch_data(task_name, endpoint, params, **kwargs)` → Extract to `src/invoca_api.py`**
   - This is a dispatcher; could be simplified

4. **`load_to_s3(task_name, endpoint, params, schema_name, table_name, **kwargs)` → Extract to `src/invoca_processor.py`**
   - Split into two functions:
     - `fetch_and_upload_to_s3()` - Get data and upload
     - `upload_transactions_to_s3()` - Specific implementation
   - Use `CustomS3Hook` instead of legacy hook

5. **`ensure_table_exists()` → Extract to `src/invoca_processor.py`**
   - Use `CustomSnowflakeHook.ensure_table_exists()` instead
   - Clean up wrapper

**Example Refactored Structure:**
```
invoca_to_snowflake/
├── src/
│   ├── main.py                  # Main class with execute() method
│   ├── invoca_api.py            # API interaction functions
│   └── invoca_processor.py      # Data processing functions
├── daily.py                     # DAG definition (keep schedule name)
└── hourly.py                    # Secondary schedule (if needed)
```

### 3.3 Variables → Connections Conversions

**Current Variable Usage:**
```python
invoca_{task_name}_last_id = Variable.get('invoca_transactions_last_id')
```

**Status**: This is a pagination checkpoint, not a configuration variable.

**Options**:
1. **Keep as Variable** (acceptable): Simple state tracking
2. **Store in Snowflake** (better): Track in audit/metadata table
3. **Use S3 + XCom** (complex): Overkill for single value

**Recommendation**: Keep as Variable for now. Migration to Snowflake can happen in phase 2.

**Current Connection Usage:**
```python
conn = BaseHook.get_connection('invoca')
```

**Connection Structure:**
- Connection ID: `invoca`
- Host: API base URL (e.g., `https://api.invoca.com/api`)
- Login: Not used (empty)
- Password: Not used (empty)
- Extra JSON:
  - `account_number`: Invoca account number
  - `auth_token`: API authentication token

**Status**: Already using Connections (good practice). No changes needed.

### 3.4 Heartbeat Safety Issues

**Current Implementation Assessment:**

Classes instantiated at DAG level:
- None (functions are used, not class instances)

Database/API calls at DAG level:
- `Variable.get('env')` - ACCEPTABLE (lightweight, expected in Airflow 2)

**Verdict**: DAG is already heartbeat-safe. No issues here.

### 3.5 Type Hints Missing

**Current State**: No type hints in any function

**Functions Requiring Type Hints:**

```python
# Before
def get_conn(endpoint):
    ...

# After
def get_conn(endpoint: str) -> Tuple[str, Dict[str, str]]:
    ...
```

**All Functions Needing Hints:**
- `get_conn(endpoint: str) -> Tuple[str, Dict[str, str]]`
- `fetch_transactions(...) -> List[Dict[str, Any]]`
- `fetch_data(...) -> Optional[List[Dict[str, Any]]]`
- `load_to_s3(...) -> Optional[str]`
- `ensure_table_exists(schema_name: str, table_name: str, **kwargs: Any) -> None`

### 3.6 Documentation Gaps

**Missing Documentation:**
- No docstrings on any functions
- No description of API pagination logic
- No error handling documentation
- No rate limiting strategy explanation

**Required Additions:**
```python
def fetch_transactions(
    base_url: str,
    headers: Dict[str, str],
    base_params: Dict[str, Any],
    task_name: str
) -> List[Dict[str, Any]]:
    """
    Fetch transactions from Invoca API using pagination.

    This function implements incremental syncing via the start_after_transaction_id
    parameter, allowing for stateful pagination across multiple DAG runs.

    :param base_url: The Invoca API base URL
    :param headers: Request headers including Authorization token
    :param base_params: Base parameters for API requests
    :param task_name: Task name for variable storage (e.g., 'transactions')
    :return: List of transaction dictionaries from API
    :raises: Logs errors but doesn't raise on partial failures

    Rate Limiting:
    - Normal request delay: 3 seconds between paginated requests
    - 429 (Rate Limit) response: 30-second backoff before retry
    - No exponential backoff implemented (could be improved)
    """
```

### 3.7 Error Handling Improvements Needed

**Current Issues:**

1. **Incomplete Error Handling in `fetch_transactions()`**:
   ```python
   # Current: breaks on error but doesn't raise
   if response.status_code != 200:
       logger.error(f"Failed to fetch data: {response.text}")
       if response.status_code == 429:
           time.sleep(30)
       else:
           break  # Just stops, no exception
   ```
   - Should raise exception on final failure
   - No limit on 429 retries

2. **Silent Failures**:
   ```python
   # Current: Silently returns empty list on error
   if task_name == 'transactions':
       transactions = fetch_transactions(...)
   else:
       logger.error(f"Task {task_name} not found.")
       return None
   ```
   - Should raise exception for unknown task

3. **Missing Validation**:
   - No check for None data before S3 upload
   - No validation of response structure

**Improvements Needed:**
```python
def fetch_transactions(...) -> List[Dict[str, Any]]:
    """..."""
    max_retries = 3
    retry_count = 0

    while has_more_data:
        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 429:
                if retry_count < max_retries:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.info(f"Rate limited. Waiting {retry_after}s before retry")
                    time.sleep(retry_after)
                    retry_count += 1
                    continue
                else:
                    raise Exception(f"Max retries exceeded after rate limiting")

            response.raise_for_status()

            # Process response...
            retry_count = 0  # Reset on success

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}", exc_info=True)
            raise
```

---

## 4. MIGRATION STRATEGY

### 4.1 Recommended File Structure

```
dags/invoca_to_snowflake/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main class with execute() method
│   ├── invoca_api.py        # API interactions (get_conn, fetch_transactions)
│   └── invoca_processor.py  # Data processing (load to S3, table management)
├── hourly.py                # DAG for hourly schedule (primary)
├── daily.py                 # DAG for daily schedule (secondary, if needed)
└── README.md                # Documentation (create after production deploy)
```

### 4.2 Task Breakdown Plan

**Recommendation**: Keep 3-task structure but improve modularity

```
┌────────────────────────────────────────────┐
│ hourly.py (DAG)                            │
├────────────────────────────────────────────┤
│                                            │
│  for each active task in config:           │
│    ┌─────────────┐      ┌────────────┐    │
│    │  Ensure     │      │  Fetch &   │    │
│    │  Table      │───→  │  Load to   │    │
│    │  Exists     │      │  S3        │    │
│    └─────────────┘      └────────────┘    │
│                             │              │
│                             ↓              │
│                      ┌────────────────┐   │
│                      │ Copy from S3   │   │
│                      │ to Snowflake   │   │
│                      └────────────────┘   │
└────────────────────────────────────────────┘
```

**Modern Implementation:**
- Task 1: `ensure_transactions_table` - Python operator using `CustomSnowflakeHook`
- Task 2: `fetch_transactions_to_s3` - Python operator using refactored functions
- Task 3: `copy_transactions_to_snowflake` - SnowflakeOperator (native Airflow 2)

### 4.3 External Table vs Raw Table Decision

**Current Implementation**: Raw table with COPY INTO

**Analysis**:
- Data: JSON records with pagination-based incrementing ID
- Unique Key: `transaction_id` (available)
- Timestamp: Not explicitly in data (only system timestamp)
- Processing: Incremental append, no complex merge logic

**Recommendation**: **Keep Raw Table Approach**

**Reasons**:
1. Data is already in S3 (from Invoca API fetch)
2. Incremental loading via pagination (append-only pattern)
3. No complex deduplication needed
4. COPY INTO is performant for this workload
5. External table would add S3 dependency without benefit

**Alternative (Phase 2)**: Could implement external tables if DBT modeling changes

### 4.4 Hook/Operator Reuse Plan

**Replace All Legacy Hooks with Modern Versions:**

| Legacy | Modern | Usage |
|---|---|---|
| `S3UploadHook` | `CustomS3Hook` | Upload transactions JSON to S3 |
| `SnowflakeCheckTableExists` | `CustomSnowflakeHook.check_table_exists()` | Check if invoca table exists |
| `SnowflakeCreateTable` | `CustomSnowflakeHook.create_table()` | Create invoca raw table |
| Custom callbacks | `CustomCallbacks` from `common/` | on_success and on_failure |

**New Operators to Use:**
- `SnowflakeOperator` (from `airflow.providers.snowflake`) for COPY INTO

### 4.5 TaskGroup Opportunities

**Current Structure**: Only 1 active task (transactions)

**Opportunity for Future Growth**:
```python
# If more endpoints are added:
with TaskGroup("fetch_and_load_group") as fetch_group:
    for task in active_tasks:
        with TaskGroup(f"{task['task_name']}_group") as task_group:
            ensure = PythonOperator(...)
            fetch = PythonOperator(...)
            copy = SnowflakeOperator(...)
            ensure >> fetch >> copy
```

**Current Recommendation**: Keep simple without TaskGroup (only 1 active task). Add TaskGroup if more endpoints added.

### 4.6 Configuration Migration

**Current Config File** (`config/invoca/config.py`):
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

**Status**: This is clean and should be kept as-is. Move to `src/config.py` or keep as module-level constant.

---

## 5. IMPLEMENTATION ROADMAP

### Phase 1: Core Migration
- [ ] Create directory structure
- [ ] Refactor functions to modular design
- [ ] Update all imports to Airflow 2.0 providers
- [ ] Replace legacy hooks with modern versions
- [ ] Add type hints throughout
- [ ] Add comprehensive docstrings
- [ ] Improve error handling with retry logic
- [ ] Local testing with sample data
- [ ] Compare output with Legacy DAG

### Phase 2: Enhancement (Post-Production)
- [ ] Migrate pagination state from Variables to Snowflake metadata table
- [ ] Add monitoring/alerting for rate limiting
- [ ] Implement async API calls if performance issues identified
- [ ] Create SOP documentation in GitHub wiki
- [ ] Update DAG doc_md reference

### Phase 3: Cleanup (After Legacy Deprecation)
- [ ] Remove legacy DAG from production
- [ ] Archive Legacy configuration

---

## 6. CRITICAL MIGRATION NOTES

### 6.1 Breaking Changes to Handle

1. **Import Path Changes** (covered above)
2. **Callback System** - Must update to use `CustomCallbacks` from `common/`
3. **Custom Hook Methods** - `CustomSnowflakeHook` has different method signatures
4. **Stage Name** - Verify S3 stage name matches between environments

### 6.2 Testing Strategy

**Before Production Deployment:**

1. **Local Testing**:
   - Run with `env = local` (schedule_interval = None)
   - Test with sample Invoca data
   - Verify S3 upload works
   - Verify Snowflake COPY works

2. **Data Consistency Validation**:
   - Run both Legacy and Airflow 2 DAGs for same time period
   - Compare row counts in `invoca.transactions` table
   - Verify no duplicate records

3. **Staging Validation**:
   - Deploy to staging environment
   - Run multiple hourly cycles
   - Monitor execution times
   - Verify pagination tracking works correctly

4. **Performance Benchmarking**:
   - Compare execution time: Legacy vs. Airflow 2
   - Monitor S3 upload speeds
   - Monitor Snowflake COPY performance

### 6.3 Known Constraints

1. **Rate Limiting**: Invoca API has rate limits (3sec delays built in)
   - Current implementation handles 429 but doesn't have backoff ceiling
   - Recommendation: Add `max_retries` parameter

2. **Pagination Statefulness**: Relies on Airflow Variable
   - If variable is lost/reset, DAG will reprocess old data
   - Recommendation (Phase 2): Move to Snowflake metadata table

3. **Timestamp Field Missing**: No explicit timestamp in API response
   - Using `pipe_loaded_at` (system timestamp when loaded)
   - Could miss data if not processed in order

### 6.4 Backward Compatibility

**Breaking for Legacy DAG Users**:
- None - New DAG will coexist until Legacy is deprecated
- Both can run simultaneously during transition period

**Connection/Variable Compatibility**:
- Invoca connection ID remains same: `invoca`
- Variables remain same: `invoca_{task_name}_last_id`
- No changes needed in Airflow infrastructure

---

## 7. SPECIFIC RECOMMENDATIONS

### 7.1 Short-term (Required for Migration)
1. Update all imports to Airflow 2.0 providers
2. Replace legacy hooks with modern custom hooks
3. Add type hints and docstrings
4. Improve error handling (especially rate limiting)
5. Test thoroughly before production

### 7.2 Medium-term (Phase 2)
1. Migrate pagination checkpoint from Variable to Snowflake
2. Add monitoring for API rate limiting issues
3. Consider async API calls if hourly schedule becomes bottleneck
4. Create comprehensive SOP documentation

### 7.3 Long-term (Phase 3+)
1. Evaluate if external tables would benefit performance
2. Consider consolidating multiple Invoca endpoints if added
3. Evaluate if data modeling in DBT changes architecture needs

---

## 8. OWNER AND CONTACT

**DAG Owner**: zak.browning@goaptive.com

**Migration Specialist**: Should coordinate with owner on:
- Testing strategy and timeline
- Staging environment deployment
- Production cutover plan
- Legacy DAG deprecation schedule

---

## APPENDIX A: Variable Reference

**Airflow Variables Used:**
```
env                                    # Environment (local/staging/prod)
invoca_transactions_last_id           # Last transaction ID for pagination
etl-tmp-bucket                        # S3 bucket for temporary uploads (used by CustomS3Hook)
```

**Airflow Connections Used:**
```
invoca                                # Invoca API connection
  - Host: API base URL
  - Extra:
    - account_number: Invoca account identifier
    - auth_token: API authentication token
snowflake_default                     # Snowflake connection (used by CustomSnowflakeHook)
aws_default                           # AWS connection (used by CustomS3Hook)
```

---

## APPENDIX B: API Details

**Invoca API Endpoint:**
```
GET {host}/{endpoint}/{account_number}.json
  ?include_columns=<columns>
  &start_after_transaction_id=<transaction_id> (for pagination)
  &from=<date> (YYYY-MM-DD format, only for first request)
  &to=<date>
```

**Rate Limiting:**
- Status Code: 429 (Too Many Requests)
- Response Header: `Retry-After` (seconds to wait)
- Default Backoff: 30 seconds if no Retry-After header

**Response Format:**
- Array of transaction objects
- Empty array when no more data
- Each object includes `transaction_id` for next pagination

---

## APPENDIX C: Snowflake Stage Details

**Stage**: `@STAGE.S3_STRATEGY_DATA_LAKE/invoca/transactions`

**File Format**: JSON (strip_outer_array = true)

**Table Structure** (after COPY INTO):
```sql
CREATE TABLE invoca.transactions (
    raw_json VARIANT,
    s3_path VARCHAR,
    s3_row_number NUMBER,
    pipe_loaded_at TIMESTAMP_TZ
)
```

---

## SUMMARY

**Migration Complexity**: **MEDIUM**
- Clear data flow
- Well-structured current code
- Limited custom hooks/operators
- No complex dependencies

**Estimated Effort**: **2-3 days**
- Day 1: Code refactoring and migration (4-6 hours)
- Day 1-2: Testing and validation (4-6 hours)
- Day 2-3: Staging deployment and monitoring (4-8 hours)

**Risk Level**: **LOW**
- Simple append-only pattern
- No data loss risk
- Can run both DAGs simultaneously
- Incremental state tracking minimizes corruption risk

**Go-No-Go Decision Points:**
- [ ] Data consistency validated against Legacy DAG
- [ ] Staging tests pass with multiple cycles
- [ ] Performance benchmarks acceptable
- [ ] Owner approval for production deployment

---

*This analysis provides the foundation for a successful migration. The actual implementation should follow the patterns and guidelines established in the modern Airflow 2 deployment.*
