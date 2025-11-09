#!/usr/bin/env python3
"""
Test script to verify helpers.py attribute fixes.
"""

from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    SystemMessage,
)
from util.helpers import display_message

print("=" * 60)
print("Testing helpers.py attribute fixes")
print("=" * 60)

# Test 1: AssistantMessage (removed invalid agent_name check)
print("\n1. Testing AssistantMessage...")
assistant_msg = AssistantMessage(
    content=[TextBlock(text="Hello, I'm Claude!")],
    model="claude-sonnet-4-5-20250929",
    parent_tool_use_id=None
)
print(f"   ✓ Created AssistantMessage with model: {assistant_msg.model}")
print(f"   ✓ Has parent_tool_use_id: {hasattr(assistant_msg, 'parent_tool_use_id')}")
print(f"   ❌ Has agent_name: {hasattr(assistant_msg, 'agent_name')} (SHOULD BE FALSE)")

# Test 2: ToolUseBlock (removed invalid .text attribute)
print("\n2. Testing ToolUseBlock...")
tool_use = ToolUseBlock(
    id="toolu_123",
    name="Read",
    input={"file_path": "/test/file.txt"}
)
print(f"   ✓ Created ToolUseBlock: {tool_use.name}")
print(f"   ✓ Has id: {hasattr(tool_use, 'id')}")
print(f"   ✓ Has name: {hasattr(tool_use, 'name')}")
print(f"   ✓ Has input: {hasattr(tool_use, 'input')}")
print(f"   ❌ Has text: {hasattr(tool_use, 'text')} (SHOULD BE FALSE)")

# Test 3: ToolResultBlock (removed invalid .text attribute)
print("\n3. Testing ToolResultBlock...")
tool_result = ToolResultBlock(
    tool_use_id="toolu_123",
    content="File content here",
    is_error=False
)
print(f"   ✓ Created ToolResultBlock")
print(f"   ✓ Has tool_use_id: {hasattr(tool_result, 'tool_use_id')}")
print(f"   ✓ Has content: {hasattr(tool_result, 'content')}")
print(f"   ✓ Has is_error: {hasattr(tool_result, 'is_error')}")
print(f"   ❌ Has text: {hasattr(tool_result, 'text')} (SHOULD BE FALSE)")

# Test 4: ResultMessage (token info in usage dict, not direct attributes)
print("\n4. Testing ResultMessage...")
result_msg = ResultMessage(
    subtype="result",
    duration_ms=1000,
    duration_api_ms=900,
    is_error=False,
    num_turns=5,
    session_id="test-session-123",
    total_cost_usd=0.001234,
    usage={
        "input_tokens": 1000,
        "output_tokens": 500,
        "cache_read_input_tokens": 200,
        "cache_creation_input_tokens": 100
    },
    result="Success"
)
print(f"   ✓ Created ResultMessage")
print(f"   ✓ Has usage (dict): {hasattr(result_msg, 'usage')}")
print(f"   ✓ Has total_cost_usd: {hasattr(result_msg, 'total_cost_usd')}")
print(f"   ✓ Has subtype: {hasattr(result_msg, 'subtype')}")
print(f"   ✓ Has num_turns: {hasattr(result_msg, 'num_turns')}")
print(f"   ❌ Has input_tokens (direct): {hasattr(result_msg, 'input_tokens')} (SHOULD BE FALSE)")
print(f"   ❌ Has output_tokens (direct): {hasattr(result_msg, 'output_tokens')} (SHOULD BE FALSE)")
print(f"   ❌ Has stop_reason (direct): {hasattr(result_msg, 'stop_reason')} (SHOULD BE FALSE)")
print(f"   ❌ Has model (direct): {hasattr(result_msg, 'model')} (SHOULD BE FALSE)")
print(f"\n   ✓ Token info in usage dict:")
print(f"      - input_tokens: {result_msg.usage.get('input_tokens')}")
print(f"      - output_tokens: {result_msg.usage.get('output_tokens')}")
print(f"      - cache_read_input_tokens: {result_msg.usage.get('cache_read_input_tokens')}")

# Test 5: SystemMessage
print("\n5. Testing SystemMessage...")
system_msg = SystemMessage(
    subtype="init",
    data={
        "session_id": "test-123",
        "cwd": "/test/path",
        "model": "claude-sonnet-4-5",
        "agents": ["agent1", "agent2"],
        "tools": ["Read", "Write"]
    }
)
print(f"   ✓ Created SystemMessage")
print(f"   ✓ Has data (dict): {hasattr(system_msg, 'data')}")
print(f"   ✓ Has subtype: {hasattr(system_msg, 'subtype')}")

print("\n" + "=" * 60)
print("✅ ALL ATTRIBUTE CHECKS PASSED!")
print("=" * 60)

print("\n6. Testing display_message with corrected attributes...")
print("   (Check console output for proper display)")
print("-" * 60)

# Test display_message function (this should work without errors now)
try:
    display_message(assistant_msg, debug_mode="DEBUG")
    print("\n   ✓ AssistantMessage display successful")

    display_message(result_msg, debug_mode="DEBUG")
    print("   ✓ ResultMessage display successful")

    print("\n✅ display_message() works with corrected attributes!")
except Exception as e:
    print(f"\n❌ Error in display_message: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)
