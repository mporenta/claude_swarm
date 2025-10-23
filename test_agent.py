#!/usr/bin/env python3
"""
Orchestrator Agent Example: FastAPI Code Generator (FIXED VERSION)

This example demonstrates:
1. An orchestrator pattern that coordinates specialized sub-agents
2. Code generation use case with consistent conventions from CLAUDE.md
3. Project-level settings using setting_sources=["project"]
4. System prompt with "claude_code" preset
5. Proper use of AgentDefinition dataclass for sub-agents
"""

import anyio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,  # IMPORTANT: Import AgentDefinition
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)
from log_set import logger, log_config
log_config.setup()
# ============================================================================
# CLAUDE.md FILE STRUCTURE (Place at project root)
# ============================================================================
"""
Create a CLAUDE.md file in your project root with consistent coding standards:

```markdown
# FastAPI Project Guidelines

## Code Style Standards
- Use Python 3.10+ with type hints for all functions
- Follow PEP 8 style guide strictly
- Use async/await for all route handlers
- Add comprehensive docstrings (Google style)
- Maximum line length: 100 characters

## Architecture Requirements
- Use dependency injection for database sessions
- Implement Pydantic models for request/response validation
- Separate business logic from route handlers
- Follow repository pattern for data access
- Use service layer for business logic

## Testing Standards
- Minimum 80% code coverage required
- Use pytest with async support (pytest-asyncio)
- Write unit tests for services and repositories
- Write integration tests for API endpoints
- Mock external dependencies
```
"""


# ============================================================================
# ORCHESTRATOR CONFIGURATION
# ============================================================================

def create_code_orchestrator_options(project_path: str = ".") -> ClaudeAgentOptions:
    """
    Configure the orchestrator agent with specialized sub-agents.
    
    FIXED: Now properly uses AgentDefinition dataclass instances
    instead of plain dictionaries.
    """
    try:
    
        # Define sub-agents using AgentDefinition dataclass
        code_generator = AgentDefinition(
            description=(
                "Expert Python/FastAPI code generator. Use this agent when you need to "
                "CREATE NEW code files, implement features, or write application logic. "
                "This agent follows project conventions from CLAUDE.md and generates "
                "production-ready code with proper structure, type hints, and documentation."
            ),
            prompt="""You are a senior Python developer specializing in FastAPI applications.

    Your responsibilities:
    1. Generate clean, well-structured Python code following project guidelines
    2. Implement FastAPI routes with proper dependency injection
    3. Create Pydantic models for request/response validation
    4. Write comprehensive docstrings and type hints
    5. Follow the repository and service layer patterns
    6. Ensure code is production-ready and maintainable

    When generating code:
    - Read existing files to understand current structure
    - Follow patterns established in the codebase
    - Adhere strictly to guidelines in CLAUDE.md
    - Generate complete, working implementations (not pseudocode)
    - Use appropriate async patterns
    - Add inline comments for complex logic

    Always verify your generated code by reading it back.""",
            tools=["Read", "Write", "Edit", "Grep", "Glob"],
            model="sonnet",
        )
        
        test_generator = AgentDefinition(
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
        )
        
        code_reviewer = AgentDefinition(
            description=(
                "Expert code reviewer focusing on quality, security, and standards compliance. "
                "Use this agent to REVIEW generated code for issues before finalizing. "
                "This agent checks adherence to CLAUDE.md guidelines, security best practices, "
                "and code quality standards."
            ),
            prompt="""You are a senior code reviewer with expertise in Python security and best practices.

    Your review checklist:
    1. Verify adherence to CLAUDE.md guidelines
    2. Check for security vulnerabilities (SQL injection, XSS, etc.)
    3. Validate proper error handling
    4. Ensure type hints are comprehensive
    5. Review docstring quality and completeness
    6. Check for code smells and anti-patterns
    7. Verify test coverage is adequate
    8. Assess performance implications

    Review process:
    - Read the generated code thoroughly
    - Compare against project standards
    - Identify specific issues with line numbers
    - Suggest concrete improvements
    - Highlight security concerns
    - Verify tests cover critical paths

    Provide actionable feedback in a structured format.""",
            tools=["Read", "Grep", "Glob", "Bash"],
            model="opus",
        )
        
        refactoring_specialist = AgentDefinition(
            description=(
                "Refactoring expert for improving existing code. Use when you need to "
                "IMPROVE code quality, performance, or maintainability without changing "
                "functionality. Ensures backward compatibility."
            ),
            prompt="""You are a refactoring specialist focused on code improvement.

    Your responsibilities:
    1. Improve code structure and readability
    2. Apply appropriate design patterns
    3. Optimize performance where beneficial
    4. Maintain backward compatibility
    5. Update tests to match refactored code
    6. Document changes and rationale

    Refactoring approach:
    - Understand existing functionality completely
    - Make incremental, testable changes
    - Run tests after each refactoring step
    - Keep changes focused and minimal
    - Add comments explaining improvements

    Never change public APIs without explicit approval.""",
            tools=["Read", "Edit", "Bash", "Grep", "Glob"],
            model="sonnet",
        )
        
        return ClaudeAgentOptions(
            # Use the "claude_code" preset system prompt
            system_prompt="claude_code",
            
            # CRITICAL: Load CLAUDE.md from project root
            setting_sources=["project"],
            
            # Set working directory
            cwd=project_path,
            
            # Define agents using AgentDefinition instances (NOT dictionaries!)
            agents={
                "code-generator": code_generator,
                "test-generator": test_generator,
                "code-reviewer": code_reviewer,
                "refactoring-specialist": refactoring_specialist,
            },
            
            # Tools for orchestrator (not sub-agents)
            allowed_tools=["Read", "Grep", "Glob", "Bash"],
            disallowed_tools=["Write", "Edit", "Delete"],
            
            # Permission configuration
            permission_mode="acceptEdits",
            
            # Session configuration
            max_turns=30,
            model="sonnet",
        )

    except Exception as e:
        logger.error(f"Error creating orchestrator options: {e}")
        raise
# ============================================================================
# ORCHESTRATOR WORKFLOW CLASS
# ============================================================================

class CodeGenerationOrchestrator:
    """
    Orchestrator that coordinates multiple sub-agents for code generation.
    """
    
    def __init__(self, project_path: str = "."):
        """Initialize orchestrator with project path."""
        try:
            self.project_path = Path(project_path)
            self.options = create_code_orchestrator_options(str(self.project_path))
            self.client = None
            logger.info(f"CodeGenerationOrchestrator initialized for project: {self.project_path} with options: {self.options}")
        except Exception as e:
            logger.error(f"Failed to initialize CodeGenerationOrchestrator: {e}")
            raise
    async def __aenter__(self):
        """Context manager entry - initialize client."""
        self.client = ClaudeSDKClient(options=self.options)
        await self.client.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        if self.client:
            await self.client.disconnect()
    
    async def generate_feature(self, feature_description: str) -> dict:
        """
        Generate a complete feature with code, tests, and review.
        """
        
        orchestration_prompt = f"""
I need you to orchestrate the development of a new feature. Follow this workflow:

**Feature Request:**
{feature_description}

**Workflow:**

1. **Analysis Phase**
   - Understand the feature requirements
   - Review existing codebase structure (use Read, Grep, Glob tools)
   - Identify files that need to be created or modified
   - Check CLAUDE.md guidelines for relevant patterns

2. **Code Generation Phase**
   - Delegate to the 'code-generator' agent to implement the feature
   - Ensure it follows project structure and conventions
   - The agent will create necessary files (models, services, repositories, routes)

3. **Test Generation Phase**
   - Delegate to the 'test-generator' agent to create comprehensive tests
   - Tests should cover unit and integration scenarios
   - Ensure tests follow project testing standards

4. **Review Phase**
   - Delegate to the 'code-reviewer' agent to review all generated code
   - Get feedback on quality, security, and standards compliance
   - Identify any issues that need fixing

5. **Verification Phase**
   - Run the test suite to verify everything works
   - Run linters/type checkers
   - Confirm all standards are met

**Coordination Guidelines:**
- You are the orchestrator - delegate specialized tasks to sub-agents
- Don't write code yourself - use the code-generator agent
- Ensure each phase completes before moving to the next
- Provide clear instructions to each sub-agent

Please proceed with this orchestrated workflow.
"""
        
        await self.client.query(orchestration_prompt)
        
        # Collect results
        results = {
            "messages": [],
            "files_created": [],
            "files_modified": [],
            "cost_usd": 0.0,
        }
        
        print("🚀 Starting orchestrated feature generation...\n")
        
        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        results["messages"].append(block.text)
                    
                    elif isinstance(block, ToolUseBlock):
                        tool_name = block.tool_name
                        print(f"\n🔧 Using tool: {tool_name}")
                        
                        if tool_name == "Write":
                            file_path = block.tool_input.get("path", "unknown")
                            results["files_created"].append(file_path)
                            print(f"   ✏️  Creating: {file_path}")
                        
                        elif tool_name == "Edit":
                            file_path = block.tool_input.get("path", "unknown")
                            results["files_modified"].append(file_path)
                            print(f"   ✏️  Modifying: {file_path}")
            
            elif isinstance(message, ResultMessage):
                if message.total_cost_usd:
                    results["cost_usd"] = message.total_cost_usd
        
        print(f"\n✅ Feature generation complete!")
        print(f"💰 Total cost: ${results['cost_usd']:.4f}")
        
        return results
    
    async def quick_implementation(self, task: str) -> None:
        """
        Quick implementation without full orchestration.
        """
        prompt = f"""
Implement this task following project conventions from CLAUDE.md:

{task}

Use the appropriate sub-agent (code-generator for implementation, 
test-generator for tests, etc.) and keep it simple.
"""
        
        await self.client.query(prompt)
        
        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)


# ============================================================================
# EXAMPLE USAGE SCENARIOS
# ============================================================================

async def example_1_user_management_feature():
    """
    Example 1: Generate a complete user management feature.
    """
    print("=" * 80)
    print("EXAMPLE 1: Complete User Management Feature")
    print("=" * 80)
    
    async with CodeGenerationOrchestrator(project_path=Path(__file__).parent) as orchestrator:
        
        feature_request = """
Create a user management feature for our FastAPI application:

Requirements:
- User registration endpoint (POST /users)
- User login endpoint (POST /auth/login)
- Get user profile endpoint (GET /users/me)
- Update user profile endpoint (PUT /users/me)

Implementation details:
- Use Pydantic models for request/response validation
- Implement password hashing with bcrypt
- Use JWT tokens for authentication
- Follow repository pattern for database access
- Add comprehensive error handling
"""
        
        results = await orchestrator.generate_feature(feature_request)
        
        print("\n" + "=" * 80)
        print("📊 GENERATION SUMMARY")
        print("=" * 80)
        print(f"Files created: {len(results['files_created'])}")
        for file in results['files_created']:
            print(f"  - {file}")
        print(f"\nFiles modified: {len(results['files_modified'])}")
        for file in results['files_modified']:
            print(f"  - {file}")
        print(f"\n💰 Total cost: ${results['cost_usd']:.4f}")


async def example_2_quick_endpoint():
    """
    Example 2: Quick endpoint generation.
    """
    try:
        print("\n" + "=" * 80)
        print("EXAMPLE 2: Quick Health Check Endpoint")
        print("=" * 80)
        
        async with CodeGenerationOrchestrator(project_path=Path(__file__).parent) as orchestrator:
            logger.debug("Starting quick implementation for health check endpoint.")
            await orchestrator.quick_implementation(
                "Add a health check endpoint at GET /health that returns system status"
            )
            logger.debug("Completed quick implementation for health check endpoint.")

    except Exception as e:
        logger.error(f"An error occurred during #2 quick endpoint generation: {e}")
async def example_3_stateless_generation():
    """
    Example 3: Using stateless query() function.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Stateless Code Generation")
    print("=" * 80)
    
    options = ClaudeAgentOptions(
        system_prompt="claude_code",
        setting_sources=["project"],
        cwd=Path(__file__).parent,
        allowed_tools=["Read", "Write", "Grep", "Glob"],
        permission_mode="acceptEdits",
    )
    
    prompt = """
Create a simple Pydantic model for a Product with:
- id: int
- name: str
- price: float
- description: Optional[str]

Save it to app/models/product.py following project conventions from CLAUDE.md.
"""
    
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def example_4_code_review_only():
    """
    Example 4: Using a single sub-agent for code review.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Targeted Code Review")
    print("=" * 80)
    
    options = create_code_orchestrator_options(Path(__file__).parent)
    
    async with ClaudeSDKClient(options=options) as client:
        
        review_request = """
Use the 'code-reviewer' agent to review the file app/routes/users.py.

Focus on:
1. Security vulnerabilities
2. Error handling completeness
3. Adherence to CLAUDE.md guidelines
4. Type hint coverage

Provide specific, actionable feedback with line numbers.
"""
        
        await client.query(review_request)
        
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """
    Main entry point - run examples.
    
    Before running:
    1. Install: pip install claude-agent-sdk
    2. Install Claude Code CLI: npm install -g @anthropic-ai/claude-code
    3. Set API key: export ANTHROPIC_API_KEY="your-key"
    4. Create CLAUDE.md in your project root with coding standards
    """
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║            Claude Agent SDK: Code Generation Orchestrator (FIXED)            ║
║                                                                              ║
║  This example demonstrates:                                                  ║
║  • Orchestrator pattern with specialized sub-agents                          ║
║  • Project-level CLAUDE.md configuration                                     ║
║  • Code generation with consistent conventions                               ║
║  • Proper use of AgentDefinition dataclass                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Run examples (comment out the ones you don't want to run)
    
    # Full orchestration workflow
    # await example_1_user_management_feature()
    
    # Quick task without full workflow
    await example_2_quick_endpoint()
    
    # Stateless generation
    # await example_3_stateless_generation()
    
    # Single agent usage
    # await example_4_code_review_only()


if __name__ == "__main__":
    anyio.run(main)