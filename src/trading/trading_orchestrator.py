"""Programmatic orchestrator for the financial trading workflow."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
)

from util.helpers import display_message
from util.log_set import logger
from src.tools import get_market_data

from .prompt_loader import FIN_PROMPT_URL, PromptSection, fetch_financial_prompt, parse_financial_prompt

DEFAULT_ALLOWED_TOOLS = ["Read", "Write", "Edit", "Grep", "Glob", "Bash"]
MCP_TOOL_NAME = "mcp__market_data__get_market_data"


@dataclass(slots=True)
class TradingAgentConfig:
    name: str
    section: PromptSection
    tools: List[str]


class TradingOrchestrator:
    """Constructs a Claude SDK orchestrator from the trading prompt."""

    def __init__(
        self,
        *,
        prompt_text: str | None = None,
        prompt_url: str = FIN_PROMPT_URL,
        model: str = os.getenv("CLAUDE_MODEL", "sonnet"),
        max_sections: int | None = None,
    ) -> None:
        raw_prompt = prompt_text or fetch_financial_prompt(prompt_url)
        sections = parse_financial_prompt(raw_prompt, max_sections=max_sections)

        if not sections:
            raise ValueError("No sections could be parsed from the financial prompt.")

        logger.debug("Parsed %d prompt sections for trading orchestrator", len(sections))

        self.system_prompt, self.agent_configs = self._build_agent_configs(sections)
        self.options = self._build_options(model)
        self.client: ClaudeSDKClient | None = None

    def _build_agent_configs(self, sections: List[PromptSection]) -> tuple[str, List[TradingAgentConfig]]:
        """Convert prompt sections into agent configurations."""

        first_section = sections[0]
        system_prompt = first_section.prompt
        agent_sections = sections[1:] if len(sections) > 1 else sections

        configs: List[TradingAgentConfig] = []
        for section in agent_sections:
            tools = self._select_tools_for_section(section)
            configs.append(
                TradingAgentConfig(
                    name=section.identifier,
                    section=section,
                    tools=tools,
                )
            )

        return system_prompt, configs

    def _select_tools_for_section(self, section: PromptSection) -> List[str]:
        tools = list(DEFAULT_ALLOWED_TOOLS)
        title = section.title.lower()
        body = section.body.lower()
        if "market" in title or "data" in title or "market" in body:
            tools.append(MCP_TOOL_NAME)
        else:
            # Allow all agents to request data if needed by default
            tools.append(MCP_TOOL_NAME)
        return sorted(set(tools))

    def _build_options(self, model: str) -> ClaudeAgentOptions:
        agents: dict[str, AgentDefinition] = {}
        for config in self.agent_configs:
            agents[config.name] = AgentDefinition(
                description=f"Handles '{config.section.title}' responsibilities.",
                prompt=config.section.prompt,
                tools=config.tools,
                model=model,
            )

        market_data_server = create_sdk_mcp_server(
            name="market_data",
            version="1.0.0",
            tools=[get_market_data],
        )

        allowed_tools = sorted(set(DEFAULT_ALLOWED_TOOLS + [MCP_TOOL_NAME]))

        return ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            model=model,
            agents=agents,
            allowed_tools=allowed_tools,
            permission_mode="acceptEdits",
            mcp_servers={"market_data": market_data_server},
            setting_sources=["project"],
        )

    async def run(self, task: str) -> None:
        """Execute the orchestrator for the specified ``task``."""

        if not task:
            raise ValueError("A task description must be provided to start the orchestrator.")

        async with ClaudeSDKClient(self.options) as client:
            self.client = client
            await client.query(task)

            async for message in client.receive_response():
                display_message(message)
                if isinstance(message, ResultMessage):
                    break

    async def run_and_collect(self, task: str) -> List[str]:
        """Run the orchestrator and collect assistant text blocks for inspection."""

        transcripts: List[str] = []
        async with ClaudeSDKClient(self.options) as client:
            self.client = client
            await client.query(task)
            async for message in client.receive_response():
                display_message(message)
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            transcripts.append(block.text)
                if isinstance(message, ResultMessage):
                    break
        return transcripts

    async def stop(self) -> None:
        """Disconnect the orchestrator client if it is active."""

        if self.client:
            await self.client.disconnect()
            self.client = None


__all__ = ["TradingOrchestrator"]
