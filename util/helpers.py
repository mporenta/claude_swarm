# helpers.py
from pathlib import Path
import re, os
from datetime import datetime
from dotenv import load_dotenv
from rich import print
from rich.console import Console
from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ThinkingBlock,
    ToolResultBlock,
    UserMessage,
    SystemMessage,
)
load_dotenv()
from log_set import logger, log_config

SET_DEBUG = os.getenv("SET_DEBUG", "False").lower() in ("true", "1", "yes")

def display_message(msg, debug: bool=SET_DEBUG):
    """Claude SDK standardized message display function with status indicators."""
    try:
        debug=True
        timestamp = datetime.now().strftime("%H:%M:%S")
        console = Console()
        debug_print= print(msg)
        if debug:
            log_config.setup()
            logger.debug(f"message log: {msg}")
            console.print(f"[dim]Debug: Displaying message at {timestamp}[/dim]")
            console.print(msg)

        
        
        if isinstance(msg, UserMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    console.print(f"[cyan]🧑 [{timestamp}] User:[/cyan] {block.text}")
        
        elif isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    console.print(f"[green]🤖 [{timestamp}] Claude:[/green] {block.text}")
                
                elif isinstance(block, ThinkingBlock):
                    console.print(f"[yellow]💭 [{timestamp}] Thinking:[/yellow] {block.thinking[:100]}...")
                
                elif isinstance(block, ToolUseBlock):
                    console.print(f"[magenta]⚙️  [{timestamp}] Tool Use:[/magenta] {block.name}")
                    console.print(f"   Input: {str(block.input)[:100]}...")
                
                elif isinstance(block, ToolResultBlock):
                    result_preview = str(block.content)[:100] if block.content else "No content"
                    console.print(f"[blue]✅ [{timestamp}] Tool Result:[/blue] {result_preview}...")
        
        elif isinstance(msg, SystemMessage):
            pass
        
        elif isinstance(msg, ResultMessage):
            console.print(f"[bold green]✅ [{timestamp}] Result ended[/bold green]")
        
            cost = 0.0
            if msg.total_cost_usd:
                cost = float(msg.total_cost_usd)
                if cost > 0:
                    console.print(f"[bold yellow]💰 Total Cost: ${cost:.6f}[/bold yellow]")
        else:
            console.print(msg)
    except Exception as e:
        print(f"Error displaying message: {e}")

def load_markdown_for_prompt(relative_path: str) -> str:
    """
    Loads a Markdown file relative to the project root, strips YAML front matter if present,
    and returns the content as a clean string ready for use in a Claude SDK agent prompt.
    Automatically detects the project root by walking up until a marker file is found.

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

        raw_content = file_path.read_text(encoding='utf-8').strip()

        # Strip YAML front matter (--- ... ---)
        yaml_pattern = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
        content = re.sub(yaml_pattern, "", raw_content, count=1).strip()

        return content
    except Exception as e:
        print(f"Error loading markdown for prompt: {e}")
        raise RuntimeError(f"Error loading markdown for prompt: {e}") from e