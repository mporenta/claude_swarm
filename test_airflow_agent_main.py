"""
⚠️  DEPRECATED: This file is deprecated and will be removed in a future version.

Please use the new standardized entry point instead:

    python main.py --config yaml_files/airflow_agent_options.yaml

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


from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ThinkingBlock,
)

from src.agent_options import dag_mirgration_agent, dag_migration_user_prompt
from util.helpers import (
    load_markdown_for_prompt,
    display_message,
    file_path_creator,
    safe_msg,
)
from util.log_set import log_config, logger
from rich import print  # noqa: E402
from rich.console import Console  # noqa: E402


console = Console()
display_message(f"sys.path before modification: {sys.path}")
CLAUDE_LOG_LEVEL = os.getenv("CLAUDE_LOG_LEVEL", "INFO")
joy = os.getenv("JOY")
display_message(f"CLAUDE_LOG_LEVEL: {CLAUDE_LOG_LEVEL} and joy? {joy}")
# Print deprecation warning
display_message("\n[yellow]⚠️  DEPRECATION WARNING:[/yellow]")
display_message("[yellow]This script (airflow_agent_main.py) is deprecated.[/yellow]")
display_message(
    "[yellow]Please use: python main.py --config yaml_files/airflow_agent_options.yaml[/yellow]"
)
display_message("[yellow]See README.md for updated usage instructions.[/yellow]\n")


class ConversationSession:
    """Maintains a single conversation session with Claude."""

    def __init__(
        self,
        project_dir: Path = Path(__file__).resolve().parent,
    ):
        self.options: ClaudeAgentOptions = None
        self.client = ClaudeSDKClient(self.options)
        self._interactive_client = None
        self.user_prompt: str = ""
        self.turn_count = 0
        self.project_dir = project_dir
        self.should_exit = False
        self.legacy_dag_path = None
        print(f"Initialized ConversationSession with project_dir: {self.project_dir}")

    async def validate_bash_command(self, input_data, tool_use_id, context):
        """Block dangerous bash commands before execution."""
        if input_data["tool_name"] != "Bash":
            return {}

        command = input_data["tool_input"].get("command", "")
        dangerous_patterns = [
            "rm -rf",
            "dd if=",
            "mkfs",
            "> /dev/",
            "chmod 777",
            "curl | bash",
            "wget | sh",
        ]

        for pattern in dangerous_patterns:
            if pattern in command:
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"Blocked dangerous pattern: {pattern}",
                    }
                }
        return {}

    async def start(self, message: str = None):
        """Start the conversation session with proper interrupt handling."""
        try:
            logger.info(f"Starting ConversationSession... in {self.project_dir}")
            # Initialize with your specified options
            self.options = ClaudeAgentOptions(
                system_prompt={
                    "type": "preset",
                    "preset": "claude_code",
                },
                max_turns=15,
                model="sonnet",
                setting_sources=["project"],
                cwd=self.project_dir,
                add_dirs=["/Users/mike.porenta/python_dev/aptive_github"],
                # Skills should auto-discover from {cwd}/.claude/skills/
                permission_mode="acceptEdits",
                allowed_tools=[
                    "Skill",
                    "Read",
                    "Write",
                    "Edit",
                    "Bash",
                    "Grep",
                    "Glob",
                ],
            )

            display_message(
                "Starting Airflow agent session. Claude will remember context."
            )
            display_message(f"[dim]Working directory (cwd): {self.project_dir}[/dim]")
            display_message(
                f"[dim]Skills should be in: {self.project_dir}/.claude/skills/[/dim]"
            )

            # If message provided, use non-interactive mode
            if message:
                display_message(f"\n🧑 You: {message}")
                display_message("\n🤖 Claude Agent:")
                try:
                    # Create a new client instance with options for this session
                    client = ClaudeSDKClient(self.options)
                    async with client:
                        await client.query(message)
                        self.turn_count += 1

                        # Process response
                        display_message(f"\n[Turn {self.turn_count}]")
                        async for msg in client.receive_response():
                            display_message(f"1 boof Received message: {safe_msg(msg)}")
                            # Only display AssistantMessage content (the actual response)
                            if isinstance(msg, AssistantMessage):
                                for block in msg.content:
                                    if isinstance(block, TextBlock):
                                        display_message(f"\n{block.text}\n")
                                    elif isinstance(block, ThinkingBlock):
                                        display_message(
                                            f"\n[dim]💭 Thinking: {block.thinking}[/dim]\n"
                                        )
                                    elif isinstance(block, ToolUseBlock):
                                        display_message(
                                            f"\n[cyan]🔧 Using tool: {block.name}[/cyan]"
                                        )
                            elif hasattr(msg, "subtype") and msg.subtype == "success":
                                display_message(
                                    f"\n✅ Done! (Cost: ${msg.total_cost_usd:.6f})"
                                )

                        display_message("")  # New line after response

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    display_message(f"\nError: {e}")
                    raise
            else:
                # Interactive mode
                display_message(
                    "Commands: 'exit' to quit, 'interrupt' to stop current task, 'new' for new session"
                )

                while True:

                    try:
                        user_input = input("\n🧑 You: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        display_message("\n\nGoodbye!")
                        break

                    if not user_input:
                        continue

                    # Handle special commands
                    if user_input.lower() in ["exit", "quit"]:
                        display_message("\nGoodbye!")
                        break

                    if user_input.lower() == "clear":
                        display_message("\n✨ Conversation cleared. Starting fresh!\n")
                        display_message(
                            "   (Restart the script for a completely fresh session)"
                        )
                        continue

                    display_message("\n🤖 Claude:")
                    try:
                        # Create a new client instance with options for this session
                        if (
                            not hasattr(self, "_interactive_client")
                            or self._interactive_client is None
                        ):
                            print(
                                f"Creating new interactive ClaudeSDKClient...The options are {self.options} and the cwd is {self.project_dir}"
                            )
                            self._interactive_client = ClaudeSDKClient(self.options)
                            await self._interactive_client.__aenter__()

                        await self._interactive_client.query(user_input)
                        self.turn_count += 1

                        # Process response
                        display_message(f"[Turn {self.turn_count}] Claude:")
                        async for (
                            message
                        ) in self._interactive_client.receive_response():
                            if isinstance(message, AssistantMessage):
                                for block in message.content:
                                    if isinstance(block, TextBlock):
                                        print(block.text, end="", flush=True)
                                        display_message(safe_msg(block.text))
                                    elif isinstance(block, ToolUseBlock):
                                        # Show when tools are being used
                                        print(
                                            f"\n🔧 [Using tool: {block.name}]",
                                            flush=True,
                                        )
                                        display_message(safe_msg(block.name))

                            print()  # New line after response

                        display_message("")  # New line after response

                    except KeyboardInterrupt:
                        display_message("\n\nResponse interrupted by user!")
                        logger.error("Response interrupted by user (KeyboardInterrupt)")
                        break
                    except asyncio.CancelledError as e_async:
                        logger.error(f"Task was cancelled. {e_async}")
                        display_message("\n\nTask was cancelled.")
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        display_message(f"\nError: {e}")
                        # Continue the loop to allow recovery

        except KeyboardInterrupt:
            display_message("\n\nSession interrupted by user.")
        except asyncio.CancelledError:
            display_message("\n\nAsync session cancelled.")
        except Exception as e:
            logger.error(f"Unexpected error in session: {e}")
            display_message(f"\nUnexpected error: {e}")
        finally:
            # Always attempt cleanup
            try:
                if (
                    hasattr(self, "_interactive_client")
                    and self._interactive_client is not None
                ):
                    await self._interactive_client.__aexit__(None, None, None)
                else:
                    await self.client.disconnect()
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")

            display_message(f"\nConversation ended after {self.turn_count} turns.")

    async def airflow_app_orchestrator(self, prompt: str):
        """
        Orchestrator that creates a airflow web app with random styling.
        Loads prompts from markdown files via load_markdown_for_prompt().
        """
        try:
            if not prompt:
                logger.error("The prompt was passed to the agent")
                return

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

            display_message(
                "[bold cyan]🚀 Starting airflow app orchestrator with markdown prompts...[/bold cyan]\n"
            )

            # Metrics tracking
            # NOTE: message_count tracks individual messages in the response stream
            # turn_count tracks SDK agentic loop turns (limited by max_turns in ClaudeAgentOptions)
            # These are different: one turn can produce multiple messages (thinking, tool use, text, etc.)
            message_count = 0  # Total messages received (excluding StreamEvents)
            turn_count = (
                0  # Agentic loop cycles (AssistantMessage = Claude's turn response)
            )
            tool_use_count = 0
            thinking_count = 0
            text_block_count = 0
            files_created = []
            message_times = []  # Time per message
            iteration_costs = []

            async with self.client:

                # Use the already-connected client directly (no context manager needed)
                await self.client.query(prompt=prompt)

                display_message(
                    f"[bold blue]{'='*60}[/bold blue]\n"
                    f"[bold yellow]🔄 Starting orchestration...[/bold yellow]\n"
                    f"[bold blue]{'='*60}[/bold blue]\n"
                )
                total_messages = 0  # Includes StreamEvents for display purposes

                async for message in self.client.receive_response():
                    # console.print(f"3  message boof in self.client.receive_response(): {message}")

                    total_messages += 1
                    # Convert message to string and escape special chars for safe logging
                    # Escape curly braces (format placeholders) and angle brackets (color tags)

                    # console.print(safe_msg(message))
                    # Skip StreamEvent messages entirely - they are logged to file only
                    # display_message(message, print_raw=True)

                    message_count += 1
                    message_start_time = time.perf_counter()

                    # Track turn count (each AssistantMessage = one agentic loop turn)
                    if isinstance(message, AssistantMessage):
                        self.turn_count += 1

                        # display_message(message, iteration=self.turn_count)

                    # Display message header
                    display_message(
                        f"\n[bold magenta]{'─'*60}[/bold magenta]\n"
                        f"[bold cyan]📍 MESSAGE {message_count} | Turn {self.turn_count} | "
                        f"Type: {message.__class__.__name__}[/bold cyan]\n"
                        f"[bold magenta]{'─'*60}[/bold magenta]"
                    )

                    # Display the message with debugging context
                    # display_message(message, iteration=message_count)

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
                            f"[bold green]✅ airflow app creation complete![/bold green]\n"
                            f"[bold green]{'='*60}[/bold green]\n"
                        )

                        display_message(
                            f"\n[bold yellow]📊 ORCHESTRATION METRICS:[/bold yellow]"
                        )
                        display_message(f"[bold cyan]{'─'*60}[/bold cyan]")
                        display_message(
                            f"[bold white]Agentic Loop Metrics:[/bold white]"
                        )
                        display_message(
                            f"   • SDK Turns (agentic loops): [bold]{self.turn_count}[/bold] "
                            f"(max_turns={self.options.max_turns if hasattr(self.options, 'max_turns') else 'unlimited'})"
                        )
                        display_message(
                            f"   • Total messages processed: [bold]{message_count}[/bold]"
                        )
                        display_message(
                            f"   • Messages per turn: [bold]{message_count/turn_count if turn_count > 0 else 0:.1f}[/bold]"
                        )

                        display_message(
                            f"\n[bold white]Message Processing Times:[/bold white]"
                        )
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

                        display_message(
                            f"\n[bold white]Cost & Time Metrics:[/bold white]"
                        )
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
                            display_message(
                                f"   • Input tokens: {message.input_tokens:,}"
                            )
                        if hasattr(message, "output_tokens") and message.output_tokens:
                            display_message(
                                f"   • Output tokens: {message.output_tokens:,}"
                            )
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

                        if files_created:
                            display_message("[bold white]Files created:[/bold white]")
                            for i, file in enumerate(files_created, 1):
                                display_message(f"   {i}. {file}")

                        display_message(
                            f"\n[bold green]{'='*60}[/bold green]\n"
                            f"[bold green]⏱️  TOTAL TIME: {total_duration:.2f} seconds[/bold green]\n"
                            f"[bold green]🔄 SDK TURNS: {self.turn_count} | MESSAGES: {message_count}[/bold green]\n"
                            f"[bold green]{'='*60}[/bold green]\n"
                        )

        except Exception as ex:
            display_message(f"[bold red]Error:[/bold red] {ex}")
            logger.error(f"Unhandled exception: {ex}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    try:
        # logging setup
        CLAUDE_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        log_config.setup(CLAUDE_LOG_LEVEL)
        # Script location: /home/dev/claude_swarm/airflow_agent.py
        script_path = Path(__file__).resolve()

        # Project root: /home/dev (where CLAUDE.md is located)
        project_root = script_path.parent.parent  # /home/dev

        # Output directory: Use Linux paths
        output_dir = str(project_root / "airflow" / "data-airflow" / "dags")

        dev_airflow_dir = project_root

        display_message(
            "[bold magenta]╔══════════════════════════════════════════════════════╗[/bold magenta]"
        )
        display_message(
            "[bold magenta]║  Apache Airflow Claude Code Agent Swarm (Markdown Prompts)  ║[/bold magenta]"
        )
        display_message(
            "[bold magenta]╚══════════════════════════════════════════════════════╝[/bold magenta]\n"
        )
        display_message(f"[dim]Project root (CLAUDE.md location): {project_root}[/dim]")
        display_message(f"[dim]Default output directory: {output_dir}[/dim]")
        display_message(f"[dim]Additional access: {dev_airflow_dir}[/dim]\n")

        # Load markdown prompt files \
        airflow_dev_prompt = load_markdown_for_prompt(
            "prompts/airflow_prompts/dag-developer.md"
        )
        migration_specialist = load_markdown_for_prompt(
            "prompts/airflow_prompts/migration-specialist.md"
        )
        code_reviewer_prompt = load_markdown_for_prompt(
            "prompts/airflow_prompts/airflow-code-reviewer.md"
        )
        orchestrator_agent = load_markdown_for_prompt("repo_CLAUDE.md")

        # Model Variable
        CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "sonnet")
        display_message(f"Using CLAUDE_MODEL env: {CLAUDE_MODEL}")

        # Build environment configuration from .env settings with sensible defaults
        default_airflow_root = project_root / "airflow" / "data-airflow"
        default_airflow_dags = default_airflow_root / "dags"
        default_legacy_root = project_root / "airflow" / "data-airflow-legacy"
        default_legacy_dags = default_legacy_root / "dags"

        env_defaults = {
            "AIRFLOW_HOME": str(project_root),
            "AIRFLOW__CORE__DAGS_FOLDER": str(default_airflow_dags),
            "AIRFLOW_2_DAGS_DIR": str(default_airflow_dags),
            "AIRFLOW_2_ROOT": str(default_airflow_root),
            "AIRFLOW_LEGACY_DAGS_DIR": str(default_legacy_dags),
            "AIRFLOW_LEGACY_ROOT": str(default_legacy_root),
        }

        env_config: dict[str, str] = {}
        for key, default_value in env_defaults.items():
            value = os.getenv(key, default_value)
            if value:
                env_config[key] = value

        python_path = os.getenv("PYTHONPATH")
        if python_path:
            env_config["PYTHONPATH"] = python_path

        env_config["PROJECT_ROOT"] = str(project_root)

        add_dirs = [
            path
            for path in [
                env_config.get("AIRFLOW_2_DAGS_DIR"),
                env_config.get("AIRFLOW_LEGACY_DAGS_DIR"),
            ]
            if path
        ]
        add_dirs = list(dict.fromkeys(add_dirs))  # Preserve order, drop duplicates

        # Determine session project directory from environment overrides
        project_dir_env = os.getenv("OUTPUT_DIR")
        if project_dir_env:
            project_dir_path = Path(project_dir_env).resolve()
        else:
            # Use the claude_swarm directory as the working directory
            project_dir_path = Path(__file__).resolve().parent

        display_message(f"[dim]Session project directory: {project_dir_path}[/dim]")
        env_config["OUTPUT_DIR"] = str(project_dir_path)
        config_dir = Path(__file__).resolve().parent

        session = ConversationSession(project_dir=config_dir)

        def signal_handler(signum, frame):
            """Handle interrupt signals gracefully."""
            del signum, frame  # Suppress unused variable warnings
            display_message("\n\nReceived interrupt signal. Shutting down...")
            session.should_exit = True
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Check if message provided via command line
        message = None
        if len(sys.argv) > 1:
            message = " ".join(sys.argv[1:])
            # Override project_dir for command-line mode to use current directory
            session.project_dir = Path.cwd()
            display_message(
                f"[dim]Command-line mode: using {session.project_dir}[/dim]"
            )

        try:
            asyncio.run(session.start(message=message))
        except KeyboardInterrupt:
            display_message("\nInterrupted by user. Exiting...")
        except Exception as e:
            display_message(f"\nUnexpected error: {e}")
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            sys.exit(0)
    except Exception as ex:
        display_message(f"\nFatal error: {ex}")
        logger.error(f"Fatal error: {ex}")
        sys.exit(1)
# /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/cresta_to_snowflake.py
