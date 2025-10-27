# CLAUDE.md - Orchestration Guide for Claude Swarm Multi-Agent System

## 🎯 YOUR ROLE: Main Orchestrator

**You are the main orchestrator** coordinating specialized AI agents to build Flask applications. Your job is to **delegate tasks to agents**, not to do the work yourself.

### ⚠️ CRITICAL: How to Delegate to Agents

When you receive a task (like building a Flask app), you MUST:

1. **Break down the task** into logical steps
2. **Delegate each step** to the appropriate agent using `@agent-name` syntax
3. **Coordinate their work** sequentially or in parallel
4. **Monitor progress** and ensure quality

**DO NOT attempt to do everything yourself!** You have specialized agents for each type of work.

### 🔧 Agent Delegation Syntax

Use this format to delegate tasks:

```markdown
@agent-name

[Clear, specific instructions for what this agent should do]
[Include file names, function signatures, requirements]
[Specify any validation or quality checks needed]
```

### 👥 Available Agents

#### @flask-developer
- **Purpose**: Backend Flask development
- **Tools**: Read, Write, Edit, Bash
- **Use for**:
  - Creating app.py with Flask routes
  - Implementing business logic
  - Creating requirements.txt
  - Writing Python code and documentation
  - Running Python tests

#### @frontend-developer
- **Purpose**: Frontend and UI development
- **Tools**: Read, Write, Edit
- **Use for**:
  - Creating HTML templates (templates/*.html)
  - Writing CSS styling
  - Implementing responsive design
  - Creating user interfaces

#### @code-reviewer
- **Purpose**: Code quality and validation
- **Tools**: Read, Grep, Glob, Bash
- **Use for**:
  - Running flake8 validation
  - Checking file structure
  - Verifying code quality
  - Security review
  - Running test commands

### 📋 Typical Flask App Workflow

**For a Flask "Hello World" app, delegate like this:**

```markdown
Step 1: Backend Development
@flask-developer

Create the Flask application backend:
- File: flask_app/app.py
- Include: [specific requirements]

Step 2: Frontend Development
@frontend-developer

Create the HTML template:
- File: flask_app/templates/index.html
- Include: [specific requirements]

Step 3: Documentation
@flask-developer

Create project documentation:
- File: flask_app/README.md
- Include: [specific sections]

Step 4: Quality Review
@code-reviewer

Validate the code:
- Check file structure
- Run flake8
- Verify requirements.txt
```

### ⚠️ DO NOT:
- ❌ Do all the work yourself using your own tools
- ❌ Skip agent delegation
- ❌ Create files directly without delegating to the appropriate agent
- ❌ Ignore the specialized agents available to you

### ✅ DO:
- ✅ Break tasks into clear steps
- ✅ Delegate each step to the appropriate agent
- ✅ Provide detailed instructions to each agent
- ✅ Wait for agent responses before proceeding
- ✅ Coordinate agent work efficiently

---

## Project Overview

This project is the **Claude Swarm Agent Orchestration System** - a sophisticated AI-powered code generation framework that orchestrates multiple specialized Claude agents to collaborate on web application development. The system is built on the Claude Agent SDK and demonstrates advanced multi-agent coordination for automated Flask and Airflow application generation.

**Repository**: https://github.com/mporenta/claude_swarm

**Purpose**: Enable multiple AI agents with specialized expertise to work together on complex development tasks, with each agent having specific roles, tool access, and capabilities for efficient collaboration.

## Architecture & Key Concepts

### Core Design Pattern: Multi-Agent Orchestration

The system uses an **orchestrator pattern** where:
- A main orchestrator coordinates multiple specialized agents
- Each agent has specific roles and tool permissions
- Agents collaborate through a conversation-based workflow
- Prompts are loaded dynamically from markdown files

### Agent Types (Reference)

#### Flask Development Agents
1. **@flask-developer**: Backend Flask development (Read, Write, Edit, Bash)
2. **@frontend-developer**: Frontend and templates (Read, Write, Edit)
3. **@code-reviewer**: Code quality and security (Read, Grep, Glob, Bash)

#### Airflow Development Agents (Beta)
1. **@dag-architect**: DAG architecture and design (Read, Grep, Glob)
2. **@dag-developer**: DAG implementation (Read, Write, Edit, Bash, Grep)
3. **@migration-specialist**: Airflow 1.0 to 2.0 migration (Read, Write, Edit, Grep, Glob)
4. **@airflow-code-reviewer**: Airflow-specific code review (Read, Grep, Glob)

### Directory Structure

```
claude_swarm/
├── flask_agent.py              # Main Flask orchestrator
├── airflow/
│   └── airflow_agent.py        # Airflow DAG orchestrator
├── dev/
│   ├── client_query.py         # CLAUDE.md support orchestrator
│   ├── flask_app_dev.py        # Flask dev orchestrator
│   └── test_dev.py             # Advanced code generation orchestrator
├── prompts/                    # Agent role definitions (markdown)
│   ├── main-query.md
│   ├── flask-developer.md
│   ├── frontend-developer.md
│   ├── code-reviewer.md
│   └── airflow_prompts/
├── util/
│   ├── log_set.py              # Logging configuration
│   └── helpers.py              # Display utilities
├── examples/                   # 12 official SDK examples
├── logs/                       # Application logs
└── generated_code/             # Output directory
```

## Development Guidelines

### Code Style & Standards

#### Python Standards (PEP 8 Compliance)
- Use type hints for all functions and methods
- Write comprehensive docstrings (Google style preferred)
- Meaningful variable names (no single letters except loop counters)
- Maximum line length: 88 characters (Black formatter compatible)
- Use f-strings for string formatting
- Imports organized: standard library, third-party, local imports

**Example**:
```python
from typing import Dict, List, Optional
import logging

def process_agent_response(
    response: Dict[str, any],
    agent_name: str,
    session_id: Optional[str] = None
) -> List[str]:
    """
    Process and extract files created from agent response.
    
    Args:
        response: Agent response dictionary with tool calls
        agent_name: Name of the agent that generated the response
        session_id: Optional session identifier for tracking
        
    Returns:
        List of file paths created during agent execution
        
    Raises:
        ValueError: If response format is invalid
    """
    # Implementation here
    pass
```

#### Logging Standards
- Use the centralized `LogConfig` class from `util/log_set.py`
- All errors must include traceback context
- Use appropriate log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General informational messages
  - `WARNING`: Warning messages for potential issues
  - `ERROR`: Error messages with traceback
- Include timestamps (timezone-aware using pytz)

**Example**:
```python
from util.log_set import LogConfig

# Initialize logging
logger = LogConfig.setup_logging()

# Usage
logger.info("Starting Flask agent orchestration")
logger.debug(f"Agent configuration: {agent_config}")
logger.error(f"Failed to load prompt: {prompt_file}", exc_info=True)
```

#### Error Handling
- Always use try-except blocks for external calls (API, file I/O)
- Catch specific exceptions, not bare `except:`
- Log errors with context before re-raising or handling
- Provide user-friendly error messages
- Clean up resources in `finally` blocks

**Example**:
```python
try:
    prompt_content = load_markdown_prompt(prompt_path)
except FileNotFoundError as e:
    logger.error(f"Prompt file not found: {prompt_path}", exc_info=True)
    raise ValueError(f"Required prompt file missing: {prompt_path}") from e
except Exception as e:
    logger.error(f"Unexpected error loading prompt: {e}", exc_info=True)
    raise
```

### Agent Definition Guidelines

When creating or modifying agent definitions in `prompts/`:

1. **Structure**: Use markdown format with clear sections
2. **Role Definition**: Clear, concise agent purpose statement
3. **Capabilities**: List specific tasks the agent can perform
4. **Tool Access**: Explicitly state which tools are needed
5. **Examples**: Include example delegations and expected outputs
6. **Constraints**: Document what the agent should NOT do

**Template**:
```markdown
# Agent: {agent-name}

## Role
{Clear, one-sentence description of agent's primary responsibility}

## Capabilities
- Specific capability 1
- Specific capability 2
- Specific capability 3

## Tool Access
- Read: For viewing files and directories
- Write: For creating new files
- Edit: For modifying existing files

## Guidelines
1. {Primary guideline}
2. {Secondary guideline}
3. {Code quality expectations}

## Examples
### Example 1: {Task Description}
Input: {User request}
Output: {Expected agent response}

## Constraints
- Do NOT {forbidden action 1}
- NEVER {forbidden action 2}
- AVOID {antipattern}
```

### Configuration Management

#### Environment Variables
Required: `ANTHROPIC_API_KEY`

Optional:
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `SET_DEBUG`: true/false (default: false)
- `CLAUDE_MODEL`: sonnet, opus, haiku (default: sonnet)
- `FLASK_ENV`: development, production (default: development)
- `FLASK_PROJECT_PATH`: Custom output path
- `AIRFLOW_HOME`: Airflow installation directory
- `AIRFLOW__CORE__DAGS_FOLDER`: Airflow DAGs location

**Always use `.env` file** - never commit API keys to version control

#### SDK Configuration
```python
from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition

options = ClaudeAgentOptions(
    setting_sources=["project"],  # Load .CLAUDE.md if present
    cwd="/path/to/working/directory",
    agents={
        "agent-name": AgentDefinition(
            role="role-definition-here",
            allowed_tools=["Read", "Write", "Edit"],
            model="sonnet"  # or "opus", "haiku"
        )
    },
    allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
    permission_mode="acceptEdits"  # or "prompt", "accept"
)
```

## Key Development Tasks

### Adding a New Agent

1. **Create prompt file**: `prompts/{agent-name}.md`
2. **Define agent role**: Clear purpose and capabilities
3. **Specify tools**: Only grant necessary tool permissions
4. **Add to orchestrator**: Update `AgentDefinition` in main file
5. **Test delegation**: Verify agent responds correctly to queries
6. **Document**: Update README and CLAUDE.md guidelines

**Example**:
```python
# In flask_agent.py or custom orchestrator
agents = {
    "new-agent": AgentDefinition(
        role=load_markdown_prompt("prompts/new-agent.md"),
        allowed_tools=["Read", "Write"],
        model="sonnet"
    )
}
```

### Modifying Orchestration Logic

**Key Files**:
- `flask_agent.py`: Main Flask orchestration loop
- `airflow/airflow_agent.py`: Airflow orchestration loop
- `dev/client_query.py`: Custom CLAUDE.md orchestrator

**Guidelines**:
1. Maintain conversation context across turns
2. Track created files from tool calls
3. Handle interrupts gracefully (SIGINT)
4. Provide rich terminal output with status indicators
5. Calculate and display session metrics (tokens, cost)

**Tool Call Tracking**:
```python
created_files = []
for content in response.content:
    if hasattr(content, 'tool_use_id'):
        # Extract file paths from tool calls
        if 'path' in content.input:
            created_files.append(content.input['path'])
```

### Testing Changes

#### Unit Testing Strategy
- Test agent prompt loading
- Test configuration parsing
- Test file tracking logic
- Test error handling

#### Integration Testing
1. Run orchestrator with test query
2. Verify all agents respond appropriately
3. Check generated files are correct
4. Validate flake8 compliance
5. Review logs for errors

#### Manual Testing
```bash
# Test Flask orchestrator
python flask_agent.py
# Type: flask

# Test Airflow orchestrator
python airflow/airflow_agent.py
# Provide DAG specification

# Test custom orchestrator
python dev/client_query.py
# Test with CLAUDE.md guidelines
```

### Debugging

#### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
export SET_DEBUG=true
python flask_agent.py
```

#### Common Debug Points
1. **Agent not responding**: Check prompt file loading
2. **Wrong tools used**: Verify `allowed_tools` in AgentDefinition
3. **Files not created**: Check `cwd` configuration and permissions
4. **API errors**: Verify `ANTHROPIC_API_KEY` is set correctly
5. **Import errors**: Ensure all dependencies in `requirements.txt`

#### Debug Logging Pattern
```python
logger.debug(f"Loading prompt from: {prompt_path}")
logger.debug(f"Agent configuration: {agent_name} -> {agent_def}")
logger.debug(f"Tool call: {tool_name} with params: {tool_params}")
logger.debug(f"Response content length: {len(response.content)}")
```

## Common Development Patterns

### Pattern 1: Adding a New Orchestrator

```python
"""Custom orchestrator for {specific use case}."""
import logging
from pathlib import Path
from typing import Dict, List

from claude_agent_sdk import ClaudeAgent, ClaudeAgentOptions, AgentDefinition
from util.log_set import LogConfig
from util.helpers import load_markdown_prompt, display_message

# Setup logging
logger = LogConfig.setup_logging()

def create_agent_options() -> ClaudeAgentOptions:
    """Create agent configuration."""
    return ClaudeAgentOptions(
        setting_sources=["project"],
        cwd=str(Path(__file__).parent / "output"),
        agents={
            "agent-1": AgentDefinition(
                role=load_markdown_prompt("prompts/agent-1.md"),
                allowed_tools=["Read", "Write", "Edit"],
                model="sonnet"
            ),
            # Add more agents
        },
        allowed_tools=["Read", "Write", "Edit", "Bash"],
        permission_mode="acceptEdits"
    )

def main():
    """Main orchestration loop."""
    options = create_agent_options()
    agent = ClaudeAgent(options)
    
    logger.info("Starting custom orchestrator")
    
    try:
        # Orchestration logic here
        response = agent.get_response("Initial query")
        display_message(response)
        
    except KeyboardInterrupt:
        logger.info("Orchestration interrupted by user")
    except Exception as e:
        logger.error(f"Orchestration failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
```

### Pattern 2: Loading and Using CLAUDE.md

```python
def load_project_guidelines(project_path: Path) -> str:
    """Load CLAUDE.md guidelines if present."""
    claude_md_path = project_path / "CLAUDE.md"
    
    if claude_md_path.exists():
        with open(claude_md_path, 'r') as f:
            return f.read()
    
    logger.warning(f"No CLAUDE.md found at {claude_md_path}")
    return ""

# In agent configuration
guidelines = load_project_guidelines(Path.cwd())
main_prompt = f"{base_prompt}\n\n# Project Guidelines\n{guidelines}"
```

### Pattern 3: Rich Terminal Display

```python
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

def display_agent_response(agent_name: str, content: str):
    """Display agent response with formatting."""
    panel = Panel(
        Markdown(content),
        title=f"🤖 {agent_name}",
        border_style="green"
    )
    console.print(panel)

def display_error(error_msg: str):
    """Display error message."""
    console.print(f"[red]❌ Error:[/red] {error_msg}")

def display_success(files: List[str]):
    """Display success message with created files."""
    console.print("[green]✅ Success![/green]")
    console.print(f"[blue]Created {len(files)} file(s):[/blue]")
    for file in files:
        console.print(f"  • {file}")
```

## File Modification Guidelines

### Critical Files (Require Careful Changes)
- `flask_agent.py`: Main orchestrator - test thoroughly
- `airflow/airflow_agent.py`: Airflow orchestrator - verify DAG generation
- `util/log_set.py`: Logging configuration - affects all components
- `prompts/*.md`: Agent definitions - review with multiple test cases

### Safe to Modify
- `examples/*.py`: SDK examples - independent scripts
- `dev/*.py`: Development orchestrators - experimental
- `README.md`: Documentation only
- `.env.example`: Template only, doesn't affect runtime

### Never Modify
- `.env`: Contains secrets (add to .gitignore if not present)
- `generated_code/`: Output directory (regenerated each run)
- `logs/*.log`: Log files (auto-generated)

## Flask Application File Structure Standards

When generating Flask applications, agents MUST follow this **exact directory structure**:

### ✅ Correct Structure

```
generated_code/
└── flask_app/                    ← Application root directory
    ├── app.py                    ← Main Flask application (MUST be here!)
    ├── requirements.txt          ← Python dependencies
    ├── README.md                 ← Documentation (optional)
    ├── templates/                ← Jinja2 templates directory
    │   ├── index.html
    │   ├── base.html
    │   └── ...
    ├── static/                   ← Static assets (optional)
    │   ├── css/
    │   ├── js/
    │   └── images/
    └── config.py                 ← Configuration (optional)
```

### ❌ Common Mistakes to AVOID

**WRONG: app.py inside templates/**
```
flask_app/
└── templates/
    ├── app.py          ❌ WRONG LOCATION!
    └── index.html
```

**WRONG: Missing flask_app subdirectory**
```
generated_code/
├── app.py              ❌ Should be in flask_app/
└── templates/
```

### File Path Validation Rules

When using the `Write` tool, agents must verify:

1. **app.py location**:
   - ✅ CORRECT: `/path/to/generated_code/flask_app/app.py`
   - ❌ WRONG: `/path/to/generated_code/flask_app/templates/app.py`
   - ❌ WRONG: `/path/to/generated_code/app.py`

2. **Templates location**:
   - ✅ CORRECT: `/path/to/generated_code/flask_app/templates/*.html`
   - ❌ WRONG: `/path/to/generated_code/templates/*.html`

3. **Static files location** (if needed):
   - ✅ CORRECT: `/path/to/generated_code/flask_app/static/css/style.css`
   - ❌ WRONG: `/path/to/generated_code/static/css/style.css`

### Why This Matters

Incorrect file structure causes:
- ❌ Application won't run (`python app.py` fails)
- ❌ Flask can't find templates (TemplateNotFound errors)
- ❌ Static files return 404 errors
- ❌ Imports fail
- ❌ Deployment issues

### Verification Steps

After file creation, agents should verify structure:

```bash
# Check that app.py exists at root level
ls flask_app/app.py

# Check templates directory
ls flask_app/templates/

# Verify structure
find flask_app -type f | sort
```

**Expected output:**
```
flask_app/app.py
flask_app/requirements.txt
flask_app/templates/index.html
```

### Code Reviewer Responsibility

The **@code-reviewer** agent MUST:
1. Verify all files are in correct locations
2. Check that `app.py` is NOT inside `templates/` or `static/`
3. Validate directory structure matches Flask conventions
4. Flag any misplaced files immediately

## Quality Assurance Checklist

Before committing changes:

- [ ] Code passes `flake8` linting (no errors)
- [ ] All functions have type hints
- [ ] Docstrings added for new functions
- [ ] Error handling implemented with logging
- [ ] Manual testing completed successfully
- [ ] No hardcoded paths or API keys
- [ ] Environment variables used for configuration
- [ ] Logging statements added at appropriate levels
- [ ] README updated if new features added
- [ ] CLAUDE.md updated if agent behavior changed

**Run Quality Checks**:
```bash
# PEP 8 compliance
flake8 flask_agent.py --max-line-length=88

# Type checking (if mypy installed)
mypy flask_agent.py

# Test orchestrators
python flask_agent.py
python airflow/airflow_agent.py
```

## Troubleshooting Development Issues

### Issue: "ModuleNotFoundError: No module named 'claude_agent_sdk'"
**Solution**: 
```bash
pip install -r requirements.txt
# or
pip install claude-agent-sdk
```

### Issue: "API key not found" errors
**Solution**:
1. Create `.env` file: `cp .env.example .env`
2. Add API key: `ANTHROPIC_API_KEY=your-key-here`
3. Verify file is in project root

### Issue: Agent not using correct tools
**Solution**: Check `allowed_tools` in `AgentDefinition` matches tools needed in prompt

### Issue: Files created in wrong directory
**Solution**: Verify `cwd` in `ClaudeAgentOptions` points to desired output directory

### Issue: Prompt not loading
**Solution**: 
- Check prompt file path is correct
- Verify markdown syntax in prompt file
- Add debug logging: `logger.debug(f"Loading: {prompt_path}")`

### Issue: Logging not working
**Solution**:
- Check `LOG_LEVEL` environment variable
- Ensure `logs/` directory exists
- Verify `LogConfig.setup_logging()` is called

## Contributing Guidelines

### Adding New Features

1. **Discuss First**: Open an issue to discuss the feature
2. **Branch**: Create a feature branch (`feature/new-agent` or `fix/bug-description`)
3. **Document**: Update README and CLAUDE.md
4. **Test**: Add test coverage if applicable
5. **Lint**: Ensure code passes flake8
6. **PR**: Submit pull request with clear description

### Code Review Checklist

When reviewing PRs:
- [ ] Code follows PEP 8 standards
- [ ] All new functions have type hints and docstrings
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate and informative
- [ ] No hardcoded credentials or paths
- [ ] Tests pass (if tests exist)
- [ ] Documentation is updated
- [ ] Changes are backward compatible

## Project Roadmap

### Current Focus Areas
- [ ] Stabilize Airflow agent orchestration (currently beta)
- [ ] Add comprehensive test suite
- [ ] Improve error handling and recovery
- [ ] Add metrics and performance monitoring

### Future Enhancements
- [ ] Support for Django and FastAPI frameworks
- [ ] Database integration agents
- [ ] Testing framework orchestration (pytest, unittest)
- [ ] CI/CD pipeline generation agents
- [ ] Docker containerization agent
- [ ] API documentation generation
- [ ] Deployment orchestration (AWS, GCP, Azure)

## Resources

### Official Documentation
- [Claude Agent SDK Python Docs](https://docs.claude.com/en/api/agent-sdk/python)
- [Claude Agent SDK GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Anthropic API Reference](https://docs.anthropic.com/)

### Project Documentation
- `README.md`: Project overview and usage
- `flask_CLAUDE.md`: Flask-specific orchestration guidelines
- `airflow/README_AIRFLOW_AGENT.md`: Airflow agent documentation
- `examples/README.md`: Links to SDK examples

### Dependencies Documentation
- [Rich Library](https://github.com/Textualize/rich): Terminal formatting
- [Loguru](https://github.com/Delgan/loguru): Advanced logging
- [python-dotenv](https://github.com/theskumar/python-dotenv): Environment configuration

## Success Criteria for Development

A successful contribution/change includes:
- ✅ Code follows all standards in this document
- ✅ Comprehensive error handling and logging
- ✅ Type hints and docstrings for all functions
- ✅ flake8 compliance with no errors
- ✅ Manual testing completed successfully
- ✅ Documentation updated appropriately
- ✅ No breaking changes to existing functionality
- ✅ Environment variables used (no hardcoded config)
- ✅ Changes are production-ready quality

---

**Built with Claude Agent SDK** - This project demonstrates the power of multi-agent AI orchestration. When developing, always consider how changes affect agent coordination and the overall orchestration flow.