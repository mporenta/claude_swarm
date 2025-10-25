"""Utilities for loading Claude agent configuration from YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

from util.helpers import load_markdown_for_prompt


def load_agent_options_from_yaml(
    config_path: str | Path,
    context: Mapping[str, Any] | None = None,
) -> ClaudeAgentOptions:
    """Load :class:`ClaudeAgentOptions` definitions from a YAML configuration file.

    The YAML structure mirrors the keyword arguments accepted by ``ClaudeAgentOptions``
    with an ``agents`` section defining individual :class:`AgentDefinition` values.

    ``context`` values can be referenced in the YAML using Python ``str.format``
    placeholders, e.g. ``"{project_root}"``. ``Path`` instances in the context are
    automatically converted to strings before formatting.

    Args:
        config_path: Location of the YAML configuration file.
        context: Optional mapping of placeholder values available for string
            formatting within the YAML configuration.

    Returns:
        A fully-instantiated :class:`ClaudeAgentOptions` instance.
    """

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Agent configuration not found: {config_file}")

    with config_file.open("r", encoding="utf-8") as fh:
        raw_config: dict[str, Any] = yaml.safe_load(fh) or {}

    formatted_config = _apply_context(raw_config, context or {})

    agent_definitions = _build_agent_definitions(formatted_config.pop("agents", {}))

    option_keys = {
        "system_prompt",
        "continue_conversation",
        "setting_sources",
        "cwd",
        "add_dirs",
        "env",
        "allowed_tools",
        "permission_mode",
    }

    options_kwargs = {
        key: formatted_config[key]
        for key in option_keys
        if key in formatted_config
    }

    return ClaudeAgentOptions(agents=agent_definitions, **options_kwargs)


def _apply_context(value: Any, context: Mapping[str, Any]) -> Any:
    """Recursively resolve strings using the provided ``context`` mapping."""

    def prepare_context() -> dict[str, Any]:
        prepared: dict[str, Any] = {}
        for key, val in context.items():
            if isinstance(val, Path):
                prepared[key] = str(val)
            else:
                prepared[key] = val
        return prepared

    prepared_context = prepare_context()

    if isinstance(value, dict):
        return {k: _apply_context(v, prepared_context) for k, v in value.items()}
    if isinstance(value, list):
        return [_apply_context(item, prepared_context) for item in value]
    if isinstance(value, str):
        try:
            return value.format(**prepared_context)
        except KeyError:
            return value
    return value


def _build_agent_definitions(
    agent_config: Mapping[str, Any]
) -> dict[str, AgentDefinition]:
    """Convert agent configuration mapping into ``AgentDefinition`` objects."""

    definitions: dict[str, AgentDefinition] = {}
    for agent_name, config in agent_config.items():
        if not isinstance(config, Mapping):
            raise TypeError(
                f"Invalid configuration for agent '{agent_name}': expected mapping"
            )

        config_dict = dict(config)
        prompt = config_dict.pop("prompt", None)

        if prompt:
            prompt = load_markdown_for_prompt(prompt)

        if prompt is None:
            raise ValueError(
                f"Agent '{agent_name}' must define either 'prompt' or 'prompt'."
            )

        definitions[agent_name] = AgentDefinition(prompt=prompt, **config_dict)

    return definitions
