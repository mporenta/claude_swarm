# Data Engineering Agents

Claude-powered agents for automating data engineering workflows and infrastructure management.

## Overview

This repository contains AI agents built using the Claude API to assist the Aptive Data Engineering team with:

- Automated infrastructure repository creation
- Standardized Terraform configuration generation
- Workflow automation and operational tasks
- Code migration and transformation

Agents encode team best practices and institutional knowledge, reducing cognitive load and ensuring consistency across projects.

--- 

## Repository Structure

```
data-de-agents/
├── agents/                    # Individual agent implementations
│   ├── <agent-name>/
│   │   ├── main.py           # CLI entry point
│   │   ├── agent.py          # Agent logic and conversation flow
│   │   ├── tools.py          # Tool definitions
│   │   ├── prompts.py        # System prompts and instructions
│   │   └── README.md         # Agent-specific documentation
│   └── ...
├── shared/                    # Shared utilities across agents
│   ├── github_utils.py       # GitHub API helpers
│   ├── aws_utils.py          # AWS SDK helpers
│   ├── config.py             # Team standards and conventions
│   └── templates/            # Reusable templates
├── tests/                     # Test suite
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

Each agent has its own directory with a dedicated README explaining its specific purpose and usage.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Claude API access (team service account)
- GitHub access token (for agents that interact with repositories)
- AWS credentials (for agents that interact with AWS services)

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone git@github.com:aptive/data-de-agents.git
   cd data-de-agents
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure credentials:**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Add required credentials to `.env`:
   ```bash
   # Claude API (get from team password manager)
   ANTHROPIC_API_KEY=sk-ant-...
   
   # GitHub (personal access token with repo scope)
   GITHUB_TOKEN=ghp_...
   
   # AWS (use your existing credentials)
   AWS_PROFILE=default
   ```
   
   **Never commit `.env` to git** - it's already in `.gitignore`.

4. **Verify setup:**
   ```bash
   python -c "import anthropic; print('Setup successful!')"
   ```

### Running an Agent

Navigate to the specific agent directory and follow its README:

```bash
cd agents/<agent-name>
python main.py
```

Most agents run interactively, asking questions to gather requirements before taking action.

---

## Team Infrastructure Standards

Agents in this repository generate infrastructure that follows these standards:

### AWS Account Structure

- **Development/Staging**: AWS Account `595908349263`
- **Production**: Separate AWS Account
- **Region**: us-east-1 (all resources)
- **VPC**: Functions run in VPC by default

### Terraform Configuration

**State Management:**
- Backend: S3 bucket `aptive.data-production.terraform-state`
- Locking: DynamoDB table `terraform-state-lock`
- State organization: `[repo-name]/[environment]/terraform.tfstate`

**Repository structure:**
- Modules in `terraform/modules/`
- Environment configs in `terraform/environments/{dev,prod}/`
- Source code in `src/[function-name]/`

### Lambda Standards

- **Runtime**: Python 3.11 (default for new functions)
- **Naming**: `[domain]-[action]-[resource]-[environment]`
- **Layers**: Reference centralized layers repo (baseutils, dataprocessing, databaseconnectors, messaging, aiml)
- **VPC**: Required for database/internal service access
- **Build**: Dependencies packaged with function code

### Common Infrastructure Patterns

**Lambda + API Gateway**
- REST API endpoints with Lambda integration
- Optional API key requirement and CORS configuration

**Lambda + S3 Trigger**
- Process files uploaded to S3
- Filter by prefix/suffix, configurable concurrency

**Lambda + EventBridge Schedule**
- Scheduled/cron jobs
- Configurable schedule expressions

**Lambda + SQS/SNS**
- Asynchronous message processing
- Dead letter queues and retry policies

**DynamoDB Tables**
- NoSQL database with optional GSIs
- On-demand or provisioned billing

**Kinesis Firehose to S3**
- Streaming data ingestion to data lake
- Configurable buffering and compression

### CI/CD Standards

- **Branch strategy**: `staging` → dev, `master` → prod
- **Authentication**: OIDC (no long-lived credentials)
- **Environments**: dev (auto-deploy), prod (manual approval)
- **Workflows**: Separate plan and apply per environment

### Naming Conventions

| Resource | Format | Example |
|----------|--------|---------|
| Lambda Functions | `[domain]-[action]-[resource]-[env]` | `solar-query-metrics-dev` |
| DynamoDB Tables | `[domain]-[resource]-[env]` | `solar-metrics-dev` |
| IAM Roles | `[resource-name]-[purpose]-role` | `solar-query-metrics-dev-execution-role` |
| API Paths | `/[resource]` or `/[action]-[resource]` | `/query-metrics` |
| Firehose Streams | `[source]-[purpose]-[env]` | `sendgrid-events-dev` |

### Required Tags

All AWS resources must include:

```hcl
{
  Project     = "[project-name]"
  Environment = "dev" | "prod"
  ManagedBy   = "terraform"
  Repository  = "aptive/[repo-name]"
  Team        = "data-engineering"
  CostCenter  = "engineering"
}
```

### Secrets Management

- **Primary method**: AWS Secrets Manager
- **Naming**: `[repo-name]/[environment]/[resource-name]`
- **Access**: Lambda functions retrieve at runtime
- **Never**: Store application secrets in GitHub

---

## Development Guidelines

### Adding a New Agent

1. Create a new directory in `agents/`
2. Follow the standard agent structure (main.py, agent.py, tools.py, prompts.py)
3. Add agent-specific README with usage instructions
4. Update shared utilities if adding reusable functionality
5. Add tests in `tests/agents/<agent-name>/`
6. Create PR with at least one approval before merging to main

### Code Quality

- Follow PEP 8 style guidelines
- Add type hints where appropriate
- Include docstrings for functions and classes
- Write unit tests for tools and utilities
- Keep agent logic separate from tool implementations

### API Usage

All agents use the team's shared Anthropic API account:
- API key stored in team password manager
- Usage tracked centrally
- Estimated cost: ~$0.10-0.30 per agent interaction
- Report any unusual usage patterns to team lead

---

## Support

### Getting Help

- **Agent issues**: Check the agent's specific README first
- **Setup problems**: Contact [your name] or [team lead]
- **API access**: Request from team password manager
- **Feature requests**: Open an issue in this repository

### Contributing

We welcome contributions from the data engineering team! Please:
1. Create a feature branch
2. Make your changes
3. Add/update tests and documentation
4. Submit a PR for review
5. Get at least one approval before merging

---

## Security

**Never commit sensitive information:**
- API keys
- AWS credentials
- GitHub tokens
- Database passwords
- Any `.env` files

All credentials should be stored in:
- Team password manager (1Password, etc.)
- AWS Secrets Manager
- Environment variables (local development)

If you accidentally commit secrets, immediately:
1. Rotate the compromised credentials
2. Notify the team lead
3. Remove from git history using `git-filter-repo` or similar

---

## Additional Resources

- [Claude API Documentation](https://docs.anthropic.com)
- [Anthropic Console](https://console.anthropic.com) (for usage monitoring)
- [Team Terraform Standards](link to internal docs if available)
- [AWS Infrastructure Guide](link to internal docs if available)

---

**Maintained by**: Aptive Data Engineering Team  
**Questions?** Contact mason.porter@goaptive.com
