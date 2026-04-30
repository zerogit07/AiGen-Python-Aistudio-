"""Model: kling_2_5_turbo
3 operations: post_create, get_list, get_task
"""
from src.services.models.kling_2_5_turbo.post_create import create_task, ENDPOINT, STATUS_PATH
from src.services.models.kling_2_5_turbo.get_list import list_tasks
from src.services.models.kling_2_5_turbo.get_task import get_task

__all__ = ["create_task", "list_tasks", "get_task", "ENDPOINT", "STATUS_PATH"]
