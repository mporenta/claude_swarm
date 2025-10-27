"""
Claude Swarm Orchestrator

Core orchestration logic for coordinating specialized AI agents.
"""

import os
import signal
import sys
import time
import asyncio
import yaml
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ThinkingBlock,
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError
)

from src.config_loader import load_agent_options_from_yaml
from util.helpers import load_markdown_for_prompt, display_message, debug_log
from util.log_set import logger
from util.agent_loader import discover_agents

console = Console()


class SwarmOrchestrator:
    """
    Generalist orchestrator that coordinates specialized AI agents.

    Configuration is loaded from YAML files which define:
    - System prompts and main task prompts
    - Specialized agents with their roles and tools
    - Working directories and environment variables
    - Allowed tools and permission modes
    """

    def __init__(
        self,
        config_path: str | Path,
        context: Optional[dict] = None

    ):
        """
        Initialize orchestrator with configuration from YAML.

        Args:
            config_path: Path to YAML configuration file
            context: Optional context dict for YAML variable substitution
        """
        self.config_path = Path(config_path)
        self.context = context or self._build_default_context()
        self.options: ClaudeAgentOptions = None
        self.client:ClaudeSDKClient = None
        self.should_exit = False
        self.main_prompt_file = None  # Will be loaded from YAML config

        # Load configuration
        loaded_config = self._load_configuration()
        display_message(loaded_config, print_raw=True)

        # Initialize client
        #self.client = ClaudeSDKClient(self.options)

    async def _disconnect_from_claude(self, function_name: str =""):
        try:
            console.print(f"[yellow] ClaudeSDKClient Cleanup initiated by {function_name} [/yellow]")
            
            
            await self.client.disconnect()
            await asyncio.sleep(0.2)  # Yield control to event loop
            
              # Yield control to event loop
            console.print(f"[yellow] self.client status {self.client} [/yellow]")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")








    def _build_default_context(self) -> dict:
        """
        Build default context for YAML variable substitution.

        Supports environment variables for flexible path configuration
        across different machines (local, AWS Bedrock, CI/CD).

        Priority: Environment Variables > Defaults
        """
        project_root = Path(__file__).resolve().parent.parent

        # Airflow 2.0 paths (check env vars first)
        airflow_2_root = Path(os.getenv(
            "AIRFLOW_2_ROOT",
            project_root / "airflow" / "data-airflow"
        ))
        airflow_2_dags_dir = Path(os.getenv(
            "AIRFLOW_2_DAGS_DIR",
            airflow_2_root / "dags"
        ))

        # Airflow Legacy paths (check env vars first)
        airflow_legacy_root = Path(os.getenv(
            "AIRFLOW_LEGACY_ROOT",
            project_root / "airflow" / "data-airflow-legacy"
        ))
        airflow_legacy_dags_dir = Path(os.getenv(
            "AIRFLOW_LEGACY_DAGS_DIR",
            airflow_legacy_root / "dags"
        ))

        # Airflow home directory
        airflow_home = Path(os.getenv(
            "AIRFLOW_HOME",
            airflow_2_root
        ))

        # Python path for Airflow imports
        pythonpath = os.getenv(
            "PYTHONPATH",
            "/opt/airflow/dags"
        )

        return {
            # Claude Swarm project paths
            "project_root": project_root,
            "output_dir": project_root / "generated_code",

            # Airflow 2.0 paths
            "AIRFLOW_2_ROOT": airflow_2_root,
            "AIRFLOW_2_DAGS_DIR": airflow_2_dags_dir,
            "airflow_2_dags_dir": airflow_2_dags_dir,  # backward compat

            # Airflow Legacy paths
            "AIRFLOW_LEGACY_ROOT": airflow_legacy_root,
            "AIRFLOW_LEGACY_DAGS_DIR": airflow_legacy_dags_dir,
            "airflow_legacy_dags_dir": airflow_legacy_dags_dir,  # backward compat

            # Airflow configuration
            "AIRFLOW_HOME": airflow_home,
            "PYTHONPATH": pythonpath,

            # Model configuration
            "CLAUDE_MODEL": os.getenv("CLAUDE_MODEL", "sonnet"),
        }

    def _load_configuration(self):
        """Load ClaudeAgentOptions from YAML configuration file."""
        try:
            # First, load raw YAML to extract main_prompt_file
            with open(self.config_path, 'r', encoding='utf-8') as fh:
                raw_config = yaml.safe_load(fh) or {}

            # Extract main_prompt_file if present
            if "main_prompt_file" in raw_config:
                self.main_prompt_file = raw_config["main_prompt_file"]
                # Apply context substitution to the path
                if self.main_prompt_file:
                    try:
                        # Convert Path objects in context to strings
                        context_for_format = {
                            k: str(v) if isinstance(v, Path) else v
                            for k, v in self.context.items()
                        }
                        self.main_prompt_file = self.main_prompt_file.format(
                            **context_for_format
                        )
                    except KeyError:
                        pass  # Keep original if substitution fails
                logger.debug(f"Found main_prompt_file in YAML: {self.main_prompt_file}")

            # Load the main orchestrator prompt if specified in context
            if "orchestrator_agent" not in self.context:
                # Try to load from default locations
                project_root = Path(__file__).resolve().parent.parent
                prompt_files = [
                    "dag_CLAUDE_v2.md",
                    "flask_CLAUDE.md",
                    "CLAUDE.md"
                ]
                for prompt_file in prompt_files:
                    prompt_path = project_root / prompt_file
                    if prompt_path.exists():
                        self.context["orchestrator_agent"] = (
                            load_markdown_for_prompt(str(prompt_path))
                        )
                        logger.debug(
                            f"Loaded orchestrator prompt from: {prompt_file}"
                        )
                        break

            # Load options from YAML with context
            self.options = load_agent_options_from_yaml(
                self.config_path,
                context=self.context
            )
            logger.debug(f"Loaded agent options from YAML: {self.options}")

            # Discover and merge frontmatter agents from .claude/agents/
            project_root = Path(__file__).resolve().parent.parent
            frontmatter_agents = discover_agents(project_root)

            if frontmatter_agents:
                logger.info(f"Discovered {len(frontmatter_agents)} frontmatter agent(s) from .claude/agents/")

                # Merge frontmatter agents with YAML agents
                # Frontmatter agents have lower priority than YAML config
                for agent_name, agent_def in frontmatter_agents.items():
                    if agent_name not in self.options.agents:
                        self.options.agents[agent_name] = agent_def
                        logger.info(f"Added frontmatter agent: {agent_name}")
                    else:
                        logger.debug(f"Skipped frontmatter agent '{agent_name}' (overridden by YAML config)")

            logger.debug(
                f"Successfully loaded configuration from: "
                f"{self.config_path}"
            )
            logger.debug(
                f"Agents configured: {list(self.options.agents.keys())}"
            )

        except Exception as e:
            logger.error(
                f"Failed to load configuration: {e}",
                exc_info=True
            )
            raise

    async def run_orchestration(self, main_prompt: Optional[str] = None):
        """
        Execute the main orchestration loop.

        Args:
            main_prompt: Optional main task prompt. If not provided, will be loaded
                        from the configuration or prompted from user.
        """
        
        # Display configuration info
        
        

        try:
            self._display_orchestrator_info()
            self.client = ClaudeSDKClient(self.options)
            agent_model = self.options.agents.get("model")
            display_message(f"Using agent model: {agent_model}")

            # Get main prompt if not provided
            logger.debug(f"Main prompt is {main_prompt}")
            if not main_prompt:
                await asyncio.sleep(0.1)  # Yield control to event loop
                main_prompt = self._get_main_prompt()
                #logger.debug(f"User entered task: {main_prompt}")

            # Metrics tracking
            start_time = time.perf_counter()
            iteration_count = 0
            tool_use_count = 0
            thinking_count = 0
            text_block_count = 0
            files_created = []
            iteration_times = []
            iteration_costs = []

            async with self.client:
                # Send initial query
                await self.client.query(prompt=main_prompt)

                display_message(
                    f"\n[bold blue]{'='*60}[/bold blue]\n"
                    f"[bold yellow]🔄 Starting orchestration...[/bold yellow]\n"
                    f"[bold blue]{'='*60}[/bold blue]\n"
                )

                message_count = 0

                # Process responses
                async for message in self.client.receive_response():
                    message_count += 1
                    display_message(message, print_raw=True)


                    iteration_count += 1
                    iteration_start_time = time.perf_counter()

                    # Display iteration header
                    display_message(
                        f"\n[bold magenta]{'─'*60}[/bold magenta]\n"
                        f"[bold cyan]📍 ITERATION {iteration_count} | "
                        f"Type: {message.__class__.__name__}[/bold cyan]\n"
                        f"[bold magenta]{'─'*60}[/bold magenta]"
                    )

                    # Display the message
                    display_message(message, iteration=iteration_count)

                    # Track metrics
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                text_block_count += 1
                            elif isinstance(block, ThinkingBlock):
                                thinking_count += 1
                            elif isinstance(block, ToolUseBlock):
                                tool_use_count += 1
                                if (
                                    block.name == "Write"
                                    and "file_path" in block.input
                                ):
                                    files_created.append(
                                        block.input["file_path"]
                                    )

                    # Calculate iteration timing
                    iteration_end_time = time.perf_counter()
                    iteration_duration = (
                        iteration_end_time - iteration_start_time
                    )
                    iteration_times.append(iteration_duration)

                    display_message(
                        f"[dim]⏱️  Iteration {iteration_count} took: "
                        f"{iteration_duration:.3f}s[/dim]"
                    )

                    # Handle completion
                    if isinstance(message, ResultMessage):
                        cost = float(message.total_cost_usd or 0)
                        iteration_costs.append(cost)

                        self._display_final_metrics(
                            iteration_count=iteration_count,
                            message_count=message_count,
                            start_time=start_time,
                            iteration_times=iteration_times,
                            text_block_count=text_block_count,
                            thinking_count=thinking_count,
                            tool_use_count=tool_use_count,
                            files_created=files_created,
                            cost=cost,
                            message=message,
                        )
                        break

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Orchestration interrupted by user during orchestration[/yellow]")
            await self._disconnect_from_claude("run_orchestration")
        except CLINotFoundError:
            logger.error("Please install Claude Code: npm install -g @anthropic-ai/claude-code")
            raise
        except ProcessError as e:
            logger.error(f"Process failed with exit code: {e.exit_code}")
            raise
        except CLIJSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            raise
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            display_message(f"\n[red]❌ Orchestration failed: {e}[/red]")
            raise 

    def _display_orchestrator_info(self):
        """Display information about the loaded configuration."""
        console.print("\n")
        console.print(
            "[bold magenta]╔══════════════════════════════════════════════════════╗"
            "[/bold magenta]"
        )
        console.print(
            "[bold magenta]║     Claude Swarm Multi-Agent Orchestrator           ║"
            "[/bold magenta]"
        )
        console.print(
            "[bold magenta]╚══════════════════════════════════════════════════════╝"
            "[/bold magenta]\n"
        )

        console.print(f"[dim]Configuration: {self.config_path}[/dim]")
        console.print(f"[dim]Output directory: {self.options.cwd}[/dim]")

        # Display configured agents
        console.print("\n[bold cyan]Configured Agents:[/bold cyan]")
        for agent_name in self.options.agents.keys():
            console.print(f"  • [green]{agent_name}[/green]")

        console.print("")

    def _get_main_prompt(self) -> str:
        """
        Get the main task prompt.

        Checks for main_prompt_file in YAML config first, otherwise prompts user.
        """
        # Check if main_prompt_file was loaded from YAML config
        if self.main_prompt_file:
            prompt_path = Path(self.main_prompt_file)

            if prompt_path.exists():
                logger.info(
                    f"Loading main prompt from YAML config: {self.main_prompt_file}"
                )
                console.print(
                    f"\n[dim]📄 Using prompt from: {prompt_path}[/dim]"
                )
                return load_markdown_for_prompt(str(prompt_path))
            else:
                logger.warning(
                    f"main_prompt_file specified but not found: {prompt_path}"
                )
                console.print(
                    f"[yellow]⚠️  Warning: Prompt file not found: {prompt_path}[/yellow]"
                )

        # Fallback: Check if main_prompt_file is specified in context (legacy)
        if "main_prompt_file" in self.context:
            prompt_path = Path(self.context["main_prompt_file"])

            if prompt_path.exists():
                logger.info(
                    f"Loading main prompt from context: {self.context['main_prompt_file']}"
                )
                return load_markdown_for_prompt(str(prompt_path))

        # Interactive mode - ask user
        console.print("\n[bold yellow]📝 Enter your task description:[/bold yellow]")
        console.print("[dim](Or 'exit' to quit)[/dim]\n")

        task = Prompt.ask("[bold]Task")
        logger.debug(f"User entered task: {task}")

        if task.lower() == "exit":
            sys.exit(0)

        return task

    def _display_final_metrics(
        self,
        iteration_count: int,
        message_count: int,
        start_time: float,
        iteration_times: list,
        text_block_count: int,
        thinking_count: int,
        tool_use_count: int,
        files_created: list,
        cost: float,
        message: ResultMessage,
    ):
        """Display final orchestration metrics."""
        end_time = time.perf_counter()
        total_duration = end_time - start_time
        avg_iteration_time = (
            sum(iteration_times) / len(iteration_times)
            if iteration_times
            else 0
        )

        display_message(
            f"\n[bold green]{'='*60}[/bold green]\n"
            f"[bold green]✅ Orchestration complete![/bold green]\n"
            f"[bold green]{'='*60}[/bold green]\n"
        )

        display_message("\n[bold yellow]📊 ORCHESTRATION METRICS:[/bold yellow]")
        display_message(f"[bold cyan]{'─'*60}[/bold cyan]")

        # Iteration metrics
        display_message("[bold white]Iteration Metrics:[/bold white]")
        display_message(f"   • Total iterations: [bold]{iteration_count}[/bold]")
        display_message(f"   • Total messages: [bold]{message_count}[/bold]")
        display_message(
            f"   • Average time/iteration: "
            f"[bold]{avg_iteration_time:.3f}s[/bold]"
        )
        display_message(
            f"   • Fastest iteration: "
            f"[bold]{min(iteration_times):.3f}s[/bold]"
        )
        display_message(
            f"   • Slowest iteration: "
            f"[bold]{max(iteration_times):.3f}s[/bold]"
        )

        # Content metrics
        display_message("\n[bold white]Content Metrics:[/bold white]")
        display_message(f"   • Text blocks: {text_block_count}")
        display_message(f"   • Thinking blocks: {thinking_count}")
        display_message(f"   • Tool uses: {tool_use_count}")
        display_message(f"   • Files created: {len(files_created)}")

        # Cost metrics
        display_message("\n[bold white]Cost & Time Metrics:[/bold white]")
        if cost > 0:
            display_message(
                f"   • Total cost: [bold yellow]${cost:.6f}[/bold yellow]"
            )
            if iteration_count > 1:
                display_message(
                    f"   • Cost per iteration: "
                    f"[bold]${cost/iteration_count:.6f}[/bold]"
                )
        display_message(
            f"   • Total duration: "
            f"[bold green]{total_duration:.2f}s[/bold green]"
        )

        # Token usage
        display_message("\n[bold white]Token Usage:[/bold white]")
        if hasattr(message, "usage") and message.usage:
            usage = message.usage
            if hasattr(usage, "input_tokens"):
                display_message(f"   • Input tokens: {usage.input_tokens:,}")
            if hasattr(usage, "output_tokens"):
                display_message(f"   • Output tokens: {usage.output_tokens:,}")
            if hasattr(usage, "cache_read_input_tokens"):
                display_message(
                    f"   • Cache read tokens: "
                    f"{usage.cache_read_input_tokens:,}"
                )

        # Files created
        if files_created:
            display_message("\n[bold white]Files Created:[/bold white]")
            for i, file_path in enumerate(files_created, 1):
                display_message(f"   {i}. {file_path}")

        display_message(f"\n[bold cyan]{'─'*60}[/bold cyan]")
        display_message(f"[bold]📁 Output location:[/bold] {self.options.cwd}\n")


def list_available_configs(config_dir: Path) -> list[Path]:
    """List available YAML configuration files."""
    if not config_dir.exists():
        return []

    return sorted(config_dir.glob("*.yaml")) + sorted(config_dir.glob("*.yml"))


def interactive_config_selection(config_dir: Path) -> Path:
    """Let user select a configuration file interactively."""
    configs = list_available_configs(config_dir)

    if not configs:
        console.print("[red]❌ No configuration files found in yaml_files/[/red]")
        sys.exit(1)

    # Display available configurations
    console.print("\n[bold cyan]Available Configurations:[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Configuration", style="green")
    table.add_column("Path", style="dim")

    for i, config_path in enumerate(configs, 1):
        table.add_row(
            str(i),
            config_path.stem,
            str(config_path.relative_to(Path.cwd()))
        )

    console.print(table)
    console.print("")

    # Get user selection
    while True:
        choice = Prompt.ask(
            "[bold]Select configuration number (or 'exit' to quit)[/bold]",
            default="1"
        )

        if choice.lower() == "exit":
            sys.exit(0)

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(configs):
                return configs[idx]
            else:
                console.print(
                    f"[red]Invalid selection. Please choose "
                    f"1-{len(configs)}[/red]"
                )
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")
