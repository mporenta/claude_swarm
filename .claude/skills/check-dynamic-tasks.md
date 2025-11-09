# Check Dynamic Tasks Skill

## Purpose
Identify loops and dynamic task generation patterns in legacy DAGs and convert to TaskFlow `.override()` pattern for Airflow 2.x.

## When to Use
**RECOMMENDED** during migration:
- When legacy DAG contains loops creating tasks
- When task_ids are dynamically generated
- To identify task groups that should use `@task_group`
- For parallel task pattern detection

## Execution Steps

### 1. Find Loops Creating Tasks
```bash
# Find for loops in DAG file
grep -n "for .* in " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Get context around loops
grep -B 3 -A 10 "for .* in " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 2. Identify Dynamic task_id Generation
```bash
# Find f-string or format() in task_id
grep -n "task_id=f['\"]" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "task_id=.*\.format(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "task_id=.*%" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 3. Check for List Iterations
```bash
# Find iterations over lists/dicts
grep -n "for .* in \[" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "for .* in range(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "for .* in enumerate(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 4. Find Task Group Candidates
```bash
# Look for comments indicating groups
grep -n "# Group\|# Section\|# Phase" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py -i

# Find related task naming patterns
grep -o "task_id=['\"][^'\"]*['\"]" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | grep -E "(_start|_end|_phase|_group)"
```

### 5. Analyze Loop Variables
```bash
# Extract what's being iterated
grep "for .* in " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sed 's/.*for \(.*\) in \(.*\):/\1 <- \2/'
```

### 6. Check for Dynamic Dependencies
```bash
# Find dependencies inside loops
grep -B 10 " >> \| << " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | grep -A 5 "for .* in "
```

## Dynamic Task Patterns

### Pattern 1: Simple Loop Creating Tasks
**Legacy**:
```python
for state in ['CA', 'TX', 'NY', 'FL']:
    task = PythonOperator(
        task_id=f'process_{state}',
        python_callable=process_state,
        op_kwargs={'state': state},
        dag=dag
    )
```

**Modern**:
```python
@task
def process_state(state: str) -> dict:
    # Business logic here
    return result

# Create dynamic tasks with .override()
states = ['CA', 'TX', 'NY', 'FL']
for state in states:
    process_state.override(task_id=f'process_{state}')(state)
```

### Pattern 2: Loop with Dependencies
**Legacy**:
```python
previous_task = start_task
for i in range(5):
    task = PythonOperator(
        task_id=f'step_{i}',
        python_callable=process_step,
        op_kwargs={'step': i},
        dag=dag
    )
    previous_task >> task
    previous_task = task
```

**Modern**:
```python
@task
def process_step(step: int) -> dict:
    return result

# Sequential dynamic tasks
tasks = []
for i in range(5):
    task = process_step.override(task_id=f'step_{i}')(i)
    tasks.append(task)

# Create dependencies
for i in range(len(tasks) - 1):
    tasks[i] >> tasks[i + 1]

# Or using chain
from airflow.models.baseoperator import chain
chain(*tasks)
```

### Pattern 3: Parallel Dynamic Tasks (Fan-Out)
**Legacy**:
```python
start = DummyOperator(task_id='start', dag=dag)

for item in items:
    task = PythonOperator(
        task_id=f'process_{item}',
        python_callable=process_item,
        op_kwargs={'item': item},
        dag=dag
    )
    start >> task
```

**Modern**:
```python
@task
def start_task():
    return items

@task
def process_item(item: str) -> dict:
    return result

# Parallel execution with dynamic tasks
start = start_task()
for item in items:
    task = process_item.override(task_id=f'process_{item}')(item)
    start >> task  # All tasks depend on start
```

### Pattern 4: Task Groups (Recommended for Related Tasks)
**Legacy**:
```python
# Extract phase
for source in ['api', 'db', 'file']:
    extract = PythonOperator(task_id=f'extract_{source}', ...)

# Transform phase
for source in ['api', 'db', 'file']:
    transform = PythonOperator(task_id=f'transform_{source}', ...)

# Dependencies
# ... complex dependency setup
```

**Modern** (Using TaskGroup):
```python
from airflow.utils.task_group import TaskGroup

@task
def extract_data(source: str) -> dict: ...

@task
def transform_data(source: str, data: dict) -> dict: ...

sources = ['api', 'db', 'file']

with TaskGroup('extract_phase') as extract_group:
    extract_tasks = []
    for source in sources:
        task = extract_data.override(task_id=f'extract_{source}')(source)
        extract_tasks.append(task)

with TaskGroup('transform_phase') as transform_group:
    transform_tasks = []
    for i, source in enumerate(sources):
        task = transform_data.override(task_id=f'transform_{source}')(
            source, extract_tasks[i]
        )
        transform_tasks.append(task)

# Clean dependency
extract_group >> transform_group
```

### Pattern 5: Dynamic Task with Mapped Values
**Legacy**:
```python
states = Variable.get('states_list', deserialize_json=True)

for state in states:
    task = PythonOperator(
        task_id=f'process_{state}',
        python_callable=process_state,
        op_kwargs={'state': state},
        dag=dag
    )
```

**Modern** (Airflow 2.3+ Dynamic Task Mapping):
```python
from airflow.models import Variable

@task
def get_states() -> list:
    return Variable.get('states_list', deserialize_json=True)

@task
def process_state(state: str) -> dict:
    return result

# Dynamic task mapping (Airflow 2.3+)
states = get_states()
process_state.expand(state=states)  # Creates one task per state automatically

# OR using .override() for more control
states_list = Variable.get('states_list', deserialize_json=True, default_var=['CA', 'TX'])
for state in states_list:
    process_state.override(task_id=f'process_{state}')(state)
```

## Output Report Format

After executing this skill, provide:

```markdown
## Dynamic Task Analysis Report: [dag_name]

### Dynamic Task Patterns Found

**Total Loops**: [N]
**Dynamic Tasks**: [N]
**Task Group Candidates**: [N]

---

### Pattern 1: State Processing Loop (Lines 45-55)

**Legacy Code**:
```python
states = ['CA', 'TX', 'NY', 'FL', 'IL', 'OH']

for state in states:
    task = PythonOperator(
        task_id=f'process_{state}',
        python_callable=process_state_data,
        op_kwargs={'state': state},
        provide_context=True,
        dag=dag
    )
    extract_task >> task >> load_task
```

**Pattern Type**: Simple parallel loop (Fan-out → Fan-in)

**Issues**:
- ❌ Creates 6 separate task instances imperatively
- ❌ Uses `provide_context=True` (deprecated)
- ❌ All tasks have same dependencies (extract → process → load)
- ⚠️ No task grouping (UI will show 6 individual tasks)

**Task IDs Created**:
- `process_CA`
- `process_TX`
- `process_NY`
- `process_FL`
- `process_IL`
- `process_OH`

---

**Modern Conversion (Option 1: .override() - More Control)**:
```python
@task
def process_state_data(state: str) -> dict:
    # Business logic here
    return processed_data

# Create dynamic tasks
states = ['CA', 'TX', 'NY', 'FL', 'IL', 'OH']
extract = extract_task()

process_tasks = []
for state in states:
    task = process_state_data.override(task_id=f'process_{state}')(state)
    extract >> task
    process_tasks.append(task)

load = load_task()
process_tasks >> load  # All process tasks must complete before load
```

**Benefits**:
- ✅ TaskFlow pattern with automatic XCom
- ✅ No `provide_context` needed
- ✅ Clear data flow
- ✅ Type hints for safety

---

**Modern Conversion (Option 2: Dynamic Task Mapping - Airflow 2.3+)**:
```python
@task
def get_states() -> list:
    return ['CA', 'TX', 'NY', 'FL', 'IL', 'OH']

@task
def process_state_data(state: str) -> dict:
    return processed_data

# Dynamic task mapping
extract = extract_task()
states = get_states()

# .expand() creates one task instance per state automatically
process = process_state_data.expand(state=states)

extract >> process >> load_task()
```

**Benefits**:
- ✅ Airflow handles dynamic task creation
- ✅ More efficient (tasks created at runtime)
- ✅ Cleaner syntax
- ⚠️ Requires Airflow 2.3+

---

**Recommended Approach**: Use `.override()` for explicit control, or `.expand()` if on Airflow 2.3+

**Complexity**: MEDIUM (6 parallel tasks)

---

### Pattern 2: Sequential Processing Pipeline (Lines 78-95)

**Legacy Code**:
```python
steps = ['fetch', 'validate', 'transform', 'enrich', 'aggregate']

previous = start_task
for step in steps:
    task = PythonOperator(
        task_id=f'step_{step}',
        python_callable=globals()[f'do_{step}'],
        dag=dag
    )
    previous >> task
    previous = task

previous >> end_task
```

**Pattern Type**: Sequential chain with dynamic naming

**Issues**:
- ❌ Uses `globals()` to dynamically resolve functions (fragile)
- ❌ Sequential dependency makes it hard to parallelize later
- ⚠️ Could benefit from task grouping

**Task IDs Created**:
- `step_fetch`
- `step_validate`
- `step_transform`
- `step_enrich`
- `step_aggregate`

---

**Modern Conversion**:
```python
@task
def fetch_data() -> dict: ...

@task
def validate_data(data: dict) -> dict: ...

@task
def transform_data(data: dict) -> dict: ...

@task
def enrich_data(data: dict) -> dict: ...

@task
def aggregate_data(data: dict) -> dict: ...

# Data flow creates sequential dependencies automatically
result = aggregate_data(
    enrich_data(
        transform_data(
            validate_data(
                fetch_data()
            )
        )
    )
)

# Or more readable:
fetched = fetch_data()
validated = validate_data(fetched)
transformed = transform_data(validated)
enriched = enrich_data(transformed)
aggregated = aggregate_data(enriched)
```

**Benefits**:
- ✅ No dynamic function resolution
- ✅ Explicit data flow
- ✅ Type-safe with hints
- ✅ Easy to modify individual steps
- ⚠️ Not truly dynamic (if steps are actually dynamic, use .override())

**Alternative (If truly dynamic)**:
```python
# If steps really need to be dynamic
step_functions = {
    'fetch': fetch_data,
    'validate': validate_data,
    'transform': transform_data,
    'enrich': enrich_data,
    'aggregate': aggregate_data,
}

steps = ['fetch', 'validate', 'transform', 'enrich', 'aggregate']
tasks = []

for step in steps:
    func = step_functions[step]
    task = func.override(task_id=f'step_{step}')()
    tasks.append(task)

# Chain them
from airflow.models.baseoperator import chain
chain(*tasks)
```

**Recommended Approach**: Use explicit @task functions (not truly dynamic)

**Complexity**: SIMPLE (linear chain)

---

### Pattern 3: Phase-Based Processing (Lines 120-180)

**Legacy Code**:
```python
sources = ['salesforce', 'hubspot', 'zendesk']

# Extract phase
extract_tasks = []
for source in sources:
    task = PythonOperator(
        task_id=f'extract_{source}',
        python_callable=extract_from_source,
        op_kwargs={'source': source},
        dag=dag
    )
    extract_tasks.append(task)

# Transform phase
transform_tasks = []
for source in sources:
    task = PythonOperator(
        task_id=f'transform_{source}',
        python_callable=transform_data,
        op_kwargs={'source': source},
        dag=dag
    )
    transform_tasks.append(task)
    extract_tasks[sources.index(source)] >> task

# Load phase
load_task = PythonOperator(task_id='load_all', python_callable=load_data, dag=dag)
for task in transform_tasks:
    task >> load_task
```

**Pattern Type**: Multi-phase with task groups

**Issues**:
- ⚠️ No visual grouping (9 tasks flat in UI)
- ❌ Index lookup `sources.index(source)` is fragile
- ⚠️ Could use TaskGroup for better organization

**Task IDs Created**:
- Extract: `extract_salesforce`, `extract_hubspot`, `extract_zendesk`
- Transform: `transform_salesforce`, `transform_hubspot`, `transform_zendesk`
- Load: `load_all`

---

**Modern Conversion (Recommended - With TaskGroup)**:
```python
from airflow.utils.task_group import TaskGroup

@task
def extract_from_source(source: str) -> dict:
    return extracted_data

@task
def transform_data(source: str, data: dict) -> dict:
    return transformed_data

@task
def load_all(data_list: list) -> None:
    for data in data_list:
        load(data)

sources = ['salesforce', 'hubspot', 'zendesk']

# Extract phase (grouped)
with TaskGroup('extract_phase', tooltip='Extract from all sources') as extract_group:
    extract_tasks = [
        extract_from_source.override(task_id=f'extract_{source}')(source)
        for source in sources
    ]

# Transform phase (grouped)
with TaskGroup('transform_phase', tooltip='Transform all data') as transform_group:
    transform_tasks = [
        transform_data.override(task_id=f'transform_{source}')(source, extract_tasks[i])
        for i, source in enumerate(sources)
    ]

# Load phase
load_task = load_all(transform_tasks)

# Clean group dependencies
extract_group >> transform_group >> load_task
```

**Benefits**:
- ✅ Visual grouping in Airflow UI
- ✅ Collapsible task groups
- ✅ Clear phase separation
- ✅ Data flow between tasks
- ✅ Type-safe parameters

**UI Appearance**:
```
[extract_phase] → [transform_phase] → [load_all]
  └─ extract_salesforce
  └─ extract_hubspot
  └─ extract_zendesk
```

**Recommended Approach**: Use TaskGroup for organization

**Complexity**: MEDIUM (9 tasks in 3 phases)

---

### Summary

| Pattern | Lines | Tasks Created | Recommended Conversion | Priority |
|---------|-------|---------------|------------------------|----------|
| State processing | 45-55 | 6 parallel | .override() or .expand() | HIGH |
| Sequential pipeline | 78-95 | 5 sequential | Explicit @task (not dynamic) | MEDIUM |
| Phase-based | 120-180 | 9 (3 phases) | TaskGroup with .override() | HIGH |

**Total Dynamic Tasks**: 20

**Task Groups Recommended**: 2 (extract_phase, transform_phase)

**Dynamic Task Mapping Candidates** (Airflow 2.3+): 1 (state processing)

---

### Migration Checklist

- [ ] Convert state processing loop to .override() pattern
- [ ] Convert sequential pipeline to explicit @task functions
- [ ] Wrap phase-based tasks in TaskGroup
- [ ] Remove `provide_context=True`
- [ ] Add type hints to all @task functions
- [ ] Test dynamic task creation with `airflow dags test`
- [ ] Verify task IDs match expected patterns
- [ ] Consider .expand() for state processing (if on Airflow 2.3+)

---

### Recommended Priority

**High Priority** (Must convert):
1. State processing loop (6 tasks, parallel)
2. Phase-based processing (needs TaskGroup)

**Medium Priority** (Simplify):
3. Sequential pipeline (convert to explicit functions)

**Benefits of Conversion**:
- Cleaner code (less imperative, more declarative)
- Better UI organization (TaskGroups)
- Type safety (type hints)
- Modern TaskFlow patterns
- No deprecated parameters

**LOC Impact**:
- Legacy: ~60 lines of loop code
- Modern: ~45 lines with TaskFlow + TaskGroup
- Reduction: 25% fewer lines, much clearer intent
```

## Enforcement

This skill SHOULD be executed:
- When legacy DAG contains loops
- When dynamic task_ids are generated
- To identify TaskGroup opportunities
- For better UI organization

**Proper dynamic task handling ensures scalable, maintainable DAG patterns.**
