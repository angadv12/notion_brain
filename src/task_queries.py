"""Notification-specific task queries for Notion data source.

This module provides functions to query tasks based on various criteria
needed for notification triggers: overdue, urgent, due on specific dates,
and high priority tasks.
"""

import os
import httpx
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

from src.config import settings
from src.schemas import RelatedTask

# Notion API headers
headers = {
    "Authorization": f"Bearer {settings.NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2025-09-03"
}


async def _query_notion_with_filter(
    filter_dict: dict,
    page_size: int = 50
) -> list[RelatedTask]:
    """Base function to query Notion with a custom filter.

    Args:
        filter_dict: Notion filter dict for the query body
        page_size: Maximum results to return

    Returns:
        List of RelatedTask objects
    """
    if not settings.NOTION_DATA_SOURCE_ID:
        print("Warning: NOTION_DATA_SOURCE_ID not set")
        return []

    url = f"https://api.notion.com/v1/data_sources/{settings.NOTION_DATA_SOURCE_ID}/query"

    body = {
        "page_size": page_size,
        "filter": filter_dict
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=body, headers=headers)
            if response.status_code != 200:
                print(f"Notion Query Error: {response.text}")
                return []

            data = response.json()
            results = data.get("results", [])

            tasks = []
            for result in results:
                props = result.get("properties", {})

                # Extract title
                name_list = props.get("Name", {}).get("title", [])
                title = "".join([t.get("plain_text", "") for t in name_list])

                # Extract category
                category_obj = props.get("Category", {}).get("select")
                category = category_obj.get("name") if category_obj else None

                # Extract due date
                due_date_obj = props.get("Due date", {}).get("date")
                due_date = due_date_obj.get("start") if due_date_obj else None

                # Extract priority
                priority_obj = props.get("Priority", {}).get("select")
                priority = priority_obj.get("name") if priority_obj else None

                # Extract status
                status_obj = props.get("Status", {}).get("select")
                status = status_obj.get("name") if status_obj else None

                tasks.append(
                    RelatedTask(
                        id=result.get("id", ""),
                        title=title,
                        category=category,
                        due_date=due_date,
                        priority=priority,
                        status=status
                    )
                )

            return tasks

        except Exception as e:
            print(f"Error querying Notion: {e}")
            return []


async def get_overdue_tasks() -> list[RelatedTask]:
    """Get tasks that are overdue (due date < now, Status != "Done").

    Returns:
        List of overdue RelatedTask objects
    """
    eastern_tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(eastern_tz)
    now_iso = now.isoformat()

    # Compound filter: due date is before now AND status is not "Done"
    filter_dict = {
        "and": [
            {
                "property": "Due date",
                "date": {"before": now_iso}
            },
            {
                "property": "Status",
                "select": {"does_not_equal": "Done"}
            }
        ]
    }

    print(f"--- Checking for overdue tasks (before {now_iso}) ---")
    tasks = await _query_notion_with_filter(filter_dict)
    print(f"Found {len(tasks)} overdue tasks")
    return tasks


async def get_urgent_tasks(hours: int = 4) -> list[RelatedTask]:
    """Get tasks due within N hours (Status != "Done").

    Args:
        hours: Number of hours to look ahead (default: 4)

    Returns:
        List of urgent RelatedTask objects
    """
    eastern_tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(eastern_tz)
    cutoff = now + timedelta(hours=hours)
    cutoff_iso = cutoff.isoformat()
    now_iso = now.isoformat()

    # Due date within next N hours AND status is not "Done"
    filter_dict = {
        "and": [
            {
                "property": "Due date",
                "date": {"on_or_before": cutoff_iso}
            },
            {
                "property": "Due date",
                "date": {"on_or_after": now_iso}
            },
            {
                "property": "Status",
                "select": {"does_not_equal": "Done"}
            }
        ]
    }

    print(f"--- Checking for urgent tasks (within {hours} hours) ---")
    tasks = await _query_notion_with_filter(filter_dict)
    print(f"Found {len(tasks)} urgent tasks")
    return tasks


async def get_tasks_due_on(target_date: datetime) -> list[RelatedTask]:
    """Get tasks due on a specific date (Status != "Done").

    Args:
        target_date: The date to check (datetime object)

    Returns:
        List of RelatedTask objects due on target_date
    """
    eastern_tz = ZoneInfo(settings.TIMEZONE)

    # Get start and end of the target date in Eastern time
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Make timezone-aware
    start_of_day = start_of_day.replace(tzinfo=eastern_tz)
    end_of_day = end_of_day.replace(tzinfo=eastern_tz)

    start_iso = start_of_day.isoformat()
    end_iso = end_of_day.isoformat()

    # Due date is within the target date range AND status is not "Done"
    filter_dict = {
        "and": [
            {
                "property": "Due date",
                "date": {"on_or_after": start_iso}
            },
            {
                "property": "Due date",
                "date": {"on_or_before": end_iso}
            },
            {
                "property": "Status",
                "select": {"does_not_equal": "Done"}
            }
        ]
    }

    date_str = target_date.strftime("%Y-%m-%d")
    print(f"--- Checking for tasks due on {date_str} ---")
    tasks = await _query_notion_with_filter(filter_dict)
    print(f"Found {len(tasks)} tasks due on {date_str}")
    return tasks


async def get_high_priority_due_soon(days: int = 3) -> list[RelatedTask]:
    """Get high priority tasks due within N days (Status != "Done").

    Args:
        days: Number of days to look ahead (default: 3)

    Returns:
        List of high priority RelatedTask objects
    """
    eastern_tz = ZoneInfo(settings.TIMEZONE)
    now = datetime.now(eastern_tz)
    cutoff = now + timedelta(days=days)
    cutoff_iso = cutoff.isoformat()
    now_iso = now.isoformat()

    # Priority is "High" AND due within N days AND status is not "Done"
    filter_dict = {
        "and": [
            {
                "property": "Priority",
                "select": {"equals": "High"}
            },
            {
                "property": "Due date",
                "date": {"on_or_before": cutoff_iso}
            },
            {
                "property": "Due date",
                "date": {"on_or_after": now_iso}
            },
            {
                "property": "Status",
                "select": {"does_not_equal": "Done"}
            }
        ]
    }

    print(f"--- Checking for high priority tasks (within {days} days) ---")
    tasks = await _query_notion_with_filter(filter_dict)
    print(f"Found {len(tasks)} high priority tasks due soon")
    return tasks


async def get_today_tasks() -> list[RelatedTask]:
    """Get all tasks due today (Status != "Done").

    Returns:
        List of RelatedTask objects due today
    """
    eastern_tz = ZoneInfo(settings.TIMEZONE)
    today = datetime.now(eastern_tz)
    return await get_tasks_due_on(today)


async def get_tomorrow_tasks() -> list[RelatedTask]:
    """Get all tasks due tomorrow (Status != "Done").

    Returns:
        List of RelatedTask objects due tomorrow
    """
    eastern_tz = ZoneInfo(settings.TIMEZONE)
    tomorrow = datetime.now(eastern_tz) + timedelta(days=1)
    return await get_tasks_due_on(tomorrow)
