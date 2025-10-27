"""Tests for trading prompt parsing utilities."""

from src.trading.prompt_loader import parse_financial_prompt, PromptSection

SAMPLE_PROMPT = """
Welcome to the trading orchestrator.

## Research Analyst
- Evaluate macro trends.
- Summarize key indicators.

## Risk Manager
- Identify major risks.
- Suggest mitigations.

## Execution Specialist
Focus on trade execution strategies.
"""


def test_parse_financial_prompt_sections() -> None:
    sections = parse_financial_prompt(SAMPLE_PROMPT)
    assert len(sections) == 4

    overview = sections[0]
    assert isinstance(overview, PromptSection)
    assert overview.identifier == "overview"
    assert "Welcome" in overview.body

    research = sections[1]
    assert research.identifier == "research-analyst"
    assert "Evaluate macro trends" in research.body

    execution = sections[-1]
    assert execution.identifier == "execution-specialist"
    assert execution.prompt.startswith("## Execution Specialist")
