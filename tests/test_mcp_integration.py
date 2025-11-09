#!/usr/bin/env python3
"""
Test script to verify MCP migration tools integration with SwarmOrchestrator.

This tests that:
1. Migration tools are loaded successfully
2. MCP server is created
3. Tools are available in ClaudeAgentOptions
4. YAML configuration properly references MCP tools
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator import SwarmOrchestrator, MIGRATION_TOOLS_AVAILABLE
from rich.console import Console

console = Console()


def test_migration_tools_import():
    """Test 1: Verify migration tools can be imported."""
    console.print("\n[bold cyan]TEST 1: Migration Tools Import[/bold cyan]")
    console.print("=" * 60)

    if MIGRATION_TOOLS_AVAILABLE:
        console.print("[green]✅ Migration tools imported successfully[/green]")

        # Try importing them directly
        try:
            from src.tools.migration_tools import (
                detect_legacy_imports,
                detect_deprecated_parameters,
                compare_dags,
            )
            # MCP tools are SdkMcpTool objects, check their type
            console.print(f"  • detect_legacy_imports: {type(detect_legacy_imports).__name__}")
            console.print(f"  • detect_deprecated_parameters: {type(detect_deprecated_parameters).__name__}")
            console.print(f"  • compare_dags: {type(compare_dags).__name__}")
            return True
        except ImportError as e:
            console.print(f"[red]❌ Failed to import migration tools: {e}[/red]")
            return False
        except AttributeError as e:
            console.print(f"[red]❌ Attribute error with migration tools: {e}[/red]")
            return False
    else:
        console.print("[red]❌ Migration tools not available[/red]")
        return False


def test_mcp_server_creation():
    """Test 2: Verify MCP server creation in orchestrator."""
    console.print("\n[bold cyan]TEST 2: MCP Server Creation[/bold cyan]")
    console.print("=" * 60)

    try:
        # Create orchestrator instance
        config_path = project_root / "yaml_files" / "airflow_agent_options_local.yaml"

        if not config_path.exists():
            console.print(f"[red]❌ Config file not found: {config_path}[/red]")
            return False

        orchestrator = SwarmOrchestrator(config_path=config_path)

        # Check if MCP servers were created
        if hasattr(orchestrator.options, 'mcp_servers') and orchestrator.options.mcp_servers:
            console.print(f"[green]✅ MCP servers created: {list(orchestrator.options.mcp_servers.keys())}[/green]")

            # Check for migration server specifically
            if 'migration' in orchestrator.options.mcp_servers:
                console.print("  • [green]Migration server present[/green]")
                return True
            else:
                console.print("  • [red]Migration server not found[/red]")
                return False
        else:
            console.print("[yellow]⚠️  No MCP servers found in options[/yellow]")
            return False

    except Exception as e:
        console.print(f"[red]❌ Error creating orchestrator: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_yaml_tool_configuration():
    """Test 3: Verify YAML configuration has MCP tool references."""
    console.print("\n[bold cyan]TEST 3: YAML Tool Configuration[/bold cyan]")
    console.print("=" * 60)

    try:
        config_path = project_root / "yaml_files" / "airflow_agent_options_local.yaml"

        with open(config_path, 'r') as f:
            content = f.read()

        # Check for MCP tool references
        mcp_tools = [
            "mcp__migration__detect_legacy_imports",
            "mcp__migration__detect_deprecated_parameters",
            "mcp__migration__compare_dags"
        ]

        found_tools = []
        missing_tools = []

        for tool in mcp_tools:
            if tool in content:
                found_tools.append(tool)
            else:
                missing_tools.append(tool)

        if found_tools:
            console.print(f"[green]✅ Found {len(found_tools)}/{len(mcp_tools)} MCP tools in YAML:[/green]")
            for tool in found_tools:
                console.print(f"  • {tool}")

        if missing_tools:
            console.print(f"[yellow]⚠️  Missing {len(missing_tools)} MCP tools:[/yellow]")
            for tool in missing_tools:
                console.print(f"  • {tool}")
            return False

        return len(found_tools) == len(mcp_tools)

    except Exception as e:
        console.print(f"[red]❌ Error reading YAML: {e}[/red]")
        return False


def test_agent_tool_permissions():
    """Test 4: Verify agents have access to MCP tools."""
    console.print("\n[bold cyan]TEST 4: Agent Tool Permissions[/bold cyan]")
    console.print("=" * 60)

    try:
        config_path = project_root / "yaml_files" / "airflow_agent_options_local.yaml"
        orchestrator = SwarmOrchestrator(config_path=config_path)

        # Check migration-specialist agent
        if 'migration-specialist' in orchestrator.options.agents:
            agent = orchestrator.options.agents['migration-specialist']
            console.print("[green]✅ migration-specialist agent found[/green]")

            if hasattr(agent, 'tools'):
                console.print(f"  • Tools configured: {len(agent.tools)}")

                # Check for MCP tools
                mcp_tools_in_agent = [t for t in agent.tools if t.startswith('mcp__migration__')]
                if mcp_tools_in_agent:
                    console.print(f"  • MCP tools: {len(mcp_tools_in_agent)}")
                    for tool in mcp_tools_in_agent:
                        console.print(f"    - {tool}")
                    return True
                else:
                    console.print("  • [yellow]No MCP tools found in agent[/yellow]")
                    return False
            else:
                console.print("  • [red]Agent has no tools attribute[/red]")
                return False
        else:
            console.print("[red]❌ migration-specialist agent not found[/red]")
            return False

    except Exception as e:
        console.print(f"[red]❌ Error checking agent permissions: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests."""
    console.print("\n[bold magenta]╔════════════════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║   MCP Migration Tools Integration Test Suite          ║[/bold magenta]")
    console.print("[bold magenta]╚════════════════════════════════════════════════════════╝[/bold magenta]")

    results = {
        "Migration Tools Import": test_migration_tools_import(),
        "MCP Server Creation": test_mcp_server_creation(),
        "YAML Tool Configuration": test_yaml_tool_configuration(),
        "Agent Tool Permissions": test_agent_tool_permissions(),
    }

    # Summary
    console.print("\n[bold yellow]" + "=" * 60 + "[/bold yellow]")
    console.print("[bold yellow]TEST SUMMARY[/bold yellow]")
    console.print("[bold yellow]" + "=" * 60 + "[/bold yellow]")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "[green]✅ PASS[/green]" if result else "[red]❌ FAIL[/red]"
        console.print(f"{status} - {test_name}")

    console.print("\n" + "=" * 60)

    if passed == total:
        console.print(f"[bold green]🎉 ALL TESTS PASSED ({passed}/{total})[/bold green]")
        console.print("\n[green]Migration tools are successfully integrated![/green]")
        return 0
    else:
        console.print(f"[bold red]❌ SOME TESTS FAILED ({passed}/{total} passed)[/bold red]")
        console.print("\n[red]Please review the failures above.[/red]")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
