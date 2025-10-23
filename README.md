# Claude Swarm Agent Orchestration System

A sophisticated AI-powered code generation framework that orchestrates multiple specialized Claude agents to collaborate on web application development. Built on the Claude Agent SDK, this system demonstrates advanced multi-agent coordination for automated Flask application generation.

## Overview

Claude Swarm uses an orchestrator pattern where different AI agents with specialized expertise work together on complex development tasks. Each agent has specific roles, tool access, and capabilities, enabling efficient collaboration on backend development, frontend design, and code quality assurance.

## Claude Doc

- Refer to the documentation here for the [Claude Agent Python SDK](https://docs.claude.com/en/api/agent-sdk/python)
- Check out the [Github Repo](https://github.com/anthropics/claude-agent-sdk-python)

## Features

- **Multi-Agent Orchestration**: Coordinate specialized AI agents for different development tasks
- **Dynamic Prompt Loading**: Markdown-based agent role definitions loaded at runtime
- **Interactive CLI**: Rich terminal interface with conversation history and metrics
- **Comprehensive Logging**: Timezone-aware logging with automatic rotation and retention
- **Production-Ready Code**: Generates Flask applications following best practices
- **Flexible Configuration**: Project-level settings and environment variable support
- **Tool-Based Access Control**: Fine-grained permissions for file operations and code execution

## Architecture

### Directory Structure

```
claude_swarm/
├── Core Orchestration
│   └── flask_agent.py           # Main Flask orchestrator with conversation loop
│
├── Airflow Orchestration
│   └── airflow/
│       ├── airflow_agent.py     # Airflow DAG orchestrator
│       ├── README_AIRFLOW_AGENT.md # Airflow agent documentation
│       ├── CREATION_SUMMARY.md  # DAG creation summary
│       ├── COMPARISON.md        # Migration comparison
│       └── airflow_CLAUDE.md    # Airflow guidelines
│
├── Development & Testing
│   └── dev/
│       ├── client_query.py      # Alternative orchestrator with CLAUDE.md support
│       ├── flask_app_dev.py     # Flask development orchestrator
│       ├── test_dev.py          # Advanced code generation orchestrator
│       └── basic_CLAUDE_fib.md  # Fibonacci implementation example
│
├── Prompts & Agent Definitions
│   └── prompts/
│       ├── main-query.md        # Main orchestration prompt
│       ├── flask-developer.md   # Backend developer agent role
│       ├── frontend-developer.md # Frontend developer agent role
│       ├── code-reviewer.md     # Code reviewer agent role
│       └── airflow_prompts/     # Airflow-specific agent prompts
│           ├── airflow-orchestrator.md
│           ├── dag-architect.md
│           ├── dag-developer.md
│           ├── migration-specialist.md
│           └── airflow-code-reviewer.md
│
├── Utilities
│   └── util/
│       ├── log_set.py           # Centralized logging configuration
│       └── helpers.py           # Display and markdown loading utilities
│
├── Examples
│   └── examples/                # 12 official Claude Agent SDK examples
│       ├── quick_start.py
│       ├── agents.py
│       ├── streaming_mode.py
│       └── README.md            # Links to official SDK examples
│
├── Configuration
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Example environment variables
│   ├── CLAUDE.md                # Core agent orchestration guidelines
│   ├── flask_CLAUDE.md          # Flask orchestration guidelines
│   ├── pyproject.toml           # Project metadata
│   └── .gitignore               # Git ignore patterns
│
├── Logs
│   └── logs/                    # Application logs (date-stamped)
│
└── Output
    └── generated_code/          # Generated applications (Flask, Airflow DAGs)
        ├── app.py               # (Generated on demand)
        ├── requirements.txt     # (Generated on demand)
        └── templates/           # (Generated on demand)
            └── index.html
```

## Available Agents

### @flask-developer
- **Purpose**: Backend Flask development expert
- **Tools**: Read, Write, Edit, Bash
- **Capabilities**:
  - Flask application architecture
  - API endpoint creation
  - Server configuration
  - Backend business logic
  - Python best practices (PEP 8)

### @frontend-developer
- **Purpose**: Frontend and template development expert
- **Tools**: Read, Write, Edit
- **Capabilities**:
  - HTML5 semantic markup
  - Modern CSS styling (flexbox, gradients, animations)
  - Responsive design (mobile, tablet, desktop)
  - Jinja2 templating
  - UI/UX best practices

### @code-reviewer
- **Purpose**: Code quality and security specialist
- **Tools**: Read, Grep, Glob
- **Capabilities**:
  - Code quality analysis
  - Security vulnerability detection
  - PEP 8 compliance verification
  - flake8 linting execution
  - Best practices validation

## Airflow Agents (Beta)
**Yes, the Airflow Agents are Beta...**

### @dag-architect
- **Purpose**: Airflow DAG architecture and design expert
- **Tools**: Read, Grep, Glob
- **Capabilities**:
  - DAG structure design
  - Task dependency planning
  - Scheduling and configuration
  - Best practices for Airflow workflows

### @dag-developer
- **Purpose**: Airflow DAG implementation specialist
- **Tools**: Read, Write, Edit, Bash, Grep
- **Capabilities**:
  - DAG code implementation
  - Task creation and configuration
  - Operator selection and usage
  - Connection and variable management

### @migration-specialist
- **Purpose**: Airflow 1.0 to 2.0 migration expert
- **Tools**: Read, Write, Edit, Grep, Glob
- **Capabilities**:
  - Legacy code analysis
  - Migration path planning
  - Code modernization
  - Compatibility issue resolution

### @airflow-code-reviewer
- **Purpose**: Airflow-specific code quality reviewer
- **Tools**: Read, Grep, Glob
- **Capabilities**:
  - Airflow best practices verification
  - DAG structure validation
  - Performance optimization
  - Security and compliance checks

## Installation

### Prerequisites
- Python 3.8+
- Claude API access (Anthropic API key)

### Setup

```bash
# Clone the repository
cd {root_path}/claude_swarm

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (REQUIRED)
# Copy the example .env file and add your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Or set environment variables manually
export ANTHROPIC_API_KEY="your-api-key-here"
export LOG_LEVEL=DEBUG
export SET_DEBUG=false
```

### Environment Configuration

The system requires a `.env` file in the project root directory with your Anthropic API key. This is **mandatory** for the Claude Agent SDK to function.

**Required Environment Variables:**
- `ANTHROPIC_API_KEY` - Your Anthropic API key (obtain from https://console.anthropic.com/)

**Optional Environment Variables:**
- `LOG_LEVEL` - Logging verbosity: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `SET_DEBUG` - Enable debug output: true/false (default: false)
- `CLAUDE_MODEL` - Model selection: sonnet, opus, haiku (default: sonnet)
- `FLASK_ENV` - Flask environment: development, production (default: development)
- `FLASK_PROJECT_PATH` - Custom path for Flask generated code
- `AIRFLOW_HOME` - Airflow installation directory
- `AIRFLOW__CORE__DAGS_FOLDER` - Airflow DAGs folder location

See [.env.example](.env.example) for a complete template.

### Dependencies

```
claude-agent-sdk>=0.1.0   # Core SDK for agent orchestration
rich>=13.0.0              # Terminal formatting and output
loguru>=0.7.0             # Advanced logging
python-dotenv>=1.0.0      # Environment configuration
pytz>=2023.0              # Timezone support
tzlocal>=5.0.0            # Local timezone detection
anyio>=4.0.0              # Async I/O support
```

## Usage

### Interactive Mode

Run the main orchestrator with an interactive conversation loop using the Flask App `Hello World` example:

```bash
python flask_agent.py
```

**Available Commands:**
- `flask` - Trigger Flask app generation orchestration
- `exit` - Quit the session
- `interrupt` - Stop current task execution
- `new` - Start a fresh conversation session

### Airflow Mode

Run the Airflow orchestrator for DAG creation and migration:

```bash
cd airflow
python airflow_agent.py
```

**Available Commands:**
- `create-dag` - Create a new Airflow DAG
- `migrate-dag` - Migrate Airflow 1.0 DAG to 2.0
- `exit` - Quit the session
- `interrupt` - Stop current task execution
- `new` - Start a fresh conversation session

### Programmatic Usage

```python
from flask_agent import ConversationSession
import asyncio

async def generate_flask_app():
    session = ConversationSession()
    await session.initialize()
    await session.flask_app_orchestrator()

asyncio.run(generate_flask_app())
```

### Agent Delegation Syntax

Use `@agent-name` to delegate tasks to specific agents:

```python
# Example orchestration workflow
"""
@flask-developer Create a Flask app that:
- Runs on port 5010
- Has route '/' for homepage
- Generates random styling values

@frontend-developer Create templates/index.html that:
- Displays "Hello World"
- Uses Flask template variables for dynamic styling
- Has responsive, modern design

@code-reviewer Review all files and:
- Run flake8 on Python files
- Check code quality standards
- Verify project structure
"""
```

## Generated Flask Application

The orchestration system generates a complete Flask application with:

### app.py
- **Port**: 5010
- **Route**: Single `'/'` homepage
- **Features**:
  - Random text color (8 color options)
  - Random font size (20px-100px range)
  - Random font family (6 font options)
  - Error handlers (404, 500)
  - Type hints and docstrings
  - Production-ready structure

### templates/index.html
- **HTML5 structure** with semantic elements
- **Modern CSS**:
  - Gradient animated background
  - Glass-morphism card design
  - Responsive breakpoints (mobile, tablet, desktop)
  - Accessibility features (prefers-reduced-motion)
  - Print-friendly styles
- **Dynamic Styling**: Uses Flask template variables for randomization

### requirements.txt
- Flask with version specification
- All necessary dependencies (Werkzeug, Jinja2, etc.)

## Orchestration Patterns

### Pattern 1: Sequential Development
```
@flask-developer → Backend logic
    ↓
@frontend-developer → UI/templates
    ↓
@code-reviewer → Quality assurance
```

### Pattern 2: Iterative Refinement
```
@flask-developer → Initial implementation
    ↓
@code-reviewer → Review and suggest improvements
    ↓
@flask-developer → Implement improvements
    ↓
@code-reviewer → Final verification
```

### Pattern 3: Parallel Development
```
@flask-developer → Work on app.py (independent)
@frontend-developer → Work on templates (independent)
# Agents work simultaneously, then integrate
```

## Logging System

### LogConfig Class Features
- **Timezone-aware logging**: Auto-detects local timezone
- **Multiple log levels**: DEBUG, INFO, ERROR
- **Date-stamped files**: `YYYY_MM_DD_*.log` format
- **Automatic rotation**: 10MB-100MB thresholds
- **Retention policies**: 1 week to 3 months
- **Thread-safe**: Uses `loguru` for concurrent logging

### Log Files Generated
- `app.log`: General application logs
- `error.log`: Error-specific logs with backtraces
- `debug.log`: Comprehensive debug information

## Configuration

### Agent Configuration Options

```python
ClaudeAgentOptions(
    setting_sources=["project"],
    cwd="{root_path}/claude_swarm/generated_code",
    agents={
        "flask-developer": AgentDefinition(...),
        "frontend-developer": AgentDefinition(...),
        "code-reviewer": AgentDefinition(...)
    },
    allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
    permission_mode="acceptEdits"
)
```

## Code Quality Standards

### Python Standards (PEP 8)
- Type hints for all functions
- Meaningful variable names
- Comprehensive docstrings
- Proper error handling
- flake8 compliance

### Flask Standards
- Port 5010 specification
- Jinja2 templating best practices
- Error handlers (404, 500)
- Security considerations
- Production-ready structure

### HTML/CSS Standards
- Semantic HTML5 elements
- Responsive design principles
- Modern CSS (flexbox, animations, gradients)
- Accessibility features
- Cross-browser compatibility

## Advanced Features

### Conversation Context
- Session-based conversation memory
- Turn counting and tracking
- Context preservation across queries
- Interrupt capability for long-running tasks

### File Generation Tracking
- Automatic detection of created files
- Path extraction from tool calls
- Summary reporting with metrics
- Cost calculation per session

### Rich Terminal Output
- Colored message types:
  - 🗣️ **Cyan**: User messages
  - 🤖 **Green**: Assistant responses
  - 💭 **Yellow**: Thinking blocks
  - 🔧 **Magenta**: Tool invocations
  - ✅ **Blue**: Tool results
- Timestamps for all messages
- Status indicators and progress tracking

## Example Workflow

```bash
$ python flask_agent.py

Turn 1: You: flask

📊 Orchestrating Flask app generation...

🔧 @flask-developer: Creating Flask application structure...
✅ Created: app.py
✅ Created: requirements.txt

🔧 @frontend-developer: Designing HTML template...
✅ Created: templates/index.html

🔧 @code-reviewer: Running code quality checks...
✅ flake8 validation passed
✅ All standards compliance verified

📈 Session Metrics:
- Files created: 3
- Tool calls: 12
- Thinking blocks: 8
- Total cost: $0.15

Turn 2: You: exit
```

## Examples and Testing

### Official SDK Examples

The `examples/` directory contains 12 example scripts from the official Claude Agent SDK that demonstrate various features:

- **quick_start.py** - Basic agent setup and usage
- **agents.py** - Multi-agent orchestration patterns
- **streaming_mode.py** - Streaming responses with asyncio
- **streaming_mode_trio.py** - Streaming with Trio async framework
- **streaming_mode_ipython.py** - Interactive IPython streaming
- **hooks.py** - Custom hooks for agent lifecycle events
- **system_prompt.py** - Custom system prompt configuration
- **setting_sources.py** - Configuration source management
- **tool_permission_callback.py** - Tool permission handling
- **stderr_callback_example.py** - Error handling callbacks
- **include_partial_messages.py** - Partial message handling
- **mcp_calculator.py** - Model Context Protocol example

See [examples/README.md](examples/README.md) for links to the official documentation.

### Development Test Orchestrators

The `dev/` directory includes advanced test orchestrators:

#### dev/test_dev.py
Demonstrates 4-agent orchestration with:
1. **code-generator**: Feature implementation
2. **test-generator**: Test suite creation
3. **code-reviewer**: Quality assurance
4. **refactoring-specialist**: Code improvement

Includes 5-phase workflow:
1. Analysis Phase
2. Code Generation Phase
3. Test Generation Phase
4. Review Phase
5. Verification Phase

#### dev/client_query.py
Alternative orchestrator that supports CLAUDE.md guidelines for custom project workflows.

#### dev/flask_app_dev.py
Development version of Flask orchestrator with additional debugging and testing features.

## Troubleshooting

### Issue: "API key not found" or authentication errors
**Solution**:
1. Ensure you have created a `.env` file in the project root
2. Copy from `.env.example`: `cp .env.example .env`
3. Add your Anthropic API key to the `.env` file
4. Verify the key is valid at https://console.anthropic.com/

### Issue: Agent doesn't have required tool access
**Solution**: Check agent definition - ensure the agent has necessary tools (e.g., `code-reviewer` needs Read, Grep, Glob)

### Issue: Agents working on conflicting files
**Solution**: Delegate sequentially or assign different file responsibilities

### Issue: Unclear which agent to use for Flask
**Solution**:
- Python/Flask/Backend → `@flask-developer`
- HTML/CSS/Templates → `@frontend-developer`
- Linting/Review/Quality → `@code-reviewer`

### Issue: Unclear which agent to use for Airflow
**Solution**:
- DAG Architecture/Design → `@dag-architect`
- DAG Implementation → `@dag-developer`
- Airflow 1.0 to 2.0 Migration → `@migration-specialist`
- Code Review/Best Practices → `@airflow-code-reviewer`

### Issue: Import errors or missing dependencies
**Solution**: Reinstall requirements: `pip install -r requirements.txt`

### Issue: Logging files not being created
**Solution**: Check `LOG_LEVEL` environment variable and ensure the `logs/` directory exists

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Code Style**: Follow PEP 8 for Python code
2. **Logging**: Use the LogConfig class for all logging
3. **Agent Definitions**: Add new agents in `prompts/` directory
4. **Documentation**: Update README for new features
5. **Testing**: Test orchestration workflows thoroughly

## Project Roadmap

- [ ] Add support for additional web frameworks (Django, FastAPI)
- [ ] Implement database integration agents
- [ ] Add testing framework orchestration (pytest, unittest)
- [ ] Create CI/CD pipeline generation
- [ ] Add Docker containerization agent
- [ ] Implement API documentation generation
- [ ] Add deployment orchestration (AWS, GCP, Azure)

## License

See [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Claude Agent SDK](https://docs.anthropic.com/claude/docs)
- Uses [Rich](https://github.com/Textualize/rich) for terminal formatting
- Logging powered by [Loguru](https://github.com/Delgan/loguru)

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Review the `flask_CLAUDE.md` and `airflow_CLAUDE.md` for specific guidelines
- Check agent definitions in `prompts/` directory

## Success Criteria

A successful Flask app generation includes:
- ✅ Clean, well-structured Flask application
- ✅ Properly templated HTML with dynamic styling
- ✅ All files pass flake8 linting
- ✅ Requirements.txt with correct dependencies
- ✅ Code follows best practices
- ✅ Professional, production-ready quality
- ✅ All files in correct directory structure

---

**Built with Claude Agent SDK** - Demonstrating the power of multi-agent AI orchestration for automated code generation.
