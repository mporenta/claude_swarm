# Quick Test Guide - New Main Prompt

## What Was Changed

### 1. New Main Prompt
- **File**: `prompts/main-query.md`
- **Lines**: 278 (was 61 lines)
- **Key Addition**: Explicit `@agent-name` delegation syntax

### 2. Code-Reviewer Tool Access
- **File**: `flask_agent_main.py:414`
- **Change**: Added "Bash" to tools list
- **Reason**: Needs to run flake8 and structure validation commands

---

## How to Test

### Step 1: Run the Orchestrator

```bash
cd /home/dev/claude_dev/claude_swarm

# Start the Flask agent orchestrator
python flask_agent_main.py

# When prompted, type:
flask
```

### Step 2: Monitor Output

Watch for agent delegation patterns in the terminal output:

**Expected to see**:
```
Turn 1: @flask-developer starting...
Creating app.py...
Creating requirements.txt...

Turn 2: @frontend-developer starting...
Creating templates/index.html...

Turn 3: @flask-developer starting...
Creating README.md...

Turn 4: @code-reviewer starting...
Running structure validation...
Running flake8...
```

**Should NOT see**:
```
Turn 1-59: Main orchestrator doing everything
[No agent delegation]
```

### Step 3: Check Logs

```bash
# Find today's log file
LOG_FILE="logs/$(date +%Y_%m_%d)_debug.log"

# Search for agent delegation
grep -E "@flask-developer|@frontend-developer|@code-reviewer" "$LOG_FILE"

# Should see multiple matches (old prompt showed 0 matches)
```

### Step 4: Review Metrics

At the end of execution, compare metrics:

| Metric | Old Value | Expected New | Status |
|--------|-----------|--------------|--------|
| Iterations | 59 | 15-20 | [ ] |
| Cost | $0.464 | $0.08-0.12 | [ ] |
| Time | 134.64s | 40-60s | [ ] |
| Agents Used | 0 | 3 | [ ] |
| Files Created | 4 | 4 | [ ] |

### Step 5: Verify Code Quality

```bash
cd generated_code/flask_app

# Check structure
find . -type f ! -path '*__pycache__*' | sort

# Expected output:
# ./README.md
# ./app.py
# ./requirements.txt
# ./templates/index.html

# Run flake8
flake8 app.py --max-line-length=88

# Expected output: (no errors)

# Count lines
wc -l app.py templates/index.html

# Expected: ~110 lines (app.py), ~85 lines (index.html)
```

---

## Success Criteria

### ✅ Must Pass:
1. [ ] Agents are invoked (grep shows @agent-name in logs)
2. [ ] Iterations < 25 (not 59)
3. [ ] Cost < $0.15 (not $0.46)
4. [ ] Time < 70s (not 135s)
5. [ ] All 4 files created correctly
6. [ ] flake8 passes with 0 errors
7. [ ] Code reviewer provides final verdict

### ✅ Nice to Have:
1. [ ] Iterations between 15-20 (optimal range)
2. [ ] Cost between $0.08-0.12 (optimal range)
3. [ ] Time between 40-60s (optimal range)
4. [ ] Code quality matches previous run (was excellent)
5. [ ] Clear agent turn boundaries in output

---

## Troubleshooting

### Issue: Agents Still Not Being Used

**Symptoms**:
- Main orchestrator does everything
- No @agent-name in logs
- High iteration count (50+)

**Potential Causes**:
1. Claude Agent SDK may not support `@agent-name` syntax
2. Delegation mechanism may be different than expected
3. System prompt may override agent delegation

**Actions**:
```bash
# Check SDK documentation
# Look at examples/agents.py for correct delegation syntax

# Try alternative syntax in main-query.md:
# Instead of: @flask-developer
# Try: "Delegate to flask-developer agent:"
# Or: "Task for flask-developer:"
```

### Issue: Code Reviewer Can't Run Bash

**Symptoms**:
- Error: "Tool 'Bash' not allowed for agent code-reviewer"
- Flake8 validation skipped

**Fix**:
Already fixed in `flask_agent_main.py:414` - verify the change:
```bash
grep -A2 "code-reviewer.*AgentDefinition" flask_agent_main.py | grep tools
# Should show: tools=["Read", "Grep", "Glob", "Bash"],
```

### Issue: Files Created in Wrong Location

**Symptoms**:
- app.py inside templates/
- Missing flask_app/ subdirectory

**Cause**:
Agent definitions include this warning, but may need emphasis

**Action**:
Already addressed in new prompt with explicit path validation

### Issue: High Iteration Count Despite New Prompt

**Symptoms**:
- Still 50+ iterations
- Agents are being used but taking too long

**Potential Causes**:
1. TodoWrite tool overhead (currently used 10+ times)
2. Verbose iteration logging
3. Too much context in prompts

**Actions**:
```bash
# Count TodoWrite uses in logs
grep -c "TodoWrite" "$LOG_FILE"

# If > 10, consider reducing or removing TodoWrite
# Simple tasks don't need todo tracking
```

---

## Baseline Comparison

### Old Run (2025-10-25 00:07-00:09)
```
Duration: 134.64s (2m 15s)
Iterations: 59
Cost: $0.463901
Token Usage:
  - Input: 120
  - Cache creation: 40,863
  - Cache reads: 714,094
  - Output: 6,272
Files Created: 4
Agents Used: 0 (main orchestrator only)
Quality: Excellent (PEP 8 compliant, production-ready)
```

### Expected New Run
```
Duration: 40-60s (~1m)
Iterations: 15-20
Cost: $0.08-0.12
Token Usage:
  - Input: ~200 (longer prompt)
  - Cache reads: <200k (less context reloading)
  - Output: ~4,000 (similar)
Files Created: 4
Agents Used: 3 (flask-developer, frontend-developer, code-reviewer)
Quality: Excellent (same or better)
```

### Key Improvements
- 66-70% fewer iterations
- 75-85% lower cost
- 55-70% faster
- Proper agent delegation
- Better separation of concerns

---

## After Testing

### If Successful:
1. Document metrics in `PERFORMANCE_COMPARISON.md`
2. Update README.md with prompt writing guidelines
3. Add example prompts to examples/ directory
4. Share improvements with team

### If Failed:
1. Review SDK documentation for delegation syntax
2. Check examples/agents.py for working patterns
3. Consider alternative orchestration approach
4. Document findings in TROUBLESHOOTING.md

---

## Quick Commands Reference

```bash
# Run orchestrator
python flask_agent_main.py

# Monitor logs in real-time
tail -f logs/$(date +%Y_%m_%d)_debug.log

# Search for agent delegation
grep "@" logs/$(date +%Y_%m_%d)_debug.log | head -20

# Check final metrics
tail -50 logs/$(date +%Y_%m_%d)_debug.log | grep -E "ITERATIONS|Cost|seconds"

# Verify generated files
ls -lh generated_code/flask_app/
find generated_code/flask_app -type f

# Test the app
cd generated_code/flask_app
python app.py
# Visit: http://localhost:5010
```

---

## Expected Terminal Output

### Start
```
╔══════════════════════════════════════════════════════╗
║  Flask Hello World App Generator (Markdown Prompts)  ║
╚══════════════════════════════════════════════════════╝

Using CLAUDE_MODEL env: sonnet

[Turn 1] You: flask

🚀 Starting Flask app orchestrator with markdown prompts...
```

### Agent Delegation (New)
```
============================================================
🔄 Starting orchestration iterations...
============================================================

────────────────────────────────────────────────────────────
📍 ITERATION 1 | Type: AssistantMessage
────────────────────────────────────────────────────────────

@flask-developer: Creating Flask application backend...

[Tool Use: Write - flask_app/app.py]
[Tool Use: Write - flask_app/requirements.txt]

────────────────────────────────────────────────────────────
📍 ITERATION 5 | Type: AssistantMessage
────────────────────────────────────────────────────────────

@frontend-developer: Creating HTML template...

[Tool Use: Write - flask_app/templates/index.html]
```

### Completion
```
🎯 CODE REVIEW RESULTS

📁 Structure: PASS
   ✅ app.py location: flask_app/app.py
   ✅ templates location: flask_app/templates/

🐍 Python Quality: PASS
   ✅ flake8: No errors

🎉 FINAL VERDICT: READY FOR PRODUCTION

============================================================
✅ Flask app creation complete!
============================================================

📊 ORCHESTRATION METRICS:
   • Total iterations: 18
   • Total cost: $0.09
   • Total duration: 45.2s

🔄 ITERATIONS: 18
============================================================
```

---

**Ready to test!** Run `python flask_agent_main.py` and type `flask` when prompted.
