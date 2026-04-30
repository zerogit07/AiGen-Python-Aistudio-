from __future__ import annotations

import time
from dataclasses import dataclass, field

from src.core.types import ModelStats


@dataclass
class JobLog:
    user_id: int
    model_id: str
    timestamp: int
    prompt: str


global_stats = ModelStats()
global_logs: list[JobLog] = []


def log_activity(user_id: int, model_id: str, prompt: str) -> None:
    global_stats.total_videos += 1
    global_stats.model_usage[model_id] = (
        global_stats.model_usage.get(model_id, 0) + 1
    )
    global_logs.insert(
        0,
        JobLog(
            user_id=user_id,
            model_id=model_id,
            timestamp=int(time.time() * 1000),
            prompt=prompt,
        ),
    )
    # Keep only last 100 logs
    while len(global_logs) > 100:
        global_logs.pop()
