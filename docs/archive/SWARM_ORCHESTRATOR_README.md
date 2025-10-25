# Claude Swarm Orchestrator - Usage Guide

## Overview

The **Swarm Orchestrator** is a generalist multi-agent system that dynamically loads configuration from YAML files. It replaces framework-specific orchestrators (like `flask_agent_main.py`) with a single flexible system.

## Key Features

✅ **Framework-Agnostic**: Works with Flask, Airflow, or any framework
✅ **YAML-Driven Configuration**: All agents, prompts, and settings in YAML
✅ **Dynamic Agent Loading**: No code changes needed for new agent types
✅ **Variable Substitution**: Use `${variable}` syntax in YAML
✅ **Interactive Mode**: Select configuration from menu
✅ **Rich Metrics**: Detailed timing, cost, and iteration tracking

---

## Quick Start

### 1. Interactive Mode (Recommended)

```bash
python swarm_orchestrator.py
```

This will:
1. Show available YAML configurations in `yaml_files/`
2. Let you select one by number
3. Prompt for task description
4. Execute orchestration with selected agents

### 2. Direct Configuration

```bash
# Airflow DAG generation
python swarm_orchestrator.py --config yaml_files/airflow_agent_options.yaml

# Flask app generation
python swarm_orchestrator.py --config yaml_files/flask_agent_options.yaml
```

### 3. With Task Argument

```bash
python swarm_orchestrator.py \
  --config yaml_files/airflow_agent_options.yaml \
  --task "Migrate the marketo_to_snowflake DAG from Airflow 1 to 2"
```

### 4. With Custom Context

```bash
python swarm_orchestrator.py \
  --config yaml_files/airflow_agent_options.yaml \
  --context '{"project_root": "/custom/path", "output_dir": "/output"}'
```

---

## YAML Configuration Structure

### Complete Example

```yaml
# System configuration
system_prompt:
  type: preset
  preset: claude_code
  append: ${orchestrator_agent}
model: ${CLAUDE_MODEL}
main_prompt_file: prompts/main-query.md

# Claude Agent SDK settings
setting_sources:
   project
cwd: ${output_dir}
add_dirs:
   ${project_root}

# Environment variables
env:
  FRAMEWORK_ENV: development
  PROJECT_ROOT: ${project_root}
  OUTPUT_DIR: ${output_dir}

# Agent definitions
agents:
  agent-name:
    description: "Brief description of agent role"
    prompt: prompts/agent-name.md
    tools:
       Read
       Write
       Edit
       Bash
       Grep
       Glob
    model: haiku

# Global settings
allowed_tools:
   Read
   Write
   Edit
   Bash
   Grep
   Glob
permission_mode: acceptEdits
```

### Configuration Sections

#### 1. System Prompt
```yaml
system_prompt:
  type: preset
  preset: claude_code
  append: ${orchestrator_agent}
```

- `preset`: Use Claude Code preset (recommended)
- `append`: Additional orchestrator instructions (from CLAUDE.md files)

#### 2. Model Selection
```yaml
model: ${CLAUDE_MODEL}  # Uses env var, defaults to "sonnet"
```

Options: `sonnet`, `opus`, `haiku`

#### 3. Main Prompt File
```yaml
main_prompt_file: prompts/main-query.md
```

The task description/instructions file. If omitted, user will be prompted interactively.

#### 4. Working Directory
```yaml
cwd: ${output_dir}
add_dirs:
   ${airflow_2_dags_dir}
   ${airflow_legacy_dags_dir}
```

- `cwd`: Where files will be created
- `add_dirs`: Additional directories agents can access

#### 5. Environment Variables
```yaml
env:
  AIRFLOW_HOME: ${project_root}
  CUSTOM_VAR: value
```

Passed to agent execution environment.

#### 6. Agent Definitions
```yaml
agents:
  dag-architect:
    description: "Expert Airflow architect"
    prompt: prompts/airflow_prompts/dag-architect.md
    tools:
       Read
       Grep
       Glob
    model: haiku
```

Each agent needs:
- **description**: Brief role description
- **prompt**: Path to markdown prompt file
- **tools**: List of allowed tools
- **model**: `sonnet`, `opus`, or `haiku`

#### 7. Global Settings
```yaml
allowed_tools:
   Read
   Write
   Edit
   Bash
   Grep
   Glob
permission_mode: acceptEdits
```

- `allowed_tools`: Tools available to main orchestrator
- `permission_mode`: `acceptEdits`, `prompt`, or `accept`

---

## Variable Substitution

### Default Context Variables

The orchestrator provides these default variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `${project_root}` | `/home/dev/claude_dev/claude_swarm` | Project root directory |
| `${output_dir}` | `${project_root}/generated_code` | Output directory |
| `${airflow_2_dags_dir}` | `airflow/data-airflow-2/dags` | Airflow 2 DAGs |
| `${airflow_legacy_dags_dir}` | `airflow/data-airflow-legacy/dags` | Legacy Airflow DAGs |
| `${CLAUDE_MODEL}` | From `$CLAUDE_MODEL` env var | Claude model (sonnet/opus/haiku) |
| `${orchestrator_agent}` | Auto-loaded from CLAUDE.md files | Orchestrator system prompt |

### Custom Context

Add your own variables via `--context`:

```bash
python swarm_orchestrator.py \
  --config config.yaml \
  --context '{"custom_var": "value", "api_key": "sk-..."}'
```

Then use in YAML:
```yaml
env:
  MY_API_KEY: ${api_key}
  CUSTOM_PATH: ${custom_var}/subdir
```

---

## Creating New Configurations

### Step 1: Create YAML File

```bash
touch yaml_files/my_framework_agent_options.yaml
```

### Step 2: Define Configuration

```yaml
system_prompt:
  type: preset
  preset: claude_code
  append: ${orchestrator_agent}
model: sonnet
main_prompt_file: prompts/my_framework/main-query.md

cwd: ${output_dir}

agents:
  architect:
    description: "System architect"
    prompt: prompts/my_framework/architect.md
    tools: [Read, Grep, Glob]
    model: haiku

  developer:
    description: "Code developer"
    prompt: prompts/my_framework/developer.md
    tools: [Read, Write, Edit, Bash]
    model: haiku

  reviewer:
    description: "Code reviewer"
    prompt: prompts/my_framework/reviewer.md
    tools: [Read, Grep, Glob, Bash]
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

### Step 3: Create Prompt Files

Create markdown files for each agent in `prompts/my_framework/`:

```
prompts/
└── my_framework/
    ├── main-query.md         # Main task description
    ├── architect.md          # Architect agent role
    ├── developer.md          # Developer agent role
    └── reviewer.md           # Reviewer agent role
```

### Step 4: Test Configuration

```bash
python swarm_orchestrator.py --config yaml_files/my_framework_agent_options.yaml
```

---

## Example Configurations

### Airflow DAG Migration

**File**: `yaml_files/airflow_agent_options.yaml`

**Agents**:
- `@dag-architect`: Plans DAG structure
- `@dag-developer`: Writes Airflow 2 code
- `@migration-specialist`: Converts Airflow 1 → 2
- `@airflow-code-reviewer`: Validates heartbeat safety, imports

**Use Case**: Migrate legacy Airflow 1 DAGs to Airflow 2 with proper patterns

**Command**:
```bash
python swarm_orchestrator.py --config yaml_files/airflow_agent_options.yaml
# Task: "Migrate marketo_to_snowflake.py from Airflow 1 to 2"
```

### Flask Application Generation

**File**: `yaml_files/flask_agent_options.yaml`

**Agents**:
- `@flask-developer`: Backend Flask development
- `@frontend-developer`: HTML/CSS/templates
- `@code-reviewer`: PEP 8, flake8 validation

**Use Case**: Generate Flask applications with proper structure

**Command**:
```bash
python swarm_orchestrator.py --config yaml_files/flask_agent_options.yaml
# Task: "Create a REST API for user management"
```

---

## Metrics & Output

### Terminal Output

The orchestrator provides rich, formatted output:

```
╔══════════════════════════════════════════════════════╗
║     Claude Swarm Multi-Agent Orchestrator           ║
╚══════════════════════════════════════════════════════╝

Configuration: yaml_files/airflow_agent_options.yaml
Output directory: /home/dev/claude_dev/claude_swarm/generated_code

Configured Agents:
  • dag-architect
  • dag-developer
  • migration-specialist
  • airflow-code-reviewer

============================================================
🔄 Starting orchestration...
============================================================

────────────────────────────────────────────────────────────
📍 ITERATION 1 | Type: AssistantMessage
────────────────────────────────────────────────────────────
[Agent output...]
```

### Final Metrics

After completion:

```
============================================================
✅ Orchestration complete!
============================================================

📊 ORCHESTRATION METRICS:
────────────────────────────────────────────────────────────
Iteration Metrics:
   • Total iterations: 18
   • Total messages: 28
   • Average time/iteration: 0.007s
   • Fastest iteration: 0.004s
   • Slowest iteration: 0.020s

Content Metrics:
   • Text blocks: 12
   • Thinking blocks: 2
   • Tool uses: 24
   • Files created: 4

Cost & Time Metrics:
   • Total cost: $0.123456
   • Cost per iteration: $0.006859
   • Total duration: 45.23s

Token Usage:
   • Input tokens: 15,234
   • Output tokens: 4,567
   • Cache read tokens: 123,456

Files Created:
   1. /path/to/output/dags/my_dag/src/main.py
   2. /path/to/output/dags/my_dag/daily.py
   3. /path/to/output/dags/my_dag/README.md

────────────────────────────────────────────────────────────
📁 Output location: /home/dev/claude_dev/claude_swarm/generated_code
```

---

## Comparison: Old vs New

### Old Approach (Flask-specific)

**File**: `flask_agent_main.py`

**Problems**:
- ❌ Hardcoded for Flask only
- ❌ Agent definitions in Python code
- ❌ Need new file for each framework
- ❌ Prompts loaded individually
- ❌ Configuration scattered

**Code**:
```python
# 450+ lines of hardcoded Flask logic
flask_dev_prompt = load_markdown_for_prompt("prompts/flask-developer.md")
frontend_dev_prompt = load_markdown_for_prompt("prompts/frontend-developer.md")
# ...
options = ClaudeAgentOptions(
    system_prompt={"type": "preset", "preset": "claude_code", "append": orchestrator_agent},
    agents={
        "flask-developer": AgentDefinition(
            description="Expert Flask developer.",
            prompt=flask_dev_prompt,
            tools=["Read", "Write", "Edit", "Bash"],
            model="haiku",
        ),
        # ...hardcoded agents
    }
)
```

### New Approach (Generalist)

**File**: `swarm_orchestrator.py`

**Advantages**:
- ✅ Works with ANY framework
- ✅ Agents defined in YAML
- ✅ Single orchestrator for all use cases
- ✅ Variable substitution
- ✅ Centralized configuration

**Usage**:
```bash
# Same orchestrator, different configs
python swarm_orchestrator.py --config yaml_files/flask_agent_options.yaml
python swarm_orchestrator.py --config yaml_files/airflow_agent_options.yaml
python swarm_orchestrator.py --config yaml_files/terraform_agent_options.yaml
```

**Code**: ~450 lines → generic, reusable

---

## Troubleshooting

### Configuration File Not Found

```
❌ Configuration file not found: yaml_files/my_config.yaml
```

**Fix**: Ensure file exists in `yaml_files/` directory

### Invalid YAML Syntax

```
yaml.parser.ParserError: while parsing...
```

**Fix**: Validate YAML syntax (indentation, colons, quotes)

### Prompt File Not Found

```
FileNotFoundError: prompts/agent.md
```

**Fix**: Ensure prompt file path is correct relative to project root

### Agent Configuration Invalid

```
TypeError: Invalid configuration for agent 'my-agent': expected mapping
```

**Fix**: Agent must be a YAML mapping with `description`, `prompt`, `tools`, `model`

### Variable Not Found

```
KeyError: 'unknown_var'
```

**Fix**: Either add variable to default context or pass via `--context`

---

## Advanced Usage

### Loading Custom Orchestrator Prompts

The orchestrator automatically searches for CLAUDE.md files:
1. `dag_CLAUDE_v2.md` (Airflow-specific)
2. `flask_CLAUDE.md` (Flask-specific)
3. `CLAUDE.md` (General)

Override in YAML:
```yaml
system_prompt:
  type: preset
  preset: claude_code
  append: ${orchestrator_agent}
```

Then pass in context:
```bash
python swarm_orchestrator.py \
  --config config.yaml \
  --context '{"orchestrator_agent": "Custom prompt text"}'
```

### Multiple Output Directories

```yaml
cwd: ${output_dir}/${framework_name}/${timestamp}
```

With context:
```bash
python swarm_orchestrator.py \
  --config config.yaml \
  --context '{"framework_name": "airflow", "timestamp": "2025-01-15"}'
```

Creates: `generated_code/airflow/2025-01-15/`

### Conditional Agent Loading

Use YAML anchors for reusable configs:

```yaml
.base_agent: &base_agent
  model: haiku
  tools:
    - Read
    - Grep
    - Glob

agents:
  architect:
    <<: *base_agent
    description: "System architect"
    prompt: prompts/architect.md

  developer:
    <<: *base_agent
    description: "Developer"
    prompt: prompts/developer.md
    tools:  # Override base
      - Read
      - Write
      - Edit
```

---

## Migration Guide

### From flask_agent_main.py

**1. Create YAML config** from Python code:

```python
# Old: flask_agent_main.py
options = ClaudeAgentOptions(
    agents={
        "flask-developer": AgentDefinition(
            prompt=flask_dev_prompt,
            tools=["Read", "Write"],
            model="haiku",
        ),
    },
)
```

Becomes:

```yaml
# New: yaml_files/flask_agent_options.yaml
agents:
  flask-developer:
    description: "Flask developer"
    prompt: prompts/flask-developer.md
    tools:
       Read
       Write
    model: haiku
```

**2. Update command**:

```bash
# Old
python flask_agent_main.py
# Type: flask

# New
python swarm_orchestrator.py --config yaml_files/flask_agent_options.yaml
```

**3. Test**:
```bash
python swarm_orchestrator.py --config yaml_files/flask_agent_options.yaml --task "flask"
```

---

## Best Practices

### 1. Organize Prompts by Framework

```
prompts/
├── airflow_prompts/
│   ├── main-query-airflow.md
│   ├── dag-architect.md
│   ├── dag-developer.md
│   └── airflow-code-reviewer.md
├── flask_prompts/
│   ├── main-query-flask.md
│   ├── flask-developer.md
│   └── frontend-developer.md
└── terraform_prompts/
    ├── main-query-terraform.md
    └── ...
```

### 2. Use Descriptive Config Names

```
yaml_files/
├── airflow_migration_agent_options.yaml
├── flask_api_generator_options.yaml
└── terraform_infra_options.yaml
```

Not:
```
config1.yaml
config2.yaml
```

### 3. Document Agent Descriptions

```yaml
agents:
  dag-architect:
    description: "Expert Airflow architect for planning DAG structure, task dependencies, and identifying patterns like batching, rate limiting, and external table usage."
    prompt: prompts/airflow_prompts/dag-architect.md
```

### 4. Test with Minimal Prompts First

Start with simple main prompts:
```markdown
# prompts/test-query.md

Create a simple Hello World application.
```

Then iterate to more complex tasks.

### 5. Version Control YAML Configs

```bash
git add yaml_files/*.yaml
git commit -m "Add Airflow agent configuration"
```

---

## Future Enhancements

### Planned Features

- [ ] **Config validation** with JSON schema
- [ ] **Agent inheritance** (extend base agent configs)
- [ ] **Multi-config orchestration** (combine multiple YAMLs)
- [ ] **Hot reload** (watch YAML for changes)
- [ ] **Web UI** for configuration management
- [ ] **Agent marketplace** (share/download configs)
- [ ] **Cost budgets** (stop if exceeds $X)
- [ ] **Parallel agent execution** (run multiple agents concurrently)

### Contribute

Want to add features? See `CONTRIBUTING.md` for guidelines.

---

## Summary

The **Swarm Orchestrator** transforms framework-specific orchestrators into a single, flexible system:

✅ **One orchestrator** for all frameworks
✅ **YAML configuration** for easy customization
✅ **No code changes** for new agents
✅ **Rich metrics** and monitoring
✅ **Interactive mode** for ease of use

**Get started**:
```bash
python swarm_orchestrator.py
```

**Questions?** See [GitHub Issues](https://github.com/mporenta/claude_swarm/issues)
