"""
Main entry point for Invoca to Snowflake DAG.

This module provides the Main class which serves as the entry point for all
Invoca to Snowflake DAG tasks and contains the task configuration.
"""

from typing import Any, Dict, List


class Main:
    """
    Main class for Invoca to Snowflake DAG tasks.

    Provides configuration and execution methods for Invoca API
    data ingestion into Snowflake via S3.
    """

    # Task configuration for all endpoints
    TASKS: List[Dict[str, Any]] = [
        {
            'active': 1,
            'task_name': 'transactions',
            'endpoint': '2020-10-01/advertisers/transactions',
            'params': {
                'include_columns': '$invoca_custom_columns, $invoca_default_columns'
                # 'limit': 50  # For testing only
            },
            'schema_name': 'invoca',
            'table_name': 'transactions'
        }
    ]

    def __init__(self) -> None:
        """Initialize Main class."""
        pass

    def execute(self, **kwargs: Any) -> None:
        """
        Execute the main DAG logic.

        This method is provided for compatibility with standard DAG patterns
        but is not used since individual task callables are defined separately.

        Args:
            **kwargs: Airflow context and op_kwargs
        """
        pass

    @classmethod
    def get_tasks(cls) -> List[Dict[str, Any]]:
        """
        Get the list of configured tasks.

        Returns:
            List[Dict[str, Any]]: List of task configurations
        """
        return cls.TASKS

    @classmethod
    def get_active_tasks(cls) -> List[Dict[str, Any]]:
        """
        Get the list of active tasks (filtered by 'active' flag).

        Returns:
            List[Dict[str, Any]]: List of active task configurations
        """
        return [task for task in cls.TASKS if task.get('active', 0) == 1]
