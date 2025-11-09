# Airflow DAG Development Agent

A multi-agent system powered by Claude Agent SDK for creating and migrating Apache Airflow 2 DAGs following strict standards defined in CLAUDE.md.

## Overview

This agent orchestrator uses specialized subagents to handle different aspects of Airflow DAG development:

- **@dag-architect**: Plans DAG structure, dependencies, and architecture
- **@dag-developer**: Writes production-ready Airflow 2 code
- **@migration-specialist**: Handles Airflow 1.0 to 2.0 migrations
- **@airflow-code-reviewer**: Reviews code for CLAUDE.md compliance

## Features

### 1. New DAG Creation
- Designs optimal DAG architecture
- Generates complete file structure
- Implements src/main.py with Main class pattern
- Adds comprehensive type hints and documentation
- Ensures heartbeat-safe code
- Validates flake8 compliance

### 2. DAG Migration (Airflow 1.0 → 2.0)
- Analyzes legacy DAG code
- Updates all imports to Airflow 2.0 provider structure
- Refactors monolithic functions into modular tasks
- Implements TaskGroups for organization
- Converts Variables to Connections
- Ensures full CLAUDE.md compliance

## File Structure

```
claude_test/
├── airflow_agent.py                 # Main orchestrator
├── prompts/
│   ├── dag-architect.md            # DAG architecture planning agent
│   ├── dag-developer.md            # DAG implementation agent
│   ├── migration-specialist.md     # Airflow 1.0→2.0 migration agent
│   ├── airflow-code-reviewer.md    # Code review and compliance agent
│   └── airflow-orchestrator.md     # Main orchestration prompt
└── generated_dags/                  # Output directory for DAGs
```

## Usage

### Starting the Agent

```bash
python airflow_agent.py
```

### Interactive Commands

- **`create-dag`**: Create a new Airflow DAG from scratch
- **`migrate-dag`**: Migrate an Airflow 1.0 DAG to 2.0
- **`new`**: Start a fresh conversation (clears context)
- **`interrupt`**: Stop current task
- **`exit`**: Quit the session

### Example: Creating a New DAG

```
[Turn 1] You: create-dag
DAG name (e.g., 'marketo_to_snowflake'): customer_data_pipeline
Schedule (daily/intraday/hourly/nightly/weekly/monthly): daily
Brief description of what this DAG should do: Fetch customer data from API and load to Snowflake
```

The orchestrator will:
1. Use @dag-architect to design the structure
2. Use @dag-developer to implement the code
3. Use @airflow-code-reviewer to verify compliance

### Example: Migrating a Legacy DAG

```
[Turn 1] You: migrate-dag
Path to legacy DAG file: /home/dev/airflow/data-airflow-legacy/dags/old_pipeline.py
New DAG name (leave blank to use same name): new_customer_pipeline
```

The orchestrator will:
1. Analyze the legacy code with @migration-specialist
2. Design modern structure with @dag-architect
3. Implement migration with @migration-specialist
4. Review compliance with @airflow-code-reviewer

## Standards Enforced

### File Structure
```
dags/
├── pipeline_name/
│   ├── src/
│   │   ├── main.py          # Main class with execute() method
│   │   └── helpers.py
│   └── daily.py             # Named by schedule
```

### Type Hints (Required)
All functions must have complete type hints:
```python
from typing import Optional, List, Dict, Union, Any

def process_data(data: List[Dict], config: Dict[str, str]) -> str:
    """Comprehensive docstring required."""
    pass
```

### Heartbeat Safety (Critical)
No heavy operations at DAG level:
- ❌ Database connections
- ❌ API calls
- ❌ File I/O operations
- ✅ Variable.get() only
- ✅ Lightweight assignments

### Airflow 2.0 Imports
```python
# ✅ Modern imports
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

# ❌ Legacy imports (will be caught and fixed)
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.hooks.snowflake_hook import SnowflakeHook
```

### Environment Awareness
```python
env = Variable.get("environment", default_var="local")

if env == "local":
    schedule_interval = None
    max_records = 50_000
elif env == "prod":
    schedule_interval = '0 1 * * *'
    max_records = None
```

## Configuration

The agent has access to:
- **Airflow 2 DAGs**: `/home/dev/airflow/data-airflow-2/dags`
- **Legacy DAGs**: `/home/dev/airflow/data-airflow-legacy/dags`
- **Output Directory**: `/home/dev/claude_test/generated_dags`
- **CLAUDE.md**: Full standards documentation

## Agent Capabilities

### dag-architect
- **Tools**: Read, Grep, Glob
- **Focus**: Architecture planning, dependency design, operator selection

### dag-developer
- **Tools**: Read, Write, Edit, Bash, Grep
- **Focus**: Code implementation, testing, documentation

### migration-specialist
- **Tools**: Read, Write, Edit, Grep, Glob
- **Focus**: Airflow 1.0→2.0 upgrades, refactoring, modernization

### airflow-code-reviewer
- **Tools**: Read, Grep, Glob
- **Focus**: Compliance checking, best practices validation, flake8 verification

## Output

Generated DAGs will:
- ✅ Pass flake8 linting
- ✅ Have complete type hints
- ✅ Be heartbeat-safe
- ✅ Follow CLAUDE.md standards
- ✅ Use Airflow 2.0 imports
- ✅ Include comprehensive documentation
- ✅ Have proper error handling
- ✅ Be environment-aware

## Next Steps After Generation

1. **Review the code**:
   ```bash
   cd generated_dags/dags/your_pipeline_name
   ```

2. **Run linting**:
   ```bash
   flake8 .
   ```

3. **Test locally**:
   ```bash
   docker compose up -d
   ```

4. **Access Airflow UI**:
   ```
   http://localhost:8080
   ```

5. **Deploy to staging** for validation

6. **Deploy to production** after approval

## Benefits

- **Standards Compliance**: Automatic enforcement of CLAUDE.md standards
- **Best Practices**: Built-in knowledge of Airflow 2.0 best practices
- **Modular Design**: Specialized agents for different concerns
- **Quality Assurance**: Automatic code review before completion
- **Migration Safety**: Systematic approach to legacy code updates
- **Documentation**: Comprehensive docstrings and comments
- **Type Safety**: Full type hint coverage

## Troubleshooting

If you encounter issues:

1. **Flake8 failures**: Review generated code for common issues (trailing whitespace, line length)
2. **Import errors**: Verify all imports are Airflow 2.0 provider-based
3. **Heartbeat issues**: Check for database/API calls at DAG level
4. **Type hint errors**: Ensure all typing imports are present

## Additional Resources

- CLAUDE.md: Complete standards documentation
- Airflow 2 DAGs: `/home/dev/airflow/data-airflow-2/dags` for examples
- Custom hooks: `common/custom_hooks/` for reusable components
- Custom operators: `common/custom_operators/` for task patterns
