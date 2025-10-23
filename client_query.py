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

from pathlib import Path
import asyncio
from rich import print
from util.helpers import load_markdown_for_prompt, display_message, logger



class ConversationSession:
    """Maintains a single conversation session with Claude."""

    def __init__(self, options: ClaudeAgentOptions = None):
        self.client = ClaudeSDKClient(options)
        self.turn_count = 0

    async def start(self):
        await self.client.connect()
        print("Starting conversation session. Claude will remember context.")
        print("Commands: 'exit' to quit, 'interrupt' to stop current task, 'new' for new session")

        while True:
            user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")

            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'interrupt':
                await self.client.interrupt()
                print("Task interrupted!")
                continue
            elif user_input.lower() == 'new':
                # Disconnect and reconnect for a fresh session
                await self.client.disconnect()
                await self.client.connect()
                self.turn_count = 0
                print("Started new conversation session (previous context cleared)")
                continue

            # Send message - Claude remembers all previous messages in this session
            await self.client.query(user_input)
            self.turn_count += 1

            # Process response
            print(f"[Turn {self.turn_count}] Claude: ", end="")
            async for message in self.client.receive_response():
                display_message(message)
                
            print()  # New line after response

        await self.client.disconnect()
        print(f"Conversation ended after {self.turn_count} turns.")

    async def flask_app_orchestrator(self, project_dir: str = "./flask_hello_world"):
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

        display_message("[bold cyan]🚀 Starting Flask app orchestrator with CLAUDE.md context...[/bold cyan]\n")
        display_message(f"[dim]📁 Project directory: {project_path.absolute()}[/dim]\n")
        
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
                
                display_message(f"\n[bold green]✅ Flask app creation complete![/bold green]")
                display_message(f"[dim]📊 Activity Summary:[/dim]")
                display_message(f"   • Tool uses: {tool_use_count}")
                display_message(f"   • Thinking blocks: {thinking_count}")
                display_message(f"   • Files created: {len(files_created)}")
                if cost > 0:
                    display_message(f"   • Total cost: ${cost:.4f}")
                
                display_message(f"\n[bold]📁 Project location:[/bold] {project_path.absolute()}")
                display_message(f"\n[bold cyan]🚀 To run your Flask app:[/bold cyan]")
                display_message(f"   cd {project_path.absolute()}")
                display_message(f"   pip install -r requirements.txt")
                display_message(f"   python app.py")
                display_message(f"\n   Then visit: [bold]http://localhost:5010[/bold]")
                display_message(f"   Refresh the page to see different random styles!\n")
                
                if files_created:
                    display_message("[dim]Files created:[/dim]")
                    for file in files_created:
                        display_message(f"   • {file}")
async def main():
    output_path=Path(__file__).parent
    PROJECT_DIR = "/home/dev"
    options = ClaudeAgentOptions(
        # Enable loading of CLAUDE.md from project directory
        setting_sources=["project"],
        
        # Set working directory to project root
        cwd=str(PROJECT_DIR),
        
        # Define subagents for different tasks
        agents={
            'Apache Airflow-developer': AgentDefinition(
                description='Expert Apache Airflow web developer. Use for creating Apache Airflow applications, routes, and server configuration.',
                prompt='''You are an expert Apache Airflow web developer with deep knowledge of Python web development.

When creating Apache Airflow applications:
- Write clean, modular Apache Airflow code
- Follow Apache Airflow best practices and conventions
- Include proper error handling
- Consider security best practices
- Make code production-ready

Create well-structured, maintainable web applications.''',
                tools=['Read', 'Write', 'Edit', 'Bash'],
                model='sonnet'
            ),
            
            'python-developer': AgentDefinition(
                description='Expert Python developer. Generalist for creating Python code, scripts, and automation.',
                prompt='''You are an expert Python developer specializing in async programming and automation.

When creating apps:
- Follow best practices for async programming and Python development
- Write clean, modular, and efficient code
- Consider security best practices
- Do not use init params that could be problematic for the Apache Airflow environment and heartbeat


Build beautiful, functional user interfaces.''',
                tools=['Read', 'Write', 'Edit'],
                model='sonnet'
            ),
            
            'code-reviewer': AgentDefinition(
                description='Expert code review specialist. Use for quality, security, and best practices reviews.',
                prompt='''You are a code review specialist with expertise in web security and best practices.

When reviewing code:
- Check for security vulnerabilities
- Verify Apache Airflow-specific best practices
- Ensure proper error handling
- Suggest improvements
- Check code with flake8

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
  
    session = ConversationSession(options)
    await session.start()

# Example conversation:
# Turn 1 - You: "Create a file called hello.py"
# Turn 1 - Claude: "I'll create a hello.py file for you..."
# Turn 2 - You: "What's in that file?"
# Turn 2 - Claude: "The hello.py file I just created contains..." (remembers!)
# Turn 3 - You: "Add a main function to it"
# Turn 3 - Claude: "I'll add a main function to hello.py..." (knows which file!)

# Run the orchestrator
if __name__ == "__main__":
    # Set the project directory
    output_path = Path(__file__).resolve().parent
    PROJECT_DIR = f"{output_path}/generated_code"
    
    display_message("[bold magenta]╔══════════════════════════════════════════════════════╗[/bold magenta]")
    display_message("[bold magenta]║  Flask Hello World App Generator with CLAUDE.md     ║[/bold magenta]")
    display_message("[bold magenta]╚══════════════════════════════════════════════════════╝[/bold magenta]\n")
    
    asyncio.run(main(project_dir=PROJECT_DIR))