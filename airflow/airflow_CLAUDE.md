# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains our self-managed Apache Airflow 2 deployment on AWS EKS. This document serves dual purposes:
1. **Operational Guide**: Instructions for working with the existing Airflow 2 environment
2. **Migration Guide**: Comprehensive guidance for migrating DAGs from Airflow Legacy to Airflow 2

## Local Development Setup
1. Login to AWS:
   ```bash
   python3 infrastructure/scripts/update_aws_sso_creds.py data-staging
   # For Intel Mac: bash infrastructure/scripts/login_to_aws_intel_mac.sh
   ```
2. Create override file: `bash scripts/create_override_file.sh`
3. Build and run: `docker build -t docker-airflow-2 . && docker compose up -d`
4. Refresh Airflow Variables & Connections: `python3 scripts/refresh_pg_db.py`
5. Load AWS creds to Airflow: `python3 scripts/load_aws_to_airflow.py`

## Common Commands
- **Build Docker**: `docker build -t docker-airflow-2 .`
- **Run Docker**: `docker compose up -d`
- **Lint**: `pip install flake8 && flake8` (required before PR merge)
- **Refresh DB**: `python3 scripts/refresh_pg_db.py`
- **Load AWS**: `python3 scripts/load_aws_to_airflow.py`
- **Push to ECR**: `bash scripts/push_image_to_ecr.sh`
- **Hard reset staging**: `bash scripts/hard_reset_staging.sh`
- **Health Check**: `bash scripts/health_check.sh` (comprehensive EKS Airflow health validation)
- **Auto-Remediation**: `AUTO_FIX=true bash scripts/health_check.sh` (automatically fixes common pod issues)
- **Dry Run Fix**: `DRY_RUN=true AUTO_FIX=true bash scripts/health_check.sh` (shows what would be fixed)

## Architecture Overview

This is a self-managed Apache Airflow deployment on AWS EKS with the following structure:

### DAG Architecture
- **Directory Structure**: Each DAG has its own directory under `dags/` named by purpose (e.g., `pestroutes/`, `genesys_to_snowflake/`)
- **DAG Files**: Named by schedule frequency (`daily.py`, `intraday.py`, `hourly.py`, `nightly.py`, `weekly.py`, `monthly.py`)
- **Entry Points**: All DAGs follow a standard pattern with `src/main.py` containing a `Main` class with `execute()` method
- **Templates**: Use `_dag_template/` or `_dag_taskflow_template/` as starting points for new DAGs

### General Data Pipeline Process

Our standard data pipeline follows this pattern:

1. **Airflow 2**: Fetch data from source and load to S3
2. **DBT**: Fetch data from S3 (usually JSON format) and normalize it, typically using external tables

#### External Tables vs Raw Tables

- **Preferred**: External tables pointing to S3 data (handled by DBT)
- **Alternative**: Airflow loads to S3 AND directly to raw Snowflake tables (when external tables don't fit)
- **DBT Models**:
  - External table approach: `models/raw/pestroutes` (pulls from `raw.external_tables` schema)
  - Direct load approach: `models/clean/google_sheets` (pulls from `raw` database)

### Common Components
- **Hooks**: Custom reusable connection handlers in `common/custom_hooks/` (Snowflake, S3, PestRoutes, etc.)
- **Operators**: Custom reusable task operators in `common/custom_operators/` (cross-DB, Spark, ETL operators)
- **Callbacks**: Standard success/failure callbacks in `common/custom_callbacks/`

### Infrastructure
- **EKS Cluster**: Self-managed Airflow on AWS EKS with separate node groups for workers and scheduler (which also hosts webserver), and optional GPU nodes
- **Data Flow**: Typically source → S3 → Snowflake pattern for data ingestion
- **Batch Processing**: Default batch size of 250,000 records for large data operations (configurable via `batch_size` parameter)

## Code Style Guidelines

### Clean Code Principles

**Mandatory Requirements:**
- **Meaningful Names**: Descriptive, unambiguous names for variables, functions, and classes
- **Small Functions**: Keep functions focused on a single task
- **Sparse Comments**: Code should be self-explanatory; comments only when necessary
- **Consistent Style**: Follow established coding patterns
- **Proper Error Handling**: Graceful error handling with meaningful messages
- **DRY Principle**: Avoid code duplication through abstraction
- **Single Responsibility**: Each class/module should have one reason to change
- **Readable Code**: Easy to read, understand, and maintain
- **Flake8 Compliance**: All Python code must pass flake8 linting standards for deployment
- **Heartbeat-Safe Code**: Avoid operations in DAG-level code that run on Airflow's heartbeat

### Linting Standards

- Ensure that a new line is always left at the end of any Python file

### Type Hints (Required)

Use Python type hints (Optional, List, Dict, Union) for all functions and methods:

```python
from typing import Optional, List, Dict, Union

def example_function(param1: int, param2: Optional[str]) -> Union[str, None]:
    """
    Always include comprehensive docstrings.

    :param param1: An integer parameter
    :param param2: An optional string parameter
    :return: A formatted string if param2 provided, otherwise None
    """
    if param2:
        return f"Param1 is {param1} and Param2 is {param2}"
    return None
```

### File Structure Standards

Each DAG should follow a standard pattern of having its own directory in the dags directory. The DAG file(s) should be named to communicate what the schedule of that DAG is. For example, to create a DAG to collect sales rep data, create and name the new directory `sales_rep_data_to_s3`, and the DAG file `intraday.py`.

The DAG might need to run additional code outside of the DAG file, so put all that code into a `src` directory within the DAG directory. For all situations like this, name the class for the task code `main` and the Python callable function `execute`.

The files in `common` should be rarely changed. The purpose of this code is to be highly reusable by any of the other DAGs. Hooks & operators should not be doing obscure things like formatting data, or getting a date from a database. They should be used to load data from a database or loading files to a destination.

```
dags/
├── my_pipeline_name/
│   ├── src/                 # Reusable code for the DAG's tasks
│   │   ├── main.py          # Standard entry point class/function
│   │   ├── additional_code.py
│   │   └── sql/
│   │       └── query.sql
│   ├── daily.py             # DAG file named by schedule
│   └── intraday.py          # DAG file named by schedule
├── common/
│   ├── custom_operators/
│   │   └── custom_operator.py
│   └── custom_hooks/
│       └── custom_hook.py
```

### Airflow Heartbeat Considerations

**Critical**: Avoid operations that run on Airflow's heartbeat (when DAGs are parsed):

**❌ Avoid in DAG-level code:**
- Database connections
- API calls
- File I/O operations
- Heavy `__init__` methods in classes instantiated by DAGs

**✅ Acceptable in DAG-level code:**
- `Variable.get()` calls (needed for environment-specific configuration)
- Lightweight variable assignments
- Simple imports

**Recommended Pattern:**
```python
# ❌ Avoid: Classes with __init__ methods instantiated in DAG files
class DataProcessor:
    def __init__(self, schema_name: str, table_name: str):
        self.schema_name = schema_name
        self.table_name = table_name
        # Even lightweight __init__ methods should be avoided if possible

# ✅ Preferred: Pass parameters directly to execution methods
class DataProcessor:
    def initialize(self, schema_name: str, table_name: str):
        # Heavy operations here, called only when task executes
        self.connection = create_database_connection()
        self.api_client = setup_api_client()
        self.schema_name = schema_name
        self.table_name = table_name

    def execute(self, schema_name: str, table_name: str, **kwargs):
        self.initialize(schema_name, table_name)  # Initialize only when task runs
        # Task logic here

# Or even better: Use functions instead of classes when appropriate
def process_data(schema_name: str, table_name: str, **kwargs):
    # All initialization and processing happens only when task executes
    connection = create_database_connection()
    api_client = setup_api_client()
    # Task logic here
```

### Class vs Function Design Guidelines

**Use Classes When:**
- **Shared State**: Multiple methods need access to the same configuration/connections
- **Complex Business Logic**: Multiple related operations that belong together conceptually
- **Reusable Patterns**: When you might instantiate multiple versions with different configurations
- **Method Interdependence**: When methods build on each other or share complex initialization

```python
# ✅ Good Class Usage - Multiple related methods with shared state
class PestRoutesProcessor:
    def fetch_appointments(self, office_id: str) -> List[Dict]:
        # Uses shared API client and configuration

    def fetch_customers(self, office_id: str) -> List[Dict]:
        # Uses shared API client and configuration

    def process_and_upload(self, data: List[Dict], table: str) -> str:
        # Shared by both above methods, uses shared S3 client
```

**Use Functions When:**
- **Single Purpose Tasks**: One clear job, minimal state needed
- **Simple Pipelines**: Linear process without complex interdependencies
- **Stateless Operations**: No shared configuration between operations
- **Quick Data Transformations**: Simple input → output transformations

```python
# ✅ Good Function Usage - Single purpose, no shared state
def fetch_datadog_tests(endpoint: str, params: Dict[str, Any]) -> List[Dict]:
    # Single purpose, no shared state needed

def upload_to_s3(data: List[Dict], schema: str, table: str) -> str:
    # Simple, stateless operation
```

**Migration Evaluation**: If a Legacy class has only one method or no shared state between methods, consider refactoring to functions. Classes should provide clear organizational or reusability benefits.

## Airflow Legacy to Airflow 2 Migration

### Migration Philosophy

**This migration represents a fresh start.** We're not just making Legacy code compatible with Airflow 2; we're bringing older code up to functional OOP standards and implementing best practices that have matured in our organization.

### Pre-Migration Assessment

Before starting any migration, complete this assessment:

#### Critical Questions to Ask

**Hook & Operator Analysis:**
- [ ] Does a new hook need to be created? (Only if it will be used by multiple jobs)
- [ ] Does an existing Legacy hook need to be modified for Airflow 2? Can it be consolidated?
- [ ] Should this DAG use an existing custom hook or operator instead of creating new ones?
- [ ] If the Legacy DAG has a custom hook, is it used in more than one place? (If not, it shouldn't be a hook)

**Environment & Configuration:**
- [ ] Are connections or variables different between prod, staging, or local?
- [ ] Is this DAG using variables for data that should be in connections?
- [ ] Is this DAG using variables to store large or growing data sets?

**Data & Modeling:**
- [ ] Is this data already modeled in DBT? Can you share those files?
- [ ] What are the unique key and timestamp fields for deduplication?
- [ ] Does this require incremental loads, full reloads, or both?

**Performance & Efficiency:**
- [ ] Does this DAG make many API calls that could be made asynchronously?
- [ ] Can API calls be constructed beforehand (predictable date ranges, pagination)?
- [ ] Does this DAG run slowly relative to its schedule interval?

### Architecture Decision Guidelines

#### External Tables vs Raw Tables Decision Tree

**Use External Tables When Either:**

**Option A:** All three conditions are met:
- ✅ Data has consistent unique key for deduplication
- ✅ Data has timestamp field for incremental processing
- ✅ No complex merge logic required

**Option B:** Single condition met:
- ✅ Data loads are incremental only with no overlap

**Use Direct Raw Table Loading When:**
- ❌ Complex deduplication logic needed
- ❌ Merge statements required for data updates
- ❌ Real-time processing requirements
- ❌ Data lacks unique key or timestamp for clean incremental processing

#### Hook vs Inline Code Decision

Create a custom hook when:
- [ ] Logic will be used by multiple DAGs/tasks
- [ ] Complex connection management required
- [ ] Reusable data source interaction patterns

Keep logic inline when:
- [ ] Single-use functionality
- [ ] Simple, one-off operations
- [ ] DAG-specific business logic

#### Variable vs Connection Guidelines

**Use Connections for:**
- API URLs and credentials
- Username/password combinations
- Database connection strings
- Any authentication-related configuration

**Use Variables for:**
- Small configuration values
- Environment-specific settings
- Timestamps and simple state
- Non-sensitive operational parameters

**Avoid Variables for:**
- Large data sets (use XCom or external storage)
- Growing lists (like sprint names in Jira pipeline)
- Sensitive information (use connections with proper encryption)

#### Async Implementation Guidelines

**Consider async when:**
- DAG makes many predictable API calls
- API supports pagination with known page counts
- Date ranges can be determined in advance
- Current DAG runs slowly relative to schedule interval

**Avoid async when:**
- DAG already runs efficiently
- API calls depend on previous responses
- Next API call URL comes from previous response
- Complexity outweighs performance benefits

**Always ask before implementing async** - get approval before adding async complexity.

**Async Implementation using AIOEase:**

AIOEase simplifies asynchronous HTTP requests with rate limiting. It accepts a list of request dictionaries and returns responses with status codes.

```python
from aioease import execute_async_requests

# Basic usage
requests = [
    {
        "url": "https://api.example.com/endpoint1",
        "method": "get",
        "data": {"key": "value"},
        "headers": {"Authorization": "Bearer token"}
    },
    {
        "url": "https://api.example.com/endpoint2",
        "method": "post",
        "data": {"payload": "data"},
        "headers": {"Content-Type": "application/json"}
    }
]

# Execute with rate limiting (max 10 requests per second)
responses = execute_async_requests(requests, requests_per_second_max=10)

# Responses include status, response body, and optional unique ID
# [{"status": 200, "response": "response_body"}, ...]

# Use unique IDs to match requests to responses
requests_with_ids = [
    {
        "url": "https://api.example.com/endpoint",
        "method": "get",
        "id": "unique-identifier-1"
    }
]
responses = execute_async_requests(requests_with_ids, requests_per_second_max=5)
# [{"status": 200, "response": "response_body", "id": "unique-identifier-1"}]
```

#### Task Group Usage

Use TaskGroups when:
- Multiple related tasks that logically group together
- Tasks that iterate over similar operations (like PestRoutes offices)
- Complex DAGs that benefit from visual organization

**Example Pattern** (from pestroutes DAGs):
```python
from airflow.utils.task_group import TaskGroup

for entity in entities:
    with TaskGroup(group_id=f"{entity['name']}_group") as entity_group:
        # Create multiple related tasks within the group
        get_tasks = []
        for office_id, office_config in branch_keys.items():
            task = create_task(entity, office_id, office_config)
            get_tasks.append(task())

        # Set task dependencies within the group
        get_tasks >> process_task >> cleanup_task
```

### Migration Process

#### Step 1: Analysis and Planning

1. **Complete the Pre-Migration Assessment** (see checklist above)
2. **Review Legacy DAG structure** and identify patterns
3. **Identify required hooks and operators** from `common/` directory
4. **Plan external table strategy** based on data characteristics
5. **Design task breakdown** - can large tasks be split into smaller, focused tasks?

#### Step 2: Code Migration

1. **Create new directory** following naming convention: `{pipeline_name}/`
2. **Implement `src/main.py`** with proper class structure and `execute()` method
3. **Create DAG file** named by schedule (`daily.py`, `intraday.py`, etc.)
4. **Migrate custom logic** while improving code quality
5. **Implement proper error handling**, especially for API calls
6. **Add type hints and documentation** throughout

#### Step 3: Configuration Migration

1. **Convert variables to connections** where appropriate
2. **Update environment-specific configurations**
3. **Ensure proper secret management**
4. **Validate connection configurations** across environments

#### Step 4: Testing and Validation

1. **Unit test core functionality** in development environment
2. **Compare outputs** between Legacy and Airflow 2 versions
3. **Validate data consistency** in DBT models
4. **Performance testing** to ensure efficiency improvements
5. **End-to-end testing** in staging environment

### Common Legacy Anti-Patterns to Fix

#### Big Functions (Violate Single Responsibility)
**Problem**: Single function/task doing multiple unrelated operations
**Solution**: Break into focused, single-purpose tasks

#### Poor Naming Conventions
**Problem**: Unclear variable/function names like `data`, `result`, `temp`
**Solution**: Descriptive names that explain purpose and content

#### Commented-Out Code
**Problem**: Dead code left in files "just in case"
**Solution**: Remove all commented-out code; use version control for history

#### Monolithic Tasks
**Problem**: One massive task doing work that should be distributed
**Solution**: Break into logical task dependencies using `>>` operator or TaskGroups

#### XCom Abuse
**Problem**: Storing large datasets in XCom
**Solution**: Use S3 or other appropriate storage; XCom for small data only (<100MB)

#### Variable Misuse
**Problem**: Storing large/growing data in Airflow Variables
**Solution**: Use appropriate storage solutions; variables for small config only

#### Connection Information in Variables
**Problem**: API URLs and keys stored separately in variables
**Solution**: Consolidate into properly configured Airflow connections

#### Synchronous API Calls
**Problem**: Sequential API calls when parallelization possible
**Solution**: Implement async patterns where beneficial (with approval)

#### Single-Use Custom Hooks/Operators
**Problem**: Creating reusable components for one-time use
**Solution**: Keep simple logic inline; only create hooks/operators for multi-use cases

#### Multiple DAGs per File
**Problem**: Several related DAGs defined in one file
**Solution**: One DAG per file, named by schedule (`daily.py`, `intraday.py`)

### Specific Migration Patterns

#### Pattern 1: File Structure & Organization

**Before (Legacy):**
```python
# All business logic mixed in config/ask_nicely/__init__.py
from airflow import DAG
from ask_nicely import AskNicely
from config.ask_nicely.unsubscribed import Unsubscribed

# DAG with tasks calling methods directly
surveys_to_snowflake = PythonOperator(
    python_callable=AskNicely().surveys_to_snowflake,
    dag=dag
)
```

**After (Airflow 2):**
```python
# Proper directory structure: ask_nicely/src/main.py + ask_nicely/intraday.py
from ask_nicely.src.main import AskNicely
from ask_nicely.src.unsubscribed import Unsubscribed

# Clean separation with schedule-based naming
with DAG("ask_nicely", ...) as dag:
    surveys_to_snowflake = PythonOperator(
        python_callable=AskNicely().surveys_to_snowflake,
        dag=dag
    )
```

**Key Improvements:**
- Proper `{pipeline_name}/src/main.py` directory structure
- Schedule-based DAG file naming (`intraday.py`, `nightly.py`)
- Clear separation between DAG definition and business logic

#### Pattern 2: Modern Import Updates

**Before (Legacy):**
```python
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.hooks.snowflake_hook import SnowflakeHook
from plugins.operators.snowflake_execute_query import SnowflakeExecuteQueryOperator
```

**After (Airflow 2):**
```python
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from common.custom_operators.snowflake_external_table_operator import SnowflakeExternalTableOperator
```

**Key Improvements:**
- Updated to modern Airflow 2 import paths
- Replaced deprecated `contrib` imports with `providers`
- Uses existing custom operators instead of creating single-use ones

#### Pattern 3: Breaking Down Monolithic Functions

**Before (Legacy):**
```python
def execute(task_name, endpoint, params, schema_name, table_name, **kwargs):
    # 50+ line function doing everything
    if task_name == 'tests':
        # Fetch data logic
        base_url, headers = get_conn()
        all_data = []
        # Complex pagination logic...
        # Data processing logic...
        # S3 upload logic...
        # Variable storage logic...
    elif task_name == 'test_results':
        # Different complex logic...
        # API calls, retries, batching...
        # More S3 uploads...
```

**After (Airflow 2):**
```python
def execute(task_name: str, endpoint: str, params: Dict[str, Any],
           schema_name: str, table_name: str, **kwargs: Any) -> Optional[int]:
    # Simple 15-line dispatcher
    if task_name == 'tests':
        fetch_tests(endpoint, params, schema_name, table_name)
    elif task_name == 'test_results':
        return fetch_test_results(endpoint, schema_name, table_name,
                                 public_id, last_check_time, **kwargs)

def fetch_tests(endpoint: str, params: Dict[str, Any],
               schema_name: str, table_name: str) -> None:
    # Focused on just fetching tests

def fetch_test_results(endpoint: str, schema_name: str, table_name: str,
                      public_id: Optional[str], from_ts: int, **kwargs: Any) -> int:
    # Focused on just fetching results

def process_and_store_tests(tests: List[Dict[str, Any]],
                           schema_name: str, table_name: str) -> None:
    # Focused on just processing and storing
```

**Key Improvements:**
- Single-responsibility functions instead of monolithic code
- Clear function boundaries and focused purposes
- Easier to test, debug, and maintain individual components

#### Pattern 4: Adding Comprehensive Type Hints

**Before (Legacy):**
```python
def fetch_test_results(task_name, schema_name, table_name, endpoint, public_id,
                       from_ts=DEFAULT_START_EPOCH_MS, to_ts=None, **kwargs):
    # No type information
    base_url, headers = get_conn()
    all_results = []
    largest_check_time_seen = from_ts
```

**After (Airflow 2):**
```python
def fetch_test_results(
    endpoint: str,
    schema_name: str,
    table_name: str,
    public_id: Optional[str],
    from_ts: int,
    to_ts: Optional[int] = None,
    **kwargs: Any
) -> int:
    base_url: str
    headers: Dict[str, str]
    base_url, headers = get_conn()
    all_results: List[Dict[str, Any]] = []
    largest_check_time_seen: int = from_ts
```

**Key Improvements:**
- Comprehensive type hints for all parameters and return values
- Clear variable type annotations throughout functions
- Better IDE support and code clarity

#### Pattern 5: Modern Hook Usage

**Before (Legacy):**
```python
# Manual S3 client creation
aws_conn = BaseHook.get_connection('aws_default')
access_key_id = aws_conn.login
secret_access_key = aws_conn.password
s3_client = boto3.client('s3', aws_access_key_id=access_key_id,
                        aws_secret_access_key=secret_access_key)

# Manual S3 upload
s3_key = S3UploadHook(
    s3_client=s3_client,
    s3_prefix=s3_prefix,
    data=data_list,
    file_name=s3_file_name,
    file_type="csv"
).upload_file()
```

**After (Airflow 2):**
```python
# Use existing custom hooks
s3_key = CustomS3Hook(
    s3_prefix=f"{schema_name}/{table_name}",
    data=data,
    file_type="json"
).upload_file()

# Use custom Snowflake operations
CustomSnowflakeHook().ensure_table_exists(
    schema='datadog',
    table='tests',
    table_types=["raw", "external"]
)
```

**Key Improvements:**
- Leverages existing custom hooks instead of recreating infrastructure
- Cleaner, more maintainable code
- Consistent patterns across all DAGs

#### Pattern 6: TaskGroup Implementation

**Before (Legacy):**
```python
# Manual task generation with complex dependencies
fetch_test_results_tasks = []
for test in tests_info:
    task_id = f"fetch_{test['public_id']}_results_to_s3"
    test_results_to_s3_task = PythonOperator(task_id=task_id, ...)
    ensure_test_results_table_exists_task >> test_results_to_s3_task
    fetch_test_results_tasks.append(test_results_to_s3_task)

# Complex dependency management
for fetch_test_results_task in fetch_test_results_tasks:
    fetch_test_results_task >> save_check_times_task
```

**After (Airflow 2):**
```python
# Clean TaskGroup usage
with TaskGroup("fetch_test_results_group") as fetch_test_results_group:
    for test in tests_info:
        test_results_to_s3_task = PythonOperator(
            task_id=f"fetch_{test['public_id']}_results_to_s3",
            python_callable=execute,
            op_kwargs={...}
        )

# Simple dependency chains
ensure_tests_table_exists_task >> fetch_test_results_group >> save_check_times_task
```

**Key Improvements:**
- Visual organization of related tasks
- Simplified dependency management
- Better DAG readability and maintenance

#### Pattern 7: Enhanced Error Handling

**Before (Legacy):**
```python
try:
    response = requests.get(url=url, headers=headers)
    if resp.status_code > 300:
        raise Exception(f"status_code: {resp.status_code} , Error: {resp.text}")
except Exception as e:
    logger.error(f"Failed to fetch tests due to an error: {e}")
    break
```

**After (Airflow 2):**
```python
try:
    response = requests.get(f"{base_url}{endpoint}", headers=headers, params=params)
    if response.status_code == 429:  # Rate limit handling
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            time.sleep(int(retry_after))
        else:
            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
    response.raise_for_status()
except RequestException as e:
    logger.error(f"Error fetching tests: {e}", exc_info=True)
    raise
```

**Key Improvements:**
- Specific handling for different HTTP status codes
- Smart rate limiting with exponential backoff
- Detailed error context with `exc_info=True`
- Proper exception types instead of generic `Exception`

### Hook Consolidation Strategy

#### Current Hook Analysis

We have identified potential consolidation opportunities in these hooks:
- `CustomS3ToSnowflakeHook` (uses merge statements)
- `CustomS3ToSnowflakeInsertHook` (uses insert statements)

**Consolidation Approach:**

The main difference between these hooks is the SQL operation type (MERGE vs INSERT). A consolidated approach could:

1. **Single Hook with Operation Parameter:**
```python
CustomS3ToSnowflakeHook(
    schema="ask_nicely",
    table="surveys",
    s3_key=s3_key,
    operation="merge",  # or "insert"
    merge_on_field="id",  # only required for merge
    fields_to_merge=[...],
    # other parameters
)
```

2. **Factory Pattern:**
```python
# Keep separate hooks but standardize interface
class S3ToSnowflakeHookFactory:
    @staticmethod
    def create_merge_hook(**kwargs):
        return CustomS3ToSnowflakeHook(**kwargs)

    @staticmethod
    def create_insert_hook(**kwargs):
        return CustomS3ToSnowflakeInsertHook(**kwargs)
```

**Recommendation:** Evaluate usage patterns across all DAGs before consolidating. If arguments can be cleanly unified, consolidate. If not, maintain separate hooks with consistent interfaces.

### Error Handling Standards

#### API Error Handling (Mandatory)

All API calls must implement proper error handling to capture:
- HTTP status codes
- API error messages
- Request/response details for debugging

```python
try:
    response = api_call()
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"API call failed: {e}")
    logger.error(f"Request details: {request_info}")
    logger.error(f"Response details: {response.text if response else 'No response'}")
    # Decide whether to raise or continue based on DAG requirements
    raise  # or handle gracefully depending on context
```

#### Database Connection Handling

Always ensure database connections are properly closed:
```python
try:
    with hook.get_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()
except Exception as e:
    logger.error(f"Database operation failed: {e}")
    raise
finally:
    # Connection cleanup handled by context manager
    pass
```

#### File System Cleanup

Remove temporary files from Airflow EC2 instances:
```python
import tempfile
import os

temp_file = None
try:
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        # Process file
        pass
finally:
    if temp_file and os.path.exists(temp_file.name):
        os.unlink(temp_file.name)
```

### Documentation Standards

#### DAG Documentation

Every migrated DAG must include:

1. **Comprehensive docstrings** in all functions and classes during development
2. **Clear task descriptions** explaining purpose and dependencies
3. **SOP Document** created in GitHub wiki **after DAG is production-ready**
4. **DAG doc_md reference** pointing to the SOP (added when SOP is complete)
5. **Required Callbacks** in default_args

**Important**: Do not create SOP documentation during initial development. SOPs should only be written once the DAG is stable and production-ready to avoid outdated documentation.

#### Required Default Args Structure

Every DAG must include these standardized default_args:

```python
default_args = {
    "owner": "[airflow_legacy_dag_owner]@goaptive.com",  # Always ask for clarification
    "depends_on_past": False,
    "start_date": pendulum.datetime(year=2025, month=1, day=7, tz="America/Denver"),  # Today's date
    "email": [],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,  # Ask if this should be adjusted for specific DAG
    "retry_delay": timedelta(minutes=3),
    "on_success_callback": [cb().on_success_callback],
    "on_failure_callback": [cb().on_failure_callback],
}
```

**Migration Questions to Always Ask:**
- "Who should be the owner of this DAG?" (default to previous owner but confirm)
- "Should retries be set to 1, or does this DAG need different retry behavior?"

**Example SOP Reference** (added when production-ready):
```python
with DAG(
    "my_pipeline_daily",
    default_args=default_args,
    schedule_interval=schedule_interval,
    doc_md="For more information, [see documentation](https://github.com/aptive-env/data-airflow/wiki/SOP:-My-Pipeline)",
    tags=tags
) as dag:
```

#### Testing Documentation

**Testing Requirements for Migrated DAGs:**

1. **Data Consistency Validation:**
   - Run both Legacy and Airflow 2 DAGs for the same time period
   - Compare row counts in final Snowflake tables
   - Validate data types and formats match expectations
   - Check for missing or duplicate records

2. **Functional Testing:**
   - Test all environment configurations (local, staging, prod)
   - Validate error handling with intentional failures
   - Test retry logic and rate limiting
   - Verify connection and variable usage

3. **Integration Testing:**
   - End-to-end pipeline testing including DBT models
   - Validate external table functionality (if applicable)
   - Test task dependencies and TaskGroup behavior
   - Verify XCom usage is appropriate (small data only)

4. **Performance Testing:**
   - Benchmark execution time vs. Legacy version
   - Monitor resource usage during execution
   - Validate Snowflake query efficiency
   - Test with production-scale data volumes

**Testing Checklist:**
- [ ] Local environment testing completed
- [ ] Staging environment validation passed
- [ ] Data consistency verified against Legacy
- [ ] Error scenarios tested
- [ ] Performance benchmarks recorded
- [ ] Integration with downstream systems validated

### Validation Framework

#### Data Consistency Validation

**Requirement**: New DAG must produce identical results to Legacy DAG after DBT modeling

**Validation Process:**
1. Run both Legacy and Airflow 2 DAGs for same time period
2. Compare final DBT model outputs
3. Investigate and resolve any discrepancies:
   - Missing data → Fix data retrieval
   - Duplicate data → Implement proper deduplication
   - Data differences → Trace through pipeline to identify source

#### Performance Validation

**Performance Validation Criteria:**

Compare the following metrics between Legacy and Airflow 2 versions:

1. **Execution Time Metrics:**
   - Total DAG execution time
   - Individual task execution time
   - Time to first data availability
   - Recovery time from failures

2. **Resource Usage:**
   - Peak memory usage during execution
   - CPU utilization patterns
   - Network I/O for API calls and data transfers
   - Temporary disk space usage

3. **Snowflake Efficiency:**
   - Number of Snowflake connections opened
   - Total query execution time in Snowflake
   - Data warehouse credit consumption
   - Queue time for Snowflake operations

4. **Data Pipeline Efficiency:**
   - API call patterns (sequential vs. parallel)
   - S3 upload/download efficiency
   - Batch size optimization
   - Error recovery time

**Validation Process:**
1. Run both versions with identical data sets
2. Monitor metrics for at least 3 execution cycles
3. Document any performance regressions
4. Identify root causes of performance differences
5. Validate that improvements justify any performance costs

**Acceptable Trade-offs:**
- Slower Airflow execution for faster Snowflake queries
- Additional monitoring overhead for better observability
- More complex retry logic for improved reliability

### Migration Checklist

**Pre-Migration:**
- [ ] Assessment questions completed
- [ ] Legacy DAG analyzed and documented
- [ ] Migration plan created and reviewed

**Development:**
- [ ] New directory structure created
- [ ] Code quality standards implemented
- [ ] Type hints added throughout
- [ ] Error handling implemented
- [ ] Custom hooks/operators evaluated for reuse vs creation

**Testing:**
- [ ] Local testing completed
- [ ] Data consistency validated
- [ ] Performance benchmarked
- [ ] Environment-specific configurations tested

**Documentation:**
- [ ] Code comments reviewed and cleaned
- [ ] Comprehensive docstrings added

**Deployment:**
- [ ] Staging deployment successful
- [ ] Production deployment planned
- [ ] Legacy DAG deprecation scheduled
- [ ] **SOP document created** (only after production deployment)
- [ ] **DAG doc_md updated** with SOP reference

## Git Workflow
- **Main Branch**: Production branch (connects to production Airflow)
- **Staging Branch**: Testing branch (connects to staging Airflow, auto-reset to main every Wednesday 5AM UTC)
- **Feature Development**: Create branches from `main` for standard features, from `staging` for extended testing
- **Cherry-picking**: Use cherry-pick to move staging-tested features to main-based branches before merging to main

## Performance Considerations

### Efficiency Guidelines

**Snowflake Efficiency** (Primary concern - optimize for reduced Snowflake costs):
- **Minimize Snowflake Connections**: Use single merge statements instead of 100 individual inserts
- **Batch Operations**: Wait to collect all files before writing to Snowflake rather than individual file writes
- **Optimize Query Patterns**: Design efficient queries in DBT models
- **Proper Data Loading**: Use efficient loading strategies (external tables, bulk operations)
- **Smart Resource Usage**: Consider spending more in Airflow if it results faster Snowflake queries

**Airflow Efficiency** (Important but secondary to Snowflake costs):
- Remove unnecessary task dependencies
- Implement parallel processing where possible
- Use appropriate task concurrency settings
- Clean up temporary resources
- Efficient use of XCom (small data only)

### Benchmarking

**Performance Validation Criteria:**

1. **Execution Time Comparison:**
   - Legacy DAG execution time vs. Airflow 2 execution time
   - Target: Similar or improved performance
   - Consider that some improvement may come at cost of better error handling/logging

2. **Resource Efficiency:**
   - Memory usage during task execution
   - Temporary file cleanup (no files left on Airflow EC2s)
   - Connection usage patterns

3. **Snowflake Efficiency Metrics:**
   - Number of connections to Snowflake (fewer is better)
   - Query execution time in Snowflake
   - Data warehouse credit usage
   - Use of batch operations vs. individual operations

4. **Reliability Improvements:**
   - Reduced failure rates due to better error handling
   - Faster recovery from transient failures
   - Better rate limiting and retry logic

**Acceptable Trade-offs:**
- Slightly slower Airflow execution if it results in significantly faster Snowflake queries
- Additional Airflow resource usage for better error handling and monitoring
- More complex code if it provides better maintainability and reliability

### Batch Processing
- **Batch Processing**: For large data operations, implement batch processing (PestRoutes class uses `batch_size` parameter)
- **Default Batch Size**: 250,000 records for large data uploads
- **Async Processing**: Use asyncio for parallel processing when appropriate
- **Memory Management**: Monitor memory usage in Airflow tasks and implement batching for memory-intensive operations
- **XCom Limits**: Keep XCom messages below 100MB; use `xcom_persist_tasks` variable for longer retention

## Infrastructure Management
- **Terraform**: Infrastructure as code in `infrastructure/` directory
- **EKS Environments**: Separate staging and production environments with different backend configs
- **Node Groups**: Dedicated node groups for worker and scheduler (consolidates webserver), and optional GPU components
- **Scaling**: Auto-scaling configured for different workload types

### Critical: Node Selector Configuration
- **Current Architecture**: Only 2 node groups exist: `worker` (role=worker) and `scheduler` (role=scheduler)
- **Webserver Placement**: Webserver pods MUST use `nodeSelector: role=scheduler` (NOT role=webserver)
- **Before Modifying Node Selectors**: Always verify available nodes with `kubectl get nodes -L role`
- **Never create deployments requiring non-existent node groups**

### EKS Instance Type Requirements
- **Memory Requirements**: Airflow worker pods require 2GB+ memory (1GB main container + 1GB init container + system overhead)
- **Safe Instance Types**: Use only instance types with 8GB+ memory for reliable scheduling
  - **Worker Nodes**: `["t3.large", "t3.xlarge", "t3a.large", "t3a.xlarge", "m5.large", "m5.xlarge", "m5a.large", "m5a.xlarge", "m5n.large", "m5n.xlarge", "m4.large", "m4.xlarge", "c5.xlarge", "c5a.xlarge", "c5n.xlarge"]`
  - **Scheduler Nodes** (also hosts webserver): `["t3.medium", "t3.large", "m5.large", "m5.xlarge", "m4.large", "m4.xlarge", "c5.large", "c5.xlarge", "c4.large", "c4.xlarge"]`
- **Avoid Small Instances**: c4.large (3.75GB), c5.large (4GB), c5a.large (4GB) cause pod scheduling failures
- **Node Group Updates**: Instance type changes require node group recreation (delete + recreate), not in-place updates

### Production Instance Type Guidelines
- **Critical Finding**: Production resource usage can be 2x higher than staging environments
- **Minimum Requirements**: 8GB+ RAM per node to handle production workloads safely
- **Recommended Configuration** (Post-2025-07-16 upgrade):
  - **Scheduler** (also hosts webserver): `["c5.xlarge", "c5.2xlarge", "m5.xlarge", "m5.2xlarge", "m4.xlarge", "m4.2xlarge"]`
  - **Worker**: `["m5.large", "m5.xlarge", "m5.2xlarge", "c5.xlarge", "c5.2xlarge", "m4.large", "m4.xlarge", "t3.large", "t3.xlarge"]`
- **Instance Type Strategy**: Better to have fewer adequate instance types than many inadequate ones

## Health Check Auto-Remediation

The health check script includes automatic remediation capabilities for common EKS Airflow issues:

### Auto-Fix Features
- **Volume Node Affinity Conflicts**: Automatically deletes stuck StatefulSets and PVCs when pods can't schedule due to missing nodes
- **Stuck Pod Recovery**: Restarts pods that have been pending for more than 10 minutes
- **Hybrid Architecture Support**: Uses docker-compose restart for components when K8s scheduling fails

### Usage Examples
```bash
# Standard health check (no fixes)
bash scripts/health_check.sh

# Enable auto-remediation
AUTO_FIX=true bash scripts/health_check.sh

# Preview what would be fixed without executing
DRY_RUN=true AUTO_FIX=true bash scripts/health_check.sh

# Customize auto-fix behavior
FIX_VOLUME_AFFINITY=false AUTO_FIX=true bash scripts/health_check.sh
FIX_STUCK_PODS=false AUTO_FIX=true bash scripts/health_check.sh
```

### Configuration Options
- `AUTO_FIX=true/false`: Enable automatic issue remediation (default: false)
- `FIX_VOLUME_AFFINITY=true/false`: Fix volume node affinity conflicts (default: true when AUTO_FIX=true)
- `FIX_STUCK_PODS=true/false`: Restart pods stuck in Pending >10min (default: true when AUTO_FIX=true)
- `DRY_RUN=true/false`: Show what would be fixed without executing (default: false)

### Automated Scheduling
For production environments, consider running with auto-remediation on a schedule:
```bash
# Add to crontab for automatic healing every 10 minutes
*/10 * * * * AUTO_FIX=true /path/to/scripts/health_check.sh >> /var/log/airflow-health.log 2>&1
```

### Infrastructure Troubleshooting

#### Pod Scheduling Issues
- **Symptoms**: Pods stuck in `Pending` state, `FailedScheduling` events
- **Diagnosis**:
  ```bash
  kubectl describe pod [pod-name] -n airflow
  kubectl describe nodes | grep -A 10 "Allocated resources"
  ```
- **Common Causes**: Insufficient memory, wrong node selector, resource conflicts
- **Solutions**: Update instance types, check node labels, verify resource requests

#### Common Error Patterns
- **502 Errors**: Usually indicate webserver pod scheduling problems due to insufficient node resources
- **Triggerer Stuck**: Often caused by insufficient memory on scheduler nodes
- **Memory Analysis**: Compare pod resource requests against node allocatable memory, account for system overhead
- **Spot Instance Strategy**: Better to have fewer adequate instance types than many inadequate ones

#### Emergency Procedures
- **Immediate**: Check pod events with `kubectl describe pod`
- **Quick Fix**: Scale down non-essential pods to free resources
- **Long-term**: Update infrastructure following procedures in `infrastructure/README.md`

## GBTPA Monthly DAG Implementation Notes

### Project Context
- **Purpose**: Monthly processing of Gallagher Bassett claims data (~400 columns)
- **Data Flow**: Data Lake S3 → Snowflake (split into Claim Summary + Financial Summary tables)
- **Schedule**: Monthly (@monthly) with schema validation first, then processing
- **Key Features**: Schema validation, CS/FS record splitting, upsert via CLAIM_NUM

### Technical Architecture
- **DAG Structure**: Two-task design for fail-fast schema validation
  - Task 1: `validate_schema_compatibility` - Fast schema check using INFER_SCHEMA
  - Task 2: `process_gbtpa_monthly_data` - Full data processing in Snowflake
- **Data Processing**: 100% Snowflake-native (no pandas downloads)
- **Format**: Parquet for staging, direct CSV processing from S3 stage
- **Error Handling**: Proper exceptions to ensure task failures are visible

### Current Status (2025-07-18)
- **Core Implementation**: 90% complete
- **Current Blocker**: File path extraction from Snowflake LIST command
- **File Format Issues**: Special characters in filenames cause SQL parsing errors
- **Next Steps**: Fix file path handling and implement proper upstream naming

### Key Learnings
- **Snowflake Stage Integration**: Using existing S3_STRATEGY_DATA_LAKE stage
- **File Format**: Uses existing RAW_STAGING.STAGE.CSV format
- **Schema Validation**: INFER_SCHEMA requires proper file paths and naming
- **Error Patterns**: Spaces and parentheses in filenames break Snowflake SQL parsing

### File Naming Requirements
- **Current Issue**: `Snapshot 2004-06-30 (1).csv` has spaces/parentheses
- **Recommended Pattern**: `gbtpa_YYYY_MM_export.csv` or `gbtpa_snapshot_YYYYMMDD.csv`
- **Critical**: No spaces, parentheses, or special characters in filenames

### Environment Configuration
- **Staging**: Uses RAW_STAGING database and RAW_STAGING.STAGE.CSV format
- **Production**: Uses RAW database and RAW.STAGE.CSV format
- **S3 Path**: `aptive-sftp/gbtpa/` in S3_STRATEGY_DATA_LAKE stage

## Infrastructure Change Management

### Pre-Change Validation
Always run pre-flight checks before infrastructure changes:
```bash
# Environment validation
echo "Current AWS Account: $(aws sts get-caller-identity --query Account --output text)"
terraform plan -var-file=staging.tfvars | grep -E "Plan:|No changes"

# System health check
kubectl get pods -n airflow --field-selector=status.phase!=Running
kubectl top nodes  # Check resource usage
```

### Change Approval Process
1. **Staging First**: Always test changes in staging environment
2. **Documentation**: Update both README.md and CLAUDE.md as needed
3. **Rollback Plan**: Have rollback procedures ready before applying changes
4. **Validation**: Post-change verification of all system components

### Post-Change Validation
```bash
# Verify all pods are running
kubectl get pods -n airflow

# Check node resource allocation
kubectl describe nodes | grep -A 10 "Allocated resources"

# Test Airflow functionality
kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
```

## Terraform Workflow

### Variable Application
- **Always reference**: `infrastructure/README.md` for proper variable application and setup
- **Environment-specific**: Use correct `.tfvars` file for target environment
- **Backend Configuration**: Always initialize with correct backend config when switching environments

### State Management Best Practices
- **Backup before changes**: `terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate`
- **Import existing resources**: Use `terraform import` for resources not in state
- **Clean up state**: Remove orphaned resources with `terraform state rm`
- **State validation**: Regular `terraform plan` runs to detect drift

### Troubleshooting Terraform Issues
- **State conflicts**: Import existing resources or remove from state
- **Resource conflicts**: Check AWS console for actual resource state
- **Authentication**: Refresh AWS credentials if encountering auth errors
- **Backend issues**: Verify backend configuration matches environment

### EKS Version Upgrades

#### Sequential Upgrade Requirements
EKS requires incremental upgrades - cannot skip versions. For major upgrades (e.g., 1.29 → 1.33):

**Required Path**: 1.29 → 1.30 → 1.31 → 1.32 → 1.33

#### Upgrade Procedure (Verified 2025-07-29)
1. **Update Terraform Variables**:
   ```bash
   # Update infrastructure/variables.tf
   variable "eks_cluster_version" {
     default = "1.30"  # Start with next increment
   }
   ```

2. **Apply Sequential Upgrades**:
   ```bash
   # For each version increment:
   terraform apply -var-file=production.tfvars -auto-approve

   # Verify cluster version
   aws eks describe-cluster --name airflow --query 'cluster.version' --output text
   ```

3. **Monitor Update Progress**:
   ```bash
   # Check update status
   aws eks list-updates --name airflow
   aws eks describe-update --name airflow --update-id <update-id>

   # Node group status
   aws eks describe-nodegroup --cluster-name airflow --nodegroup-name airflow-eks-node-worker
   ```

#### EKS 1.33+ AMI Requirements
- **Critical**: EKS 1.33+ requires AL2023_x86_64_STANDARD AMI (AL2_x86_64 no longer supported)
- **Node Group Configuration**:
  ```hcl
  worker_node_group = {
    ami_type = "AL2023_x86_64_STANDARD"
    # ... other config
  }
  scheduler_node_group = {
    ami_type = "AL2023_x86_64_STANDARD"
    # ... other config
  }
  ```

#### Upgrade Validation
```bash
# Verify cluster version
aws eks describe-cluster --name airflow --query 'cluster.version' --output text

# Check node versions (may lag during rolling update)
kubectl get nodes -o wide

# Health check
bash scripts/health_check.sh
```

#### Common Issues and Solutions
- **"Cannot VersionUpdate because cluster currently has an update in progress"**: Wait for previous update to complete
- **"AMI Type AL2_x86_64 is only supported for kubernetes versions 1.32 or earlier"**: Update node group AMI type to AL2023_x86_64_STANDARD
- **"another operation (install/upgrade/rollback) is in progress"**: Helm operations may conflict during upgrades - wait for completion
- **Node group recreation required**: AMI type changes force node group replacement (expected behavior)

#### Post-Upgrade Verification
- EKS cluster shows target version
- All Airflow components running (`bash scripts/health_check.sh`)
- Node groups may complete update asynchronously
- Airflow functionality operational (core objective achieved)

### EKS Node Group Recreation Procedure
When EKS node groups fail to update due to instance type changes, use this procedure:

1. **Remove from Terraform State**:
   ```bash
   terraform state rm 'module.eks.module.eks_managed_node_group["scheduler_node_group"].aws_eks_node_group.this[0]'
   terraform state rm 'module.eks.module.eks_managed_node_group["worker_node_group"].aws_eks_node_group.this[0]'
   terraform state rm 'module.eks.module.eks_managed_node_group["webserver_node_group"].aws_eks_node_group.this[0]'
   ```

2. **Manually Delete Node Groups**:
   ```bash
   aws eks delete-nodegroup --cluster-name airflow --nodegroup-name airflow-eks-node-scheduler
   aws eks delete-nodegroup --cluster-name airflow --nodegroup-name airflow-eks-node-worker
   aws eks delete-nodegroup --cluster-name airflow --nodegroup-name airflow-eks-node-webserver
   ```

3. **Wait for Deletion** (check status until "DELETED"):
   ```bash
   aws eks describe-nodegroup --cluster-name airflow --nodegroup-name airflow-eks-node-scheduler --query 'nodegroup.status'
   ```

4. **Apply Terraform** (creates new node groups):
   ```bash
   terraform apply -var-file=production.tfvars -auto-approve
   ```

5. **Validate Health**:
   ```bash
   bash scripts/health_check.sh
   ```

## Troubleshooting Guide

### Common Migration Issues and Solutions

#### 1. Import Errors
**Issue**: `ImportError: No module named 'airflow.operators.python_operator'`
**Solution**: Update to modern Airflow 2 imports:
```python
# Change from:
from airflow.operators.python_operator import PythonOperator
# To:
from airflow.operators.python import PythonOperator
```

#### 2. Hook Import Failures
**Issue**: `ImportError: No module named 'airflow.contrib.hooks.snowflake_hook'`
**Solution**: Update to providers-based imports:
```python
# Change from:
from airflow.contrib.hooks.snowflake_hook import SnowflakeHook
# To:
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
```

#### 3. Large Function Migration Errors
**Issue**: Monolithic functions causing timeout or memory issues
**Solution**: Break into smaller, focused functions:
- Separate data fetching from processing
- Implement batching for large datasets
- Add progress logging for long-running operations

#### 4. Variable vs. Connection Configuration
**Issue**: API authentication failing after migration
**Solution**: Consolidate separate variables into connections:
```python
# Instead of:
base_url = Variable.get('api-url')
api_key = Variable.get('secret-api-key')
# Use:
conn = BaseHook.get_connection('api_connection')
base_url = conn.host
api_key = conn.password
```

#### 5. TaskGroup Dependencies
**Issue**: Tasks in TaskGroup not executing in correct order
**Solution**: Ensure proper dependency setup:
```python
with TaskGroup("group_name") as task_group:
    # Tasks defined here

# Dependencies outside the group
upstream_task >> task_group >> downstream_task
```

#### 6. Type Hint Errors
**Issue**: `TypeError` or `AttributeError` with type annotations
**Solution**: Ensure all imports are available:
```python
from typing import Optional, List, Dict, Union, Any
```

#### 7. XCom Size Issues
**Issue**: `XCom value too large` errors
**Solution**: Use external storage for large data:
```python
# Instead of returning large data directly:
return large_dataset
# Use S3 and return key:
s3_key = upload_to_s3(large_dataset)
return s3_key
```

#### 8. External Table Setup
**Issue**: External table not finding S3 data
**Solution**: Verify S3 path structure and permissions:
- Check S3 prefix matches external table location
- Verify Snowflake stage permissions
- Validate file format matches expectations

#### 9. Rate Limiting Issues
**Issue**: API rate limit errors causing task failures
**Solution**: Implement proper rate limiting:
```python
if response.status_code == 429:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        time.sleep(int(retry_after))
    else:
        time.sleep(exponential_backoff_delay)
```

#### 10. Legacy Custom Hook Failures
**Issue**: Legacy custom hooks not working in Airflow 2
**Solution**:
- Check if equivalent functionality exists in `common/` directory
- Update hook to use modern Airflow patterns
- Consider consolidating with existing hooks

## Appendices

### Appendix A: Useful Custom Hooks and Operators

**Available in `common/` directory:**
- `CustomS3Hook` - S3 upload/download operations
- `CustomSnowflakeHook` - Enhanced Snowflake operations
- `CustomExternalTableHook` - External table management
- `CustomGoogleSheetsHook` - Google Sheets integration
- `CustomPestRoutesHook` - PestRoutes API operations
- `SheetsToSnowflakeOperator` - Complete sheets-to-snowflake pipeline
- `SnowflakeExternalTableOperator` - External table operations
- `SnowflakeToS3StageOperator` - Snowflake to S3 export

### Appendix B: Environment Configuration Patterns

**Local Environment:**
```python
if env == "local":
    schedule_interval = None
    max_records = 50_000
```

**Staging Environment:**
```python
elif env == "staging":
    schedule_interval = None
    max_records = None
```

**Production Environment:**
```python
elif env == "prod":
    schedule_interval = '0 1 * * *'  # Daily at 1 AM
    max_records = None
```

### Appendix C: DBT Integration Patterns

**External Table Pattern:**
- Airflow loads to S3
- DBT uses external tables in `raw.external_tables` schema
- DBT models in `models/raw/{source_name}/`

**Direct Load Pattern:**
- Airflow loads to S3 AND raw Snowflake tables
- DBT models start with clean/base models in `models/clean/{source_name}/`

---

*This document will continue to evolve as we gain experience with migrations and add concrete examples from Legacy DAG transformations.*