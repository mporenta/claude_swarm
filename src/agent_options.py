import os
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions,
    AgentDefinition,
)
from util.helpers import load_markdown_for_prompt
from util.log_set import logger

DATA_AIRFLOW_ROOT = os.getenv("DATA_AIRFLOW_ROOT", "/home/dev/claude_dev/airflow/data-airflow")
DATA_AIRFLOW_LEGACY_ROOT = os.getenv(
    "DATA_AIRFLOW_LEGACY_ROOT", "/home/dev/claude_dev/airflow/data-airflow-legacy"
)
DATA_AIRFLOW_DAGS_DIR = os.getenv("DATA_AIRFLOW_DAGS_DIR", f"{DATA_AIRFLOW_ROOT}/dags")
DATA_AIRFLOW_LEGACY_DAGS_DIR = os.getenv("DATA_AIRFLOW_LEGACY_DAGS_DIR", f"{DATA_AIRFLOW_LEGACY_ROOT}/dags")
CLAUDE_WORKING_DIR = os.getenv("CLAUDE_WORKING_DIR", "/home/dev/claude_dev")
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
        default_cwd = project_root / "generated_dags"

        # Use environment variable if set, otherwise use default
        cwd_path = os.getenv("CLAUDE_WORKING_DIR", str(default_cwd))

        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": """
🎯 ORCHESTRATOR ROLE: DELEGATE IMMEDIATELY, DON'T MICRO-MANAGE

You are an orchestrator, NOT a worker. Your ONLY job is to:
1. Understand what DAG needs migrating
2. IMMEDIATELY delegate to @migration-specialist via Task tool
3. After migration completes, IMMEDIATELY delegate to @airflow-code-reviewer via Task tool
4. Review final code review output

DO NOT:
- ❌ Read files yourself
- ❌ Run discovery commands
- ❌ Explore the codebase
- ❌ Track skills yourself
- ❌ Create TodoWrite lists
- ❌ Spend turns on setup

DO:
- ✅ Delegate to @migration-specialist on Turn 1-2 MAX
- ✅ Include the legacy DAG path in delegation
- ✅ Let subagent do ALL the work
- ✅ When migration-specialist completes, delegate to @airflow-code-reviewer
- ✅ Review code review output when complete

DELEGATION PATTERN:
1. Task tool → migration-specialist → "Migrate {dag_path} from Airflow 1.x to 2.x. Use common components. Follow skills workflow."
2. Task tool → airflow-code-reviewer → "Review the migrated DAG at {output_path}. Validate against Airflow 2.x best practices, check for DRY violations, run validation checks."

Remember: More orchestrator turns = exponentially more cost. DELEGATE IMMEDIATELY.
""",
            },
            max_turns=8,  # Orchestrator needs budget for: migration delegation (1-2), code review delegation (3-4), final review (5+)
            model="sonnet",
            setting_sources=["project"],
            cwd=cwd_path,
            add_dirs=[
                DATA_AIRFLOW_ROOT,  # New DAG source
                DATA_AIRFLOW_LEGACY_ROOT,  # Legacy DAG destination
            
            ],
            # Skills are auto-discovered from .claude/skills/ directory via setting_sources=["project"]
            # The check-common-components skill is available as: /check-common-components
            agents={
                "migration-specialist": AgentDefinition(
                    description="Converts legacy Airflow operators and patterns to modern equivalents",
                    prompt=load_markdown_for_prompt(
            "prompts/airflow_prompts/migration-specialist.md"
        ),
                    tools=["Read", "Write", "Edit", "Grep", "Glob", "Bash", "Skill"],
                    model="haiku",
                ),
                "airflow-code-reviewer": AgentDefinition(
                    description="Validates migrated code against Airflow 2.x best practices and standards",
                    prompt=load_markdown_for_prompt(
                        "prompts/airflow_prompts/airflow-code-reviewer.md"
                    ),
                    tools=["Read", "Grep", "Glob", "Bash", "Skill"],
                    model="sonnet",
                ),
            },
            permission_mode="acceptEdits",
            allowed_tools=["Skill", "Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        )
        return options
    except Exception as e:
        logger.error(f"Error in agent options: {e}")


def dag_migration_user_prompt(
    _legacy_py_file: str, _new_dag_path: str, cwd_path: str = None
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
        default_cwd = project_root / "generated_dags"
        cwd_path = os.getenv("CLAUDE_WORKING_DIR", str(default_cwd))

    # Use environment variables for paths
    legacy_dag_full_path = f"{DATA_AIRFLOW_LEGACY_DAGS_DIR}/{_legacy_py_file}"
    output_dag_full_path = f"{DATA_AIRFLOW_DAGS_DIR}/{_new_dag_path}"
    common_components_path = f"{DATA_AIRFLOW_DAGS_DIR}/common"
    working_dir = cwd_path if cwd_path else CLAUDE_WORKING_DIR

    prompt = f"""🎯 IMMEDIATE DELEGATION REQUIRED

**Legacy DAG:** `{legacy_dag_full_path}`
**Output Location:** `{output_dag_full_path}`
**Working Directory:** `{working_dir}`

Your task: Two-step delegation process:

STEP 1: Delegate to @migration-specialist on Turn 1 or 2 MAX
STEP 2: After migration completes, delegate to @airflow-code-reviewer for validation

Use the Task tool immediately with this delegation:

"Migrate {legacy_dag_full_path} from Airflow 1.x to 2.x.

CRITICAL INSTRUCTIONS:
1. FIRST: Read /home/dev/claude_dev/claude_swarm/SKILL_USAGE_CRITERIA.md - This defines which skills to run based on DAG complexity
2. Assess DAG complexity (lines, structure) to determine file output (1-2 files for simple, 2-3 for medium, 3-5 for complex)
3. Run ONLY mandatory skills + conditional skills that match criteria (don't run all 13 skills)
4. Use common components from {common_components_path} - NO custom implementations
5. Output files to {output_dag_full_path}
6. Keep it simple: Simple DAGs stay simple (1-2 files), don't over-engineer

KEY PRINCIPLE: 'Migrate to 2.x syntax, not to best practice abstractions.'"

After migration completes, delegate to @airflow-code-reviewer:

"Review the migrated DAG at {output_dag_full_path}. Validate against Airflow 2.x best practices, check for DRY violations using /check-common-components skill, run flake8 validation, and provide comprehensive code review report."

DO NOT explore, read files, analyze, or create todos. Your system prompt tells you exactly what to do: DELEGATE IMMEDIATELY.
"""
    return prompt
