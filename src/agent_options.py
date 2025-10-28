
import asyncio
import os
import signal
import sys
import time
from pathlib import Path


from claude_agent_sdk import (
    ClaudeAgentOptions,
    AgentDefinition,
 
)
from util.helpers import load_markdown_for_prompt
from util.log_set import logger



def dag_mirgration_agent() -> ClaudeAgentOptions:
    try:
        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": 'CRITICAL: Execute `/check-common-components` skill BEFORE recommending any custom operators, hooks, or utilities.',
            },
            max_turns=15,  # Orchestrator only - subagents have their own iteration limits in prompts
            model="sonnet",
            setting_sources=["project"],
            cwd="/home/dev/claude_dev",
            # Skills are auto-discovered from .claude/skills/ directory via setting_sources=["project"]
            # The check-common-components skill is available as: /check-common-components
            agents={
                
                "migration-specialist": AgentDefinition(
                    description="Converts legacy Airflow operators and patterns to modern equivalents",
                    prompt="""You are an Apache Airflow migration expert specializing in code transformation.

        🔧 MANDATORY: Execute `check-common-components` found in the skills: `/home/dev/claude_dev/claude_swarm/.claude/skills/check-common-components.md` skill BEFORE writing ANY custom operators, hooks, or utilities. Report findings before implementation.

        ⚠️ ITERATION LIMIT: You have a MAXIMUM of 8 tool-use iterations to complete your task. Plan your work efficiently:
        - Iterations 1-2: Analysis (read legacy DAG, identify components needed)
        - Iteration 3: Check existing components (run /check-common-components or search common/)
        - Iterations 4-6: Implementation (write migrated DAG, documentation)
        - Iterations 7-8: Final verification and handoff

        If you cannot complete the task within 8 iterations, stop and report what you've accomplished and what remains.

        Your focus areas:
        1. **Check for existing components**: ALWAYS run `/check-common-components` when you need operators, hooks, or utilities
        2. **Operator modernization**: Convert legacy operators to Airflow 2.x equivalents OR use existing common components
        3. **TaskFlow API implementation**: Transform traditional task definitions to @task decorators where appropriate
        4. **Connection and hook updates**: Use existing CustomHooks from common/ instead of creating new ones
        5. **Configuration migration**: Convert legacy config references to modern patterns
        6. **Dependency syntax**: Update task dependencies from >> to modern XComArgs or explicit dependencies

        When working on migrations:
        - FIRST: Run `/check-common-components` for any custom code needs
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
            allowed_tools=["Skill","Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        )
        return options
    except Exception as e:
        logger.error(f"Error in agent options: {e}")

def dag_migration_user_prompt(legacy_py_file: str, new_dag_path: str):

    prompt = f"""Perform a migration of an existing Airflow 1.x DAG to a 2.x DAG and create documentation.

## Task Overview
I need you to do the migration using subagents used in a successfully migrated DAG by comparing the legacy and modern versions.

⚠️ EFFICIENCY REQUIREMENTS:
- You (orchestrator) have a maximum of 15 conversation turns
- Each subagent has iteration limits defined in their prompts:
  * @migration-specialist: 8 iterations max
  * @airflow-code-reviewer: 5 iterations max
- Delegate work efficiently and avoid unnecessary back-and-forth
- Consolidate analysis and provide complete context when delegating

## 🔧 CRITICAL REQUIREMENT
Before any subagent writes custom operators, hooks, or utilities, they MUST execute the `/check-common-components` skill to search for existing reusable components in `./data-airflow/dags/common/`. This is NON-NEGOTIABLE.

## File to Analyze

**Legacy DAG (Airflow 1.x):**
`/home/dev/claude_dev/airflow/data-airflow-legacy/dags/{legacy_py_file}`

**Migrated DAG (Airflow 2.x): Path for output**
`/home/dev/claude_dev/airflow/data-airflow/dags/{new_dag_path}`

## Your Deliverables

- You convert legacy Apache Airflow assets into maintainable Airflow 2 implementations.
- Use your subagents team to speed the job and to help you stay on task.
- Use your team member: @migration-specialist as you see fit. You may use them asynchronously to speed up the work.
- Ensure all agents use `/check-common-components` before creating custom code.
- You must **END THE PROJECT** by getting a seal of approval from @airflow-code-reviewer.

## Delegation Best Practices
- Provide complete context to subagents in your delegation prompts (don't make them re-read files unnecessarily)
- Include analysis results, component inventory, and specific instructions
- Request comprehensive deliverables to minimize iteration rounds
- Only delegate when subagent expertise is truly needed

Treat every migration as an opportunity to eliminate legacy anti-patterns, improve reliability, and document the new operating model.
"""
    return prompt