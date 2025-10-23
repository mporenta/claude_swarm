from log_set import logger, log_config
from typing import Any
import re
from datetime import datetime
from pathlib import Path
log_config.setup()
import asyncio
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
    query,
    tool,
    create_sdk_mcp_server,
    UserMessage,
    SystemMessage,
)
from rich import print
from rich.console import Console

console = Console()

def display_message(msg):
    """Standardized message display function with status indicators."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
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

async def flask_app_orchestrator(project_dir: str = "./flask_hello_world"):
    """
    Orchestrator that creates a Flask web app with random styling.
    
    This demonstrates:
    - Using CLAUDE.md for project context
    - Multi-file code generation
    - Real-time status monitoring
    - Working directory management
    
    Args:
        project_dir: Directory where the Flask app will be created
    """
    
    # Create project directory structure
    project_path = Path(project_dir)
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "templates").mkdir(exist_ok=True)
    print(f"[dim]📁 Created project directory at: {project_path.absolute()}[/dim]\n")
    
   
    
    options = ClaudeAgentOptions(
        # Enable loading of CLAUDE.md from project directory
        setting_sources=["project"],
        
        # Set working directory to project root
        cwd=str(project_path),
        
        # Define subagents for different tasks
        agents={
            'flask-developer': AgentDefinition(
                description='Expert Flask web developer. Use for creating Flask applications, routes, and server configuration.',
                prompt='''You are an expert Flask web developer with deep knowledge of Python web development.

When creating Flask applications:
- Write clean, modular Flask code
- Follow Flask best practices and conventions
- Include proper error handling
- Use Jinja2 templating effectively
- Consider security best practices
- Make code production-ready

Create well-structured, maintainable web applications.''',
                tools=['Read', 'Write', 'Edit', 'Bash'],
                model='sonnet'
            ),
            
            'frontend-developer': AgentDefinition(
                description='Expert frontend developer. Use for creating HTML templates, CSS styling, and client-side functionality.',
                prompt='''You are an expert frontend developer specializing in HTML, CSS, and modern web design.

When creating web interfaces:
- Write semantic, accessible HTML
- Create responsive, modern designs
- Use CSS best practices
- Ensure cross-browser compatibility
- Focus on user experience
- Keep designs clean and maintainable

Build beautiful, functional user interfaces.''',
                tools=['Read', 'Write', 'Edit'],
                model='sonnet'
            ),
            
            'code-reviewer': AgentDefinition(
                description='Expert code review specialist. Use for quality, security, and best practices reviews.',
                prompt='''You are a code review specialist with expertise in web security and best practices.

When reviewing code:
- Check for security vulnerabilities
- Verify Flask-specific best practices
- Ensure proper error handling
- Check HTML/CSS quality
- Suggest improvements

Provide thorough, constructive feedback.''',
                tools=['Read', 'Grep', 'Glob'],
                model='sonnet'
            )
        },
        
        # Allow necessary tools
        allowed_tools=['Read', 'Write', 'Edit', 'Bash', 'Grep', 'Glob'],
        
        # Auto-accept file edits for smoother workflow
        permission_mode='acceptEdits'
    )

    console.print("[bold cyan]🚀 Starting Flask app orchestrator with CLAUDE.md context...[/bold cyan]\n")
    console.print(f"[dim]📁 Project directory: {project_path.absolute()}[/dim]\n")
    
    tool_use_count = 0
    thinking_count = 0
    files_created = []
    
    async for message in query(
        prompt="""Create a complete Flask web application with the following requirements:

1. **Main Flask App (app.py)**:
   - Run on port 5010
   - Single route: '/' for homepage
   - On each page refresh, generate random values for:
     * Text color (choose from a variety of colors)
     * Font size (between 20px and 100px)
     * Font family (choose from different fonts)
   - Pass these random values to the template

2. **HTML Template (templates/index.html)**:
   - Display "Hello World" text
   - Use the random styling values from Flask
   - Include clean, modern HTML structure
   - Make it responsive and centered on the page
   - Add a subtle background or design element

3. **Requirements File (requirements.txt)**:
   - List Flask and any other dependencies

4. **Testing**:
   - After creating all files, briefly test that the app structure is correct
   - Do NOT actually start the server (user will do this manually)

Follow the guidelines in CLAUDE.md. Create professional, production-ready code.""",
        options=options
    ):
        display_message(message)
        
        # Track activity metrics
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ThinkingBlock):
                    thinking_count += 1
                elif isinstance(block, ToolUseBlock):
                    tool_use_count += 1
                    # Track file creation
                    if block.name == "Write" and "file_path" in block.input:
                        files_created.append(block.input["file_path"])
        
        # When we get the final result, show summary
        if isinstance(message, ResultMessage):
            cost = 0.0
            if message.total_cost_usd:
                cost = float(message.total_cost_usd)
            
            console.print(f"\n[bold green]✅ Flask app creation complete![/bold green]")
            console.print(f"[dim]📊 Activity Summary:[/dim]")
            console.print(f"   • Tool uses: {tool_use_count}")
            console.print(f"   • Thinking blocks: {thinking_count}")
            console.print(f"   • Files created: {len(files_created)}")
            if cost > 0:
                console.print(f"   • Total cost: ${cost:.4f}")
            
            console.print(f"\n[bold]📁 Project location:[/bold] {project_path.absolute()}")
            console.print(f"\n[bold cyan]🚀 To run your Flask app:[/bold cyan]")
            console.print(f"   cd {project_path.absolute()}")
            console.print(f"   pip install -r requirements.txt")
            console.print(f"   python app.py")
            console.print(f"\n   Then visit: [bold]http://localhost:5010[/bold]")
            console.print(f"   Refresh the page to see different random styles!\n")
            
            if files_created:
                console.print("[dim]Files created:[/dim]")
                for file in files_created:
                    console.print(f"   • {file}")

# Run the orchestrator
if __name__ == "__main__":
    # Set the project directory
    output_path=Path(__file__).parent
    PROJECT_DIR = f"{output_path}/generated_code"
    
    console.print("[bold magenta]╔══════════════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║  Flask Hello World App Generator with CLAUDE.md     ║[/bold magenta]")
    console.print("[bold magenta]╚══════════════════════════════════════════════════════╝[/bold magenta]\n")
    
    asyncio.run(flask_app_orchestrator(project_dir=PROJECT_DIR))