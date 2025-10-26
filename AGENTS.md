# AGENTS.md — Codex Agent Operating Manual (for `claude_swarm`)

## Purpose
You (Codex) are the automation agent assigned to **debug, harden, and improve** this repository. Operate as a disciplined engineer: plan, change, test, document, and open PRs.

---

## Required URLs (confirm at startup)
1) **Ask the operator to provide the official Claude Agent SDK (Python) docs URL.**  
   - If none is provided, use and log this default:  
     `https://docs.claude.com/en/api/agent-sdk/python`
2) **Use and review** the **multiple-agents example**:  
   `https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/agents.py`

Persist confirmed URLs (e.g., `.env` `CLAUDE_AGENT_SDK_DOCS_URL=...`) and echo them in your session log.

---

## Environment & Secrets
- Your runtime has `ANTHROPIC_API_KEY` available via the secrets manager. Do **not** print it or commit it. Access via `os.environ["ANTHROPIC_API_KEY"]`.
- Expect Python ≥ 3.10, Node.js, and `@anthropic-ai/claude-code` installed; verify on first run:
  - `python --version`
  - `node --version`
  - `claude-code --version`
- Install SDK if needed: `pip install -U claude-agent-sdk`

---

## SDK Primitives You MUST Use
- `claude_agent_sdk.ClaudeAgentOptions`
- `claude_agent_sdk.ClaudeSDKClient`

You should favor `ClaudeSDKClient` (interactive, tools/hooks) for repo work; use `query()` only for quick, stateless checks.

**Boot snippet (use/adapt):**
```python
import os, anyio
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

PROJECT_ROOT = Path(__file__).resolve().parents[0]
DOCS_URL = os.getenv("CLAUDE_AGENT_SDK_DOCS_URL") or "https://docs.claude.com/en/api/agent-sdk/python"
print(f"[codex] Using Claude Agent SDK docs: {DOCS_URL}")

options = ClaudeAgentOptions(
    cwd=str(PROJECT_ROOT),
    system_prompt="You are a strict, test-driven code agent working on the claude_swarm repo.",
    allowed_tools=["Read","Write","Bash"],         # Expand only if necessary.
    permission_mode="acceptEdits"                  # For non-destructive edits use 'ask' and escalate.
)

async def run_task(prompt: str):
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for msg in client.receive_response():
            # Stream to console/logs; parse edits/results as needed.
            print(msg)

if __name__ == "__main__":
    anyio.run(run_task, "Self-check: list repo, run unit/static checks, report findings.")


⸻

Operating Rules (non-negotiable)
	1.	Understand before changing. Read README.md, CLAUDE.md, AGENTS.md, and examples/ in this repo. Summarize intent and risks before edits.
	2.	Branching: create a feature branch per task (feat/<slug> or fix/<slug>). Never push directly to main.
	3.	Guardrails:
	•	No secrets in logs, commits, or comments.
	•	For destructive ops (deleting files, schema changes), ask first and propose a reversible plan.
	4.	TDD bias: add/adjust tests that fail first, then implement; keep coverage from regressing.
	5.	Reproducible runs: add/maintain scripts (make, uv, or bash) to run lint, typecheck, tests, and example agents locally.

⸻

Task Protocol (follow this every time)
	1.	Intake: Restate the task in 1–3 lines. List assumptions. Confirm or adjust with operator if ambiguous.
	2.	Recon:
	•	Scan README.md, CLAUDE.md, docs/, examples/, and src/.
	•	Open and review anthropics/.../examples/agents.py for multi-agent patterns to reuse.
	3.	Plan: Draft a minimal, testable plan (bullets). Include the SDK touchpoints (ClaudeAgentOptions, ClaudeSDKClient, hooks/tools).
	4.	Implement:
	•	Small commits; clear messages.
	•	Prefer allowed_tools=["Read","Write","Bash"] and only escalate tool surface if justified.
	•	If multi-agent orchestration is needed, mirror patterns from examples/agents.py (programmatic subagents, session forking) adapted to this codebase.
	5.	Validate:
	•	Lint (ruff/flake8), types (pyright/mypy), tests (pytest -q), smoke-run relevant agent scripts.
	•	Capture artifacts/logs in the PR.
	6.	Deliver:
	•	Open PR with: scope, risk, before/after behavior, test evidence, and rollout notes.
	•	Update docs/README examples if CLI or usage changes.

⸻

Common Tasks You Will Receive
	•	Debug failing flows or exceptions; add minimal repros and tests.
	•	Refactor agent orchestration to use ClaudeSDKClient hooks and scoped tools.
	•	Add an internal SDK MCP tool (Python function + create_sdk_mcp_server) for repo-local utilities.
	•	Introduce multi-agent execution in this repo, borrowing patterns from examples/agents.py.
	•	Harden scripts (idempotent setup; clear exit codes; better logs).
	•	Docs: keep CLAUDE.md/README.md aligned with behavior and entrypoints.

⸻

Multi-Agent Notes (how to adapt the example)
	•	Use programmatic sub-agents or forked sessions to isolate roles (e.g., “orchestrator”, “tester”, “refactorer”).
	•	Keep shared context minimal; pass only what each agent needs (task brief + file subset).
	•	Aggregate results deterministically; prefer file diffs + test outcomes over raw prose.

⸻

Quick Health Check (run first)
	•	Toolchain: python -V && node -v && claude-code --version
	•	SDK present: python -c "import claude_agent_sdk, sys; print(claude_agent_sdk.__version__)" (or pip show)
	•	Repo status clean: git status --porcelain
	•	Smoke tests: pytest -q (or repo’s equivalent)

⸻

Communications
	•	Be terse. Evidence > claims. If blocked, state the exact command/output and your next move.
	•	When you need the SDK docs URL or example link, ask; if silent, proceed with the defaults above and log them.

**References:** Official Python Agent SDK docs and repo info (installation, prerequisites, `ClaudeSDKClient` vs `query`) and the multi-agents example path were confirmed from Anthropic sources.  [oai_citation:0‡docs.claude.com](https://docs.claude.com/en/api/agent-sdk/python?utm_source=chatgpt.com)
