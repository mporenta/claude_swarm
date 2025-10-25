#!/usr/bin/env python3
"""
⚠️  DEPRECATED: This file has been superseded by the new standardized structure.

This file is replaced by:
    main.py (entry point)
    src/orchestrator.py (orchestration logic)
    src/config_loader.py (YAML configuration)

Please use the new entry point:

    python main.py --config yaml_files/airflow_agent_options.yaml
    python main.py --config yaml_files/flask_agent_options.yaml
    python main.py  # Interactive mode

For more information, see:
- README.md (updated usage instructions)
- PROJECT_STRUCTURE.md (new structure documentation)

The new structure follows standard Python best practices with:
- Clear entry point (main.py)
- Core logic in src/ package
- Better organization and maintainability

This file will be removed in a future version.
"""

from dotenv import load_dotenv

load_dotenv()

import argparse
import asyncio
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

from rich import print
from rich.prompt import Prompt
from rich.table import Table
from rich.console import Console

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ThinkingBlock,
)

from util.config_loader import load_agent_options_from_yaml
from util.helpers import load_markdown_for_prompt, display_message
from util.log_set import log_config, logger

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
        context: Optional[dict] = None,
    ):
        """
        Initialize orchestrator with configuration from YAML.

        Args:
            config_path: Path to YAML configuration file
            context: Optional context dict for YAML variable substitution
        """
        self.config_path = Path(config_path)
        self.context = context or self._build_default_context()
        self.options = None
        self.client = None
        self.should_exit = False

        # Load configuration
        self._load_configuration()

        # Initialize client
        self.client = ClaudeSDKClient(self.options)

    def _build_default_context(self) -> dict:
        """Build default context for YAML variable substitution."""
        project_root = Path(__file__).resolve().parent

        return {
            "project_root": project_root,
            "output_dir": project_root / "generated_code",
            "airflow_2_dags_dir": project_root / "airflow" / "data-airflow-2" / "dags",
            "airflow_legacy_dags_dir": project_root / "airflow" / "data-airflow-legacy" / "dags",
            "CLAUDE_MODEL": os.getenv("CLAUDE_MODEL", "sonnet"),
        }

    def _load_configuration(self):
        """Load ClaudeAgentOptions from YAML configuration file."""
        try:
            # Load the main orchestrator prompt if specified in context
            if "orchestrator_agent" not in self.context:
                # Try to load from default locations
                for prompt_file in ["dag_CLAUDE_v2.md", "flask_CLAUDE.md", "CLAUDE.md"]:
                    prompt_path = Path(__file__).resolve().parent / prompt_file
                    if prompt_path.exists():
                        self.context["orchestrator_agent"] = load_markdown_for_prompt(str(prompt_path))
                        logger.info(f"Loaded orchestrator prompt from: {prompt_file}")
                        break

            # Load options from YAML with context
            self.options = load_agent_options_from_yaml(
                self.config_path,
                context=self.context
            )

            logger.info(f"Successfully loaded configuration from: {self.config_path}")
            logger.info(f"Agents configured: {list(self.options.agents.keys())}")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}", exc_info=True)
            raise

    async def run_orchestration(self, main_prompt: Optional[str] = None):
        """
        Execute the main orchestration loop.

        Args:
            main_prompt: Optional main task prompt. If not provided, will be loaded
                        from the configuration or prompted from user.
        """
        # Setup signal handling
        def signal_handler(_signum, _frame):
            """Handle interrupt signals gracefully."""
            console.print("\n\n[yellow]Received interrupt signal. Shutting down...[/yellow]")
            self.should_exit = True
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Display configuration info
        self._display_orchestrator_info()

        # Get main prompt if not provided
        if not main_prompt:
            main_prompt = self._get_main_prompt()

        # Metrics tracking
        start_time = time.perf_counter()
        iteration_count = 0
        tool_use_count = 0
        thinking_count = 0
        text_block_count = 0
        files_created = []
        iteration_times = []
        iteration_costs = []

        try:
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

                    # Skip StreamEvent messages
                    from claude_agent_sdk.types import StreamEvent
                    if isinstance(message, StreamEvent):
                        continue

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
                                if block.name == "Write" and "file_path" in block.input:
                                    files_created.append(block.input["file_path"])

                    # Calculate iteration timing
                    iteration_end_time = time.perf_counter()
                    iteration_duration = iteration_end_time - iteration_start_time
                    iteration_times.append(iteration_duration)

                    display_message(
                        f"[dim]⏱️  Iteration {iteration_count} took: {iteration_duration:.3f}s[/dim]"
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
            console.print("\n\n[yellow]Orchestration interrupted by user![/yellow]")
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            console.print(f"\n[red]❌ Orchestration failed: {e}[/red]")
            raise

    def _display_orchestrator_info(self):
        """Display information about the loaded configuration."""
        console.print("\n")
        console.print("[bold magenta]╔══════════════════════════════════════════════════════╗[/bold magenta]")
        console.print("[bold magenta]║     Claude Swarm Multi-Agent Orchestrator           ║[/bold magenta]")
        console.print("[bold magenta]╚══════════════════════════════════════════════════════╝[/bold magenta]\n")

        console.print(f"[dim]Configuration: {self.config_path}[/dim]")
        console.print(f"[dim]Output directory: {self.options.cwd}[/dim]")

        # Display configured agents
        console.print(f"\n[bold cyan]Configured Agents:[/bold cyan]")
        for agent_name in self.options.agents.keys():
            console.print(f"  • [green]{agent_name}[/green]")

        console.print("")

    def _get_main_prompt(self) -> str:
        """
        Get the main task prompt.

        Checks for main_prompt in YAML config, otherwise prompts user.
        """
        # Check if main_prompt is specified in context
        if "main_prompt_file" in self.context:
            prompt_path = Path(self.context["main_prompt_file"])
            if prompt_path.exists():
                return load_markdown_for_prompt(str(prompt_path))

        # Interactive mode - ask user
        console.print("\n[bold yellow]📝 Enter your task description:[/bold yellow]")
        console.print("[dim](Or 'exit' to quit)[/dim]\n")

        task = Prompt.ask("[bold]Task")

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
        avg_iteration_time = sum(iteration_times) / len(iteration_times) if iteration_times else 0

        display_message(
            f"\n[bold green]{'='*60}[/bold green]\n"
            f"[bold green]✅ Orchestration complete![/bold green]\n"
            f"[bold green]{'='*60}[/bold green]\n"
        )

        display_message(f"\n[bold yellow]📊 ORCHESTRATION METRICS:[/bold yellow]")
        display_message(f"[bold cyan]{'─'*60}[/bold cyan]")

        # Iteration metrics
        display_message(f"[bold white]Iteration Metrics:[/bold white]")
        display_message(f"   • Total iterations: [bold]{iteration_count}[/bold]")
        display_message(f"   • Total messages: [bold]{message_count}[/bold]")
        display_message(f"   • Average time/iteration: [bold]{avg_iteration_time:.3f}s[/bold]")
        display_message(f"   • Fastest iteration: [bold]{min(iteration_times):.3f}s[/bold]")
        display_message(f"   • Slowest iteration: [bold]{max(iteration_times):.3f}s[/bold]")

        # Content metrics
        display_message(f"\n[bold white]Content Metrics:[/bold white]")
        display_message(f"   • Text blocks: {text_block_count}")
        display_message(f"   • Thinking blocks: {thinking_count}")
        display_message(f"   • Tool uses: {tool_use_count}")
        display_message(f"   • Files created: {len(files_created)}")

        # Cost metrics
        display_message(f"\n[bold white]Cost & Time Metrics:[/bold white]")
        if cost > 0:
            display_message(f"   • Total cost: [bold yellow]${cost:.6f}[/bold yellow]")
            if iteration_count > 1:
                display_message(f"   • Cost per iteration: [bold]${cost/iteration_count:.6f}[/bold]")
        display_message(f"   • Total duration: [bold green]{total_duration:.2f}s[/bold green]")

        # Token usage
        display_message(f"\n[bold white]Token Usage:[/bold white]")
        if hasattr(message, "usage") and message.usage:
            usage = message.usage
            if hasattr(usage, "input_tokens"):
                display_message(f"   • Input tokens: {usage.input_tokens:,}")
            if hasattr(usage, "output_tokens"):
                display_message(f"   • Output tokens: {usage.output_tokens:,}")
            if hasattr(usage, "cache_read_input_tokens"):
                display_message(f"   • Cache read tokens: {usage.cache_read_input_tokens:,}")

        # Files created
        if files_created:
            display_message(f"\n[bold white]Files Created:[/bold white]")
            for i, file_path in enumerate(files_created, 1):
                display_message(f"   {i}. {file_path}")

        display_message(f"\n[bold cyan]{'─'*60}[/bold cyan]")
        display_message(f"[bold]📁 Output location:[/bold] {self.options.cwd}\n")


def list_available_configs(config_dir: Path) -> list[Path]:
    """List available YAML configuration files."""
    if not config_dir.exists():
        return []

    return sorted(config_dir.glob("*.yaml")) + sorted(config_dir.glob("*.yml"))


def interactive_config_selection() -> Path:
    """Let user select a configuration file interactively."""
    console = Console()
    config_dir = Path(__file__).resolve().parent / "yaml_files"

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
        table.add_row(str(i), config_path.stem, str(config_path.relative_to(Path.cwd())))

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
                console.print(f"[red]Invalid selection. Please choose 1-{len(configs)}[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")


def main():
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(
        description="Claude Swarm Multi-Agent Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use specific configuration
  python swarm_orchestrator.py --config yaml_files/airflow_agent_options.yaml

  # Interactive mode (select from available configs)
  python swarm_orchestrator.py

  # Specify custom context variables
  python swarm_orchestrator.py --config config.yaml --context '{"project": "/path/to/project"}'
        """
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to YAML configuration file"
    )

    parser.add_argument(
        "--context",
        type=str,
        help="JSON string with context variables for YAML substitution"
    )

    parser.add_argument(
        "--task",
        "-t",
        type=str,
        help="Task description (overrides interactive prompt)"
    )

    args = parser.parse_args()

    # Get config path
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            console.print(f"[red]❌ Configuration file not found: {config_path}[/red]")
            sys.exit(1)
    else:
        # Interactive selection
        config_path = interactive_config_selection()

    # Build context
    context = None
    if args.context:
        import json
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ Invalid JSON in --context: {e}[/red]")
            sys.exit(1)

    try:
        # Initialize orchestrator
        orchestrator = SwarmOrchestrator(
            config_path=config_path,
            context=context
        )

        # Run orchestration
        asyncio.run(orchestrator.run_orchestration(main_prompt=args.task))

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user. Exiting...[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"\n[red]❌ Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
