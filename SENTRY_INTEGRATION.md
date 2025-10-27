# Sentry Integration Guide for Claude Swarm

## Overview

Sentry integration has been added to `claude_swarm` to provide comprehensive error tracking and performance monitoring for Claude Agent SDK interactions. All messages flowing through the system are now automatically logged to Sentry with rich context.

## What Was Added

### 1. **Sentry Logging in `util/helpers.py`**

#### `debug_log()` Function
- **Breadcrumbs**: All debug messages are now sent to Sentry as breadcrumbs
- **Truncation**: Messages are truncated to 500 chars for privacy
- **Category**: `debug`

#### `display_message()` Function
Comprehensive tracking for all Claude SDK message types:

**UserMessage**
- Category: `user_input`
- Data: Message length, model info
- Truncation: 200 chars for privacy

**AssistantMessage - TextBlock**
- Category: `assistant_response`
- Data: Length, block index, total blocks, model
- Truncation: 200 chars

**AssistantMessage - ThinkingBlock**
- Category: `assistant_thinking`
- Level: `debug`
- Data: Thinking length, block index
- Truncation: 200 chars

**AssistantMessage - ToolUseBlock**
- **Span**: `gen_ai.execute_tool`
- **Breadcrumb**: Tool use details
- Data: Tool name, ID, input preview
- Truncation: 1000 chars for inputs

**ToolResultBlock**
- Category: `tool_result`
- Level: `error` if failed, `info` if success
- Data: Tool use ID, error status, result length

**SystemMessage**
- Category: `system_message`
- Data: Subtype, session ID, model, agent count, tool count

**ResultMessage** (Most comprehensive)
- **Sentry Contexts**:
  - `claude_usage`: Token usage metrics
  - `claude_metrics`: Cost, duration, num turns
- **Breadcrumb**: Summary of token usage
- **Data Captured**:
  - Input/output tokens
  - Cache read/creation tokens
  - Total cost in USD
  - Duration (ms)
  - API duration (ms)
  - Number of turns
  - Session ID
  - Stop reason

**Error Handling**
- Exception capture with context
- Message type, debug mode, iteration info

## Setup for Local Sentry (Docker Desktop, Port 9000)

### 1. **Start Sentry**

```bash
# If you have Sentry running via Docker Desktop on port 9000
docker ps | grep sentry

# Or start a new Sentry instance
docker run -d \
  -p 9000:9000 \
  --name sentry \
  sentry
```

### 2. **Get Your Sentry DSN**

1. Access Sentry UI: `http://localhost:9000`
2. Create a new project (Python/Flask)
3. Copy the DSN (looks like: `http://PUBLIC_KEY@localhost:9000/PROJECT_ID`)

### 3. **Configure Environment Variables**

Add to your `.env` file:

```bash
# Sentry Configuration
SENTRY_DSN=http://YOUR_PUBLIC_KEY@localhost:9000/PROJECT_ID
SENTRY_ENVIRONMENT=local

# Optional: Set to DEBUG to see more detail
LOG_LEVEL=DEBUG
```

### 4. **Initialize Sentry in Your Application**

Add this to your main application file (e.g., `main.py` or `src/orchestrator.py`):

```python
import os
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from dotenv import load_dotenv

load_dotenv()

# Initialize Sentry
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,  # 100% of transactions
        environment=os.getenv("SENTRY_ENVIRONMENT", "local"),
        send_default_pii=False,  # Privacy-first
        enable_tracing=True,  # Performance monitoring
        integrations=[
            LoggingIntegration(
                level=logging.INFO,  # Capture info logs as breadcrumbs
                event_level=logging.ERROR,  # Send errors as events
            ),
        ],
    )
    print("✅ Sentry monitoring initialized")
else:
    print("⚠️  SENTRY_DSN not set - monitoring disabled")
```

## Viewing Data in Sentry

### 1. **Breadcrumbs Trail**

In Sentry UI, you'll see a complete breadcrumb trail showing:
- User inputs
- Assistant responses
- Tool executions
- Tool results
- System messages
- Debug logs

### 2. **Performance Monitoring**

**Spans** show execution time for:
- Tool executions (`gen_ai.execute_tool`)
- Each tool has input/output data attached

**Contexts** provide structured data:
- `claude_usage`: All token metrics
- `claude_metrics`: Cost, duration, turns
- `system_message`: Session, model, agents, tools

### 3. **Error Tracking**

When errors occur:
- Full exception with stack trace
- Message type that caused error
- Debug mode and iteration info
- Complete breadcrumb trail leading to error

## Example Sentry Event Structure

```
Event: Claude Orchestration
├── Breadcrumbs
│   ├── [user_input] "Create a Flask app..."
│   ├── [assistant_thinking] "I need to create..."
│   ├── [tool_use] Tool: Write
│   ├── [tool_result] ✅ File created
│   ├── [assistant_response] "I've created..."
│   └── [result_message] Result: 2500 in, 800 out tokens
├── Contexts
│   ├── claude_usage
│   │   ├── input_tokens: 2500
│   │   ├── output_tokens: 800
│   │   ├── cache_read_input_tokens: 1000
│   │   └── cache_creation_input_tokens: 0
│   ├── claude_metrics
│   │   ├── total_cost_usd: 0.015
│   │   ├── duration_ms: 3245
│   │   ├── duration_api_ms: 2890
│   │   └── num_turns: 3
│   └── system_message
│       ├── model: claude-sonnet-4-5
│       ├── num_agents: 3
│       └── num_tools: 8
└── Spans
    ├── gen_ai.execute_tool: Write (duration: 150ms)
    ├── gen_ai.execute_tool: Read (duration: 75ms)
    └── gen_ai.execute_tool: Edit (duration: 120ms)
```

## Privacy Considerations

All logging includes privacy protections:
- User messages truncated to 200 chars
- Tool inputs truncated to 1000 chars
- `send_default_pii=False` in Sentry config
- No sensitive data in breadcrumbs by default

## Testing the Integration

```bash
# 1. Ensure Sentry is running
curl http://localhost:9000

# 2. Set your DSN
export SENTRY_DSN="http://YOUR_KEY@localhost:9000/1"
export SENTRY_ENVIRONMENT="local"

# 3. Run claude_swarm
python main.py --config yaml_files/flask_agent_options.yaml

# 4. Check Sentry UI
open http://localhost:9000
```

## Benefits

1. **Complete Visibility**: See every message, tool call, and response
2. **Performance Insights**: Token usage, costs, and duration tracking
3. **Error Context**: Rich context when things go wrong
4. **Cost Tracking**: Monitor Claude API costs in real-time
5. **Tool Analytics**: See which tools are used most frequently
6. **Session Tracking**: Follow conversations across turns

## Next Steps

- Add Sentry initialization to `src/orchestrator.py`
- Wrap orchestration calls in transactions
- Add custom spans for agent delegation
- Create Sentry alerts for high costs or errors
- Set up Sentry dashboards for monitoring

---

**Status**: ✅ Integrated and ready to use
**Dependencies**: `sentry-sdk>=2.0.0` (added to requirements.txt)
**Files Modified**:
- `util/helpers.py` (added Sentry logging)
- `requirements.txt` (added sentry-sdk)
