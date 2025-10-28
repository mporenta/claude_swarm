# Find Anti-Patterns Skill

## Purpose
Detect DRY violations, code smells, and anti-patterns in legacy DAGs that should be addressed during migration.

## When to Use
**RECOMMENDED** during initial analysis:
- After analyzing legacy DAG structure
- Before starting implementation
- To identify technical debt
- To prioritize refactoring opportunities

## Execution Steps

### 1. Detect Custom SFTP Implementations
```bash
# Search for SFTP-related code
grep -n "sftp\|SFTP\|paramiko\|pysftp" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Check for SFTP classes/functions
grep -B 2 -A 10 "class.*SFTP\|def.*sftp" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py -i
```

### 2. Detect Direct AWS SDK Usage
```bash
# Search for direct boto3/botocore usage
grep -n "boto3\|botocore" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Check for S3 client creation
grep -n "boto3.client\|boto3.resource" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 3. Detect Custom Database Clients
```bash
# Search for direct DB library usage
grep -n "pymysql\|psycopg2\|mysql.connector\|cx_Oracle" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Check for custom connection logic
grep -n "\.connect(\|\.Connection(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 4. Detect Hardcoded Credentials
```bash
# Search for credential patterns (security risk!)
grep -n "password\s*=\|api_key\s*=\|secret\s*=" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py -i

# Check for hardcoded URLs/hostnames
grep -n "http://\|https://" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find environment variable usage (better, but check if should use connections)
grep -n "os.environ\|os.getenv" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 5. Detect Overly Complex Single Files
```bash
# Count lines of code
LOC=$(wc -l < /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
if [ $LOC -gt 300 ]; then
    echo "⚠ Anti-pattern: DAG file too large ($LOC lines)"
fi

# Count functions
FUNC_COUNT=$(grep -c "^def " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
if [ $FUNC_COUNT -gt 10 ]; then
    echo "⚠ Anti-pattern: Too many functions ($FUNC_COUNT) - consider extracting to modules"
fi
```

### 6. Detect Repeated Patterns Across DAGs
```bash
# Compare with other legacy DAGs for similar code patterns
# Example: Find other DAGs with similar SFTP logic
for dag in /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/*.py; do
    if grep -q "paramiko\|pysftp" "$dag" 2>/dev/null; then
        echo "Found SFTP code in: $(basename $dag)"
    fi
done
```

### 7. Detect Missing Error Handling
```bash
# Check for try/except blocks
TRY_COUNT=$(grep -c "try:" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
OPERATOR_COUNT=$(grep -c "Operator(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)

if [ $TRY_COUNT -eq 0 ] && [ $OPERATOR_COUNT -gt 5 ]; then
    echo "⚠ Anti-pattern: No error handling in complex DAG"
fi
```

### 8. Detect Deprecated Airflow Patterns
```bash
# Check for deprecated imports
grep -n "from airflow.operators.python_operator import" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "from airflow.contrib" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "provide_context=True" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Check for Variable.get() without defaults (can cause import errors)
grep -n "Variable.get(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 9. Detect Missing Callbacks
```bash
# Check if callbacks are used
CALLBACK_COUNT=$(grep -c "on_failure_callback\|on_success_callback" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)

if [ $CALLBACK_COUNT -eq 0 ]; then
    echo "⚠ Missing callbacks - should use AirflowCallback from common/"
fi
```

### 10. Check Against Common Operators
```bash
# This is a quick check - detailed check is in /check-common-components
echo "Quick check for replaceable patterns:"

# SFTP patterns
if grep -q "paramiko\|pysftp" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py; then
    echo "⚠ SFTP code detected - check SFTPToSnowflakeOperator"
fi

# PestRoutes patterns
if grep -q "pestroutes\|PestRoutes" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py -i; then
    echo "⚠ PestRoutes code detected - check CustomPestRoutesToS3Operator"
fi

# Google Sheets patterns
if grep -q "googleapiclient\|gspread" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py; then
    echo "⚠ Google Sheets code detected - check CustomSheetsToSnowflakeOperator"
fi
```

## Anti-Pattern Categories

### Category 1: DRY Violations (Critical)
- Custom SFTP/S3/Snowflake implementations
- Duplicated code from other DAGs
- Reimplementing existing common components

**Impact**: High technical debt, maintenance burden
**Priority**: CRITICAL - Must fix during migration

### Category 2: Security Issues (Critical)
- Hardcoded credentials
- Passwords in plain text
- API keys in code

**Impact**: Security vulnerability
**Priority**: CRITICAL - Must fix immediately

### Category 3: Complexity Anti-Patterns (High)
- Single file >300 LOC
- Functions >100 LOC
- 10+ functions in one file
- Deep nesting (>4 levels)

**Impact**: Maintainability, testability
**Priority**: HIGH - Refactor during migration

### Category 4: Airflow 1.x Deprecated Patterns (Medium)
- Old imports
- `provide_context=True`
- Missing callbacks
- No error handling

**Impact**: Compatibility, observability
**Priority**: MEDIUM - Fix during migration

### Category 5: Code Smells (Low)
- Poor naming conventions
- Missing type hints
- No docstrings
- Commented-out code

**Impact**: Code quality
**Priority**: LOW - Improve if time permits

## Output Report Format

After executing this skill, provide:

```markdown
## Anti-Pattern Detection Report: [dag_name]

### 🚨 CRITICAL Issues (Must Fix)

#### 1. DRY Violation: Custom SFTP Implementation (Lines 45-195)

**Pattern**: Custom SFTP client with paramiko

**Code Sample**:
```python
# Lines 45-95
class SFTPClient:
    def __init__(self, host, username, private_key):
        self.host = host
        self.username = username
        self.private_key = private_key
        # ... 50 lines of SFTP logic

    def download_file(self, remote_path, local_path):
        # ... 30 lines of download logic

    def upload_to_s3(self, file_path, bucket, key):
        # ... 40 lines of S3 upload logic

# Lines 120-195
def execute_sftp_pipeline(**context):
    # ... 75 lines using SFTPClient
```

**Why This Is An Anti-Pattern**:
- ❌ 150 lines of redundant code
- ❌ SFTPToSnowflakeOperator already exists in common/
- ❌ Duplicates functionality with no added value
- ❌ Must maintain separately from common implementation
- ❌ No unit tests for custom code

**Available Alternative**:
```python
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

task = SFTPToSnowflakeOperator(
    task_id="sftp_task",
    sftp_conn_id="cresta_sftp",
    directory="/incoming",
    s3_prefix="cresta/data/",
    snowflake_query="SELECT max_date FROM control_table",
    use_flat_structure=True,
)
```

**Impact**:
- Technical debt: 150 lines to maintain
- DRY violation: Duplicates tested code
- Risk: Custom implementation may have bugs

**Action**: ✅ **REPLACE** with SFTPToSnowflakeOperator

**LOC Saved**: 150 lines (35% of DAG)

**Priority**: 🔴 **CRITICAL**

---

#### 2. DRY Violation: Direct boto3 Usage (Lines 135-160)

**Pattern**: Custom boto3 client instead of hook

**Code Sample**:
```python
import boto3

def upload_to_s3(**context):
    s3_client = boto3.client('s3',
        aws_access_key_id=os.environ['AWS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET']
    )
    s3_client.upload_file(local_file, bucket, key)
```

**Why This Is An Anti-Pattern**:
- ❌ Bypasses Airflow connection management
- ❌ Credentials in environment variables (should use connections)
- ❌ CustomS3Hook already exists in common/
- ❌ No retry logic or error handling
- ❌ Harder to test and mock

**Available Alternative**:
```python
from common.custom_hooks.custom_s3_hook import CustomS3Hook

def upload_to_s3(**context):
    hook = CustomS3Hook(aws_conn_id="aws_default")
    hook.upload_file(local_file, bucket, key)
```

**Impact**:
- Security: Credentials not managed properly
- Maintainability: Custom error handling needed
- Testing: Difficult to mock boto3 client

**Action**: ✅ **REPLACE** with CustomS3Hook

**LOC Saved**: 25 lines

**Priority**: 🔴 **CRITICAL**

---

#### 3. Security Issue: Hardcoded Credentials (Line 67)

**Pattern**: Password in plain text

**Code Sample**:
```python
SFTP_PASSWORD = "my_secret_password_123"  # Line 67
```

**Why This Is An Anti-Pattern**:
- ❌ **SECURITY VULNERABILITY** - Credentials in source code
- ❌ Visible in git history
- ❌ No encryption
- ❌ Shared across team

**Required Action**:
```python
# Use Airflow connection instead
# Set via UI: Admin > Connections > cresta_sftp
# Or CLI:
# airflow connections add 'cresta_sftp' --conn-type 'ssh' --conn-password '***'

# In code:
hook = SFTPHook(ssh_conn_id="cresta_sftp")  # Password from connection
```

**Impact**: 🔴 **SECURITY RISK** - Immediate fix required

**Action**: ✅ **REMOVE** hardcoded credential, use Airflow connection

**Priority**: 🔴 **CRITICAL - SECURITY**

---

### ⚠️ HIGH Priority Issues (Should Fix)

#### 4. Complexity Anti-Pattern: Oversized DAG File (425 LOC)

**Pattern**: Single file with 425 lines

**Why This Is An Anti-Pattern**:
- ⚠️ Difficult to navigate and understand
- ⚠️ Hard to test individual components
- ⚠️ Mixing concerns (DAG definition + business logic + utilities)
- ⚠️ Violates separation of concerns

**Recommended Structure**:
```
cresta_to_snowflake/
├── main.py (DAG definition, ~50 lines)
├── src/
│   ├── main.py (Main class with business logic, ~80 lines)
│   └── config.py (Configuration, ~25 lines)
```

**Impact**: Maintainability suffers

**Action**: ✅ **REFACTOR** to modular structure

**LOC After Refactor**: ~155 lines (63% reduction)

**Priority**: 🟡 **HIGH**

---

#### 5. Missing Standard Callbacks (No callbacks found)

**Pattern**: No failure or success callbacks

**Why This Is An Anti-Pattern**:
- ⚠️ No alerting when DAG fails
- ⚠️ No visibility into failures
- ⚠️ Doesn't follow team standards

**Available Solution**:
```python
from common.custom_callbacks.custom_callbacks import AirflowCallback

default_args = {
    'on_failure_callback': AirflowCallback.failure_callback,
    'on_success_callback': AirflowCallback.success_callback,
}
```

**Impact**: Observability and alerting

**Action**: ✅ **ADD** AirflowCallback from common/

**Priority**: 🟡 **HIGH**

---

### 📋 MEDIUM Priority Issues (Fix During Migration)

#### 6. Deprecated Imports (Lines 1-15)

**Pattern**: Old-style imports

**Code Sample**:
```python
from airflow.operators.python_operator import PythonOperator  # Deprecated
from airflow.contrib.hooks.snowflake_hook import SnowflakeHook  # Moved
```

**Modern Imports**:
```python
from airflow.decorators import dag, task  # Use TaskFlow
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
```

**Action**: ✅ **UPDATE** imports during migration

**Priority**: 🟢 **MEDIUM**

---

#### 7. Missing Error Handling (No try/except blocks)

**Pattern**: No exception handling in 8 functions

**Why This Is An Anti-Pattern**:
- ⚠️ Errors bubble up without context
- ⚠️ No custom error messages
- ⚠️ Difficult to debug failures

**Recommended Pattern**:
```python
@task
def process_data():
    try:
        result = risky_operation()
        return result
    except SpecificException as e:
        logger.error(f"Failed to process data: {e}")
        raise AirflowException(f"Processing failed: {e}")
```

**Action**: ✅ **ADD** error handling to critical functions

**Priority**: 🟢 **MEDIUM**

---

### 📝 LOW Priority Issues (Nice to Have)

#### 8. Missing Type Hints

**Pattern**: No type annotations

**Improvement**:
```python
# Current
def transform_data(data):
    return process(data)

# Improved
def transform_data(data: dict) -> dict:
    return process(data)
```

**Priority**: 🔵 **LOW**

---

### Summary

| Category | Count | Priority | Must Fix? |
|----------|-------|----------|-----------|
| DRY Violations | 2 | 🔴 CRITICAL | ✅ Yes |
| Security Issues | 1 | 🔴 CRITICAL | ✅ Yes |
| Complexity Issues | 2 | 🟡 HIGH | ✅ Yes |
| Deprecated Patterns | 3 | 🟢 MEDIUM | ⚠️ During migration |
| Code Smells | 2 | 🔵 LOW | ❌ Optional |

**Total Issues Found**: 10

**Critical Issues**: 3 (must fix)
**High Priority**: 2 (should fix)

**Total LOC That Can Be Eliminated**: 175 lines (41% of DAG)

**Biggest Win**: Replace custom SFTP implementation with SFTPToSnowflakeOperator (150 lines saved)

---

### Recommended Actions (Priority Order)

1. 🔴 **CRITICAL**: Remove hardcoded password, use Airflow connection
2. 🔴 **CRITICAL**: Replace custom SFTP code with SFTPToSnowflakeOperator (run `/check-common-components`)
3. 🔴 **CRITICAL**: Replace boto3 with CustomS3Hook
4. 🟡 **HIGH**: Refactor to modular structure (src/main.py pattern)
5. 🟡 **HIGH**: Add AirflowCallback from common/
6. 🟢 **MEDIUM**: Update deprecated imports during migration
7. 🟢 **MEDIUM**: Add error handling to critical functions
8. 🔵 **LOW**: Add type hints (if time permits)

---

### Next Steps

1. ✅ Run `/check-common-components` to confirm operator replacements
2. ✅ Run `/map-operators-to-common` for detailed mapping
3. ✅ Remove security issue immediately (hardcoded password)
4. ✅ Begin migration with anti-pattern fixes as primary goal
```

## Enforcement

This skill SHOULD be executed:
- After analyzing legacy DAG structure
- Before starting implementation
- To identify technical debt
- To prioritize refactoring work

**Identifying anti-patterns early ensures they are addressed during migration rather than carried forward.**
