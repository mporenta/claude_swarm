#!/bin/bash
# Airflow Migration Helper Script
# Simplifies running the Claude Swarm orchestrator for Airflow DAG migrations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================================"
echo "🚀 Claude Swarm - Airflow Migration Orchestrator"
echo "================================================================================================"
echo

# Check if .env.airflow exists
if [ ! -f .env.airflow ]; then
    echo "❌ ERROR: .env.airflow not found"
    echo
    echo "First-time setup:"
    echo "  1. cp .env.airflow.example .env.airflow"
    echo "  2. Edit .env.airflow with your actual paths"
    echo "  3. Run this script again"
    echo
    exit 1
fi

# Source environment
echo "📂 Loading environment variables..."
set -a
source .env.airflow
set +a
echo "   ✓ Loaded .env.airflow"
echo

# Validate paths
echo "🔍 Validating paths..."
if ! ./test_airflow_paths.sh; then
    echo
    echo "❌ Path validation failed. Fix the errors and try again."
    exit 1
fi

# Show configuration summary
echo
echo "Configuration Summary:"
echo "────────────────────────────────────────────────────────────────────────────────────────────────"
echo "  Airflow 2.0 DAGs: $AIRFLOW_2_DAGS_DIR"
echo "  Legacy DAGs:      $AIRFLOW_LEGACY_DAGS_DIR"
echo "  Output Directory: $(pwd)/generated_code"
echo "  Model:            $CLAUDE_MODEL"
echo "────────────────────────────────────────────────────────────────────────────────────────────────"
echo

# Check for ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  WARNING: ANTHROPIC_API_KEY not set"
    echo "   Set it in your environment or add to .env.airflow"
    echo
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Aborted."
        exit 1
    fi
fi

# Run orchestrator
echo
echo "🤖 Starting Claude Swarm orchestrator..."
echo "────────────────────────────────────────────────────────────────────────────────────────────────"
echo

python3 main.py --config yaml_files/airflow_agent_options.local.yaml

# Show results
echo
echo "================================================================================================"
echo "✅ Orchestration complete!"
echo
echo "Check the results:"
echo "  - Generated code: $(pwd)/generated_code/"
echo "  - Logs: $(pwd)/logs/"
echo "  - Analyzed logs: $(pwd)/logs/analyzed/"
echo "================================================================================================"
