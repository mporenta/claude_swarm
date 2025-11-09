# Claude Swarm - Project Structure

## Directory Layout

```
claude_swarm/
├── main.py                             # 🎯 Main entry point
├── src/                                # 📦 Core application code
│   ├── __init__.py                     # Package initialization
│   ├── orchestrator.py                 # Orchestration logic
│   └── config_loader.py                # YAML configuration loading
├── util/                               # 🔧 Shared utilities
│   ├── __init__.py
│   ├── helpers.py                      # Helper functions (display, load prompts)
│   └── log_set.py                      # Logging configuration
├── yaml_files/                         # ⚙️ Configuration files
│   ├── flask_agent_options.yaml        # Flask configuration
│   └── airflow_agent_options.yaml      # Airflow configuration
├── prompts/                            # 📝 Agent prompt definitions
│   ├── main-query.md                   # Flask main prompt
│   ├── flask-developer.md              # Flask backend agent
│   ├── frontend-developer.md           # Frontend agent
│   ├── code-reviewer.md                # Code review agent
│   └── airflow_prompts/
│       ├── main-query-airflow.md       # Airflow main prompt
│       ├── dag-architect.md            # DAG architecture agent
│       ├── dag-developer.md            # DAG development agent
│       ├── migration-specialist.md     # Airflow 1→2 migration agent
│       └── airflow-code-reviewer.md    # Airflow code review agent
├── generated_code/                     # 📂 Output directory
├── logs/                               # 📋 Application logs
├── airflow/                            # 🌬️ Airflow DAG examples
│   ├── data-airflow-2/
│   └── data-airflow-legacy/
├── examples/                           # 💡 Example scripts
├── dev/                                # 🧪 Development files
├── tests/                              # 🧪 Test files (future)
├── docs/                               # 📚 Documentation
├── .env                                # 🔐 Environment variables (not in git)
├── .env.example                        # Template for .env
├── requirements.txt                    # 📦 Python dependencies
├── README.md                           # Project overview
├── CLAUDE.md                           # Claude Code instructions
├── flask_CLAUDE.md                     # Flask orchestrator instructions
├── dag_CLAUDE_v2.md                    # Airflow orchestrator instructions
└── SWARM_ORCHESTRATOR_README.md        # Usage guide
```

---

## Core Components

### 1. Entry Point: `main.py`

**Purpose**: Application entry point that handles CLI arguments and initialization

**Responsibilities**:
- Parse command-line arguments
- Load environment variables
- Initialize orchestrator
- Handle top-level errors
- Provide `--help`, `--version` commands

**Usage**:
```bash
python main.py --config yaml_files/flask_agent_options.yaml
python main.py --task "Create a Flask app"
python main.py  # Interactive mode
```

---

### 2. Core Application: `src/`

#### `src/orchestrator.py`

**Purpose**: Main orchestration logic

**Classes**:
- `SwarmOrchestrator`: Coordinates multi-agent workflows
  - Loads configuration from YAML
  - Manages Claude SDK client
  - Handles agent delegation
  - Tracks metrics (iterations, cost, time)
  - Displays results

**Functions**:
- `list_available_configs()`: Find YAML configs
- `interactive_config_selection()`: Menu-based selection

#### `src/config_loader.py`

**Purpose**: Load and parse YAML configurations

**Functions**:
- `load_agent_options_from_yaml()`: Main loader
  - Parses YAML file
  - Applies variable substitution
  - Creates AgentDefinition objects
  - Returns ClaudeAgentOptions

- `_apply_context()`: Recursive variable substitution
- `_build_agent_definitions()`: Convert YAML to AgentDefinition

#### `src/__init__.py`

**Purpose**: Package initialization and exports

**Exports**:
```python
from src import SwarmOrchestrator, load_agent_options_from_yaml
```

---

### 3. Utilities: `util/`

#### `util/helpers.py`

**Purpose**: Shared helper functions

**Functions**:
- `load_markdown_for_prompt()`: Load markdown files
- `display_message()`: Rich terminal output
- Other display utilities

#### `util/log_set.py`

**Purpose**: Logging configuration

**Classes**:
- `LogConfig`: Centralized logging setup
  - Daily rotating logs
  - Separate error logs
  - Debug mode support

**Exports**:
```python
from util.log_set import logger
```

---

### 4. Configuration: `yaml_files/`

**Purpose**: YAML configuration files for different frameworks

**Structure**:
```yaml
system_prompt: ...
model: ...
agents:
  agent-name:
    description: ...
    prompt: ...
    tools: [...]
    model: ...
allowed_tools: [...]
permission_mode: ...
```

**Files**:
- `flask_agent_options.yaml`: Flask application generation
- `airflow_agent_options.yaml`: Airflow DAG generation

---

### 5. Prompts: `prompts/`

**Purpose**: Markdown files defining agent roles and instructions

**Organization**:
```
prompts/
├── <framework>-developer.md          # Agent roles
├── main-query.md                     # Task descriptions
└── <framework>_prompts/
    └── specialized-agent.md
```

**Format**: Markdown with sections:
- Role definition
- Capabilities
- Tool access
- Guidelines
- Examples
- Constraints

---

### 6. Output: `generated_code/`

**Purpose**: Generated code and artifacts

**Structure** (created dynamically):
```
generated_code/
├── flask_app/
│   ├── app.py
│   ├── templates/
│   └── requirements.txt
└── airflow_dag/
    ├── src/
    └── daily.py
```

---

## Import Structure

### Absolute Imports (Preferred)

```python
# From root (main.py)
from src.orchestrator import SwarmOrchestrator
from src.config_loader import load_agent_options_from_yaml
from util.log_set import logger
from util.helpers import display_message

# From src/
from src.config_loader import load_agent_options_from_yaml
from util.helpers import load_markdown_for_prompt

# From anywhere
from util.log_set import logger
```

### Why This Structure?

1. **Separation of Concerns**:
   - `main.py`: CLI and initialization
   - `src/`: Core business logic
   - `util/`: Reusable utilities

2. **Standard Python Layout**:
   - Follows PEP conventions
   - Easy to package (`pip install -e .`)
   - Clear entry point

3. **Testability**:
   - Core logic in `src/` is easily testable
   - Utilities in `util/` can be tested independently
   - Entry point (`main.py`) is thin

4. **Extensibility**:
   - Add new modules to `src/`
   - Keep utilities in `util/`
   - Configuration in `yaml_files/`

---

## Running the Application

### Development

```bash
# From project root
python main.py

# With specific config
python main.py --config yaml_files/flask_agent_options.yaml

# With task
python main.py --config yaml_files/airflow_agent_options.yaml \
  --task "Migrate marketo_to_snowflake.py"
```

### Production

```bash
# Make executable
chmod +x main.py

# Run directly
./main.py --config yaml_files/flask_agent_options.yaml
```

### As Module

```bash
# Install in development mode
pip install -e .

# Import in Python
python
>>> from src import SwarmOrchestrator
>>> orchestrator = SwarmOrchestrator("config.yaml")
```

---

## Environment Setup

### Required Files

1. **`.env`** (not in git):
```bash
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=sonnet
LOG_LEVEL=INFO
```

2. **`.env.example`** (template):
```bash
ANTHROPIC_API_KEY=your-api-key-here
CLAUDE_MODEL=sonnet
LOG_LEVEL=INFO
```

### Dependencies

Install from `requirements.txt`:
```bash
pip install -r requirements.txt
```

**Core dependencies**:
- `claude-agent-sdk`: Claude Agent SDK
- `python-dotenv`: Environment variables
- `rich`: Terminal formatting
- `pyyaml`: YAML parsing

---

## Adding New Features

### Add New Framework Configuration

1. **Create YAML config**:
   ```bash
   touch yaml_files/terraform_agent_options.yaml
   ```

2. **Define agents**:
   ```yaml
   agents:
     terraform-architect:
       description: "Terraform infrastructure architect"
       prompt: prompts/terraform_prompts/architect.md
       tools: [Read, Grep, Glob]
       model: haiku
   ```

3. **Create prompt files**:
   ```bash
   mkdir -p prompts/terraform_prompts
   touch prompts/terraform_prompts/architect.md
   ```

4. **Run**:
   ```bash
   python main.py --config yaml_files/terraform_agent_options.yaml
   ```

### Add New Utility

1. **Create in `util/`**:
   ```bash
   touch util/my_utility.py
   ```

2. **Import in code**:
   ```python
   from util.my_utility import my_function
   ```

### Add New Core Module

1. **Create in `src/`**:
   ```bash
   touch src/my_module.py
   ```

2. **Export in `src/__init__.py`**:
   ```python
   from src.my_module import MyClass
   __all__.append("MyClass")
   ```

3. **Import**:
   ```python
   from src import MyClass
   ```

---

## Testing Structure (Future)

```
tests/
├── __init__.py
├── test_orchestrator.py        # Test SwarmOrchestrator
├── test_config_loader.py       # Test YAML loading
├── test_helpers.py             # Test utilities
├── fixtures/
│   ├── test_config.yaml
│   └── test_prompt.md
└── conftest.py                 # Pytest configuration
```

**Run tests**:
```bash
pytest tests/
pytest tests/test_orchestrator.py -v
```

---

## Documentation Structure

```
docs/
├── architecture.md             # System architecture
├── configuration.md            # YAML configuration guide
├── agents.md                   # Agent development guide
├── api.md                      # API reference
└── examples/
    ├── flask.md
    └── airflow.md
```

---

## Git Workflow

### Ignored Files (`.gitignore`)

```
.env
__pycache__/
*.pyc
logs/
generated_code/
.venv/
.pytest_cache/
```

### Tracked Files

```
✅ main.py
✅ src/
✅ util/
✅ yaml_files/
✅ prompts/
✅ requirements.txt
✅ README.md
✅ .env.example
```

---

## Backwards Compatibility

### Old Entry Points (Deprecated)

These still work but will be removed:

```bash
# Old way (deprecated)
python swarm_orchestrator.py --config config.yaml
python flask_agent_main.py

# New way (preferred)
python main.py --config config.yaml
```

### Migration Path

1. **Phase 1** (current): Both old and new work
2. **Phase 2** (next): Add deprecation warnings
3. **Phase 3** (future): Remove old entry points

---

## Summary

### Standard Pythonic Structure ✅

- ✅ Clear entry point (`main.py`)
- ✅ Core logic in `src/` package
- ✅ Shared utilities in `util/`
- ✅ Configuration in `yaml_files/`
- ✅ Tests in `tests/` (future)
- ✅ Docs in `docs/` (future)

### Benefits

1. **Professional**: Follows Python best practices
2. **Maintainable**: Clear separation of concerns
3. **Testable**: Easy to write unit tests
4. **Extensible**: Simple to add new features
5. **Packageable**: Can be installed with `pip`

### Quick Start

```bash
# Clone and setup
git clone <repo>
cd claude_swarm
pip install -r requirements.txt
cp .env.example .env  # Add API key

# Run
python main.py

# Or with config
python main.py --config yaml_files/flask_agent_options.yaml
```

**Ready to use!** 🚀
