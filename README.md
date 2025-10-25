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
  append: ${orchestrator_agent}

model: ${CLAUDE_MODEL}
main_prompt_file: prompts/main-query.md
cwd: ${output_dir}

agents:
  flask-developer:
    description: "Backend Flask development"
    prompt: prompts/flask-developer.md
    tools: [Read, Write, Edit, Bash]
    model: haiku

  frontend-developer:
    description: "Frontend and UI development"
    prompt: prompts/frontend-developer.md
    tools: [Read, Write, Edit]
    model: haiku

  code-reviewer:
    description: "Code quality and best practices"
    prompt: prompts/code-reviewer.md
    tools: [Read, Grep, Glob, Bash]
    model: haiku

allowed_tools: [Read, Write, Edit, Bash, Grep, Glob]
permission_mode: acceptEdits
```

**Variable Substitution:**
- `${project_root}` - Project root directory
- `${output_dir}` - Output directory (default: `generated_code/`)
- `${CLAUDE_MODEL}` - Model from environment variable
- `${orchestrator_agent}` - System orchestration prompt

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
| `@dag-architect` | DAG architecture and design | Read, Grep, Glob |
| `@dag-developer` | DAG implementation | Read, Write, Edit, Bash, Grep |
| `@migration-specialist` | Airflow 1.x to 2.x migration | Read, Write, Edit, Grep, Glob |
| `@airflow-code-reviewer` | Airflow best practices | Read, Grep, Glob |

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
│   └── config_loader.py        # YAML configuration
├── yaml_files/                  # Agent configurations
│   ├── flask_agent_options.yaml
│   └── airflow_agent_options.yaml
├── prompts/                     # Agent role definitions
│   ├── flask-developer.md
│   ├── frontend-developer.md
│   └── airflow_prompts/
├── util/                        # Utilities
│   ├── log_set.py              # Logging
│   └── helpers.py              # Display utilities
├── examples/                    # SDK examples
├── logs/                        # Application logs
└── generated_code/             # Output directory
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

Options:
  --config, -c CONFIG    Path to YAML configuration file
  --context CONTEXT      JSON string with context variables
  --task, -t TASK        Task description (skips interactive prompt)
  --version, -v          Show version and exit
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
- **[flask_CLAUDE.md](flask_CLAUDE.md)** - Flask orchestrator system prompt
- **[dag_CLAUDE_v2.md](dag_CLAUDE_v2.md)** - Airflow orchestrator system prompt
- **[examples/](examples/)** - Official Claude Agent SDK examples
- **[docs/archive/](docs/archive/)** - Historical documentation

## Dependencies

```
claude-agent-sdk>=0.1.0   # Core orchestration framework
rich>=13.0.0              # Terminal formatting
loguru>=0.7.0             # Advanced logging
python-dotenv>=1.0.0      # Environment configuration
pyyaml>=6.0.0             # YAML parsing
pytz>=2023.0              # Timezone support
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
