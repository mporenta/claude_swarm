# Skill Usage Criteria - Airflow Migration Agents

## Critical Finding: Over-Engineering Problem

### The Real DAG vs Generated DAG Comparison

| Aspect | Real Production DAG | Generated Test DAG | Over-Engineering? |
|--------|---------------------|-------------------|------------------|
| **Files** | 1 file (`daily.py`, 156 lines) | 11 files (main.py, config.py, 6 docs) | ❌ YES - 11x files |
| **Structure** | Everything inline | Split: main + config + docs | ❌ YES - unnecessary separation |
| **Config** | Inline (lines 24-34) | Separate config.py (214 lines, UNUSED) | ❌ YES - dead code |
| **SQL Queries** | Inline strings (lines 48-125) | Inline strings (lines 89-168) | ✅ GOOD - both inline |
| **Documentation** | None (0 KB) | 6 files (64 KB total) | ❌ YES - excessive |
| **Type Hints** | None (Airflow 1.x) | 100% coverage | ⚠️ OVERKILL for simple DAG |
| **Operators** | SFTPToSnowflakeOperator | SFTPToSnowflakeOperator | ✅ GOOD - both use common |
| **Helper Tasks** | None | EmptyOperator start/end | ❌ YES - unnecessary |
| **Callbacks** | AirflowCallback from common | AirflowCallback from common | ✅ GOOD - both use common |

**Cost of Over-Engineering:**
- **11x file count** (1 file → 11 files)
- **214 lines of dead code** (config.py not imported)
- **64 KB of documentation** for a 3-task DAG
- **Cognitive overhead** - developers must understand modular structure for simple logic

---

## Root Cause: Too Many Skills, No Criteria

The migration system has **13 skills** but **no clear criteria** for when to use each skill. This leads to:
1. Agents running ALL skills unnecessarily
2. Over-engineering simple migrations
3. Creating abstractions that aren't needed
4. Excessive documentation generation

### Current Skills (13 Total)

#### Phase 1: Pre-Migration Analysis
1. `/validate-migration-readiness` - Pre-flight checklist
2. `/analyze-legacy-dag` - Parse legacy structure
3. `/check-common-components` - Find existing operators
4. `/find-anti-patterns` - Detect violations

#### Phase 2: Migration Planning
5. `/map-operators-to-common` - Match operators
6. `/extract-business-logic` - Plan code placement
7. `/suggest-template-choice` - Template decision
8. `/analyze-connection-usage` - Document connections

#### Phase 3: Implementation Details
9. `/compare-dag-configs` - Map parameters
10. `/check-xcom-patterns` - Convert XCom
11. `/identify-dependencies` - Convert dependencies
12. `/check-dynamic-tasks` - Convert loops

#### Phase 4: Validation
13. `/generate-migration-diff` - Value report

---

## NEW SKILL USAGE CRITERIA

### Decision Tree: When to Use Each Skill

#### ALWAYS RUN (Mandatory - 3 skills)
```
┌─────────────────────────────────────────┐
│ MANDATORY for ALL Migrations           │
├─────────────────────────────────────────┤
│ 1. /check-common-components             │  ⭐ CRITICAL - Prevents code duplication
│ 2. /find-anti-patterns                  │  ⭐ CRITICAL - Detects security issues
│ 3. /compare-dag-configs                 │  ⭐ CRITICAL - Ensures correct 2.x syntax
└─────────────────────────────────────────┘
```

**Rationale:**
- `/check-common-components` - Prevents 150-400 lines of redundant code
- `/find-anti-patterns` - Catches security issues, deprecated patterns
- `/compare-dag-configs` - Maps 1.x params to 2.x (schedule_interval → schedule, etc.)

#### CONDITIONALLY RUN (Run if condition met - 6 skills)

| Skill | Condition | Example | Run? |
|-------|-----------|---------|------|
| `/analyze-legacy-dag` | Legacy file > 200 lines OR complex structure | 425-line DAG with nested logic | ✅ YES |
| | Simple DAG < 200 lines, flat structure | cresta_to_snowflake (156 lines) | ❌ NO |
| `/map-operators-to-common` | Legacy uses custom operators/plugins | `from plugins.operators.custom import ...` | ✅ YES |
| | Legacy only uses standard operators | Only `SFTPToSnowflakeOperator` from common | ❌ NO |
| `/extract-business-logic` | DAG has helper functions OR complex Python | Functions, classes, data processing | ✅ YES |
| | DAG is operator config only | Only operator instantiation | ❌ NO |
| `/analyze-connection-usage` | DAG uses 3+ connections OR custom auth | MySQL, Postgres, SFTP, API | ✅ YES |
| | DAG uses 1-2 standard connections | Just `cresta_sftp` | ❌ NO |
| `/check-xcom-patterns` | Legacy has manual XCom (ti.xcom_push/pull) | `ti.xcom_push('key', value)` | ✅ YES |
| | No XCom usage | Tasks don't share data | ❌ NO |
| `/check-dynamic-tasks` | Legacy has loops creating tasks | `for item in items: PythonOperator(...)` | ✅ YES |
| | Static task definitions | Fixed set of tasks | ❌ NO |

#### RARELY RUN (Special cases only - 3 skills)

| Skill | When to Use | When to SKIP |
|-------|-------------|--------------|
| `/validate-migration-readiness` | First time migrating a team's DAGs, or complex multi-DAG dependency | Individual DAG migration |
| `/suggest-template-choice` | Unclear if TaskFlow or Traditional needed | Obvious choice (Python-only = TaskFlow) |
| `/identify-dependencies` | Complex cross-DAG dependencies or unclear lineage | Simple `>>` dependencies visible in code |

#### NEVER RUN AUTOMATICALLY (Post-migration only - 1 skill)

| Skill | When to Use |
|-------|-------------|
| `/generate-migration-diff` | **ONLY after migration complete** - generates value report for stakeholders |

---

## CRESTA Migration Example: What SHOULD Have Happened

### Legacy DAG Analysis (156 lines)
```python
# cresta_to_snowflake/daily.py
- Imports: 6 lines
- default_args: 12 lines
- Env config: 11 lines (if/elif/else)
- DAG definition: 11 lines
- 3 SQL queries: 77 lines
- 3 operator instantiations: 30 lines
```

**Complexity Assessment:**
- ✅ Simple structure (< 200 lines)
- ✅ Flat logic (no helper functions)
- ✅ Single operator type (SFTPToSnowflakeOperator)
- ✅ Single connection (cresta_sftp)
- ✅ No XCom usage
- ✅ Static tasks (no loops)

### Skills That SHOULD Have Run (3 only)

| Skill | Why? | Result |
|-------|------|--------|
| `/check-common-components` | ⭐ Mandatory - verifies SFTPToSnowflakeOperator exists in common | FOUND: Use existing operator ✓ |
| `/find-anti-patterns` | ⭐ Mandatory - checks for deprecated patterns | FOUND: `dag=dag` param deprecated ✓ |
| `/compare-dag-configs` | ⭐ Mandatory - maps 1.x to 2.x syntax | FOUND: schedule_interval → schedule, concurrency → max_active_tasks ✓ |

### Skills That Should NOT Have Run (10 skills)

| Skill | Why Skip? |
|-------|-----------|
| `/analyze-legacy-dag` | Simple 156-line file, flat structure |
| `/validate-migration-readiness` | Individual DAG, no blockers |
| `/map-operators-to-common` | Already using common operator |
| `/extract-business-logic` | No helper functions to extract |
| `/suggest-template-choice` | Obvious: operator-based = Traditional template |
| `/analyze-connection-usage` | Single connection (cresta_sftp) |
| `/check-xcom-patterns` | No XCom usage |
| `/identify-dependencies` | No dependencies (parallel tasks) |
| `/check-dynamic-tasks` | Static tasks (no loops) |
| `/generate-migration-diff` | Run AFTER completion, not during |

### Expected Output (Simple Migration)

**Files to Create:**
1. **main.py** (~180 lines) - Single file migration
   - Convert `DAG()` → `@dag`
   - Update parameters: `schedule_interval` → `schedule`, `concurrency` → `max_active_tasks`
   - Keep SQL queries inline
   - Keep env config inline
   - Use existing `SFTPToSnowflakeOperator` from common
   - Call decorated function: `cresta_to_snowflake_dag = cresta_to_snowflake()`

2. **README.md** (~50 lines, optional) - Basic usage
   - DAG purpose
   - Required connections
   - Schedule info
   - Owner/contact

**Files NOT to Create:**
- ❌ config.py - No need for separate config (inline is fine)
- ❌ MIGRATION.md - Excessive for simple migration
- ❌ MIGRATION_SUMMARY.md - Excessive
- ❌ QUICK_START.md - README is sufficient
- ❌ COMPLETION_REPORT.md - Excessive
- ❌ INDEX.md - Unnecessary

**Expected Complexity:**
- **1-2 files** (main.py + optional README)
- **~180 lines** of code (15% increase from 156 for @dag decorator syntax)
- **LOC reduction: N/A** (simple DAG, already using common operators)
- **Documentation: 0-50 lines** (1 README if needed)

---

## Skill Decision Matrix

### Quick Reference Table

| DAG Characteristic | Mandatory Skills | Conditional Skills | Skip Skills |
|-------------------|------------------|-------------------|-------------|
| **Simple (< 200 lines, flat)** | check-common, find-anti-patterns, compare-configs | None | All others |
| **Medium (200-500 lines)** | check-common, find-anti-patterns, compare-configs | analyze-legacy, map-operators | validate-readiness, suggest-template |
| **Complex (> 500 lines)** | check-common, find-anti-patterns, compare-configs | analyze-legacy, map-operators, extract-logic | None (evaluate all) |
| **Custom operators used** | check-common, find-anti-patterns, compare-configs | map-operators, extract-logic | — |
| **Manual XCom usage** | check-common, find-anti-patterns, compare-configs | check-xcom-patterns | — |
| **Dynamic task generation** | check-common, find-anti-patterns, compare-configs | check-dynamic-tasks | — |
| **Complex dependencies** | check-common, find-anti-patterns, compare-configs | identify-dependencies | — |

### File Output Decision Matrix

| DAG Complexity | Files to Create | Rationale |
|----------------|----------------|-----------|
| **Simple (< 200 lines)** | 1-2 files: main.py + optional README | Inline config, minimal docs |
| **Medium (200-500 lines)** | 2-3 files: main.py, src/main.py, README | Separate business logic if complex |
| **Complex (> 500 lines)** | 3-5 files: main.py, src/main.py, src/config.py, README, MIGRATION.md | Full modular structure |

**Documentation Guidelines:**
- **Simple DAG**: 0-50 lines (1 README if needed)
- **Medium DAG**: 50-150 lines (README + basic migration notes)
- **Complex DAG**: 150-300 lines (README + detailed MIGRATION.md)

---

## Implementation: Updating Migration-Specialist Prompt

### Current Problem
Migration-specialist prompt says:
> "Follow the skills workflow documented in your prompt."

This encourages running ALL 13 skills for every migration, leading to over-engineering.

### Proposed Solution

Add **Skill Decision Logic** to migration-specialist prompt:

```markdown
## Skill Selection (Use Criteria - Don't Run All)

### ALWAYS RUN (3 skills - MANDATORY):
1. /check-common-components - Prevent code duplication
2. /find-anti-patterns - Security and deprecation check
3. /compare-dag-configs - 1.x to 2.x parameter mapping

### ANALYZE FIRST, THEN DECIDE:

After reading the legacy DAG, assess:
- **Lines of code**: < 200 = Simple, 200-500 = Medium, > 500 = Complex
- **Structure**: Flat (operators only) vs Nested (helper functions/classes)
- **Operators**: Standard vs Custom/Plugin
- **XCom usage**: Manual (ti.xcom_push/pull) = YES, None = NO
- **Dynamic tasks**: Loops creating tasks = YES, Static = NO

### CONDITIONAL SKILLS (Run if condition met):

| Skill | Run If... |
|-------|----------|
| /analyze-legacy-dag | DAG > 200 lines OR nested structure |
| /map-operators-to-common | Uses custom operators from plugins/ |
| /extract-business-logic | Has helper functions OR complex Python |
| /analyze-connection-usage | Uses 3+ connections OR custom auth |
| /check-xcom-patterns | Has ti.xcom_push/pull |
| /check-dynamic-tasks | Has loops creating tasks |

### SKIP THESE (Unless special case):
- /validate-migration-readiness - Only for first team migration
- /suggest-template-choice - Only if truly unclear
- /identify-dependencies - Only for complex cross-DAG deps

### NEVER RUN DURING MIGRATION:
- /generate-migration-diff - Run AFTER completion only

## File Output Guidelines

**Simple DAG (< 200 lines):**
- Create: main.py (single file migration)
- Optional: README.md (if connections/setup needed)
- Skip: config.py, MIGRATION.md, other docs

**Medium DAG (200-500 lines):**
- Create: main.py, src/main.py (if business logic present)
- Create: README.md
- Skip: config.py (unless 10+ config values), excessive docs

**Complex DAG (> 500 lines):**
- Create: main.py, src/main.py, src/config.py (if warranted)
- Create: README.md, MIGRATION.md
- Skip: COMPLETION_REPORT.md, INDEX.md, SUMMARY.md (excessive)

**Documentation Limits:**
- Simple: 0-50 lines (1 README)
- Medium: 50-150 lines (README + notes)
- Complex: 150-300 lines (README + detailed docs)

NO DAG should generate 64 KB of documentation (6 files).
```

---

## Expected Outcomes After Implementing Criteria

### For Cresta Migration (Simple DAG)

**Before (Current):**
- Skills run: 13 (all skills)
- Files created: 11 (main.py, config.py, 6 docs, __init__, __pycache__)
- Lines of code: 262 (main.py + config.py)
- Documentation: 64 KB (6 markdown files)
- Unused code: 214 lines (config.py not imported)

**After (With Criteria):**
- Skills run: 3 (check-common, find-anti-patterns, compare-configs)
- Files created: 1-2 (main.py, optional README)
- Lines of code: ~180 (single main.py)
- Documentation: 0-50 lines (1 README if needed)
- Unused code: 0 lines

**Improvements:**
- ✅ 77% reduction in skills run (13 → 3)
- ✅ 82% reduction in files created (11 → 2)
- ✅ 31% reduction in code lines (262 → 180)
- ✅ 92% reduction in documentation (64 KB → 5 KB)
- ✅ 100% elimination of dead code (214 → 0)

### For Complex DAG (> 500 lines with business logic)

**Skills run:** 8-10 (all mandatory + relevant conditional)
**Files created:** 3-5 (main, src/main, src/config, README, MIGRATION.md)
**Outcome:** Appropriate modular structure for complexity

---

## Orchestrator Impact

### Current Orchestrator Behavior
```python
prompt = f"""Migrate {legacy_dag_path} from Airflow 1.x to 2.x.
Follow the skills workflow documented in your prompt.
"""
```

This says "follow the skills workflow" without criteria, leading to ALL skills being run.

### Recommended Orchestrator Update

```python
prompt = f"""Migrate {legacy_dag_path} from Airflow 1.x to 2.x.

SKILL USAGE:
- ALWAYS run: /check-common-components, /find-anti-patterns, /compare-dag-configs
- ANALYZE FIRST: Read the legacy DAG, assess complexity (LOC, structure)
- RUN CONDITIONALLY: Only run skills that match the DAG's characteristics
- KEEP SIMPLE: For DAGs < 200 lines, create 1-2 files max (main.py + optional README)

Refer to SKILL_USAGE_CRITERIA.md for full decision matrix.
"""
```

---

## Testing the New Criteria

### Test Case 1: Simple DAG (cresta_to_snowflake)
- **Input**: 156-line DAG, flat structure, standard operator
- **Expected Skills**: 3 (check-common, find-anti-patterns, compare-configs)
- **Expected Output**: main.py (~180 lines) + optional README
- **Pass Criteria**: No config.py, no excessive docs, < 5 skills run

### Test Case 2: Medium DAG (200-500 lines)
- **Input**: DAG with helper functions, 3+ connections
- **Expected Skills**: 5-6 (3 mandatory + analyze-legacy + map-operators + analyze-connections)
- **Expected Output**: main.py, src/main.py, README
- **Pass Criteria**: Business logic in src/, appropriate modularization

### Test Case 3: Complex DAG (> 500 lines)
- **Input**: Multi-operator DAG with custom logic, XCom, dynamic tasks
- **Expected Skills**: 8-10 (all relevant skills)
- **Expected Output**: main.py, src/main.py, src/config.py, README, MIGRATION.md
- **Pass Criteria**: Full modular structure, comprehensive docs

---

## Action Items

1. **Update migration-specialist prompt** with skill decision logic
2. **Update orchestrator prompt** to reference criteria
3. **Add SKILL_USAGE_CRITERIA.md to agent context** (this document)
4. **Test with cresta migration** to verify 3 skills run, 1-2 files created
5. **Monitor skill usage patterns** via log analyzer
6. **Iterate on criteria** based on results

---

## Summary: Key Principle

**"Migrate to 2.x syntax, not to 'best practice' abstractions."**

- **Simple DAGs stay simple** - Don't modularize flat operator configs
- **Complex DAGs get structure** - Only separate when complexity warrants it
- **Documentation is minimal** - 1 README, not 6 documentation files
- **Skills are surgical** - Run only what's needed, not everything

The goal is **Airflow 2.x compliance**, not **software engineering perfection**.
