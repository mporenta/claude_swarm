# Flask Agent Orchestrator - Debugging Guide

## Overview

The Flask Agent Orchestrator now includes comprehensive debugging features to help you:
- Track iteration counts for finding optimal `max_turns` settings
- Measure performance with detailed timing metrics
- Monitor costs per iteration and total
- View detailed agent activity and message content
- Optimize orchestration efficiency

## Quick Start

### Enable Debug Mode

Set the `LOG_LEVEL` environment variable to `DEBUG`:

```bash
export LOG_LEVEL=DEBUG
python flask_agent_main.py
```

Or in your `.env` file:
```
LOG_LEVEL=DEBUG
```

### Normal Mode (Less Verbose)

```bash
export LOG_LEVEL=INFO  # Default
python flask_agent_main.py
```

## Features Added

### 1. Iteration Tracking

**What It Does:**
- Counts every iteration through the orchestration loop
- Displays clear iteration headers with visual separators
- Helps you understand how many turns your agents need

**Output Example:**
```
============================================================
🔄 Starting orchestration iterations...
============================================================

────────────────────────────────────────────────────────────
📍 ITERATION 1 | Type: AssistantMessage
────────────────────────────────────────────────────────────
```

**Why It Matters:**
This helps you find the sweet spot for `ClaudeAgentOptions.max_turns`. If your orchestration typically completes in 5 iterations, you might set `max_turns=7` to allow some buffer.

### 2. Performance Timing

**What It Tracks:**
- Total elapsed time (start to finish)
- Time per iteration
- Average iteration time
- Fastest and slowest iterations

**Output Example:**
```
📊 ORCHESTRATION METRICS:
────────────────────────────────────────────────────────────
Iteration Metrics:
   • Total iterations: 5
   • Average time/iteration: 2.345s
   • Fastest iteration: 0.523s
   • Slowest iteration: 8.123s

⏱️  Iteration 1 took: 0.523s
⏱️  Iteration 2 took: 2.345s
```

**Why It Matters:**
- Identify slow iterations (usually tool-heavy operations)
- Optimize prompt size and complexity
- Predict total execution time for similar tasks

### 3. Cost Tracking

**What It Tracks:**
- Total cost in USD
- Cost per iteration (when available)
- Token usage (input, output, cache)

**Output Example:**
```
Cost & Time Metrics:
   • Total cost: $0.004523
   • Cost per iteration: $0.000905
   • Total duration: 11.73s

Token Usage:
   • Input tokens: 12,345
   • Output tokens: 3,456
   • Total tokens: 15,801
   • Cache read tokens: 8,234
   • Cache creation tokens: 1,234
```

**Why It Matters:**
- Budget management and cost optimization
- Identify expensive operations
- Compare costs across different orchestration strategies
- Monitor cache effectiveness

### 4. Content Metrics

**What It Tracks:**
- Text blocks (agent responses)
- Thinking blocks (reasoning steps)
- Tool uses (file operations, bash commands)
- Files created

**Output Example:**
```
Content Metrics:
   • Text blocks: 12
   • Thinking blocks: 8
   • Tool uses: 24
   • Files created: 6

Files created:
   1. /home/dev/claude_dev/generated_code/app.py
   2. /home/dev/claude_dev/generated_code/requirements.txt
   3. /home/dev/claude_dev/generated_code/templates/index.html
   4. /home/dev/claude_dev/generated_code/templates/about.html
   5. /home/dev/claude_dev/generated_code/static/style.css
   6. /home/dev/claude_dev/generated_code/README.md
```

**Why It Matters:**
- Understand agent behavior patterns
- Verify expected outputs
- Track complexity of generated solutions

### 5. Enhanced Debug Messages

**What You See in DEBUG Mode:**

#### For All Messages:
```
🔍 Debug [Iteration 3] | 14:23:45 | Type: AssistantMessage
```

#### For Text Blocks:
```
🤖 [14:23:45] Claude: Creating Flask application structure...
   Block 1/3 | Length: 234 chars
```

#### For Thinking Blocks:
```
💭 [14:23:45] Thinking: I need to create a Flask app with...
   Block 2/3 | Full length: 567 chars
   Full thinking: [complete thinking content displayed]
```

#### For Tool Use:
```
⚙️  [14:23:45] Tool Use: Write
   Input: {'file_path': '/home/dev/claude_dev/generated_code/app.py', 'content': '...'}...
   Block 3/3 | Tool ID: toolu_01ABC123
   Full input: [complete input displayed]
```

#### For Results:
```
✅ [14:23:45] Result Message Received
💰 Total Cost: $0.004523
📊 Token Usage Details:
   • Input tokens: 12,345
   • Output tokens: 3,456
   • Cache read tokens: 8,234
🔍 Result Message Details:
   Stop reason: end_turn
   Model: claude-sonnet-4-5-20250929
```

## Using the Debugging Features

### Finding Optimal max_turns

1. **Run with DEBUG mode:**
   ```bash
   export LOG_LEVEL=DEBUG
   python flask_agent_main.py
   ```

2. **Type "flask" at the prompt to start orchestration**

3. **Watch the iteration counter:**
   - Count how many iterations until `ResultMessage`
   - Note which iterations take longest
   - Identify patterns in tool usage

4. **Analyze the final summary:**
   ```
   🔄 ITERATIONS: 5
   ```

5. **Set max_turns:**
   - Typical completion: 5 iterations → set `max_turns=7`
   - Add 20-40% buffer for complex tasks
   - Start conservative, reduce if consistently finishing early

### Optimizing Performance

1. **Review iteration times:**
   - Look for slowest iterations
   - Check what tools were used in slow iterations
   - Consider if prompts can be more specific

2. **Monitor tool usage:**
   - High tool use count = more API calls = slower + more expensive
   - Can prompts be refined to reduce unnecessary tool calls?
   - Are agents re-reading files unnecessarily?

3. **Check thinking block counts:**
   - More thinking = better decisions but slower
   - Adjust prompt specificity to balance speed vs. quality

### Cost Optimization

1. **Compare runs:**
   ```bash
   # Run 1
   Total cost: $0.004523
   Iterations: 5
   Cost per iteration: $0.000905

   # After optimization
   Total cost: $0.002834
   Iterations: 4
   Cost per iteration: $0.000709
   ```

2. **Monitor cache effectiveness:**
   - High cache read tokens = good prompt reuse
   - Low cache usage = consider adding more context caching

3. **Token usage analysis:**
   - Input tokens too high? → Simplify prompts
   - Output tokens too high? → More specific instructions

## Example Debugging Session

```bash
$ export LOG_LEVEL=DEBUG
$ python flask_agent_main.py

Helper LOG_LEVEL: DEBUG
sonnet
╔══════════════════════════════════════════════════════╗
║  Flask Hello World App Generator (Markdown Prompts)  ║
╚══════════════════════════════════════════════════════╝

[Turn 1] You: flask

📁 Created project directory at: /home/dev/claude_dev/generated_code

🚀 Starting Flask app orchestrator with markdown prompts...

============================================================
🔄 Starting orchestration iterations...
============================================================

────────────────────────────────────────────────────────────
📍 ITERATION 1 | Type: AssistantMessage
────────────────────────────────────────────────────────────
🔍 Debug [Iteration 1] | 14:23:42 | Type: AssistantMessage

💭 [14:23:42] Thinking: I need to create a Flask application...
   Block 1/5 | Full length: 456 chars

🤖 [14:23:42] Claude: I'll create a Flask application for you...
   Block 2/5 | Length: 123 chars

⚙️  [14:23:42] Tool Use: Write
   Input: {'file_path': '/home/dev/claude_dev/generated_code/app.py'...
   Block 3/5 | Tool ID: toolu_01ABC123

⏱️  Iteration 1 took: 0.523s

[... more iterations ...]

────────────────────────────────────────────────────────────
📍 ITERATION 5 | Type: ResultMessage
────────────────────────────────────────────────────────────
✅ [14:23:54] Result Message Received
💰 Total Cost: $0.004523
📊 Token Usage Details:
   • Input tokens: 12,345
   • Output tokens: 3,456
   • Cache read tokens: 8,234
   • Cache creation tokens: 1,234
🔍 Result Message Details:
   Stop reason: end_turn
   Model: claude-sonnet-4-5-20250929

⏱️  Iteration 5 took: 1.234s

============================================================
✅ Flask app creation complete!
============================================================

📊 ORCHESTRATION METRICS:
────────────────────────────────────────────────────────────
Iteration Metrics:
   • Total iterations: 5
   • Average time/iteration: 2.345s
   • Fastest iteration: 0.523s
   • Slowest iteration: 8.123s

Content Metrics:
   • Text blocks: 12
   • Thinking blocks: 8
   • Tool uses: 24
   • Files created: 6

Cost & Time Metrics:
   • Total cost: $0.004523
   • Cost per iteration: $0.000905
   • Total duration: 11.73s

Token Usage:
   • Input tokens: 12,345
   • Output tokens: 3,456
   • Total tokens: 15,801

============================================================
⏱️  TOTAL TIME: 11.73 seconds
🔄 ITERATIONS: 5
============================================================
```

## Configuration in ClaudeAgentOptions

Based on your debugging analysis, configure max_turns:

```python
options = ClaudeAgentOptions(
    system_prompt="claude_code",
    setting_sources=["project"],
    cwd=str(output_dir),
    max_turns=7,  # Set based on typical iteration count + buffer
    agents={...},
    allowed_tools=[...],
    permission_mode="acceptEdits",
)
```

## Troubleshooting

### "Iteration count is always hitting max_turns"
- **Cause:** max_turns too low or agents in infinite loop
- **Solution:** Increase max_turns OR review agent prompts for clarity

### "Cost per iteration is very high"
- **Cause:** Large prompts, excessive tool use, or no caching
- **Solution:** Simplify prompts, add caching, reduce tool calls

### "Some iterations are extremely slow"
- **Cause:** Heavy I/O operations (file reads/writes, bash commands)
- **Solution:** Batch operations, optimize prompts to reduce tool calls

### "Debug output is too verbose"
- **Solution:** Set `LOG_LEVEL=INFO` for summary metrics only

## Best Practices

1. **Always start with DEBUG mode** when testing new orchestrations
2. **Log metrics to file** for comparison:
   ```bash
   python flask_agent_main.py 2>&1 | tee orchestration_metrics.log
   ```
3. **Track costs over time** to identify optimization opportunities
4. **Review iteration patterns** to refine agent prompts
5. **Set max_turns** with 20-40% buffer above typical completion
6. **Use INFO mode in production** to reduce log volume

## Summary

These debugging features give you complete visibility into:
- ✅ How many iterations your orchestration needs (for max_turns tuning)
- ✅ Exact timing per iteration and total
- ✅ Cost breakdown and token usage
- ✅ Agent behavior and content metrics
- ✅ Complete message flow in debug mode

Use this information to optimize your orchestration for speed, cost, and reliability!

## Related Files

- `flask_agent_main.py:137-283` - Enhanced orchestrator with metrics
- `util/helpers.py:28-175` - Enhanced display_message with debugging
- `util/log_set.py` - Logging configuration

## Need Help?

Run with DEBUG mode and review the detailed output to understand exactly what your agents are doing at each step!
