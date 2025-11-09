"""
Migration Tools for Airflow DAG Analysis.

Provides SDK MCP tools for detecting legacy patterns, deprecated parameters,
and comparing DAG migrations.
"""

import re
import ast
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from claude_agent_sdk import tool


@tool(
    "detect_legacy_imports",
    "Find Airflow 1.x legacy imports and suggest modern replacements",
    {"file_path": str}
)
async def detect_legacy_imports(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan Python file for deprecated Airflow 1.x import patterns.

    Detects:
    - *_operator imports (python_operator, bash_operator, dummy_operator)
    - *_hook imports (snowflake_hook, S3_hook, etc.)
    - .contrib.* imports (all deprecated)
    - Old sensor imports

    Returns JSON with:
    - List of legacy imports found
    - Line numbers for each
    - Suggested modern replacements
    - Severity level (critical, warning)
    """
    try:
        file_path = Path(args["file_path"])

        if not file_path.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: File not found: {file_path}"
                }],
                "is_error": True
            }

        # Read file content
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()

        # Legacy import patterns with replacements
        legacy_patterns = [
            # Operators
            {
                "pattern": r"from airflow\.operators\.python_operator import (\w+)",
                "replacement": "from airflow.operators.python import \\1",
                "severity": "critical",
                "description": "PythonOperator import uses deprecated path"
            },
            {
                "pattern": r"from airflow\.operators\.bash_operator import (\w+)",
                "replacement": "from airflow.operators.bash import \\1",
                "severity": "critical",
                "description": "BashOperator import uses deprecated path"
            },
            {
                "pattern": r"from airflow\.operators\.dummy_operator import DummyOperator",
                "replacement": "from airflow.operators.empty import EmptyOperator",
                "severity": "critical",
                "description": "DummyOperator is renamed to EmptyOperator in Airflow 2.x"
            },
            # Hooks
            {
                "pattern": r"from airflow\.contrib\.hooks\.(\w+)_hook import (\w+)",
                "replacement": "from airflow.providers... (check provider docs for exact path)",
                "severity": "critical",
                "description": "Contrib hooks are deprecated, use provider-based paths"
            },
            {
                "pattern": r"from airflow\.hooks\.(\w+)_hook import (\w+)",
                "replacement": "Check if custom hook exists in common.custom_hooks",
                "severity": "warning",
                "description": "Consider using custom hooks from common/ directory"
            },
            # Sensors
            {
                "pattern": r"from airflow\.sensors\.external_task_sensor import (\w+)",
                "replacement": "from airflow.sensors.external_task import \\1",
                "severity": "critical",
                "description": "Sensor import uses deprecated path"
            },
            # Contrib operators
            {
                "pattern": r"from airflow\.contrib\.operators\.(\w+)",
                "replacement": "from airflow.providers... (check provider docs)",
                "severity": "critical",
                "description": "Contrib operators are deprecated"
            },
        ]

        issues = []

        for line_num, line in enumerate(lines, 1):
            for pattern_info in legacy_patterns:
                match = re.search(pattern_info["pattern"], line)
                if match:
                    issues.append({
                        "line_number": line_num,
                        "line_content": line.strip(),
                        "pattern": pattern_info["description"],
                        "severity": pattern_info["severity"],
                        "suggested_fix": pattern_info["replacement"],
                        "matched_import": match.group(0)
                    })

        # Format results
        if not issues:
            result_text = f"✅ No legacy imports found in {file_path.name}\n\n"
            result_text += "All imports appear to use modern Airflow 2.x patterns."
        else:
            result_text = f"⚠️  Found {len(issues)} legacy import(s) in {file_path.name}\n\n"

            # Group by severity
            critical = [i for i in issues if i["severity"] == "critical"]
            warnings = [i for i in issues if i["severity"] == "warning"]

            if critical:
                result_text += f"## CRITICAL Issues ({len(critical)})\n\n"
                for issue in critical:
                    result_text += f"**Line {issue['line_number']}:** {issue['pattern']}\n"
                    result_text += f"```python\n{issue['line_content']}\n```\n"
                    result_text += f"**Suggested fix:**\n```python\n{issue['suggested_fix']}\n```\n\n"

            if warnings:
                result_text += f"## Warnings ({len(warnings)})\n\n"
                for issue in warnings:
                    result_text += f"**Line {issue['line_number']}:** {issue['pattern']}\n"
                    result_text += f"```python\n{issue['line_content']}\n```\n"
                    result_text += f"**Suggestion:** {issue['suggested_fix']}\n\n"

            # Add quick fix commands
            result_text += "\n## Quick Fix Commands\n\n"
            result_text += "```bash\n"
            result_text += f"# Fix PythonOperator import\n"
            result_text += f"sed -i 's/from airflow\\.operators\\.python_operator/from airflow.operators.python/' {file_path}\n\n"
            result_text += f"# Fix BashOperator import\n"
            result_text += f"sed -i 's/from airflow\\.operators\\.bash_operator/from airflow.operators.bash/' {file_path}\n\n"
            result_text += f"# Fix DummyOperator to EmptyOperator\n"
            result_text += f"sed -i 's/from airflow\\.operators\\.dummy_operator import DummyOperator/from airflow.operators.empty import EmptyOperator/' {file_path}\n"
            result_text += f"sed -i 's/DummyOperator/EmptyOperator/g' {file_path}\n"
            result_text += "```\n"

        return {
            "content": [{
                "type": "text",
                "text": result_text
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error analyzing imports: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "detect_deprecated_parameters",
    "Find deprecated Airflow 2.x parameters like provide_context",
    {"file_path": str}
)
async def detect_deprecated_parameters(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan Python file for deprecated Airflow parameters.

    Detects:
    - provide_context=True (deprecated in AF2)
    - execution_date usage (should use logical_date in AF2)
    - Old callback patterns

    Returns JSON with:
    - List of deprecated parameters found
    - Line numbers
    - Recommended actions
    """
    try:
        file_path = Path(args["file_path"])

        if not file_path.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: File not found: {file_path}"
                }],
                "is_error": True
            }

        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()

        deprecated_patterns = [
            {
                "pattern": r"provide_context\s*=\s*True",
                "issue": "provide_context parameter is deprecated",
                "action": "Remove this parameter (context is always provided in Airflow 2.x)",
                "severity": "critical"
            },
            {
                "pattern": r"provide_context\s*=\s*False",
                "issue": "provide_context parameter is deprecated",
                "action": "Remove this parameter",
                "severity": "warning"
            },
            {
                "pattern": r"['\"]execution_date['\"]",
                "issue": "execution_date is deprecated in Airflow 2.x",
                "action": "Consider using 'logical_date' instead",
                "severity": "warning"
            },
            {
                "pattern": r"kwargs\[['\"']execution_date['\"]\]",
                "issue": "Accessing execution_date from kwargs",
                "action": "Use kwargs['logical_date'] in Airflow 2.x",
                "severity": "warning"
            },
        ]

        issues = []

        for line_num, line in enumerate(lines, 1):
            for pattern_info in deprecated_patterns:
                if re.search(pattern_info["pattern"], line):
                    issues.append({
                        "line_number": line_num,
                        "line_content": line.strip(),
                        "issue": pattern_info["issue"],
                        "action": pattern_info["action"],
                        "severity": pattern_info["severity"]
                    })

        # Format results
        if not issues:
            result_text = f"✅ No deprecated parameters found in {file_path.name}\n\n"
            result_text += "Code appears to use modern Airflow 2.x patterns."
        else:
            result_text = f"⚠️  Found {len(issues)} deprecated parameter(s) in {file_path.name}\n\n"

            critical = [i for i in issues if i["severity"] == "critical"]
            warnings = [i for i in issues if i["severity"] == "warning"]

            if critical:
                result_text += f"## CRITICAL Issues ({len(critical)})\n\n"
                for issue in critical:
                    result_text += f"**Line {issue['line_number']}:** {issue['issue']}\n"
                    result_text += f"```python\n{issue['line_content']}\n```\n"
                    result_text += f"**Action:** {issue['action']}\n\n"

            if warnings:
                result_text += f"## Warnings ({len(warnings)})\n\n"
                for issue in warnings:
                    result_text += f"**Line {issue['line_number']}:** {issue['issue']}\n"
                    result_text += f"```python\n{issue['line_content']}\n```\n"
                    result_text += f"**Recommendation:** {issue['action']}\n\n"

            # Add quick fix commands
            result_text += "\n## Quick Fix Commands\n\n"
            result_text += "```bash\n"
            result_text += f"# Remove provide_context=True lines\n"
            result_text += f"sed -i '/provide_context=True,/d' {file_path}\n"
            result_text += f"sed -i '/provide_context=True$/d' {file_path}\n"
            result_text += "```\n"

        return {
            "content": [{
                "type": "text",
                "text": result_text
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error detecting deprecated parameters: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    "compare_dags",
    "Compare legacy and migrated DAG structures",
    {"legacy_path": str, "migrated_path": str}
)
async def compare_dags(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two DAG files/directories to validate migration.

    Analyzes:
    - Task counts
    - Import differences
    - Parameter changes
    - File structure differences

    Returns comparison report with:
    - Side-by-side task list
    - Import analysis
    - Structural changes
    - Migration completeness score
    """
    try:
        legacy_path = Path(args["legacy_path"])
        migrated_path = Path(args["migrated_path"])

        if not legacy_path.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Legacy file not found: {legacy_path}"
                }],
                "is_error": True
            }

        if not migrated_path.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Migrated file not found: {migrated_path}"
                }],
                "is_error": True
            }

        # Analyze both files
        legacy_analysis = _analyze_dag_file(legacy_path)
        migrated_analysis = _analyze_dag_file(migrated_path)

        # Build comparison report
        result_text = f"# DAG Migration Comparison\n\n"
        result_text += f"**Legacy:** `{legacy_path}`\n"
        result_text += f"**Migrated:** `{migrated_path}`\n\n"

        # File structure comparison
        result_text += "## File Structure\n\n"
        result_text += f"| Aspect | Legacy | Migrated |\n"
        result_text += f"|--------|--------|----------|\n"
        result_text += f"| Lines of code | {legacy_analysis['line_count']} | {migrated_analysis['line_count']} |\n"
        result_text += f"| File count | {legacy_analysis['file_count']} | {migrated_analysis['file_count']} |\n"
        result_text += f"| Has src/ dir | {legacy_analysis['has_src_dir']} | {migrated_analysis['has_src_dir']} |\n\n"

        # Import comparison
        result_text += "## Import Analysis\n\n"
        result_text += f"**Legacy Imports:** {len(legacy_analysis['imports'])}\n"
        for imp in legacy_analysis['imports'][:5]:
            result_text += f"- `{imp}`\n"
        if len(legacy_analysis['imports']) > 5:
            result_text += f"- ... and {len(legacy_analysis['imports']) - 5} more\n"

        result_text += f"\n**Migrated Imports:** {len(migrated_analysis['imports'])}\n"
        for imp in migrated_analysis['imports'][:5]:
            result_text += f"- `{imp}`\n"
        if len(migrated_analysis['imports']) > 5:
            result_text += f"- ... and {len(migrated_analysis['imports']) - 5} more\n"

        # Check for legacy imports in migrated
        legacy_imports_remaining = [
            imp for imp in migrated_analysis['imports']
            if '_operator' in imp or '_hook' in imp or 'contrib' in imp
        ]

        if legacy_imports_remaining:
            result_text += f"\n⚠️  **Warning:** {len(legacy_imports_remaining)} legacy import(s) still present in migrated code:\n"
            for imp in legacy_imports_remaining:
                result_text += f"- `{imp}`\n"

        # Task ID comparison
        result_text += "\n## Tasks\n\n"
        result_text += f"**Legacy task count:** {len(legacy_analysis['task_ids'])}\n"
        result_text += f"**Migrated task count:** {len(migrated_analysis['task_ids'])}\n\n"

        if legacy_analysis['task_ids'] and migrated_analysis['task_ids']:
            result_text += "Task ID comparison:\n"
            all_tasks = set(legacy_analysis['task_ids']) | set(migrated_analysis['task_ids'])
            for task_id in sorted(all_tasks):
                in_legacy = task_id in legacy_analysis['task_ids']
                in_migrated = task_id in migrated_analysis['task_ids']
                if in_legacy and in_migrated:
                    result_text += f"- ✅ `{task_id}` (present in both)\n"
                elif in_legacy:
                    result_text += f"- ⚠️  `{task_id}` (only in legacy)\n"
                else:
                    result_text += f"- ➕ `{task_id}` (new in migrated)\n"

        # Migration completeness score
        result_text += "\n## Migration Completeness\n\n"

        score = 0
        max_score = 5

        # Check 1: Has src/ directory
        if migrated_analysis['has_src_dir']:
            score += 1
            result_text += "- ✅ Has modular src/ directory structure\n"
        else:
            result_text += "- ❌ Missing src/ directory structure\n"

        # Check 2: No legacy imports
        if not legacy_imports_remaining:
            score += 1
            result_text += "- ✅ No legacy imports detected\n"
        else:
            result_text += f"- ❌ {len(legacy_imports_remaining)} legacy import(s) remaining\n"

        # Check 3: Task preservation
        if set(legacy_analysis['task_ids']).issubset(set(migrated_analysis['task_ids'])):
            score += 1
            result_text += "- ✅ All legacy tasks preserved\n"
        else:
            result_text += "- ⚠️  Some legacy tasks may be missing\n"

        # Check 4: Uses custom hooks
        uses_custom_hooks = any('common.custom_hooks' in imp for imp in migrated_analysis['imports'])
        if uses_custom_hooks:
            score += 1
            result_text += "- ✅ Uses custom hooks from common/\n"
        else:
            result_text += "- ⚠️  Not using custom hooks from common/\n"

        # Check 5: Modern callbacks
        uses_modern_callbacks = any('common.custom_callbacks' in imp for imp in migrated_analysis['imports'])
        if uses_modern_callbacks:
            score += 1
            result_text += "- ✅ Uses modern callbacks from common/\n"
        else:
            result_text += "- ⚠️  Not using modern callbacks\n"

        result_text += f"\n**Overall Score:** {score}/{max_score} ({int(score/max_score*100)}%)\n\n"

        if score == max_score:
            result_text += "🎉 **Excellent!** Migration appears complete and follows best practices.\n"
        elif score >= 3:
            result_text += "👍 **Good!** Migration is mostly complete. Address remaining issues.\n"
        else:
            result_text += "⚠️  **Needs Work:** Significant migration work still needed.\n"

        return {
            "content": [{
                "type": "text",
                "text": result_text
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error comparing DAGs: {str(e)}"
            }],
            "is_error": True
        }


def _analyze_dag_file(path: Path) -> Dict[str, Any]:
    """Analyze a DAG file or directory for comparison."""
    analysis = {
        "line_count": 0,
        "file_count": 1,
        "has_src_dir": False,
        "imports": [],
        "task_ids": [],
    }

    # If it's a directory, analyze the main DAG file and check structure
    if path.is_dir():
        analysis["has_src_dir"] = (path / "src").exists()
        analysis["file_count"] = len(list(path.rglob("*.py")))

        # Find main DAG file (hourly.py, daily.py, etc.)
        dag_files = list(path.glob("*.py"))
        if dag_files:
            path = dag_files[0]  # Use first DAG file found
        else:
            return analysis

    # Analyze the file
    content = path.read_text(encoding='utf-8')
    lines = content.splitlines()
    analysis["line_count"] = len(lines)

    # Extract imports
    import_pattern = r"^(?:from|import)\s+[\w\.]+"
    for line in lines:
        if re.match(import_pattern, line):
            analysis["imports"].append(line.strip())

    # Extract task IDs (simple pattern matching)
    task_id_pattern = r"task_id\s*=\s*['\"]([^'\"]+)['\"]"
    for line in lines:
        match = re.search(task_id_pattern, line)
        if match:
            analysis["task_ids"].append(match.group(1))

    return analysis
