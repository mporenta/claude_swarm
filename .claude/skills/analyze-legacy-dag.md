# Analyze Legacy DAG Skill

## Purpose
Parse and document legacy Airflow 1.x DAG structure before migration to understand operators, dependencies, XCom patterns, and connections.

## When to Use
**MANDATORY** at the start of every migration:
- Before beginning any Airflow 1.x to 2.x migration
- When analyzing complexity of a legacy DAG
- To create a migration plan
- To identify custom code that needs refactoring

## Execution Steps

### 1. Verify Legacy DAG Exists
```bash
# Check if legacy DAG file exists
ls -lh /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Preview first 50 lines
head -50 /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 2. Count Lines of Code
```bash
# Total lines in DAG
wc -l /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Lines excluding comments and blank lines
grep -v "^\s*#" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | grep -v "^\s*$" | wc -l
```

### 3. Identify Operators Used
```bash
# Find all operator instantiations
grep -n "Operator(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Count operator types
grep -o "[A-Za-z]*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sort | uniq -c | sort -rn
```

### 4. Extract Dependencies
```bash
# Find task dependencies (>> and << operators)
grep -n " >> \| << " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 5. Identify XCom Usage
```bash
# Find XCom push operations
grep -n "xcom_push" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find XCom pull operations
grep -n "xcom_pull" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 6. Extract Connections
```bash
# Find connection IDs
grep -n "_conn_id" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find BaseHook.get_connection calls
grep -n "get_connection" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 7. Identify DAG Configuration
```bash
# Find default_args
grep -A 10 "default_args\s*=" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find schedule_interval
grep -n "schedule_interval" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find concurrency settings
grep -n "concurrency" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 8. Find Custom Functions
```bash
# Find function definitions (potential business logic)
grep -n "^def " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Find class definitions
grep -n "^class " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 9. Identify Imports
```bash
# Extract all imports
grep -n "^import \|^from " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

## Output Report Format

After executing this skill, provide:

```markdown
## Legacy DAG Analysis: [dag_name]

**File Location**: `/Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/[dag_name].py`

**Size Metrics**:
- Total lines: [N]
- Code lines (excl. comments/blanks): [N]
- Functions defined: [N]
- Classes defined: [N]

**Operators Used**:
| Operator Type | Count | Line Numbers |
|---------------|-------|--------------|
| PythonOperator | [N] | [lines] |
| BashOperator | [N] | [lines] |
| SnowflakeOperator | [N] | [lines] |
| CustomOperator | [N] | [lines] |

**Dependencies Found**:
```python
# Task dependency graph (line references)
task_a >> task_b  # Line 45
task_b >> task_c  # Line 46
```

**XCom Usage**:
- Push operations: [N] (lines: [list])
- Pull operations: [N] (lines: [list])
- Keys used: [list of xcom keys]

**Connections Required**:
| Connection ID | Type | Usage Location |
|---------------|------|----------------|
| sftp_conn | SFTP | Line 34 |
| snowflake_default | Snowflake | Line 78 |

**DAG Configuration**:
- Schedule: [schedule_interval value]
- Start Date: [start_date]
- Concurrency: [value]
- Catchup: [value]
- Tags: [list]

**Custom Code Identified**:
1. Function `[name]` (lines [X-Y]): [description]
2. Class `[name]` (lines [X-Y]): [description]

**Key Imports**:
- Airflow imports: [list]
- Custom imports: [list]
- External libraries: [list]

**Complexity Assessment**: [SIMPLE | MEDIUM | COMPLEX]
- Simple: <100 LOC, Python-only, no custom logic
- Medium: 100-300 LOC, mixed operators, some custom logic
- Complex: >300 LOC, custom operators/hooks, complex dependencies

**Migration Considerations**:
- [Flag any complex patterns that need special attention]
- [Note any deprecated features]
- [Identify code that should be in common/]
```

## Enforcement

This skill MUST be executed:
- Before starting any migration from Airflow 1.x to 2.x
- When creating a migration plan
- Before running other migration skills

**Running this skill first prevents wasted effort and ensures informed migration decisions.**
