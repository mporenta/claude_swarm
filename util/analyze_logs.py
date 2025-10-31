#!/usr/bin/env python3
"""
Enhanced Log Analyzer - Parse Claude Agent SDK logs.

Parses the actual log format:
[2025_10_30] raw message: 2025_10_30: MessageType(content=[...], ...)

Features:
- Track delegation flow (orchestrator → subagents)
- Extract file creation (Write/Edit tools)
- Parse cost and token usage from ResultMessage
- Identify issues (no delegation, no files, etc.)
- Create actionable diagnostics
"""

import re
import ast
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

def parse_log_line(line: str) -> Optional[Tuple[str, str]]:
    """
    Parse a single log line.

    Format: [2025_10_30] raw message: 2025_10_30: MessageType(...)

    Returns:
        (message_type, message_content) or None
    """
    match = re.search(r'\[[\d_]+\] raw message: [\d_]+: (\w+)\((.*)\)$', line, re.DOTALL)
    if match:
        msg_type = match.group(1)
        msg_content = match.group(2)
        return (msg_type, msg_content)
    return None

def extract_tool_uses_from_line(line: str) -> List[Dict]:
    """
    Extract all ToolUseBlock instances from a line.

    Format: ToolUseBlock(id='toolu_...', name='ToolName', input={{...}})
    """
    tools = []

    # Find all ToolUseBlock instances
    pattern = r"ToolUseBlock\(id='([^']+)',\s*name='([^']+)',\s*input=(\{(?:[^{}]|\{[^{}]*\})*\})\)"

    for match in re.finditer(pattern, line):
        tool_id = match.group(1)
        tool_name = match.group(2)
        input_str = match.group(3)

        # Try to parse input dict
        try:
            # Replace double braces with single braces for eval
            input_str_clean = input_str.replace('{{', '{').replace('}}', '}')
            tool_input = ast.literal_eval(input_str_clean)
        except:
            tool_input = {}

        tools.append({
            "id": tool_id,
            "name": tool_name,
            "input": tool_input,
            "line": line
        })

    return tools

def extract_result_message_data(line: str) -> Optional[Dict]:
    """
    Extract cost, tokens, and num_turns from ResultMessage.

    Format: ResultMessage(subtype='...', duration_ms=..., total_cost_usd=..., usage={{...}}, num_turns=...)
    """
    # Extract total_cost_usd
    cost_match = re.search(r'total_cost_usd=([\d.]+)', line)
    cost = float(cost_match.group(1)) if cost_match else 0.0

    # Extract num_turns
    turns_match = re.search(r'num_turns=(\d+)', line)
    num_turns = int(turns_match.group(1)) if turns_match else 0

    # Extract usage dict
    usage_match = re.search(r"usage=(\{[^}]+(?:\{[^}]+\}[^}]*)*\})", line)
    usage = {}
    if usage_match:
        try:
            usage_str = usage_match.group(1)
            # Clean up nested dicts
            usage_str = usage_str.replace('{{', '{').replace('}}', '}')
            usage = ast.literal_eval(usage_str)
        except Exception as e:
            # Fallback: extract tokens with regex
            input_tokens_match = re.search(r"'input_tokens':\s*(\d+)", line)
            output_tokens_match = re.search(r"'output_tokens':\s*(\d+)", line)
            cache_read_match = re.search(r"'cache_read_input_tokens':\s*(\d+)", line)
            cache_creation_match = re.search(r"'cache_creation_input_tokens':\s*(\d+)", line)

            usage = {
                'input_tokens': int(input_tokens_match.group(1)) if input_tokens_match else 0,
                'output_tokens': int(output_tokens_match.group(1)) if output_tokens_match else 0,
                'cache_read_input_tokens': int(cache_read_match.group(1)) if cache_read_match else 0,
                'cache_creation_input_tokens': int(cache_creation_match.group(1)) if cache_creation_match else 0,
            }

    return {
        "cost_usd": cost,
        "num_turns": num_turns,
        "input_tokens": usage.get('input_tokens', 0),
        "output_tokens": usage.get('output_tokens', 0),
        "cache_read_tokens": usage.get('cache_read_input_tokens', 0),
        "cache_creation_tokens": usage.get('cache_creation_input_tokens', 0)
    }

def extract_delegations(tool_uses: List[Dict]) -> List[Dict]:
    """Extract Task tool delegations to subagents."""
    delegations = []

    for tool in tool_uses:
        if tool['name'] == 'Task':
            delegation = {
                "tool_id": tool['id'],
                "subagent": tool['input'].get('subagent_type', 'unknown'),
                "description": tool['input'].get('description', ''),
                "prompt_preview": tool['input'].get('prompt', '')[:200] + "..." if tool['input'].get('prompt') else "",
                "model": tool['input'].get('model', 'N/A')
            }
            delegations.append(delegation)

    return delegations

def extract_file_operations(tool_uses: List[Dict]) -> Dict[str, List[str]]:
    """Extract file creation/modification from tool calls."""
    operations = {
        "created": [],
        "edited": [],
        "read": []
    }

    for tool in tool_uses:
        tool_name = tool['name']
        tool_input = tool['input']

        if tool_name == 'Write' and 'file_path' in tool_input:
            operations["created"].append(tool_input['file_path'])
        elif tool_name == 'Edit' and 'file_path' in tool_input:
            operations["edited"].append(tool_input['file_path'])
        elif tool_name == 'Read' and 'file_path' in tool_input:
            operations["read"].append(tool_input['file_path'])

    return operations

def identify_issues(stats: Dict, delegations: List, file_ops: Dict, tool_uses: List) -> List[str]:
    """Identify common orchestration issues."""
    issues = []

    # Issue 1: No delegations
    if len(delegations) == 0:
        issues.append("❌ NO DELEGATION: Orchestrator never delegated to subagents")

    # Issue 2: No files created
    if len(file_ops["created"]) == 0:
        issues.append("❌ NO FILES CREATED: Migration produced no output files")

    # Issue 3: Excessive tool use without delegation
    tool_use_count = len(tool_uses)
    if tool_use_count > 10 and len(delegations) == 0:
        issues.append(f"⚠️  MICRO-MANAGING: {tool_use_count} tool calls without delegation")

    # Issue 4: TodoWrite overhead
    todo_count = sum(1 for tool in tool_uses if tool['name'] == 'TodoWrite')
    if todo_count > 0:
        issues.append(f"⚠️  TODO OVERHEAD: {todo_count} TodoWrite calls")

    # Issue 5: Excessive exploration (Bash commands)
    bash_count = sum(1 for tool in tool_uses if tool['name'] == 'Bash')
    if bash_count > 5:
        issues.append(f"⚠️  EXCESSIVE EXPLORATION: {bash_count} Bash discovery commands")

    return issues

def parse_log_file(log_path: Path) -> Dict:
    """Parse log file and extract all data."""

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Statistics
    stats = {
        'total_lines': 0,
        'system_messages': 0,
        'assistant_messages': 0,
        'user_messages': 0,
        'result_messages': 0
    }

    tool_uses = []
    result_data = None

    # Parse each line
    for line in content.split('\n'):
        if not line.strip():
            continue

        stats['total_lines'] += 1

        # Parse the message
        parsed = parse_log_line(line)
        if not parsed:
            continue

        msg_type, msg_content = parsed

        # Count message types
        if msg_type == 'SystemMessage':
            stats['system_messages'] += 1
        elif msg_type == 'AssistantMessage':
            stats['assistant_messages'] += 1
            # Extract tool uses from AssistantMessage
            tools = extract_tool_uses_from_line(line)
            tool_uses.extend(tools)
        elif msg_type == 'UserMessage':
            stats['user_messages'] += 1
        elif msg_type == 'ResultMessage':
            stats['result_messages'] += 1
            # Extract cost and usage data
            result_data = extract_result_message_data(line)

    # Derived analysis
    delegations = extract_delegations(tool_uses)
    file_ops = extract_file_operations(tool_uses)
    issues = identify_issues(stats, delegations, file_ops, tool_uses)

    # Tool counts
    tool_counts = defaultdict(int)
    for tool in tool_uses:
        tool_counts[tool['name']] += 1

    return {
        "stats": stats,
        "tool_uses": tool_uses,
        "tool_counts": dict(tool_counts),
        "delegations": delegations,
        "file_ops": file_ops,
        "result_data": result_data or {},
        "issues": issues
    }

def create_diagnostic_report(output_dir: Path, analysis: Dict):
    """Create comprehensive diagnostic report."""
    report_file = output_dir / "00_DIAGNOSTIC_REPORT.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Orchestration Diagnostic Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        # Issues Section (Most Important)
        f.write("## 🚨 Issues Detected\n\n")
        if analysis["issues"]:
            for issue in analysis["issues"]:
                f.write(f"{issue}\n")
        else:
            f.write("✅ No major issues detected\n")
        f.write("\n---\n\n")

        # Executive Summary
        f.write("## 📊 Executive Summary\n\n")
        f.write(f"- **Total Messages**: {sum(analysis['stats'].values())}\n")
        f.write(f"- **Tool Calls**: {len(analysis['tool_uses'])}\n")
        f.write(f"- **Delegations**: {len(analysis['delegations'])}\n")
        f.write(f"- **Files Created**: {len(analysis['file_ops']['created'])}\n")
        f.write(f"- **Files Edited**: {len(analysis['file_ops']['edited'])}\n")

        if analysis['result_data']:
            result = analysis['result_data']
            f.write(f"- **Cost**: ${result.get('cost_usd', 0):.4f}\n")
            f.write(f"- **Turns**: {result.get('num_turns', 0)}\n")
            f.write(f"- **Input Tokens**: {result.get('input_tokens', 0):,}\n")
            f.write(f"- **Output Tokens**: {result.get('output_tokens', 0):,}\n")
            f.write(f"- **Cache Read**: {result.get('cache_read_tokens', 0):,}\n")
            f.write(f"- **Cache Creation**: {result.get('cache_creation_tokens', 0):,}\n")

        f.write("\n---\n\n")

        # Delegation Timeline
        f.write("## Delegation Timeline\n\n")
        if analysis['delegations']:
            for i, deleg in enumerate(analysis['delegations'], 1):
                f.write(f"### Delegation {i}: {deleg['subagent']}\n\n")
                f.write(f"- **Description**: {deleg['description']}\n")
                f.write(f"- **Model**: {deleg['model']}\n")
                f.write(f"- **Prompt Preview**: {deleg['prompt_preview']}\n")
                f.write("\n")
        else:
            f.write("⚠️  **No delegations occurred**\n\n")

        f.write("\n---\n\n")

        # File Operations
        f.write("## 📁 File Operations\n\n")
        if analysis['file_ops']['created']:
            f.write("### Files Created\n\n")
            for file in analysis['file_ops']['created']:
                f.write(f"- `{file}`\n")
            f.write("\n")
        else:
            f.write("⚠️  **No files were created**\n\n")

        if analysis['file_ops']['edited']:
            f.write("### Files Edited\n\n")
            for file in analysis['file_ops']['edited']:
                f.write(f"- `{file}`\n")
            f.write("\n")

        f.write("---\n\n")

        # Tool Usage Summary
        f.write("## 🔧 Tool Usage Summary\n\n")
        for tool_name in sorted(analysis['tool_counts'].keys()):
            count = analysis['tool_counts'][tool_name]
            f.write(f"- **{tool_name}**: {count} times\n")

        f.write("\n---\n\n")

        # Recommendations
        f.write("## 💡 Recommendations\n\n")

        if len(analysis['delegations']) == 0:
            f.write("- ❌ **Add delegation**: Orchestrator should delegate to subagents immediately\n")

        if len(analysis['file_ops']['created']) == 0:
            f.write("- ❌ **Enable file creation**: Ensure subagents have Write/Edit tool access\n")

        bash_count = analysis['tool_counts'].get('Bash', 0)
        if bash_count > 5:
            f.write(f"- ⚠️  **Reduce exploration**: {bash_count} Bash commands indicate micro-managing\n")

        if not analysis['issues']:
            f.write("✅ Session executed successfully with no major issues\n")

        f.write("\n")

    print(f"✓ Created: {report_file.name}")

def write_tool_details(output_dir: Path, analysis: Dict):
    """Write detailed tool execution log."""
    tools_file = output_dir / "01_tool_details.log"

    with open(tools_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Tool Execution Details\n")
        f.write("="*80 + "\n\n")

        if analysis['tool_uses']:
            for i, tool in enumerate(analysis['tool_uses'], 1):
                f.write(f"{i}. {tool['name']}\n")
                f.write(f"   ID: {tool['id']}\n")
                if tool['input']:
                    f.write(f"   Input: {tool['input']}\n")
                f.write("\n")
        else:
            f.write("No tool uses found.\n")

    print(f"✓ Created: {tools_file.name}")

def write_delegation_details(output_dir: Path, analysis: Dict):
    """Write delegation details if any exist."""
    if not analysis['delegations']:
        return

    deleg_file = output_dir / "02_delegations.log"

    with open(deleg_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Delegation Events\n")
        f.write("="*80 + "\n\n")

        for i, deleg in enumerate(analysis['delegations'], 1):
            f.write(f"Delegation {i}\n")
            f.write(f"  Subagent: {deleg['subagent']}\n")
            f.write(f"  Model: {deleg['model']}\n")
            f.write(f"  Description: {deleg['description']}\n")
            f.write(f"  Prompt Preview: {deleg['prompt_preview']}\n")
            f.write("\n")

    print(f"✓ Created: {deleg_file.name}")

def main():
    """Main execution."""
    project_root = Path(__file__).resolve().parent.parent
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = project_root / "logs" / f"{today}_log_to_file.log"
    output_dir = project_root / "logs" / "analyzed"

    print("="*80)
    print("Enhanced Log Analyzer - Claude Agent SDK Logs")
    print("="*80)
    print(f"\nInput: {log_path}")
    print(f"Output Directory: {output_dir}\n")

    if not log_path.exists():
        print(f"❌ Error: Log file not found at {log_path}")
        print(f"\nSearching for alternative log files...")

        # Search for any log file with "copy" in name
        log_dir = project_root / "logs"
        alt_logs = list(log_dir.glob("*log_to_file*.log"))
        if alt_logs:
            log_path = alt_logs[0]
            print(f"✓ Found: {log_path}")
        else:
            print(f"❌ No log files found in {log_dir}")
            return

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Parse the log
    print("Parsing log file...")
    analysis = parse_log_file(log_path)

    print(f"✓ Parsed {analysis['stats']['total_lines']} log lines\n")

    # Create reports
    print("Creating diagnostic report...")
    create_diagnostic_report(output_dir, analysis)

    print("\nCreating detailed logs...")
    write_tool_details(output_dir, analysis)
    write_delegation_details(output_dir, analysis)

    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print("="*80)
    print(f"\nOrganized logs saved to: {output_dir}/")
    print(f"Start with: {output_dir}/00_DIAGNOSTIC_REPORT.md")
    print("\n🔍 Issues detected:")
    if analysis['issues']:
        for issue in analysis['issues']:
            print(f"   {issue}")
    else:
        print("   ✅ No major issues detected")
    print()

if __name__ == "__main__":
    main()
