import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Mock payload
valid_payload = {
    "data": {
        "id": "123",
        "properties": {
            "Name": {
                "title": [
                    {"plain_text": "Finish report by Friday $"}
                ]
            }
        }
    }
}

ignored_payload = {
    "data": {
        "id": "123",
        "properties": {
            "Name": {
                "title": [
                    {"plain_text": "Finish report by Friday"}
                ]
            }
        }
    }
}

@patch("services.update_notion_task", new_callable=AsyncMock)
@patch("services.analyze_task")
@patch("services.parse_notion_payload")
def test_webhook_triggers_with_dollar(mock_parse, mock_analyze, mock_update):
    # Setup mocks
    mock_parse.return_value = {"id": "123", "title": "Finish report by Friday $"}
    mock_analyze.return_value = {
        "category": "University Work",
        "priority": "High",
        "due_date_iso": "2026-01-23T17:00:00",
        "summary": "Report Friday",
        "urgency_level": 5,
        "importance_level": 4,
        "priority_rationale": "High urgency due to deadline."
    }
    
    response = client.post("/webhook", json=valid_payload)
    
    assert response.status_code == 200
    assert response.json() == {"status": "received"}
    
    # Verify analyze_task called with STRIPPED title
    mock_analyze.assert_called_once_with("Finish report by Friday")
    
    # Verify update called
    mock_update.assert_called_once()

@patch("services.update_notion_task", new_callable=AsyncMock)
@patch("services.analyze_task")
@patch("services.parse_notion_payload")
def test_webhook_ignores_without_dollar(mock_parse, mock_analyze, mock_update):
    # Setup mocks
    mock_parse.return_value = {"id": "123", "title": "Finish report by Friday"}
    
    response = client.post("/webhook", json=ignored_payload)
    
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}
    
    # Verify analyze_task NOT called
    mock_analyze.assert_not_called()
    mock_update.assert_not_called()
