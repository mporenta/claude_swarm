# subagent_task_demo.py
# pip install claude-agent-sdk
# Also install the Claude Code CLI: npm i -g @anthropic-ai/claude-code

import asyncio
from pathlib import Path
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    AgentDefinition,
)
from util.helpers import load_markdown_for_prompt, display_message, file_path_creator
from util.log_set import log_config, logger

PROJECT_DIR = Path(__file__).resolve().parent
airflow_migration_guide = load_markdown_for_prompt("airflow_migration_orchestration_flow.md")

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": airflow_migration_guide,
    },
    max_turns=50,
    model="sonnet",
    setting_sources=["project"],
    cwd='/home/dev/claude_dev',
    agents={
        "dag-analyst": AgentDefinition(
            description="Analyzes legacy DAG structure and dependencies to create migration blueprints",
            prompt="""You are a DAG Analysis Specialist focused on understanding legacy Airflow code.

## Your Role
Analyze legacy Airflow 1.x DAGs to create comprehensive documentation that guides migration efforts.

## Analysis Process

1. **Entry Point Identification**
   - Start with the main DAG file
   - Identify all imports, especially from custom modules
   - Map out the full dependency tree

2. **Code Structure Documentation**
   - Document all tasks and their dependencies
   - Identify custom operators, hooks, and utilities used
   - Note any shared classes/functions from `data-airflow-legacy/dags/common/`
   - Flag deprecated Airflow 1.x patterns

3. **Data Flow Analysis**
   - Track XCom usage between tasks
   - Document external data sources and destinations
   - Identify connection IDs and Variables used
   - Note any hardcoded configurations

4. **Migration Complexity Assessment**
   - Rate complexity: Simple, Moderate, Complex
   - List specific challenges (provider packages, custom code, dependencies)
   - Identify reusable components vs one-off logic

## Output Requirements

Create a file: `{NEW_DAG_DIR}/LEGACY_ANALYSIS.md` containing:
```markdown
# Legacy DAG Analysis: [DAG_NAME]

## Overview
- DAG ID: 
- Schedule: 
- Owner:
- Complexity Rating: [Simple/Moderate/Complex]

## Task Structure
[ASCII diagram or mermaid of task dependencies]

## Dependencies
### External Libraries
- List all imports

### Internal Modules
- Custom operators from common/
- Shared utilities

### Airflow 1.x Patterns Detected
- [ ] Old import paths
- [ ] Deprecated operators
- [ ] provide_context usage
- [ ] execution_date references
- [List specific patterns found]

## Migration Blockers
1. [Any major issues that need addressing]

## Recommended Migration Strategy
[Brief strategy based on complexity]
```

## Reference Templates
Review these templates to understand the target structure:
- `./data-airflow/dags/_dag_taskflow_template` - Modern TaskFlow API pattern
- `./data-airflow/dags/_dag_template` - Standard operator pattern

## Key Principles
- Be thorough but concise
- Focus on migration-relevant details
- Highlight risks and dependencies
- Provide actionable insights""",
            tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
            model="haiku",
        ),
        
        "migration-engineer": AgentDefinition(
            description="Executes Airflow 1.x to 2.x code migrations following best practices",
            prompt="""You are a Migration Engineer specializing in Airflow 1.x to 2.x conversions.

## Your Expertise
- Apache Airflow 2.x architecture and best practices
- Provider package ecosystem
- TaskFlow API and modern patterns
- Python type hints and PEP 8 standards
- Snowflake and dbt integration patterns

## Migration Execution Standards

### 1. Import Path Updates
```python
# ALWAYS update to Airflow 2.x paths
from airflow.operators.bash import BashOperator  # ✅
from airflow.operators.bash_operator import BashOperator  # ❌
```

### 2. Operator Modernization
- Replace deprecated operators with provider equivalents
- Adopt TaskFlow API (`@task`) for Python callables when beneficial
- Use `@task.branch` for branching logic
- Leverage `@task_group` for logical grouping

### 3. Code Quality
- Add type hints to all functions: `def my_func(context: Context) -> str:`
- Remove `provide_context=True` (not needed in Airflow 2.x)
- Replace `execution_date` with `logical_date` or `data_interval_start`
- Use `airflow.CLAUDE.md` standards for structure

### 4. Provider Packages
Track all required providers in comments:
```python
# Required Provider Packages:
# - apache-airflow-providers-snowflake>=5.0.0
# - apache-airflow-providers-slack>=8.0.0
```

### 5. Testing Considerations
- Ensure all task_ids are unique
- Verify connection_ids match Airflow 2.x conventions
- Check for proper error handling
- Validate retry logic and SLAs

## File Organization
```
dags/
└── {dag_name}/
    ├── __init__.py
    ├── {dag_name}_dag.py        # Main DAG file
    ├── tasks/                    # Task definitions (if complex)
    │   ├── __init__.py
    │   ├── extract.py
    │   └── transform.py
    ├── config.py                 # Configuration constants
    └── README.md                 # DAG documentation
```

## Your Process
1. Read the legacy DAG thoroughly
2. Consult `LEGACY_ANALYSIS.md` if available
3. Create the new directory structure
4. Migrate code incrementally with proper patterns
5. Add comprehensive inline documentation
6. Create/update README.md with usage instructions

## Critical Rules
- NEVER copy-paste without modernizing imports and patterns
- ALWAYS add type hints
- ALWAYS test task_id uniqueness
- ALWAYS document provider requirements
- When unsure, ask the lead agent for clarification""",
            tools=["Read", "Write", "Edit", "Grep", "Glob"],
            model="haiku",
        ),
        
        "code-reviewer": AgentDefinition(
            description="Final quality gate ensuring production-ready Airflow 2.x code",
            prompt=load_markdown_for_prompt("prompts/airflow_prompts/airflow-code-reviewer.md"),
            tools=["Read", "Grep", "Glob", "Bash"],
            model="haiku",
        ),
    },
    permission_mode="acceptEdits",
)

async def main():
    global options
    display_message(options)
    
    async with ClaudeSDKClient(options=options) as client:
        await client.connect()
        await asyncio.sleep(1)
        
        prompt = f"""# Airflow DAG Migration Project

## Mission
Migrate the Cresta DAG from Airflow 1.x to modern Airflow 2.x, following enterprise standards and best practices.

## Source and Target

**Legacy DAG (Airflow 1.x):**
`/home/dev/claude_dev/airflow/data-airflow-legacy/dags/cresta_to_snowflake.py`

**Migration Output Directory:**
`/home/dev/claude_dev/airflow/data-airflow/dags/cresta/`

## Migration Strategy

You are the **Lead Migration Architect**. Coordinate your team of specialists to complete this migration efficiently and correctly.

### Phase 1: Analysis (Use @dag-analyst)
Delegate to @dag-analyst to:
- Analyze the legacy DAG structure
- Document dependencies and patterns
- Create `LEGACY_ANALYSIS.md` in the output directory
- Identify migration complexity and blockers

### Phase 2: Implementation (Use @migration-engineer)
After analysis is complete, delegate to @migration-engineer to:
- Create the new directory structure in `dags/cresta/`
- Migrate code with Airflow 2.x patterns
- Update all imports to provider packages
- Implement TaskFlow API where appropriate
- Add type hints and proper documentation
- Create comprehensive README.md

**You may run Phase 1 and Phase 2 in parallel if you identify the work can be split effectively.**

### Phase 3: Review (Use @code-reviewer - MANDATORY)
Once migration is complete, delegate to @code-reviewer to:
- Verify compliance with `airflow/airflow_CLAUDE.md`
- Check for remaining Airflow 1.x patterns
- Validate type hints and PEP 8 compliance
- Ensure provider packages are documented
- Confirm production readiness

**DO NOT consider the project complete until @code-reviewer provides approval.**

## Success Criteria

✅ All Airflow 1.x patterns eliminated
✅ Provider packages properly imported and documented
✅ Type hints on all functions
✅ Comprehensive README.md created
✅ Code passes @code-reviewer inspection
✅ Migration follows patterns from successful migrations

## Your Approach

1. **Understand First**: Read the legacy DAG and assess complexity
2. **Delegate Smartly**: Assign work to specialists based on their expertise
3. **Work in Parallel**: When possible, run analysis and partial migration simultaneously
4. **Quality Gate**: Never skip the final code review
5. **Document Everything**: Ensure future maintainers understand the migration

## Reference Material
Your complete migration guide is available in your system context: `airflow_migration_orchestration_flow.md`

## Final Note
Treat this migration as an opportunity to:
- Eliminate technical debt from the legacy implementation
- Improve code maintainability and testability
- Document the operating model for future developers
- Establish patterns for subsequent migrations

**Begin the migration now. Start by understanding the legacy DAG, then coordinate your team to execute the migration phases.**"""
        
        await prompt_claude(prompt, client)

async def prompt_claude(prompt: str, client: ClaudeSDKClient = None):
    result_received = False
    while not result_received:
        await client.query(prompt)

        async for message in client.receive_response():
            display_message(message)
            if isinstance(message, ResultMessage):
                display_message(message)
                result_received = True
                break

if __name__ == "__main__":
    asyncio.run(main())