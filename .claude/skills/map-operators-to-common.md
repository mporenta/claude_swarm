# Map Operators to Common Components Skill

## Purpose
Match legacy operators to existing common components, enforcing DRY principles by identifying opportunities to use existing operators instead of custom implementations.

## When to Use
**MANDATORY** after analyzing legacy DAG:
- After running `/analyze-legacy-dag`
- Before writing any custom operator code
- When custom operator patterns are identified
- To enforce reuse of common components

## Execution Steps

### 1. List Available Common Operators
```bash
# List all operators in common/
find /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators -name "*.py" -type f

# Get operator class names
grep -h "^class.*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*.py
```

### 2. Extract Legacy Operator Usage
```bash
# From the target legacy DAG
grep -n "Operator(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Get unique operator types
grep -o "[A-Za-z]*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sort -u
```

### 3. Search Common Operators by Functionality

#### For SFTP Operations:
```bash
grep -l "sftp\|SFTP" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*.py
grep -A 20 "class.*SFTP.*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*sftp*.py
```

#### For Snowflake Operations:
```bash
grep -l "snowflake\|Snowflake" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*.py
grep -A 20 "class.*Snowflake.*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*snowflake*.py
```

#### For S3 Operations:
```bash
grep -l "s3\|S3" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*.py
grep -A 20 "class.*S3.*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*s3*.py
```

#### For API Integrations:
```bash
# PestRoutes
grep -l "pestroutes\|PestRoutes" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*.py

# Google Sheets
grep -l "sheets\|Sheets" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*.py
```

### 4. Read Operator Parameters
```bash
# Read specific operator to understand parameters
# Example for SFTPToSnowflakeOperator
grep -A 50 "def __init__" /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/sftp_to_snowflake_operator.py
```

### 5. Identify Custom Python Functions
```bash
# Find PythonOperator usage with custom functions
grep -B 5 -A 10 "PythonOperator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | grep -A 5 "python_callable"
```

## Mapping Decision Matrix

### USE Existing Operator
**Criteria**: Operator exists and covers 80%+ of requirements

**Action**: Import and configure existing operator
```python
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

task = SFTPToSnowflakeOperator(
    task_id="sftp_task",
    sftp_conn_id="...",
    # ... configure parameters
)
```

### EXTEND Existing Operator
**Criteria**: Operator exists but needs 10-20% customization

**Action**: Create subclass with inheritance
```python
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

class CustomSFTPOperator(SFTPToSnowflakeOperator):
    def execute(self, context):
        # Custom pre-processing
        result = super().execute(context)
        # Custom post-processing
        return result
```

### CREATE New Operator
**Criteria**: No existing operator fits requirements

**Action**: Create new operator in DAG directory, document why common operators weren't suitable

## Output Report Format

After executing this skill, provide:

```markdown
## Operator Mapping Report: [dag_name]

**Available Common Operators**:
- SFTPToSnowflakeOperator
- CustomSheetsToSnowflakeOperator
- CrossDbOperator
- SnowflakeToS3StageOperator
- CustomPestRoutesToS3Operator
- [list all found]

---

### Mapping Analysis

#### 1. Legacy Operator: PythonOperator (python_callable=process_sftp)

**Functionality**: Downloads files from SFTP, uploads to S3, loads to Snowflake

**Common Operator Match**: SFTPToSnowflakeOperator
- **Location**: `common/custom_operators/sftp_to_snowflake_operator.py`
- **Match Percentage**: 95%
- **Decision**: ✅ USE
- **Reasoning**: Existing operator handles entire pipeline with configurable parameters

**Migration Code**:
```python
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

sftp_task = SFTPToSnowflakeOperator(
    task_id="sftp_to_snowflake",
    sftp_conn_id="my_sftp_conn",
    directory="/incoming",
    s3_prefix="data/incoming/",
    snowflake_query="SELECT max_date FROM control_table",
    use_flat_structure=True,
    determination_method="snowflake"
)
```

**LOC Reduction**: 150 lines → 9 lines (94% reduction)

---

#### 2. Legacy Operator: PythonOperator (python_callable=custom_transform)

**Functionality**: Custom data transformation logic

**Common Operator Match**: None
- **Decision**: ✅ CONVERT to @task
- **Reasoning**: Pure Python logic, no matching common operator, ideal for TaskFlow

**Migration Code**:
```python
@task
def custom_transform(input_data: dict) -> dict:
    # Business logic here
    return transformed_data
```

---

#### 3. Legacy Operator: CustomAPIOperator

**Functionality**: Custom API client with authentication and pagination

**Common Operator Match**: CustomPestRoutesToS3Operator
- **Location**: `common/custom_operators/custom_pestroutes_to_s3_operator.py`
- **Match Percentage**: 60%
- **Decision**: ⚠️ EVALUATE
- **Reasoning**: Similar pattern but different API

**Options**:
1. Extend CustomPestRoutesToS3Operator as template
2. Create new operator following similar pattern
3. Use generic HttpOperator if simpler

**Recommendation**: Review CustomPestRoutesToS3Operator implementation for patterns to reuse

---

### Summary

| Legacy Operator/Function | Common Match | Decision | LOC Saved |
|--------------------------|--------------|----------|-----------|
| process_sftp() | SFTPToSnowflakeOperator | USE | 150 |
| custom_transform() | None | @task | 0 |
| load_to_snowflake() | SnowflakeOperator | USE | 80 |
| custom_api_call() | Evaluate | EXTEND | TBD |

**Total LOC Reduction**: ~230 lines (estimated)

**DRY Compliance**: ✅ All mappings enforce code reuse

**Next Steps**:
1. Import identified common operators
2. Convert pure Python functions to @task
3. Evaluate custom operators for extension opportunities
```

## Enforcement

This skill MUST be executed:
- After analyzing legacy DAG structure
- Before implementing any custom operator
- When PythonOperator with complex logic is found
- To validate DRY compliance

**Failure to map operators to common components violates DRY and creates technical debt.**
