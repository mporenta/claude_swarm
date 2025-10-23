import time
import asyncio
from pathlib import Path
from rich import print
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    ResultMessage,
    ToolUseBlock,
    ThinkingBlock,
    query,

)
from util.helpers import load_markdown_for_prompt, display_message


class AirflowAgentSession:
    """Maintains a single conversation session with Claude for Airflow development."""

    def __init__(self, options: ClaudeAgentOptions = None, project_dir: str = Path(__file__).resolve().parent):
        self.options = options
        self.client = ClaudeSDKClient(self.options)
        self.turn_count = 0
        self.project_dir = project_dir

    async def start(self):
        await self.client.connect()
        print("Starting Airflow agent session. Claude will remember context.")
        print("Commands: 'exit' to quit, 'interrupt' to stop current task, 'new' for new session")
        print("Special: 'create-dag' to create a new DAG, 'migrate-dag' to migrate from Airflow 1.0")

        while True:
            user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")

            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'interrupt':
                await self.client.interrupt()
                print("Task interrupted!")
                continue
            elif user_input.lower() == 'create-dag':
                await self.create_dag_orchestrator()
            elif user_input.lower() == 'migrate-dag':
                await self.migrate_dag_orchestrator()
            elif user_input.lower() == 'new':
                # Disconnect and reconnect for a fresh session
                await self.client.disconnect()
                await self.client.connect()
                self.turn_count = 0
                print("Started new conversation session (previous context cleared)")
                continue
            else:
                # Send message - Claude remembers all previous messages in this session
                await self.client.query(user_input)
                self.turn_count += 1

                # Process response
                print(f"[Turn {self.turn_count}] Claude: ", end="")
                async for message in self.client.receive_response():
                    display_message(message)
                    
                print()  # New line after response

        await self.client.disconnect()
        print(f"Conversation ended after {self.turn_count} turns.")

    async def create_dag_orchestrator(self):
        """
        Orchestrator that creates a new Airflow DAG following all standards.
        Uses specialized subagents for architecture, development, and code review.
        """
        start = time.perf_counter()
        project_path = Path(self.project_dir)
        project_path.mkdir(parents=True, exist_ok=True)
        display_message(f"[dim]📁 Output directory: {project_path.absolute()}[/dim]\n")

        # Load the main orchestrator prompt
        main_prompt = load_markdown_for_prompt("prompts/airflow_prompts/airflow-orchestrator.md")
        
        # Get user requirements
        dag_name = input("DAG name (e.g., 'marketo_to_snowflake'): ")
        schedule = input("Schedule (daily/intraday/hourly/nightly/weekly/monthly): ")
        description = input("Brief description of what this DAG should do: ")

        # Construct the creation request
        creation_request = f"""
Create a new Airflow 2 DAG with the following requirements:

**DAG Name:** {dag_name}
**Schedule:** {schedule}
**Description:** {description}

Follow the complete orchestration process:
1. Use @dag-architect to design the DAG structure
2. Use @dag-developer to implement the code
3. Use @airflow-code-reviewer to verify compliance

Ensure all CLAUDE.md standards are followed, including:
- Proper directory structure: dags/{dag_name}/
- src/main.py with Main class and execute() method
- Type hints on all functions
- Heartbeat-safe code
- Airflow 2.0 imports
- Environment awareness (local/staging/prod)
- Flake8 compliance

Create complete, production-ready code.
"""

        display_message("[bold cyan]🚀 Starting Airflow DAG creation orchestrator...[/bold cyan]\n")
        display_message(f"[bold]DAG Name:[/bold] {dag_name}")
        display_message(f"[bold]Schedule:[/bold] {schedule}")
        display_message(f"[bold]Description:[/bold] {description}\n")

        tool_use_count = 0
        thinking_count = 0
        files_created = []
        agent_switches = 0

        async for message in query(prompt=f"{main_prompt}\n\n{creation_request}", options=self.options):
            display_message(message)

            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ThinkingBlock):
                        thinking_count += 1
                    elif isinstance(block, ToolUseBlock):
                        tool_use_count += 1
                        if block.name == "Write" and "file_path" in block.input:
                            files_created.append(block.input["file_path"])
                        elif block.name == "SwitchAgent":
                            agent_switches += 1

            if isinstance(message, ResultMessage):
                cost = float(message.total_cost_usd or 0)
                display_message(f"\n[bold green]✅ DAG creation complete![/bold green]")
                display_message(f"[dim]📊 Summary:[/dim]")
                display_message(f"   • Tool uses: {tool_use_count}")
                display_message(f"   • Agent switches: {agent_switches}")
                display_message(f"   • Thinking blocks: {thinking_count}")
                display_message(f"   • Files created: {len(files_created)}")
                if cost > 0:
                    display_message(f"   • Total cost: ${cost:.4f}")

                display_message(f"\n[bold]📁 DAG location:[/bold] {project_path.absolute()}/dags/{dag_name}/")
                display_message(f"[bold cyan]🚀 Next steps:[/bold cyan]")
                display_message(f"   1. Review the generated code")
                display_message(f"   2. Run: flake8 dags/{dag_name}/")
                display_message(f"   3. Test locally: docker compose up -d")
                display_message(f"   4. Access Airflow UI: http://localhost:8080\n")
                
                if files_created:
                    display_message("[dim]Files created:[/dim]")
                    for file in files_created:
                        display_message(f"   • {file}")
                
                end = time.perf_counter()
                display_message(f"\n[bold]⏱️ Total time elapsed: {end - start:.2f} seconds[/bold]\n")

    async def migrate_dag_orchestrator(self):
        """
        Orchestrator that migrates a DAG from Airflow 1.0 to 2.0.
        Uses specialized subagents for migration, architecture, and review.
        """
        start = time.perf_counter()
        project_path = Path(self.project_dir)
        project_path.mkdir(parents=True, exist_ok=True)
        display_message(f"[dim]📁 Output directory: {project_path.absolute()}[/dim]\n")

        # Load the main orchestrator prompt
        main_prompt = load_markdown_for_prompt("prompts/airflow_prompts/airflow-orchestrator.md")
        
        # Get user requirements
        legacy_dag_path = input("Path to legacy DAG file: ")
        new_dag_name = input("New DAG name (leave blank to use same name): ")
        
        migration_request = f"""
Migrate an Airflow 1.0 DAG to Airflow 2.0 with full modernization.

**Legacy DAG Path:** {legacy_dag_path}
**New DAG Name:** {new_dag_name if new_dag_name else "Use original name"}

Follow the complete migration orchestration process:
1. Use @migration-specialist to analyze the legacy DAG and identify all required changes
2. Use @dag-architect to design the modernized structure
3. Use @migration-specialist to implement the migration
4. Use @dag-developer for any additional enhancements
5. Use @airflow-code-reviewer to verify complete compliance

Migration must include:
- Update all imports to Airflow 2.0 provider-based structure
- Refactor monolithic functions into modular, focused tasks
- Implement TaskGroups for logical organization
- Convert Variables to Connections where appropriate
- Ensure heartbeat-safe code (no DB/API calls at DAG level)
- Add comprehensive type hints
- Add proper documentation
- Implement error handling and callbacks
- Ensure flake8 compliance

Create production-ready, modernized code following all CLAUDE.md standards.
"""

        display_message("[bold cyan]🚀 Starting Airflow DAG migration orchestrator...[/bold cyan]\n")
        display_message(f"[bold]Legacy DAG:[/bold] {legacy_dag_path}")
        display_message(f"[bold]New DAG Name:[/bold] {new_dag_name if new_dag_name else '(same as original)'}\n")

        tool_use_count = 0
        thinking_count = 0
        files_created = []
        agent_switches = 0

        async for message in query(prompt=f"{main_prompt}\n\n{migration_request}", options=self.options):
            display_message(message)

            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ThinkingBlock):
                        thinking_count += 1
                    elif isinstance(block, ToolUseBlock):
                        tool_use_count += 1
                        if block.name == "Write" and "file_path" in block.input:
                            files_created.append(block.input["file_path"])
                        elif block.name == "SwitchAgent":
                            agent_switches += 1

            if isinstance(message, ResultMessage):
                cost = float(message.total_cost_usd or 0)
                display_message(f"\n[bold green]✅ DAG migration complete![/bold green]")
                display_message(f"[dim]📊 Summary:[/dim]")
                display_message(f"   • Tool uses: {tool_use_count}")
                display_message(f"   • Agent switches: {agent_switches}")
                display_message(f"   • Thinking blocks: {thinking_count}")
                display_message(f"   • Files created: {len(files_created)}")
                if cost > 0:
                    display_message(f"   • Total cost: ${cost:.4f}")

                display_message(f"\n[bold]📁 Migrated DAG location:[/bold] {project_path.absolute()}/")
                display_message(f"[bold cyan]🚀 Next steps:[/bold cyan]")
                display_message(f"   1. Review migration changes")
                display_message(f"   2. Run: flake8 dags/")
                display_message(f"   3. Test locally: docker compose up -d")
                display_message(f"   4. Compare behavior with legacy DAG")
                display_message(f"   5. Deploy to staging for validation\n")
                
                if files_created:
                    display_message("[dim]Files created:[/dim]")
                    for file in files_created:
                        display_message(f"   • {file}")
                
                end = time.perf_counter()
                display_message(f"\n[bold]⏱️ Total time elapsed: {end - start:.2f} seconds[/bold]\n")


if __name__ == "__main__":
    # Script location: /home/dev/claude_test/airflow_agent.py
    script_path = Path(__file__).resolve()
    
    # Project root: /home/dev (where CLAUDE.md is located)
    project_root = script_path.parent.parent  # /home/dev
    
    # Output directory: /home/dev/claude_test/generated_dags
    output_dir = script_path.parent / "generated_dags"  # /home/dev/claude_test/generated_dags
    
    display_message("[bold magenta]╔═══════════════════════════════════════════════════╗[/bold magenta]")
    display_message("[bold magenta]║  Airflow DAG Development Agent (Multi-Agent)     ║[/bold magenta]")
    display_message("[bold magenta]╚═══════════════════════════════════════════════════╝[/bold magenta]\n")
    display_message(f"[dim]Project root (CLAUDE.md location): {project_root}[/dim]")
    display_message(f"[dim]Output directory: {output_dir}[/dim]")
    display_message(f"[dim]Airflow DAGs directory: {project_root}/airflow/data-airflow-2/dags[/dim]\n")
    
    # Load markdown prompt files for all subagents
    dag_architect_prompt = load_markdown_for_prompt("prompts/airflow_prompts/dag-architect.md")
    dag_developer_prompt = load_markdown_for_prompt("prompts/airflow_prompts/dag-developer.md")
    migration_specialist_prompt = load_markdown_for_prompt("prompts/airflow_prompts/migration-specialist.md")
    code_reviewer_prompt = load_markdown_for_prompt("prompts/airflow_prompts/airflow-code-reviewer.md")
    
    # Additional directory access for airflow DAGs
    airflow_2_dags_dir = project_root / "airflow" / "data-airflow-2" / "dags"
    airflow_legacy_dags_dir = project_root / "airflow" / "data-airflow-legacy" / "dags"
    
    options = ClaudeAgentOptions(
        system_prompt="claude_code",
        setting_sources=["project"],  # Look for .claude/settings.json at project root
        cwd=str(output_dir),  # Set working directory to output location
        add_dirs=[
            str(airflow_2_dags_dir),      # Grant access to Airflow 2 DAGs
            str(airflow_legacy_dags_dir), # Grant access to legacy DAGs for migration
        ],
        env={
            # Airflow configuration
            "AIRFLOW_HOME": str(project_root / "airflow"),
            "AIRFLOW__CORE__DAGS_FOLDER": str(airflow_2_dags_dir),
            
            # Python configuration
            "PYTHONPATH": "/home/dev/.pyenv/versions/3.13.5/bin/python3",
            
            # Project configuration
            "PROJECT_ROOT": str(project_root),
            "OUTPUT_DIR": str(output_dir),
        },
        agents={
            "dag-architect": AgentDefinition(
                description="Expert Airflow architect for planning DAG structure and dependencies.",
                prompt=dag_architect_prompt,
                tools=["Read", "Grep", "Glob"],
                model="sonnet",
            ),
            "dag-developer": AgentDefinition(
                description="Expert Airflow 2 developer for writing production-ready DAG code.",
                prompt=dag_developer_prompt,
                tools=["Read", "Write", "Edit", "Bash", "Grep"],
                model="sonnet",
            ),
            "migration-specialist": AgentDefinition(
                description="Expert in migrating Airflow 1.0 DAGs to 2.0 with modernization.",
                prompt=migration_specialist_prompt,
                tools=["Read", "Write", "Edit", "Grep", "Glob"],
                model="sonnet",
            ),
            "airflow-code-reviewer": AgentDefinition(
                description="Code review specialist for Airflow best practices and CLAUDE.md compliance.",
                prompt=code_reviewer_prompt,
                tools=["Read", "Grep", "Glob"],
                model="sonnet",
            ),
        },
        allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        permission_mode="acceptEdits",
    )
    
    session = AirflowAgentSession(options, project_dir=str(output_dir))
    asyncio.run(session.start())
