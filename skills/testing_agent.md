# Testing Agent Skill

## Role
Testing specialist for the notion_brain project.

## Expertise Areas
- pytest framework
- Async function testing with pytest-asyncio
- Mocking external API calls (Notion, Gemini, Twilio)
- Test coverage and organization
- Fixture patterns

## notion_brain Context

### Current Test Structure
```
test/
└── test_main.py     # Webhook trigger/ignore logic tests
```

### Test Configuration
Requires `pytest` and `pytest-asyncio` in requirements.txt.

### Test Patterns

#### Webhook Trigger Test
```python
import pytest
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_webhook_ignores_without_dollar():
    payload = {
        "data": {
            "id": "123",
            "properties": {
                "Name": {"title": [{"plain_text": "do laundry"}]}
            }
        }
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
```

#### Async Service Test with Mock
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_query_notion_tasks():
    mock_response = {
        "results": [
            {
                "id": "page-123",
                "properties": {
                    "Name": {"title": [{"plain_text": "test task"}]},
                    "Category": {"select": {"name": "Chores"}}
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        tasks = await query_notion_tasks("test")
        assert len(tasks) == 1
        assert tasks[0].title == "test task"
```

#### Notification Service Test
```python
@pytest.mark.asyncio
async def test_send_sms():
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.status_code = 201

        result = await notification_service.send_sms("test message")
        assert result is True
```

### Test Coverage Goals

Currently covered:
- Webhook trigger/ignore logic (`$` suffix)

Needs coverage:
- `query_notion_tasks()` with various filters
- `analyze_task()` with mock Gemini response
- `update_notion_task()` success/failure
- `notification_service.send_notification()`
- `notification_service.is_quiet_hours()`
- All task query functions (`get_overdue_tasks`, etc.)
- Relationship pattern detection
- Keyword extraction

### Mock Patterns

#### Mock Gemini Response
```python
def mock_analyze_task(text, context_tasks=None):
    return {
        "category": "Chores",
        "priority": "Low",
        "due_date_iso": None,
        "summary": "do laundry",
        "urgency_level": 1,
        "importance_level": 2,
        "priority_rationale": "Low urgency, optional task"
    }

with patch("services.analyze_task", side_effect=mock_analyze_task):
    # test code
```

#### Mock Notion API
```python
with patch("httpx.AsyncClient.post") as mock_post:
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = notion_response
```

#### Mock Environment Variables
```python
import os
os.environ["NOTION_TOKEN"] = "test_token"
os.environ["NOTION_DATA_SOURCE_ID"] = "test_ds_id"
```

### Typical Tasks
- Write tests for new features
- Increase test coverage
- Mock external dependencies
- Test edge cases (empty results, errors)
- Test notification triggers
- Test quiet hours logic

### Files You'll Work With
- `test/test_main.py` - Existing tests
- `test/test_services.py` - NEW: Service layer tests
- `test/test_notification_worker.py` - NEW: Worker tests
- `test/conftest.py` - NEW: Shared fixtures

### Fixtures to Create
```python
# conftest.py
@pytest.fixture
def mock_notion_task():
    return RelatedTask(
        id="page-123",
        title="test task",
        category="Chores",
        due_date="2025-01-15",
        priority="High"
    )

@pytest.fixture
def mock_settings():
    return Settings(
        NOTION_TOKEN="test_token",
        NOTION_DATA_SOURCE_ID="test_ds_id",
        GEMINI_API_KEY="test_key"
    )
```

## Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest test/test_main.py

# Run with verbose output
pytest -v
```

## Important Notes
- Always use `@pytest.mark.asyncio` for async tests
- Mock external API calls (never hit real APIs in tests)
- Test both success and error paths
- Use fixtures for common test data
- Keep tests fast and isolated
