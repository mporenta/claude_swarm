# Turn Limit Fix - Multi-Agent Orchestration

## Problem Summary

The orchestrator was running for **60-62 turns** despite `max_turns=25` being configured in `ClaudeAgentOptions`.

### Root Cause (Confirmed by Claude Docs)

Per the official Claude Agent SDK documentation:

- **`max_turns` only applies to the main orchestrator agent**
- **Subagents run WITHOUT turn limits** - `AgentDefinition` does NOT support a `max_turns` parameter
- When using the `Task` tool to delegate to subagents, each spawns its own conversation with **unlimited iterations**
- This is **intentional SDK design**, not a bug

### Evidence

From the previous run (`2025-10-28` logs):
- Main orchestrator configured: `max_turns=25`
- Actual execution: `num_turns=60` (240% over limit!)
- Subagent delegations: 119 calls total
- Task breakdown:
  - Orchestrator analysis: ~16 turns
  - `@migration-specialist`: ~25+ iterations (nested within Task tool)
  - `@airflow-code-reviewer`: ~15+ iterations (nested within Task tool)
  - Final wrap-up: ~4 turns

---

## Solution Applied

Following official SDK guidance, we've added **explicit iteration limits via prompt engineering** for each subagent.

### Changes Made

#### 1. Updated `migration-specialist` Subagent
**File**: `/home/dev/claude_dev/claude_swarm/src/agent_options.py:36-68`

**Added**:
```
⚠️ ITERATION LIMIT: You have a MAXIMUM of 8 tool-use iterations to complete your task.
- Iterations 1-2: Analysis (read legacy DAG, identify components)
- Iteration 3: Check existing components (run /check-common-components)
- Iterations 4-6: Implementation (write migrated DAG, documentation)
- Iterations 7-8: Final verification and handoff
```

**Why 8 iterations?**
- 2 for reading/analysis
- 1 for component verification (DRY enforcement)
- 3 for writing code and docs
- 2 for final checks
- Buffer for unexpected complexity

#### 2. Updated `airflow-code-reviewer` Subagent
**File**: `/home/dev/claude_dev/claude_swarm/prompts/airflow_prompts/airflow-code-reviewer.md:5-11`

**Added**:
```
⚠️ ITERATION LIMIT: You have a MAXIMUM of 5 tool-use iterations for code review.
- Iteration 1: Read migrated DAG file and documentation
- Iteration 2: Search/verify common components were used (Grep/Glob)
- Iteration 3: Run validation checks (flake8, grep patterns)
- Iterations 4-5: Compile comprehensive review report
```

**Why 5 iterations?**
- 1 for reading files
- 1 for searching/grepping
- 1 for validation commands (flake8, etc.)
- 2 for compiling comprehensive report
- Code review is more constrained than implementation

#### 3. Adjusted Orchestrator `max_turns`
**File**: `/home/dev/claude_dev/claude_swarm/src/agent_options.py:28`

**Changed**: `max_turns=25` → `max_turns=15`

**Why reduce?**
- Orchestrator should **delegate** work, not do it directly
- With subagent iteration limits in place, orchestrator can be more conservative
- Forces efficient delegation (consolidate analysis, provide complete context)
- Expected orchestrator work:
  - 2-3 turns: Initial analysis
  - 2-4 turns: Delegation to migration-specialist
  - 2-3 turns: Delegation to code-reviewer
  - 2-3 turns: Final synthesis and user communication
  - **Total: ~10-13 turns**

#### 4. Updated User Prompt
**File**: `/home/dev/claude_dev/claude_swarm/src/agent_options.py:85-127`

**Added**:
```
⚠️ EFFICIENCY REQUIREMENTS:
- You (orchestrator) have a maximum of 15 conversation turns
- Each subagent has iteration limits defined in their prompts:
  * @migration-specialist: 8 iterations max
  * @airflow-code-reviewer: 5 iterations max
- Delegate work efficiently and avoid unnecessary back-and-forth

## Delegation Best Practices
- Provide complete context to subagents (don't make them re-read files)
- Include analysis results, component inventory, and specific instructions
- Request comprehensive deliverables to minimize iteration rounds
```

**Why?**
- Makes the orchestrator **aware** of the constraints
- Encourages efficient delegation patterns
- Reduces "chatty" behavior between orchestrator and subagents

---

## Expected Behavior After Fix

### Turn Budget Breakdown

| Agent | Max Turns/Iterations | Expected Usage | Purpose |
|-------|---------------------|----------------|---------|
| **Orchestrator** | 15 | 10-13 | Analysis, delegation, synthesis |
| **migration-specialist** | 8 | 6-8 | Read, check components, implement, document |
| **airflow-code-reviewer** | 5 | 4-5 | Read, validate, report |
| **TOTAL** | 28 | 20-26 | Complete migration workflow |

### Workflow Optimization

**Before (60 turns total)**:
1. Orchestrator reads files → delegates → specialist re-reads → returns
2. Orchestrator processes → delegates again → reviewer re-reads → returns
3. Multiple back-and-forth cycles without clear context
4. Subagents running unlimited iterations

**After (20-26 turns expected)**:
1. Orchestrator consolidates analysis → delegates with full context → specialist implements efficiently
2. Orchestrator receives deliverable → delegates with specifics → reviewer validates efficiently
3. Single pass delegation with complete information
4. Subagents constrained by iteration limits

---

## Verification Steps

### 1. Syntax Check
```bash
python -m py_compile /home/dev/claude_dev/claude_swarm/src/agent_options.py
```

### 2. Run Test Migration
```bash
cd /home/dev/claude_dev/claude_swarm
python airflow_agent_main.py
# Select option 2: Legacy DAG migration
# Use: cresta_to_snowflake.py
```

### 3. Monitor Turn Usage
Watch for these metrics in console output:
```
SDK TURNS: X | MESSAGES: Y

Expected ranges:
- SDK TURNS: 20-26 (was 60-62)
- MESSAGES: 80-120 (was 110+)
```

### 4. Check Subagent Behavior
In logs, look for:
- Migration specialist completing in ~6-8 tool uses
- Code reviewer completing in ~4-5 tool uses
- Orchestrator staying under 15 turns

### 5. Quality Validation
Ensure output quality hasn't degraded:
- Migrated DAG still created
- Documentation still comprehensive
- Code review still thorough
- All deliverables present

---

## Troubleshooting

### If turn count is still high (>30):

**Check 1**: Are subagents respecting iteration limits?
- Look for phrases in logs: "Iteration X of 8" or "stopping due to limit"
- If not, the prompt may need stronger language

**Check 2**: Is orchestrator re-analyzing unnecessarily?
- Look for duplicate file reads or redundant searches
- May need to strengthen "delegation best practices" section

**Check 3**: Are subagents being called multiple times?
- Check logs for multiple `Task` tool invocations with same subagent
- May indicate orchestrator isn't getting complete deliverables

### If quality degrades:

**Increase iteration limits**:
- Migration specialist: 8 → 10
- Code reviewer: 5 → 6
- Orchestrator max_turns: 15 → 18

**Add more specific workflow guidance**:
- Break down complex steps further
- Provide examples of efficient iteration patterns

### If subagents exceed limits silently:

**Strengthen prompt language**:
```
⚠️ HARD LIMIT: You MUST stop after 8 iterations.
After iteration 8, summarize progress and STOP immediately.
```

**Add countdown tracking**:
```
Track your iteration count:
- [1/8] Read legacy DAG
- [2/8] Search components
...
```

---

## Key Takeaways

1. **SDK Limitation**: `max_turns` in `ClaudeAgentOptions` ONLY applies to main agent
2. **Subagents Run Unlimited**: `AgentDefinition` has no built-in turn/iteration limit parameter
3. **Prompt Engineering Solution**: Iteration limits must be enforced via explicit instructions
4. **Efficiency Matters**: Good delegation patterns reduce total turn consumption
5. **Monitor and Adjust**: Watch actual turn usage and tune limits accordingly

---

## References

- **Claude Docs Chatbot Response**: `/home/dev/claude_dev/claude_swarm/docs_help.md`
- **Official SDK Types**: `ClaudeAgentOptions`, `AgentDefinition`
- **Log Analysis**: `/home/dev/claude_dev/claude_swarm/logs/analyzed/00_SUMMARY.md`
- **Previous Run Metrics**: 60 turns, $1.74 cost, 865s duration

---

## Success Metrics

After implementing these changes, success is defined as:

✅ **Total turn count**: 20-26 (down from 60-62)
✅ **Quality maintained**: All deliverables still produced
✅ **Time reduced**: ~400-500s (down from 865s)
✅ **Cost reduced**: ~$0.70-1.00 (down from $1.74)
✅ **Efficiency improved**: Single-pass delegation vs. multiple rounds

---

**Updated**: 2025-10-28
**Status**: Ready for Testing
