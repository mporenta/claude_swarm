#!/usr/bin/env python3
"""
Test script to verify main_prompt_file is loaded from YAML config.
"""

from pathlib import Path
from src.orchestrator import SwarmOrchestrator

def test_config_loading():
    """Test that main_prompt_file is extracted from YAML."""

    config_path = Path("yaml_files/flask_agent_options.yaml")

    print(f"Loading configuration from: {config_path}")

    orchestrator = SwarmOrchestrator(config_path=config_path)

    print(f"\n✓ Configuration loaded successfully")
    print(f"✓ main_prompt_file found: {orchestrator.main_prompt_file}")

    if orchestrator.main_prompt_file:
        prompt_path = Path(orchestrator.main_prompt_file)
        if prompt_path.exists():
            print(f"✓ Prompt file exists: {prompt_path}")
            print(f"\n✅ SUCCESS: Automated mode will work without user prompts!")
        else:
            print(f"❌ ERROR: Prompt file not found: {prompt_path}")
    else:
        print(f"❌ ERROR: main_prompt_file not loaded from YAML")

    print(f"\nConfigured agents:")
    for agent_name in orchestrator.options.agents.keys():
        print(f"  • {agent_name}")

if __name__ == "__main__":
    test_config_loading()
