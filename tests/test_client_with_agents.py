#!/usr/bin/env python3
"""
Enhanced test for Claude agent client with frontmatter agents.

This test validates the complete flow including frontmatter agent discovery:
1. YAML config → config_loader.py → ClaudeAgentOptions
2. Frontmatter agents discovered from .claude/agents/
3. Agents merged into ClaudeAgentOptions
4. ClaudeAgentOptions passed to ClaudeSDKClient
5. Client successfully instantiated with all agents

This mimics what SwarmOrchestrator does in its initialization.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.config_loader import load_agent_options_from_yaml
from util.agent_loader import discover_agents
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition
from util.log_set import logger
from util.log_set import logger
from rich.console import Console
from util.helpers import debug_log
console = Console()

def test_client_with_agents(config_path: str) -> bool:
    """
    Test the complete client instantiation flow with agents.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        True if successful, False otherwise
    """
    console.print("\n" + "="*60)
    console.print("Claude Agent Client Test (with Frontmatter Agents)")
    console.print("="*60 + "\n")

    try:
        # Step 1: Build context
        console.print("Step 1: Building context...")
        context = {
            "project_root": project_root,
            "output_dir": project_root / "generated_code",
            "AIRFLOW_HOME": Path.home() / "claude_dev" / "airflow",
            "AIRFLOW_2_DAGS_DIR": Path.home() / "claude_dev" / "airflow" / "data-airflow" / "dags",
            "AIRFLOW_LEGACY_DAGS_DIR": Path.home() / "claude_dev" / "airflow" / "data-airflow-legacy" / "dags",
            "AIRFLOW_2_ROOT": Path.home() / "claude_dev" / "airflow" / "data-airflow",
            "AIRFLOW_LEGACY_ROOT": Path.home() / "claude_dev" / "airflow" / "data-airflow-legacy",
            "PYTHONPATH": "/opt/airflow/dags",
            "CLAUDE_MODEL": "sonnet",
        }
        console.print(f"✅ Context built")
        console.print()

        # Step 2: Load ClaudeAgentOptions from YAML
        console.print("Step 2: Loading ClaudeAgentOptions from YAML...")
        console.print(f"   Config: {config_path}")

        options: ClaudeAgentOptions = load_agent_options_from_yaml(
            config_path=config_path,
            context=context
        )

        yaml_agent_count = len(options.agents)
        console.print(f"✅ ClaudeAgentOptions loaded")
        console.print(f"   Agents from YAML: {yaml_agent_count}")
        console.print("options")
        console.print(options)
        console.print()

        # Step 3: Discover frontmatter agents (mimics orchestrator)
        console.print("Step 3: Discovering frontmatter agents...")
        console.print(f"   Looking in: {project_root}/.claude/agents/")

        frontmatter_agents = discover_agents(project_root)

        console.print(f"✅ Discovered {len(frontmatter_agents)} frontmatter agent(s)")
        for agent_name in frontmatter_agents.keys():
            console.print(f"   • {agent_name}")
        console.print(frontmatter_agents)
        console.print()

        # Step 4: Merge frontmatter agents (mimics orchestrator)
        console.print("Step 4: Merging frontmatter agents into ClaudeAgentOptions...")

        merged_count = 0
        skipped_count = 0

        for agent_name, agent_def in frontmatter_agents.items():
            if agent_name not in options.agents:
                options.agents[agent_name] = agent_def
                merged_count += 1
                console.print(f"   ✅ Added: {agent_name}")
            else:
                skipped_count += 1
                console.print(f"   ⚠️  Skipped: {agent_name} (overridden by YAML)")

        console.print(f"\n✅ Merge complete:")
        console.print(f"   - Added: {merged_count}")
        console.print(f"   - Skipped: {skipped_count}")
        console.print(f"   - Total agents: {len(options.agents)}")
        console.print()

        # Step 5: Validate merged agents
        console.print("Step 5: Validating merged agents...")

        for agent_name, agent_def in options.agents.items():
            assert isinstance(agent_def, AgentDefinition), \
                f"Agent '{agent_name}' is not an AgentDefinition"

            tools_count = len(agent_def.tools) if agent_def.tools else 0
            console.print(f"   • {agent_name}:")
            console.print(f"     - Tools: {tools_count}")
            console.print(f"     - Model: {agent_def.model}")
            console.print(f"     - Prompt length: {len(agent_def.prompt)} chars")

        console.print()

        # Step 6: Instantiate ClaudeSDKClient
        console.print("Step 6: Instantiating ClaudeSDKClient with merged agents...")

        client = ClaudeSDKClient(options)

        console.print(f"✅ ClaudeSDKClient instantiated")
        console.print(client)
        console.print()

        # Step 7: Validate client
        console.print("Step 7: Validating ClaudeSDKClient...")

        assert hasattr(client, 'options'), "Client missing 'options'"
        assert client.options is options, "Client options mismatch"
        assert len(client.options.agents) == len(options.agents), "Agent count mismatch"

        console.print(f"✅ Client.options contains {len(client.options.agents)} agent(s)")

        # List all agents available in client
        console.print(f"\n   Available agents in client:")
        for agent_name in client.options.agents.keys():
            console.print(f"     • @{agent_name}")

        console.print()

        # Final summary
        console.print("="*60)
        console.print("TEST PASSED ✅")
        console.print("="*60)
        console.print()
        console.print("Summary:")
        console.print(f"  • YAML agents: {yaml_agent_count}")
        console.print(f"  • Frontmatter agents: {len(frontmatter_agents)}")
        console.print(f"  • Merged agents: {merged_count}")
        console.print(f"  • Total agents: {len(client.options.agents)}")
        console.print()
        console.print("Flow verified:")
        console.print("  YAML → config_loader.py → ClaudeAgentOptions")
        console.print("  .claude/agents/ → discover_agents() → merge")
        console.print("  ClaudeAgentOptions → ClaudeSDKClient ✅")
        console.print()

        return True

    except Exception as e:
        console.print()
        console.print("="*60)
        console.print("TEST FAILED ❌")
        console.print("="*60)
        console.print()
        console.print(f"Error: {e}")
        console.print()
        logger.error(f"Client test failed: {e}", exc_info=True)
        return False


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Claude agent client with frontmatter agents"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='yaml_files/airflow_agent_options_local.yaml',
        help='Path to YAML configuration file'
    )

    args = parser.parse_args()

    # Resolve config path
    config_path = project_root / args.config

    if not config_path.exists():
        console.print(f"❌ Error: Config file not found: {config_path}")
        sys.exit(1)

    # Run test
    success = test_client_with_agents(str(config_path))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
