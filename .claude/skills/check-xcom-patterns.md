# Check XCom Patterns Skill

## Purpose
Identify XCom usage in legacy DAGs and convert to TaskFlow API automatic return/parameter patterns for cleaner, type-safe data flow.

## When to Use
**RECOMMENDED** during migration:
- After analyzing legacy DAG structure
- Before converting PythonOperators to @task
- When manual XCom push/pull is detected
- To modernize data passing between tasks

## Execution Steps

### 1. Find XCom Push Operations
```bash
# Search for xcom_push calls
grep -n "xcom_push" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Get context (5 lines before and after)
grep -B 5 -A 5 "xcom_push" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 2. Find XCom Pull Operations
```bash
# Search for xcom_pull calls
grep -n "xcom_pull" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Get context (5 lines before and after)
grep -B 5 -A 5 "xcom_pull" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 3. Identify XCom Keys
```bash
# Extract key names used in XCom
grep -o "key=['\"][^'\"]*['\"]" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sort -u

# Also check for return_value (default key)
grep -n "key='return_value'" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 4. Map Data Flow
```bash
# Find task_ids in xcom_pull to understand dependencies
grep -o "task_ids=['\"][^'\"]*['\"]" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Check for multiple task pulls (list of task_ids)
grep "task_ids=\[" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 5. Check for Context Usage
```bash
# Find **context or **kwargs usage
grep -n "\*\*context\|\*\*kwargs" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find ti (task instance) usage
grep -n "ti\s*=" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find provide_context=True (deprecated)
grep -n "provide_context=True" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

## XCom Pattern Classification

### Pattern 1: Simple Return Value (Default Key)
**Legacy**:
```python
def extract_data(**context):
    data = fetch_data()
    context['ti'].xcom_push(key='return_value', value=data)
    # OR
    return data  # Implicitly uses 'return_value' key

def transform_data(**context):
    data = context['ti'].xcom_pull(task_ids='extract')
    return process(data)
```

**Modern**:
```python
@task
def extract_data() -> dict:
    return fetch_data()  # Automatic XCom push

@task
def transform_data(data: dict) -> dict:  # Automatic XCom pull via parameter
    return process(data)

# Data flow
transform_data(extract_data())  # Implicit dependency + data passing
```

### Pattern 2: Named Keys (Multiple Values)
**Legacy**:
```python
def extract_data(**context):
    ti = context['ti']
    ti.xcom_push(key='customers', value=customer_data)
    ti.xcom_push(key='orders', value=order_data)
    ti.xcom_push(key='metadata', value=metadata)

def load_data(**context):
    ti = context['ti']
    customers = ti.xcom_pull(task_ids='extract', key='customers')
    orders = ti.xcom_pull(task_ids='extract', key='orders')
    metadata = ti.xcom_pull(task_ids='extract', key='metadata')
```

**Modern**:
```python
from typing import NamedTuple

class ExtractResult(NamedTuple):
    customers: list
    orders: list
    metadata: dict

@task
def extract_data() -> ExtractResult:
    return ExtractResult(
        customers=customer_data,
        orders=order_data,
        metadata=metadata
    )

@task
def load_data(extract_result: ExtractResult):
    customers = extract_result.customers
    orders = extract_result.orders
    metadata = extract_result.metadata
```

### Pattern 3: Multiple Task Pulls
**Legacy**:
```python
def combine_data(**context):
    ti = context['ti']
    data1 = ti.xcom_pull(task_ids='task1')
    data2 = ti.xcom_pull(task_ids='task2')
    data3 = ti.xcom_pull(task_ids='task3')
    return merge(data1, data2, data3)
```

**Modern**:
```python
@task
def combine_data(data1: dict, data2: dict, data3: dict) -> dict:
    return merge(data1, data2, data3)

# Data flow with multiple inputs
combine_data(task1(), task2(), task3())
```

### Pattern 4: Optional/Conditional XCom
**Legacy**:
```python
def process_data(**context):
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract', default=None)
    if data:
        return process(data)
    return None
```

**Modern**:
```python
@task
def process_data(data: Optional[dict] = None) -> Optional[dict]:
    if data:
        return process(data)
    return None
```

## Output Report Format

After executing this skill, provide:

```markdown
## XCom Pattern Migration Report: [dag_name]

### XCom Usage Summary

**XCom Push Operations**: [N] found
**XCom Pull Operations**: [N] found
**Unique Keys Used**: [list of keys]

---

### Pattern Analysis

#### 1. extract_data() → transform_data() (Lines 45-78)

**Legacy Pattern**: Simple return value
```python
def extract_data(**context):
    data = fetch_data()
    return data  # Line 50

def transform_data(**context):
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract_data')  # Line 65
    return process(data)
```

**XCom Keys**:
- Key: `return_value` (default)
- Data type: dict
- Flow: extract_data → transform_data

**Modern Pattern**:
```python
@task
def extract_data() -> dict:
    return fetch_data()

@task
def transform_data(data: dict) -> dict:
    return process(data)

# Data flow
transform_data(extract_data())
```

**Benefits**:
- ✅ No manual XCom push/pull
- ✅ Type hints for data validation
- ✅ Automatic dependency creation
- ✅ Cleaner, more readable code

---

#### 2. fetch_multiple_sources() → merge_data() (Lines 120-180)

**Legacy Pattern**: Multiple named keys
```python
def fetch_multiple_sources(**context):
    ti = context['ti']
    ti.xcom_push(key='api_data', value=api_response)  # Line 135
    ti.xcom_push(key='db_data', value=db_result)  # Line 140
    ti.xcom_push(key='file_data', value=file_content)  # Line 145

def merge_data(**context):
    ti = context['ti']
    api = ti.xcom_pull(task_ids='fetch', key='api_data')  # Line 165
    db = ti.xcom_pull(task_ids='fetch', key='db_data')  # Line 166
    file = ti.xcom_pull(task_ids='fetch', key='file_data')  # Line 167
```

**XCom Keys**:
- Keys: `api_data`, `db_data`, `file_data`
- Data types: dict, list, str

**Modern Pattern** (Recommended - NamedTuple):
```python
from typing import NamedTuple

class FetchResult(NamedTuple):
    api_data: dict
    db_data: list
    file_data: str

@task
def fetch_multiple_sources() -> FetchResult:
    return FetchResult(
        api_data=api_response,
        db_data=db_result,
        file_data=file_content
    )

@task
def merge_data(fetch_result: FetchResult) -> dict:
    return merge(
        fetch_result.api_data,
        fetch_result.db_data,
        fetch_result.file_data
    )

# Data flow
merge_data(fetch_multiple_sources())
```

**Alternative Pattern** (Dict):
```python
@task
def fetch_multiple_sources() -> dict:
    return {
        'api_data': api_response,
        'db_data': db_result,
        'file_data': file_content
    }

@task
def merge_data(data: dict) -> dict:
    return merge(data['api_data'], data['db_data'], data['file_data'])
```

**Benefits**:
- ✅ Type-safe data structure
- ✅ Single XCom value (more efficient)
- ✅ Clear data contract
- ✅ Better IDE support

---

### Summary

| XCom Pattern | Legacy LOC | Modern LOC | Complexity |
|--------------|------------|------------|------------|
| Simple return | 8 | 4 | SIMPLE |
| Named keys (3) | 15 | 12 | MEDIUM |
| Multiple pulls | 12 | 6 | SIMPLE |

**Total XCom Operations**: 12 push + 15 pull = 27 operations
**Conversion**: 27 manual operations → 0 (automatic via TaskFlow)

**Code Reduction**: ~35 lines of XCom boilerplate eliminated

**Type Safety**: ✅ All data flows now have type hints

**Complexity Reduction**:
- No more ti.xcom_push/pull
- No more **context parameter
- No more task_ids string references
- No more key name management

### Migration Checklist

- [ ] Remove all `context['ti'].xcom_push()` calls
- [ ] Remove all `context['ti'].xcom_pull()` calls
- [ ] Add type hints to @task function signatures
- [ ] Convert multiple named keys to NamedTuple or dict
- [ ] Update data flow to use function calls: `task2(task1())`
- [ ] Remove `provide_context=True` from operators
- [ ] Test data passing between tasks

### Next Steps

1. Convert functions to @task decorators
2. Add type hints (dict, list, str, NamedTuple, etc.)
3. Replace XCom push/pull with return values and parameters
4. Update task dependencies to use data flow pattern
5. Test with `airflow tasks test`
```

## Enforcement

This skill SHOULD be executed:
- When legacy DAG contains xcom_push or xcom_pull
- Before converting PythonOperators to @task
- To modernize data passing patterns
- To improve type safety and code clarity

**Modern XCom patterns via TaskFlow are cleaner, safer, and more maintainable than manual XCom operations.**
