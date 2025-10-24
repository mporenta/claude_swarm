"""
Invoca data processing and loading functions.

This module provides functions for ensuring Snowflake tables exist and
uploading fetched data to S3 and Snowflake.
"""

import logging
from typing import Any, Dict, Optional

from common.custom_hooks.custom_s3_hook import CustomS3Hook
from common.custom_hooks.custom_snowflake_hook import CustomSnowflakeHook

from .invoca_api import fetch_data

# Set up logging
logger = logging.getLogger(__name__)


def ensure_transactions_table(
    schema_name: str,
    table_name: str,
    **kwargs: Any
) -> None:
    """
    Ensure that the transactions table exists in Snowflake.

    Creates the table if it does not exist, using the CustomSnowflakeHook
    to handle environment-specific database selection.

    Args:
        schema_name (str): Snowflake schema name (e.g., 'invoca')
        table_name (str): Snowflake table name (e.g., 'transactions')
        **kwargs: Airflow context (unused but accepted for compatibility)

    Raises:
        Exception: If unable to check or create the table
    """
    logger.info(f'Ensuring table {schema_name}.{table_name} exists...')

    try:
        hook = CustomSnowflakeHook()

        # Check if table exists
        table_exists = hook.check_table_exists(schema_name, table_name)

        if table_exists:
            logger.info(f'Table {schema_name}.{table_name} already exists')
        else:
            logger.info(f'Table {schema_name}.{table_name} does not exist. Creating...')
            # Create table with raw JSON schema
            hook.ensure_table_exists(schema_name, table_name, table_types=['raw'])
            logger.info(f'Table {schema_name}.{table_name} created successfully')

    except Exception as e:
        logger.error(f'Error ensuring table exists: {e}')
        raise


def fetch_and_upload_to_s3(
    task_name: str,
    endpoint: str,
    params: Dict[str, Any],
    schema_name: str,
    table_name: str,
    **kwargs: Any
) -> Optional[str]:
    """
    Fetch data from Invoca API and upload to S3.

    Orchestrates the process of fetching transactions from the Invoca API
    and uploading the results to S3 as JSON.

    Args:
        task_name (str): Name of the task (determines which API endpoint)
        endpoint (str): API endpoint to fetch from
        params (Dict[str, Any]): Query parameters for API
        schema_name (str): S3 prefix schema name
        table_name (str): S3 prefix table name
        **kwargs: Airflow context

    Returns:
        Optional[str]: S3 key of uploaded file, or None if no data

    Raises:
        Exception: If fetch or upload fails
    """
    logger.info(
        f'Starting data fetch and S3 upload for {task_name} '
        f'({schema_name}.{table_name})'
    )

    try:
        # Fetch data from API
        logger.info(f'Fetching data from Invoca API endpoint: {endpoint}')
        data = fetch_data(task_name, endpoint, params, **kwargs)

        if not data:
            logger.info('No data fetched from API. Skipping S3 upload.')
            return None

        logger.info(f'Fetched {len(data)} records from API')

        # Upload to S3
        logger.info(f'Uploading {len(data)} records to S3...')
        try:
            s3_hook = CustomS3Hook(
                s3_prefix=f"{schema_name}/{table_name}",
                data=data,
                file_type="json"
            )
            s3_key = s3_hook.upload_file()
            logger.info(f'Successfully uploaded data to S3: {s3_key}')
            return s3_key

        except Exception as e:
            logger.error(f'Error uploading file to S3: {e}')
            raise

    except Exception as e:
        logger.error(f'Error in fetch and upload process: {e}')
        raise
