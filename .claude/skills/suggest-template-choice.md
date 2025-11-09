# Suggest Template Choice Skill

## Purpose
Recommend TaskFlow vs Traditional template based on DAG complexity, operator types, and migration goals.

## When to Use
**RECOMMENDED** early in migration:
- After analyzing legacy DAG structure
- Before starting implementation
- To choose correct starting template
- When team needs guidance on approach

## Execution Steps

### 1. Count Operator Types
```bash
# Get all unique operator types
grep -o "[A-Za-z]*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sort | uniq -c | sort -rn

# Count PythonOperator specifically
PYTHON_OP_COUNT=$(grep -c "PythonOperator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "PythonOperator count: $PYTHON_OP_COUNT"

# Count all operators
TOTAL_OP_COUNT=$(grep -c "Operator(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "Total operators: $TOTAL_OP_COUNT"
```

### 2. Identify Non-Python Operators
```bash
# Find operators that can't be converted to @task
grep -E "BashOperator|SnowflakeOperator|EmailOperator|HttpOperator|S3Operator|SFTPOperator|DockerOperator|KubernetesPodOperator|SparkSubmitOperator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 3. Check for Custom Operators
```bash
# Find custom operator usage
grep -n "from common.custom_operators" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "from .*operators import.*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | grep -v "python_operator"
```

### 4. Analyze Data Flow Complexity
```bash
# Count XCom usage (indicator of data passing)
XCOM_COUNT=$(grep -c "xcom_push\|xcom_pull" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "XCom operations: $XCOM_COUNT"

# Count dependencies (complexity indicator)
DEP_COUNT=$(grep -c " >> \| << " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "Dependency statements: $DEP_COUNT"
```

### 5. Check Template Availability
```bash
# Verify templates exist
ls -la /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/_dag_taskflow_template/
ls -la /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/_dag_template/
```

### 6. Assess LOC and Complexity
```bash
# Total lines
LOC=$(wc -l < /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "Lines of code: $LOC"

# Function count
FUNC_COUNT=$(grep -c "^def " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "Functions: $FUNC_COUNT"
```

## Template Comparison

### TaskFlow Template (`_dag_taskflow_template/`)

**Best For**:
- Pure Python workflows
- Heavy data passing between tasks
- Simple to medium complexity
- When 90%+ tasks are Python

**Characteristics**:
```python
from airflow.decorators import dag, task
from pendulum import datetime

@dag(
    schedule='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['taskflow'],
)
def my_dag():
    @task
    def extract() -> dict:
        return data

    @task
    def transform(data: dict) -> dict:
        return transformed

    # Data flow pattern
    transform(extract())

my_dag()
```

**Advantages**:
- ✅ Clean, concise syntax
- ✅ Automatic XCom handling
- ✅ Type hints for data safety
- ✅ Implicit dependencies via data flow
- ✅ Less boilerplate

**Limitations**:
- ⚠️ Python-only (can mix with explicit operators, but less clean)
- ⚠️ Learning curve for explicit dependencies when needed
- ⚠️ Must call decorated function at end

**Template Structure**:
```
_dag_taskflow_template/
├── main.py          # DAG definition with @dag/@task
├── src/
│   ├── main.py      # Main class with business logic
│   └── config.py    # Configuration constants
└── README.md
```

---

### Traditional Template (`_dag_template/`)

**Best For**:
- Mixed operator types (Python + Bash + Snowflake + Custom)
- Complex custom operators
- When explicit control needed
- Team familiar with Airflow 1.x patterns

**Characteristics**:
```python
from airflow.decorators import dag, task
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator

@dag(
    schedule='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['traditional'],
)
def my_dag():
    @task
    def extract():
        return data

    # Mix @task with traditional operators
    sftp_task = SFTPToSnowflakeOperator(
        task_id='sftp_load',
        sftp_conn_id='my_sftp',
        # ...
    )

    snowflake_task = SnowflakeOperator(
        task_id='run_query',
        snowflake_conn_id='snowflake_default',
        sql='SELECT * FROM table',
    )

    # Explicit dependencies
    extract() >> sftp_task >> snowflake_task

my_dag()
```

**Advantages**:
- ✅ Supports all operator types
- ✅ Familiar to Airflow 1.x users
- ✅ Explicit dependency control
- ✅ Can still use @task for Python portions

**Limitations**:
- ⚠️ More verbose
- ⚠️ Manual XCom if needed
- ⚠️ Less type safety

**Template Structure**:
```
_dag_template/
├── main.py          # DAG definition (mixed operators)
├── src/
│   ├── main.py      # Main class with business logic
│   └── config.py    # Configuration
└── README.md
```

## Decision Matrix

### Choose **TaskFlow Template** If:

1. **Python-Heavy**: ≥90% PythonOperators
2. **Data-Intensive**: Heavy data passing between tasks (many XCom operations)
3. **Simple to Medium**: <10 tasks, straightforward dependencies
4. **Modern Approach**: Team wants cleanest, most modern code
5. **No Custom Operators**: Uses only built-in operators or @task

**Formula**:
```
TaskFlow Score = (PythonOperator_count / Total_operators) * 100
If score ≥ 90% → TaskFlow Template
```

---

### Choose **Traditional Template** If:

1. **Mixed Operators**: Uses Snowflake, Bash, Email, HTTP, or other non-Python operators
2. **Custom Operators**: Uses operators from `common/custom_operators/`
3. **Complex**: >10 tasks, complex dependency graphs, branching
4. **Team Preference**: Team more comfortable with explicit patterns
5. **Provider Operators**: Heavy use of provider packages

**Formula**:
```
Non-Python Score = (Non_Python_operators / Total_operators) * 100
If score ≥ 20% → Traditional Template
```

---

### Hybrid Approach (Traditional Template + TaskFlow)

**When**: Mixed operator types but want TaskFlow benefits for Python portions

**Pattern**:
```python
@dag(...)
def my_dag():
    # TaskFlow for Python tasks
    @task
    def python_task() -> dict:
        return data

    # Traditional for other operators
    snowflake_task = SnowflakeOperator(...)
    custom_task = CustomOperator(...)

    # Mix dependencies
    data = python_task()
    data >> snowflake_task >> custom_task
```

## Output Report Format

After executing this skill, provide:

```markdown
## Template Recommendation Report: [dag_name]

### Operator Analysis

**Total Operators**: 12

**Operator Breakdown**:
| Operator Type | Count | Percentage | Can Convert to @task? |
|---------------|-------|------------|-----------------------|
| PythonOperator | 5 | 42% | ✅ Yes |
| SnowflakeOperator | 3 | 25% | ❌ No (use as-is) |
| BashOperator | 2 | 17% | ⚠️ Maybe (simple scripts) |
| Custom (SFTP) | 2 | 17% | ❌ No (from common/) |

**Python vs Non-Python**:
- Python tasks: 5 (42%)
- Non-Python tasks: 7 (58%)

---

### Complexity Metrics

**Size**:
- Lines of code: 425
- Functions: 8
- Tasks: 12

**Data Flow**:
- XCom operations: 10
- Dependencies: 8 statements
- Branching: 1 (BranchPythonOperator)

**Complexity Level**: MEDIUM-HIGH

---

### Template Recommendation

## 🎯 Recommended Template: **Traditional Template** (`_dag_template/`)

### Reasoning

**Primary Factors**:
1. ❌ **Mixed Operator Types** (58% non-Python)
   - 3 SnowflakeOperators (can't convert to @task)
   - 2 Custom SFTPToSnowflakeOperators (from common/)
   - 2 BashOperators (could convert, but traditional is fine)

2. ✅ **Custom Operators Present**
   - Uses `SFTPToSnowflakeOperator` from common/
   - Custom operators work better with traditional pattern

3. ⚠️ **Medium-High Complexity**
   - 12 tasks with complex dependencies
   - Branching logic present
   - Traditional template provides explicit control

**Score Calculation**:
- TaskFlow Score: 42% (< 90% threshold)
- Non-Python Score: 58% (> 20% threshold)
- **Result**: Traditional Template

---

### Implementation Approach

#### Use **Hybrid Pattern** (Recommended)

Combine traditional operators with TaskFlow for Python portions:

```python
from airflow.decorators import dag, task
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from common.custom_operators.sftp_to_snowflake_operator import SFTPToSnowflakeOperator
from pendulum import datetime

@dag(
    dag_id='my_dag',
    schedule='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['production', 'hybrid'],
)
def my_dag():
    # TaskFlow for Python business logic (5 tasks)
    @task
    def extract_metadata() -> dict:
        """Pure Python extraction logic."""
        return metadata

    @task
    def validate_data(data: dict) -> bool:
        """Pure Python validation."""
        return is_valid

    @task
    def prepare_query(metadata: dict) -> str:
        """Generate SQL query from metadata."""
        return sql_query

    # Traditional operators for non-Python tasks
    sftp_load = SFTPToSnowflakeOperator(
        task_id='sftp_to_snowflake',
        sftp_conn_id='my_sftp',
        directory='/incoming',
        s3_prefix='data/',
        snowflake_query='SELECT max_date FROM control',
    )

    run_query = SnowflakeOperator(
        task_id='run_snowflake_query',
        snowflake_conn_id='snowflake_default',
        sql='{{ ti.xcom_pull(task_ids="prepare_query") }}',
    )

    post_process = BashOperator(
        task_id='archive_files',
        bash_command='mv /incoming/* /archive/',
    )

    # Mix data flow and explicit dependencies
    metadata = extract_metadata()
    valid = validate_data(metadata)
    query = prepare_query(metadata)

    # Explicit dependencies
    valid >> sftp_load >> run_query >> post_process

my_dag()
```

**Benefits of Hybrid**:
- ✅ TaskFlow benefits for Python tasks (5 tasks)
- ✅ Traditional operators for specialized work (7 tasks)
- ✅ Clean, type-safe Python code
- ✅ Explicit control where needed
- ✅ Best of both worlds

---

### Alternative: Pure TaskFlow (Not Recommended)

**Why Not Pure TaskFlow**:
- ❌ 58% of operators are non-Python
- ❌ Mixing @task with SnowflakeOperator is less clean
- ❌ Custom operators (SFTP) don't benefit from TaskFlow
- ❌ Would require more boilerplate to integrate non-Python operators

**Only use if**: You can convert all operators to Python equivalents (not recommended here)

---

### Template Structure

Based on `_dag_template/`, create:

```
my_dag/
├── main.py                 # DAG definition (hybrid pattern)
│   ├── @dag decorator with config
│   ├── @task functions for Python logic
│   ├── Traditional operators for Snowflake/SFTP/Bash
│   └── Mixed dependencies
│
├── src/
│   ├── main.py            # Main class with business logic
│   │   └── Main.execute() method
│   └── config.py          # Configuration constants
│
└── README.md              # DAG documentation
```

**File Sizes (Estimated)**:
- `main.py`: ~80 lines (DAG definition)
- `src/main.py`: ~100 lines (business logic)
- `src/config.py`: ~30 lines (config)
- Total: ~210 lines (vs 425 in legacy = 50% reduction)

---

### Migration Plan

**Phase 1: Convert Python Tasks**
- Convert 5 PythonOperators → @task decorators
- Add type hints
- Use data flow pattern where possible

**Phase 2: Integrate Non-Python Operators**
- Keep 3 SnowflakeOperators as-is
- Keep 2 SFTPToSnowflakeOperators (from common/)
- Update 2 BashOperators (or convert to @task if simple)

**Phase 3: Dependencies**
- Data flow for Python task chains
- Explicit `>>` for non-Python dependencies
- Mix patterns where they meet

**Phase 4: Testing**
- Test Python @task functions in isolation
- Test operator configuration
- Test end-to-end DAG execution

---

### Comparison Summary

| Criteria | Pure TaskFlow | Hybrid (Recommended) | Pure Traditional |
|----------|---------------|----------------------|------------------|
| Python tasks | ✅ Excellent | ✅ Excellent | ⚠️ Good |
| Non-Python ops | ⚠️ Awkward | ✅ Natural | ✅ Natural |
| Code clarity | ✅ Very clean | ✅ Clean | ⚠️ Verbose |
| Type safety | ✅ Yes | ✅ For Python | ❌ No |
| Learning curve | ⚠️ Medium | ⚠️ Medium | ✅ Easy |
| Best for this DAG | ❌ No | ✅ **YES** | ⚠️ Acceptable |

---

### Final Recommendation

✅ **Use Traditional Template with Hybrid Pattern**

**Why**:
1. Supports mixed operator types (58% non-Python)
2. Allows TaskFlow benefits for Python tasks (42%)
3. Clean integration with custom operators
4. Explicit control for complex dependencies
5. Best balance of modern + practical

**Start With**:
```bash
# Copy traditional template
cp -r /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/_dag_template /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/my_dag

# Modify main.py for hybrid pattern
```

**Next Steps**:
1. Copy `_dag_template/` as starting point
2. Convert Python logic to @task decorators
3. Keep non-Python operators as traditional
4. Mix data flow and explicit dependencies
5. Test thoroughly
```

## Enforcement

This skill SHOULD be executed:
- After analyzing legacy DAG structure
- Before starting implementation
- To guide template selection
- When team needs architecture decision

**Choosing the right template upfront saves refactoring time and ensures best practices.**
