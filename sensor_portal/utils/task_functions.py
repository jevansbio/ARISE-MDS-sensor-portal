import logging
from typing import Any

from sensor_portal.celery import app

logger = logging.getLogger(__name__)


class TooManyTasks(Exception):
    """
    Exception raised when too many instances of a specific task are running.
    """

    def __init__(self, task: Any) -> None:
        """
        Initialize the TooManyTasks exception.

        Args:
            task: The Celery task instance that triggered the exception.
        """
        self.task_id: str = task.request.id
        self.task_name: str = task.name
        self.current_retries: int = task.request.retries
        self.max_retries: int = task.max_retries
        super(TooManyTasks, self).__init__()

    def __str__(self) -> str:
        """
        Return a descriptive error message.

        Returns:
            str: Error message with task details.
        """
        return (
            f"{self.task_id} not run. Too many {self.task_name} tasks already running. "
            f"Try {self.current_retries}/{self.max_retries}"
        )


def check_simultaneous_tasks(task: Any, max_tasks: int) -> None:
    """
    Check the number of currently running instances of a given task and
    raise an exception if the number exceeds the allowed maximum.

    Args:
        task: The Celery task instance to check for.
        max_tasks: The maximum allowed number of simultaneous task instances.

    Raises:
        TooManyTasks: If the maximum number of simultaneous tasks is exceeded.
    """
    active_tasks = app.control.inspect().active()
    all_tasks = []
    for worker, running_tasks in active_tasks.items():
        for running_task in running_tasks:
            if (task.name in running_task["name"] and running_task["id"] != task.request.id):
                all_tasks.append(task)
    logger.info(f"{len(all_tasks)} running")
    if len(all_tasks) + 1 > max_tasks:
        raise TooManyTasks(task)
