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
        # Find project root using the same logic as file_path_creator
        def find_project_root(start: Path) -> Path:
            """Find project root by looking for marker files."""
            markers = {"pyproject.toml", "requirements.txt", ".git", ".gitignore"}
            for parent in [start] + list(start.parents):
                if any((parent / marker).exists() for marker in markers):
                    return parent
            return start

        # Get the correct working directory from environment or use project root
        script_dir = Path(__file__).resolve().parent
        project_root = find_project_root(script_dir)
        default_cwd = project_root / "claude_dev"

        # Use environment variable if set, otherwise use default
        cwd_path = os.getenv("CLAUDE_WORKING_DIR", str(default_cwd))

        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": """
CRITICAL DRY ENFORCEMENT:
- Execute `/check-common-components` skill BEFORE recommending any custom operators, hooks, or utilities
- For all migrations, follow the 4-phase skills workflow documented in .claude/skills/README.md
- Phase 1 skills (validate-migration-readiness, analyze-legacy-dag, check-common-components, find-anti-patterns) are MANDATORY before implementation
- Skills are auto-discovered from .claude/skills/ directory
""",
            },
            max_turns=15,  # Orchestrator only - subagents have their own iteration limits in prompts
            model="sonnet",
            setting_sources=["project"],
            cwd=cwd_path,
            # Skills are auto-discovered from .claude/skills/ directory via setting_sources=["project"]
            # The check-common-components skill is available as: /check-common-components
            agents={
                "migration-specialist": AgentDefinition(
                    description="Converts legacy Airflow operators and patterns to modern equivalents",
                    prompt="""You are an Apache Airflow migration expert specializing in code transformation.

⚠️ ITERATION LIMIT: You have a MAXIMUM of 8 tool-use iterations to complete your task. Plan your work efficiently.

🔧 MANDATORY SKILLS WORKFLOW - Execute in order:

Phase 1: Pre-Migration Analysis (Iterations 1-3, ALWAYS RUN FIRST)
1. /validate-migration-readiness - Pre-flight checklist
2. /analyze-legacy-dag - Detailed structure analysis
3. /check-common-components ⭐ CRITICAL - Prevent code duplication
4. /find-anti-patterns - Identify DRY violations

Phase 2: Migration Planning (Before Coding)
5. /map-operators-to-common - Which operators to use
6. /extract-business-logic - Where code should live
7. /suggest-template-choice - TaskFlow vs Traditional
8. /analyze-connection-usage - Connection requirements

Phase 3: Implementation Details (As Needed, Iterations 4-7)
9. /compare-dag-configs - Parameter migration
10. /check-xcom-patterns - XCom conversion
11. /identify-dependencies - Dependency patterns
12. /check-dynamic-tasks - Loop conversion

Phase 4: Handoff (Iteration 8)
- Document all skills executed and their findings
- Report LOC reduction, anti-patterns eliminated
- Hand off to airflow-code-reviewer

CRITICAL RULES:
- DO NOT SKIP Phase 1 skills - They prevent wasted effort
- ALWAYS run /check-common-components before custom code
- Document skill results before implementation
- Use existing components from common/ per skill recommendations

Your focus areas:
1. **Skills execution**: Follow the 4-phase workflow above
2. **DRY compliance**: Use common components, never duplicate
3. **TaskFlow API**: Convert to @task where appropriate
4. **Type safety**: Add type hints throughout
5. **Documentation**: Record all decisions and skill results

If you cannot complete within 8 iterations, report what's done and what remains with skill execution status.""",
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
            allowed_tools=["Skill", "Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        )
        return options
    except Exception as e:
        logger.error(f"Error in agent options: {e}")


def dag_migration_user_prompt(
    legacy_py_file: str, new_dag_path: str, cwd_path: str = None
) -> str:
    # If cwd_path not provided, use default with robust project root finding
    if cwd_path is None:

        def find_project_root(start: Path) -> Path:
            """Find project root by looking for marker files."""
            markers = {"pyproject.toml", "requirements.txt", ".git", ".gitignore"}
            for parent in [start] + list(start.parents):
                if any((parent / marker).exists() for marker in markers):
                    return parent
            return start

        script_dir = Path(__file__).resolve().parent
        project_root = find_project_root(script_dir)
        default_cwd = project_root / "claude_dev"
        cwd_path = os.getenv("CLAUDE_WORKING_DIR", str(default_cwd))

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

## 🔧 CRITICAL SKILLS WORKFLOW

All subagents MUST follow the 4-phase skills workflow documented in `.claude/skills/README.md`:

**Phase 1: Pre-Migration Analysis (MANDATORY - Run First)**
- `/validate-migration-readiness` - Pre-flight checklist
- `/analyze-legacy-dag` - Structure analysis
- `/check-common-components` ⭐ **NON-NEGOTIABLE** - Search common/ for existing components
- `/find-anti-patterns` - DRY violations and security issues

**Phase 2: Migration Planning (Before Implementation)**
- `/map-operators-to-common` - Which common components to use
- `/extract-business-logic` - Where code should live
- `/suggest-template-choice` - TaskFlow vs Traditional
- `/analyze-connection-usage` - Connection mapping

**Phase 3: Implementation Details (As Needed)**
- `/compare-dag-configs` - Parameter migration
- `/check-xcom-patterns` - XCom conversion
- `/identify-dependencies` - Dependency patterns
- `/check-dynamic-tasks` - Loop conversion

**Phase 4: Validation (Post-Migration)**
- `/generate-migration-diff` - Document improvements

**DO NOT skip Phase 1 skills** - They prevent hours of wasted effort and ensure DRY compliance.

## File to Analyze

**Legacy DAG (Airflow 1.x):**
`{cwd_path}/airflow/data-airflow-legacy/dags/{{legacy_py_file}}`

**Migrated DAG (Airflow 2.x): Path for output**
`{cwd_path}/airflow/data-airflow/dags/{{new_dag_path}}`

## Your Deliverables

- You convert legacy Apache Airflow assets into maintainable Airflow 2 implementations.
- Use your subagents team to speed the job and to help you stay on task.
- Use your team member: @migration-specialist as you see fit. You may use them asynchronously to speed up the work.
- **ENFORCE Phase 1 skills execution** - Verify @migration-specialist ran all 4 Phase 1 skills before implementation
- Ensure all agents use `/check-common-components` before creating custom code.
- Review skill execution results and common component usage in final code
- You must **END THE PROJECT** by getting a seal of approval from @airflow-code-reviewer with skills validation.

## Delegation Best Practices
- Provide complete context to subagents in your delegation prompts (don't make them re-read files unnecessarily)
- Include analysis results, component inventory, and specific instructions
- Request comprehensive deliverables to minimize iteration rounds
- Only delegate when subagent expertise is truly needed

Treat every migration as an opportunity to eliminate legacy anti-patterns, improve reliability, and document the new operating model.
"""
    return prompt
