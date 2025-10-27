"""Tests for the TradingOrchestrator."""

import anyio
import pytest

from claude_agent_sdk import ClaudeAgentOptions

from src.trading.trading_orchestrator import TradingOrchestrator

SAMPLE_PROMPT = """
Intro text for orchestrator.

## Research
Focus on market research tasks.

## Execution
Plan orders and interact with exchanges.
"""


def test_trading_orchestrator_builds_agents() -> None:
    orchestrator = TradingOrchestrator(prompt_text=SAMPLE_PROMPT, model="haiku")
    options = orchestrator.options
    assert isinstance(options, ClaudeAgentOptions)
    assert options.system_prompt.startswith("## Overview")
    assert "research" in options.agents
    assert "execution" in options.agents

    allowed_tools = options.allowed_tools
    assert "mcp__market_data__get_market_data" in allowed_tools

    market_data_config = options.mcp_servers.get("market_data")
    assert market_data_config is not None


def test_trading_orchestrator_requires_task() -> None:
    orchestrator = TradingOrchestrator(prompt_text=SAMPLE_PROMPT)
    with pytest.raises(ValueError):
        anyio.run(orchestrator.run, "")
