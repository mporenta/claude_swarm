# Implementation Summary: Skill Usage Criteria Integration

## Question: How do agents know about SKILL_USAGE_CRITERIA.md?

**Answer**: Via three integration points in the agent prompts:

---

## 1. Migration-Specialist Prompt Update

**File**: `/home/dev/claude_dev/claude_swarm/prompts/airflow_prompts/migration-specialist.md`

### Changes Made:

#### A. Added at Top (Lines 7-23):
```markdown
## 📋 FIRST TASK: Read Skill Usage Criteria

**BEFORE doing anything else**, read this file:
/home/dev/claude_dev/claude_swarm/SKILL_USAGE_CRITERIA.md

This file contains:
- Decision matrix for which skills to run based on DAG complexity
- File output guidelines (simple vs medium vs complex DAGs)
- Real production DAG comparison showing what "good" looks like
- Prevention of over-engineering (no unnecessary config.py, excessive docs)

**KEY PRINCIPLE**: "Migrate to 2.x syntax, not to 'best practice' abstractions."
- Simple DAGs (< 200 lines) → Stay simple (1-2 files max)
- Medium DAGs (200-500 lines) → Moderate structure (2-3 files)
- Complex DAGs (> 500 lines) → Full modular structure (3-5 files)
```

**Why This Works**: The agent's first instruction is now to read the criteria file, ensuring it has the context before any decisions.

#### B. Replaced "MANDATORY SKILLS WORKFLOW" Section (Lines 56-96):

**Before**:
```markdown
## 🔧 MANDATORY SKILLS WORKFLOW
Execute these skills in order BEFORE implementation:
### Phase 1: Pre-Migration Analysis (ALWAYS RUN FIRST)
1. /validate-migration-readiness
2. /analyze-legacy-dag
3. /check-common-components
4. /find-anti-patterns
[... all 13 skills listed as mandatory]
```

**After**:
```markdown
## 🔧 SKILL SELECTION: Use Criteria, Don't Run All

**CRITICAL**: Do NOT run all 13 skills for every migration. Use the decision matrix in SKILL_USAGE_CRITERIA.md.

### ALWAYS RUN (3 skills - MANDATORY for all migrations):
1. /check-common-components
2. /find-anti-patterns
3. /compare-dag-configs

### CONDITIONAL SKILLS (Run ONLY if condition met):
[Table with conditions for each skill]
```

**Impact**: Agent now knows to check criteria before running skills, not run all 13 automatically.

#### C. Updated Migration Playbook (Lines 104-167):

**Before**: Listed all skills sequentially across 7 steps

**After**:
```markdown
## Migration Playbook (Criteria-Based)
1. **Read & Assess** (Iteration 1)
   - FIRST: Read SKILL_USAGE_CRITERIA.md
   - SECOND: Read legacy DAG, count lines, assess structure
   - THIRD: Decide which skills to run based on criteria

2. **Run Mandatory Skills** (Iteration 2)
   - ALWAYS: /check-common-components, /find-anti-patterns, /compare-dag-configs

3. **Run Conditional Skills** (Iteration 3, if needed)
   - ONLY IF conditions match from criteria file
```

**Impact**: Agent follows a decision-tree approach rather than a "do everything" approach.

#### D. Updated Deliverables & Success Factors (Lines 169-193):

**Added**:
```markdown
- ✅ Read SKILL_USAGE_CRITERIA.md FIRST before any work
- ✅ Assessed DAG complexity (lines, structure) to determine file count
- ✅ Only ran 3 mandatory skills + conditional skills that matched criteria
- ✅ File count appropriate to complexity (simple DAG = 1-2 files, not 11)
- ✅ No unused code (no config.py that's not imported)
- ✅ Documentation minimal and focused (no 64 KB of docs for simple DAG)
```

**Impact**: Success is now measured by appropriate complexity, not by running all skills.

---

## 2. Orchestrator Prompt Update

**File**: `/home/dev/claude_dev/claude_swarm/src/agent_options.py`

### Changes Made (Lines 174-184):

**Before**:
```python
"Migrate {legacy_dag_full_path} from Airflow 1.x to 2.x.
Follow the skills workflow documented in your prompt.
Use common components from {common_components_path}.
Output files to {output_dag_full_path}.
Complete the migration and create all necessary files."
```

**After**:
```python
"Migrate {legacy_dag_full_path} from Airflow 1.x to 2.x.

CRITICAL INSTRUCTIONS:
1. FIRST: Read /home/dev/claude_dev/claude_swarm/SKILL_USAGE_CRITERIA.md - This defines which skills to run based on DAG complexity
2. Assess DAG complexity (lines, structure) to determine file output (1-2 files for simple, 2-3 for medium, 3-5 for complex)
3. Run ONLY mandatory skills + conditional skills that match criteria (don't run all 13 skills)
4. Use common components from {common_components_path} - NO custom implementations
5. Output files to {output_dag_full_path}
6. Keep it simple: Simple DAGs stay simple (1-2 files), don't over-engineer

KEY PRINCIPLE: 'Migrate to 2.x syntax, not to best practice abstractions.'"
```

**Impact**: The orchestrator now explicitly tells the migration-specialist to read the criteria file as the first step.

---

## 3. SKILL_USAGE_CRITERIA.md Document

**File**: `/home/dev/claude_dev/claude_swarm/SKILL_USAGE_CRITERIA.md`

### Contents:

1. **Over-Engineering Analysis** (Lines 1-50)
   - Comparison table: Real DAG (1 file, 156 lines) vs Generated (11 files, 262 lines + 64 KB docs)
   - Cost of over-engineering quantified

2. **Decision Tree** (Lines 52-140)
   - **ALWAYS RUN**: 3 mandatory skills
   - **CONDITIONALLY RUN**: 6 skills with specific conditions
   - **RARELY RUN**: 3 skills for special cases
   - **NEVER AUTO-RUN**: 1 skill (post-migration only)

3. **File Output Decision Matrix** (Lines 142-195)
   - Simple (< 200 lines): 1-2 files, 0-50 lines docs
   - Medium (200-500 lines): 2-3 files, 50-150 lines docs
   - Complex (> 500 lines): 3-5 files, 150-300 lines docs

4. **Real Example Analysis** (Lines 197-267)
   - Cresta DAG: What SHOULD have happened
   - Skills that should run: 3 only
   - Skills that should skip: 10
   - Expected output: 1 file (main.py ~180 lines)

5. **Quick Reference Tables** (Lines 269-310)
   - Skill decision matrix by DAG characteristics
   - File output guidelines

6. **Implementation Guide** (Lines 312-364)
   - How to update migration-specialist prompt
   - Expected outcomes after implementing criteria

7. **Test Cases** (Lines 366-392)
   - Simple DAG test case (cresta)
   - Medium DAG test case
   - Complex DAG test case

---

## How the Flow Works

### Current Workflow (After Changes):

```
┌─────────────────────────────────────────────────┐
│ 1. Orchestrator Receives User Request          │
│    - User provides legacy DAG path              │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│ 2. Orchestrator Delegates (Turn 1)             │
│    - Task tool → @migration-specialist          │
│    - Includes instruction:                      │
│      "FIRST: Read SKILL_USAGE_CRITERIA.md"      │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│ 3. Migration-Specialist Reads Criteria         │
│    - Read tool on SKILL_USAGE_CRITERIA.md       │
│    - Learns decision matrix                     │
│    - Understands file output guidelines         │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│ 4. Migration-Specialist Reads Legacy DAG       │
│    - Read tool on legacy DAG file               │
│    - Counts lines (156 lines)                   │
│    - Assesses structure (flat, operators only)  │
│    - Determines: SIMPLE DAG                     │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│ 5. Skill Selection Decision (Based on Criteria)│
│    - Check criteria: < 200 lines = Simple       │
│    - Check criteria: Flat structure = Simple    │
│    - Check criteria: Standard operators = Skip  │
│    - DECISION: Run 3 mandatory skills only      │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│ 6. Execute Mandatory Skills (3 skills)         │
│    - Skill: /check-common-components            │
│    - Skill: /find-anti-patterns                 │
│    - Skill: /compare-dag-configs                │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│ 7. Implement Migration (Based on Criteria)     │
│    - Create main.py (single file)               │
│    - Keep config inline (no config.py)          │
│    - Keep SQL queries inline                    │
│    - Use SFTPToSnowflakeOperator from common    │
│    - Optional: Create basic README              │
│    - TOTAL FILES: 1-2 max                       │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│ 8. Return to Orchestrator                      │
│    - Files created: 1-2 (not 11)                │
│    - Skills run: 3 (not 13)                     │
│    - Documentation: 0-50 lines (not 64 KB)      │
└─────────────────────────────────────────────────┘
```

---

## Expected Improvements (Cresta Example)

| Metric | Before (Current) | After (With Criteria) | Improvement |
|--------|------------------|----------------------|-------------|
| **Skills Run** | 13 | 3 | 77% reduction |
| **Files Created** | 11 | 1-2 | 82% reduction |
| **Code Lines** | 262 (214 unused) | ~180 (0 unused) | 31% reduction, 100% usable |
| **Documentation** | 64 KB (6 files) | 0-5 KB (0-1 file) | 92% reduction |
| **Dead Code** | 214 lines | 0 lines | 100% elimination |
| **Iterations Used** | 8+ | 3-4 | 50% reduction |
| **Cost per Migration** | $0.48 (222 messages) | Est. $0.15-0.20 | 60-70% reduction |

---

## Verification: How to Test

### Test 1: Check Agent Prompt Loading
```bash
# Verify migration-specialist prompt has the new content
grep -A 5 "FIRST TASK: Read Skill Usage Criteria" /home/dev/claude_dev/claude_swarm/prompts/airflow_prompts/migration-specialist.md

# Expected output:
## 📋 FIRST TASK: Read Skill Usage Criteria
**BEFORE doing anything else**, read this file:
/home/dev/claude_dev/claude_swarm/SKILL_USAGE_CRITERIA.md
```

### Test 2: Check Orchestrator Delegation
```bash
# Verify orchestrator prompt has the new delegation instructions
grep -A 8 "CRITICAL INSTRUCTIONS" /home/dev/claude_dev/claude_swarm/src/agent_options.py

# Expected output:
CRITICAL INSTRUCTIONS:
1. FIRST: Read /home/dev/claude_dev/claude_swarm/SKILL_USAGE_CRITERIA.md
2. Assess DAG complexity...
```

### Test 3: Run Migration and Check Logs
```bash
# Run the migration agent
cd /home/dev/claude_dev/claude_swarm
python airflow_agent_main.py

# After completion, analyze logs
python util/analyze_logs.py

# Expected results:
# - Skills run: 3 (check-common, find-anti-patterns, compare-configs)
# - Files created: 1-2 (main.py + optional README)
# - No config.py
# - Documentation: 0-50 lines
```

---

## Summary

### Three Integration Points:

1. **Migration-Specialist Prompt** (`prompts/airflow_prompts/migration-specialist.md`)
   - First instruction: Read SKILL_USAGE_CRITERIA.md
   - Replaced "run all skills" with criteria-based selection
   - Updated success factors to measure appropriate complexity

2. **Orchestrator Delegation** (`src/agent_options.py`)
   - User prompt now includes: "FIRST: Read SKILL_USAGE_CRITERIA.md"
   - Passes key principle: "Migrate to 2.x syntax, not to best practice abstractions"
   - Specifies file count expectations per complexity

3. **Criteria Document** (`SKILL_USAGE_CRITERIA.md`)
   - Decision tree for skill selection
   - File output guidelines
   - Real production DAG comparison
   - Test cases and expected outcomes

### Result:
The migration-specialist agent will:
1. **Read the criteria file** as its first action (via prompt instruction)
2. **Assess DAG complexity** before making any decisions
3. **Run only relevant skills** based on the decision matrix
4. **Create appropriate file count** based on complexity (not over-engineer)
5. **Keep documentation minimal** and focused

This prevents the over-engineering that produced 11 files with 214 lines of dead code and 64 KB of documentation for a simple 156-line DAG.
