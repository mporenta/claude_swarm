# Extract Business Logic Skill

## Purpose
Separate business logic from Airflow boilerplate following the `Main` class pattern, identifying code that belongs in `src/main.py` vs common components vs @task functions.

## When to Use
**MANDATORY** during migration planning:
- After analyzing legacy DAG structure
- Before converting PythonOperators to @task
- When DAG file exceeds 200 lines
- When complex business logic is embedded in operators

## Execution Steps

### 1. Identify Function Definitions
```bash
# Find all function definitions in legacy DAG
grep -n "^def " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Count lines per function
awk '/^def / {if (name) print name, NR-start; name=$2; start=NR} END {if (name) print name, NR-start}' /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 2. Extract Functions with Context
```bash
# Get function with 20 lines of context
grep -A 20 "^def function_name" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 3. Identify PythonOperator Callables
```bash
# Find python_callable references
grep -B 3 -A 5 "python_callable=" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 4. Check for Common Component Patterns
```bash
# Search for SFTP implementations
grep -n "sftp\|SFTP\|paramiko\|pysftp" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Search for S3 implementations
grep -n "boto3\|s3_client\|upload_file\|download_file" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Search for API client patterns
grep -n "requests\|http\|api_call\|get_connection" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Search for Snowflake operations
grep -n "SnowflakeHook\|snowflake\|execute_query" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 5. Analyze Function Dependencies
```bash
# Find imports used by functions
grep -n "^import \|^from " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Check for external library usage
grep -n "pandas\|numpy\|json\|csv\|xml" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 6. Check for Classes
```bash
# Find class definitions (potential Main class candidates)
grep -n "^class " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

## Classification Decision Tree

### COMMON COMPONENT (Belongs in `/common/`)
**Indicators**:
- SFTP/S3/Snowflake client implementations
- Generic API client patterns
- Reusable hook/operator logic
- Used by multiple DAGs

**Action**: Check if already exists in common/, otherwise flag for promotion

### SRC/MAIN.PY (Main class pattern)
**Indicators**:
- DAG-specific business logic
- Data transformation logic
- Orchestration helpers
- 50+ lines of complex logic

**Action**: Extract to `src/main.py` with `Main` class and `execute()` method

### @TASK FUNCTION (Inline TaskFlow)
**Indicators**:
- Simple, focused logic (<50 lines)
- Pure Python operations
- Single responsibility
- Returns data for downstream tasks

**Action**: Convert to @task decorator

### CONFIGURATION (src/config.py)
**Indicators**:
- Constants, mappings, settings
- Environment variable references
- Connection IDs
- Schema definitions

**Action**: Extract to `src/config.py`

## Output Report Format

After executing this skill, provide:

```markdown
## Business Logic Extraction Report: [dag_name]

### Functions Identified

#### 1. Function: `process_sftp_files` (Lines 45-195, 150 LOC)

**Current Implementation**: Custom SFTP client with paramiko

**Classification**: ❌ REDUNDANT - Use common component

**Reasoning**:
- Implements SFTP download, S3 upload, Snowflake load
- SFTPToSnowflakeOperator already exists in common/
- 150 lines of code can be replaced with operator configuration

**Action**:
```python
# DELETE this function
# REPLACE with:
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator
```

**LOC Saved**: 150 lines

---

#### 2. Function: `transform_data` (Lines 200-280, 80 LOC)

**Current Implementation**: Pandas data transformation

**Classification**: ✅ SRC/MAIN.PY - Extract to Main class

**Reasoning**:
- DAG-specific business logic
- Complex transformations (80 lines)
- Should be in Main class for testability

**Action**:
```python
# Create: src/main.py

class Main:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def transform_data(self, input_data):
        # Move 80 lines of transformation logic here
        pass

    def execute(self):
        # Main orchestration
        data = self.extract()
        transformed = self.transform_data(data)
        return transformed
```

**LOC Impact**: Move 80 lines to src/main.py

---

#### 3. Function: `validate_schema` (Lines 285-310, 25 LOC)

**Current Implementation**: Simple validation checks

**Classification**: ✅ @TASK - Convert to TaskFlow

**Reasoning**:
- Simple logic (<50 lines)
- Pure Python
- Single responsibility
- Returns boolean for branching

**Action**:
```python
@task
def validate_schema(data: dict) -> bool:
    # Move 25 lines of validation logic here
    return is_valid
```

**LOC Impact**: Convert to @task inline

---

#### 4. Function: `get_snowflake_connection` (Lines 320-345, 25 LOC)

**Current Implementation**: Custom Snowflake connection helper

**Classification**: ❌ REDUNDANT - Use common component

**Reasoning**:
- CustomSnowflakeHook already exists in common/
- Duplicates existing functionality

**Action**:
```python
# DELETE this function
# REPLACE with:
from common.custom_hooks.custom_snowflake_hook import CustomSnowflakeHook

hook = CustomSnowflakeHook(conn_id="snowflake_default")
```

**LOC Saved**: 25 lines

---

### Configuration Constants (Lines 15-40)

**Current Implementation**: Scattered throughout DAG file

**Classification**: ✅ CONFIG - Extract to src/config.py

**Constants Found**:
```python
SFTP_HOST = "sftp.example.com"
S3_BUCKET = "my-bucket"
SNOWFLAKE_SCHEMA = "raw_data"
TABLE_MAPPINGS = {...}
```

**Action**:
```python
# Create: src/config.py

SFTP_HOST = "sftp.example.com"
S3_BUCKET = "my-bucket"
SNOWFLAKE_SCHEMA = "raw_data"
TABLE_MAPPINGS = {...}
```

---

### Summary

| Function | LOC | Classification | Action | LOC Saved |
|----------|-----|----------------|--------|-----------|
| process_sftp_files | 150 | REDUNDANT | Use SFTPToSnowflakeOperator | 150 |
| transform_data | 80 | SRC/MAIN.PY | Extract to Main class | 0 (moved) |
| validate_schema | 25 | @TASK | Convert to TaskFlow | 0 (converted) |
| get_snowflake_connection | 25 | REDUNDANT | Use CustomSnowflakeHook | 25 |
| Constants | 25 | CONFIG | Extract to config.py | 0 (moved) |

**Total LOC in Legacy DAG**: 305 lines of logic + Airflow boilerplate

**Proposed Structure**:
```
dag_name/
├── main.py (DAG definition with @dag, @task) - ~50 lines
├── src/
│   ├── main.py (Main class with business logic) - ~80 lines
│   └── config.py (Configuration constants) - ~25 lines
```

**Total LOC in Modern DAG**: ~155 lines (50% reduction)

**LOC Eliminated via Common Components**: 175 lines

**DRY Compliance**: ✅ All redundant code replaced with common components

### Next Steps

1. ✅ Use SFTPToSnowflakeOperator from common/
2. ✅ Use CustomSnowflakeHook from common/
3. ✅ Extract transform_data to src/main.py with Main class
4. ✅ Convert validate_schema to @task
5. ✅ Move constants to src/config.py
6. ✅ Create modular DAG structure
```

## Enforcement

This skill MUST be executed:
- Before starting code migration
- When DAG contains 3+ function definitions
- When PythonOperators reference complex callables
- To ensure proper code organization

**Proper business logic extraction is critical for maintainable, testable, DRY-compliant DAGs.**
