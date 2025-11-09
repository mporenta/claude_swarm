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
from src.agent_options import dag_mirgration_agent
from util.helpers import load_markdown_for_prompt, display_message, file_path_creator
from util.log_set import log_config, logger

PROJECT_DIR = Path(__file__).resolve().parent
airflow_dev_prompt = load_markdown_for_prompt("airflow_migration_orchestration_flow.md")
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": 'CRITICAL: Execute `/check-common-components` skill BEFORE recommending any custom operators, hooks, or utilities.',
    },
    max_turns=25,
    model="sonnet",
    setting_sources=[
        "project"
    ],  # This tells SDK to look for .claude/settings.json at project root
    cwd="/home/dev/claude_dev",
    # Skills are auto-discovered from .claude/skills/ directory via setting_sources=["project"]
    # The check-common-components skill is available as: /check-common-components
    agents={
        "scrum-master": AgentDefinition(
            description="Analyzes legacy DAG structure and creates migration roadmap",
            prompt="""You are a technical analyst specializing in Apache Airflow migrations.

🔧 CRITICAL: Execute `/check-common-components` skill BEFORE recommending any custom operators, hooks, or utilities.

Your responsibilities:
1. **Analyze the legacy DAG structure**: Read all .py files starting from the entry point, working upstream to map dependencies
2. **Identify common patterns**: Use `/check-common-components` to search `./data-airflow/dags/common` for reusable operators, hooks, and callbacks. Document what exists and what can be reused.
3. **Create migration documentation**: Compare legacy structure against modern templates (_dag_taskflow_template and _dag_template in ./data-airflow/dags/)
4. **Output deliverable**: Write a comprehensive markdown outline saved to data-airflow/dags/{NEW_DAG_DIR}/MIGRATION_PLAN.md

The outline should include:
- Current DAG structure and dependencies
- List of operators and their modern equivalents
- Identified anti-patterns to eliminate
- Recommended refactoring steps
- Risk assessment

Be thorough but concise. Your analysis guides the migration team.""",
            tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
            model="haiku",
        ),
        "migration-specialist": AgentDefinition(
            description="Converts legacy Airflow operators and patterns to modern equivalents",
            prompt="""You are an Apache Airflow migration expert specializing in code transformation.

🔧 MANDATORY: Execute `/check-common-components` skill BEFORE writing ANY custom operators, hooks, or utilities. Report findings before implementation.

Your focus areas:
1. **Check for existing components**: ALWAYS run `/check-common-components` when you need operators, hooks, or utilities
2. **Operator modernization**: Convert legacy operators to Airflow 2.x equivalents OR use existing common components
3. **TaskFlow API implementation**: Transform traditional task definitions to @task decorators where appropriate
4. **Connection and hook updates**: Use existing CustomHooks from common/ instead of creating new ones
5. **Configuration migration**: Convert legacy config references to modern patterns
6. **Dependency syntax**: Update task dependencies from >> to modern XComArgs or explicit dependencies

When working on migrations:
- FIRST: Run `/check-common-components` for any custom code needs
- Reference the scrum-master's analysis for context
- Follow patterns from successfully migrated DAGs
- Preserve business logic while modernizing structure
- Add type hints and improve error handling
- Document any assumptions or decisions

Hand off completed code sections to the airflow-code-reviewer for validation.""",
            tools=["Read", "Write", "Edit", "Grep", "Glob"],
            model="haiku",
        ),
        "airflow-code-reviewer": AgentDefinition(
            description="Validates migrated code against Airflow 2.x best practices and standards",
            prompt=load_markdown_for_prompt(
                "prompts/airflow_prompts/airflow-code-reviewer.md"
            ),
            tools=["Read", "Grep", "Glob", "Bash"],
            model="haiku",
        ),
    },
    permission_mode="acceptEdits",
)
async def prompt_claude(prompt: str, client: ClaudeSDKClient = None):
    result_received = False
    while not result_received:
        await client.query(prompt)

        # Stream and print everything until the run finishes
        async for message in client.receive_response():
            display_message(message)
            if isinstance(message, ResultMessage):
                display_message(message)
                result_received = True
                break


async def main():
   

    async with ClaudeSDKClient(options=dag_mirgration_agent()) as client:
        await client.connect()
        await asyncio.sleep(1)
     

        prompt = f"""Perform a migration of an existing Airflow 1.x DAG to a 2.x DAG and create documentation.

## Task Overview
I need you to do the migration using subagents used in a successfully migrated DAG by comparing the legacy and modern versions.

## 🔧 CRITICAL REQUIREMENT
Before any subagent writes custom operators, hooks, or utilities, they MUST execute the `/check-common-components` skill to search for existing reusable components in `./data-airflow/dags/common/`. This is NON-NEGOTIABLE.

## File to Analyze

**Legacy DAG (Airflow 1.x):**
`/home/dev/claude_dev/airflow/data-airflow-legacy/dags/cresta_to_snowflake.py`

**Migrated DAG (Airflow 2.x): Path for output**
`/home/dev/claude_dev/airflow/data-airflow/dags/cresta`

## Your Deliverables

- You convert legacy Apache Airflow assets into maintainable Airflow 2 implementations.
- Use your subagents team to speed the job and to help you stay on task.
- Use your team members: @scrum-master and @migration-specialist as you see fit. You may use them asynchronously to speed up the work.
- Ensure all agents use `/check-common-components` before creating custom code.
- You must **END THE PROJECT** by getting a seal of approval from @airflow-code-reviewer.



Treat every migration as an opportunity to eliminate legacy anti-patterns, improve reliability, and document the new operating model.
"""
        await prompt_claude(prompt, client)


if __name__ == "__main__":
    asyncio.run(main())
