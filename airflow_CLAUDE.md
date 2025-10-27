# claude_swarm Project Instructions

This repository houses multi-agent workflows built on the Claude Agent SDK for Python. These instructions are always loaded alongside the `claude_code` system preset—ensure your SDK configuration points to this directory and enables filesystem settings.

## SDK Configuration Requirements
- Instantiate clients with `ClaudeAgentOptions` and `ClaudeSDKClient` from `claude_agent_sdk`.
- Set `cwd` to the directory containing this file when launching agents so project settings are discovered.
- Include `setting_sources=["project", "user"]` (add `"local"` when needed) so the SDK reads CLAUDE.md, custom commands, and prompts.
- Document the SDK docs URL in logs; default to `https://docs.claude.com/en/api/agent-sdk/python` if the operator does not supply one.

## Operating Principles
1. **Understand First** – Read `README.md`, `docs/`, `airflow/airflow_CLAUDE.md`, and prompt files before making changes. Summarize intent, risks, and assumptions with the operator when work begins.
2. **Plan Before Editing** – Produce a short, testable plan that references relevant SDK hooks, tools, and validation steps. Confirm ambiguous requirements.
3. **Disciplined Delivery** – Work on feature branches (e.g., `feat/<slug>`), commit in logical slices, and keep the working tree clean.
4. **Testing & Quality** – Favor TDD. Run linting, typing, and unit/integration tests that correspond to your changes. Record exact commands and outcomes.
5. **Documentation Alignment** – Update README, docs, and prompts whenever behavior or workflows change. Keep instructions synchronized with the codebase.
6. **Security & Secrets** – Never print or commit sensitive values such as `ANTHROPIC_API_KEY`. Escalate if a task requires handling credentials.

## Multi-Agent Guidance
- Reuse patterns from `examples/` and `airflow/` for orchestrating sub-agents. Delegate work through well-scoped prompts stored in `prompts/`.
- Keep shared context minimal. Pass only the files, configs, and acceptance criteria required for each sub-agent to act.
- Capture results deterministically (diffs, logs, test outcomes). Avoid relying on conversational memory alone.

## Validation Expectations
- Run `pytest -q` (or the relevant subset) after modifying executable code.
- Execute static analysis (`ruff`, `pyright`, or repo-specific tools) when touching Python modules.
- For prompt-only changes, note the absence of code execution but still validate markdown formatting.

## Communication & PRs
- Provide concise status updates and surface blockers immediately.
- Summarize changes, risks, and testing evidence in commits and pull requests. Include rollout or follow-up actions when applicable.
- Reference supporting documentation (e.g., `airflow/airflow_CLAUDE.md`, SDK guides) when they inform implementation decisions.

Follow these guardrails to keep the claude_swarm project stable, testable, and easy to extend.