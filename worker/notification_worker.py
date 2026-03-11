"""Notification worker - background job logic for task notifications.

This module contains the core logic for checking and sending notifications
based on various trigger types.
"""

import sys
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

# Add src directory to path for imports
sys.path.insert(0, "/usr/local/app/src")

from config import settings
from task_queries import (
    get_overdue_tasks,
    get_urgent_tasks,
    get_today_tasks,
    get_tomorrow_tasks,
    get_high_priority_due_soon,
)
from notification_service import notification_service


async def check_and_notify(trigger_type: str) -> dict:
    """Check for tasks matching trigger type and send notification.

    Args:
        trigger_type: One of "overdue", "urgent", "today", "tomorrow", "high_priority"

    Returns:
        Dict with results of the check
    """
    if not settings.NOTIFICATION_ENABLED:
        return {"status": "disabled", "tasks_found": 0, "notification_sent": False}

    eastern_tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(eastern_tz)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*50}")
    print(f"Notification Worker: {trigger_type.upper()}")
    print(f"Time: {now_str}")
    print(f"{'='*50}\n")

    tasks = []

    match trigger_type:
        case "overdue":
            tasks = await get_overdue_tasks()
        case "urgent":
            tasks = await get_urgent_tasks(hours=4)
        case "today":
            tasks = await get_today_tasks()
        case "tomorrow":
            tasks = await get_tomorrow_tasks()
        case "high_priority":
            tasks = await get_high_priority_due_soon(days=3)
        case _:
            print(f"Unknown trigger type: {trigger_type}")
            return {"status": "error", "error": f"Unknown trigger type: {trigger_type}"}

    notification_sent = False
    if tasks:
        notification_sent = await notification_service.send_notification(
            trigger_type=trigger_type,
            tasks=tasks
        )
    else:
        print(f"No tasks found for trigger: {trigger_type}")

    result = {
        "trigger_type": trigger_type,
        "status": "completed",
        "tasks_found": len(tasks),
        "notification_sent": notification_sent,
        "timestamp": now.isoformat()
    }

    print(f"\n{'='*50}")
    print(f"Result: {result}")
    print(f"{'='*50}\n")

    return result


async def run_all_checks() -> list[dict]:
    """Run all notification checks (useful for testing).

    Returns:
        List of results from each check
    """
    triggers = ["overdue", "urgent", "today", "high_priority"]
    results = []

    for trigger in triggers:
        result = await check_and_notify(trigger)
        results.append(result)

    return results
