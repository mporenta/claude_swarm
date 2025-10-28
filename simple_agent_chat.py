"""
Simple Claude Agent Chat - Send a message and get a response.
Usage: python simple_agent_chat.py "Your message here"
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import sys
from pathlib import Path

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    AssistantMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
)

async def send_message(message: str, project_dir: Path = None):
    """Send a single message to the Claude agent and return the response."""

    if project_dir is None:
        project_dir = Path(__file__).resolve().parent

    async def validate_bash_command(input_data, tool_use_id, context):
        """Block dangerous bash commands before execution."""
        if input_data["tool_name"] != "Bash":
            return {}

        command = input_data["tool_input"].get("command", "")
        dangerous_patterns = [
            "rm -rf",
            "dd if=",
            "mkfs",
            "> /dev/",
            "chmod 777",
            "curl | bash",
            "wget | sh",
        ]

        for pattern in dangerous_patterns:
            if pattern in command:
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"Blocked dangerous pattern: {pattern}",
                    }
                }
        return {}

    # Initialize agent options
    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
        },
        max_turns=15,
        model="sonnet",
        setting_sources=["project"],
        cwd=project_dir,
        permission_mode="plan",
        allowed_tools=[
            "Skill",
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Grep",
            "Glob",
        ],
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[validate_bash_command])
            ]
        },
    )

    client = ClaudeSDKClient(options)

    try:
        async with client:
            # Send the query
            await client.query(message)

            # Collect and print responses
            print("\n🤖 Agent Response:\n")
            print("=" * 60)

            async for response_message in client.receive_response():
                # Print the response in a simple format
                print(response_message)
                print("-" * 60)

            print("\n✅ Done!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ Usage: python simple_agent_chat.py \"Your message here\"\n")
        sys.exit(1)

    # Get message from command line argument
    user_message = " ".join(sys.argv[1:])

    print(f"\n🧑 You: {user_message}\n")

    # Run the async function
    asyncio.run(send_message(user_message))
