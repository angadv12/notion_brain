import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Inject env vars BEFORE any src.* module is imported during collection.
# pydantic-settings reads these at Settings() instantiation time.
os.environ.setdefault("NOTION_TOKEN", "test_notion_token")
os.environ.setdefault("NOTION_DATA_SOURCE_ID", "test_ds_id_123")
os.environ.setdefault("GEMINI_API_KEY", "test_gemini_key")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACtest")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test_auth")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "+15550000001")
os.environ.setdefault("USER_PHONE_NUMBER", "+15550000002")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_tg_token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "test_chat_id")
os.environ.setdefault("NOTIFICATION_CHANNELS", "sms,telegram")

from src.schemas import RelatedTask


@pytest.fixture
def sample_task() -> RelatedTask:
    return RelatedTask(
        id="page-abc123",
        title="Study for math test",
        category="University Work",
        due_date="2026-03-15T23:59:00-04:00",
        priority="High",
        status="Not started",
    )


@pytest.fixture
def sample_ai_decision() -> dict:
    return {
        "category": "University Work",
        "priority": "High",
        "due_date_iso": "2026-03-15T23:59:00-04:00",
        "summary": "Study for math test",
        "urgency_level": 4,
        "importance_level": 5,
        "priority_rationale": "Hard deadline tomorrow.",
        "action_notes": "- Review chapter 5 formulas\n- Practice integration problems\n- Do past exam questions",
    }


@pytest.fixture
def valid_webhook_payload() -> dict:
    return {
        "data": {
            "id": "page-abc123",
            "properties": {
                "Name": {"title": [{"plain_text": "Finish report by Friday $"}]}
            },
        }
    }


@pytest.fixture
def ignored_webhook_payload() -> dict:
    return {
        "data": {
            "id": "page-abc123",
            "properties": {
                "Name": {"title": [{"plain_text": "Finish report by Friday"}]}
            },
        }
    }


@pytest.fixture
def notion_api_task_result() -> dict:
    return {
        "id": "page-abc123",
        "properties": {
            "Name": {"title": [{"plain_text": "Study for math test"}]},
            "Category": {"select": {"name": "University Work"}},
            "Due date": {"date": {"start": "2026-03-15T23:59:00-04:00"}},
            "Priority": {"select": {"name": "High"}},
            "Status": {"select": {"name": "Not started"}},
        },
    }


@pytest.fixture
def mock_notion_response(notion_api_task_result) -> dict:
    return {"results": [notion_api_task_result], "has_more": False}


@pytest.fixture
def mock_httpx_response():
    def _make(status_code: int = 200, json_data: dict = None, text: str = ""):
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = json_data or {}
        mock.text = text
        return mock
    return _make


@pytest.fixture
def make_async_client_mock(mock_httpx_response):
    def _factory(status_code: int = 200, json_data: dict = None, text: str = ""):
        resp = mock_httpx_response(status_code, json_data, text)
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.get.return_value = resp
        client.post.return_value = resp
        client.patch.return_value = resp
        client.delete.return_value = resp
        return client
    return _factory
