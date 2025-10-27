# helpers.py
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import sentry_sdk  # noqa: E402
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

from util.log_set import logger, log_config  # noqa: E402

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
print(f"[dim]Helper LOG_LEVEL: {LOG_LEVEL}[/dim]")


def send_to_sentry(message: str):
    """
    Send a message to Sentry as a breadcrumb.

    Args:
        message: Message to send to Sentry
    """
    sentry_sdk.add_breadcrumb(
        category="info",
        message=message[:500],  # Truncate long messages
        level="info",
    )
    sentry_sdk.logger.info(f"Debug log: {message}")


def debug_log(message: str):
    """
    Log debug messages to file and add as Sentry breadcrumb.

    Args:
        message: Debug message to log
    """
    if LOG_LEVEL == "DEBUG":
        log_config.log_to_file_only(message)

        # Add Sentry breadcrumb for debug messages
        sentry_sdk.add_breadcrumb(
            category="debug",
            message=message[:500],  # Truncate long messages
            level="debug",
        )


def display_message(
    msg, debug_mode: str = LOG_LEVEL, iteration: int = None, print_raw: bool = False
):
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

            # Add Sentry breadcrumb for user message
            for block in msg.content:
                if isinstance(block, TextBlock):
                    sentry_sdk.add_breadcrumb(
                        category="user_input",
                        message=block.text[:200],  # Truncate for privacy
                        level="info",
                        data={
                            "length": len(block.text),
                            "model": msg.model if hasattr(msg, "model") else "N/A",
                        },
                    )

                    console.print(f"[cyan]🧑 [{timestamp}] User:[/cyan] {block.text}")
                    if debug_mode:
                        console.print(
                            f"[dim]   Character count: {len(block.text)}[/dim]"
                        )

        # AssistantMessage handling
        elif isinstance(msg, AssistantMessage):
            debug_log(
                f"Assistant Message: {msg} msg_model {msg.model if hasattr(msg, 'model') else 'N/A'}"
            )
            # Show model info if available
            logger.info(f"AssistantMessage model: {msg}")
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
                    # Add Sentry breadcrumb for assistant text response
                    sentry_sdk.add_breadcrumb(
                        category="assistant_response",
                        message=block.text[:200],  # Truncate for brevity
                        level="info",
                        data={
                            "length": len(block.text),
                            "block_index": block_idx,
                            "total_blocks": len(msg.content),
                            "model": msg.model if hasattr(msg, "model") else "N/A",
                        },
                    )

                    console.print(
                        f"[green]🤖 [{timestamp}] Claude:[/green] {block.text}"
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
                    # Add Sentry breadcrumb for thinking
                    sentry_sdk.add_breadcrumb(
                        category="assistant_thinking",
                        message=block.thinking[:200],
                        level="debug",
                        data={"length": len(block.thinking), "block_index": block_idx},
                    )

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
                    # Create Sentry span for tool execution
                    with sentry_sdk.start_span(
                        op="gen_ai.execute_tool", name=f"execute_tool {block.name}"
                    ) as tool_span:
                        tool_span.set_data("gen_ai.operation.name", "execute_tool")
                        tool_span.set_data("tool_name", block.name)
                        tool_span.set_data("tool_id", block.id)
                        tool_span.set_data("block_index", block_idx)

                        # Serialize tool input (truncate if too large)
                        tool_input_str = str(block.input)
                        if len(tool_input_str) > 1000:
                            tool_input_str = tool_input_str[:1000] + "... (truncated)"
                        tool_span.set_data("tool_input", tool_input_str)

                    # Add breadcrumb for tool use
                    sentry_sdk.add_breadcrumb(
                        category="tool_use",
                        message=f"Tool: {block.name}",
                        level="info",
                        data={
                            "tool_name": block.name,
                            "tool_id": block.id,
                            "input_preview": str(block.input)[:200],
                        },
                    )

                    console.print(
                        f"[magenta]⚙️  [{timestamp}] Tool Use:[/magenta] {block.name}"
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

                    # Add Sentry breadcrumb for tool result
                    sentry_sdk.add_breadcrumb(
                        category="tool_result",
                        message=f"Tool result: {result_preview[:100]}",
                        level="error" if block.is_error else "info",
                        data={
                            "tool_use_id": block.tool_use_id,
                            "is_error": block.is_error,
                            "result_length": (
                                len(str(block.content)) if block.content else 0
                            ),
                            "block_index": block_idx,
                        },
                    )

                    console.print(
                        f"[blue]{status_icon} [{timestamp}] Tool Result:[/blue] {result_preview}..."
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
            # Add Sentry context for system message
            if hasattr(msg, "data") and isinstance(msg.data, dict):
                sentry_sdk.add_breadcrumb(
                    category="system_message",
                    message=f"System: {msg.data.get('subtype', 'N/A')}",
                    level="info",
                    data={
                        "subtype": msg.data.get("subtype", "N/A"),
                        "session_id": msg.data.get("session_id", "N/A"),
                        "model": msg.data.get("model", "N/A"),
                        "num_agents": len(msg.data.get("agents", [])),
                        "num_tools": len(msg.data.get("tools", [])),
                    },
                )

            if debug_mode:
                console.print(f"[dim]ℹ️  [{timestamp}] System Message[/dim]")
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
            # Capture comprehensive metrics in Sentry context
            usage_data = {}
            if msg.usage and isinstance(msg.usage, dict):
                usage_data = {
                    "input_tokens": msg.usage.get("input_tokens", 0),
                    "output_tokens": msg.usage.get("output_tokens", 0),
                    "cache_read_input_tokens": msg.usage.get(
                        "cache_read_input_tokens", 0
                    ),
                    "cache_creation_input_tokens": msg.usage.get(
                        "cache_creation_input_tokens", 0
                    ),
                    "stop_reason": msg.usage.get("stop_reason", "N/A"),
                }

            # Set comprehensive Sentry context for metrics
            sentry_sdk.set_context("claude_usage", usage_data)

            # Add cost and duration data
            metrics_data = {
                "total_cost_usd": (
                    float(msg.total_cost_usd) if msg.total_cost_usd else 0.0
                ),
                "duration_ms": (
                    msg.duration_ms
                    if hasattr(msg, "duration_ms") and msg.duration_ms
                    else 0
                ),
                "duration_api_ms": (
                    msg.duration_api_ms
                    if hasattr(msg, "duration_api_ms") and msg.duration_api_ms
                    else 0
                ),
                "num_turns": (
                    msg.num_turns if hasattr(msg, "num_turns") and msg.num_turns else 0
                ),
                "session_id": (
                    msg.session_id
                    if hasattr(msg, "session_id") and msg.session_id
                    else "N/A"
                ),
            }
            sentry_sdk.set_context("claude_metrics", metrics_data)

            # Add breadcrumb with summary
            sentry_sdk.add_breadcrumb(
                category="result_message",
                message=f"Result: {usage_data.get('input_tokens', 0)} in, {usage_data.get('output_tokens', 0)} out tokens",
                level="info",
                data={**usage_data, **metrics_data},
            )

            console.print(
                f"[bold green]✅ [{timestamp}] " "Result Message Received[/bold green]"
            )

            # Cost information
            cost = 0.0
            if msg.total_cost_usd:
                cost = float(msg.total_cost_usd)
                if cost > 0:
                    console.print(
                        f"[bold yellow]💰 Total Cost: ${cost:.6f}" "[/bold yellow]"
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

        # StreamEvent handling - log to file only, no console output
        elif isinstance(msg, StreamEvent):
            # Write to log file only
            today_str = datetime.now().strftime("%Y_%m_%d")
            logs_dir = Path(__file__).parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            log_file = logs_dir / f"{today_str}_app.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} | INFO | StreamEvent: {msg}\n")
            return

        # Unknown message type - just print it
        else:
            console.print(msg)
            if debug_mode:
                console.print(f"[dim]⚠️  Unknown message type: {type(msg)}[/dim]")

    except Exception as e:
        logger.error(f"Error displaying message: {e}", exc_info=True)

        # Capture exception in Sentry with context
        sentry_sdk.set_context(
            "message_display_error",
            {
                "message_type": type(msg).__name__ if msg else "unknown",
                "error": str(e),
                "debug_mode": debug_mode,
                "iteration": iteration,
            },
        )
        sentry_sdk.capture_exception(e)

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
        project_root = find_project_root(
            script_dir
        )  # /home/dev/claude_dev/claude_swarm
        parent_root = project_root.parent  # /home/dev/claude_dev
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
            + f"\n\nTip: Use absolute path (e.g., /home/dev/claude_dev/airflow/...) or "
            f"verify the relative path is correct."
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
