import pytest
from pydantic import ValidationError
from src.schemas import (
    NotionEvent,
    RelatedTask,
    TaskQuery,
    NotificationConfig,
    NotificationTrigger,
)
from datetime import datetime


def test_notion_event_defaults():
    event = NotionEvent(id="x", title="y")
    assert event.priority == "Unknown"
    assert event.days_remaining == "Unknown"


def test_related_task_optional_fields():
    task = RelatedTask(id="x", title="y")
    assert task.category is None
    assert task.due_date is None
    assert task.priority is None
    assert task.status is None


def test_related_task_rejects_missing_id():
    with pytest.raises(ValidationError):
        RelatedTask(title="y")


def test_related_task_rejects_missing_title():
    with pytest.raises(ValidationError):
        RelatedTask(id="x")


def test_notification_config_defaults():
    config = NotificationConfig()
    assert config.enabled is True
    assert config.channels == ["sms"]
    assert config.quiet_hours_start == "22:00"
    assert config.quiet_hours_end == "08:00"
    assert config.timezone == "America/New_York"


def test_notification_trigger_requires_all_fields():
    with pytest.raises(ValidationError):
        NotificationTrigger(trigger_type="overdue", task_count=1, tasks=[])

    trigger = NotificationTrigger(
        trigger_type="overdue",
        task_count=1,
        tasks=[],
        triggered_at=datetime.now(),
    )
    assert trigger.trigger_type == "overdue"


def test_task_query_all_optional():
    query = TaskQuery()
    assert query.status is None
    assert query.priority is None
    assert query.due_before is None
    assert query.due_after is None
