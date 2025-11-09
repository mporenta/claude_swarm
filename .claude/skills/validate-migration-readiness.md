# Validate Migration Readiness Skill

## Purpose
Pre-flight checklist before starting migration to assess readiness, complexity, and potential blockers.

## When to Use
**MANDATORY** at the very start:
- Before any migration work begins
- To assess migration complexity
- To identify blockers early
- To estimate effort required

## Execution Steps

### 1. Check Legacy DAG Exists
```bash
# Verify legacy DAG file
if [ -f "/Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py" ]; then
    echo "✓ Legacy DAG exists"
    wc -l "/Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py"
else
    echo "✗ Legacy DAG not found"
    exit 1
fi
```

### 2. Check Modern Folder Status
```bash
# Check if modern folder exists
if [ -d "/Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}" ]; then
    echo "⚠ Modern folder already exists"
    ls -la "/Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/${DAG_NAME}"
else
    echo "✓ Modern folder does not exist (ready for creation)"
fi
```

### 3. Test Legacy DAG Can Be Parsed
```bash
# Try to parse the DAG (basic syntax check)
python3 -m py_compile "/Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py"

if [ $? -eq 0 ]; then
    echo "✓ Legacy DAG parses successfully"
else
    echo "✗ Legacy DAG has syntax errors"
fi
```

### 4. Check for Import Errors
```bash
# Look for problematic imports
grep -n "from airflow.operators.python_operator import PythonOperator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "from airflow.contrib" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
grep -n "from airflow.hooks" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 5. Count Operators and Complexity
```bash
# Count total operators
OPERATOR_COUNT=$(grep -c "Operator(" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "Total operators: $OPERATOR_COUNT"

# Count unique operator types
grep -o "[A-Za-z]*Operator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | sort -u | wc -l

# Count custom functions
FUNCTION_COUNT=$(grep -c "^def " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "Custom functions: $FUNCTION_COUNT"

# Count lines of code
LOC=$(wc -l < /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py)
echo "Lines of code: $LOC"
```

### 6. Check for Common Components
```bash
# Check if common/ directory exists
ls -d /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators
ls -d /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_hooks
ls -d /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_callbacks

# Count available common operators
echo "Available common operators:"
ls -1 /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/common/custom_operators/*.py | wc -l
```

### 7. Identify Complexity Indicators
```bash
# Check for complex patterns
echo "Checking complexity indicators..."

# Dynamic tasks (loops)
grep -c "for .* in " /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Branching
grep -c "BranchPythonOperator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# Custom operators/hooks
grep -c "class.*Operator\|class.*Hook" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py

# XCom usage
grep -c "xcom_push\|xcom_pull" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py
```

### 8. Check Template Suitability
```bash
# Check if templates exist
ls -d /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/_dag_template
ls -d /Users/mike.porenta/python_dev/aptive_github/data-airflow/dags/_dag_taskflow_template

# Count non-Python operators
NON_PYTHON=$(grep -E "SnowflakeOperator|BashOperator|EmailOperator|HttpOperator" /Users/mike.porenta/python_dev/aptive_github/data-airflow-legacy/dags/${DAG_NAME}.py | wc -l)
echo "Non-Python operators: $NON_PYTHON"
```

## Complexity Assessment

### SIMPLE Migration
- < 100 LOC
- Python-only operators
- No custom operators/hooks
- Linear dependencies
- No branching or dynamic tasks

### MEDIUM Migration
- 100-300 LOC
- Mixed operator types
- Some custom logic
- Fan-out/fan-in patterns
- XCom usage

### COMPLEX Migration
- \> 300 LOC
- Custom operators/hooks
- Complex dependencies
- Branching + dynamic tasks
- Heavy XCom usage
- Anti-patterns (duplicate code)

## Output Report Format

After executing this skill, provide:

```markdown
## Migration Readiness Assessment: [dag_name]

### Pre-Flight Checks

| Check | Status | Details |
|-------|--------|---------|
| Legacy DAG exists | ✓ PASS | `/data-airflow-legacy/dags/[dag_name].py` |
| Modern folder exists | ⚠ WARNING | Folder already exists (may need cleanup) |
| DAG parses | ✓ PASS | No syntax errors |
| Import compatibility | ✓ PASS | No deprecated imports |
| Common components available | ✓ PASS | Operators/hooks available |

---

### Complexity Metrics

**Size**:
- Lines of code: 425
- Function definitions: 8
- Class definitions: 2
- Operators: 12

**Operator Types**:
- PythonOperator: 5
- SnowflakeOperator: 3
- BashOperator: 2
- Custom operators: 2

**Complexity Indicators**:
- XCom operations: 10 (push + pull)
- Branching: 1 (BranchPythonOperator)
- Dynamic tasks: 0
- Custom hooks: 1
- Dependencies: 8 statements

**Complexity Assessment**: ⚠️ **MEDIUM-HIGH**

---

### Template Recommendation

**Recommended Template**: `_dag_template/` (Traditional)

**Reasoning**:
- Mixed operator types (Python + Snowflake + Bash)
- Custom operators present
- Not pure Python workflow

**Alternative**: Could use TaskFlow for Python portions with explicit dependencies for non-Python operators

---

### Blockers Identified

#### ✗ BLOCKER: Custom SFTP Implementation (Lines 45-195)

**Issue**: 150 lines of custom SFTP client code

**Impact**: High - duplicates SFTPToSnowflakeOperator

**Resolution**:
```bash
# Must run this skill BEFORE migration
/check-common-components
```

**Action**: Replace with `SFTPToSnowflakeOperator` from common/

**Estimated LOC Reduction**: 150 lines (35% of DAG)

---

#### ⚠️ WARNING: Direct boto3 Usage (Lines 135-160)

**Issue**: Custom boto3 client instead of CustomS3Hook

**Impact**: Medium - creates maintenance burden

**Resolution**: Replace with CustomS3Hook from common/

**Estimated LOC Reduction**: 25 lines

---

### Common Component Opportunities

**Available Operators That May Apply**:
1. ✅ SFTPToSnowflakeOperator - **HIGHLY LIKELY** (SFTP detected in DAG)
2. ✅ CustomSnowflakeHook - **CONFIRMED** (SnowflakeOperator usage)
3. ✅ CustomS3Hook - **CONFIRMED** (boto3 usage detected)

**Next Step**: Run `/check-common-components` to confirm matches

---

### Migration Effort Estimate

**Complexity**: MEDIUM-HIGH

**Estimated Effort**:
- Pre-migration analysis: 1-2 hours
  - `/analyze-legacy-dag`
  - `/check-common-components`
  - `/map-operators-to-common`
  - `/extract-business-logic`

- Implementation: 3-4 hours
  - Replace custom SFTP with operator (30 min)
  - Replace boto3 with CustomS3Hook (30 min)
  - Convert PythonOperators to @task (1 hour)
  - Migrate configuration (30 min)
  - Update dependencies (30 min)
  - Refactor to modular structure (1 hour)

- Testing & validation: 1 hour
  - Syntax validation
  - Test runs
  - Compare outputs

**Total**: 5-7 hours

**LOC Reduction Expected**: ~175 lines (41% reduction)

---

### Migration Sequence

**Phase 1: Analysis** (Run these skills first)
1. ✅ `/validate-migration-readiness` (COMPLETED)
2. 🔄 `/analyze-legacy-dag` (NEXT)
3. 🔄 `/check-common-components` (CRITICAL)
4. 🔄 `/find-anti-patterns`
5. 🔄 `/map-operators-to-common`

**Phase 2: Planning**
6. 🔄 `/extract-business-logic`
7. 🔄 `/suggest-template-choice`
8. 🔄 `/analyze-connection-usage`

**Phase 3: Implementation**
9. 🔄 Create modular structure
10. 🔄 Replace redundant code with common components
11. 🔄 Convert operators to TaskFlow
12. 🔄 Migrate configuration

**Phase 4: Validation**
13. 🔄 Run tests
14. 🔄 Compare with legacy behavior

---

### Readiness Status

**Overall Readiness**: ⚠️ **READY WITH WARNINGS**

**Blockers**: 1 (Custom SFTP implementation)
**Warnings**: 2 (Direct boto3, complexity)

**Recommendation**:
✅ **PROCEED** with migration after running `/check-common-components` to confirm operator replacements

**Risk Level**: MEDIUM
- Complexity is manageable
- Clear opportunities for code reuse
- Well-defined anti-patterns to address

---

### Pre-Migration Checklist

Before starting implementation:
- [ ] Run `/analyze-legacy-dag` for detailed structure
- [ ] Run `/check-common-components` for operator mapping
- [ ] Run `/find-anti-patterns` to identify all DRY violations
- [ ] Confirm SFTPToSnowflakeOperator fits requirements
- [ ] Confirm CustomSnowflakeHook and CustomS3Hook availability
- [ ] Create modern folder structure
- [ ] Set up testing environment
```

## Enforcement

This skill MUST be executed:
- **FIRST**, before any other migration skills
- To assess if migration is feasible
- To identify blockers early
- To estimate effort and complexity

**Running this skill first prevents wasted effort on blocked migrations and ensures informed planning.**
