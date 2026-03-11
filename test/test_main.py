from unittest.mock import AsyncMock, patch
from src.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("src.services.write_action_notes", new_callable=AsyncMock)
@patch("src.services.update_notion_task", new_callable=AsyncMock)
@patch("src.services.query_notion_tasks", new_callable=AsyncMock, return_value=[])
@patch("src.services.analyze_task")
@patch("src.services.parse_notion_payload")
def test_webhook_triggers_with_dollar(mock_parse, mock_analyze, mock_query, mock_update, mock_notes):
    mock_parse.return_value = {"id": "123", "title": "Finish report by Friday $"}
    mock_analyze.return_value = {
        "category": "University Work",
        "priority": "High",
        "due_date_iso": "2026-01-23T17:00:00",
        "summary": "Report Friday",
        "urgency_level": 5,
        "importance_level": 4,
        "priority_rationale": "High urgency due to deadline.",
        "action_notes": "- Draft outline\n- Write intro",
    }

    response = client.post("/webhook", json={"data": {"id": "123", "properties": {"Name": {"title": [{"plain_text": "Finish report by Friday $"}]}}}})

    assert response.status_code == 200
    assert response.json() == {"status": "received"}
    mock_analyze.assert_called_once()
    assert mock_analyze.call_args[0][0] == "Finish report by Friday"
    mock_update.assert_called_once()
    mock_notes.assert_called_once_with("123", "- Draft outline\n- Write intro")


@patch("src.services.write_action_notes", new_callable=AsyncMock)
@patch("src.services.update_notion_task", new_callable=AsyncMock)
@patch("src.services.query_notion_tasks", new_callable=AsyncMock, return_value=[])
@patch("src.services.analyze_task")
@patch("src.services.parse_notion_payload")
def test_webhook_ignores_without_dollar(mock_parse, mock_analyze, mock_query, mock_update, mock_notes):
    mock_parse.return_value = {"id": "123", "title": "Finish report by Friday"}

    response = client.post("/webhook", json={"data": {"id": "123", "properties": {"Name": {"title": [{"plain_text": "Finish report by Friday"}]}}}})

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}
    mock_analyze.assert_not_called()
    mock_update.assert_not_called()
    mock_notes.assert_not_called()


@patch("src.services.write_action_notes", new_callable=AsyncMock)
@patch("src.services.update_notion_task", new_callable=AsyncMock)
@patch("src.services.query_notion_tasks", new_callable=AsyncMock, return_value=[])
@patch("src.services.analyze_task")
@patch("src.services.parse_notion_payload")
def test_webhook_ignores_when_parse_returns_none(mock_parse, mock_analyze, mock_query, mock_update, mock_notes):
    mock_parse.return_value = None

    response = client.post("/webhook", json={})

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}
    mock_analyze.assert_not_called()


@patch("src.services.write_action_notes", new_callable=AsyncMock)
@patch("src.services.update_notion_task", new_callable=AsyncMock)
@patch("src.services.query_notion_tasks", new_callable=AsyncMock, return_value=[])
@patch("src.services.analyze_task")
@patch("src.services.parse_notion_payload")
def test_webhook_skips_update_when_ai_returns_none(mock_parse, mock_analyze, mock_query, mock_update, mock_notes):
    mock_parse.return_value = {"id": "123", "title": "do stuff $"}
    mock_analyze.return_value = None

    response = client.post("/webhook", json={"data": {"id": "123", "properties": {"Name": {"title": [{"plain_text": "do stuff $"}]}}}})

    assert response.status_code == 200
    assert response.json() == {"status": "received"}
    mock_update.assert_not_called()
    mock_notes.assert_not_called()


@patch("src.services.write_action_notes", new_callable=AsyncMock)
@patch("src.services.update_notion_task", new_callable=AsyncMock)
@patch("src.services.query_notion_tasks", new_callable=AsyncMock, return_value=[])
@patch("src.services.analyze_task")
@patch("src.services.parse_notion_payload")
def test_webhook_skips_notes_when_action_notes_empty(mock_parse, mock_analyze, mock_query, mock_update, mock_notes):
    mock_parse.return_value = {"id": "123", "title": "do stuff $"}
    mock_analyze.return_value = {
        "category": "Chores",
        "priority": "Low",
        "due_date_iso": None,
        "summary": "Do stuff",
        "urgency_level": 1,
        "importance_level": 1,
        "priority_rationale": "No deadline.",
        "action_notes": None,
    }

    response = client.post("/webhook", json={"data": {"id": "123", "properties": {"Name": {"title": [{"plain_text": "do stuff $"}]}}}})

    assert response.status_code == 200
    mock_update.assert_called_once()
    mock_notes.assert_not_called()


@patch("src.services.write_action_notes", new_callable=AsyncMock)
@patch("src.services.update_notion_task", new_callable=AsyncMock)
@patch("src.services.query_notion_tasks", new_callable=AsyncMock, return_value=[])
@patch("src.services.analyze_task", return_value={"category": "Chores", "priority": "Low", "due_date_iso": None, "summary": "x", "urgency_level": 1, "importance_level": 1, "priority_rationale": "x", "action_notes": None})
@patch("src.services.parse_notion_payload")
def test_webhook_relationship_pattern_after(mock_parse, mock_analyze, mock_query, mock_update, mock_notes):
    mock_parse.return_value = {"id": "123", "title": "study after laundry $"}

    client.post("/webhook", json={"data": {"id": "123", "properties": {"Name": {"title": [{"plain_text": "study after laundry $"}]}}}})

    mock_query.assert_called_once()
    assert mock_query.call_args.kwargs["search_query"] == "laundry"


@patch("src.services.write_action_notes", new_callable=AsyncMock)
@patch("src.services.update_notion_task", new_callable=AsyncMock)
@patch("src.services.query_notion_tasks", new_callable=AsyncMock, return_value=[])
@patch("src.services.analyze_task", return_value={"category": "Chores", "priority": "Low", "due_date_iso": None, "summary": "x", "urgency_level": 1, "importance_level": 1, "priority_rationale": "x", "action_notes": None})
@patch("src.services.parse_notion_payload")
def test_webhook_relationship_pattern_before(mock_parse, mock_analyze, mock_query, mock_update, mock_notes):
    mock_parse.return_value = {"id": "123", "title": "submit assignment before class $"}

    client.post("/webhook", json={"data": {"id": "123", "properties": {"Name": {"title": [{"plain_text": "submit assignment before class $"}]}}}})

    mock_query.assert_called_once()
    assert mock_query.call_args.kwargs["search_query"] == "class"


@patch("src.services.write_action_notes", new_callable=AsyncMock)
@patch("src.services.update_notion_task", new_callable=AsyncMock)
@patch("src.services.query_notion_tasks", new_callable=AsyncMock, return_value=[])
@patch("src.services.analyze_task", return_value={"category": "Chores", "priority": "Low", "due_date_iso": None, "summary": "x", "urgency_level": 1, "importance_level": 1, "priority_rationale": "x", "action_notes": None})
@patch("src.services.parse_notion_payload")
def test_webhook_keyword_fallback_skips_stop_words(mock_parse, mock_analyze, mock_query, mock_update, mock_notes):
    mock_parse.return_value = {"id": "123", "title": "do the dishes $"}

    client.post("/webhook", json={"data": {"id": "123", "properties": {"Name": {"title": [{"plain_text": "do the dishes $"}]}}}})

    mock_query.assert_called_once()
    assert mock_query.call_args.kwargs["search_query"] == "dishes"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Server is running..."}
