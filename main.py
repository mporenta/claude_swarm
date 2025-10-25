#!/usr/bin/env python3
"""
Claude Swarm - Multi-Agent Orchestration System

Main entry point for the orchestrator application.

Usage:
    python main.py --config yaml_files/airflow_agent_options.yaml
    python main.py --config yaml_files/flask_agent_options.yaml
    python main.py  # Interactive mode
"""

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()
import json
import threading
import signal
import os
import argparse  # noqa: E402
import asyncio  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

from rich.console import Console  # noqa: E402

from src.orchestrator import (  # noqa: E402
    SwarmOrchestrator,
    interactive_config_selection,
)
from util.log_set import logger, log_config  # noqa: E402

log_config.setup()
console = Console()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Claude Swarm Multi-Agent Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use specific configuration
  python main.py --config yaml_files/airflow_agent_options.yaml

  # Interactive mode (select from available configs)
  python main.py

  # Specify custom context variables
  python main.py --config config.yaml --context '{"project": "/path/to/project"}'

  # Provide task description directly
  python main.py --config config.yaml --task "Create a Flask REST API"
        """,
    )

    parser.add_argument(
        "--config", "-c", type=str, help="Path to YAML configuration file"
    )

    parser.add_argument(
        "--context",
        type=str,
        help="JSON string with context variables for YAML substitution",
    )

    parser.add_argument(
        "--task", "-t", type=str, help="Task description (overrides interactive prompt)"
    )

    parser.add_argument(
        "--version", "-v", action="version", version="Claude Swarm 1.0.0"
    )

    return parser.parse_args()


def get_config_path(args: argparse.Namespace) -> Path:
    """
    Get configuration file path.

    Args:
        args: Parsed command-line arguments

    Returns:
        Path to configuration file

    Raises:
        SystemExit: If config file not found
    """
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            console.print(f"[red]❌ Configuration file not found: {config_path}[/red]")
            sys.exit(1)
        return config_path
    else:
        # Interactive selection
        config_dir = Path(__file__).resolve().parent / "yaml_files"
        return interactive_config_selection(config_dir)


def build_context(args: argparse.Namespace) -> dict | None:
    """
    Build context dictionary from command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Context dictionary or None

    Raises:
        SystemExit: If JSON parsing fails
    """
    if not args.context:
        return None


    try:
        return json.loads(args.context)
    except json.JSONDecodeError as e:
        console.print(f"[red]❌ Invalid JSON in --context: {e}[/red]")
        sys.exit(1)


async def main_async():
    """Async main function."""
    # Parse arguments
    args = parse_arguments()
    logger.debug(f"Arguments parsed: {args}")

    # Get configuration path
    config_path = get_config_path(args)
    logger.debug(f"Configuration path: {config_path}")

    # Build context
    context = build_context(args)
    logger.debug(f"Context built: {context}")

    try:
        # Initialize orchestrator
        logger.debug(f"Initializing orchestrator with config: {config_path}")
        orchestrator = SwarmOrchestrator(config_path=config_path, context=context)
        logger.debug(f"Orchestrator initialized successfully with object: {orchestrator}")

        # Run orchestration
        await orchestrator.run_orchestration(main_prompt=args.task)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user. Exiting...[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"\n[red]❌ Fatal error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user. Exiting...[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import time
    claude_connection = None
    
    args = parse_arguments()
    logger.debug(f"Arguments parsed: {args}")

    # Get configuration path
    config_path = get_config_path(args)
    logger.debug(f"Configuration path: {config_path}")

    # Build context
    context = build_context(args)
    logger.debug(f"Context built: {context}")
    

    try:
        # Initialize orchestrator
        logger.debug(f"Initializing orchestrator with config: {config_path}")
        orchestrator = SwarmOrchestrator(config_path=config_path, context=context)
        logger.debug(f"Orchestrator initialized successfully with object: {orchestrator}")
        if orchestrator.client:
            claude_connection = orchestrator.client

        # Run orchestration
        asyncio.run(orchestrator.run_orchestration(main_prompt=args.task))

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user. Exiting...[/yellow]")
        asyncio.run(orchestrator._disconnect_from_claude("main KeyboardInterrupt"))
        time.sleep(1)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"\n[red]❌ Fatal error: {e}[/red]")
        sys.exit(1)
    def force_exit():
        logger.warning("Forcing application exit after timeout")
        # Use os._exit instead of sys.exit to force termination
        os._exit(0)

    # Add signal handlers that include a force-exit failsafe 
    def handle_exit(sig, frame):
        logger.info(f"Received signal {sig} - initiating graceful shutdown")
        asyncio.run(orchestrator._disconnect_from_claude("handle_exit"))

        # Set a timeout to force exit if needed
        timer = threading.Timer(1.0, force_exit)
        timer.daemon = True  # Make sure the timer doesn't prevent exit
        timer.start()

        # Let the normal shutdown process continue 

    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)