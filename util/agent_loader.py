"""
Utility functions for loading Claude Code subagents from .claude/agents/ directory.

Supports the official Claude Code subagent protocol with YAML frontmatter.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from claude_agent_sdk import AgentDefinition
from util.log_set import logger


def parse_frontmatter(content: str) -> tuple[Dict, str]:
    """
    Parse YAML frontmatter from markdown file.

    Args:
        content: Full markdown file content

    Returns:
        Tuple of (frontmatter_dict, body_content)

    Example:
        ```
        ---
        name: agent-name
        description: Agent description
        tools: Read,Write
        model: haiku
        ---
        System prompt here
        ```
    """
    # Match frontmatter pattern: ---\n<yaml>\n---\n<content>
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        raise ValueError("Invalid frontmatter format. Expected:\n---\nkey: value\n---\nContent")

    frontmatter_yaml = match.group(1)
    body_content = match.group(2).strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_yaml)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")

    return frontmatter, body_content


def load_agent_from_file(agent_file: Path) -> tuple[str, AgentDefinition]:
    """
    Load a single agent from a frontmatter markdown file.

    Args:
        agent_file: Path to agent markdown file

    Returns:
        Tuple of (agent_name, AgentDefinition)

    Raises:
        ValueError: If file format is invalid
        FileNotFoundError: If file doesn't exist
    """
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_file}")

    logger.debug(f"Loading agent from: {agent_file}")

    content = agent_file.read_text(encoding='utf-8')
    frontmatter, prompt = parse_frontmatter(content)

    # Validate required fields
    required_fields = ['name', 'description']
    for field in required_fields:
        if field not in frontmatter:
            raise ValueError(f"Missing required field '{field}' in {agent_file}")

    agent_name = frontmatter['name']

    # Parse tools (comma-separated string to list)
    tools = None
    if 'tools' in frontmatter and frontmatter['tools']:
        if isinstance(frontmatter['tools'], str):
            tools = [t.strip() for t in frontmatter['tools'].split(',')]
        elif isinstance(frontmatter['tools'], list):
            tools = frontmatter['tools']

    # Parse model
    model = frontmatter.get('model', 'inherit')

    # Create AgentDefinition
    agent_def = AgentDefinition(
        prompt=prompt,
        tools=tools,
        model=model,
        description=frontmatter['description']
    )

    logger.info(f"Loaded agent '{agent_name}' with {len(tools) if tools else 'all'} tool(s), model={model}")

    return agent_name, agent_def


def load_agents_from_directory(agents_dir: Path) -> Dict[str, AgentDefinition]:
    """
    Load all agents from a .claude/agents directory.

    Scans for .md files and loads each as a subagent following the
    Claude Code subagent protocol.

    Args:
        agents_dir: Path to .claude/agents directory

    Returns:
        Dictionary mapping agent names to AgentDefinition objects

    Example:
        ```python
        agents = load_agents_from_directory(Path(".claude/agents"))
        # Returns: {
        #     "migration-specialist": AgentDefinition(...),
        #     "dag-developer": AgentDefinition(...),
        # }
        ```
    """
    if not agents_dir.exists():
        logger.warning(f"Agents directory not found: {agents_dir}")
        return {}

    if not agents_dir.is_dir():
        logger.warning(f"Path is not a directory: {agents_dir}")
        return {}

    agents = {}
    agent_files = list(agents_dir.glob("*.md"))

    logger.info(f"Found {len(agent_files)} agent file(s) in {agents_dir}")

    for agent_file in agent_files:
        try:
            agent_name, agent_def = load_agent_from_file(agent_file)
            agents[agent_name] = agent_def
        except Exception as e:
            logger.error(f"Failed to load agent from {agent_file}: {e}", exc_info=True)
            # Continue loading other agents

    return agents


def discover_agents(project_root: Optional[Path] = None) -> Dict[str, AgentDefinition]:
    """
    Discover and load agents following Claude Code's agent discovery protocol.

    Checks for agents in order of priority:
    1. Project-level: {project_root}/.claude/agents/
    2. User-level: ~/.claude/agents/ (if project_root not specified)

    Args:
        project_root: Optional project root directory. If not provided,
                     uses current working directory.

    Returns:
        Dictionary of discovered agents
    """
    if project_root is None:
        project_root = Path.cwd()

    agents = {}

    # Priority 1: Project-level agents
    project_agents_dir = project_root / ".claude" / "agents"
    if project_agents_dir.exists():
        logger.info(f"Loading project-level agents from: {project_agents_dir}")
        project_agents = load_agents_from_directory(project_agents_dir)
        agents.update(project_agents)

    # Priority 2: User-level agents (lower priority, don't override)
    user_agents_dir = Path.home() / ".claude" / "agents"
    if user_agents_dir.exists():
        logger.info(f"Loading user-level agents from: {user_agents_dir}")
        user_agents = load_agents_from_directory(user_agents_dir)
        # Only add user agents that don't exist in project agents
        for name, agent_def in user_agents.items():
            if name not in agents:
                agents[name] = agent_def
                logger.debug(f"Added user-level agent: {name}")
            else:
                logger.debug(f"Skipped user-level agent '{name}' (overridden by project agent)")

    logger.info(f"Discovered {len(agents)} agent(s) total")
    return agents
