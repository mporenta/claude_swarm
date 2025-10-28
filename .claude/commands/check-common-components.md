# Check Common Components

You are executing the **Check Common Components** workflow. This is MANDATORY before creating any custom operators, hooks, utilities, or integration code.

## Execution Protocol

### Step 1: Search Common Directory Structure

Search for all available components in the common directory:

```bash
# Find all operators
find /home/dev/claude_dev/airflow/data-airflow/dags/common/custom_operators -name "*.py" -type f 2>/dev/null || echo "Operators directory not accessible"

# Find all hooks
find /home/dev/claude_dev/airflow/data-airflow/dags/common/custom_hooks -name "*.py" -type f 2>/dev/null || echo "Hooks directory not accessible"

# Find all callbacks
find /home/dev/claude_dev/airflow/data-airflow/dags/common/custom_callbacks -name "*.py" -type f 2>/dev/null || echo "Callbacks directory not accessible"
```

### Step 2: Search for Task-Specific Functionality

Based on the user's requirements, search for relevant components using keywords:

- **SFTP**: `grep -r "sftp" /home/dev/claude_dev/airflow/data-airflow/dags/common --include="*.py" -i`
- **Snowflake**: `grep -r "class.*Snowflake.*Operator" /home/dev/claude_dev/airflow/data-airflow/dags/common --include="*.py"`
- **S3**: `grep -r "class.*S3.*Hook" /home/dev/claude_dev/airflow/data-airflow/dags/common --include="*.py"`
- **PestRoutes**: `grep -r "PestRoutes" /home/dev/claude_dev/airflow/data-airflow/dags/common --include="*.py" -i`
- **Google Sheets**: `grep -r "Sheets" /home/dev/claude_dev/airflow/data-airflow/dags/common --include="*.py" -i`

### Step 3: Read Relevant Implementations

For any promising matches, READ the full implementation to understand capabilities:

```bash
cat /home/dev/claude_dev/airflow/data-airflow/dags/common/custom_operators/[filename].py
```

### Step 4: Generate Decision Report

Provide a structured report:

```markdown
## Common Components Check Report

**Task**: [Describe what the user is trying to implement]

**Search Results**:
- Found [N] operators in common/custom_operators/
- Found [N] hooks in common/custom_hooks/
- Found [N] callbacks in common/custom_callbacks/

**Relevant Components**:
1. **[Component Name]** (`[file path]`)
   - **Capabilities**: [What it does]
   - **Key Parameters**: [Main configuration options]
   - **Match**: [X]% fit for requirements
   - **Why**: [Explain the match]

2. [Additional components if found...]

**Decision**: ✅ USE | ⚠️ EXTEND | 🆕 CREATE

**Reasoning**:
[Explain the decision based on:]
- Coverage of requirements
- Parameter flexibility
- Extension points available
- Gaps in functionality

**Recommended Implementation**:

[Provide code example showing:]
- Import statement
- Component instantiation
- Parameter configuration
- OR: Inheritance structure if extending
- OR: Justification for creating new component
```

## Decision Matrix

**USE (80%+ match)**:
- Component meets requirements with existing parameters
- Minor configuration achieves goals
- No custom logic needed

**EXTEND (50-79% match)**:
- Core functionality exists but needs custom behavior
- Can inherit and override specific methods
- Maintains compatibility with common component

**CREATE (0-49% match)**:
- No existing component addresses the use case
- Requirements are fundamentally different
- Document why existing components don't fit

## Available Components Reference

### Custom Operators
- **SFTPToSnowflakeOperator**: SFTP → S3 → Snowflake (manifest/Snowflake filtering)
- **CustomSheetsToSnowflakeOperator**: Google Sheets → Snowflake
- **CrossDbOperator**: Cross-database operations
- **SnowflakeToS3StageOperator**: Snowflake → S3 staging
- **SnowflakeToPestroutesOperator**: Snowflake → PestRoutes
- **SnowflakeExternalTableOperator**: External table creation
- **CustomSparkKubernetesOperator**: Spark on K8s
- **TriggerDbtJobOperator**: dbt Cloud job triggering
- **CustomPestRoutesToS3Operator**: PestRoutes API → S3 (20+ entities)

### Custom Hooks
- **CustomSnowflakeHook**: Enhanced Snowflake operations
- **CustomExternalTableHook**: External table management
- **CustomS3Hook**: S3 operations with prefix support
- **S3ToSnowflakeHook**: S3 → Snowflake data loading
- **S3ToSnowflakeInsertHook**: S3 → Snowflake inserts
- **CustomPestRoutesHook**: PestRoutes API integration
- **CustomGoogleSheetsHook**: Google Sheets API

### Custom Callbacks
- **AirflowCallback**: Success/failure callbacks (Slack, logging, metrics)

## Critical Reminders

1. **DRY Principle**: If it exists in `common/`, USE IT
2. **No Duplication**: Creating duplicate code is a critical error
3. **Cost of Duplication**:
   - Maintenance burden (bug fixes in multiple places)
   - Inconsistent behavior
   - Technical debt
   - Testing overhead

4. **Anti-Pattern Example**: The `cresta` DAG created 407 lines of redundant SFTP code instead of using `SFTPToSnowflakeOperator`

## After Report

After providing the report:
- Wait for user confirmation before implementing
- If using existing component, show import and configuration
- If extending, show inheritance structure
- If creating, justify why common components insufficient

**DO NOT proceed with implementation until this check is complete.**
