#!/usr/bin/env python3
"""
Log Analyzer - Parse and organize verbose orchestration logs by message type.
"""

import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def parse_log_file(log_path: Path):
    """Parse log file and categorize by message type."""

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by iteration markers
    iterations = re.split(r'ITERATION \d+ \|', content)

    # Storage for different message types
    chunks = {
        'system_messages': [],
        'assistant_messages': [],
        'user_messages': [],
        'tool_uses': [],
        'tool_results': [],
        'timing_info': [],
        'model_info': [],
        'subagent_responses': []
    }

    # Counters
    stats = defaultdict(int)

    # Parse each line
    for line in content.split('\n'):
        # Skip empty lines
        if not line.strip():
            continue

        # System Messages
        if 'SystemMessage' in line and 'subtype=' in line:
            chunks['system_messages'].append(line)
            stats['system_message'] += 1

        # Assistant Messages (Claude responses)
        elif 'AssistantMessage' in line and 'model=' in line:
            chunks['assistant_messages'].append(line)
            stats['assistant_message'] += 1

            # Check if it's a subagent
            if 'parent_tool_use_id=' in line and "parent_tool_use_id=None" not in line:
                chunks['subagent_responses'].append(line)
                stats['subagent_response'] += 1

        # User Messages (tool results)
        elif 'UserMessage' in line and 'ToolResultBlock' in line:
            chunks['user_messages'].append(line)
            stats['user_message'] += 1

        # Tool Uses
        elif 'ToolUseBlock' in line and 'name=' in line:
            chunks['tool_uses'].append(line)
            stats['tool_use'] += 1

        # Tool Results
        elif 'ToolResultBlock' in line and 'tool_use_id=' in line:
            chunks['tool_results'].append(line)
            stats['tool_result'] += 1

        # Timing information
        elif 'Iteration' in line and 'took:' in line:
            chunks['timing_info'].append(line)
            stats['timing'] += 1

        # Model information
        elif 'msg_model' in line or 'Using agent model' in line:
            chunks['model_info'].append(line)
            stats['model_info'] += 1

        # Subagent responses
        elif 'Subagent response' in line:
            chunks['subagent_responses'].append(line)

    return chunks, stats

def extract_tools_used(chunks):
    """Extract unique tools used from tool_uses."""
    tools = set()
    for line in chunks['tool_uses']:
        match = re.search(r"name='([^']+)'", line)
        if match:
            tools.add(match.group(1))
    return sorted(tools)

def extract_models_used(chunks):
    """Extract unique models used."""
    models = set()
    for line in chunks['model_info'] + chunks['assistant_messages']:
        # Look for model patterns
        match = re.search(r"model='([^']+)'", line)
        if match:
            models.add(match.group(1))
    return sorted(models)

def write_chunk_file(output_dir: Path, name: str, lines: list, header: str):
    """Write a chunk to a separate file."""
    output_file = output_dir / f"{name}.log"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"{'='*80}\n")
        f.write(f"{header}\n")
        f.write(f"Total entries: {len(lines)}\n")
        f.write(f"{'='*80}\n\n")

        for i, line in enumerate(lines, 1):
            f.write(f"{i:4d}. {line}\n")

    print(f"✓ Created: {output_file.name} ({len(lines)} entries)")

def create_summary_report(output_dir: Path, stats: dict, tools: list, models: list, chunks: dict):
    """Create a comprehensive summary report."""
    summary_file = output_dir / "00_SUMMARY.md"

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# Log Analysis Summary\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        # Statistics
        f.write("## Message Statistics\n\n")
        f.write("| Message Type | Count |\n")
        f.write("|--------------|-------|\n")
        for msg_type, count in sorted(stats.items()):
            f.write(f"| {msg_type.replace('_', ' ').title()} | {count} |\n")
        f.write(f"\n**Total Messages**: {sum(stats.values())}\n\n")

        # Tools Used
        f.write("## Tools Used\n\n")
        for tool in tools:
            tool_count = sum(1 for line in chunks['tool_uses'] if f"name='{tool}'" in line)
            f.write(f"- **{tool}**: {tool_count} times\n")
        f.write(f"\n**Total Unique Tools**: {len(tools)}\n\n")

        # Models Used
        f.write("## Models Used\n\n")
        for model in models:
            f.write(f"- `{model}`\n")
        f.write(f"\n**Total Models**: {len(models)}\n\n")

        # File Organization
        f.write("## Generated Files\n\n")
        f.write("The log has been split into the following files:\n\n")
        f.write("1. **01_system_messages.log** - System initialization messages\n")
        f.write("2. **02_assistant_messages.log** - Claude's responses (orchestrator)\n")
        f.write("3. **03_user_messages.log** - Tool execution results\n")
        f.write("4. **04_tool_uses.log** - All tool invocations\n")
        f.write("5. **05_tool_results.log** - Tool execution outputs\n")
        f.write("6. **06_subagent_responses.log** - Subagent communications\n")
        f.write("7. **07_timing_info.log** - Performance metrics per iteration\n")
        f.write("8. **08_model_info.log** - Model usage information\n\n")

        # Timing Analysis
        f.write("## Timing Analysis\n\n")
        timings = []
        for line in chunks['timing_info']:
            match = re.search(r'(\d+\.\d+)s', line)
            if match:
                timings.append(float(match.group(1)))

        if timings:
            f.write(f"- **Total Iterations**: {len(timings)}\n")
            f.write(f"- **Average Time**: {sum(timings)/len(timings):.3f}s\n")
            f.write(f"- **Fastest Iteration**: {min(timings):.3f}s\n")
            f.write(f"- **Slowest Iteration**: {max(timings):.3f}s\n")
            f.write(f"- **Total Time**: {sum(timings):.2f}s\n\n")

        # Subagent Analysis
        f.write("## Subagent Analysis\n\n")
        subagent_models = [m for m in models if 'haiku' in m.lower()]
        orchestrator_models = [m for m in models if 'sonnet' in m.lower()]

        f.write(f"- **Orchestrator Models**: {', '.join(orchestrator_models) if orchestrator_models else 'N/A'}\n")
        f.write(f"- **Subagent Models**: {', '.join(subagent_models) if subagent_models else 'N/A'}\n")
        f.write(f"- **Subagent Responses**: {stats.get('subagent_response', 0)}\n\n")

        f.write("---\n\n")
        f.write("## How to Use These Files\n\n")
        f.write("Each log file contains organized entries for a specific message type.\n")
        f.write("Use them to:\n\n")
        f.write("- **Debug**: Track specific tool calls and their results\n")
        f.write("- **Performance**: Analyze timing patterns\n")
        f.write("- **Flow**: Understand orchestrator → subagent communication\n")
        f.write("- **Optimization**: Identify slow operations or redundant calls\n\n")

    print(f"✓ Created: {summary_file.name}")

def main():
    """Main execution."""
    project_root = Path(__file__).resolve().parent.parent
    today = datetime.now().strftime("%Y_%m_%d")
    log_path = project_root / "logs" / f"{today}_file_only.log"
    output_dir = project_root / "logs" / "analyzed"

    print("="*80)
    print("Log Analyzer - Organizing Verbose Logs")
    print("="*80)
    print(f"\nInput: {log_path}")
    print(f"Output Directory: {output_dir}\n")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Parse the log
    print("Parsing log file...")
    chunks, stats = parse_log_file(log_path)

    # Extract metadata
    tools = extract_tools_used(chunks)
    models = extract_models_used(chunks)

    print(f"✓ Parsed {sum(stats.values())} total log entries\n")

    # Write chunk files
    print("Creating organized log files...")
    write_chunk_file(output_dir, "01_system_messages", chunks['system_messages'],
                     "System Messages - Initialization & Configuration")
    write_chunk_file(output_dir, "02_assistant_messages", chunks['assistant_messages'],
                     "Assistant Messages - Claude Orchestrator Responses")
    write_chunk_file(output_dir, "03_user_messages", chunks['user_messages'],
                     "User Messages - Tool Execution Results")
    write_chunk_file(output_dir, "04_tool_uses", chunks['tool_uses'],
                     "Tool Uses - All Tool Invocations")
    write_chunk_file(output_dir, "05_tool_results", chunks['tool_results'],
                     "Tool Results - Tool Execution Outputs")
    write_chunk_file(output_dir, "06_subagent_responses", chunks['subagent_responses'],
                     "Subagent Responses - Specialized Agent Communications")
    write_chunk_file(output_dir, "07_timing_info", chunks['timing_info'],
                     "Timing Information - Performance Metrics")
    write_chunk_file(output_dir, "08_model_info", chunks['model_info'],
                     "Model Information - Model Usage Details")

    print("\nCreating summary report...")
    create_summary_report(output_dir, stats, tools, models, chunks)

    print("\n" + "="*80)
    print("✅ Log analysis complete!")
    print("="*80)
    print(f"\nOrganized logs saved to: {output_dir}/")
    print(f"Start with: {output_dir}/00_SUMMARY.md")

if __name__ == "__main__":
    main()
