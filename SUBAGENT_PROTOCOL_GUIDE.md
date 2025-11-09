# Claude Code Subagent Protocol Implementation Guide

## Overview

The Claude Swarm orchestrator now supports the **official Claude Code subagent protocol** using YAML frontmatter in Markdown files stored in `.claude/agents/` directories.

**Benefits:**
- ✅ **Simpler configuration** - No need to define agents in YAML
- ✅ **Follows official standard** - Compatible with Claude Code conventions
- ✅ **Better organization** - One file per agent with metadata + prompt
- ✅ **Auto-discovery** - Agents automatically loaded from `.claude/agents/`
- ✅ **Priority system** - Project-level agents override user-level agents
- ✅ **Tool specification** - Each agent declares its own tools

---

## Quick Start

### 1. Agent File Structure

Agents are stored in `.claude/agents/` with YAML frontmatter:

```markdown
---
name: agent-name
description: When/why to use this agent. Use PROACTIVELY for auto-delegation.
tools: Read,Write,Edit,Bash
model: haiku
---

System prompt content here...

## Your Responsibilities

- Task 1
- Task 2

## Best Practices

...
```

### 2. Directory Structure

```
claude_swarm/
├── .claude/
│   └── agents/                          # Project-level agents (highest priority)
│       ├── migration-specialist.md
│       ├── dag-developer.md
│       └── airflow-code-reviewer.md
├── yaml_files/
│   └── airflow_agent_options_frontmatter.yaml  # Simplified config
└── ...
```

### 3. Simplified YAML Configuration

```yaml
# No need to define agents here - they're auto-discovered!
system_prompt:
  type: preset
  preset: claude_code
  append: "{orchestrator_agent}"

model: "{CLAUDE_MODEL}"
main_prompt_file: prompts/airflow_prompts/main-query-airflow.md

allowed_tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob

permission_mode: acceptEdits

# Agents auto-discovered from .claude/agents/
```

---

## Frontmatter Fields

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Lowercase identifier with hyphens | `migration-specialist` |
| `description` | When/why to use agent | `Expert in migrating Airflow DAGs...` |

### Optional Fields

| Field | Description | Example | Default |
|-------|-------------|---------|---------|
| `tools` | Comma-separated tool list | `Read,Write,Edit,mcp__migration__detect_legacy_imports` | Inherit all from main thread |
| `model` | Model alias or 'inherit' | `haiku`, `sonnet`, `opus`, `inherit` | `inherit` |

### Tool Specification

**Comma-separated string:**
```yaml
tools: Read,Write,Edit,Bash,Grep,Glob
```

**Includes MCP tools:**
```yaml
tools: Read,Write,Edit,mcp__migration__detect_legacy_imports,mcp__migration__compare_dags
```

**Leave blank to inherit all:**
```yaml
tools:
# Agent will have access to all tools available to orchestrator
```

---

## Agent Discovery

The orchestrator follows this priority:

1. **Project-level:** `.claude/agents/` in project root (highest priority)
2. **User-level:** `~/.claude/agents/` in home directory (lower priority)
3. **YAML-defined:** Agents in YAML config override frontmatter agents

### Discovery Logic

```python
# Automatic discovery on orchestrator initialization
from util.agent_loader import discover_agents

# Discovers agents from:
# 1. {project_root}/.claude/agents/
# 2. ~/.claude/agents/ (if not overridden)

agents = discover_agents(project_root)
# Returns: {
#     "migration-specialist": AgentDefinition(...),
#     "dag-developer": AgentDefinition(...),
#     "airflow-code-reviewer": AgentDefinition(...)
# }
```

---

## Created Agents

### 1. migration-specialist

**File:** `.claude/agents/migration-specialist.md`

```yaml
---
name: migration-specialist
description: Expert in migrating Airflow DAGs from 1.0 to 2.0. Use PROACTIVELY when user mentions DAG migration.
tools: Read,Write,Edit,Grep,Glob,mcp__migration__detect_legacy_imports,mcp__migration__detect_deprecated_parameters,mcp__migration__compare_dags
model: haiku
---
```

**Key Features:**
- Import modernization guide
- Incremental migration strategy (6 steps)
- Common gotchas (6 patterns)
- Has access to migration tools

### 2. dag-developer

**File:** `.claude/agents/dag-developer.md`

```yaml
---
name: dag-developer
description: Expert Airflow 2 developer for production-ready pipelines. Use PROACTIVELY when user mentions creating DAG or implementing pipeline.
tools: Read,Write,Edit,Bash,Grep,Glob,mcp__migration__detect_legacy_imports
model: haiku
---
```

**Key Features:**
- Import quick reference (✅/❌ patterns)
- PythonOperator modern pattern
- Heartbeat-safe code examples
- Clean code principles

### 3. airflow-code-reviewer

**File:** `.claude/agents/airflow-code-reviewer.md`

```yaml
---
name: airflow-code-reviewer
description: Code review specialist for Airflow 2. Use PROACTIVELY after DAG code written or migrated.
tools: Read,Grep,Glob,Bash,mcp__migration__detect_legacy_imports,mcp__migration__detect_deprecated_parameters
model: haiku
---
```

**Key Features:**
- Migration-specific review checklist
- Quick audit bash commands
- Auto-fix suggestions (sed commands)
- Structured feedback format

---

## Usage Examples

### Example 1: Using Auto-Discovered Agents

```bash
# Run with simplified config
python main.py --config yaml_files/airflow_agent_options_frontmatter.yaml \
  --task "Migrate the invoca DAG from Airflow 1.x to 2.0"

# Orchestrator will:
# 1. Auto-discover agents from .claude/agents/
# 2. Recognize @migration-specialist, @dag-developer, @airflow-code-reviewer
# 3. Delegate to appropriate agents based on description
```

### Example 2: Delegating to Frontmatter Agents

```
# In orchestration prompt:
@migration-specialist
Migrate the legacy invoca_to_snowflake.py DAG to Airflow 2.0.
Use detect_legacy_imports to check for issues first.

@dag-developer
Implement the migrated DAG following the file structure pattern.

@airflow-code-reviewer
Review the migrated code for compliance.
Use detect_legacy_imports and detect_deprecated_parameters.
```

### Example 3: Overriding Frontmatter Agents

If you need to override a frontmatter agent, define it in YAML:

```yaml
# airflow_agent_options.yaml
agents:
  migration-specialist:
    description: "Custom migration specialist with different tools"
    prompt: prompts/custom-migration.md
    tools: [Read, Write, Edit]
    model: sonnet

# This YAML agent will override the frontmatter agent
```

---

## Migration from Old Format

### Before (Old Format)

**Configuration in YAML:**
```yaml
# yaml_files/airflow_agent_options.local.yaml
agents:
  dag-developer:
    description: "Backend Flask development"
    prompt: prompts/airflow_prompts/dag-developer.md
    tools: [Read, Write, Edit, Bash]
    model: haiku

  migration-specialist:
    description: "Airflow migration expert"
    prompt: prompts/airflow_prompts/migration-specialist.md
    tools: [Read, Write, Edit, Grep, Glob]
    model: haiku

  airflow-code-reviewer:
    description: "Code review specialist"
    prompt: prompts/airflow_prompts/airflow-code-reviewer.md
    tools: [Read, Grep, Glob, Bash]
    model: haiku
```

**Prompts stored separately:**
```
prompts/
└── airflow_prompts/
    ├── dag-developer.md (no frontmatter)
    ├── migration-specialist.md (no frontmatter)
    └── airflow-code-reviewer.md (no frontmatter)
```

### After (New Format)

**Minimal YAML configuration:**
```yaml
# yaml_files/airflow_agent_options_frontmatter.yaml
system_prompt:
  type: preset
  preset: claude_code
  append: "{orchestrator_agent}"

model: "{CLAUDE_MODEL}"
allowed_tools: [Read, Write, Edit, Bash, Grep, Glob]
permission_mode: acceptEdits

# Agents auto-discovered from .claude/agents/
```

**Agents with frontmatter:**
```
.claude/
└── agents/
    ├── dag-developer.md (with frontmatter)
    ├── migration-specialist.md (with frontmatter)
    └── airflow-code-reviewer.md (with frontmatter)
```

**Benefits:**
- 📉 **50% less YAML configuration**
- 📁 **Self-contained agents** (metadata + prompt in one file)
- 🔄 **Follows Claude Code standard**
- ✅ **Auto-discovery** (no manual registration needed)

---

## Implementation Details

### Agent Loader (`util/agent_loader.py`)

**Key Functions:**

1. **`parse_frontmatter(content)`**
   - Parses YAML frontmatter from markdown
   - Returns tuple of (frontmatter_dict, body_content)

2. **`load_agent_from_file(agent_file)`**
   - Loads single agent from frontmatter file
   - Creates AgentDefinition object
   - Returns tuple of (agent_name, agent_def)

3. **`load_agents_from_directory(agents_dir)`**
   - Scans directory for `*.md` files
   - Loads each as a subagent
   - Returns dict of agents

4. **`discover_agents(project_root)`**
   - Checks project-level `.claude/agents/`
   - Checks user-level `~/.claude/agents/`
   - Returns merged dict with priority handling

### Orchestrator Integration

**Modified `_load_configuration()` in `orchestrator.py`:**

```python
def _load_configuration(self):
    # Load YAML config
    self.options = load_agent_options_from_yaml(self.config_path, self.context)

    # Discover frontmatter agents
    project_root = Path(__file__).resolve().parent.parent
    frontmatter_agents = discover_agents(project_root)

    # Merge agents (YAML has higher priority)
    for agent_name, agent_def in frontmatter_agents.items():
        if agent_name not in self.options.agents:
            self.options.agents[agent_name] = agent_def
            logger.info(f"Added frontmatter agent: {agent_name}")
```

---

## Testing

### Test Agent Discovery

```python
from util.agent_loader import discover_agents
from pathlib import Path

# Discover agents
agents = discover_agents(Path("."))

print(f"Discovered {len(agents)} agents:")
for name, agent_def in agents.items():
    print(f"  - {name}")
    print(f"    Model: {agent_def.model}")
    print(f"    Tools: {agent_def.tools}")
```

### Test with Orchestrator

```bash
# Test with frontmatter config
python main.py --config yaml_files/airflow_agent_options_frontmatter.yaml

# Orchestrator will show:
# INFO: Discovered 3 frontmatter agent(s) from .claude/agents/
# INFO: Added frontmatter agent: migration-specialist
# INFO: Added frontmatter agent: dag-developer
# INFO: Added frontmatter agent: airflow-code-reviewer
```

---

## Best Practices

### 1. Use "PROACTIVELY" in Descriptions

```yaml
description: Expert in migrating Airflow DAGs. Use PROACTIVELY when user mentions migration.
```

This tells the orchestrator to auto-delegate without explicit `@agent` mentions.

### 2. Specify Minimal Required Tools

```yaml
# Only give agent the tools it needs
tools: Read,Write,Edit  # No Bash if not needed
```

### 3. Choose Appropriate Model

```yaml
# Use haiku for fast, routine tasks
model: haiku

# Use sonnet for complex reasoning
model: sonnet

# Inherit from orchestrator
model: inherit
```

### 4. Keep Prompts Focused

- One file per agent
- Single responsibility
- Clear examples
- Explicit dos/don'ts

### 5. Version Control Agents

Commit `.claude/agents/` to git for team collaboration:

```bash
git add .claude/agents/
git commit -m "Add Airflow subagents with frontmatter protocol"
```

---

## Troubleshooting

### Issue: Agents Not Discovered

**Check:**
1. `.claude/agents/` directory exists in project root
2. Agent files have `.md` extension
3. Frontmatter format is correct (---\nYAML\n---\nContent)
4. `name` and `description` fields are present

**Debug:**
```bash
# Check logs
tail -f logs/*.log | grep "Discovered"
# Should see: "Discovered 3 frontmatter agent(s)"
```

### Issue: Invalid Frontmatter Format

**Error:** `ValueError: Invalid frontmatter format`

**Fix:** Ensure format is:
```markdown
---
name: agent-name
description: Description here
---
Content here
```

**Common mistakes:**
- Missing `---` delimiters
- Space in `---` (should be no spaces)
- Invalid YAML syntax
- Missing required fields

### Issue: Agent Not Available

**Check:**
1. Agent name matches filename (without `.md`)
2. Agent not overridden by YAML config
3. Logs show agent was discovered

**Debug:**
```python
# Check what agents are loaded
print(list(self.options.agents.keys()))
```

---

## Summary

**Implementation Complete:** ✅
- ✅ Created `.claude/agents/` directory
- ✅ Converted 3 agents to frontmatter format
- ✅ Created `util/agent_loader.py` for discovery
- ✅ Updated orchestrator to auto-discover agents
- ✅ Created simplified YAML config example

**Benefits Realized:**
- 📉 Simpler configuration (minimal YAML)
- 📁 Self-contained agents (metadata + prompt)
- 🔄 Follows Claude Code standard
- ✅ Auto-discovery mechanism
- 🎯 Tool specification per agent

**Next Steps:**
1. Test with new configuration
2. Migrate other agents (Flask, general-purpose)
3. Share `.claude/agents/` across team
4. Document custom agents in team wiki

---

## Files Modified/Created

```
✅ .claude/agents/migration-specialist.md (created)
✅ .claude/agents/dag-developer.md (created)
✅ .claude/agents/airflow-code-reviewer.md (created)
✅ util/agent_loader.py (created)
✅ src/orchestrator.py (updated - added agent discovery)
✅ yaml_files/airflow_agent_options_frontmatter.yaml (created)
✅ SUBAGENT_PROTOCOL_GUIDE.md (this file)
```

The Claude Swarm orchestrator now fully supports the official Claude Code subagent protocol! 🎉
