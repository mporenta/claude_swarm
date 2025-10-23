# Project: Flask App Generator with Agent Orchestration

## Overview
This project uses Claude Agent SDK to orchestrate multiple specialized agents for web application development. The orchestrator pattern allows different AI agents to collaborate on complex tasks, each with specific expertise and tool access.

## Agent Orchestration System

### Available Agents

#### @app-architect
- **Purpose**: Application architecture and system design expert
- **Capabilities**: Creates project plans, defines application structure, designs data flow, makes technical architecture decisions, creates specifications for other agents
- **Tools**: Read, Write, Edit, Bash
- **Model**: Sonnet
- **When to use**: 
  - At the start of a new project to plan overall structure
  - For defining API contracts and data models
  - When designing multi-component systems
  - To create technical specifications for other agents
  - For breaking down complex requirements into agent tasks
  - When refactoring or restructuring existing code

#### @flask-developer
- **Purpose**: Backend Flask development expert
- **Capabilities**: Creates Flask applications, routes, server configuration, backend logic
- **Tools**: Read, Write, Edit, Bash
- **Model**: Sonnet
- **When to use**: For creating Flask apps, API endpoints, server-side logic, Python backend code

#### @frontend-developer  
- **Purpose**: Frontend and template development expert
- **Capabilities**: HTML, CSS, JavaScript, responsive design, UI/UX
- **Tools**: Read, Write, Edit
- **Model**: Sonnet
- **When to use**: For creating templates, styling, client-side code, visual design

#### @code-reviewer
- **Purpose**: Code quality and best practices specialist
- **Capabilities**: Code review, linting, security checks, optimization suggestions
- **Tools**: Read, Grep, Glob
- **Model**: Sonnet
- **When to use**: For reviewing code quality, running linters, checking standards compliance

### How to Use Agents

**Syntax**: Use `@agent-name` to delegate tasks to a specific agent.

**Example Task Delegation**:
```
@app-architect Design the overall application structure and create specifications for a Flask app with user authentication

@flask-developer Create a Flask app that runs on port 5010 with a single route for '/'

@frontend-developer Create an HTML template with random styling that displays "Hello World"

@code-reviewer Review all Python files and run flake8 to ensure code quality
```

### Agent Orchestration Best Practices

1. **Start with Architecture**: Use @app-architect to plan the project before implementation
2. **Break Down Complex Tasks**: Split large projects into specialized subtasks for each agent
3. **Sequential Delegation**: Complete one agent's work before moving to the next when there are dependencies
4. **Parallel Work**: Multiple agents can work simultaneously on independent components
5. **Clear Instructions**: Give each agent specific, actionable requirements
6. **Review Step**: Always include a code-reviewer step at the end

## Project Structure

### Required Files
```
/home/dev/claude_swarm/generated_code/
├── app.py                    # Flask application (by @flask-developer)
├── requirements.txt          # Dependencies (by @flask-developer)
└── templates/
    └── index.html           # Frontend template (by @frontend-developer)
```

### Working Directory
- **Output Directory**: `/home/dev/claude_swarm/generated_code`
- All generated files should be created in this directory
- Use relative paths within the working directory

## Flask Application Requirements

### app.py Specifications
- Run Flask server on **port 5010**
- Single route: `'/'` for homepage
- Generate random values on each page refresh:
  * Text color (choose from: red, blue, green, purple, orange, teal, magenta, gold)
  * Font size (random between 20px and 100px)
  * Font family (choose from: Arial, Helvetica, Georgia, Times New Roman, Courier, Verdana)
- Pass random values to template via `render_template()`
- Include proper error handling
- Use `if __name__ == '__main__':` for running the app

### templates/index.html Specifications
- Display "Hello World" text prominently
- Apply random styling from Flask variables:
  * `{{ color }}` for text color
  * `{{ font_size }}` for font size
  * `{{ font_family }}` for font family
- Use modern HTML5 structure
- Center content vertically and horizontally
- Add responsive design (works on mobile and desktop)
- Include subtle background or design element
- Clean, minimal CSS styling

### requirements.txt
- Flask (with version specification)
- Any additional dependencies needed

## Code Quality Standards

### Python Standards
- Follow PEP 8 style guide
- Use meaningful variable names
- Include docstrings for functions
- Handle errors gracefully
- Pass flake8 linting with no errors
- Use type hints where appropriate

### HTML/CSS Standards
- Semantic HTML5 elements
- Proper indentation (2 spaces)
- Responsive design principles
- Modern CSS (flexbox for centering)
- Cross-browser compatibility

### Testing Requirements
- Verify file structure is correct
- Run flake8 on Python files
- Check that imports are correct
- Ensure proper file permissions
- **DO NOT** actually start the Flask server (user will do this manually)

## Example Orchestration Workflow

For creating a complete Flask application:

1. **@app-architect**: Design overall application structure, define component specifications, plan file organization
2. **@flask-developer**: Create `app.py` with Flask setup, routing, and random value generation
3. **@flask-developer**: Create `requirements.txt` with Flask and dependencies
4. **@frontend-developer**: Create `templates/index.html` with dynamic styling that uses Flask template variables
5. **@code-reviewer**: Review all files, run flake8, check code quality
6. **Summary**: Report files created, tests passed, and next steps for user

## Environment Configuration

### Available Environment Variables
- `AWS_PROFILE`: AWS profile for data access
- `SNOWFLAKE_ACCOUNT`: Snowflake account identifier
- `AIRFLOW_HOME`: Airflow installation directory
- `PYTHONPATH`: Additional Python module paths

### Accessible Directories
- **Project Root**: `/home/dev` (contains this CLAUDE.md)
- **Output Directory**: `/home/dev/claude_swarm/generated_code`
- **Airflow DAGs**: `/home/dev/airflow/data-airflow-legacy/dags` (for reference if needed)

## Delegation Examples

### Bad Example (No Agent Delegation)
```
Create a Flask app with HTML template and review the code
```
*Problem*: No clear agent specialization, unclear responsibilities

### Good Example (Proper Agent Delegation)
```
@app-architect Create architecture document for Flask app with:
- Component breakdown (backend, frontend, templates)
- Data flow diagram for random styling values
- File structure specifications
- Technical requirements for each component

@flask-developer Create app.py with:
- Flask app running on port 5010
- Route '/' that generates random color, font_size, font_family
- Pass these values to index.html template

@frontend-developer Create templates/index.html that:
- Displays "Hello World" with styling from Flask variables
- Centers content on page
- Uses modern, responsive design

@code-reviewer After all files are created:
- Run flake8 on all Python files
- Verify file structure is correct
- Report any issues found
```
*Benefit*: Clear responsibilities, specific requirements, proper sequence

## Tips for Effective Orchestration

1. **Start with planning**: Use @app-architect to design the system before implementation
2. **Be specific**: Give detailed requirements to each agent
3. **Check dependencies**: Some tasks must complete before others can start
4. **Use code review**: Always end with a code-reviewer check
5. **Iterate if needed**: If an agent's output isn't perfect, delegate refinements
6. **Clear output paths**: Always specify where files should be created
7. **Test incrementally**: Have code-reviewer validate after each major component
8. **Architecture first**: Complex projects benefit from @app-architect planning before any code is written

## Common Patterns

### Pattern 1: Full Stack Development (with Architecture)
```
@app-architect → System design and specifications
@flask-developer → Backend logic and server setup
@frontend-developer → UI/UX and templates  
@code-reviewer → Quality assurance
```

### Pattern 2: Backend + Frontend + Review (Simple Projects)
```
@flask-developer → Backend logic and server setup
@frontend-developer → UI/UX and templates  
@code-reviewer → Quality assurance
```

### Pattern 3: Iterative Development
```
@app-architect → Create initial architecture
@flask-developer → Create initial version
@code-reviewer → Review and suggest improvements
@flask-developer → Implement improvements
@code-reviewer → Final verification
```

### Pattern 4: Parallel Development
```
@app-architect → Create specifications for both agents (sequential first step)
@flask-developer → Work on app.py based on specs (parallel)
@frontend-developer → Work on templates based on specs (parallel)
@code-reviewer → Review all components (sequential last step)
```

### Pattern 5: Complex Application Design
```
@app-architect → Design system architecture, API contracts, data models
@app-architect → Create detailed specifications document
@flask-developer → Implement backend based on specifications
@frontend-developer → Implement frontend based on specifications
@code-reviewer → Review architecture alignment and code quality
```

## Troubleshooting Agent Delegation

**Issue**: Agent doesn't have required tool access
- **Solution**: Check agent definition - ensure the agent has the tools it needs (e.g., @code-reviewer needs Read, Grep, Glob for code review)

**Issue**: Agents working on conflicting files
- **Solution**: Delegate sequentially or assign different file responsibilities. Use @app-architect to define clear boundaries.

**Issue**: Agent output quality issues  
- **Solution**: Provide more specific requirements and context in delegation prompt. Consider having @app-architect create detailed specs first.

**Issue**: Unclear which agent to use
- **Solution**: 
  - Architecture/Design/Planning → @app-architect
  - Python/Flask/Backend → @flask-developer
  - HTML/CSS/Templates → @frontend-developer
  - Linting/Review/Quality → @code-reviewer

**Issue**: Project scope too large or complex
- **Solution**: Start with @app-architect to break down the project into manageable components with clear specifications for other agents

**Issue**: Integration problems between components
- **Solution**: Have @app-architect define API contracts and interfaces before implementation begins

## Success Criteria

A successful Flask app generation includes:
- ✅ Well-designed architecture (if complex project)
- ✅ Clean, well-structured Flask application
- ✅ Properly templated HTML with dynamic styling
- ✅ All files pass flake8 linting
- ✅ Requirements.txt with correct dependencies
- ✅ Code follows best practices
- ✅ Professional, production-ready quality
- ✅ All files in correct directory structure
- ✅ Components integrate seamlessly based on architectural specifications