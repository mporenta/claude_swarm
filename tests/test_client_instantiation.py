#!/usr/bin/env python3
"""
Test script for validating Claude agent client instantiation.

This test validates the flow:
1. YAML config → config_loader.py
2. config_loader.py creates ClaudeAgentOptions with AgentDefinition objects
3. ClaudeAgentOptions passed to ClaudeSDKClient
4. Client is successfully instantiated

Stops before running orchestration - only tests initialization.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.config_loader import load_agent_options_from_yaml
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition
from util.log_set import logger
from rich.console import Console
from util.helpers import debug_log

console = Console()

def test_client_instantiation(config_path: str) -> bool:
    """
    Test the client instantiation flow.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        True if successful, False otherwise
    """
    console.print("\n" + "="*60)
    console.print("Claude Agent Client Instantiation Test")
    console.print("="*60 + "\n")

    try:
        # Step 1: Build context (mimics main.py)
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
        console.print(f"✅ Context built with {len(context)} variables")
        console.print(f"   - project_root: {context['project_root']}")
        console.print(f"   - output_dir: {context['output_dir']}")
        console.print()

        # Step 2: Load ClaudeAgentOptions from YAML
        console.print("Step 2: Loading ClaudeAgentOptions from YAML...")
        console.print(f"   Config: {config_path}")
        debug_log(f"Loading options from {config_path}")

        options: ClaudeAgentOptions = load_agent_options_from_yaml(
            config_path=config_path,
            context=context
        )

        console.print(f"✅ ClaudeAgentOptions loaded successfully")
        console.print(options)
        console.print()
        debug_log(f"ClaudeAgentOptions loaded: {options}")

        # Step 3: Validate ClaudeAgentOptions structure
        console.print("Step 3: Validating ClaudeAgentOptions structure...")

        # Check type
        assert isinstance(options, ClaudeAgentOptions), \
            f"Expected ClaudeAgentOptions, got {type(options)}"
        console.print(f"✅ Type: {type(options).__name__}")

        # Check agents dictionary
        assert hasattr(options, 'agents'), "ClaudeAgentOptions missing 'agents' attribute"
        assert isinstance(options.agents, dict), f"agents should be dict, got {type(options.agents)}"
        console.print(f"✅ Agents dict exists with {len(options.agents)} agent(s)")
        debug_log(f"Agents loaded: {list(options.agents.keys())}")

        # Validate each agent
        for agent_name, agent_def in options.agents.items():
            assert isinstance(agent_def, AgentDefinition), \
                f"Agent '{agent_name}' should be AgentDefinition, got {type(agent_def)}"

            # Check required AgentDefinition attributes
            assert hasattr(agent_def, 'description'), f"Agent '{agent_name}' missing 'description'"
            assert hasattr(agent_def, 'prompt'), f"Agent '{agent_name}' missing 'prompt'"
            assert hasattr(agent_def, 'tools'), f"Agent '{agent_name}' missing 'tools'"
            assert hasattr(agent_def, 'model'), f"Agent '{agent_name}' missing 'model'"

            tools_count = len(agent_def.tools) if agent_def.tools else 0
            console.print(f"   • {agent_name}:")
            console.print(f"     - Description: {agent_def.description[:50]}...")
            console.print(f"     - Prompt length: {len(agent_def.prompt)} chars")
            console.print(f"     - Tools: {tools_count} tool(s)")
            console.print(f"     - Model: {agent_def.model}")

        console.print()

        # Check other important options
        console.print("Step 4: Validating other ClaudeAgentOptions attributes...")

        attrs_to_check = [
            ('system_prompt', dict),
            ('model', str),
            ('cwd', str),
            ('allowed_tools', list),
            ('permission_mode', str),
        ]

        for attr_name, expected_type in attrs_to_check:
            if hasattr(options, attr_name):
                attr_value = getattr(options, attr_name)
                if attr_value is not None:
                    actual_type = type(attr_value)
                    # For union types, check if it matches one of the expected types
                    if expected_type == str:
                        assert isinstance(attr_value, (str, type(None))), \
                            f"{attr_name} should be {expected_type}, got {actual_type}"
                    else:
                        assert isinstance(attr_value, expected_type), \
                            f"{attr_name} should be {expected_type}, got {actual_type}"
                    console.print(f"✅ {attr_name}: {actual_type.__name__}")
                    debug_log(f"{attr_name}: {attr_value}")
                else:
                    console.print(f"⚠️  {attr_name}: None")
                    debug_log(f"{attr_name}: None")
            else:
                console.print(f"⚠️  {attr_name}: Not set")
                debug_log(f"{attr_name}: Not set")

        console.print()

        # Step 5: Instantiate ClaudeSDKClient
        console.print("Step 5: Instantiating ClaudeSDKClient...")
        console.print(f"   Passing ClaudeAgentOptions to ClaudeSDKClient()")

        client = ClaudeSDKClient(options)

        console.print(f"✅ ClaudeSDKClient instantiated successfully")
        console.print(f"client: {client}")
        debug_log(f"ClaudeSDKClient instantiated: {client}")

        # Step 6: Validate client
        console.print("Step 6: Validating ClaudeSDKClient...")

        assert hasattr(client, 'options'), "Client missing 'options' attribute"
        assert client.options is options, "Client options should reference the same object"
        console.print(f"✅ Client has 'options' attribute")
        console.print(f"✅ Client.options references the ClaudeAgentOptions object")

        # Verify agents are accessible through client
        assert client.options.agents == options.agents, "Client agents mismatch"
        console.print(f"✅ Client.options.agents contains {len(client.options.agents)} agent(s)")
        debug_log(f"Client options agents: {list(client.options.agents.keys())}")

        console.print()

        # Final summary
        console.print("="*60)
        console.print("TEST PASSED ✅")
        console.print("="*60)
        console.print()
        console.print("Summary:")
        console.print(f"  • Configuration file: {config_path}")
        console.print(f"  • ClaudeAgentOptions: ✅ Created")
        console.print(f"  • AgentDefinition objects: ✅ {len(options.agents)} agent(s)")
        console.print(f"  • ClaudeSDKClient: ✅ Instantiated")
        console.print(f"  • Client validation: ✅ Passed")
        console.print()
        console.print("Flow verified:")
        console.print("  YAML → config_loader.py → ClaudeAgentOptions → ClaudeSDKClient ✅")
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
        logger.error(f"Client instantiation test failed: {e}", exc_info=True)
        return False


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Claude agent client instantiation"
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
    success = test_client_instantiation(str(config_path))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
