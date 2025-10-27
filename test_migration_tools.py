#!/usr/bin/env python3
"""Test script for migration tools."""

import asyncio
from util.helpers import file_path_creator
from src.tools.migration_tools import (
    detect_legacy_imports,
    detect_deprecated_parameters,
    compare_dags,
)


async def test_detect_legacy_imports(file_name: str):
    """Test detect_legacy_imports with invoca DAG."""
    print("\n" + "=" * 60)
    print("TEST 1: detect_legacy_imports on migrated invoca DAG")
    print("=" * 60)

    result = await detect_legacy_imports({
        "file_path": f"{file_path_creator('/data-airflow/dags/invoca_to_s3/')}/{file_name}"
    })

    print(result["content"][0]["text"])


async def test_detect_deprecated_parameters(file_name: str):
    """Test detect_deprecated_parameters with invoca DAG."""
    print("\n" + "=" * 60)
    print("TEST 2: detect_deprecated_parameters on migrated invoca DAG")
    print("=" * 60)

    result = await detect_deprecated_parameters({
        "file_path": f"{file_path_creator('/data-airflow/dags/invoca_to_s3')}/{file_name}"
    })

    print(result["content"][0]["text"])


async def test_compare_dags(file_name: str):
    """Test compare_dags between legacy and migrated."""
    print("\n" + "=" * 60)
    print("TEST 3: compare_dags (legacy vs migrated)")
    print("=" * 60)

    result = await compare_dags({
        "legacy_path": f"{file_path_creator('/data-airflow-legacy/dags/')}/{file_name}",
        "migrated_path": f"{file_path_creator('/data-airflow/dags/invoca_to_s3')}"
    })

    print(result["content"][0]["text"])


async def main():
    """Run all tests."""
    print("\n🧪 Testing Claude Swarm Migration Tools")
    print("=" * 60)

    try:
        await test_detect_legacy_imports()
        await test_detect_deprecated_parameters()
        await test_compare_dags()

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
