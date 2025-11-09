Based on the `ClaudeAgentOptions` configuration in the Python Agent SDK, the `max_turns` parameter applies to the main conversation session, not to individual subagents[(1)](https://docs.claude.com/en/api/agent-sdk/python#types). When subagents are invoked, they run with their own isolated context and don't inherit the `max_turns` limit from the parent session[(1)](https://docs.claude.com/en/api/agent-sdk/python#types).

According to the documentation, `max_turns` is defined as "Maximum conversation turns" at the top-level `ClaudeAgentOptions`[(1)](https://docs.claude.com/en/api/agent-sdk/python#types). However, the `AgentDefinition` type used for configuring subagents does not include a `max_turns` parameter[(1)](https://docs.claude.com/en/api/agent-sdk/python#types). The `AgentDefinition` only supports:

- `description` (required)
- `prompt` (required)
- `tools` (optional)
- `model` (optional)[(1)](https://docs.claude.com/en/api/agent-sdk/python#types)

This means your subagents (`migration-specialist` and `airflow-code-reviewer`) are running without turn limits. Each time they're invoked, they can continue for as many turns as needed to complete their task, which explains why your total session reaches 60-70 turns despite setting `max_turns=25` on the main options.

Currently, there's no documented way to set per-subagent turn limits in the `AgentDefinition` configuration[(1)](https://docs.claude.com/en/api/agent-sdk/python#types). The `max_turns` parameter only controls the main agent's conversation length, not the subagents it spawns.

**
 You can add explicit iteration limits directly in your subagent prompts. Based on best practices for prompt engineering[(1)](https://github.com/anthropics/courses/blob/master/real_world_prompting/03_prompt_engineering.ipynb), you should include clear, specific instructions about workflow constraints.

Here's how to adjust your subagent prompts to limit iterations:

**For your migration-specialist:**

```python
"migration-specialist": AgentDefinition(
    description="Converts legacy Airflow operators and patterns to modern equivalents",
    prompt="""You are an Apache Airflow migration expert specializing in code transformation.

🔧 MANDATORY: Execute `check-common-components` found in the skills: `/home/dev/claude_dev/claude_swarm/.claude/skills/check-common-components.md` skill BEFORE writing ANY custom operators, hooks, or utilities. Report findings before implementation.

⚠️ ITERATION LIMIT: You have a MAXIMUM of 5 tool-use iterations to complete your task. Plan your work efficiently:
- Iteration 1-2: Analysis and component checking
- Iteration 3-4: Implementation
- Iteration 5: Final verification and handoff

If you cannot complete the task within 5 iterations, stop and report what you've accomplished and what remains.

Your focus areas:
1. **Check for existing components**: ALWAYS run `/check-common-components` when you need operators, hooks, or utilities
2. **Operator modernization**: Convert legacy operators to Airflow 2.x equivalents OR use existing common components
3. **TaskFlow API implementation**: Transform traditional task definitions to @task decorators where appropriate
4. **Connection and hook updates**: Use existing CustomHooks from common/ instead of creating new ones
5. **Configuration migration**: Convert legacy config references to modern patterns
6. **Dependency syntax**: Update task dependencies from >> to modern XComArgs or explicit dependencies

When working on migrations:
- FIRST: Run `/check-common-components` for any custom code needs
- Follow patterns from successfully migrated DAGs
- Preserve business logic while modernizing structure
- Add type hints and improve error handling
- Document any assumptions or decisions

Hand off completed code sections to the airflow-code-reviewer for validation.""",
    tools=["Read", "Write", "Edit", "Grep", "Glob"],
    model="haiku",
)
```

**For your airflow-code-reviewer:**

```python
"airflow-code-reviewer": AgentDefinition(
    description="Validates migrated code against Airflow 2.x best practices and standards",
    prompt="""[Your existing prompt content]

⚠️ ITERATION LIMIT: You have a MAXIMUM of 3 tool-use iterations for review:
- Iteration 1: Read and analyze the code
- Iteration 2: Run validation checks (grep/bash)
- Iteration 3: Compile and report findings

Complete your review within 3 iterations. If critical issues require more investigation, report them and stop.""",
    tools=["Read", "Grep", "Glob", "Bash"],
    model="haiku",
)
```

**Key prompting strategies to enforce limits:**[(1)](https://github.com/anthropics/courses/blob/master/real_world_prompting/03_prompt_engineering.ipynb)

1. **Be explicit and specific** - State the exact number of allowed iterations
2. **Provide a workflow structure** - Break down what should happen in each iteration
3. **Include stop conditions** - Tell the agent what to do if it reaches the limit
4. **Use clear formatting** - Make the limit highly visible (emojis, caps, bold)

According to prompt engineering best practices, "well-engineered prompts are precise, leaving little room for misinterpretation by the model"[(1)](https://github.com/anthropics/courses/blob/master/real_world_prompting/03_prompt_engineering.ipynb). By explicitly stating iteration limits and expected workflow structure, you guide the subagent to work more efficiently within constraints.