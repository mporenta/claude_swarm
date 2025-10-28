# Chat with Your Claude Agent

Your Claude Agent is now ready to use! You can interact with it in two ways:

## 1. Command-Line Mode (Single Message)

Send a single message and get a response:

```bash
./chat_with_agent.sh "Your message here"
```

**Examples:**
```bash
# Ask a simple question
./chat_with_agent.sh "What is 2+2?"

# Get help with your codebase
./chat_with_agent.sh "What files are in the current directory?"

# Ask for code help
./chat_with_agent.sh "Help me refactor this function to use list comprehension"

# Migrate an Airflow DAG
./chat_with_agent.sh "Migrate the DAG in /path/to/dag.py from Airflow 1.x to 2.x"
```

**Note:** Each command-line invocation creates a new session, so the agent won't remember previous conversations.

## 2. Interactive Mode (Persistent Conversation)

Run without arguments to start an interactive session:

```bash
./chat_with_agent.sh
```

Then type your messages and press Enter. The agent will remember the conversation context within that session.

**Special commands:**
- `exit` or `quit` - End the session
- `clear` - Clear the conversation (requires restart for full reset)

**Example session:**
```
🧑 You: Hello! What can you help me with?
🤖 Claude: [Agent responds with capabilities]

🧑 You: Can you read the file src/main.py?
🤖 Claude: [Agent reads and analyzes the file]

🧑 You: Now refactor it to use the TaskFlow API
🤖 Claude: [Agent refactors the code]

🧑 You: exit
Goodbye!
```

## Your Agent's Capabilities

- **File Operations**: Read, write, and edit files
- **Code Search**: Grep and Glob for finding code patterns
- **Bash Commands**: Execute shell commands (with safety checks)
- **Airflow Expertise**: Specializes in migrating DAGs from 1.x to 2.x
- **Python Development**: General Python coding assistance

## Configuration

- **Model**: Currently using `haiku` (fast, cost-effective)
- **Working Directory**: `/Users/mike.porenta/python_dev/aptive_github/claude_swarm`
- **Max Turns**: 15 per session
- **Permission Mode**: `plan` (agent plans before executing)
- **Allowed Tools**: Skill, Read, Write, Edit, Bash, Grep, Glob

## Logs

All conversations and debug information are logged to:
```
/Users/mike.porenta/python_dev/aptive_github/claude_swarm/logs/
```

## Tips

1. **Be specific**: The clearer your request, the better the agent can help
2. **Provide context**: Mention file paths, function names, or specific requirements
3. **Use command-line mode for quick queries**: Faster for one-off questions
4. **Use interactive mode for complex tasks**: Better for multi-step workflows that require context

## Example Use Cases

### Migrate an Airflow DAG
```bash
./chat_with_agent.sh "Migrate the cresta DAG to Airflow 2.x TaskFlow API, ensuring we use the existing SFTPToSnowflakeOperator from common/custom_operators/"
```

### Debug a Python error
```bash
./chat_with_agent.sh "I'm getting a KeyError in line 42 of src/main.py. Can you help me fix it?"
```

### Refactor code
```bash
./chat_with_agent.sh "Refactor src/utils.py to follow PEP 8 style guidelines"
```

### Get code explanations
```bash
./chat_with_agent.sh "Explain how the ClaudeSDKClient class works in test_airflow_agent_main.py"
```

---

**Note:** This agent uses the Claude Code system prompt and has been configured specifically for Airflow DAG migration tasks, but it can handle general Python development as well.
