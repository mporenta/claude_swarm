# Invoca DAG Migration - Complete Index

**Project**: Airflow 1.0 to 2.0 Migration
**DAG**: invoca_to_snowflake
**Status**: COMPLETE & PRODUCTION-READY
**Date**: October 24, 2025

---

## Navigation Guide

### For Quick Start
Start here if you just want to deploy:
1. Read: **README.md** (Quick start, configuration, tasks)
2. Then: Copy files and test locally
3. See: Deployment Checklist in MIGRATION_COMPLETED.md

### For Understanding the Migration
1. Read: **MIGRATION_COMPLETED.md** (Detailed migration changes)
2. Reference: **MIGRATION_MAPPING.md** (Before/after code mapping)
3. Review: **hourly.py** and **src/** files

### For Operational Support
1. Consult: **README.md** (Configuration, debugging, monitoring)
2. Check: Common Issues section in README.md
3. Run: Monitoring queries from README.md

### For Complete Details
1. **INVOCA_MIGRATION_SUMMARY.md** (Original analysis - in parent directory)
2. **MIGRATION_COMPLETED.md** (Complete migration details)
3. **MIGRATION_MAPPING.md** (Line-by-line mapping)

---

## File Organization

### DAG Implementation (Production Files)
These are the actual DAG files deployed to Airflow:

```
hourly.py (152 lines)
  ├─ Main DAG definition
  ├─ Airflow 2.0 operators and callbacks
  ├─ Task loop for endpoint configuration
  └─ Environment-aware scheduling

src/main.py (70 lines)
  ├─ Configuration via Main class
  ├─ Task definitions
  └─ Helper methods (get_tasks, get_active_tasks)

src/invoca_api.py (218 lines)
  ├─ get_conn() - API credentials
  ├─ fetch_transactions() - Paginated API fetch
  ├─ fetch_data() - Task dispatcher
  └─ Enhanced error handling & rate limiting

src/invoca_processor.py (118 lines)
  ├─ ensure_transactions_table() - Table check/create
  └─ fetch_and_upload_to_s3() - Fetch & upload orchestration
```

**Total Code**: ~560 lines (modular, type-hinted)

### Documentation (Reference & Support)
These files provide guidance and documentation:

```
README.md (400+ lines)
  ├─ Quick start guide
  ├─ Configuration requirements
  ├─ Task breakdown with timings
  ├─ Code examples
  ├─ Debugging guide with common issues
  ├─ Monitoring queries
  └─ Maintenance procedures

MIGRATION_COMPLETED.md (500+ lines)
  ├─ Migration summary
  ├─ Before/after comparisons
  ├─ Error handling improvements
  ├─ Code organization changes
  ├─ Type hints addition
  ├─ Hook integration
  ├─ Testing procedures
  ├─ Deployment steps
  ├─ Rollback plan
  └─ Success criteria

MIGRATION_MAPPING.md (400+ lines)
  ├─ Import mapping table
  ├─ Function mapping (legacy → modern)
  ├─ Configuration mapping
  ├─ DAG definition mapping
  ├─ Error handling mapping
  ├─ Type hints migration
  ├─ Module organization comparison
  └─ Summary table

INDEX.md (This file)
  └─ Navigation and file organization guide
```

**Total Documentation**: ~1300+ lines

### Metadata Files
```
__init__.py (2 lines)
  └─ Root package marker

src/__init__.py (2 lines)
  └─ Source package marker
```

---

## By Use Case

### "I just need to deploy this"
Files to read (in order):
1. README.md - Configuration section
2. MIGRATION_COMPLETED.md - Deployment steps section
3. Copy the files and test locally

Expected time: 15 minutes (excluding testing)

### "I want to understand what changed"
Files to read (in order):
1. MIGRATION_COMPLETED.md - Executive Summary & Migration Changes
2. MIGRATION_MAPPING.md - Complete mapping reference
3. Review hourly.py and src/ files
4. Compare with legacy files

Expected time: 1-2 hours

### "I need to debug an issue"
Files to reference:
1. README.md - Debugging guide & Common Issues section
2. MIGRATION_COMPLETED.md - Error Handling Improvements section
3. Check appropriate task logs in /home/dev/airflow/logs/

Expected time: 10-30 minutes

### "I need to monitor the DAG"
Files to reference:
1. README.md - Monitoring & Debugging section
2. README.md - Useful Snowflake Queries section
3. README.md - Task breakdown with timings

Expected time: 5-10 minutes

### "I need to modify or extend the DAG"
Files to read (in order):
1. README.md - Maintenance & Updates section
2. MIGRATION_MAPPING.md - Code organization section
3. src/main.py - Configuration section
4. Review relevant task functions

Expected time: 30 minutes - 1 hour

---

## Key Features Summary

### Pagination & State
- Uses `start_after_transaction_id` for incremental sync
- Pagination state stored in Variable: `invoca_transactions_last_id`
- Automatic recovery from checkpoint

### Error Handling
- Rate limiting: HTTP 429 with max 3 retries
- Request timeout: 30 seconds
- Explicit exception raising (no silent failures)
- Retry-After header support

### Environment Awareness
- Local: Manual triggers only
- Staging: Hourly at :30 minute (7 AM - 11 PM)
- Production: Hourly on hour (7 AM - 11 PM)
- Database: RAW_STAGING (dev) or RAW (prod)

### Modern Patterns
- Full type hints (100% coverage)
- Comprehensive docstrings
- Modular single-responsibility functions
- Modern Airflow 2.0 operators and callbacks
- Heartbeat-safe code

---

## Configuration Quick Reference

### Required Connections
- `invoca` (API connection with account_number & auth_token)
- `snowflake_default` (auto-managed)
- `aws_default` (auto-managed)

### Required Variables
- `env` (local/staging/prod)
- `etl-tmp-bucket` (S3 bucket name)
- `invoca_transactions_last_id` (auto-managed)

### Schedules
- Local: None
- Staging: 30 7-23 * * *
- Production: 0 7-23 * * *

---

## Testing Steps

### Local
```bash
python -m py_compile src/*.py hourly.py
python -c "from dags.invoca_to_snowflake.hourly import dag; print(dag.dag_id)"
AIRFLOW_VAR_env=local airflow dags test invoca_to_snowflake 2024-02-01
```

### Staging
- Deploy to staging
- Run 3 hourly cycles
- Monitor logs for errors
- Verify data consistency

### Production
- Copy files
- Verify DAG loads
- Schedule-based monitoring
- Track first week of runs

---

## Common Tasks

### Deploy DAG
1. Copy /home/dev/claude_swarm/generated_dags/invoca_to_snowflake to /home/dev/airflow/data-airflow/dags/
2. Refresh Airflow: `python scripts/refresh_pg_db.py`
3. Verify in UI: should see "invoca_to_snowflake" DAG

### Update API Credentials
1. Go to Airflow UI → Admin → Connections
2. Find 'invoca' connection
3. Update extras with new account_number and auth_token
4. No DAG redeploy needed

### Reset Pagination
```bash
airflow variables delete invoca_transactions_last_id
```
(Only use if data consistency issues occur)

### Monitor Data Load
```sql
SELECT s3_path, pipe_loaded_at, COUNT(*) as count
FROM raw_staging.invoca.transactions
GROUP BY s3_path, pipe_loaded_at
ORDER BY pipe_loaded_at DESC
LIMIT 10;
```

### Check Task Logs
```bash
tail -f /home/dev/airflow/logs/invoca_to_snowflake/*/task.log
```

---

## Support

### For Questions About
- **Migration details**: See MIGRATION_COMPLETED.md
- **Operations**: See README.md
- **Code mapping**: See MIGRATION_MAPPING.md
- **Configuration**: See README.md - Configuration section
- **Debugging**: See README.md - Debugging section

### Key Contacts
- **DAG Owner**: zak.browning@goaptive.com
- **Documentation**: This index + linked files
- **Code**: /home/dev/claude_swarm/generated_dags/invoca_to_snowflake/

---

## Document Details

| File | Lines | Purpose | Audience |
|------|-------|---------|----------|
| hourly.py | 152 | DAG definition | Developers, DevOps |
| src/main.py | 70 | Configuration | Developers |
| src/invoca_api.py | 218 | API functions | Developers |
| src/invoca_processor.py | 118 | Processing | Developers |
| README.md | 400+ | Operations guide | DevOps, Operators |
| MIGRATION_COMPLETED.md | 500+ | Migration details | Everyone |
| MIGRATION_MAPPING.md | 400+ | Reference mapping | Developers |
| INDEX.md | This | Navigation guide | Everyone |

---

## Quick Links to Sections

### README.md
- [Quick Start](README.md#quick-start)
- [Configuration](README.md#configuration)
- [Task Breakdown](README.md#task-breakdown)
- [Debugging](README.md#monitoring--debugging)
- [Common Issues](README.md#common-issues)
- [Maintenance](README.md#maintenance--updates)

### MIGRATION_COMPLETED.md
- [Migration Changes](MIGRATION_COMPLETED.md#migration-changes)
- [Error Handling](MIGRATION_COMPLETED.md#2-error-handling-improvements)
- [Testing](MIGRATION_COMPLETED.md#testing--validation)
- [Deployment](MIGRATION_COMPLETED.md#deployment-steps)
- [Rollback](MIGRATION_COMPLETED.md#rollback-plan)

### MIGRATION_MAPPING.md
- [Import Migrations](MIGRATION_MAPPING.md#import-migrations)
- [Function Migrations](MIGRATION_MAPPING.md#function-migrations)
- [Error Handling](MIGRATION_MAPPING.md#error-handling-migrations)
- [Summary Table](MIGRATION_MAPPING.md#summary-table)

---

## Version Information

- **Airflow 1.0**: Legacy version (original DAG)
- **Airflow 2.0**: Modern version (this migration)
- **Python**: 3.7+
- **Providers**: amazon, snowflake, core
- **Status**: Production-ready

---

**Last Updated**: October 24, 2025
**Status**: COMPLETE & PRODUCTION-READY
**Location**: `/home/dev/claude_swarm/generated_dags/invoca_to_snowflake/`
