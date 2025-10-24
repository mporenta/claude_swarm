"""
Invoca API interaction functions.

This module provides functions for connecting to the Invoca API and
fetching transaction data with pagination support and error handling.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from airflow.hooks.base import BaseHook
from airflow.models import Variable

# Set up logging
logger = logging.getLogger(__name__)

# Default date range for initial data fetch
DEFAULT_START_DATE = '2024-02-01'
DEFAULT_END_DATE = '2024-02-01'

# Rate limiting configuration
RATE_LIMIT_RETRY_MAX = 3
RATE_LIMIT_BACKOFF_SECONDS = 30
NORMAL_REQUEST_DELAY_SECONDS = 3


def get_conn(endpoint: str) -> Tuple[str, Dict[str, str]]:
    """
    Get API credentials from Airflow connection.

    Retrieves the Invoca API connection details from the 'invoca' connection
    and constructs the base URL and headers for API requests.

    Args:
        endpoint (str): The API endpoint (e.g., '2020-10-01/advertisers/transactions')

    Returns:
        Tuple[str, Dict[str, str]]: A tuple containing:
            - base_url (str): The full API URL with account number
            - headers (Dict[str, str]): Authorization headers for API requests

    Raises:
        Exception: If unable to retrieve connection or missing required extras
    """
    logger.info('Getting API Credentials from Invoca connection...')
    try:
        conn_id = "invoca"
        conn = BaseHook.get_connection(conn_id)
        host = conn.host
        account_number = conn.extra_dejson.get('account_number')
        auth_token = conn.extra_dejson.get('auth_token')

        if not account_number or not auth_token:
            raise ValueError(
                "Invoca connection must have 'account_number' and 'auth_token' in extras"
            )

        base_url = f'{host}/{endpoint}/{account_number}.json'
        headers = {"Authorization": auth_token}

        logger.info('API Credentials retrieved successfully')
        return base_url, headers

    except Exception as e:
        logger.error(f'Error retrieving API credentials: {e}')
        raise


def fetch_transactions(
    base_url: str,
    headers: Dict[str, str],
    base_params: Dict[str, Any],
    task_name: str
) -> List[Dict[str, Any]]:
    """
    Fetch transactions from Invoca API with pagination support.

    Implements incremental sync via start_after_transaction_id pagination,
    with error handling for rate limiting and network issues.

    Args:
        base_url (str): The API endpoint URL
        headers (Dict[str, str]): Authorization headers
        base_params (Dict[str, Any]): Base query parameters
        task_name (str): Name of the task (used for pagination state tracking)

    Returns:
        List[Dict[str, Any]]: List of transaction records fetched from API

    Raises:
        Exception: If max retries exceeded or unrecoverable API error occurs
    """
    transactions: List[Dict[str, Any]] = []
    has_more_data = True
    variable_key = f"invoca_{task_name}_last_id"
    start_after_transaction_id: Optional[str] = Variable.get(
        variable_key,
        default_var=None
    )

    logger.info(f'Starting transaction fetch for {task_name}')
    logger.info(f'Using pagination starting point: {start_after_transaction_id}')

    while has_more_data:
        # Create a copy of base parameters for each iteration
        current_params = base_params.copy()

        # Determine pagination parameters
        if start_after_transaction_id:
            # Use pagination token for subsequent requests
            current_params["start_after_transaction_id"] = start_after_transaction_id
            # Remove date-based parameters when using pagination
            current_params.pop("from", None)
            current_params.pop("to", None)
        else:
            # Use default date range for initial request
            current_params.setdefault("from", DEFAULT_START_DATE)
            current_params.setdefault("to", DEFAULT_END_DATE)

        logger.info(f"Fetching data with params: {current_params}")

        try:
            response = requests.get(
                base_url,
                headers=headers,
                params=current_params,
                timeout=30
            )

            if response.status_code == 200:
                # Successful response
                batch = response.json()

                if batch:
                    # Data received, add to transactions list
                    transactions.extend(batch)
                    start_after_transaction_id = batch[-1].get('transaction_id')
                    batch_size = len(batch)
                    logger.info(
                        f'Fetched {batch_size} transactions. '
                        f'Last transaction ID: {start_after_transaction_id}'
                    )
                    # Delay before next request to respect rate limits
                    time.sleep(NORMAL_REQUEST_DELAY_SECONDS)
                else:
                    # Empty batch indicates end of data
                    has_more_data = False
                    logger.info("No more data to fetch from API")

            elif response.status_code == 429:
                # Rate limit encountered
                logger.warning("Rate limit (429) encountered from Invoca API")
                retry_after = response.headers.get("Retry-After")
                retry_delay = int(retry_after) if retry_after else RATE_LIMIT_BACKOFF_SECONDS

                logger.info(f"Rate limit encountered. Waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Do not increment transaction count, will retry same request

            else:
                # Other HTTP errors
                error_msg = (
                    f'API returned status code {response.status_code}: '
                    f'{response.text}'
                )
                logger.error(error_msg)
                raise requests.exceptions.RequestException(error_msg)

        except requests.exceptions.Timeout as e:
            logger.error(f'API request timeout: {e}')
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f'API request failed: {e}')
            raise

    # Update pagination checkpoint for next run
    if transactions:
        logger.info(
            f'Updating pagination checkpoint with last transaction ID: '
            f'{start_after_transaction_id}'
        )
        Variable.set(variable_key, start_after_transaction_id)
        total_fetched = len(transactions)
        logger.info(f'Transaction fetch complete. Total fetched: {total_fetched}')
    else:
        logger.info('No transactions fetched in this run')

    return transactions


def fetch_data(
    task_name: str,
    endpoint: str,
    params: Dict[str, Any],
    **kwargs: Any
) -> List[Dict[str, Any]]:
    """
    Dispatcher function to fetch data based on task type.

    This function routes data fetch requests to the appropriate handler
    based on the task_name parameter.

    Args:
        task_name (str): Name of the task to execute
        endpoint (str): API endpoint to fetch from
        params (Dict[str, Any]): Query parameters for API request
        **kwargs: Airflow context (unused but accepted for compatibility)

    Returns:
        List[Dict[str, Any]]: Fetched data records

    Raises:
        ValueError: If task_name is not recognized
        Exception: If data fetch fails
    """
    logger.info(f'Fetching data for task: {task_name} from endpoint: {endpoint}')

    if task_name == 'transactions':
        base_url, headers = get_conn(endpoint)
        transactions = fetch_transactions(base_url, headers, params, task_name)
        return transactions
    else:
        error_msg = f'Unknown task: {task_name}. Must be one of: [transactions]'
        logger.error(error_msg)
        raise ValueError(error_msg)
