# Analyze Connection Usage Skill

## Purpose
Document connections and hooks used in the legacy DAG, mapping them to Airflow 2.x connection requirements and common hooks.

## When to Use
**RECOMMENDED** during migration:
- After analyzing legacy DAG structure
- Before implementing operators that need connections
- To ensure all connections are created in Airflow 2.x
- To identify common hooks that can be reused

## Execution Steps

### 1. Find Connection ID References
```bash
# Find all *_conn_id parameters
grep -n "_conn_id" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Extract connection IDs with context
grep -o "[a-z_]*_conn_id\s*=\s*['\"][^'\"]*['\"]" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sort -u
```

### 2. Find BaseHook.get_connection() Calls
```bash
# Find direct connection retrievals
grep -n "BaseHook.get_connection\|get_connection(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Get surrounding context
grep -B 3 -A 3 "get_connection" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 3. Identify Hook Usage
```bash
# Find hook instantiations
grep -n "Hook(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find specific hook types
grep -E "SnowflakeHook|S3Hook|HttpHook|SftpHook|PostgresHook|MySqlHook" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 4. Check for Custom Connection Logic
```bash
# Find custom connection handling
grep -n "boto3.client\|boto3.resource\|paramiko\|pymysql\|psycopg2" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find environment variable usage for credentials
grep -n "os.environ\|os.getenv" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 5. Search Common Hooks
```bash
# Check what hooks are available in common/
ls -1 /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_hooks/

# Search for specific hook types
find /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_hooks -name "*snowflake*" -o -name "*s3*" -o -name "*sftp*"
```

### 6. Map to Common Hooks
```bash
# For Snowflake
grep -l "Snowflake" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_hooks/*.py

# For S3
grep -l "S3" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_hooks/*.py

# For API integrations
grep -l "PestRoutes\|Sheets\|Http" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_hooks/*.py
```

## Connection Types

### Common Connection Types

| Connection Type | Conn ID Pattern | Common Hook Available? | Hook Location |
|----------------|-----------------|------------------------|---------------|
| Snowflake | `*_snowflake` or `snowflake_default` | ✅ Yes | `common/custom_hooks/custom_snowflake_hook.py` |
| AWS S3 | `aws_*` or `s3_conn` | ✅ Yes | `common/custom_hooks/custom_s3_hook.py` |
| SFTP | `*_sftp` | ⚠️ Check | Via operators |
| PestRoutes API | `pestroutes_*` | ✅ Yes | `common/custom_hooks/custom_pestroutes_hook.py` |
| Google Sheets | `google_sheets_*` | ✅ Yes | `common/custom_hooks/custom_google_sheets_hook.py` |
| HTTP/REST API | `http_*` | ⚠️ Standard | Built-in HttpHook |
| PostgreSQL | `postgres_*` | ⚠️ Standard | Built-in PostgresHook |
| MySQL | `mysql_*` | ⚠️ Standard | Built-in MySqlHook |

## Output Report Format

After executing this skill, provide:

```markdown
## Connection Usage Analysis Report: [dag_name]

### Connections Identified

#### 1. Connection: cresta_sftp

**Type**: SFTP
**Usage Locations**:
- Line 45: `SFTPHook(ssh_conn_id='cresta_sftp')`
- Line 78: Used in custom SFTP download function

**Connection Details Needed**:
- Host: sftp.cresta.com
- Username: [from Airflow connection]
- Password/Private Key: [from Airflow connection]
- Port: 22 (default)

**Common Hook Available**: ⚠️ No direct SFTP hook
**Recommended Approach**: Use `SFTPToSnowflakeOperator` from common/
```python
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

task = SFTPToSnowflakeOperator(
    task_id="sftp_task",
    sftp_conn_id="cresta_sftp",  # ✓ Use this connection
    directory="/incoming",
    s3_prefix="cresta/data/",
    snowflake_query="...",
)
```

**Migration Action**:
- ✅ Connection already exists in Airflow 2.x
- ✅ Use existing operator instead of custom hook code

---

#### 2. Connection: snowflake_default

**Type**: Snowflake
**Usage Locations**:
- Line 92: `SnowflakeHook(snowflake_conn_id='snowflake_default')`
- Line 105: `SnowflakeOperator(snowflake_conn_id='snowflake_default')`

**Connection Details Needed**:
- Account: [snowflake_account]
- Database: [database_name]
- Schema: [schema_name]
- Warehouse: [warehouse_name]
- Role: [role_name]
- User: [username]
- Password: [from Airflow connection]

**Common Hook Available**: ✅ Yes - `CustomSnowflakeHook`
**Location**: `common/custom_hooks/custom_snowflake_hook.py`

**Recommended Approach**:
```python
from common.custom_hooks.custom_snowflake_hook import CustomSnowflakeHook

# In @task function
hook = CustomSnowflakeHook(conn_id="snowflake_default")
results = hook.run_query("SELECT * FROM table")
```

**Capabilities** (from CustomSnowflakeHook):
- `run_query()` - Execute SQL and return results
- `execute_sql()` - Execute SQL without returning results
- `table_exists()` - Check if table exists
- `create_table()` - Create table from schema
- `bulk_load()` - Bulk insert data

**Migration Action**:
- ✅ Use CustomSnowflakeHook instead of standard SnowflakeHook
- ✅ Connection already exists in Airflow 2.x

---

#### 3. Connection: aws_default

**Type**: AWS (S3)
**Usage Locations**:
- Line 120: `S3Hook(aws_conn_id='aws_default')`
- Line 135: Custom boto3 client creation

**Connection Details Needed**:
- AWS Access Key ID: [from Airflow connection]
- AWS Secret Access Key: [from Airflow connection]
- Region: us-east-1 (default)

**Common Hook Available**: ✅ Yes - `CustomS3Hook`
**Location**: `common/custom_hooks/custom_s3_hook.py`

**Recommended Approach**:
```python
from common.custom_hooks.custom_s3_hook import CustomS3Hook

hook = CustomS3Hook(aws_conn_id="aws_default")
hook.upload_file(local_path, bucket, s3_key)
```

**Capabilities** (from CustomS3Hook):
- `upload_file()` - Upload file to S3
- `download_file()` - Download file from S3
- `list_objects()` - List objects with prefix
- `delete_objects()` - Delete objects

**Anti-Pattern Detected**:
```python
# ❌ WRONG - Direct boto3 usage (Line 135)
import boto3
s3_client = boto3.client('s3')
s3_client.upload_file(...)

# ✅ CORRECT - Use CustomS3Hook
from common.custom_hooks.custom_s3_hook import CustomS3Hook
hook = CustomS3Hook(aws_conn_id="aws_default")
hook.upload_file(...)
```

**Migration Action**:
- ✅ Replace direct boto3 usage with CustomS3Hook
- ✅ Connection already exists in Airflow 2.x

---

### Summary

| Connection ID | Type | Lines | Common Hook? | Migration Action |
|---------------|------|-------|--------------|------------------|
| cresta_sftp | SFTP | 45, 78 | Use Operator | Replace with SFTPToSnowflakeOperator |
| snowflake_default | Snowflake | 92, 105 | ✅ CustomSnowflakeHook | Use CustomSnowflakeHook |
| aws_default | S3 | 120, 135 | ✅ CustomS3Hook | Replace boto3 with CustomS3Hook |

**Total Connections**: 3
**Common Hooks Available**: 2
**Operators Available**: 1

---

### Anti-Patterns Found

#### ❌ Direct boto3 Usage (Line 135)
**Problem**: Bypasses Airflow connection management
**Solution**: Use CustomS3Hook with aws_default connection

#### ❌ Custom SFTP Client (Lines 45-95)
**Problem**: 150 lines of duplicate code
**Solution**: Use SFTPToSnowflakeOperator from common/

---

### Connection Checklist for Airflow 2.x

Ensure these connections exist in Airflow 2.x environment:

#### cresta_sftp
```bash
# Add via Airflow UI or CLI
airflow connections add 'cresta_sftp' \
    --conn-type 'ssh' \
    --conn-host 'sftp.cresta.com' \
    --conn-login 'username' \
    --conn-password 'password' \
    --conn-port 22
```

#### snowflake_default
```bash
airflow connections add 'snowflake_default' \
    --conn-type 'snowflake' \
    --conn-login 'username' \
    --conn-password 'password' \
    --conn-schema 'schema_name' \
    --conn-extra '{"account": "account_name", "warehouse": "warehouse_name", "database": "database_name", "role": "role_name"}'
```

#### aws_default
```bash
airflow connections add 'aws_default' \
    --conn-type 'aws' \
    --conn-login 'AWS_ACCESS_KEY_ID' \
    --conn-password 'AWS_SECRET_ACCESS_KEY' \
    --conn-extra '{"region_name": "us-east-1"}'
```

---

### Migration Priority

**High Priority** (Blocker):
1. ✅ Use CustomSnowflakeHook for Snowflake operations
2. ✅ Use CustomS3Hook for S3 operations
3. ✅ Use SFTPToSnowflakeOperator for SFTP pipeline

**Medium Priority** (Improvement):
- Consider consolidating connection usage patterns
- Document connection requirements in DAG

**Low Priority** (Optional):
- Add connection validation in DAG initialization
```

## Enforcement

This skill SHOULD be executed:
- When operators use *_conn_id parameters
- When custom connection logic is detected
- To map connections to common hooks
- To ensure connection compatibility with Airflow 2.x

**Proper connection management and hook usage ensures secure, maintainable connection handling.**
