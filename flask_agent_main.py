from dotenv import load_dotenv

load_dotenv()
import signal
import time
import asyncio, os, sys
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
    UserMessage,
    SystemMessage,
)
from util.helpers import load_markdown_for_prompt, display_message
from util.log_set import log_config, logger


class ConversationSession:
    """Maintains a single conversation session with Claude."""

    def __init__(
        self,
        options: ClaudeAgentOptions = None,
        project_dir: str = Path(__file__).resolve().parent,
    ):
        self.options = options
        self.client = ClaudeSDKClient(self.options)
        self.turn_count = 0
        self.project_dir = project_dir
        self.client_agent = None
        self.should_exit = False

    async def start(self):
        """Start the conversation session with proper interrupt handling."""
        try:
            await self.client.connect()
            print("Starting conversation session. Claude will remember context.")
            print(
                "Commands: 'exit' to quit, 'interrupt' to stop current task, 'new' for new session"
            )

            while True:
                try:
                    user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")
                except (KeyboardInterrupt, EOFError):
                    print("\n\nInterrupted by user. Exiting...")
                    break

                # Handle exit command
                if user_input.lower() == "exit":
                    print("Exiting conversation...")
                    break

                # Handle interrupt command
                elif user_input.lower() == "interrupt":
                    try:
                        await self.client.interrupt()
                        print("Task interrupted!")
                    except Exception as e:
                        logger.error(f"Error interrupting task: {e}")
                        print("Failed to interrupt task.")
                    continue

                # Handle flask orchestrator command
                elif user_input.lower() == "flask":
                    try:
                        await self.flask_app_orchestrator()
                    except KeyboardInterrupt:
                        print("\n\nFlask orchestrator interrupted!")
                        break
                    except Exception as e:
                        logger.error(f"Error in flask orchestrator: {e}")
                        print(f"Flask orchestrator failed: {e}")
                    continue

                # Handle new session command
                elif user_input.lower() == "new":
                    try:
                        await self.client.disconnect()
                        await self.client.connect()
                        self.turn_count = 0
                        print(
                            "Started new conversation session (previous context cleared)"
                        )
                    except Exception as e:
                        logger.error(f"Error creating new session: {e}")
                        print(f"Failed to create new session: {e}")
                    continue

                # Send regular message - Claude remembers all previous messages in this session
                try:
                    await self.client.query(user_input)
                    self.turn_count += 1

                    # Process response
                    print(f"[Turn {self.turn_count}] Claude: ", end="")
                    async for message in self.client.receive_response():
                        display_message(message)

                    print()  # New line after response

                except KeyboardInterrupt:
                    print("\n\nResponse interrupted by user!")
                    break
                except asyncio.CancelledError:
                    print("\n\nTask was cancelled.")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    print(f"\nError: {e}")
                    # Continue the loop to allow recovery

        except KeyboardInterrupt:
            print("\n\nSession interrupted by user.")
        except asyncio.CancelledError:
            print("\n\nAsync session cancelled.")
        except Exception as e:
            logger.error(f"Unexpected error in session: {e}")
            print(f"\nUnexpected error: {e}")
        finally:
            # Always attempt cleanup
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")

            print(f"\nConversation ended after {self.turn_count} turns.")

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
        display_message(
            f"[dim]📁 Created project directory at: {project_path.absolute()}[/dim]\n"
        )

        # Load markdown prompt files

        main_prompt = load_markdown_for_prompt("prompts/main-query.md")

        display_message(
            "[bold cyan]🚀 main Starting Flask app orchestrator with markdown prompts...[/bold cyan]\n"
        )

        tool_use_count = 0
        thinking_count = 0
        files_created = []
        async with self.client as self.client_agent:
            await self.client_agent.query(prompt=main_prompt)
            async for message in self.client_agent.receive_response():

                # async for message in self.client.query(prompt=main_prompt):
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
                    display_message(
                        f"\n[bold green]✅ Flask app creation complete![/bold green]"
                    )
                    display_message(f"[dim]📊 Summary:[/dim]")
                    display_message(f"   • Tool uses: {tool_use_count}")
                    display_message(f"   • Thinking blocks: {thinking_count}")
                    display_message(f"   • Files created: {len(files_created)}")
                    if cost > 0:
                        display_message(f"   • Total cost: ${cost:.4f}")

                    display_message(
                        f"\n[bold]📁 Project location:[/bold] {project_path.absolute()}"
                    )
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
                    display_message(
                        f"\n[bold]⏱️ Total time elapsed:  {end - start:.2f} seconds[/bold]\n"
                    )


if __name__ == "__main__":
    # logging setup
    CLAUDE_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    log_config.setup(CLAUDE_LOG_LEVEL)
    # Script location: /home/dev/claude_swarm/flask_agent.py
    script_path = Path(__file__).resolve()

    # Project root: /home/dev (where CLAUDE.md is located)
    project_root = script_path.parent.parent  # /home/dev

    # Output directory: /home/dev/claude_swarm/generated_code
    output_dir = (
        script_path.parent / "generated_code"
    )  # /home/dev/claude_swarm/generated_code

    airflow_dags_dir = project_root / "data-airflow" / "dags"

    display_message(
        "[bold magenta]╔══════════════════════════════════════════════════════╗[/bold magenta]"
    )
    display_message(
        "[bold magenta]║  Flask Hello World App Generator (Markdown Prompts)  ║[/bold magenta]"
    )
    display_message(
        "[bold magenta]╚══════════════════════════════════════════════════════╝[/bold magenta]\n"
    )
    display_message(f"[dim]Project root (CLAUDE.md location): {project_root}[/dim]")
    display_message(f"[dim]Output directory: {output_dir}[/dim]")
    display_message(f"[dim]Additional access: {airflow_dags_dir}[/dim]\n")

    # Load markdown prompt files
    flask_dev_prompt = load_markdown_for_prompt("prompts/flask-developer.md")
    frontend_dev_prompt = load_markdown_for_prompt("prompts/frontend-developer.md")
    code_reviewer_prompt = load_markdown_for_prompt("prompts/code-reviewer.md")
    main_prompt = load_markdown_for_prompt("prompts/main-query.md")

    # Model Variable
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "sonnet")
    print(CLAUDE_MODEL)

    options = ClaudeAgentOptions(
        system_prompt="claude_code",
        setting_sources=[
            "project"
        ],  # This tells SDK to look for .claude/settings.json at project root
        cwd=str(
            output_dir
        ),  # Set working directory to output location where files will be created
        add_dirs=[str(airflow_dags_dir)],  # Grant access to airflow DAGs directory
        env={
            # Airflow configuration
            "AIRFLOW_HOME": str(project_root / "airflow"),
            "AIRFLOW__CORE__DAGS_FOLDER": str(airflow_dags_dir),
            "FLASK_ENV": "development",
            "FLASK_PROJECT_PATH": str(output_dir),
            # Python configuration
            "PYTHONPATH": "/home/dev/.pyenv/versions/3.13.5/bin/python3",
        },
        agents={
            "app-architect": AgentDefinition(
                description="Expert Web App architect.",
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

    def signal_handler(signum, frame):
        print("\n\nReceived interrupt signal. Shutting down...")
        session.should_exit = True
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        asyncio.run(session.start())
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
    finally:
        sys.exit(0)
