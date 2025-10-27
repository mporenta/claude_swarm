"""Utilities for working with the external financial trading prompt."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable, List
from urllib import error, request

from util.log_set import logger

FIN_PROMPT_URL = (
    "https://raw.githubusercontent.com/mporenta/trading-app/master/"
    "gpt_agent/prompts/fin_prompt_dev_v_cai.md"
)

DOCS_URL = os.getenv("CLAUDE_AGENT_SDK_DOCS_URL", "https://docs.claude.com/en/api/agent-sdk/python")
logger.info("[codex] Using Claude Agent SDK docs: %s", DOCS_URL)
MULTI_AGENT_EXAMPLE_URL = (
    "https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/agents.py"
)
logger.info("[codex] Multi-agent example reference: %s", MULTI_AGENT_EXAMPLE_URL)


@dataclass(slots=True)
class PromptSection:
    """Represents a logical section extracted from the trading prompt."""

    identifier: str
    title: str
    body: str

    @property
    def prompt(self) -> str:
        """Return a markdown-formatted prompt for use with an agent."""
        title_line = self.title.strip() if self.title.strip() else self.identifier
        content = self.body.strip()
        if content:
            return f"## {title_line}\n\n{content}"
        return f"## {title_line}"


_SECTION_HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$", re.MULTILINE)
_IDENTIFIER_RE = re.compile(r"[^a-z0-9]+")


def fetch_financial_prompt(url: str = FIN_PROMPT_URL, timeout: float = 10.0) -> str:
    """Download the trading prompt from GitHub.

    The function adds a standard ``User-Agent`` header so the request is not
    rejected by GitHub's CDN. Errors are re-raised as :class:`RuntimeError`
    with a helpful message for the operator.
    """

    logger.debug("Fetching financial prompt from %s", url)
    headers = {"User-Agent": "claude-swarm-automation/1.0"}
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            encoding = resp.headers.get_content_charset("utf-8")
            data = resp.read()
            content = data.decode(encoding, errors="replace")
            logger.debug("Fetched %d bytes of financial prompt", len(content))
            return content
    except error.URLError as exc:
        raise RuntimeError(
            "Unable to download fin_prompt_dev_v_cai.md from GitHub. "
            "Provide the prompt content manually or ensure network access."
        ) from exc


def _slugify(value: str, fallback: str) -> str:
    normalized = value.lower().strip()
    normalized = _IDENTIFIER_RE.sub("-", normalized)
    normalized = normalized.strip("-")
    return normalized or fallback


def _section_iter(markdown: str) -> Iterable[tuple[str, str]]:
    """Yield ``(heading, body)`` tuples extracted from ``markdown``."""

    if not markdown:
        return

    matches = list(_SECTION_HEADING_RE.finditer(markdown))
    if not matches:
        yield ("Overview", markdown.strip())
        return

    # Capture leading text before the first heading as a pseudo-section
    first_match = matches[0]
    if first_match.start() > 0:
        prefix = markdown[: first_match.start()].strip()
        if prefix:
            yield ("Overview", prefix)

    for idx, match in enumerate(matches):
        heading_text = match.group(2).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        yield (heading_text or f"Section {idx + 1}", body)


def parse_financial_prompt(markdown: str, max_sections: int | None = None) -> List[PromptSection]:
    """Convert the raw prompt text into structured :class:`PromptSection` items."""

    sections: List[PromptSection] = []
    for index, (title, body) in enumerate(_section_iter(markdown), start=1):
        identifier = _slugify(title, f"section-{index}")
        sections.append(PromptSection(identifier=identifier, title=title, body=body))
        if max_sections and len(sections) >= max_sections:
            break

    return sections
