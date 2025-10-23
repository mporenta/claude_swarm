from typing import Any
import time
import asyncio, os
from pathlib import Path
from rich import print
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ThinkingBlock,
    ToolResultBlock,
    query,
    UserMessage,
    SystemMessage,
)
from util.helpers import load_markdown_for_prompt, display_message

class ConversationSession:
    """Maintains a single conversation session with Claude."""

    def __init__(self, options: ClaudeAgentOptions = None, project_dir: str = Path(__file__).resolve().parent):
        self.options = options
        self.client = ClaudeSDKClient(self.options)
        self.turn_count = 0
        self.project_dir = project_dir

    async def start(self):
        await self.client.connect()
        print("Starting conversation session. Claude will remember context.")
        print("Commands: 'exit' to quit, 'interrupt' to stop current task, 'new' for new session")

        while True:
            user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")

            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'interrupt':
                await self.client.interrupt()
                print("Task interrupted!")
                continue
            elif user_input.lower() == 'flask':
                await self.flask_app_orchestrator()

            elif user_input.lower() == 'new':
                # Disconnect and reconnect for a fresh session
                await self.client.disconnect()
                await self.client.connect()
                self.turn_count = 0
                print("Started new conversation session (previous context cleared)")
                continue

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


    async def flask_app_orchestrator(self):
        """
        Orchestrator that creates a Flask web app with random styling.
        Loads prompts from markdown files via load_markdown_for_prompt().
        """

        # Create project directories
        start = time.perf_counter()
        project_path = Path(self.project_dir)
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "templates").mkdir(exist_ok=True)
        display_message(f"[dim]📁 Created project directory at: {project_path.absolute()}[/dim]\n")

        # Load markdown prompt files
        
        main_prompt = load_markdown_for_prompt("prompts/main-query.md")

        display_message("[bold cyan]🚀 Starting Flask app orchestrator with markdown prompts...[/bold cyan]\n")

        tool_use_count = 0
        thinking_count = 0
        files_created = []

        async for message in self.client.query(prompt=main_prompt):
            display_message(message)

            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ThinkingBlock):
                        thinking_count += 1
                    elif isinstance(block, ToolUseBlock):
                        tool_use_count += 1
                        if block.name == "Write" and "file_path" in block.input:
                            files_created.append(block.input["file_path"])

            if isinstance(message, ResultMessage):
                cost = float(message.total_cost_usd or 0)
                display_message(f"\n[bold green]✅ Flask app creation complete![/bold green]")
                display_message(f"[dim]📊 Summary:[/dim]")
                display_message(f"   • Tool uses: {tool_use_count}")
                display_message(f"   • Thinking blocks: {thinking_count}")
                display_message(f"   • Files created: {len(files_created)}")
                if cost > 0:
                    display_message(f"   • Total cost: ${cost:.4f}")

                display_message(f"\n[bold]📁 Project location:[/bold] {project_path.absolute()}")
                display_message(f"[bold cyan]🚀 To run your Flask app:[/bold cyan]")
                display_message(f"   cd {project_path.absolute()}")
                display_message(f"   pip install -r requirements.txt")
                display_message(f"   python app.py\n")
                display_message(f"   Visit: [bold]http://localhost:5010[/bold]\n")
                if files_created:
                    display_message("[dim]Files created:[/dim]")
                    for file in files_created:
                        display_message(f"   • {file}")
                end = time.perf_counter()
                display_message(f"\n[bold]⏱️ Total time elapsed:  {end - start:.2f} seconds[/bold]\n")


if __name__ == "__main__":
    # Script location: /home/dev/claude_swarm/flask_agent.py
    script_path = Path(__file__).resolve()
    
    # Project root: /home/dev (where CLAUDE.md is located)
    project_root = script_path.parent.parent  # /home/dev
    
    # Output directory: /home/dev/claude_swarm/generated_code
    output_dir = script_path.parent / "generated_code"  # /home/dev/claude_swarm/generated_code
    
    display_message("[bold magenta]╔══════════════════════════════════════════════════════╗[/bold magenta]")
    display_message("[bold magenta]║  Flask Hello World App Generator (Markdown Prompts)  ║[/bold magenta]")
    display_message("[bold magenta]╚══════════════════════════════════════════════════════╝[/bold magenta]\n")
    display_message(f"[dim]Project root (CLAUDE.md location): {project_root}[/dim]")
    display_message(f"[dim]Output directory: {output_dir}[/dim]")
    display_message(f"[dim]Additional access: {project_root}/airflow/data-airflow-legacy/dags[/dim]\n")
    
    # Load markdown prompt files
    flask_dev_prompt = load_markdown_for_prompt("prompts/flask-developer.md")
    frontend_dev_prompt = load_markdown_for_prompt("prompts/frontend-developer.md")
    code_reviewer_prompt = load_markdown_for_prompt("prompts/code-reviewer.md")
    main_prompt = load_markdown_for_prompt("prompts/main-query.md")
    
    # Additional directory access for airflow DAGs
    airflow_dags_dir = project_root / "airflow" / "data-airflow-legacy" / "dags"
    
    options = ClaudeAgentOptions(
        system_prompt="claude_code",
        setting_sources=["project"],  # This tells SDK to look for .claude/settings.json at project root
        cwd=str(output_dir),  # Set working directory to output location where files will be created
        add_dirs=[str(airflow_dags_dir)],  # Grant access to airflow DAGs directory
        env={
        
        # Airflow configuration
        "AIRFLOW_HOME": "/home/dev/airflow",
        "AIRFLOW__CORE__DAGS_FOLDER": "/home/dev/airflow/data-airflow-legacy/dags",
        "FLASK_ENV": "development",
        "FLASK_PROJECT_PATH": str(output_dir),
        
        # Python configuration
        "PYTHONPATH": "/home/dev/.pyenv/versions/3.13.5/bin/python3",
    },
        agents={
            "app-archtiect": AgentDefinition(
                description="Expert Web App Archtiect.",
                prompt=main_prompt,
                tools=["Read", "Write", "Edit", "Bash"],
                model="sonnet",
            ),
            "flask-developer": AgentDefinition(
                description="Expert Flask developer.",
                prompt=flask_dev_prompt,
                tools=["Read", "Write", "Edit", "Bash"],
                model="sonnet",
            ),
            "frontend-developer": AgentDefinition(
                description="Expert frontend developer.",
                prompt=frontend_dev_prompt,
                tools=["Read", "Write", "Edit"],
                model="sonnet",
            ),
            "code-reviewer": AgentDefinition(
                description="Code review and best practices specialist.",
                prompt=code_reviewer_prompt,
                tools=["Read", "Grep", "Glob"],
                model="sonnet",
            ),
        },
        allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
        permission_mode="acceptEdits",
    )
    
    session = ConversationSession(options, project_dir=str(output_dir))
    asyncio.run(session.start())