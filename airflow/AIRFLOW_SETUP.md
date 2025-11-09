# Airflow Migration Setup Guide

**Multi-Environment Configuration for Airflow 1.0 → 2.0 Migration**

This guide explains how to configure the Claude Swarm orchestrator for Airflow DAG migration across different environments (local development, AWS Bedrock, CI/CD, etc.).

---

## Quick Start

### 1. Configure Environment Variables

```bash
# Copy the example file
cp .env.airflow.example .env.airflow

# Edit with your actual paths
nano .env.airflow  # or vim, code, etc.

# Source the environment
set -a && source .env.airflow && set +a
```

### 2. Verify Configuration

```bash
# Check that paths are set
echo "Airflow 2.0 Root: $AIRFLOW_2_ROOT"
echo "Airflow 2.0 DAGs: $AIRFLOW_2_DAGS_DIR"
echo "Legacy Root: $AIRFLOW_LEGACY_ROOT"
echo "Legacy DAGs: $AIRFLOW_LEGACY_DAGS_DIR"
```

### 3. Run Migration Orchestration

```bash
# Using the local-flexible YAML config
python main.py --config yaml_files/airflow_agent_options.local.yaml
```

---

## Environment Variables Explained

### Critical Paths (Required)

These paths **must** be configured for your environment:

| Variable | Description | Example |
|----------|-------------|---------|
| `AIRFLOW_2_ROOT` | Root directory of Airflow 2.0 project | `/home/dev/projects/data-airflow` |
| `AIRFLOW_2_DAGS_DIR` | Airflow 2.0 DAGs directory | `${AIRFLOW_2_ROOT}/dags` |
| `AIRFLOW_LEGACY_ROOT` | Root directory of Legacy Airflow | `/home/dev/projects/data-airflow-legacy` |
| `AIRFLOW_LEGACY_DAGS_DIR` | Legacy DAGs directory | `${AIRFLOW_LEGACY_ROOT}/dags` |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AIRFLOW_HOME` | Airflow home directory | `${AIRFLOW_2_ROOT}` |
| `PYTHONPATH` | Python import paths | `/opt/airflow/dags` |
| `CLAUDE_MODEL` | Model for orchestration | `claude-sonnet-4-5-20250929` |

---

## Environment-Specific Examples

### Local Development (Linux)

```bash
# .env.airflow
AIRFLOW_2_ROOT=/home/dev/projects/data-airflow
AIRFLOW_LEGACY_ROOT=/home/dev/projects/data-airflow-legacy
AIRFLOW_2_DAGS_DIR=${AIRFLOW_2_ROOT}/dags
AIRFLOW_LEGACY_DAGS_DIR=${AIRFLOW_LEGACY_ROOT}/dags
```

### Local Development (macOS)

```bash
# .env.airflow
AIRFLOW_2_ROOT=/Users/yourname/workspace/data-airflow
AIRFLOW_LEGACY_ROOT=/Users/yourname/workspace/data-airflow-legacy
AIRFLOW_2_DAGS_DIR=${AIRFLOW_2_ROOT}/dags
AIRFLOW_LEGACY_DAGS_DIR=${AIRFLOW_LEGACY_ROOT}/dags
```

### AWS Bedrock (Temporary Workspace)

```bash
# .env.airflow
# Bedrock clones repos to temp directories
AIRFLOW_2_ROOT=/tmp/bedrock-workspace-abc123/data-airflow
AIRFLOW_LEGACY_ROOT=/tmp/bedrock-workspace-abc123/data-airflow-legacy
AIRFLOW_2_DAGS_DIR=${AIRFLOW_2_ROOT}/dags
AIRFLOW_LEGACY_DAGS_DIR=${AIRFLOW_LEGACY_ROOT}/dags
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/airflow-migration.yml
env:
  AIRFLOW_2_ROOT: /home/runner/work/data-airflow/data-airflow
  AIRFLOW_LEGACY_ROOT: /home/runner/work/data-airflow-legacy/data-airflow-legacy
  AIRFLOW_2_DAGS_DIR: ${{ env.AIRFLOW_2_ROOT }}/dags
  AIRFLOW_LEGACY_DAGS_DIR: ${{ env.AIRFLOW_LEGACY_ROOT }}/dags
```

---

## How It Works

### Variable Substitution Flow

```
1. You set environment variables (AIRFLOW_2_ROOT, etc.)
   ↓
2. Orchestrator loads them in _build_default_context()
   ↓
3. YAML config uses {AIRFLOW_2_DAGS_DIR} placeholders
   ↓
4. Orchestrator substitutes actual paths
   ↓
5. Agents receive resolved paths in their environment
```

### YAML Configuration

The `airflow_agent_options.local.yaml` uses placeholders:

```yaml
add_dirs:
  - "{AIRFLOW_2_DAGS_DIR}"          # → /home/dev/projects/data-airflow/dags
  - "{AIRFLOW_LEGACY_DAGS_DIR}"     # → /home/dev/projects/data-airflow-legacy/dags

env:
  AIRFLOW_HOME: "{AIRFLOW_HOME}"
  AIRFLOW__CORE__DAGS_FOLDER: "{AIRFLOW_2_DAGS_DIR}"
```

These are automatically replaced with your environment-specific paths.

---

## Migration Workflow

### Phase 1: Setup (One-Time)

```bash
# Clone both repositories
git clone git@github.com:your-org/data-airflow.git
git clone git@github.com:your-org/data-airflow-legacy.git

# Create and configure .env.airflow
cp .env.airflow.example .env.airflow
# Edit paths to match your cloned repos

# Verify paths exist
ls -la $AIRFLOW_2_DAGS_DIR
ls -la $AIRFLOW_LEGACY_DAGS_DIR
```

### Phase 2: Migration Execution

```bash
# Source environment
set -a && source .env.airflow && set +a

# Run orchestrator
python main.py --config yaml_files/airflow_agent_options.local.yaml

# Follow prompts or provide migration task
# Example: "Migrate the ask_nicely DAG from Legacy to Airflow 2.0"
```

### Phase 3: Validation

```bash
# Check generated files
ls -la generated_code/

# Review migration logs
cat logs/$(date +%Y_%m_%d)_debug.log

# Verify code quality
cd $AIRFLOW_2_DAGS_DIR
flake8 ask_nicely/ --max-line-length=88
```

---

## Configuration Files Comparison

### Original (airflow_agent_options.yaml)

**Problem**: Hardcoded paths that only work on one machine

```yaml
add_dirs:
  - "{airflow_2_dags_dir}"
  - "{airflow_legacy_dags_dir}"

# Context in orchestrator.py:
# "airflow_2_dags_dir": project_root / "airflow" / "data-airflow-2" / "dags"
# ❌ Only works if repos are in claude_swarm/airflow/
```

### New (airflow_agent_options.local.yaml)

**Solution**: Environment-variable based paths that work everywhere

```yaml
add_dirs:
  - "{AIRFLOW_2_DAGS_DIR}"          # From environment
  - "{AIRFLOW_LEGACY_DAGS_DIR}"     # From environment

# ✅ Works on any machine with correct .env.airflow
```

---

## Troubleshooting

### Issue: "Directory not found" errors

**Symptom**:
```
ERROR: Failed to load configuration
FileNotFoundError: /home/dev/claude_dev/claude_swarm/airflow/data-airflow-2/dags
```

**Solution**:
1. Check environment variables are set:
   ```bash
   echo $AIRFLOW_2_ROOT
   echo $AIRFLOW_2_DAGS_DIR
   ```

2. If empty, source the .env.airflow file:
   ```bash
   set -a && source .env.airflow && set +a
   ```

3. Verify paths exist:
   ```bash
   ls -la $AIRFLOW_2_DAGS_DIR
   ```

### Issue: Environment variables not substituted

**Symptom**: YAML config shows `{AIRFLOW_2_DAGS_DIR}` literally instead of actual path

**Solution**:
1. Verify variable is in orchestrator context:
   ```python
   # Check src/orchestrator.py _build_default_context()
   # Should include AIRFLOW_2_DAGS_DIR in return dict
   ```

2. Ensure YAML uses correct placeholder syntax:
   ```yaml
   # Correct:
   add_dirs:
     - "{AIRFLOW_2_DAGS_DIR}"

   # Wrong:
   add_dirs:
     - "$AIRFLOW_2_DAGS_DIR"
     - "${AIRFLOW_2_DAGS_DIR}"
   ```

### Issue: Can't find Legacy DAGs

**Symptom**: Migration specialist can't read Legacy DAG files

**Solution**:
1. Verify Legacy repo is cloned:
   ```bash
   ls -la $AIRFLOW_LEGACY_ROOT
   ```

2. Check YAML includes Legacy path in `add_dirs`:
   ```yaml
   add_dirs:
     - "{AIRFLOW_2_DAGS_DIR}"
     - "{AIRFLOW_LEGACY_DAGS_DIR}"  # This is critical!
   ```

3. Confirm agents have Read permissions:
   ```yaml
   agents:
     migration-specialist:
       tools:
         - Read  # Required to read Legacy files
   ```

### Issue: Wrong Python environment

**Symptom**: Import errors for Airflow packages

**Solution**:
1. Set PYTHONPATH in .env.airflow:
   ```bash
   PYTHONPATH=$AIRFLOW_2_ROOT:$AIRFLOW_2_ROOT/dags/common:/opt/airflow/dags
   ```

2. Verify Python can import Airflow:
   ```bash
   python3 -c "import airflow; print(airflow.__version__)"
   ```

---

## Advanced Configuration

### Custom Output Directory

By default, migrated code goes to `generated_code/`. To change:

```yaml
# In airflow_agent_options.local.yaml
cwd: "{CUSTOM_OUTPUT_DIR}"
```

```bash
# In .env.airflow
CUSTOM_OUTPUT_DIR=/tmp/airflow-migrations
```

### Multiple Airflow Versions

If migrating from multiple Legacy versions:

```bash
# .env.airflow
AIRFLOW_LEGACY_V1_ROOT=/path/to/legacy-v1
AIRFLOW_LEGACY_V2_ROOT=/path/to/legacy-v2

AIRFLOW_LEGACY_V1_DAGS_DIR=${AIRFLOW_LEGACY_V1_ROOT}/dags
AIRFLOW_LEGACY_V2_DAGS_DIR=${AIRFLOW_LEGACY_V2_ROOT}/dags
```

```yaml
# airflow_agent_options.local.yaml
add_dirs:
  - "{AIRFLOW_2_DAGS_DIR}"
  - "{AIRFLOW_LEGACY_V1_DAGS_DIR}"
  - "{AIRFLOW_LEGACY_V2_DAGS_DIR}"
```

### Docker Container Paths

If running in Docker:

```bash
# .env.airflow
AIRFLOW_2_ROOT=/workspace/data-airflow
AIRFLOW_LEGACY_ROOT=/workspace/data-airflow-legacy
```

Mount volumes to match:
```bash
docker run -v /host/path/data-airflow:/workspace/data-airflow \
           -v /host/path/data-airflow-legacy:/workspace/data-airflow-legacy \
           --env-file .env.airflow \
           claude-swarm:latest
```

---

## Best Practices

### ✅ DO

1. **Use relative paths in .env.airflow** when possible
   ```bash
   AIRFLOW_2_ROOT=/home/dev/projects/data-airflow
   AIRFLOW_2_DAGS_DIR=${AIRFLOW_2_ROOT}/dags  # Relative
   ```

2. **Keep .env.airflow out of version control**
   ```bash
   echo ".env.airflow" >> .gitignore
   ```

3. **Document team-specific paths** in README or wiki
   ```markdown
   # Team Setup
   - John: repos in ~/workspace/
   - Jane: repos in /opt/airflow-dev/
   - CI/CD: repos in /home/runner/work/
   ```

4. **Validate paths before running**
   ```bash
   [ -d "$AIRFLOW_2_DAGS_DIR" ] || echo "ERROR: AIRFLOW_2_DAGS_DIR not found"
   ```

### ❌ DON'T

1. **Don't hardcode absolute paths in YAML**
   ```yaml
   # Bad:
   add_dirs:
     - /home/john/projects/data-airflow/dags
   ```

2. **Don't commit .env.airflow** (contains local paths)

3. **Don't use spaces in environment variable names**
   ```bash
   # Bad:
   AIRFLOW 2 ROOT=/path/to/airflow

   # Good:
   AIRFLOW_2_ROOT=/path/to/airflow
   ```

4. **Don't mix path separators**
   ```bash
   # Bad (Windows-style on Linux):
   AIRFLOW_2_ROOT=C:\Users\dev\airflow

   # Good (Unix-style):
   AIRFLOW_2_ROOT=/home/dev/airflow
   ```

---

## Testing Your Configuration

### Validation Script

Create `test_airflow_paths.sh`:

```bash
#!/bin/bash
# Test Airflow path configuration

set -e

echo "🔍 Testing Airflow Path Configuration..."
echo

# Source environment
if [ -f .env.airflow ]; then
    set -a
    source .env.airflow
    set +a
    echo "✓ Loaded .env.airflow"
else
    echo "❌ .env.airflow not found"
    exit 1
fi

# Check environment variables
echo
echo "Environment Variables:"
echo "  AIRFLOW_2_ROOT: $AIRFLOW_2_ROOT"
echo "  AIRFLOW_2_DAGS_DIR: $AIRFLOW_2_DAGS_DIR"
echo "  AIRFLOW_LEGACY_ROOT: $AIRFLOW_LEGACY_ROOT"
echo "  AIRFLOW_LEGACY_DAGS_DIR: $AIRFLOW_LEGACY_DAGS_DIR"

# Validate paths exist
echo
echo "Path Validation:"

if [ -d "$AIRFLOW_2_ROOT" ]; then
    echo "  ✓ AIRFLOW_2_ROOT exists"
else
    echo "  ❌ AIRFLOW_2_ROOT not found: $AIRFLOW_2_ROOT"
    exit 1
fi

if [ -d "$AIRFLOW_2_DAGS_DIR" ]; then
    echo "  ✓ AIRFLOW_2_DAGS_DIR exists"
    echo "    DAGs: $(ls -1 $AIRFLOW_2_DAGS_DIR | wc -l) directories"
else
    echo "  ❌ AIRFLOW_2_DAGS_DIR not found: $AIRFLOW_2_DAGS_DIR"
    exit 1
fi

if [ -d "$AIRFLOW_LEGACY_ROOT" ]; then
    echo "  ✓ AIRFLOW_LEGACY_ROOT exists"
else
    echo "  ❌ AIRFLOW_LEGACY_ROOT not found: $AIRFLOW_LEGACY_ROOT"
    exit 1
fi

if [ -d "$AIRFLOW_LEGACY_DAGS_DIR" ]; then
    echo "  ✓ AIRFLOW_LEGACY_DAGS_DIR exists"
    echo "    Legacy DAGs: $(ls -1 $AIRFLOW_LEGACY_DAGS_DIR | wc -l) directories"
else
    echo "  ❌ AIRFLOW_LEGACY_DAGS_DIR not found: $AIRFLOW_LEGACY_DAGS_DIR"
    exit 1
fi

echo
echo "✅ All paths configured correctly!"
echo
echo "Ready to run:"
echo "  python main.py --config yaml_files/airflow_agent_options.local.yaml"
```

```bash
chmod +x test_airflow_paths.sh
./test_airflow_paths.sh
```

---

## Summary

### Configuration Priority

1. **Environment Variables** (.env.airflow) → Highest priority
2. **Orchestrator Defaults** (src/orchestrator.py) → Fallback
3. **YAML Placeholders** → Substituted at runtime

### Key Files

| File | Purpose |
|------|---------|
| `.env.airflow` | Your local path configuration (not committed) |
| `.env.airflow.example` | Template with examples (committed) |
| `airflow_agent_options.local.yaml` | Flexible YAML config using env vars |
| `src/orchestrator.py` | Path resolution logic |
| `AIRFLOW_SETUP.md` | This documentation |

### Quick Commands Reference

```bash
# Setup
cp .env.airflow.example .env.airflow
nano .env.airflow

# Test
set -a && source .env.airflow && set +a
./test_airflow_paths.sh

# Run
python main.py --config yaml_files/airflow_agent_options.local.yaml

# Debug
echo $AIRFLOW_2_DAGS_DIR
ls -la $AIRFLOW_LEGACY_DAGS_DIR
```

---

**Questions?** Check the troubleshooting section or create an issue in the repository.

**Ready to migrate?** Follow the Quick Start at the top of this document!
