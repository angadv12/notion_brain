from pydantic import BaseModel
from typing import Optional, TypedDict

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
