# Identify Dependencies Skill

## Purpose
Extract task dependencies from legacy DAGs and convert to TaskFlow patterns, distinguishing between data flow dependencies (`task2(task1())`) and explicit dependencies (`task1 >> task2`).

## When to Use
**RECOMMENDED** during migration:
- After analyzing legacy DAG structure
- Before implementing modern DAG tasks
- When complex dependency patterns exist
- To visualize task execution order

## Execution Steps

### 1. Find Explicit Dependencies
```bash
# Find >> operators (downstream dependencies)
grep -n " >> " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find << operators (upstream dependencies)
grep -n " << " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find set_upstream calls
grep -n "set_upstream\|set_downstream" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 2. Find Chained Dependencies
```bash
# Find multi-task chains (task1 >> task2 >> task3)
grep -E ">>.*>>" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find list dependencies (task1 >> [task2, task3])
grep -E ">>\s*\[" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 3. Find Branching Patterns
```bash
# Find BranchPythonOperator
grep -n "BranchPythonOperator\|branch_task" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find conditional dependencies
grep -n "trigger_rule" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 4. Map Task IDs to Dependencies
```bash
# Extract all task_id assignments
grep -E "task_id\s*=\s*['\"]" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | grep -o "task_id\s*=\s*['\"][^'\"]*['\"]"

# Build dependency map by analyzing >> patterns
grep " >> " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sed 's/^[[:space:]]*//'
```

### 5. Check for Dynamic Dependencies
```bash
# Find dependencies in loops
grep -B 5 " >> " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | grep "for "

# Find dependencies created conditionally
grep -B 3 " >> " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | grep "if "
```

## Dependency Pattern Classification

### Pattern 1: Linear Chain (Data Flow)
**Legacy**:
```python
extract = PythonOperator(task_id='extract', python_callable=extract_func)
transform = PythonOperator(task_id='transform', python_callable=transform_func)
load = PythonOperator(task_id='load', python_callable=load_func)

extract >> transform >> load
```

**Modern** (Recommended - Data Flow):
```python
@task
def extract() -> dict:
    return extract_func()

@task
def transform(data: dict) -> dict:
    return transform_func(data)

@task
def load(data: dict):
    load_func(data)

# Data flow creates implicit dependencies
load(transform(extract()))
```

**Modern** (Alternative - Explicit):
```python
@task
def extract(): ...

@task
def transform(): ...

@task
def load(): ...

# Explicit dependencies (when no data passing needed)
extract_task = extract()
transform_task = transform()
load_task = load()

extract_task >> transform_task >> load_task
```

### Pattern 2: Fan-Out (One to Many)
**Legacy**:
```python
extract >> [transform1, transform2, transform3]
```

**Modern** (Data Flow):
```python
@task
def extract() -> dict:
    return data

@task
def transform1(data: dict): ...

@task
def transform2(data: dict): ...

@task
def transform3(data: dict): ...

# Same data to multiple tasks
data = extract()
transform1(data)
transform2(data)
transform3(data)
```

**Modern** (Explicit):
```python
extract_task = extract()
t1 = transform1()
t2 = transform2()
t3 = transform3()

extract_task >> [t1, t2, t3]
```

### Pattern 3: Fan-In (Many to One)
**Legacy**:
```python
[extract1, extract2, extract3] >> merge
```

**Modern** (Data Flow):
```python
@task
def extract1() -> dict: ...

@task
def extract2() -> dict: ...

@task
def extract3() -> dict: ...

@task
def merge(data1: dict, data2: dict, data3: dict) -> dict:
    return combine(data1, data2, data3)

# Multiple inputs to single task
merge(extract1(), extract2(), extract3())
```

### Pattern 4: Branching
**Legacy**:
```python
branch = BranchPythonOperator(task_id='branch', python_callable=branch_func)
task_a = PythonOperator(task_id='task_a', ...)
task_b = PythonOperator(task_id='task_b', ...)

branch >> [task_a, task_b]
```

**Modern**:
```python
@task.branch
def branch() -> str:
    if condition:
        return 'task_a'
    else:
        return 'task_b'

@task
def task_a(): ...

@task
def task_b(): ...

# Branching pattern
branch_result = branch()
branch_result >> [task_a(), task_b()]
```

### Pattern 5: Complex Diamond
**Legacy**:
```python
start >> [branch1, branch2] >> join >> end
```

**Modern**:
```python
@task
def start() -> dict: ...

@task
def branch1(data: dict) -> dict: ...

@task
def branch2(data: dict) -> dict: ...

@task
def join(data1: dict, data2: dict) -> dict: ...

@task
def end(data: dict): ...

# Complex flow
data = start()
result1 = branch1(data)
result2 = branch2(data)
final = join(result1, result2)
end(final)
```

## Output Report Format

After executing this skill, provide:

```markdown
## Task Dependency Analysis Report: [dag_name]

### Dependency Summary

**Total Tasks**: [N]
**Dependency Statements**: [N]
**Dependency Pattern**: [LINEAR | FAN_OUT | FAN_IN | DIAMOND | COMPLEX]

---

### Legacy Dependencies (Lines X-Y)

```python
# Extracted from legacy DAG
extract_task = PythonOperator(task_id='extract', ...)
validate_task = PythonOperator(task_id='validate', ...)
transform_task = PythonOperator(task_id='transform', ...)
load_snowflake = SnowflakeOperator(task_id='load_snowflake', ...)
load_s3 = PythonOperator(task_id='load_s3', ...)
notify = PythonOperator(task_id='notify', ...)

# Dependencies (Lines 85-90)
extract_task >> validate_task >> transform_task
transform_task >> [load_snowflake, load_s3]
[load_snowflake, load_s3] >> notify
```

**Dependency Graph (ASCII)**:
```
extract_task
     ↓
validate_task
     ↓
transform_task
     ↓
     ├─→ load_snowflake ─┐
     └─→ load_s3 ────────┤
                         ↓
                    notify
```

---

### Modern Dependencies (Recommended)

#### Option 1: Data Flow Pattern (Recommended)

```python
@task
def extract() -> dict:
    return extract_data()

@task
def validate(data: dict) -> dict:
    if not is_valid(data):
        raise ValueError("Validation failed")
    return data

@task
def transform(data: dict) -> dict:
    return transform_data(data)

@task
def load_s3(data: dict):
    upload_to_s3(data)

# Note: SnowflakeOperator can't use data flow (not a @task)
# Use explicit dependency for non-TaskFlow operators

# Data flow for Python tasks
validated_data = validate(extract())
transformed_data = transform(validated_data)
load_s3(transformed_data)

# Explicit dependency for SnowflakeOperator
load_snowflake = SnowflakeOperator(task_id='load_snowflake', ...)
notify_task = notify()

# Mixed dependencies
transformed_data >> load_snowflake
[load_snowflake, load_s3(transformed_data)] >> notify_task
```

**Why This Approach**:
- ✅ Type-safe data passing for Python tasks
- ✅ Clear data lineage
- ✅ Automatic XCom handling
- ⚠️ Mixed with explicit deps for non-@task operators

---

#### Option 2: Explicit Dependencies (Alternative)

```python
@task
def extract(): ...

@task
def validate(): ...

@task
def transform(): ...

@task
def load_s3(): ...

@task
def notify(): ...

# Create task instances
extract_task = extract()
validate_task = validate()
transform_task = transform()
load_s3_task = load_s3()
load_snowflake = SnowflakeOperator(task_id='load_snowflake', ...)
notify_task = notify()

# Explicit dependencies
extract_task >> validate_task >> transform_task
transform_task >> [load_snowflake, load_s3_task]
[load_snowflake, load_s3_task] >> notify_task
```

**Why This Approach**:
- ✅ Familiar pattern for legacy users
- ✅ Works with mixed operator types
- ⚠️ No automatic data passing
- ⚠️ Must manage XCom manually if needed

---

### Dependency Pattern Analysis

#### Pattern 1: extract → validate (Line 85)

**Type**: Linear chain with data flow

**Legacy**: `extract_task >> validate_task`

**Modern**:
```python
validated_data = validate(extract())
```

**Reasoning**: Data flows from extract to validate, so use data flow pattern

---

#### Pattern 2: transform → [load_snowflake, load_s3] (Lines 87-88)

**Type**: Fan-out (one to many)

**Legacy**:
```python
transform_task >> [load_snowflake, load_s3]
```

**Modern** (Mixed):
```python
transformed_data = transform(validated_data)
load_s3(transformed_data)  # Data flow for @task
transformed_data >> load_snowflake  # Explicit for SnowflakeOperator
```

**Reasoning**:
- load_s3 can receive data via parameter (data flow)
- load_snowflake is SnowflakeOperator (not @task), needs explicit dependency
- Both need same input, so use transformed_data

---

#### Pattern 3: [load_snowflake, load_s3] → notify (Lines 89-90)

**Type**: Fan-in (many to one)

**Legacy**:
```python
[load_snowflake, load_s3] >> notify
```

**Modern**:
```python
notify_task = notify()
[load_snowflake, load_s3_task] >> notify_task
```

**Reasoning**:
- No data passing needed (just wait for completion)
- Use explicit dependencies
- Could alternatively use `@task` with multiple parameters if data needed

---

### Special Patterns Found

#### ⚠️ Branching Detected
**Location**: Line 95
**Pattern**: BranchPythonOperator
**Action**: Convert to `@task.branch` decorator

#### ⚠️ Trigger Rules
**Location**: Line 102
**Pattern**: `trigger_rule='all_done'`
**Action**: Preserve in modern DAG (still supported)

---

### Summary

**Dependency Complexity**: MEDIUM

**Recommended Approach**: **Mixed Pattern**
- Use data flow for Python-only chains
- Use explicit dependencies for non-@task operators
- Use explicit dependencies for fan-in without data passing

**Migration Checklist**:
- [ ] Convert linear Python chains to data flow pattern
- [ ] Use explicit `>>` for SnowflakeOperator dependencies
- [ ] Preserve trigger_rule settings where used
- [ ] Convert BranchPythonOperator to @task.branch
- [ ] Test dependency execution order

**Complexity Indicators**:
- Simple: Linear chains only
- Medium: Fan-out/fan-in patterns
- Complex: Branching + trigger rules + mixed operators

**LOC Impact**:
- Legacy dependencies: 6 lines
- Modern dependencies: ~8 lines (similar, but clearer data flow)
```

## Enforcement

This skill SHOULD be executed:
- When legacy DAG has 3+ tasks
- Before implementing modern task dependencies
- When complex dependency patterns exist
- To choose between data flow vs explicit patterns

**Clear dependency patterns ensure correct task execution order and data flow.**
