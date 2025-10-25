# Airflow Migration - Flexible Configuration Summary

**Date**: 2025-10-25
**Task**: Create flexible Airflow configuration that works across different machines and environments

---

## Problem Statement

The original Airflow YAML configuration (`airflow_agent_options.yaml`) had **hardcoded paths** that only worked on one specific machine:

```yaml
# Original (hardcoded)
add_dirs:
  - "{airflow_2_dags_dir}"
  - "{airflow_legacy_dags_dir}"

# In orchestrator.py:
"airflow_2_dags_dir": project_root / "airflow" / "data-airflow-2" / "dags"
```

This caused problems:
- ❌ Doesn't work on different team member machines
- ❌ Doesn't work in AWS Bedrock (temp directories)
- ❌ Doesn't work in CI/CD environments
- ❌ Requires code changes to update paths

---

## Solution Overview

Created a **flexible, environment-variable-based configuration system** that:
- ✅ Works on any machine (local, AWS Bedrock, CI/CD)
- ✅ No code changes needed for different environments
- ✅ Simple `.env.airflow` file for path configuration
- ✅ Backward compatible with existing configs

---

## Files Created

### 1. **`.env.airflow.example`** - Environment Variable Template

**Purpose**: Template with examples for all supported environments

**Location**: `/home/dev/claude_dev/claude_swarm/.env.airflow.example`

**Key Variables**:
```bash
AIRFLOW_2_ROOT=/path/to/data-airflow
AIRFLOW_2_DAGS_DIR=${AIRFLOW_2_ROOT}/dags
AIRFLOW_LEGACY_ROOT=/path/to/data-airflow-legacy
AIRFLOW_LEGACY_DAGS_DIR=${AIRFLOW_LEGACY_ROOT}/dags
```

**Usage**:
```bash
cp .env.airflow.example .env.airflow
# Edit .env.airflow with your actual paths
```

---

### 2. **`airflow_agent_options.local.yaml`** - Flexible YAML Config

**Purpose**: YAML configuration using environment variable placeholders

**Location**: `/home/dev/claude_dev/claude_swarm/yaml_files/airflow_agent_options.local.yaml`

**Key Features**:
```yaml
# Uses environment variable placeholders
add_dirs:
  - "{AIRFLOW_2_DAGS_DIR}"          # From $AIRFLOW_2_DAGS_DIR
  - "{AIRFLOW_LEGACY_DAGS_DIR}"     # From $AIRFLOW_LEGACY_DAGS_DIR

# Passes paths to agents
env:
  AIRFLOW_HOME: "{AIRFLOW_HOME}"
  AIRFLOW_2_ROOT: "{AIRFLOW_2_ROOT}"
  AIRFLOW_LEGACY_ROOT: "{AIRFLOW_LEGACY_ROOT}"
```

**Agents Configured**:
- `dag-developer` - Airflow 2.0 DAG development (Haiku)
- `migration-specialist` - Legacy → 2.0 migration (Haiku)
- `airflow-code-reviewer` - Code quality validation (Haiku)

---

### 3. **`src/orchestrator.py`** - Enhanced Path Resolution

**Purpose**: Support environment variables with fallback defaults

**Changes**:
```python
def _build_default_context(self) -> dict:
    """
    Build default context for YAML variable substitution.
    Supports environment variables for flexible path configuration.
    Priority: Environment Variables > Defaults
    """
    # Read from env vars first, fallback to defaults
    airflow_2_root = Path(os.getenv(
        "AIRFLOW_2_ROOT",
        project_root / "airflow" / "data-airflow-2"
    ))
```

**Priority Order**:
1. Environment variables (`.env.airflow`) ← **Highest**
2. Defaults in orchestrator.py ← **Fallback**

---

### 4. **`test_airflow_paths.sh`** - Path Validation Script

**Purpose**: Validate all paths are configured correctly before running

**Location**: `/home/dev/claude_dev/claude_swarm/test_airflow_paths.sh`

**Features**:
- ✅ Checks `.env.airflow` exists
- ✅ Validates all environment variables are set
- ✅ Confirms directories exist
- ✅ Shows directory contents (DAG counts)
- ✅ Reports configuration errors clearly

**Usage**:
```bash
./test_airflow_paths.sh
```

**Example Output**:
```
✓ Loaded .env.airflow

Environment Variables:
  AIRFLOW_2_ROOT:           /home/dev/projects/data-airflow
  AIRFLOW_2_DAGS_DIR:       /home/dev/projects/data-airflow/dags
  AIRFLOW_LEGACY_ROOT:      /home/dev/projects/data-airflow-legacy
  AIRFLOW_LEGACY_DAGS_DIR:  /home/dev/projects/data-airflow-legacy/dags

Path Validation:
  ✓ AIRFLOW_2_ROOT exists
  ✓ AIRFLOW_2_DAGS_DIR exists
    └─ Contains 15 directories
  ✓ AIRFLOW_LEGACY_ROOT exists
  ✓ AIRFLOW_LEGACY_DAGS_DIR exists
    └─ Contains 23 directories

✅ All paths configured correctly!
```

---

### 5. **`run_airflow_migration.sh`** - Migration Helper Script

**Purpose**: Simplified one-command migration execution

**Location**: `/home/dev/claude_dev/claude_swarm/run_airflow_migration.sh`

**Features**:
- ✅ Automatic environment loading
- ✅ Path validation before running
- ✅ Configuration summary display
- ✅ API key validation
- ✅ Results summary after completion

**Usage**:
```bash
./run_airflow_migration.sh
```

**Workflow**:
```
1. Checks .env.airflow exists
2. Sources environment variables
3. Validates paths (runs test_airflow_paths.sh)
4. Shows configuration summary
5. Checks ANTHROPIC_API_KEY
6. Runs orchestrator
7. Shows results location
```

---

### 6. **`AIRFLOW_SETUP.md`** - Comprehensive Documentation

**Purpose**: Complete setup and usage guide

**Location**: `/home/dev/claude_dev/claude_swarm/AIRFLOW_SETUP.md`

**Sections**:
- Quick Start (3-step setup)
- Environment Variables Explained
- Environment-Specific Examples (local, Bedrock, CI/CD)
- How It Works (variable substitution flow)
- Migration Workflow (3 phases)
- Troubleshooting (common issues & solutions)
- Advanced Configuration
- Best Practices
- Testing & Validation

---

## How It Works

### Variable Substitution Flow

```
User's Machine:
  .env.airflow
  ↓
  AIRFLOW_2_ROOT=/home/dev/projects/data-airflow
  AIRFLOW_2_DAGS_DIR=/home/dev/projects/data-airflow/dags

Orchestrator:
  src/orchestrator.py
  ↓
  _build_default_context() reads env vars
  ↓
  context = {"AIRFLOW_2_DAGS_DIR": "/home/dev/projects/data-airflow/dags"}

YAML Config:
  airflow_agent_options.local.yaml
  ↓
  add_dirs:
    - "{AIRFLOW_2_DAGS_DIR}"
  ↓
  Substituted to:
    - "/home/dev/projects/data-airflow/dags"

Agents Receive:
  Resolved paths in their environment
  Can read/write to correct directories
```

---

## Usage Examples

### Local Development (Linux)

```bash
# 1. Setup
cp .env.airflow.example .env.airflow

# 2. Edit .env.airflow
cat > .env.airflow << EOF
AIRFLOW_2_ROOT=/home/dev/projects/data-airflow
AIRFLOW_LEGACY_ROOT=/home/dev/projects/data-airflow-legacy
AIRFLOW_2_DAGS_DIR=\${AIRFLOW_2_ROOT}/dags
AIRFLOW_LEGACY_DAGS_DIR=\${AIRFLOW_LEGACY_ROOT}/dags
EOF

# 3. Test
./test_airflow_paths.sh

# 4. Run
./run_airflow_migration.sh
```

### AWS Bedrock (Temp Directories)

```bash
# Bedrock clones to temp dirs
export AIRFLOW_2_ROOT=/tmp/bedrock-workspace-abc/data-airflow
export AIRFLOW_LEGACY_ROOT=/tmp/bedrock-workspace-abc/data-airflow-legacy
export AIRFLOW_2_DAGS_DIR=$AIRFLOW_2_ROOT/dags
export AIRFLOW_LEGACY_DAGS_DIR=$AIRFLOW_LEGACY_ROOT/dags

# Run migration
python main.py --config yaml_files/airflow_agent_options.local.yaml
```

### Manual (No Scripts)

```bash
# 1. Source environment
set -a && source .env.airflow && set +a

# 2. Verify
echo $AIRFLOW_2_DAGS_DIR

# 3. Run orchestrator
python main.py --config yaml_files/airflow_agent_options.local.yaml
```

---

## Comparison: Before vs After

### Before (Hardcoded)

**Configuration**:
```python
# In orchestrator.py
return {
    "airflow_2_dags_dir": project_root / "airflow" / "data-airflow-2" / "dags",
    "airflow_legacy_dags_dir": project_root / "airflow" / "data-airflow-legacy" / "dags"
}
```

**Problems**:
- Works only if repos are in `claude_swarm/airflow/`
- Requires code changes for different paths
- Not portable across machines
- Can't use in AWS Bedrock

### After (Flexible)

**Configuration**:
```bash
# In .env.airflow (per-machine)
AIRFLOW_2_ROOT=/your/actual/path/data-airflow
AIRFLOW_LEGACY_ROOT=/your/actual/path/data-airflow-legacy
```

**Benefits**:
- ✅ Works on any machine
- ✅ No code changes needed
- ✅ Simple configuration file
- ✅ Works in AWS Bedrock
- ✅ Team members can have different paths

---

## Environment-Specific Configurations

### Development Team Examples

**John's Machine (Linux)**:
```bash
AIRFLOW_2_ROOT=/home/john/workspace/data-airflow
AIRFLOW_LEGACY_ROOT=/home/john/workspace/data-airflow-legacy
```

**Jane's Machine (macOS)**:
```bash
AIRFLOW_2_ROOT=/Users/jane/projects/data-airflow
AIRFLOW_LEGACY_ROOT=/Users/jane/projects/data-airflow-legacy
```

**CI/CD (GitHub Actions)**:
```bash
AIRFLOW_2_ROOT=/home/runner/work/data-airflow/data-airflow
AIRFLOW_LEGACY_ROOT=/home/runner/work/data-airflow-legacy/data-airflow-legacy
```

**AWS Bedrock**:
```bash
AIRFLOW_2_ROOT=/tmp/bedrock-workspace-xyz/data-airflow
AIRFLOW_LEGACY_ROOT=/tmp/bedrock-workspace-xyz/data-airflow-legacy
```

All use the **same YAML config** - just different `.env.airflow` files!

---

## Testing & Validation

### Automated Testing

```bash
# Run validation script
./test_airflow_paths.sh

# Expected output:
✅ All paths configured correctly!
```

### Manual Verification

```bash
# Check environment variables
echo $AIRFLOW_2_ROOT
echo $AIRFLOW_2_DAGS_DIR
echo $AIRFLOW_LEGACY_ROOT
echo $AIRFLOW_LEGACY_DAGS_DIR

# Verify directories exist
ls -la $AIRFLOW_2_DAGS_DIR
ls -la $AIRFLOW_LEGACY_DAGS_DIR

# Check DAG counts
find $AIRFLOW_2_DAGS_DIR -maxdepth 1 -type d | wc -l
find $AIRFLOW_LEGACY_DAGS_DIR -maxdepth 1 -type d | wc -l
```

---

## Migration Workflow

### Phase 1: Initial Setup (One-Time)

```bash
# 1. Clone both Airflow repos
git clone git@github.com:your-org/data-airflow.git
git clone git@github.com:your-org/data-airflow-legacy.git

# 2. Configure environment
cd claude_swarm
cp .env.airflow.example .env.airflow
nano .env.airflow  # Edit with your paths

# 3. Validate
./test_airflow_paths.sh
```

### Phase 2: Run Migration

```bash
# Option A: Use helper script (recommended)
./run_airflow_migration.sh

# Option B: Manual execution
set -a && source .env.airflow && set +a
python main.py --config yaml_files/airflow_agent_options.local.yaml
```

### Phase 3: Review Results

```bash
# Check generated code
ls -la generated_code/

# Review logs
cat logs/$(date +%Y_%m_%d)_debug.log

# Check analyzed logs
cat logs/analyzed/00_SUMMARY.md
```

---

## Key Features

### 1. Environment Variable Support

- ✅ Read from shell environment
- ✅ Read from `.env.airflow` file
- ✅ Fallback to sensible defaults
- ✅ Clear error messages if missing

### 2. Path Validation

- ✅ Automated validation script
- ✅ Check existence before running
- ✅ Helpful error messages
- ✅ Directory content summaries

### 3. Team Collaboration

- ✅ Each team member has own `.env.airflow`
- ✅ `.env.airflow` in `.gitignore` (not committed)
- ✅ `.env.airflow.example` shared (committed)
- ✅ Documentation for all environments

### 4. CI/CD Ready

- ✅ Environment variables in CI config
- ✅ No local file dependencies
- ✅ Validation before execution
- ✅ Clear success/failure reporting

---

## Files Added/Modified

### New Files Created

1. ✅ `.env.airflow.example` - Environment variable template
2. ✅ `yaml_files/airflow_agent_options.local.yaml` - Flexible YAML config
3. ✅ `test_airflow_paths.sh` - Path validation script
4. ✅ `run_airflow_migration.sh` - Migration helper script
5. ✅ `AIRFLOW_SETUP.md` - Comprehensive setup guide
6. ✅ `AIRFLOW_MIGRATION_SUMMARY.md` - This summary (you are here)

### Modified Files

1. ✅ `src/orchestrator.py` - Enhanced `_build_default_context()` to support environment variables

### Preserved Files (Backward Compatible)

1. ✅ `yaml_files/airflow_agent_options.yaml` - Original config still works
2. ✅ All other orchestrator code unchanged

---

## Backward Compatibility

The new system is **100% backward compatible**:

```yaml
# Old style (still works)
airflow_agent_options.yaml:
  add_dirs:
    - "{airflow_2_dags_dir}"

# New style (flexible)
airflow_agent_options.local.yaml:
  add_dirs:
    - "{AIRFLOW_2_DAGS_DIR}"
```

Both work! The orchestrator checks:
1. Environment variables first (`AIRFLOW_2_DAGS_DIR`)
2. Falls back to defaults if not set
3. Old configs use defaults automatically

---

## Next Steps

### For Users

1. **Setup** (5 minutes):
   ```bash
   cp .env.airflow.example .env.airflow
   nano .env.airflow  # Update paths
   ./test_airflow_paths.sh
   ```

2. **Run Migration**:
   ```bash
   ./run_airflow_migration.sh
   ```

3. **Review Results**:
   ```bash
   cat generated_code/README.md
   ```

### For Team Leads

1. **Share** `.env.airflow.example` with team
2. **Document** your team's standard paths in wiki
3. **Add** validation to CI/CD pipeline:
   ```yaml
   - name: Validate Airflow Paths
     run: ./test_airflow_paths.sh
   ```

### For DevOps

1. **Configure** CI/CD environment variables
2. **Add** to deployment scripts:
   ```bash
   export AIRFLOW_2_ROOT=/deploy/path/data-airflow
   export AIRFLOW_LEGACY_ROOT=/deploy/path/data-airflow-legacy
   ```
3. **Monitor** migration logs in CI

---

## Success Metrics

✅ **Flexibility**: Works on local, Bedrock, and CI/CD without code changes
✅ **Simplicity**: 3-step setup (copy, edit, run)
✅ **Validation**: Automated path checking before execution
✅ **Documentation**: Comprehensive guides for all scenarios
✅ **Compatibility**: Existing configs continue to work
✅ **Maintainability**: Clear separation of config from code

---

## Troubleshooting Reference

### Quick Fixes

| Issue | Solution |
|-------|----------|
| `.env.airflow` not found | `cp .env.airflow.example .env.airflow` |
| Paths not set | `set -a && source .env.airflow && set +a` |
| Directory not found | Update paths in `.env.airflow` |
| Permission denied | `chmod +x test_airflow_paths.sh run_airflow_migration.sh` |

### Debug Commands

```bash
# Check environment
env | grep AIRFLOW

# Test paths
ls -la $AIRFLOW_2_DAGS_DIR
ls -la $AIRFLOW_LEGACY_DAGS_DIR

# Validate config
./test_airflow_paths.sh

# Dry run
python main.py --config yaml_files/airflow_agent_options.local.yaml --help
```

---

## Summary

**Problem**: Hardcoded Airflow paths prevented flexible deployment

**Solution**: Environment-variable-based configuration system

**Result**:
- ✅ Portable across all environments
- ✅ Simple `.env.airflow` configuration
- ✅ Automated validation
- ✅ Comprehensive documentation
- ✅ Backward compatible

**Impact**: Team members and CI/CD can now use different paths without code changes!

---

**Status**: ✅ **COMPLETE & TESTED**
**Ready for**: Production use across all environments

