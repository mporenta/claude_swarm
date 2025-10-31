# Path Configuration Fix Summary

## Issue
The DAG migration paths in `agent_options.py` were incorrectly configured, causing the agent to look for files in wrong locations.

## Previous Configuration (INCORRECT)

**Paths in prompt**:
- Legacy DAG: `{cwd_path}/airflow/data-airflow-legacy/dags/{legacy_py_file}`
- New DAG: `{cwd_path}/airflow/data-airflow/dags/{new_dag_path}`

**Where `cwd_path` was**: `/home/dev/claude_dev/claude_swarm/generated_dags`

**Resulting in INCORRECT paths**:
- Legacy: `/home/dev/claude_dev/claude_swarm/generated_dags/airflow/data-airflow-legacy/dags/...` ❌
- New: `/home/dev/claude_dev/claude_swarm/generated_dags/airflow/data-airflow/dags/...` ❌

## New Configuration (CORRECT)

**File**: `/home/dev/claude_dev/claude_swarm/src/agent_options.py`

### 1. Updated Prompt Paths (Lines 244-251)
```markdown
**Legacy DAG (Airflow 1.x):**
`/home/dev/claude_dev/airflow/data-airflow-legacy/dags/{legacy_py_file}`

**Migrated DAG (Airflow 2.x): Path for output**
`/home/dev/claude_dev/airflow/data-airflow/dags/{new_dag_path}`

**Working Directory for Generated Code:**
`{cwd_path}`
```

### 2. Added Directory Access (Lines 67-71)
```python
add_dirs=[
    "/home/dev/claude_dev/airflow/data-airflow-legacy/dags",  # Legacy DAG source
    "/home/dev/claude_dev/airflow/data-airflow/dags",  # New DAG destination
    "/home/dev/claude_dev/airflow/data-airflow/dags/common",  # Common components for DRY compliance
],
```

## Verified Paths

✅ **Legacy DAG directory exists**:
```bash
/home/dev/claude_dev/airflow/data-airflow-legacy/dags/
```

✅ **New DAG directory exists**:
```bash
/home/dev/claude_dev/airflow/data-airflow/dags/
```

✅ **Common components directory exists**:
```bash
/home/dev/claude_dev/airflow/data-airflow/dags/common/
```

✅ **Working directory exists**:
```bash
/home/dev/claude_dev/claude_swarm/generated_dags/
```

## Agent Configuration Summary

### Working Directory (`cwd`)
```
/home/dev/claude_dev/claude_swarm/generated_dags
```
Used for temporary files and generated code.

### Additional Directories (`add_dirs`)
```python
[
    '/home/dev/claude_dev/airflow/data-airflow-legacy/dags',
    '/home/dev/claude_dev/airflow/data-airflow/dags',
    '/home/dev/claude_dev/airflow/data-airflow/dags/common'
]
```
Grants the agent access to:
1. Read legacy DAGs for migration
2. Write new migrated DAGs
3. Access common components for DRY compliance checks

## Usage Example

When a user provides:
- Legacy DAG file: `cresta_to_snowflake.py`
- New DAG name: `cresta_to_snowflake_v2`

The agent will:
1. **Read from**: `/home/dev/claude_dev/airflow/data-airflow-legacy/dags/cresta_to_snowflake.py`
2. **Write to**: `/home/dev/claude_dev/airflow/data-airflow/dags/cresta_to_snowflake_v2/`
3. **Check common components at**: `/home/dev/claude_dev/airflow/data-airflow/dags/common/`

## Verification

Test the configuration:
```bash
python3 -c "
from src.agent_options import dag_mirgration_agent, dag_migration_user_prompt

options = dag_mirgration_agent()
print('CWD:', options.cwd)
print('Additional dirs:', options.add_dirs)

prompt = dag_migration_user_prompt('test.py', 'test_v2.py')
print('\\nPaths in prompt:')
for line in prompt.split('\\n'):
    if 'Legacy DAG' in line or 'Migrated DAG' in line or 'Working Directory' in line:
        print(line)
"
```

Expected output:
```
CWD: /home/dev/claude_dev/claude_swarm/generated_dags
Additional dirs: ['/home/dev/claude_dev/airflow/data-airflow-legacy/dags', '/home/dev/claude_dev/airflow/data-airflow/dags', '/home/dev/claude_dev/airflow/data-airflow/dags/common']

Paths in prompt:
**Legacy DAG (Airflow 1.x):**
`/home/dev/claude_dev/airflow/data-airflow-legacy/dags/{legacy_py_file}`
**Migrated DAG (Airflow 2.x): Path for output**
`/home/dev/claude_dev/airflow/data-airflow/dags/{new_dag_path}`
**Working Directory for Generated Code:**
`/home/dev/claude_dev/claude_swarm/generated_dags`
```

## Benefits

1. ✅ **Absolute paths** - No ambiguity, always resolves correctly
2. ✅ **Explicit access** - `add_dirs` ensures agent can read/write to all necessary locations
3. ✅ **Common components** - Skills like `/check-common-components` can access the common/ directory
4. ✅ **Clear separation** - Working directory separate from DAG directories
5. ✅ **Verified existence** - All directories confirmed to exist

## Related Files

- `/home/dev/claude_dev/claude_swarm/src/agent_options.py` - Configuration updated
- `/home/dev/claude_dev/claude_swarm/airflow_agent_main.py` - Calls `dag_migration_user_prompt()`
- `SKILL_TRACKING_IMPLEMENTATION.md` - Related tracking implementation
- `CLAUDE.md` - Project guidelines and architecture

## Status
✅ **COMPLETE** - All paths verified and working correctly

## Date
2025-10-29
