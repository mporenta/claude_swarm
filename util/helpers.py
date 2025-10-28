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

from util.log_set import logger, log_config  # noqa: E402

LOG_LEVEL = log_config.log_level if log_config else "DEBUG"
print(f"[dim]Helper LOG_LEVEL: {LOG_LEVEL}[/dim]")


def debug_log(message: str):
    """
    Log debug messages to file only.

    Args:
        message: Debug message to log
    """
    if LOG_LEVEL == "DEBUG":
        write_to_file(f"raw message: {log_config.today_str()}: {message}")


async def display_message(
    msg, debug_mode: str = LOG_LEVEL, iteration: int = None, print_raw: bool = False
):
    """
    Claude SDK standardized message display function with status indicators.

    Args:
        msg: Message object to display (can be string or SDK message type)
        debug_mode: Debug level (defaults to LOG_LEVEL)
        iteration: Optional iteration number for tracking orchestration loops
        print_raw: If True, print raw message without formatting
    """
    try:

        console = Console()

        if debug_mode:
            if print_raw:
                debug_log(msg)
                return
            if isinstance(msg, str):
                debug_log(msg)
                console.print(msg)
                return

        # UserMessage handling
        if isinstance(msg, UserMessage):
            debug_log(
                f"User Message: {msg} msg_model {msg.model if hasattr(msg, 'model') else 'N/A'}"
            )

            for block in msg.content:
                if isinstance(block, TextBlock):
                    console.print(
                        f"[cyan]🧑 [{log_config.today_str()}] User:[/cyan] {block.text}"
                    )
                    if debug_mode:
                        console.print(
                            f"[dim]   Character count: {len(block.text)}[/dim]"
                        )

        # AssistantMessage handling
        elif isinstance(msg, AssistantMessage):
            debug_log(
                f"Assistant Message: {msg} msg_model {msg.model if hasattr(msg, 'model') else 'N/A'}"
            )
            logger.info(
                f"AssistantMessage model: {str(msg).replace('<', '\\<').replace('>', '\\>').replace('{', '{{').replace('}', '}}')}"
            )

            # Show model info if available
            if debug_mode and hasattr(msg, "model") and msg.model:
                console.print(f"[dim]🤖 Model: {msg.model}[/dim]")

            # Show if this is a subagent response (has parent_tool_use_id)
            if (
                debug_mode
                and hasattr(msg, "parent_tool_use_id")
                and msg.parent_tool_use_id
            ):
                debug_log(
                    f"Subagent response (parent_tool_use_id: {msg.parent_tool_use_id})"
                )
                console.print("[dim]🔗 Subagent Response[/dim]")

            for block_idx, block in enumerate(msg.content, 1):
                if isinstance(block, TextBlock):
                    console.print(
                        f"[green]🤖 [{log_config.today_str()}] Claude:[/green] {block.text}"
                    )
                    if debug_mode:
                        debug_log(
                            f"[dim]   Block msg.content: {block_idx}/{msg.content} | "
                            f"block.text: {block.text}"
                        )
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Length: {len(block.text)} chars[/dim]"
                        )

                elif isinstance(block, ThinkingBlock):
                    thinking_preview = block.thinking[:300]
                    console.print(
                        f"[yellow]💭 [{log_config.today_str()}] Thinking:[/yellow] "
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
                        f"[magenta]⚙️  [{log_config.today_str()}] Tool Use:[/magenta] {block.name}"
                    )
                    input_preview = str(block.input)[:300]
                    console.print(f"   Input: {input_preview}...")

                    if debug_mode:
                        debug_log(
                            f"ToolUseBlock: block_idx: {block_idx} / Tool: {block.name} / ID: {block.id}"
                        )
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Tool ID: {block.id}[/dim]"
                        )
                        # Show full input in debug mode
                        if len(str(block.input)) > 300:
                            console.print(f"[dim]   Full input: {block.input}[/dim]")

                elif isinstance(block, ToolResultBlock):
                    result_preview = (
                        str(block.content)[:300] if block.content else "No content"
                    )
                    status_icon = "❌" if block.is_error else "✅"

                    console.print(
                        f"[blue]{status_icon} [{log_config.today_str()}] Tool Result:[/blue] {result_preview}..."
                    )
                    if debug_mode:
                        debug_log(
                            f"ToolResultBlock: block_idx: {block_idx} / tool_use_id: {block.tool_use_id} / is_error: {block.is_error}"
                        )
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Tool Use ID: {block.tool_use_id} | "
                            f"Error: {block.is_error}[/dim]"
                        )
                        if block.content and len(str(block.content)) > 300:
                            console.print(f"[dim]   Full result: {block.content}[/dim]")

        # SystemMessage handling
        elif isinstance(msg, SystemMessage):
            if debug_mode:
                console.print(
                    f"[dim]ℹ️  [{log_config.today_str()}] System Message[/dim]"
                )
                # SystemMessage has 'data' attribute, not 'content'
                if hasattr(msg, "data") and isinstance(msg.data, dict):
                    console.print(
                        f"[dim]   Subtype: {msg.data.get('subtype', 'N/A')}[/dim]"
                    )
                    if "session_id" in msg.data:
                        console.print(
                            f"[dim]   Session ID: {msg.data['session_id']}[/dim]"
                        )
                    if "cwd" in msg.data:
                        console.print(
                            f"[dim]   Working Directory: {msg.data['cwd']}[/dim]"
                        )
                    if "model" in msg.data:
                        console.print(f"[dim]   Model: {msg.data['model']}[/dim]")
                    if "agents" in msg.data:
                        agents_list = ", ".join(msg.data["agents"])
                        console.print(f"[dim]   Available Agents: {agents_list}[/dim]")
                    if "tools" in msg.data:
                        tool_count = len(msg.data["tools"])
                        console.print(
                            f"[dim]   Available Tools: {tool_count} tools[/dim]"
                        )

        # ResultMessage handling with detailed metrics
        elif isinstance(msg, ResultMessage):
            console.print(
                f"[bold green]✅ [{log_config.today_str()}] Result Message Received[/bold green]"
            )

            # Cost information
            cost = 0.0
            if msg.total_cost_usd:
                cost = float(msg.total_cost_usd)
                if cost > 0:
                    console.print(
                        f"[bold yellow]💰 Total Cost: ${cost:.6f}[/bold yellow]"
                    )

            # Token usage information
            if msg.usage and isinstance(msg.usage, dict):
                console.print("[bold cyan]📊 Token Usage Details:[/bold cyan]")
                if "input_tokens" in msg.usage and msg.usage["input_tokens"]:
                    console.print(f"   • Input tokens: {msg.usage['input_tokens']:,}")
                if "output_tokens" in msg.usage and msg.usage["output_tokens"]:
                    console.print(f"   • Output tokens: {msg.usage['output_tokens']:,}")
                if (
                    "cache_read_input_tokens" in msg.usage
                    and msg.usage["cache_read_input_tokens"]
                ):
                    console.print(
                        f"   • Cache read tokens: "
                        f"{msg.usage['cache_read_input_tokens']:,}"
                    )
                if (
                    "cache_creation_input_tokens" in msg.usage
                    and msg.usage["cache_creation_input_tokens"]
                ):
                    console.print(
                        f"   • Cache creation tokens: "
                        f"{msg.usage['cache_creation_input_tokens']:,}"
                    )

            # Additional debug info
            if debug_mode:
                console.print("[dim]🔍 Result Message Details:[/dim]")
                if hasattr(msg, "subtype") and msg.subtype:
                    console.print(f"[dim]   Subtype: {msg.subtype}[/dim]")
                if hasattr(msg, "num_turns") and msg.num_turns:
                    console.print(f"[dim]   Number of turns: {msg.num_turns}[/dim]")
                if hasattr(msg, "session_id") and msg.session_id:
                    console.print(f"[dim]   Session ID: {msg.session_id}[/dim]")
                if hasattr(msg, "duration_ms") and msg.duration_ms:
                    console.print(f"[dim]   Duration: {msg.duration_ms}ms[/dim]")
                # Check if stop_reason is in usage dict
                if (
                    msg.usage
                    and isinstance(msg.usage, dict)
                    and "stop_reason" in msg.usage
                ):
                    console.print(
                        f"[dim]   Stop reason: {msg.usage['stop_reason']}[/dim]"
                    )

        # Unknown message type - just print it
        else:
            console.print(msg)
            if debug_mode:
                console.print(f"[dim]⚠️  Unknown message type: {type(msg)}[/dim]")

    except Exception as e:
        logger.error(f"Error displaying message: {e}", exc_info=True)
        print(f"Error displaying message: {e}")

def display_message(
    msg, debug_mode: str = LOG_LEVEL, iteration: int = None, print_raw: bool = False
):
    """
    Claude SDK standardized message display function with status indicators.

    Args:
        msg: Message object to display (can be string or SDK message type)
        debug_mode: Debug level (defaults to LOG_LEVEL)
        iteration: Optional iteration number for tracking orchestration loops
        print_raw: If True, print raw message without formatting
    """
    try:

        console = Console()

        if debug_mode:
            if print_raw:
                debug_log(msg)
                return
            if isinstance(msg, str):
                debug_log(msg)
                console.print(msg)
                return

        # UserMessage handling
        if isinstance(msg, UserMessage):
            debug_log(
                f"User Message: {msg} msg_model {msg.model if hasattr(msg, 'model') else 'N/A'}"
            )

            for block in msg.content:
                if isinstance(block, TextBlock):
                    console.print(
                        f"[cyan]🧑 [{log_config.today_str()}] User:[/cyan] {block.text}"
                    )
                    if debug_mode:
                        console.print(
                            f"[dim]   Character count: {len(block.text)}[/dim]"
                        )

        # AssistantMessage handling
        elif isinstance(msg, AssistantMessage):
            debug_log(
                f"Assistant Message: {msg} msg_model {msg.model if hasattr(msg, 'model') else 'N/A'}"
            )
            logger.info(
                f"AssistantMessage model: {str(msg).replace('<', '\\<').replace('>', '\\>').replace('{', '{{').replace('}', '}}')}"
            )

            # Show model info if available
            if debug_mode and hasattr(msg, "model") and msg.model:
                console.print(f"[dim]🤖 Model: {msg.model}[/dim]")

            # Show if this is a subagent response (has parent_tool_use_id)
            if (
                debug_mode
                and hasattr(msg, "parent_tool_use_id")
                and msg.parent_tool_use_id
            ):
                debug_log(
                    f"Subagent response (parent_tool_use_id: {msg.parent_tool_use_id})"
                )
                console.print("[dim]🔗 Subagent Response[/dim]")

            for block_idx, block in enumerate(msg.content, 1):
                if isinstance(block, TextBlock):
                    console.print(
                        f"[green]🤖 [{log_config.today_str()}] Claude:[/green] {block.text}"
                    )
                    if debug_mode:
                        debug_log(
                            f"[dim]   Block msg.content: {block_idx}/{msg.content} | "
                            f"block.text: {block.text}"
                        )
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Length: {len(block.text)} chars[/dim]"
                        )

                elif isinstance(block, ThinkingBlock):
                    thinking_preview = block.thinking[:300]
                    console.print(
                        f"[yellow]💭 [{log_config.today_str()}] Thinking:[/yellow] "
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
                        f"[magenta]⚙️  [{log_config.today_str()}] Tool Use:[/magenta] {block.name}"
                    )
                    input_preview = str(block.input)[:300]
                    console.print(f"   Input: {input_preview}...")

                    if debug_mode:
                        debug_log(
                            f"ToolUseBlock: block_idx: {block_idx} / Tool: {block.name} / ID: {block.id}"
                        )
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Tool ID: {block.id}[/dim]"
                        )
                        # Show full input in debug mode
                        if len(str(block.input)) > 300:
                            console.print(f"[dim]   Full input: {block.input}[/dim]")

                elif isinstance(block, ToolResultBlock):
                    result_preview = (
                        str(block.content)[:300] if block.content else "No content"
                    )
                    status_icon = "❌" if block.is_error else "✅"

                    console.print(
                        f"[blue]{status_icon} [{log_config.today_str()}] Tool Result:[/blue] {result_preview}..."
                    )
                    if debug_mode:
                        debug_log(
                            f"ToolResultBlock: block_idx: {block_idx} / tool_use_id: {block.tool_use_id} / is_error: {block.is_error}"
                        )
                        console.print(
                            f"[dim]   Block {block_idx}/{len(msg.content)} | "
                            f"Tool Use ID: {block.tool_use_id} | "
                            f"Error: {block.is_error}[/dim]"
                        )
                        if block.content and len(str(block.content)) > 300:
                            console.print(f"[dim]   Full result: {block.content}[/dim]")

        # SystemMessage handling
        elif isinstance(msg, SystemMessage):
            if debug_mode:
                console.print(
                    f"[dim]ℹ️  [{log_config.today_str()}] System Message[/dim]"
                )
                # SystemMessage has 'data' attribute, not 'content'
                if hasattr(msg, "data") and isinstance(msg.data, dict):
                    console.print(
                        f"[dim]   Subtype: {msg.data.get('subtype', 'N/A')}[/dim]"
                    )
                    if "session_id" in msg.data:
                        console.print(
                            f"[dim]   Session ID: {msg.data['session_id']}[/dim]"
                        )
                    if "cwd" in msg.data:
                        console.print(
                            f"[dim]   Working Directory: {msg.data['cwd']}[/dim]"
                        )
                    if "model" in msg.data:
                        console.print(f"[dim]   Model: {msg.data['model']}[/dim]")
                    if "agents" in msg.data:
                        agents_list = ", ".join(msg.data["agents"])
                        console.print(f"[dim]   Available Agents: {agents_list}[/dim]")
                    if "tools" in msg.data:
                        tool_count = len(msg.data["tools"])
                        console.print(
                            f"[dim]   Available Tools: {tool_count} tools[/dim]"
                        )

        # ResultMessage handling with detailed metrics
        elif isinstance(msg, ResultMessage):
            console.print(
                f"[bold green]✅ [{log_config.today_str()}] Result Message Received[/bold green]"
            )

            # Cost information
            cost = 0.0
            if msg.total_cost_usd:
                cost = float(msg.total_cost_usd)
                if cost > 0:
                    console.print(
                        f"[bold yellow]💰 Total Cost: ${cost:.6f}[/bold yellow]"
                    )

            # Token usage information
            if msg.usage and isinstance(msg.usage, dict):
                console.print("[bold cyan]📊 Token Usage Details:[/bold cyan]")
                if "input_tokens" in msg.usage and msg.usage["input_tokens"]:
                    console.print(f"   • Input tokens: {msg.usage['input_tokens']:,}")
                if "output_tokens" in msg.usage and msg.usage["output_tokens"]:
                    console.print(f"   • Output tokens: {msg.usage['output_tokens']:,}")
                if (
                    "cache_read_input_tokens" in msg.usage
                    and msg.usage["cache_read_input_tokens"]
                ):
                    console.print(
                        f"   • Cache read tokens: "
                        f"{msg.usage['cache_read_input_tokens']:,}"
                    )
                if (
                    "cache_creation_input_tokens" in msg.usage
                    and msg.usage["cache_creation_input_tokens"]
                ):
                    console.print(
                        f"   • Cache creation tokens: "
                        f"{msg.usage['cache_creation_input_tokens']:,}"
                    )

            # Additional debug info
            if debug_mode:
                console.print("[dim]🔍 Result Message Details:[/dim]")
                if hasattr(msg, "subtype") and msg.subtype:
                    console.print(f"[dim]   Subtype: {msg.subtype}[/dim]")
                if hasattr(msg, "num_turns") and msg.num_turns:
                    console.print(f"[dim]   Number of turns: {msg.num_turns}[/dim]")
                if hasattr(msg, "session_id") and msg.session_id:
                    console.print(f"[dim]   Session ID: {msg.session_id}[/dim]")
                if hasattr(msg, "duration_ms") and msg.duration_ms:
                    console.print(f"[dim]   Duration: {msg.duration_ms}ms[/dim]")
                # Check if stop_reason is in usage dict
                if (
                    msg.usage
                    and isinstance(msg.usage, dict)
                    and "stop_reason" in msg.usage
                ):
                    console.print(
                        f"[dim]   Stop reason: {msg.usage['stop_reason']}[/dim]"
                    )

        # Unknown message type - just print it
        else:
            console.print(msg)
            if debug_mode:
                console.print(f"[dim]⚠️  Unknown message type: {type(msg)}[/dim]")

    except Exception as e:
        logger.error(f"Error displaying message: {e}", exc_info=True)
        print(f"Error displaying message: {e}")
def file_path_creator(path_input: str) -> str:
    """
    Resolve a file or directory path to an absolute path string.

    Handles both absolute and relative paths. For relative paths, tries multiple
    possible root locations to find the file/directory.

    Args:
        path_input (str): Path to resolve (absolute or relative).

    Returns:
        str: Full absolute path as a string.

    Raises:
        FileNotFoundError: If the path cannot be found in any search location.
    """
    try:
        # If already absolute and exists, return it
        input_path = Path(path_input).expanduser()
        if input_path.is_absolute():
            if input_path.exists():
                return str(input_path.resolve())
            else:
                raise FileNotFoundError(
                    f"Absolute path does not exist: {input_path}\n"
                    f"Please verify the path is correct."
                )

        # For relative paths, try multiple possible root locations
        def find_project_root(start: Path) -> Path:
            """Find project root by looking for marker files."""
            markers = {"pyproject.toml", "requirements.txt", ".git", ".gitignore"}
            for parent in [start] + list(start.parents):
                if any((parent / marker).exists() for marker in markers):
                    return parent
            return start

        # Define search locations in priority order
        script_dir = Path(__file__).resolve().parent
        project_root = find_project_root(script_dir)
        parent_root = project_root.parent
        current_dir = Path.cwd()

        search_roots = [
            current_dir,  # Current working directory
            parent_root,  # Parent of project root (for sibling dirs like airflow/)
            project_root,  # Project root itself
            script_dir,  # Script directory
        ]

        # Try each search root
        for root in search_roots:
            candidate = root / path_input
            if candidate.exists():
                resolved = candidate.resolve()
                logger.debug(
                    f"Resolved '{path_input}' to '{resolved}' via root '{root}'"
                )
                return str(resolved)

        # If not found anywhere, provide helpful error message
        tried_paths = [str(root / path_input) for root in search_roots]
        raise FileNotFoundError(
            f"Could not find path: '{path_input}'\n"
            f"Searched in the following locations:\n"
            + "\n".join(f"  - {p}" for p in tried_paths)
            + f"\n\nTip: Use absolute path or verify the relative path is correct."
        )

    except FileNotFoundError:
        raise  # Re-raise FileNotFoundError as-is
    except Exception as e:
        logger.error(f"Error resolving path '{path_input}': {e}", exc_info=True)
        raise RuntimeError(f"Error resolving path '{path_input}': {e}") from e


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


def write_to_file(msg):
    """
    Write a message to a log file in the project's logs directory using today's date in the filename.

    Args:
        msg: Message to write to the log file (can be string or any object with string representation)
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
        logs_dir = project_root / "logs"

        # Create logs directory if it doesn't exist
        logs_dir.mkdir(exist_ok=True)

        # Create filename with today's date
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = logs_dir / f"{today}_log_to_file.log"

        # Convert message to string if it's not already
        message_str = str(msg)

        # Write message to file with log_config.today_str()

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{log_config.today_str()}] {message_str}\n")

        logger.debug(f"Message written to {log_file}")

    except Exception as e:
        logger.error(f"Error writing message to file: {e}", exc_info=True)
        print(f"Error writing message to file: {e}")
