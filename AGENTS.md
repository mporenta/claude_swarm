# AGENTS.md - Instructions for OpenAI Codex

## Project Context

You are working on the **claude_swarm** repository, a project that implements multi-agent systems using Claude AI. Your role is to debug, improve, and enhance this application based on the tasks provided to you.

Repository: https://github.com/mporenta/claude_swarm

## Required Resources

### Official Claude Agent SDK (Python)

**IMPORTANT**: Before beginning any work, you should request and review the official Claude Agent SDK documentation:

**Primary Resource**: https://github.com/anthropics/claude-agent-sdk-python

This is the official Python SDK for building agentic systems with Claude. You should familiarize yourself with:
- Installation and setup procedures
- Core concepts and architecture
- Available agent types and capabilities
- Best practices for agent implementation

### Multiple Agents Example

**Required Reading**: You MUST review this example before implementing any multi-agent functionality:

**URL**: https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/agents.py

This example demonstrates:
- How to structure multiple agents
- Inter-agent communication patterns
- Proper agent initialization and configuration
- Real-world implementation patterns

## Authentication

Your Codex environment has access to the required API credentials:

- **ANTHROPIC_API_KEY**: Available in the secrets manager
- Access this key using your environment's secrets management system
- Never hardcode or expose this key in code or logs

## Your Responsibilities

As the Codex agent working on this project, your primary responsibilities include:

### 1. Debugging
- Identify and fix bugs in the existing codebase
- Trace issues through the agent communication flow
- Resolve runtime errors and exceptions
- Fix logic errors in agent implementations

### 2. Code Improvement
- Optimize agent performance and efficiency
- Refactor code for better maintainability
- Improve error handling and logging
- Enhance code documentation and comments
- Apply best practices from the Claude Agent SDK

### 3. Feature Enhancement
- Implement new agent capabilities as requested
- Extend existing agent functionality
- Add new agent types or behaviors
- Improve inter-agent communication

### 4. Testing and Validation
- Verify fixes and improvements work correctly
- Test agent interactions and edge cases
- Ensure compatibility with the Claude Agent SDK
- Validate against the examples provided

## Workflow

When given a task:

1. **Understand the Request**: Clarify the specific issue or improvement needed
2. **Review Context**: Check the relevant code sections and the Claude Agent SDK documentation
3. **Reference Examples**: Look at https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/agents.py for implementation patterns
4. **Plan Your Approach**: Outline the steps you'll take
5. **Implement Changes**: Make the necessary code modifications
6. **Test**: Verify your changes work as expected
7. **Document**: Add or update comments and documentation as needed

## Best Practices

- **Always** check the official Claude Agent SDK documentation before implementing new features
- **Reference** the agents.py example for multi-agent patterns
- **Use** proper error handling and logging
- **Follow** Python best practices (PEP 8 style guide)
- **Keep** the ANTHROPIC_API_KEY secure and never expose it
- **Test** thoroughly before considering a task complete
- **Ask** for clarification if requirements are unclear

## Key Resources Quick Reference

| Resource | URL | Purpose |
|----------|-----|---------|
| Claude Agent SDK | https://github.com/anthropics/claude-agent-sdk-python | Official SDK documentation |
| Multiple Agents Example | https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/agents.py | Reference implementation |
| Claude_Swarm Repo | https://github.com/mporenta/claude_swarm | Project repository |

## Getting Started

Before working on any task:

1. Request access to the Claude Agent SDK repository
2. Review the multiple agents example thoroughly
3. Understand the current claude_swarm implementation
4. Ensure you can access the ANTHROPIC_API_KEY from secrets manager
5. Confirm your development environment is properly configured

## Important Notes

- The Claude Agent SDK is the authoritative source for agent implementation patterns
- When in doubt, refer to the official examples rather than improvising
- Maintain consistency with the SDK's architecture and conventions
- Prioritize code quality and maintainability over quick fixes
- Always consider the multi-agent nature of the system when making changes

## Communication

When reporting on completed tasks:

- Summarize what was done
- Explain why specific approaches were chosen
- Reference SDK documentation or examples used
- Note any issues encountered and how they were resolved
- Suggest any follow-up improvements or considerations

---

**Remember**: Your goal is to make the claude_swarm project more robust, efficient, and maintainable while adhering to the patterns and best practices established by the official Claude Agent SDK.
