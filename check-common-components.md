# Check Common Components Skill

## Purpose
Enforce DRY (Don't Repeat Yourself) by verifying existing common components before writing custom code.

## When to Use
**MANDATORY** before creating any:
- Custom operators
- Custom hooks
- Custom utilities
- SFTP/S3/Snowflake integration code
- API client implementations

## Execution Steps

### 1. Search Common Directory
```bash
# Search for operators
find /home/dev/claude_dev/airflow/data-airflow/dags/common/custom_operators -name "*.py" -type f

# Search for hooks
find /home/dev/claude_dev/airflow/data-airflow/dags/common/custom_hooks -name "*.py" -type f

# Search for callbacks
find /home/dev/claude_dev/airflow/data-airflow/dags/common/custom_callbacks -name "*.py" -type f
```

### 2. Search for Relevant Functionality
When you need specific functionality, search by keyword:

```bash
# Example: Search for SFTP-related code
grep -r "sftp" /home/dev/claude_dev/airflow/data-airflow/dags/common --include="*.py" -i

# Example: Search for Snowflake operators
grep -r "class.*Snowflake.*Operator" /home/dev/claude_dev/airflow/data-airflow/dags/common --include="*.py"

# Example: Search for S3 hooks
grep -r "class.*S3.*Hook" /home/dev/claude_dev/airflow/data-airflow/dags/common --include="*.py"
```

### 3. Read Existing Implementation
Before deciding to write custom code, READ the existing implementation:

```bash
# Read the operator/hook to understand its capabilities
# Example: Read SFTP operator
cat /home/dev/claude_dev/airflow/data-airflow/dags/common/custom_operators/sftp_to_snowflake_operator.py
```

### 4. Decision Matrix

**If component exists and meets 80%+ of requirements:**
- ✅ USE the existing component directly
- Document why it was chosen
- Configure parameters to match use case

**If component exists but needs minor extension:**
- ✅ EXTEND via inheritance
- Create subclass in DAG directory
- Override only necessary methods
- Document extensions

**If component doesn't exist:**
- ✅ CREATE new component in DAG directory
- Document why existing components weren't suitable
- Consider if it should be promoted to `common/` later

## Available Common Components

### Custom Operators (`common/custom_operators/`)
- **SFTPToSnowflakeOperator**: SFTP → S3 → Snowflake pipeline
  - Supports: manifest tracking, Snowflake date filtering, flat/nested structures
  - Parameters: sftp_conn_id, directory, s3_prefix, snowflake_query, use_flat_structure, determination_method

- **CustomSheetsToSnowflakeOperator**: Google Sheets → Snowflake
  - Supports: range selection, schema/table specification, column DDL

- **CrossDbOperator**: Cross-database SQL operations

- **SnowflakeToS3StageOperator**: Snowflake → S3 staging

- **SnowflakeToPestroutesOperator**: Snowflake → PestRoutes API

- **SnowflakeExternalTableOperator**: External table creation/management

- **CustomSparkKubernetesOperator**: Spark jobs on Kubernetes

- **TriggerDbtJobOperator**: dbt Cloud job triggering

- **CustomPestRoutesToS3Operator**: PestRoutes API → S3
  - Supports 20+ entity types (appointments, customers, tickets, etc.)

### Custom Hooks (`common/custom_hooks/`)
- **CustomSnowflakeHook**: Enhanced Snowflake operations
  - Methods: run_query, execute_sql, table_exists, create_table

- **CustomExternalTableHook**: External table management

- **CustomS3Hook**: S3 operations with prefix support
  - Methods: upload_file, download_file, list_objects

- **S3ToSnowflakeHook**: S3 → Snowflake data loading

- **S3ToSnowflakeInsertHook**: S3 → Snowflake inserts

- **CustomPestRoutesHook**: PestRoutes API integration

- **CustomGoogleSheetsHook**: Google Sheets API

### Custom Callbacks (`common/custom_callbacks/`)
- **AirflowCallback**: Standard success/failure callbacks
  - Features: Slack notifications, error logging, metrics

## Example Usage

### ❌ WRONG - Creating Duplicate
```python
# DON'T: Create custom SFTP client
class SFTPClient:
    def __init__(self, host, username, password): ...
    def connect(self): ...
    def download_file(self): ...

def execute_sftp_pipeline(): ...
```

### ✅ CORRECT - Using Existing
```python
# DO: Use existing operator
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

sftp_task = SFTPToSnowflakeOperator(
    task_id="sftp_to_snowflake",
    sftp_conn_id="my_sftp_conn",
    directory="/incoming",
    s3_prefix="my_data/",
    snowflake_query="SELECT date FROM control_dates",
    use_flat_structure=True,
    determination_method="snowflake"
)
```

### ✅ CORRECT - Extending Existing
```python
# DO: Extend if custom behavior needed
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

class CustomSFTPOperator(SFTPToSnowflakeOperator):
    def __init__(self, custom_param: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_param = custom_param

    def execute(self, context):
        self.log.info(f"Custom processing: {self.custom_param}")
        return super().execute(context)
```

## Output Report Format

After executing this skill, provide:

```markdown
## Common Components Check Report

**Task**: [Describe what you're trying to implement]

**Search Results**:
- Found [N] operators in common/custom_operators/
- Found [N] hooks in common/custom_hooks/
- Found [N] callbacks in common/custom_callbacks/

**Relevant Components**:
1. [Component Name] at [file path]
   - Capabilities: [list what it does]
   - Match: [X]% fit for requirements

**Decision**: [USE | EXTEND | CREATE]

**Reasoning**: [Explain why this decision was made]

**Implementation Plan**:
- [Step 1]
- [Step 2]
- [Step 3]
```

## Enforcement

This skill MUST be executed:
- Before creating any new operator class
- Before creating any new hook class
- Before implementing SFTP/S3/Snowflake/API client code
- When you see phrases like "I'll create a custom..." in your reasoning

**Failure to use this skill when required is a critical error that violates DRY principles.**
