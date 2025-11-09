# Generate Migration Diff Skill

## Purpose
Create side-by-side comparison of legacy vs modern implementation, highlighting key changes, LOC reduction, and improvements.

## When to Use
**RECOMMENDED** after migration:
- After modern DAG is implemented
- To document changes and improvements
- For code review and validation
- To demonstrate migration value

## Execution Steps

### 1. Compare File Structures
```bash
# Legacy (single file)
echo "=== LEGACY STRUCTURE ==="
ls -lh /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
wc -l /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Modern (modular)
echo "=== MODERN STRUCTURE ==="
find /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME} -type f -name "*.py" -exec wc -l {} + | tail -1
```

### 2. Count Lines of Code
```bash
# Legacy LOC
LEGACY_LOC=$(wc -l < /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)

# Modern LOC (all Python files)
MODERN_LOC=$(find /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME} -name "*.py" -exec cat {} + | wc -l)

# Calculate reduction
REDUCTION=$(echo "scale=1; ($LEGACY_LOC - $MODERN_LOC) * 100 / $LEGACY_LOC" | bc)

echo "Legacy: $LEGACY_LOC lines"
echo "Modern: $MODERN_LOC lines"
echo "Reduction: $REDUCTION%"
```

### 3. Compare Operator Usage
```bash
# Legacy operators
echo "=== LEGACY OPERATORS ==="
grep -o "[A-Za-z]*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sort | uniq -c

# Modern operators/tasks
echo "=== MODERN @TASK + OPERATORS ==="
grep -c "@task" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/main.py
grep -o "[A-Za-z]*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/main.py | sort | uniq -c
```

### 4. Compare Imports
```bash
# Legacy imports
echo "=== LEGACY IMPORTS ==="
grep "^from \|^import " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Modern imports
echo "=== MODERN IMPORTS ==="
grep "^from \|^import " /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/main.py
```

### 5. Compare Functions/Classes
```bash
# Legacy
echo "=== LEGACY FUNCTIONS ==="
grep -c "^def " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Modern (main.py DAG definition)
echo "=== MODERN @TASK DECORATORS ==="
grep -c "@task" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/main.py

# Modern (src/main.py business logic)
if [ -f "/Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/src/main.py" ]; then
    echo "=== MODERN Main CLASS ==="
    grep -A 5 "class Main" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/src/main.py | head -10
fi
```

### 6. Identify Key Changes
```bash
# Check for removed anti-patterns
echo "=== REMOVED CODE ==="

# Custom SFTP (if removed)
if grep -q "paramiko\|pysftp" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py; then
    echo "✓ Removed custom SFTP implementation"
fi

# Direct boto3 (if removed)
if grep -q "boto3.client\|boto3.resource" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py; then
    echo "✓ Removed direct boto3 usage"
fi

# Check for added common components
echo "=== ADDED COMPONENTS ==="
grep "from common" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/main.py
```

### 7. Compare XCom Usage
```bash
# Legacy XCom operations
LEGACY_XCOM=$(grep -c "xcom_push\|xcom_pull" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)

# Modern XCom (should be 0 or minimal)
MODERN_XCOM=$(grep -c "xcom_push\|xcom_pull" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/main.py 2>/dev/null || echo 0)

echo "Legacy XCom operations: $LEGACY_XCOM"
echo "Modern XCom operations: $MODERN_XCOM (automatic via TaskFlow)"
```

### 8. Generate Visual Diff (Optional)
```bash
# If you want actual diff output
diff -u /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py \
        /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}/main.py \
        > /tmp/${DAG_NAME}_diff.txt

echo "Diff saved to: /tmp/${DAG_NAME}_diff.txt"
```

## Output Report Format

After executing this skill, provide:

```markdown
## Migration Diff Report: [dag_name]

### 📊 Summary Metrics

| Metric | Legacy | Modern | Change |
|--------|--------|--------|--------|
| **Total LOC** | 425 | 155 | -270 (-63.5%) |
| **Files** | 1 (monolithic) | 3 (modular) | +2 |
| **Functions** | 8 (global) | 5 @task + 1 Main class | Refactored |
| **Operators** | 12 | 5 @task + 4 operators | -3 |
| **XCom Operations** | 10 (manual) | 0 (automatic) | -10 |
| **Custom Code Lines** | 175 | 0 (using common/) | -175 |
| **Imports** | 15 | 8 | -7 |

**Overall Improvement**: 63.5% code reduction, modular structure, eliminated anti-patterns

---

### 🏗️ Structure Comparison

#### Legacy Structure (1 file)
```
data-airflow-legacy/dags/
└── cresta_to_snowflake.py (425 lines)
    ├── Imports (15 lines)
    ├── Constants (25 lines)
    ├── SFTPClient class (150 lines) ❌ REDUNDANT
    ├── Helper functions (80 lines)
    ├── PythonOperators (120 lines)
    ├── Other operators (20 lines)
    └── Dependencies (15 lines)
```

#### Modern Structure (3 files, modular)
```
data-airflow/dags/cresta_to_snowflake/
├── main.py (80 lines)
│   ├── Imports (8 lines)
│   ├── @dag decorator (5 lines)
│   ├── @task functions (40 lines) ✅ TaskFlow
│   ├── Operators from common/ (20 lines) ✅ Reusable
│   └── Dependencies (7 lines)
│
├── src/
│   ├── main.py (50 lines)
│   │   ├── Main class (10 lines)
│   │   └── Business logic methods (40 lines) ✅ Testable
│   │
│   └── config.py (25 lines) ✅ Centralized config
│
└── README.md
```

**Structure Benefits**:
- ✅ Separation of concerns
- ✅ Testable business logic in src/
- ✅ Configuration in dedicated file
- ✅ Clear DAG definition in main.py

---

### 🔄 Key Changes

#### 1. DAG Definition

**Legacy** (Lines 1-25):
```python
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'cresta_to_snowflake',
    default_args=default_args,
    schedule_interval='@daily',
    concurrency=5,
    catchup=False,
)
```

**Modern** (main.py, Lines 1-15):
```python
from airflow.decorators import dag, task
from pendulum import datetime
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator
from common.custom_callbacks.custom_callbacks import AirflowCallback

@dag(
    dag_id='cresta_to_snowflake',
    schedule='@daily',  # ✅ Renamed
    start_date=datetime(2023, 1, 1),  # ✅ Moved out of default_args
    catchup=False,
    max_active_tasks=5,  # ✅ Renamed from concurrency
    tags=['production', 'etl', 'cresta'],
    default_args={
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
        'on_failure_callback': AirflowCallback.failure_callback,  # ✅ Added
    }
)
def cresta_to_snowflake():
```

**Changes**:
- ✅ `DAG()` → `@dag` decorator
- ✅ `schedule_interval` → `schedule`
- ✅ `concurrency` → `max_active_tasks`
- ✅ Added standard callbacks from common/
- ✅ Added tags for better organization
- ✅ Must call function: `cresta_to_snowflake()` at end

**Impact**: Modernized configuration, +AirflowCallback for monitoring

---

#### 2. SFTP Implementation (BIGGEST WIN)

**Legacy** (Lines 45-195, **150 lines**):
```python
import paramiko
import boto3
from io import BytesIO

class SFTPClient:
    """Custom SFTP client for Cresta."""

    def __init__(self, host, username, private_key):
        self.host = host
        self.username = username
        self.private_key = private_key
        self.transport = None
        self.sftp = None

    def connect(self):
        """Establish SFTP connection."""
        # ... 20 lines of connection logic

    def download_file(self, remote_path):
        """Download file from SFTP."""
        # ... 30 lines of download logic

    def upload_to_s3(self, file_data, bucket, key):
        """Upload file to S3."""
        # ... 40 lines of S3 upload logic

    def load_to_snowflake(self, s3_path, table):
        """Load from S3 to Snowflake."""
        # ... 35 lines of Snowflake COPY logic

    def close(self):
        """Close SFTP connection."""
        # ... 10 lines

def execute_sftp_to_snowflake_pipeline(**context):
    """Execute the entire SFTP → S3 → Snowflake pipeline."""
    client = SFTPClient(
        host=os.environ['SFTP_HOST'],
        username=os.environ['SFTP_USER'],
        private_key=os.environ['SFTP_KEY']
    )
    # ... 75 lines of pipeline orchestration
```

**Modern** (main.py, Lines 40-48, **9 lines**):
```python
sftp_task = SFTPToSnowflakeOperator(
    task_id='sftp_to_snowflake',
    sftp_conn_id='cresta_sftp',
    directory='/incoming',
    s3_prefix='cresta/data/',
    snowflake_query='SELECT max_date FROM control_dates',
    use_flat_structure=True,
    determination_method='snowflake',
)
```

**Changes**:
- ❌ **REMOVED**: 150 lines of custom SFTP implementation
- ✅ **REPLACED**: With `SFTPToSnowflakeOperator` from common/
- ✅ Credentials via Airflow connections (secure)
- ✅ Tested, maintained code from common/
- ✅ Configurable via parameters

**Impact**: **-150 lines (35% of DAG)**, eliminated anti-pattern, improved security

---

#### 3. Data Transformation Logic

**Legacy** (Lines 200-280, in DAG file):
```python
def transform_data(**context):
    """Transform Cresta data."""
    ti = context['ti']
    raw_data = ti.xcom_pull(task_ids='extract_data')

    # 80 lines of transformation logic
    transformed = []
    for record in raw_data:
        # ... complex pandas operations
        # ... data validation
        # ... schema mapping

    ti.xcom_push(key='transformed_data', value=transformed)
    return transformed

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    provide_context=True,  # ❌ Deprecated
    dag=dag,
)
```

**Modern** (main.py):
```python
@task
def transform_data(raw_data: dict) -> dict:
    """Transform Cresta data using Main class."""
    from src.main import Main

    main = Main()
    return main.transform(raw_data)
```

**Modern** (src/main.py, Lines 20-60):
```python
class Main:
    """Business logic for Cresta data transformation."""

    def __init__(self):
        from src.config import TABLE_MAPPINGS, SCHEMA_CONFIG
        self.mappings = TABLE_MAPPINGS
        self.schema = SCHEMA_CONFIG

    def transform(self, raw_data: dict) -> dict:
        """Transform raw data to target schema."""
        # 40 lines of transformation logic
        # Now testable independently!
        return transformed_data
```

**Changes**:
- ✅ Separated business logic to src/main.py (testable)
- ✅ Used TaskFlow with type hints
- ✅ Removed `provide_context=True` (automatic)
- ✅ Automatic XCom via return value
- ✅ No manual xcom_push/pull

**Impact**: Better structure, testable code, cleaner DAG

---

#### 4. XCom Data Passing

**Legacy** (Manual XCom, 10 operations):
```python
def extract(**context):
    data = fetch_data()
    context['ti'].xcom_push(key='data', value=data)  # Line 65

def transform(**context):
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract', key='data')  # Line 85
    result = process(data)
    ti.xcom_push(key='result', value=result)  # Line 90

def load(**context):
    ti = context['ti']
    result = ti.xcom_pull(task_ids='transform', key='result')  # Line 105
    save(result)

# PythonOperators with provide_context=True
extract_task = PythonOperator(..., provide_context=True)
transform_task = PythonOperator(..., provide_context=True)
load_task = PythonOperator(..., provide_context=True)

extract_task >> transform_task >> load_task
```

**Modern** (Automatic XCom via TaskFlow):
```python
@task
def extract() -> dict:
    return fetch_data()  # ✅ Automatic XCom push

@task
def transform(data: dict) -> dict:  # ✅ Automatic XCom pull via parameter
    return process(data)

@task
def load(result: dict):  # ✅ Automatic XCom pull
    save(result)

# Data flow creates dependencies
load(transform(extract()))  # ✅ Clean data flow
```

**Changes**:
- ❌ **REMOVED**: 10 manual xcom_push/pull calls
- ✅ **AUTOMATIC**: Return values become XCom
- ✅ **TYPE-SAFE**: Parameters with type hints
- ✅ **CLEANER**: Implicit dependencies via data flow

**Impact**: -15 lines, improved clarity, type safety

---

#### 5. AWS S3 Operations

**Legacy** (Lines 135-160, direct boto3):
```python
import boto3

def upload_to_s3(**context):
    """Upload file to S3 using boto3."""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_KEY'],  # ❌ Insecure
        aws_secret_access_key=os.environ['AWS_SECRET']
    )

    # 25 lines of upload logic with error handling
    try:
        s3_client.upload_file(local_file, bucket, key)
    except Exception as e:
        # Custom error handling
```

**Modern** (if needed, or handled by SFTPToSnowflakeOperator):
```python
@task
def upload_to_s3(file_path: str):
    """Upload to S3 using CustomS3Hook."""
    from common.custom_hooks.custom_s3_hook import CustomS3Hook

    hook = CustomS3Hook(aws_conn_id='aws_default')  # ✅ Secure connection
    hook.upload_file(file_path, bucket='my-bucket', key='data/file.csv')
```

**Changes**:
- ❌ **REMOVED**: Direct boto3 client usage
- ✅ **REPLACED**: With CustomS3Hook from common/
- ✅ Credentials from Airflow connections (secure)
- ✅ Built-in error handling

**Impact**: -25 lines, improved security, reusable code

---

### 📈 Improvements Summary

#### Code Quality

| Aspect | Legacy | Modern | Improvement |
|--------|--------|--------|-------------|
| **Modularity** | ❌ Single 425-line file | ✅ 3 modular files | ✅ Better organization |
| **DRY Compliance** | ❌ 175 lines duplicate code | ✅ 0 (uses common/) | ✅ Eliminated duplication |
| **Testability** | ❌ Hard to test (all in DAG) | ✅ src/main.py testable | ✅ Unit tests possible |
| **Type Safety** | ❌ No type hints | ✅ Full type hints | ✅ Catch errors early |
| **Security** | ❌ Hardcoded credentials | ✅ Airflow connections | ✅ Secure |
| **Error Handling** | ⚠️ Custom, inconsistent | ✅ AirflowCallback | ✅ Standardized |
| **XCom Usage** | ❌ 10 manual operations | ✅ Automatic | ✅ Cleaner code |

#### Airflow 2.x Compliance

| Feature | Legacy (1.x) | Modern (2.x) | Status |
|---------|--------------|--------------|--------|
| DAG Definition | `DAG()` | `@dag` | ✅ Migrated |
| Task Definition | `PythonOperator` | `@task` | ✅ Migrated |
| Parameters | `schedule_interval`, `concurrency` | `schedule`, `max_active_tasks` | ✅ Updated |
| Context | `provide_context=True` | Automatic | ✅ Removed |
| Imports | `airflow.operators.python_operator` | `airflow.decorators` | ✅ Updated |
| Callbacks | ❌ None | `AirflowCallback` | ✅ Added |

#### Maintainability

**Legacy Issues**:
- ❌ 150 lines of SFTP code to maintain separately
- ❌ Direct library usage (boto3, paramiko) to update
- ❌ Hard to test without running DAG
- ❌ Single file = merge conflicts
- ❌ No separation of concerns

**Modern Benefits**:
- ✅ Uses tested common components
- ✅ Modular structure = easier collaboration
- ✅ Business logic in src/ = unit testable
- ✅ Configuration in config.py = easy updates
- ✅ Clear separation of concerns

---

### 📉 LOC Breakdown

#### Where Did 270 Lines Go?

| Category | Legacy LOC | Modern LOC | Saved | Reason |
|----------|------------|------------|-------|--------|
| **SFTP Implementation** | 150 | 9 (operator config) | **-141** | SFTPToSnowflakeOperator |
| **S3 Operations** | 25 | 3 (hook usage) | **-22** | CustomS3Hook |
| **XCom Boilerplate** | 30 | 0 | **-30** | Automatic via TaskFlow |
| **Import Statements** | 15 | 8 | **-7** | Modern imports |
| **DAG Boilerplate** | 20 | 15 | **-5** | @dag decorator |
| **Functions** | 185 | 120 | **-65** | Extracted to src/main.py |
| **Total** | **425** | **155** | **-270 (-63.5%)** | |

---

### ✅ Migration Checklist Completion

- [x] Removed custom SFTP implementation → SFTPToSnowflakeOperator
- [x] Removed direct boto3 usage → CustomS3Hook
- [x] Converted PythonOperators → @task decorators
- [x] Updated DAG configuration (schedule, max_active_tasks)
- [x] Removed provide_context=True
- [x] Added AirflowCallback for monitoring
- [x] Extracted business logic to src/main.py
- [x] Moved configuration to src/config.py
- [x] Converted manual XCom → automatic return values
- [x] Added type hints to all @task functions
- [x] Created modular structure
- [x] Updated imports to airflow.decorators

---

### 🎯 Value Delivered

**Quantitative**:
- **63.5% code reduction** (425 → 155 lines)
- **-175 lines** of duplicate/redundant code eliminated
- **-10 manual XCom operations** (now automatic)
- **+100% test coverage** possible (business logic in src/)

**Qualitative**:
- ✅ Modern Airflow 2.x TaskFlow API
- ✅ Reusable common components
- ✅ Secure credential management
- ✅ Modular, maintainable structure
- ✅ Type-safe with hints
- ✅ Standardized monitoring (AirflowCallback)
- ✅ DRY compliant

**Technical Debt Eliminated**:
- ❌ No more custom SFTP implementation
- ❌ No more hardcoded credentials
- ❌ No more manual XCom management
- ❌ No more deprecated patterns
- ❌ No more monolithic file

---

### 🚀 Next DAGs to Migrate

Based on this successful migration, prioritize these:

1. **Similar SFTP DAGs**: Can use same SFTPToSnowflakeOperator pattern
2. **Python-heavy DAGs**: Great candidates for TaskFlow conversion
3. **Anti-pattern DAGs**: High LOC reduction potential

**Migration Template Established**: This DAG can serve as template for future migrations.
```

## Enforcement

This skill SHOULD be executed:
- After modern DAG is implemented
- To document migration changes
- For team/stakeholder reporting
- To justify migration effort

**Documenting the diff demonstrates value and provides a template for future migrations.**
