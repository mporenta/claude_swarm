#!/bin/bash
# Test Airflow Path Configuration
# Validates that all required paths are set and exist

set -e

echo "================================================================================================"
echo "🔍 Testing Airflow Path Configuration"
echo "================================================================================================"
echo

# Source environment
if [ -f .env.airflow ]; then
    set -a
    source .env.airflow
    set +a
    echo "✓ Loaded .env.airflow"
else
    echo "❌ ERROR: .env.airflow not found"
    echo "   Run: cp .env.airflow.example .env.airflow"
    echo "   Then edit .env.airflow with your paths"
    exit 1
fi

# Check environment variables
echo
echo "Environment Variables:"
echo "────────────────────────────────────────────────────────────────────────────────────────────────"
printf "  %-25s %s\n" "AIRFLOW_2_ROOT:" "$AIRFLOW_2_ROOT"
printf "  %-25s %s\n" "AIRFLOW_2_DAGS_DIR:" "$AIRFLOW_2_DAGS_DIR"
printf "  %-25s %s\n" "AIRFLOW_LEGACY_ROOT:" "$AIRFLOW_LEGACY_ROOT"
printf "  %-25s %s\n" "AIRFLOW_LEGACY_DAGS_DIR:" "$AIRFLOW_LEGACY_DAGS_DIR"
printf "  %-25s %s\n" "AIRFLOW_HOME:" "$AIRFLOW_HOME"
printf "  %-25s %s\n" "PYTHONPATH:" "$PYTHONPATH"
printf "  %-25s %s\n" "CLAUDE_MODEL:" "$CLAUDE_MODEL"

# Validate paths exist
echo
echo "Path Validation:"
echo "────────────────────────────────────────────────────────────────────────────────────────────────"

ERRORS=0

if [ -d "$AIRFLOW_2_ROOT" ]; then
    echo "  ✓ AIRFLOW_2_ROOT exists"
else
    echo "  ❌ AIRFLOW_2_ROOT not found: $AIRFLOW_2_ROOT"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "$AIRFLOW_2_DAGS_DIR" ]; then
    DAG_COUNT=$(find "$AIRFLOW_2_DAGS_DIR" -maxdepth 1 -type d | wc -l)
    echo "  ✓ AIRFLOW_2_DAGS_DIR exists"
    echo "    └─ Contains $DAG_COUNT directories"
else
    echo "  ❌ AIRFLOW_2_DAGS_DIR not found: $AIRFLOW_2_DAGS_DIR"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "$AIRFLOW_LEGACY_ROOT" ]; then
    echo "  ✓ AIRFLOW_LEGACY_ROOT exists"
else
    echo "  ❌ AIRFLOW_LEGACY_ROOT not found: $AIRFLOW_LEGACY_ROOT"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "$AIRFLOW_LEGACY_DAGS_DIR" ]; then
    LEGACY_DAG_COUNT=$(find "$AIRFLOW_LEGACY_DAGS_DIR" -maxdepth 1 -type d | wc -l)
    echo "  ✓ AIRFLOW_LEGACY_DAGS_DIR exists"
    echo "    └─ Contains $LEGACY_DAG_COUNT directories"
else
    echo "  ❌ AIRFLOW_LEGACY_DAGS_DIR not found: $AIRFLOW_LEGACY_DAGS_DIR"
    ERRORS=$((ERRORS + 1))
fi

# Check for CLAUDE.md in Airflow 2 project
echo
echo "Project Files:"
echo "────────────────────────────────────────────────────────────────────────────────────────────────"

if [ -f "$AIRFLOW_2_ROOT/CLAUDE.md" ]; then
    echo "  ✓ Found CLAUDE.md in Airflow 2 project"
else
    echo "  ⚠️  CLAUDE.md not found (agents won't have project context)"
fi

# Final result
echo
echo "================================================================================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All paths configured correctly!"
    echo
    echo "Next Steps:"
    echo "  1. Review paths above to confirm they're correct"
    echo "  2. Run migration orchestration:"
    echo "     python main.py --config yaml_files/airflow_agent_options.local.yaml"
    echo
    echo "Or use the helper script:"
    echo "  ./run_airflow_migration.sh"
    echo "================================================================================================"
    exit 0
else
    echo "❌ Configuration has $ERRORS error(s)"
    echo
    echo "Fix the errors above and run this script again."
    echo "================================================================================================"
    exit 1
fi
