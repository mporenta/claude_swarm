"""
Claude Swarm - Multi-Agent Orchestration System

A framework-agnostic orchestrator for coordinating specialized AI agents.
"""

__version__ = "1.0.0"
__author__ = "Mason Porenta"

from src.orchestrator import SwarmOrchestrator
from src.config_loader import load_agent_options_from_yaml

__all__ = [
    "SwarmOrchestrator",
    "load_agent_options_from_yaml",
]
