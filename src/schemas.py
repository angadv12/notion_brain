from pydantic import BaseModel
from typing import Optional, TypedDict, List
from datetime import datetime

class NotionEvent(BaseModel):
	id: str
	title: str
	priority: Optional[str] = "Unknown"
	days_remaining: Optional[str] = "Unknown"

class TaskExtraction(TypedDict):
    category: str
    priority: str
    due_date_iso: str | None
    summary: str
    urgency_level: int
    importance_level: int
    priority_rationale: str
    action_notes: str | None


class RelatedTask(BaseModel):
    """Represents an existing task queried from Notion for context"""
    id: str
    title: str
    category: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TaskQuery(BaseModel):
    """Query parameters for filtering tasks"""
    status: Optional[str] = None
    priority: Optional[str] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None


class NotificationTrigger(BaseModel):
    """Represents a notification trigger event"""
    trigger_type: str
    task_count: int
    tasks: list[RelatedTask]
    triggered_at: datetime


class NotificationConfig(BaseModel):
    """Configuration for notification behavior"""
    enabled: bool = True
    channels: list[str] = ["sms"]
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "08:00"
    timezone: str = "America/New_York"
