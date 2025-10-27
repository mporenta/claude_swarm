#!/bin/bash
# Simple test script for migrating Invoca DAG

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=============================================="
echo "Invoca DAG Migration Test"
echo -e "==============================================${NC}"
echo ""

# Paths
SOURCE_DAG="/home/dev/claude_dev/airflow/data-airflow-legacy/dags/invoca_to_snowflake.py"
TARGET_DIR="/home/dev/claude_dev/airflow/data-airflow/dags/invoca_dev_test"

# Check source exists
if [ ! -f "$SOURCE_DAG" ]; then
    echo -e "${RED}❌ Error: Source DAG not found: ${SOURCE_DAG}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Source DAG found${NC}"
echo "  Path: $SOURCE_DAG"
echo "  Lines: $(wc -l < $SOURCE_DAG)"
echo ""

# Warn if target exists
if [ -d "$TARGET_DIR" ]; then
    echo -e "${YELLOW}⚠️  Target directory exists: ${TARGET_DIR}${NC}"
    read -p "Continue and overwrite? (y/n): " confirm
    [[ $confirm != [yY] ]] && exit 0
    echo ""
fi

echo -e "${YELLOW}Migration Details:${NC}"
echo "  Source: $SOURCE_DAG"
echo "  Target: $TARGET_DIR/"
echo ""

read -p "Press Enter to start migration..."
echo ""

# Simple task instruction - agents have the full context in their prompts
TASK="Migrate the Airflow 1.x DAG at $SOURCE_DAG to Airflow 2.0.

Create the migrated DAG in: $TARGET_DIR/

Expected structure:
- $TARGET_DIR/src/main.py (business logic)
- $TARGET_DIR/hourly.py (DAG definition)

The migration should:
- Update all deprecated imports to Airflow 2.0
- Remove 'provide_context=True' parameters
- Add type hints and docstrings to all functions
- Follow heartbeat-safe code patterns
- Pass flake8 compliance
- Preserve the dynamic task generation from configuration

Use @migration-specialist to analyze, @dag-developer to implement, and @airflow-code-reviewer to review."

echo -e "${GREEN}Starting orchestration...${NC}"
echo ""

python3 main.py \
  --config yaml_files/airflow_agent_options_frontmatter.yaml \
  --task "$TASK"

echo ""
echo -e "${CYAN}=============================================="
echo "Migration Complete!"
echo -e "==============================================${NC}"
echo ""

# Check results
if [ -d "$TARGET_DIR" ]; then
    echo -e "${GREEN}✅ Target directory created${NC}"
    echo ""
    echo -e "${BLUE}Generated structure:${NC}"
    tree "$TARGET_DIR" 2>/dev/null || find "$TARGET_DIR" -type f
    echo ""

    # Run flake8 if available
    if command -v flake8 &> /dev/null; then
        echo -e "${BLUE}Running flake8...${NC}"
        flake8 "$TARGET_DIR" --max-line-length=88 && echo -e "${GREEN}✅ Passed${NC}" || echo -e "${YELLOW}⚠️  Issues found${NC}"
        echo ""
    fi
else
    echo -e "${RED}❌ Target directory not created - check logs${NC}"
    exit 1
fi
