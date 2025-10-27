# Test Scripts

## Client Instantiation Tests

These tests validate the flow from YAML configuration through `config_loader.py` to `ClaudeSDKClient` instantiation.

### Test 1: Basic Client Instantiation

**File:** `test_client_instantiation.py`

**What it tests:**
```
YAML config → config_loader.py → ClaudeAgentOptions → ClaudeSDKClient
```

**Run:**
```bash
python3 test_client_instantiation.py
# Or with specific config:
python3 test_client_instantiation.py --config yaml_files/airflow_agent_options.yaml
```

**Expected output:**
- ✅ Context built
- ✅ ClaudeAgentOptions loaded from YAML
- ✅ ClaudeSDKClient instantiated
- ✅ All validations passed

**Purpose:** Validates that `config_loader.py` correctly:
1. Loads YAML configuration
2. Creates `ClaudeAgentOptions` with proper attributes
3. Creates `AgentDefinition` objects for agents in YAML
4. Returns a valid `ClaudeAgentOptions` that can be passed to `ClaudeSDKClient`

---

### Test 2: Client with Frontmatter Agents

**File:** `test_client_with_agents.py`

**What it tests:**
```
YAML config → config_loader.py → ClaudeAgentOptions
.claude/agents/ → discover_agents() → merge into ClaudeAgentOptions
ClaudeAgentOptions → ClaudeSDKClient
```

**Run:**
```bash
python3 test_client_with_agents.py
# Or with specific config:
python3 test_client_with_agents.py --config yaml_files/airflow_agent_options_frontmatter.yaml
```

**Expected output:**
- ✅ YAML agents: 0 (or number from YAML)
- ✅ Frontmatter agents discovered: 3
  - dag-developer
  - migration-specialist
  - airflow-code-reviewer
- ✅ Agents merged: 3
- ✅ Total agents: 3
- ✅ ClaudeSDKClient instantiated with all agents

**Purpose:** Validates the complete orchestrator initialization flow:
1. YAML config loaded via `config_loader.py`
2. Frontmatter agents discovered from `.claude/agents/`
3. Agents merged into `ClaudeAgentOptions.agents` dict
4. Client instantiated with all merged agents available

---

## Migration Test

**File:** `test_migrate_invoca.sh`

**What it tests:**
- Complete orchestration flow with actual agent execution
- Migrates real Airflow 1.x DAG to Airflow 2.0
- Tests agent collaboration (@migration-specialist, @dag-developer, @airflow-code-reviewer)

**Run:**
```bash
./test_migrate_invoca.sh
```

**What it does:**
1. Checks source DAG exists: `/home/dev/claude_dev/airflow/data-airflow-legacy/dags/invoca_to_snowflake.py`
2. Passes migration task to orchestrator
3. Agents analyze, migrate, and review the code
4. Creates output in: `/home/dev/claude_dev/airflow/data-airflow/dags/invoca_dev_test/`
5. Runs flake8 validation

**Expected output:**
- Source DAG found and validated
- Orchestration runs (60-300 seconds)
- Files created in target directory
- flake8 passes

---

## Key Differences

| Test | Purpose | Duration | Output |
|------|---------|----------|--------|
| `test_client_instantiation.py` | Validate config loading | ~1s | Validation results |
| `test_client_with_agents.py` | Validate agent discovery & merge | ~1s | Agent list + validation |
| `test_migrate_invoca.sh` | Full orchestration with agents | 60-300s | Migrated DAG files |

---

## Understanding the Architecture

### What `config_loader.py` Does:

```python
# 1. Loads YAML file
raw_config = yaml.safe_load(config_file)

# 2. Loads main_prompt_file content (if specified)
orchestrator_content = load_markdown_for_prompt(main_prompt_path)
enhanced_context["ORCHESTRATOR_AGENT"] = orchestrator_content

# 3. Builds AgentDefinition objects from YAML agents section
for agent_name, config in agents_config.items():
    prompt = load_markdown_for_prompt(config['prompt'])
    agent_definitions[agent_name] = AgentDefinition(
        prompt=prompt,
        description=config['description'],
        tools=config['tools'],
        model=config['model']
    )

# 4. Returns ClaudeAgentOptions
return ClaudeAgentOptions(
    agents=agent_definitions,  # dict[str, AgentDefinition]
    system_prompt=...,
    model=...,
    cwd=...,
    allowed_tools=...,
    permission_mode=...
)
```

### What `SwarmOrchestrator` Does:

```python
# 1. Load options from YAML via config_loader
self.options = load_agent_options_from_yaml(config_path, context)

# 2. Discover frontmatter agents
frontmatter_agents = discover_agents(project_root)

# 3. Merge frontmatter agents into options.agents
for agent_name, agent_def in frontmatter_agents.items():
    if agent_name not in self.options.agents:
        self.options.agents[agent_name] = agent_def

# 4. Instantiate client with merged agents
self.client = ClaudeSDKClient(self.options)
```

### What `ClaudeSDKClient` Does:

```python
def __init__(self, options: ClaudeAgentOptions):
    self.options = options  # Store the options with all agents
    # Now self.options.agents contains all merged agents
    # Available as: @dag-developer, @migration-specialist, etc.
```

---

## When to Use Each Test

- **Basic instantiation test:** When modifying `config_loader.py` or YAML structure
- **Agents test:** When modifying agent discovery, frontmatter loading, or merge logic
- **Migration test:** When testing end-to-end orchestration with real agent execution

---

## Troubleshooting Tests

### Test fails at "Loading ClaudeAgentOptions"
- Check YAML syntax: `python -c "import yaml; yaml.safe_load(open('yaml_files/your_config.yaml'))"`
- Verify all referenced prompt files exist
- Check context variables are properly substituted

### Test fails at "Discovering frontmatter agents"
- Check `.claude/agents/` directory exists
- Verify agent files have valid YAML frontmatter
- Check agent files have required fields: `name`, `description`, `tools`, `model`

### Test fails at "Instantiating ClaudeSDKClient"
- Check ANTHROPIC_API_KEY is set: `echo $ANTHROPIC_API_KEY`
- Verify Claude Agent SDK is installed: `pip list | grep claude-agent-sdk`
- Check ClaudeAgentOptions has all required attributes

---

## Success Criteria

All tests should show:
- ✅ All steps passed
- ✅ No exceptions or errors
- ✅ Exit code 0

For migration test specifically:
- ✅ Input tokens > 500 (task provided)
- ✅ Multiple iterations (agent work)
- ✅ Files created in target directory
- ✅ flake8 passes with no errors
