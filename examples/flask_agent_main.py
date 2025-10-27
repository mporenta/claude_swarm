"""
⚠️  DEPRECATED: This file is deprecated and will be removed in a future version.

Please use the new standardized entry point instead:

    python main.py --config yaml_files/flask_agent_options.yaml

For more information, see:
- README.md (updated usage instructions)
- PROJECT_STRUCTURE.md (new structure documentation)

The new structure provides:
- Standardized Python package layout (main.py → src/)
- YAML-based configuration
- Framework-agnostic orchestration
- Better maintainability

This file will continue to work during the transition period.
"""

from dotenv import load_dotenv

load_dotenv()
import asyncio
import os
import signal
import sys
import time
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

# Print deprecation warning
print("\n[yellow]⚠️  DEPRECATION WARNING:[/yellow]")
print("[yellow]This script (flask_agent_main.py) is deprecated.[/yellow]")
print("[yellow]Please use: python main.py --config yaml_files/flask_agent_options.yaml[/yellow]")
print("[yellow]See README.md for updated usage instructions.[/yellow]\n")


class ConversationSession:
    """Maintains a single conversation session with Claude."""

    def __init__(
        self,
        options: ClaudeAgentOptions = None,
        project_dir: Path = Path(__file__).resolve().parent,
    ):
        self.options = options
        self.client = ClaudeSDKClient(self.options)
        self.turn_count = 0
        self.project_dir = project_dir
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
                except (KeyboardInterrupt, EOFError) as e:
                    logger.error(f"Interrupted by user: {type(e).__name__}")
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
                        # Start fresh session for flask orchestration
                        await self.client.disconnect()
                        await self.client.connect()
                        self.turn_count = 0
                        print("Started new session for Flask orchestration")

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
                    logger.error("Response interrupted by user (KeyboardInterrupt)")
                    break
                except asyncio.CancelledError as e_async:
                    logger.error(f"Task was cancelled. {e_async}")
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
        start_time = time.perf_counter()
        project_path = self.project_dir
        project_path.mkdir(parents=True, exist_ok=True)
        display_message(
            f"[dim]📁 Created project directory at: {project_path.absolute()}[/dim]\n"
        )
        display_message(
            "[dim]💡 Note: Agent will create its own directory structure[/dim]\n"
        )

        # Load markdown prompt files
        main_prompt = load_markdown_for_prompt("prompts/main-query.md")

        display_message(
            "[bold cyan]🚀 Starting Flask app orchestrator with markdown prompts...[/bold cyan]\n"
        )

        # Metrics tracking
        # NOTE: message_count tracks individual messages in the response stream
        # turn_count tracks SDK agentic loop turns (limited by max_turns in ClaudeAgentOptions)
        # These are different: one turn can produce multiple messages (thinking, tool use, text, etc.)
        message_count = 0  # Total messages received (excluding StreamEvents)
        turn_count = 0  # Agentic loop cycles (AssistantMessage = Claude's turn response)
        tool_use_count = 0
        thinking_count = 0
        text_block_count = 0
        files_created = []
        message_times = []  # Time per message
        iteration_costs = []

        async with self.client:

        # Use the already-connected client directly (no context manager needed)
            await self.client.query(prompt=main_prompt)

            display_message(
                f"[bold blue]{'='*60}[/bold blue]\n"
                f"[bold yellow]🔄 Starting orchestration...[/bold yellow]\n"
                f"[bold blue]{'='*60}[/bold blue]\n"
            )
            total_messages = 0  # Includes StreamEvents for display purposes

            async for message in self.client.receive_response():
                total_messages += 1
                # Skip StreamEvent messages entirely - they are logged to file only
                from claude_agent_sdk.types import StreamEvent

                if isinstance(message, StreamEvent):
                    continue

                message_count += 1
                message_start_time = time.perf_counter()

                # Track turn count (each AssistantMessage = one agentic loop turn)
                if isinstance(message, AssistantMessage):
                    turn_count += 1

                # Display message header
                display_message(
                    f"\n[bold magenta]{'─'*60}[/bold magenta]\n"
                    f"[bold cyan]📍 MESSAGE {message_count} | Turn {turn_count} | "
                    f"Type: {message.__class__.__name__}[/bold cyan]\n"
                    f"[bold magenta]{'─'*60}[/bold magenta]"
                )

                # Display the message with debugging context
                display_message(message, iteration=message_count)

                # Track message-specific metrics
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_block_count += 1
                        elif isinstance(block, ThinkingBlock):
                            thinking_count += 1
                        elif isinstance(block, ToolUseBlock):
                            tool_use_count += 1
                            if block.name == "Write" and "file_path" in block.input:
                                files_created.append(block.input["file_path"])

                # Calculate message processing time
                message_end_time = time.perf_counter()
                message_duration = message_end_time - message_start_time
                message_times.append(message_duration)

                # Display message metrics
                display_message(
                    f"[dim]⏱️  Message {message_count} took: {message_duration:.3f}s[/dim]"
                )

                if isinstance(message, ResultMessage):
                    cost = float(message.total_cost_usd or 0)
                    iteration_costs.append(cost)

                    # Calculate final metrics
                    end_time = time.perf_counter()
                    total_duration = end_time - start_time
                    avg_message_time = (
                        sum(message_times) / len(message_times)
                        if message_times
                        else 0
                    )

                    display_message(
                        f"\n[bold green]{'='*60}[/bold green]\n"
                        f"[bold green]✅ Flask app creation complete![/bold green]\n"
                        f"[bold green]{'='*60}[/bold green]\n"
                    )

                    display_message(
                        f"\n[bold yellow]📊 ORCHESTRATION METRICS:[/bold yellow]"
                    )
                    display_message(f"[bold cyan]{'─'*60}[/bold cyan]")
                    display_message(f"[bold white]Agentic Loop Metrics:[/bold white]")
                    display_message(
                        f"   • SDK Turns (agentic loops): [bold]{turn_count}[/bold] "
                        f"(max_turns={self.options.max_turns if hasattr(self.options, 'max_turns') else 'unlimited'})"
                    )
                    display_message(
                        f"   • Total messages processed: [bold]{message_count}[/bold]"
                    )
                    display_message(
                        f"   • Messages per turn: [bold]{message_count/turn_count if turn_count > 0 else 0:.1f}[/bold]"
                    )

                    display_message(f"\n[bold white]Message Processing Times:[/bold white]")
                    display_message(
                        f"   • Average time/message: [bold]{avg_message_time:.3f}s[/bold]"
                    )
                    display_message(
                        f"   • Fastest message: [bold]{min(message_times):.3f}s[/bold]"
                    )
                    display_message(
                        f"   • Slowest message: [bold]{max(message_times):.3f}s[/bold]"
                    )

                    display_message(f"\n[bold white]Content Metrics:[/bold white]")
                    display_message(f"   • Text blocks: {text_block_count}")
                    display_message(f"   • Thinking blocks: {thinking_count}")
                    display_message(f"   • Tool uses: {tool_use_count}")
                    display_message(f"   • Files created: {len(files_created)}")

                    display_message(f"\n[bold white]Cost & Time Metrics:[/bold white]")
                    if cost > 0:
                        display_message(
                            f"   • Total cost: [bold yellow]${cost:.6f}[/bold yellow]"
                        )
                        if turn_count > 0:
                            display_message(
                                f"   • Cost per turn: [bold]${cost/turn_count:.6f}[/bold]"
                            )
                        if message_count > 0:
                            display_message(
                                f"   • Cost per message: [bold]${cost/message_count:.6f}[/bold]"
                            )
                    display_message(
                        f"   • Total duration: [bold green]{total_duration:.2f}s[/bold green]"
                    )

                    display_message(f"\n[bold white]Token Usage:[/bold white]")
                    if hasattr(message, "input_tokens") and message.input_tokens:
                        display_message(f"   • Input tokens: {message.input_tokens:,}")
                    if hasattr(message, "output_tokens") and message.output_tokens:
                        display_message(f"   • Output tokens: {message.output_tokens:,}")
                    if hasattr(message, "input_tokens") and hasattr(
                        message, "output_tokens"
                    ):
                        total_tokens = (message.input_tokens or 0) + (
                            message.output_tokens or 0
                        )
                        if total_tokens > 0:
                            display_message(f"   • Total tokens: {total_tokens:,}")

                    display_message(f"\n[bold cyan]{'─'*60}[/bold cyan]")
                    display_message(
                        f"\n[bold]📁 Project location:[/bold] {project_path.absolute()}"
                    )
                    display_message(f"[bold cyan]🚀 To run your Flask app:[/bold cyan]")
                    display_message(f"   cd {project_path.absolute()}")
                    display_message(f"   pip install -r requirements.txt")
                    display_message(f"   python app.py\n")
                    display_message(f"   Visit: [bold]http://localhost:5010[/bold]\n")

                    if files_created:
                        display_message("[bold white]Files created:[/bold white]")
                        for i, file in enumerate(files_created, 1):
                            display_message(f"   {i}. {file}")

                    display_message(
                        f"\n[bold green]{'='*60}[/bold green]\n"
                        f"[bold green]⏱️  TOTAL TIME: {total_duration:.2f} seconds[/bold green]\n"
                        f"[bold green]🔄 SDK TURNS: {turn_count} | MESSAGES: {message_count}[/bold green]\n"
                        f"[bold green]{'='*60}[/bold green]\n"
                    )


if __name__ == "__main__":
    try:
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

        dev_flask_dir = project_root

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
        display_message(f"[dim]Additional access: {dev_flask_dir}[/dim]\n")

        # Load markdown prompt files
        flask_dev_prompt = load_markdown_for_prompt("prompts/flask-developer.md")
        frontend_dev_prompt = load_markdown_for_prompt("prompts/frontend-developer.md")
        code_reviewer_prompt = load_markdown_for_prompt("prompts/code-reviewer.md")
        main_prompt = load_markdown_for_prompt("prompts/main-query.md")
        orchestrator_agent = load_markdown_for_prompt("flask_CLAUDE.md")

        # Model Variable
        CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "sonnet")
        print(f"Using CLAUDE_MODEL env: {CLAUDE_MODEL}")

        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": orchestrator_agent,
            },
            #max_turns = 5,
        
            model=CLAUDE_MODEL,
            setting_sources=[
                "project"
            ],  # This tells SDK to look for .claude/settings.json at project root
            cwd=str(
                output_dir
            ),  # Set working directory to output location where files will be created
            add_dirs=[str(dev_flask_dir)],  # Grant access to dev flask-s directory
            env={
                # dev configuration
                "dev_HOME": str(project_root / "dev"),
                "dev__CORE__flask-S_FOLDER": str(dev_flask_dir),
                "FLASK_ENV": "development",
                "FLASK_PROJECT_PATH": str(output_dir),
                # Python configuration
                "PYTHONPATH": "/home/dev/.pyenv/versions/3.13.5/lib/python3.13/site-packages",
            },
            agents={
                "flask-developer": AgentDefinition(
                    description="Expert Flask developer.",
                    prompt=flask_dev_prompt,
                    tools=["Read", "Write", "Edit", "Bash"],
                    model="haiku",
                ),
                "frontend-developer": AgentDefinition(
                    description="Expert frontend developer.",
                    prompt=frontend_dev_prompt,
                    tools=["Read", "Write", "Edit"],
                    model="haiku",
                ),
                "code-reviewer": AgentDefinition(
                    description="Code review and best practices specialist.",
                    prompt=code_reviewer_prompt,
                    tools=["Read", "Grep", "Glob", "Bash"],  # Added Bash for flake8 and structure validation
                    model="haiku",
                ),
            },
            allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
            permission_mode="acceptEdits",
        )

        session = ConversationSession(options, project_dir=output_dir)

        def signal_handler(_signum, _frame):
            """Handle interrupt signals gracefully."""
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
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            sys.exit(0)
    except Exception as ex:
        print(f"\nFatal error: {ex}")
        logger.error(f"Fatal error: {ex}")
        sys.exit(1)
