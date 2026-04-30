"""Model: kling_2_6_motion_pro
3 operations: post_create, get_list, get_task
"""
from src.services.models.kling_2_6_motion_pro.post_create import create_task, ENDPOINT, STATUS_PATH
from src.services.models.kling_2_6_motion_pro.get_list import list_tasks
from src.services.models.kling_2_6_motion_pro.get_task import get_task

__all__ = ["create_task", "list_tasks", "get_task", "ENDPOINT", "STATUS_PATH"]
