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
    ThinkingBlock,  # For extended thinking models
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
    """Standardized message display function with status indicators.

    - UserMessage: "User: <content>"
    - AssistantMessage: "Claude: <content>" (also shows thinking and tool use)
    - SystemMessage: ignored
    - ResultMessage: "Result ended" + cost if available
    """
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
                # This shows Claude's internal reasoning (extended thinking)
                console.print(f"[yellow]💭 [{timestamp}] Thinking:[/yellow] {block.thinking[:300]}...")
            
            elif isinstance(block, ToolUseBlock):
                # This shows when Claude is using a tool (acts as status/heartbeat)
                console.print(f"[magenta]⚙️  [{timestamp}] Tool Use:[/magenta] {block.name}")
                console.print(f"   Input: {str(block.input)[:300]}...")
            
            elif isinstance(block, ToolResultBlock):
                # This shows the result of a tool execution
                result_preview = str(block.content)[:300] if block.content else "No content"
                console.print(f"[blue]✅ [{timestamp}] Tool Result:[/blue] {result_preview}...")
    
    elif isinstance(msg, SystemMessage):
        # System messages can be logged for debugging
        # console.print(f"[dim]🔧 [{timestamp}] System:[/dim] {msg}")
        pass
    
    elif isinstance(msg, ResultMessage):
        console.print(f"[bold green]✅ [{timestamp}] Result ended[/bold green]")


def extract_python_code(text: str) -> str | None:
    """Extract Python code from markdown code blocks or plain text."""
    # Try to find code blocks with python tag
    python_blocks = re.findall(r'```python\s*\n(.*?)```', text, re.DOTALL)
    if python_blocks:
        return python_blocks[-1].strip()  # Return the last code block
    
    # Try to find generic code blocks
    code_blocks = re.findall(r'```\s*\n(.*?)```', text, re.DOTALL)
    if code_blocks:
        # Check if it looks like Python code
        for block in reversed(code_blocks):  # Start from the last block
            if any(keyword in block for keyword in ['def ', 'import ', 'class ', 'return ']):
                return block.strip()
    
    return None

def save_code_to_file(code: str, output_dir: str, filename: str = "fibonacci.py"):
    """Save the code to a file in the specified directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_path = output_path / filename
    with open(file_path, 'w') as f:
        f.write(code)
    
    return str(file_path)

async def orchestrator_with_subagents(output_dir: str = "./output"):
    """
    Orchestrator that creates and reviews Python code, then saves it to a file.
    
    Args:
        output_dir: Directory where the reviewed Python file will be saved
    """
    options = ClaudeAgentOptions(
        agents={
            'python-developer': AgentDefinition(
                description='Expert Python developer. Use for writing, implementing, and debugging Python code.',
                prompt='''You are an expert Python developer with deep knowledge of best practices, algorithms, and clean code principles.

When writing code:
- Write efficient, readable Python code
- Include proper error handling
- Add clear docstrings and comments
- Follow PEP 8 style guidelines
- Consider edge cases and performance

Focus on creating well-structured, maintainable code.''',
                tools=['Read', 'Write', 'Edit', 'Bash'],
                model='sonnet'
            ),
            'test_generator': AgentDefinition(
                description=(
                    "Specialized testing expert. Use this agent to GENERATE TEST SUITES "
                    "for new or existing code. This agent creates comprehensive unit and "
                    "integration tests following pytest best practices and project standards."
                ),
                prompt="""You are a testing specialist focused on Python/pytest.

Your responsibilities:
1. Generate comprehensive test suites (unit + integration tests)
2. Achieve minimum 80% code coverage
3. Use pytest fixtures effectively
4. Mock external dependencies appropriately
5. Write clear, descriptive test names and docstrings
6. Test happy paths, edge cases, and error conditions

Test generation guidelines:
- Read the implementation code first
- Create tests that mirror the app structure (tests/test_*.py)
- Use pytest-asyncio for async tests
- Include fixtures in conftest.py for reusable test data
- Add parametrize for multiple test cases
- Verify tests run successfully

Always run tests after generation to ensure they pass.""",
                tools=["Read", "Write", "Bash", "Grep", "Glob"],
                model="sonnet",
            ),
            
            'code-reviewer': AgentDefinition(
                description='Expert code review specialist. Use for quality, security, and maintainability reviews.',
                prompt='''You are a code review specialist with expertise in security, performance, and best practices.

When reviewing code:
- Identify security vulnerabilities
- Check for performance issues
- Verify adherence to coding standards
- Suggest specific improvements
- Provide the final, reviewed version of the code in a Python code block

Be thorough but concise in your feedback. Always provide the complete, improved code at the end.''',
                tools=['Read', 'Grep', 'Glob'],
                model='sonnet'
            )
        }
    )

    collected_code = []
    
    async for message in query(
        prompt="Create a Python function to calculate fibonacci numbers and review it for quality. Provide the final reviewed code.",
        options=options
    ):
        # Display message
        display_message(message)
        
        # Extract code from assistant messages
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    code = extract_python_code(block.text)
                    if code:
                        collected_code.append(code)
        
        # When we get the final result, save the code
        if isinstance(message, ResultMessage):
            cost = 0.0
            if message.total_cost_usd:
                cost = float(message.total_cost_usd)
            
            print(f"\n✅ Feature generation complete!")
            if cost > 0:
                print(f"💰 Total cost: ${cost:.4f}")
            
            # Save the last (reviewed) code to file
            if collected_code:
                final_code = collected_code[-1]  # Get the last code block (reviewed version)
                try:
                    saved_path = save_code_to_file(final_code, output_dir)
                    print(f"📝 Reviewed code saved to: {saved_path}")
                except Exception as e:
                    print(f"❌ Error saving file: {e}")
            else:
                print("⚠️ No code was extracted from the conversation")

async def orchestrator_with_status_monitoring(output_dir: str = "./output"):
    """
    Orchestrator that creates and reviews Python code with real-time status monitoring.
    
    The SDK streams messages as they arrive, allowing you to see:
    - When Claude is thinking (ThinkingBlock)
    - When Claude is using tools (ToolUseBlock) 
    - Tool execution results (ToolResultBlock)
    - Final text responses (TextBlock)
    
    Args:
        output_dir: Directory where the reviewed Python file will be saved
    """
    options = ClaudeAgentOptions(
        agents={
            'python-developer': AgentDefinition(
                description='Expert Python developer. Use for writing, implementing, and debugging Python code.',
                prompt='''You are an expert Python developer with deep knowledge of best practices, algorithms, and clean code principles.

When writing code:
- Write efficient, readable Python code
- Include proper error handling
- Add clear docstrings and comments
- Follow PEP 8 style guidelines
- Consider edge cases and performance

Focus on creating well-structured, maintainable code.''',
                tools=['Read', 'Write', 'Edit', 'Bash'],
                model='sonnet'
            ),
            'code-reviewer': AgentDefinition(
                description='Expert code review specialist. Use for quality, security, and maintainability reviews.',
                prompt='''You are a code review specialist with expertise in security, performance, and best practices.

When reviewing code:
- Identify security vulnerabilities
- Check for performance issues
- Verify adherence to coding standards
- Suggest specific improvements
- Provide the final, reviewed version of the code in a Python code block

Be thorough but concise in your feedback. Always provide the complete, improved code at the end.''',
                tools=['Read', 'Grep', 'Glob'],
                model='sonnet'
            )
        },
        # Optional: Enable extended thinking for more detailed reasoning
        # max_thinking_tokens=8000,  # This enables extended thinking mode
    )

    console.print("[bold cyan]🚀 Starting orchestrator with status monitoring...[/bold cyan]\n")
    
    collected_code = []
    tool_use_count = 0
    thinking_count = 0
    
    async for message in query(
        prompt="Create a Python function to calculate fibonacci numbers and review it for quality. Provide the final reviewed code.",
        options=options
    ):
        # Display message with status indicators
        display_message(message)
        
        # Track activity metrics
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ThinkingBlock):
                    thinking_count += 1
                elif isinstance(block, ToolUseBlock):
                    tool_use_count += 1
                elif isinstance(block, TextBlock):
                    code = extract_python_code(block.text)
                    if code:
                        collected_code.append(code)
        
        # When we get the final result, save the code and show summary
        if isinstance(message, ResultMessage):
            cost = 0.0
            if message.total_cost_usd:
                cost = float(message.total_cost_usd)
            
            console.print(f"\n[bold green]✅ Task complete![/bold green]")
            console.print(f"[dim]📊 Activity Summary:[/dim]")
            console.print(f"   • Tool uses: {tool_use_count}")
            console.print(f"   • Thinking blocks: {thinking_count}")
            if cost > 0:
                console.print(f"   • Total cost: ${cost:.4f}")
            
            # Save the last (reviewed) code to file
            if collected_code:
                final_code = collected_code[-1]
                try:
                    saved_path = save_code_to_file(final_code, output_dir)
                    console.print(f"[bold]📝 Reviewed code saved to:[/bold] {saved_path}\n")
                except Exception as e:
                    console.print(f"[red]❌ Error saving file:[/red] {e}")
            else:
                console.print("[yellow]⚠️  No code was extracted from the conversation[/yellow]")

async def orchestrator_with_hooks_monitoring(output_dir: str = "./output"):
    """
    Alternative approach using hooks for more granular event monitoring.
    Hooks can intercept events at specific points in the agent loop.
    """
    from claude_agent_sdk import HookMatcher, HookContext
    
    # Define hook callbacks for monitoring
    async def pre_tool_use_hook(input_data: dict, tool_use_id: str | None, context: HookContext) -> dict:
        """Called before each tool use - acts as a status indicator."""
        tool_name = input_data.get('tool_name', 'unknown')
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(f"[yellow]🔔 [{timestamp}] Hook: About to use tool '{tool_name}'[/yellow]")
        return {}  # Empty dict means allow the tool use
    
    async def post_tool_use_hook(input_data: dict, tool_use_id: str | None, context: HookContext) -> dict:
        """Called after each tool use completes."""
        tool_name = input_data.get('tool_name', 'unknown')
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(f"[green]✅ [{timestamp}] Hook: Completed tool '{tool_name}'[/green]")
        return {}
    
    options = ClaudeAgentOptions(
        agents={
            'python-developer': AgentDefinition(
                description='Expert Python developer.',
                prompt='You are an expert Python developer.',
                tools=['Read', 'Write', 'Edit', 'Bash'],
                model='sonnet'
            ),
        },
        # Hooks provide detailed event monitoring
        hooks={
            'PreToolUse': [
                HookMatcher(hooks=[pre_tool_use_hook])
            ],
            'PostToolUse': [
                HookMatcher(hooks=[post_tool_use_hook])
            ]
        }
    )
    
    console.print("[bold cyan]🚀 Starting orchestrator with hooks monitoring...[/bold cyan]\n")
    
    collected_code = []
    
    async for message in query(
        prompt="Create a simple Python hello world function",
        options=options
    ):
        display_message(message)
        
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    code = extract_python_code(block.text)
                    if code:
                        collected_code.append(code)
        
        if isinstance(message, ResultMessage):
            if collected_code:
                final_code = collected_code[-1]
                saved_path = save_code_to_file(final_code, output_dir, "hello_world.py")
                console.print(f"\n[bold]📝 Code saved to:[/bold] {saved_path}\n")
# Run the orchestrator
if __name__ == "__main__":
    # Specify your output directory here
    output_path=Path(__file__).parent
    OUTPUT_DIR = f"{output_path}/generated_code"
    asyncio.run(orchestrator_with_subagents(output_dir=OUTPUT_DIR))
#'python-developer': AgentDefinition(

# Test generator agent definition (kept from original)
