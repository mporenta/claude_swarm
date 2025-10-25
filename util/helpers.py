# helpers.py
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from rich import print  # noqa: E402
from rich.console import Console  # noqa: E402
from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ThinkingBlock,
    ToolResultBlock,
    UserMessage,
    SystemMessage,
)
from claude_agent_sdk.types import StreamEvent  # noqa: E402

from util.log_set import logger  # noqa: E402

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
print(f"[dim]Helper LOG_LEVEL: {LOG_LEVEL}[/dim]")


def display_message(msg, debug_mode: str = LOG_LEVEL, iteration: int = None):
    """
    Claude SDK standardized message display function with status indicators.

    Args:
        msg: Message object to display (can be string or SDK message type)
        debug: Debug level (defaults to LOG_LEVEL)
        iteration: Optional iteration number for tracking orchestration loops
    """
    try:

        timestamp = datetime.now().strftime("%H:%M:%S")
        console = Console()

        if debug_mode:
            if isinstance(msg, str):
                logger.debug(f"message log: {msg}")
                console.print(msg)
                return
            if not isinstance(msg, StreamEvent):
                logger.debug(f"message log: {msg}")
                iteration_str = f" [Iteration {iteration}]" if iteration else ""
                console.print(
                    f"[dim]🔍 Debug{iteration_str} | {timestamp} | "
                    f"Type: {msg.__class__.__name__}[/dim]"
                )

        # UserMessage handling
        if isinstance(msg, UserMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    console.print(
                        f"[cyan]🧑 [{timestamp}] User:[/cyan] {block.text}"
                    )
                    if debug_mode:
                        console.print(
                            f"[dim]   Character count: {len(block.text)}[/dim]"
                        )

        # AssistantMessage handling
        elif isinstance(msg, AssistantMessage):
            # Show agent info if available
            if debug_mode and hasattr(msg, 'agent_name'):
                console.print(f"[dim]👤 Agent: {msg.agent_name}[/dim]")

            for block_idx, block in enumerate(msg.content, 1):
                if isinstance(block, TextBlock):
                    console.print(
                        f"[green]🤖 [{timestamp}] Claude:[/green] {block.text}"
                    )
                    if debug_mode:
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Length: {len(block.text)} chars[/dim]"
                        )

                elif isinstance(block, ThinkingBlock):
                    thinking_preview = block.thinking[:300]
                    console.print(
                        f"[yellow]💭 [{timestamp}] Thinking:[/yellow] "
                        f"{thinking_preview}..."
                    )
                    if debug_mode:
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Full length: {len(block.thinking)} chars[/dim]"
                        )
                        # Show full thinking in debug mode
                        if len(block.thinking) > 300:
                            console.print(
                                f"[dim]   Full thinking: {block.thinking}[/dim]"
                            )

                elif isinstance(block, ToolUseBlock):
                    console.print(
                        f"[magenta]⚙️  [{timestamp}] Tool Use:[/magenta] {block.name}"
                    )
                    input_preview = str(block.input)[:300]
                    console.print(f"   Input: {input_preview}...")

                    if debug_mode:
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Tool ID: {getattr(block, 'id', 'N/A')}[/dim]"
                        )
                        # Show full input in debug mode
                        if len(str(block.input)) > 300:
                            console.print(f"[dim]   Full input: {block.input}[/dim]")

                elif isinstance(block, ToolResultBlock):
                    result_preview = (
                        str(block.content)[:300] if block.content else "No content"
                    )
                    console.print(
                        f"[blue]✅ [{timestamp}] Tool Result:[/blue] {result_preview}..."
                    )
                    if debug_mode:
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Tool Use ID: {getattr(block, 'tool_use_id', 'N/A')}[/dim]"
                        )
                        if block.content and len(str(block.content)) > 300:
                            console.print(f"[dim]   Full result: {block.content}[/dim]")

        # SystemMessage handling
        elif isinstance(msg, SystemMessage):
            if debug_mode:
                console.print(
                    f"[dim]ℹ️  [{timestamp}] System Message[/dim]"
                )
                # SystemMessage has 'data' attribute, not 'content'
                if hasattr(msg, 'data') and isinstance(msg.data, dict):
                    console.print(
                        f"[dim]   Subtype: {msg.data.get('subtype', 'N/A')}[/dim]"
                    )
                    if 'session_id' in msg.data:
                        console.print(
                            f"[dim]   Session ID: {msg.data['session_id']}[/dim]"
                        )
                    if 'cwd' in msg.data:
                        console.print(
                            f"[dim]   Working Directory: {msg.data['cwd']}[/dim]"
                        )
                    if 'model' in msg.data:
                        console.print(
                            f"[dim]   Model: {msg.data['model']}[/dim]"
                        )
                    if 'agents' in msg.data:
                        agents_list = ', '.join(msg.data['agents'])
                        console.print(
                            f"[dim]   Available Agents: {agents_list}[/dim]"
                        )
                    if 'tools' in msg.data:
                        tool_count = len(msg.data['tools'])
                        console.print(
                            f"[dim]   Available Tools: {tool_count} tools[/dim]"
                        )

        # ResultMessage handling with detailed metrics
        elif isinstance(msg, ResultMessage):
            console.print(
                f"[bold green]✅ [{timestamp}] "
                "Result Message Received[/bold green]"
            )

            # Cost information
            cost = 0.0
            if msg.total_cost_usd:
                cost = float(msg.total_cost_usd)
                if cost > 0:
                    console.print(
                        f"[bold yellow]💰 Total Cost: ${cost:.6f}"
                        "[/bold yellow]"
                    )

            # Token usage information
            if debug_mode or (
                hasattr(msg, 'input_tokens')
                and hasattr(msg, 'output_tokens')
            ):
                console.print(
                    "[bold cyan]📊 Token Usage Details:[/bold cyan]"
                )
                if hasattr(msg, 'input_tokens') and msg.input_tokens:
                    console.print(
                        f"   • Input tokens: {msg.input_tokens:,}"
                    )
                if hasattr(msg, 'output_tokens') and msg.output_tokens:
                    console.print(
                        f"   • Output tokens: {msg.output_tokens:,}"
                    )
                if (
                    hasattr(msg, 'cache_read_input_tokens')
                    and msg.cache_read_input_tokens
                ):
                    console.print(
                        f"   • Cache read tokens: "
                        f"{msg.cache_read_input_tokens:,}"
                    )
                if (
                    hasattr(msg, 'cache_creation_input_tokens')
                    and msg.cache_creation_input_tokens
                ):
                    console.print(
                        f"   • Cache creation tokens: "
                        f"{msg.cache_creation_input_tokens:,}"
                    )

            # Additional debug info
            if debug_mode:
                console.print("[dim]🔍 Result Message Details:[/dim]")
                if hasattr(msg, 'stop_reason'):
                    console.print(f"[dim]   Stop reason: {msg.stop_reason}[/dim]")
                if hasattr(msg, 'model'):
                    console.print(f"[dim]   Model: {msg.model}[/dim]")

        # StreamEvent handling - log to file only, no console output
        elif isinstance(msg, StreamEvent):
            # Write to log file only
            today_str = datetime.now().strftime("%Y_%m_%d")
            logs_dir = Path(__file__).parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            log_file = logs_dir / f"{today_str}_app.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} | INFO | StreamEvent: {msg}\n")
            return

        # Unknown message type - just print it
        else:
            console.print(msg)
            if debug_mode:
                console.print(f"[dim]⚠️  Unknown message type: {type(msg)}[/dim]")

    except Exception as e:
        logger.error(f"Error displaying message: {e}", exc_info=True)
        print(f"Error displaying message: {e}")


def load_markdown_for_prompt(relative_path: str) -> str:
    """
    Loads a Markdown file relative to the project root, strips YAML front
    matter if present, and returns the content as a clean string ready for
    use in a Claude SDK agent prompt. Automatically detects the project root
    by walking up until a marker file is found.

    Args:
        relative_path (str): Relative path to the markdown file (from project root).

    Returns:
        str: Clean markdown text as a string.
    """
    try:

        # Find project root by walking upward until we find a known marker
        def find_project_root(start: Path) -> Path:
            markers = {"pyproject.toml", "requirements.txt", ".git"}
            for parent in [start] + list(start.parents):
                if any((parent / marker).exists() for marker in markers):
                    return parent
            return start  # fallback to script directory if nothing found

        script_dir = Path(__file__).resolve().parent
        project_root = find_project_root(script_dir)
        file_path = project_root / relative_path

        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        raw_content = file_path.read_text(encoding="utf-8").strip()

        # Strip YAML front matter (--- ... ---)
        yaml_pattern = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
        content = re.sub(yaml_pattern, "", raw_content, count=1).strip()

        return content
    except Exception as e:
        print(f"Error loading markdown for prompt: {e}")
        logger.error(f"Error loading markdown for prompt: {e}", exc_info=True)
        raise RuntimeError(f"Error loading markdown for prompt: {e}") from e
