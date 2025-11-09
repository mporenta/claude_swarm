# Flask Agent vs Airflow Agent: Comparison

## High-Level Comparison

| Aspect | Flask Agent | Airflow Agent |
|--------|-------------|---------------|
| **Purpose** | Web app creation | DAG development & migration |
| **Agents** | 3 generic agents | 4 specialized agents |
| **Workflows** | 1 (creation only) | 2 (creation + migration) |
| **Standards** | General web dev | CLAUDE.md compliance |
| **Tools** | Basic file operations | Full dev + code review tools |
| **Domain Focus** | Frontend/Backend split | Architecture/Dev/Migration/Review |

## Agent Comparison

### Flask Agent's Subagents
```python
"flask-developer": "Expert Flask developer"
"frontend-developer": "Expert frontend developer"  
"code-reviewer": "Code review and best practices"
```

**Generic roles** - Not domain-specific

### Airflow Agent's Subagents
```python
"dag-architect": "Plans DAG structure and dependencies"
"dag-developer": "Writes production-ready Airflow 2 code"
"migration-specialist": "Handles Airflow 1.0→2.0 migrations"
"airflow-code-reviewer": "CLAUDE.md compliance verification"
```

**Specialized roles** - Deep domain expertise

## Prompt Depth Comparison

### Flask Developer Prompt
```markdown
You are an expert Flask web developer.

When creating Flask applications:
- Write clean, modular Flask code
- Follow Flask best practices
- Include proper error handling
- Use Jinja2 templating effectively

Create well-structured, maintainable web applications.
```

**~10 lines** - General guidance

### DAG Developer Prompt
```markdown
You are an expert Apache Airflow 2 developer.

## Code Standards (Critical)
- Type hints (required with examples)
- Heartbeat-safe patterns (critical with ❌/✅ examples)
- File structure patterns (with directory tree)
- Modern imports (with before/after examples)
- Environment configuration (with code samples)

## Airflow 2 Best Practices
- Complete import examples
- Custom component usage
- Callbacks implementation
- Rate limiting patterns
- XCom best practices
- Batch processing

## Clean Code Principles
(8 specific principles from CLAUDE.md)

## Common Patterns
(Code examples for each pattern)
```

**~200 lines** - Comprehensive, actionable guidance

## Feature Comparison

### Orchestrator Methods

#### Flask Agent
```python
async def flask_app_orchestrator(self):
    """Single method for Flask app creation."""
    # Loads one prompt
    # Creates app
    # Shows summary
```

#### Airflow Agent
```python
async def create_dag_orchestrator(self):
    """Interactive DAG creation with user input."""
    # Prompts for DAG name, schedule, description
    # Loads orchestrator prompt
    # Coordinates 3 agents (architect → developer → reviewer)
    # Provides detailed summary and next steps

async def migrate_dag_orchestrator(self):
    """Interactive DAG migration workflow."""
    # Prompts for legacy DAG path, new name
    # Loads orchestrator prompt
    # Coordinates 4+ agents (migration → architect → dev → review)
    # Provides migration summary and comparison steps
```

## Standards Enforcement

### Flask Agent
- General web development best practices
- No specific framework requirements
- Basic code quality

### Airflow Agent
- **10+ specific standards** from CLAUDE.md:
  - ✅ Heartbeat safety (critical)
  - ✅ Type hints (required)
  - ✅ Airflow 2.0 imports
  - ✅ File structure compliance
  - ✅ Environment awareness
  - ✅ Flake8 compliance
  - ✅ Documentation standards
  - ✅ Error handling patterns
  - ✅ Rate limiting
  - ✅ Clean code principles

## Workflow Complexity

### Flask Agent Workflow
```
User → flask_app_orchestrator → Query with prompt → Done
```

**Single linear workflow**

### Airflow Agent Workflows

#### Creation Workflow
```
User → Interactive input (name, schedule, desc)
     → create_dag_orchestrator
     → @dag-architect (design)
     → @dag-developer (implement)  
     → @airflow-code-reviewer (verify)
     → Complete with next steps
```

#### Migration Workflow
```
User → Interactive input (legacy path, new name)
     → migrate_dag_orchestrator
     → @migration-specialist (analyze)
     → @dag-architect (modernize)
     → @migration-specialist (implement)
     → @dag-developer (enhance)
     → @airflow-code-reviewer (verify)
     → Complete with comparison steps
```

**Multi-phase, agent-coordinated workflows**

## Interactive Experience

### Flask Agent
```
[Turn 1] You: flask
🚀 Starting Flask app orchestrator...
[Creates app]
✅ Flask app creation complete!
```

### Airflow Agent
```
[Turn 1] You: create-dag
DAG name (e.g., 'marketo_to_snowflake'): customer_pipeline
Schedule (daily/intraday/hourly/nightly/weekly/monthly): daily
Brief description: Fetch customer data from API and load to Snowflake

🚀 Starting Airflow DAG creation orchestrator...
DAG Name: customer_pipeline
Schedule: daily
Description: Fetch customer data from API and load to Snowflake

[Orchestrator coordinates agents]

✅ DAG creation complete!
📊 Summary:
   • Tool uses: 15
   • Agent switches: 3
   • Thinking blocks: 8
   • Files created: 4
   • Total cost: $0.0234

📁 DAG location: generated_dags/dags/customer_pipeline/

🚀 Next steps:
   1. Review the generated code
   2. Run: flake8 dags/customer_pipeline/
   3. Test locally: docker compose up -d
   4. Access Airflow UI: http://localhost:8080
```

**Detailed interactive guidance**

## Code Quality Features

### Flask Agent
- Basic code review
- General best practices
- Simple structure

### Airflow Agent
- **Heartbeat safety verification** (prevents production issues)
- **Type hint enforcement** (catches errors early)
- **Import validation** (ensures Airflow 2.0 compatibility)
- **File structure compliance** (maintains consistency)
- **Flake8 integration** (catches linting issues)
- **Documentation verification** (ensures maintainability)
- **Multi-phase review** (comprehensive quality assurance)

## Tool Access

### Flask Agent Agents
```python
"flask-developer": ["Read", "Write", "Edit", "Bash"]
"frontend-developer": ["Read", "Write", "Edit"]
"code-reviewer": ["Read", "Grep", "Glob"]
```

### Airflow Agent Agents
```python
"dag-architect": ["Read", "Grep", "Glob"]           # Research only
"dag-developer": ["Read", "Write", "Edit", "Bash", "Grep"]  # Full dev
"migration-specialist": ["Read", "Write", "Edit", "Grep", "Glob"]  # Migration
"airflow-code-reviewer": ["Read", "Grep", "Glob"]  # Review only
```

**Purpose-matched tool access**

## Directory Access

### Flask Agent
```python
add_dirs=[str(airflow_dags_dir)]  # Single directory
```

### Airflow Agent
```python
add_dirs=[
    str(airflow_2_dags_dir),      # Examples from production
    str(airflow_legacy_dags_dir), # Reference for migrations
]
```

**Context-rich access**

## Environment Configuration

### Flask Agent
```python
env={
    "FLASK_ENV": "development",
    "FLASK_PROJECT_PATH": str(output_dir),
    "PYTHONPATH": "...",
}
```

### Airflow Agent
```python
env={
    "AIRFLOW_HOME": str(project_root / "airflow"),
    "AIRFLOW__CORE__DAGS_FOLDER": str(airflow_2_dags_dir),
    "PYTHONPATH": "...",
    "PROJECT_ROOT": str(project_root),
    "OUTPUT_DIR": str(output_dir),
}
```

**Domain-specific configuration**

## Output Quality

### Flask Agent
- Working Flask app
- Basic HTML/CSS
- Single file structure
- Generic styling

### Airflow Agent
- Production-ready DAG code
- Complete type hints
- Comprehensive documentation
- Proper file structure (`dags/name/src/main.py`)
- Heartbeat-safe code
- Flake8 compliant
- Environment-aware
- Error handling
- CLAUDE.md compliant

## Migration Capability

### Flask Agent
- ❌ No migration workflow
- Only creates new apps

### Airflow Agent
- ✅ Complete migration workflow
- Analyzes legacy code
- Updates imports (1.0 → 2.0)
- Refactors monolithic functions
- Implements TaskGroups
- Converts Variables to Connections
- Ensures heartbeat safety
- Full modernization

## Summary Statistics

| Metric | Flask Agent | Airflow Agent |
|--------|-------------|---------------|
| Prompt files | 4 | 5 |
| Total prompt lines | ~50 | ~800 |
| Agents | 3 | 4 |
| Workflows | 1 | 2 |
| Standards enforced | ~3 | 10+ |
| Interactive inputs | 0 | 2-3 per workflow |
| Code examples in prompts | Few | Extensive |
| Domain depth | Generic | Deep |

## Key Improvements in Airflow Agent

1. **Domain Specialization**: Deep Airflow expertise vs generic web dev
2. **Multiple Workflows**: Creation + Migration vs creation only
3. **Interactive Input**: Guided prompts vs one-shot execution
4. **Standards Enforcement**: CLAUDE.md compliance vs general practices
5. **Agent Coordination**: Multi-phase orchestration vs single execution
6. **Code Quality**: Comprehensive validation vs basic review
7. **Documentation**: Extensive examples vs brief guidance
8. **Tool Matching**: Purpose-specific tools vs generic access
9. **Migration Support**: Full 1.0→2.0 workflow vs none
10. **Production Ready**: Enterprise-grade vs demo-quality

## Conclusion

The Airflow agent represents a significant evolution from the Flask template:
- **Deeper domain knowledge** through specialized agents
- **Better code quality** through comprehensive standards
- **More flexibility** with dual workflows
- **Better user experience** through interactive guidance
- **Production readiness** through multi-phase validation

While the Flask agent is great for quick demos, the Airflow agent is designed for **professional data engineering work** with strict quality standards.
