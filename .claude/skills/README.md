# Airflow Migration Skills

Specialized skills for migrating Airflow 1.x DAGs to 2.x with TaskFlow API, designed for Haiku subagents orchestrated by Sonnet.

## Overview

These skills enforce DRY principles, ensure proper use of common components, and guide systematic migration from legacy to modern Airflow patterns.

**Total Skills**: 13
**Matched Legacy-Modern DAG Pairs**: 14 (cresta_to_snowflake, aktify, arm_to_snowflake, etc.)

---

## 🚀 Migration Workflow

### Phase 1: Pre-Migration Analysis (MANDATORY)

Run these skills **FIRST** before any code changes:

#### 1. `/validate-migration-readiness`
**Purpose**: Pre-flight checklist - assess if migration is ready to start
**When**: Always run FIRST
**Output**: Readiness status, blockers, complexity assessment
**Key Checks**:
- ✓ Legacy DAG exists and parses
- ✓ Common components available
- ⚠ Modern folder status
- 📊 Complexity scoring (SIMPLE/MEDIUM/COMPLEX)

#### 2. `/analyze-legacy-dag`
**Purpose**: Parse and document legacy DAG structure
**When**: After validation passes
**Output**: Detailed structure report with line numbers
**Extracts**:
- Operators used (types and counts)
- Dependencies (task graph)
- XCom patterns
- Connections required
- Functions and classes
- Complexity metrics

#### 3. `/check-common-components` ⭐ CRITICAL
**Purpose**: Enforce DRY - verify existing common components before writing code
**When**: MANDATORY before creating ANY custom operator/hook
**Output**: Decision matrix (USE | EXTEND | CREATE)
**Prevents**: Duplicating code that exists in `/common/`

#### 4. `/find-anti-patterns`
**Purpose**: Detect DRY violations, security issues, code smells
**When**: After analyzing structure
**Output**: Prioritized issues (CRITICAL/HIGH/MEDIUM/LOW)
**Identifies**:
- 🚨 Custom SFTP/S3/Snowflake implementations
- 🚨 Hardcoded credentials
- ⚠️ Oversized files (>300 LOC)
- ⚠️ Missing callbacks

---

### Phase 2: Migration Planning

#### 5. `/map-operators-to-common`
**Purpose**: Match legacy operators to existing common components
**When**: After checking common components
**Output**: Operator mapping with LOC savings
**Benefits**: Shows which operators can be replaced

#### 6. `/extract-business-logic`
**Purpose**: Separate business logic from Airflow boilerplate
**When**: Before implementation
**Output**: Classification (COMMON | SRC/MAIN.PY | @TASK | CONFIG)
**Recommends**: Where each function should live

#### 7. `/suggest-template-choice`
**Purpose**: Recommend TaskFlow vs Traditional template
**When**: After understanding operator mix
**Output**: Template recommendation with reasoning
**Decides**: Based on Python % and complexity

#### 8. `/analyze-connection-usage`
**Purpose**: Document connections and map to common hooks
**When**: Before implementing operators
**Output**: Connection inventory with common hook mappings
**Ensures**: Secure credential management

---

### Phase 3: Implementation Details

#### 9. `/compare-dag-configs`
**Purpose**: Map legacy default_args to modern @dag parameters
**When**: Before converting DAG() to @dag
**Output**: Parameter migration map
**Updates**: schedule_interval → schedule, concurrency → max_active_tasks, etc.

#### 10. `/check-xcom-patterns`
**Purpose**: Convert manual XCom to TaskFlow return/parameter patterns
**When**: Before converting PythonOperators
**Output**: XCom pattern migration with code examples
**Converts**: xcom_push/pull → return values and parameters

#### 11. `/identify-dependencies`
**Purpose**: Convert task dependencies to TaskFlow patterns
**When**: Before implementing dependencies
**Output**: Dependency migration (data flow vs explicit)
**Recommends**: When to use `task2(task1())` vs `task1 >> task2`

#### 12. `/check-dynamic-tasks`
**Purpose**: Convert loops to .override() or .expand() patterns
**When**: When legacy DAG has loops creating tasks
**Output**: Dynamic task migration with TaskGroup recommendations
**Converts**: for loops → .override(task_id=...) or .expand()

---

### Phase 4: Validation

#### 13. `/generate-migration-diff`
**Purpose**: Document changes, LOC reduction, improvements
**When**: After modern DAG is implemented
**Output**: Side-by-side comparison report
**Shows**: What changed, why, and value delivered

---

## 📋 Skill Execution Order (Recommended)

```bash
# Phase 1: Pre-Migration (Always run these first)
/validate-migration-readiness
/analyze-legacy-dag
/check-common-components  # ⭐ CRITICAL - NEVER SKIP
/find-anti-patterns

# Phase 2: Planning
/map-operators-to-common
/extract-business-logic
/suggest-template-choice
/analyze-connection-usage

# Phase 3: Implementation (as needed)
/compare-dag-configs
/check-xcom-patterns
/identify-dependencies
/check-dynamic-tasks

# Phase 4: Post-Migration
/generate-migration-diff
```

---

## 🎯 Quick Reference by Use Case

### "I'm starting a new migration"
1. `/validate-migration-readiness` - Is it ready?
2. `/analyze-legacy-dag` - What am I dealing with?
3. `/check-common-components` - What can I reuse?
4. `/suggest-template-choice` - Which template?

### "I need to implement SFTP/S3/API logic"
1. `/check-common-components` ⭐ **RUN THIS FIRST**
2. `/map-operators-to-common` - Which operator to use?
3. `/analyze-connection-usage` - What connections needed?

### "I'm converting PythonOperators"
1. `/extract-business-logic` - Where should this code live?
2. `/check-xcom-patterns` - How to handle data passing?
3. `/compare-dag-configs` - How to update parameters?

### "I have loops creating tasks"
1. `/check-dynamic-tasks` - How to convert loops?

### "I'm done migrating"
1. `/generate-migration-diff` - What improved?

---

## 🚨 Critical Rules

### NEVER Write Code Without:
1. ✅ Running `/check-common-components` first
2. ✅ Checking if it exists in `/common/`
3. ✅ Verifying 80%+ match doesn't exist

### ALWAYS Use Common Components For:
- SFTP operations → `SFTPToSnowflakeOperator`
- S3 operations → `CustomS3Hook`
- Snowflake operations → `CustomSnowflakeHook`
- PestRoutes API → `CustomPestRoutesToS3Operator`
- Google Sheets → `CustomSheetsToSnowflakeOperator`
- Callbacks → `AirflowCallback`

### Migration Priorities:
1. 🔴 **CRITICAL**: Security issues (hardcoded credentials)
2. 🔴 **CRITICAL**: DRY violations (custom implementations of common components)
3. 🟡 **HIGH**: Complexity issues (oversized files, missing callbacks)
4. 🟢 **MEDIUM**: Deprecated patterns (old imports, provide_context)
5. 🔵 **LOW**: Code smells (missing type hints, no docstrings)

---

## 📊 Expected Results

### Typical Migration Metrics:
- **LOC Reduction**: 40-70%
- **DRY Compliance**: Eliminate 100-200+ lines of redundant code
- **Structure**: 1 monolithic file → 3 modular files
- **XCom**: 10+ manual operations → 0 (automatic)
- **Type Safety**: 0% → 100% (all @task functions)
- **Testability**: Hard → Easy (src/main.py)

### Real Example (cresta_to_snowflake):
- Legacy: 425 lines (1 file)
- Modern: 155 lines (3 files)
- **Reduction: 63.5%**
- Eliminated: 150 lines of custom SFTP code
- Replaced with: 9-line SFTPToSnowflakeOperator configuration

---

## 🛠️ For Orchestrator Agents

### Skill Delegation Pattern:

```markdown
# Orchestrator prompt example

I need to migrate the `cresta_to_snowflake` DAG.

Step 1: Pre-flight check
Run /validate-migration-readiness cresta_to_snowflake

[Review output]

Step 2: Understand structure
Run /analyze-legacy-dag cresta_to_snowflake

[Review output]

Step 3: Check for reusable code (CRITICAL)
Run /check-common-components

[Review output - if custom SFTP found, STOP and use operator]

Step 4: Identify problems
Run /find-anti-patterns cresta_to_snowflake

[Review output - prioritize fixes]

Step 5: Choose approach
Run /suggest-template-choice cresta_to_snowflake

[Review output - decide on TaskFlow vs Traditional]

... continue with implementation ...
```

### Parallel Execution:

For efficiency, some skills can run in parallel:

```markdown
# Phase 1 - Can run in parallel
- /validate-migration-readiness
- /analyze-legacy-dag

# Phase 2 - Run after Phase 1
- /check-common-components (sequential, critical)
- /find-anti-patterns

# Phase 3 - Can run in parallel after Phase 2
- /map-operators-to-common
- /extract-business-logic
- /analyze-connection-usage
- /suggest-template-choice

# Phase 4 - Implementation details (as needed)
- Run individually as needed during implementation
```

---

## 📝 Skill Outputs

All skills produce structured markdown reports with:
- ✅ Clear headers and sections
- 📊 Tables for comparisons
- 🔢 Metrics and statistics
- 💻 Code examples (before/after)
- ✅ Checklists for validation
- 🎯 Recommendations with reasoning

---

## 🧪 Testing After Migration

After using these skills to migrate:

```bash
# Validate DAG syntax
airflow dags list-import-errors

# Test DAG execution
airflow dags test my_dag 2024-01-01

# Test individual task
airflow tasks test my_dag task_id 2024-01-01
```

---

## 📚 Related Documentation

- **Main Guide**: `/claude_swarm/CLAUDE.md` - Core migration concepts
- **Common Components**: `/data-airflow/dags/common/` - Reusable operators/hooks
- **Templates**:
  - `/data-airflow/dags/_dag_taskflow_template/` - Pure Python
  - `/data-airflow/dags/_dag_template/` - Mixed operators

---

## 🤝 Contributing New Skills

To add a new skill:

1. Create `/Users/mike.porenta/python_dev/aptive_github/claude_swarm/.claude/skills/new-skill-name.md`
2. Follow the format:
   - `## Purpose`
   - `## When to Use`
   - `## Execution Steps` (with bash commands)
   - `## Output Report Format`
   - `## Enforcement`
3. Use actual paths: `/Users/mike.porenta/python_dev/aptive_github/data-airflow/...`
4. Include clear bash examples
5. Provide structured markdown output templates
6. Update this README with the new skill

---

## 🎓 For New Team Members

**Start here**:
1. Read `/claude_swarm/CLAUDE.md` for migration concepts
2. Review this README for skill workflow
3. Run `/validate-migration-readiness` on a DAG
4. Follow the recommended skill order
5. **NEVER skip `/check-common-components`**

**Remember**: The goal is DRY-compliant, modern, maintainable DAGs using existing common components wherever possible.

---

**Version**: 1.0
**Last Updated**: 2025-10-28
**Maintained By**: Data Engineering Team
