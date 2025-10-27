#!/usr/bin/env python3
"""Direct test of migration tool logic (without SDK wrapper)."""

import re
from pathlib import Path


def test_detect_legacy_imports_logic():
    """Test legacy import detection logic."""
    print("\n" + "=" * 60)
    print("TEST 1: Legacy Import Detection")
    print("=" * 60)

    file_path = Path("/home/dev/claude_dev/airflow/data-airflow/dags/invoca_to_s3/hourly.py")

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    content = file_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    # Check for legacy patterns
    legacy_patterns = [
        (r"from airflow\.operators\.python_operator", "PythonOperator uses deprecated import"),
        (r"from airflow\.operators\.bash_operator", "BashOperator uses deprecated import"),
        (r"from airflow\.operators\.dummy_operator", "DummyOperator uses deprecated import"),
        (r"from airflow\.contrib\.", "Contrib import is deprecated"),
        (r"from airflow\.\w+\.\w+_hook", "Hook import may be deprecated"),
    ]

    issues_found = []

    for line_num, line in enumerate(lines, 1):
        for pattern, description in legacy_patterns:
            if re.search(pattern, line):
                issues_found.append({
                    "line": line_num,
                    "content": line.strip(),
                    "issue": description
                })

    if issues_found:
        print(f"\n⚠️  Found {len(issues_found)} legacy import issue(s):\n")
        for issue in issues_found:
            print(f"Line {issue['line']}: {issue['issue']}")
            print(f"  {issue['content']}\n")
    else:
        print("\n✅ No legacy imports detected!")


def test_detect_deprecated_parameters_logic():
    """Test deprecated parameter detection logic."""
    print("\n" + "=" * 60)
    print("TEST 2: Deprecated Parameter Detection")
    print("=" * 60)

    file_path = Path("/home/dev/claude_dev/airflow/data-airflow/dags/invoca_to_s3/hourly.py")

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    content = file_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    # Check for deprecated parameters
    deprecated_patterns = [
        (r"provide_context\s*=\s*True", "provide_context=True is deprecated"),
        (r"provide_context\s*=\s*False", "provide_context=False is deprecated"),
    ]

    issues_found = []

    for line_num, line in enumerate(lines, 1):
        for pattern, description in deprecated_patterns:
            if re.search(pattern, line):
                issues_found.append({
                    "line": line_num,
                    "content": line.strip(),
                    "issue": description
                })

    if issues_found:
        print(f"\n⚠️  Found {len(issues_found)} deprecated parameter(s):\n")
        for issue in issues_found:
            print(f"Line {issue['line']}: {issue['issue']}")
            print(f"  {issue['content']}\n")
    else:
        print("\n✅ No deprecated parameters detected!")


def test_compare_structure():
    """Compare DAG structures."""
    print("\n" + "=" * 60)
    print("TEST 3: DAG Structure Comparison")
    print("=" * 60)

    legacy_path = Path("/home/dev/claude_dev/airflow/data-airflow-legacy/dags/invoca_to_snowflake.py")
    migrated_path = Path("/home/dev/claude_dev/airflow/data-airflow/dags/invoca_to_s3")

    print(f"\nLegacy DAG: {legacy_path}")
    print(f"  Exists: {legacy_path.exists()}")
    if legacy_path.exists():
        lines = legacy_path.read_text().splitlines()
        print(f"  Lines: {len(lines)}")
        print(f"  Type: Single file")

    print(f"\nMigrated DAG: {migrated_path}")
    print(f"  Exists: {migrated_path.exists()}")
    if migrated_path.exists():
        has_src = (migrated_path / "src").exists()
        print(f"  Has src/ dir: {has_src}")

        if has_src:
            py_files = list(migrated_path.rglob("*.py"))
            print(f"  Python files: {len(py_files)}")
            for py_file in py_files:
                rel_path = py_file.relative_to(migrated_path)
                lines = py_file.read_text().splitlines()
                print(f"    - {rel_path}: {len(lines)} lines")

    print("\n✅ Structure comparison complete!")


def main():
    """Run all direct tests."""
    print("\n🧪 Testing Migration Tool Logic (Direct)")
    print("=" * 60)

    test_detect_legacy_imports_logic()
    test_detect_deprecated_parameters_logic()
    test_compare_structure()

    print("\n" + "=" * 60)
    print("✅ All direct tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
