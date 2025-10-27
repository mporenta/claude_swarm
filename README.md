# Claude Swarm

Multi-agent orchestration system for automated code generation using the Claude Agent SDK. Coordinate specialized AI agents for Flask applications, Airflow DAGs, and other development tasks.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Claude Agent SDK](https://img.shields.io/badge/Claude-Agent%20SDK-blueviolet)](https://docs.claude.com/en/api/agent-sdk/python)

## Features

- **YAML-Driven Configuration** - Define agents and workflows in configuration files
- **Multi-Agent Orchestration** - Specialized agents collaborate on complex tasks
- **Framework Support** - Flask applications, Airflow DAGs (extensible to other frameworks)
- **Interactive CLI** - Rich terminal interface with real-time metrics
- **Programmatic API** - Use as a library in your Python applications

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/mporenta/claude_swarm.git
cd claude_swarm

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Basic Usage

```bash
# Interactive mode - select configuration from menu
python main.py

# Flask application generation
python main.py --config yaml_files/flask_agent_options.yaml

# Airflow DAG generation
python main.py --config yaml_files/airflow_agent_options.yaml

# Specify task directly
python main.py --config yaml_files/flask_agent_options.yaml \
  --task "Create a REST API for user management"
```

## Configuration

### Environment Variables

**Required:**
- `ANTHROPIC_API_KEY` - Get from [Anthropic Console](https://console.anthropic.com/)

**Optional:**
- `CLAUDE_MODEL` - Model: `sonnet`, `opus`, `haiku` (default: `sonnet`)
- `LOG_LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)

### YAML Configuration

Create framework-specific configurations in `yaml_files/`:

```yaml
# Example: yaml_files/flask_agent_options.yaml
system_prompt:
  type: preset
  preset: claude_code
  append: "{orchestrator_agent}"

model: "{CLAUDE_MODEL}"
main_prompt_file: prompts/main-flask-app-query.md
setting_sources:
  - project
cwd: "{output_dir}"
add_dirs:
  - "{project_root}"
env:
  FLASK_ENV: development
  FLASK_PROJECT_PATH: "{output_dir}"
  PROJECT_ROOT: "{project_root}"
  OUTPUT_DIR: "{output_dir}"

agents:
  flask-developer:
    description: "Expert Flask developer for backend development."
    prompt: prompts/flask-developer.md
    tools:
      - Read
      - Write
      - Edit
      - Bash
    model: haiku

  frontend-developer:
    description: "Expert frontend developer for HTML/CSS/JavaScript."
    prompt: prompts/frontend-developer.md
    tools:
      - Read
      - Write
      - Edit
    model: haiku

  code-reviewer:
    description: "Code review specialist for Flask best practices and quality."
    prompt: prompts/code-reviewer.md
    tools:
      - Read
      - Grep
      - Glob
      - Bash
    model: haiku

allowed_tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
permission_mode: acceptEdits
```

**Variable Substitution:**
- `"{project_root}"` - Project root directory
- `"{output_dir}"` - Output directory (default: `generated_code/`)
- `"{CLAUDE_MODEL}"` - Model from environment variable (sonnet/opus/haiku)
- `"{orchestrator_agent}"` - System orchestration prompt
- `"{airflow_2_dags_dir}"` - Airflow 2.x DAGs directory (Airflow configs)
- `"{airflow_legacy_dags_dir}"` - Legacy Airflow 1.x DAGs directory (Airflow configs)

**Available Configurations in yaml_files/:**
- `flask_agent_options.yaml` - Flask application development
- `airflow_agent_options.yaml` - Airflow DAG development
- `airflow_agent_options_frontmatter.yaml` - Airflow with frontmatter support
- `airflow_agent_options_local.yaml` - Airflow with local development settings

## Available Agents

### Flask Development

| Agent | Purpose | Tools |
|-------|---------|-------|
| `@flask-developer` | Backend Flask development | Read, Write, Edit, Bash |
| `@frontend-developer` | Frontend and templates | Read, Write, Edit |
| `@code-reviewer` | Code quality validation | Read, Grep, Glob, Bash |

### Airflow Development

| Agent | Purpose | Tools |
|-------|---------|-------|
| `@dag-developer` | Airflow 2.x DAG implementation | Read, Write, Edit, Bash, Grep |
| `@migration-specialist` | Airflow 1.x to 2.x migration | Read, Write, Edit, Grep, Glob |
| `@airflow-code-reviewer` | Airflow best practices and compliance | Read, Grep, Glob |

## Programmatic Usage

```python
from src import SwarmOrchestrator
import asyncio

async def generate_application():
    orchestrator = SwarmOrchestrator(
        config_path="yaml_files/flask_agent_options.yaml",
        context={"output_dir": "/path/to/output"}
    )

    await orchestrator.run_orchestration(
        main_prompt="Create a Flask REST API with authentication"
    )

asyncio.run(generate_application())
```

## Project Structure

```
claude_swarm/
├── main.py                      # Entry point
├── src/                         # Core application
│   ├── orchestrator.py         # Orchestration logic
│   ├── config_loader.py        # YAML configuration
│   └── tools/                  # Custom tool implementations
├── yaml_files/                  # Agent configurations
│   ├── flask_agent_options.yaml
│   └── airflow_agent_options.yaml
├── prompts/                     # Agent role definitions
│   ├── main-flask-app-query.md
│   ├── flask-developer.md
│   ├── frontend-developer.md
│   ├── code-reviewer.md
│   ├── flask_CLAUDE.md         # Flask orchestrator system prompt
│   └── airflow_prompts/        # Airflow agent prompts
│       ├── dag-developer.md
│       ├── migration-specialist.md
│       └── airflow-code-reviewer.md
├── util/                        # Utilities
│   ├── log_set.py              # Logging configuration
│   ├── helpers.py              # Display utilities
│   └── agent_loader.py         # Agent loading helpers
├── airflow/                     # Legacy Airflow orchestrator
│   └── airflow_agent.py        # Standalone Airflow script
├── dev/                         # Development scripts
│   ├── client_query.py         # CLAUDE.md support orchestrator
│   ├── flask_app_dev.py        # Flask dev orchestrator
│   └── test_dev.py             # Advanced orchestrator
├── examples/                    # Example implementations
│   ├── flask_agent_main.py     # Flask agent example
│   ├── airflow_agent_main.py   # Airflow agent example
│   ├── swarm_orchestrator.py   # Swarm orchestration example
│   └── official_sdk_examples/  # 12 official SDK examples
├── tests/                       # Test suite
├── logs/                        # Application logs
├── generated_code/             # Output directory
└── generated_dags/             # Generated Airflow DAGs
```

## Agent Delegation

Agents are invoked using `@agent-name` syntax in orchestration prompts:

```
@flask-developer
Create a Flask application with:
- REST API endpoints for CRUD operations
- SQLAlchemy database models
- Error handling and logging

@frontend-developer
Create responsive templates with:
- Bootstrap 5 styling
- Form validation
- Dynamic content rendering

@code-reviewer
Review all code for:
- PEP 8 compliance
- Security best practices
- Performance optimization
```

## Adding New Frameworks

1. **Create YAML configuration** in `yaml_files/`
2. **Define agent prompts** in `prompts/your_framework/`
3. **Specify orchestration prompt** for main workflow
4. **Run**: `python main.py --config yaml_files/your_config.yaml`

Example for Django:

```yaml
# yaml_files/django_agent_options.yaml
model: sonnet
main_prompt_file: prompts/django_prompts/main-query.md
cwd: ${output_dir}

agents:
  django-developer:
    description: "Django application development"
    prompt: prompts/django_prompts/django-developer.md
    tools: [Read, Write, Edit, Bash]
    model: haiku
```

## Logging

Logs are automatically generated with timestamps:

- `logs/YYYY_MM_DD_app.log` - General application logs
- `logs/YYYY_MM_DD_error.log` - Error logs with tracebacks
- `logs/YYYY_MM_DD_debug.log` - Detailed debug information

Configure via `LOG_LEVEL` environment variable.

## CLI Reference

```bash
python main.py --help

Claude Swarm Multi-Agent Orchestrator

Options:
  --config, -c CONFIG    Path to YAML configuration file
  --context CONTEXT      JSON string with context variables for YAML substitution
  --task, -t TASK        Task description (overrides interactive prompt)
  --version, -v          Show version and exit (Claude Swarm 1.0.0)

Examples:
  # Use specific configuration
  python main.py --config yaml_files/airflow_agent_options.yaml

  # Interactive mode (select from available configs)
  python main.py

  # Specify custom context variables
  python main.py --config config.yaml --context '{"project": "/path/to/project"}'

  # Provide task description directly
  python main.py --config config.yaml --task "Create a Flask REST API"
```

## Troubleshooting

### API Key Errors
```bash
# Verify .env file exists
cat .env | grep ANTHROPIC_API_KEY

# Test API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Configuration Issues
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('yaml_files/flask_agent_options.yaml'))"

# Check available configurations
python main.py  # Shows interactive menu
```

## Examples

### Flask REST API
```bash
python main.py --config yaml_files/flask_agent_options.yaml \
  --task "Create a REST API with user authentication and JWT tokens"
```

### Airflow DAG Migration
```bash
python main.py --config yaml_files/airflow_agent_options.yaml \
  --task "Migrate legacy Airflow 1.x DAG to Airflow 2.x with TaskFlow API"
```

### Custom Output Directory
```bash
python main.py --config yaml_files/flask_agent_options.yaml \
  --context '{"output_dir": "/custom/path"}' \
  --task "Create a Flask application with database integration"
```

## Documentation

- **[DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)** - Troubleshooting and debugging
- **[AGENTS.md](AGENTS.md)** - Agent definitions and capabilities reference
- **[SUBAGENT_PROTOCOL_GUIDE.md](SUBAGENT_PROTOCOL_GUIDE.md)** - Subagent communication protocol
- **[prompts/flask_CLAUDE.md](prompts/flask_CLAUDE.md)** - Flask orchestrator system prompt
- **[dev/dag_CLAUDE_v2.md](dev/dag_CLAUDE_v2.md)** - Airflow orchestrator system prompt
- **[examples/official_sdk_examples/](examples/official_sdk_examples/)** - 12 official Claude Agent SDK examples
- **[docs/archive/](docs/archive/)** - Historical documentation

## Dependencies

```
claude-agent-sdk>=0.1.0   # Core orchestration framework
rich>=13.0.0              # Terminal formatting and output
loguru>=0.7.0             # Advanced logging with rotation
python-dotenv>=1.0.0      # Environment variable management
PyYAML>=6.0               # YAML configuration parsing
pytz>=2023.0              # Timezone conversions
tzlocal>=5.0.0            # Local timezone detection
anyio>=4.0.0              # Async I/O compatibility layer
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-framework`)
3. Add agents and configuration in `yaml_files/` and `prompts/`
4. Test thoroughly
5. Submit a pull request

## Resources

- [Claude Agent SDK Documentation](https://docs.claude.com/en/api/agent-sdk/python)
- [Claude Agent SDK GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Anthropic API Documentation](https://docs.anthropic.com/)

---

**Built with Claude Agent SDK** | [GitHub](https://github.com/mporenta/claude_swarm)
