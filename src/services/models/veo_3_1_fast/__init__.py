"""Model: veo_3_1_fast
3 operations: post_create, get_list, get_task
"""
from src.services.models.veo_3_1_fast.post_create import create_task, ENDPOINT_TEXT, ENDPOINT_IMAGE, STATUS_PATH_TEXT, STATUS_PATH_IMAGE
from src.services.models.veo_3_1_fast.get_list import list_tasks
from src.services.models.veo_3_1_fast.get_task import get_task

ENDPOINT = ENDPOINT_TEXT

__all__ = ["create_task", "list_tasks", "get_task", "ENDPOINT", "ENDPOINT_TEXT", "ENDPOINT_IMAGE", "STATUS_PATH_TEXT", "STATUS_PATH_IMAGE"]
