import json
import re
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services import (
    parse_notion_payload,
    analyze_task,
    update_notion_task,
    query_notion_tasks,
    write_action_notes,
    _clear_page_blocks,
    _lines_to_blocks,
)


# --- parse_notion_payload ---

def test_parse_valid_payload():
    payload = {
        "data": {
            "id": "page-abc123",
            "properties": {
                "Name": {"title": [{"plain_text": "Finish report $"}]}
            },
        }
    }
    result = parse_notion_payload(payload)
    assert result == {"id": "page-abc123", "title": "Finish report $"}


def test_parse_concatenates_rich_text_blocks():
    payload = {
        "data": {
            "id": "page-abc123",
            "properties": {
                "Name": {"title": [{"plain_text": "Finish "}, {"plain_text": "report"}]}
            },
        }
    }
    result = parse_notion_payload(payload)
    assert result["title"] == "Finish report"


def test_parse_missing_id_returns_none():
    payload = {
        "data": {
            "id": "",
            "properties": {
                "Name": {"title": [{"plain_text": "task"}]}
            },
        }
    }
    assert parse_notion_payload(payload) is None


def test_parse_empty_title_returns_none():
    payload = {
        "data": {
            "id": "page-abc123",
            "properties": {
                "Name": {"title": []}
            },
        }
    }
    assert parse_notion_payload(payload) is None


def test_parse_empty_payload_returns_none():
    assert parse_notion_payload({}) is None


def test_parse_missing_name_property_returns_none():
    payload = {"data": {"id": "page-abc123", "properties": {}}}
    assert parse_notion_payload(payload) is None


# --- analyze_task ---

@patch("src.services.client")
def test_analyze_task_returns_parsed_dict(mock_genai):
    ai_response = {
        "category": "University Work",
        "priority": "High",
        "due_date_iso": None,
        "summary": "Study for test",
        "urgency_level": 4,
        "importance_level": 5,
        "priority_rationale": "Deadline soon.",
        "action_notes": "- Review notes",
    }
    mock_genai.models.generate_content.return_value.text = json.dumps(ai_response)

    result = analyze_task("study for test")
    assert result["category"] == "University Work"
    assert result["action_notes"] == "- Review notes"


@patch("src.services.client")
def test_analyze_task_attaches_eastern_timezone(mock_genai):
    ai_response = {
        "category": "Chores",
        "priority": "Low",
        "due_date_iso": "2026-03-15T23:59:00",
        "summary": "Do dishes",
        "urgency_level": 1,
        "importance_level": 1,
        "priority_rationale": "No rush.",
        "action_notes": None,
    }
    mock_genai.models.generate_content.return_value.text = json.dumps(ai_response)

    result = analyze_task("do dishes")
    assert re.fullmatch(r"2026-03-15T23:59:00-0[45]:00", result["due_date_iso"]), \
        f"Unexpected due_date_iso: {result['due_date_iso']}"


@patch("src.services.client")
def test_analyze_task_null_due_date_passes_through(mock_genai):
    ai_response = {
        "category": "Chores",
        "priority": "Low",
        "due_date_iso": None,
        "summary": "Do stuff",
        "urgency_level": 1,
        "importance_level": 1,
        "priority_rationale": "Low impact.",
        "action_notes": None,
    }
    mock_genai.models.generate_content.return_value.text = json.dumps(ai_response)

    result = analyze_task("do stuff")
    assert result["due_date_iso"] is None


@patch("src.services.client")
def test_analyze_task_includes_context_in_prompt(mock_genai, sample_task):
    ai_response = {
        "category": "University Work",
        "priority": "Medium",
        "due_date_iso": None,
        "summary": "Practice problems",
        "urgency_level": 2,
        "importance_level": 3,
        "priority_rationale": "Not urgent.",
        "action_notes": "- Do problems",
    }
    mock_genai.models.generate_content.return_value.text = json.dumps(ai_response)

    analyze_task("practice problems", context_tasks=[sample_task])

    prompt = mock_genai.models.generate_content.call_args.kwargs["contents"]
    assert "EXISTING TASKS FOR CONTEXT" in prompt
    assert "Study for math test" in prompt


@patch("src.services.client")
def test_analyze_task_omits_context_when_no_tasks(mock_genai):
    ai_response = {
        "category": "Chores",
        "priority": "Low",
        "due_date_iso": None,
        "summary": "x",
        "urgency_level": 1,
        "importance_level": 1,
        "priority_rationale": "x",
        "action_notes": None,
    }
    mock_genai.models.generate_content.return_value.text = json.dumps(ai_response)

    analyze_task("do stuff")

    prompt = mock_genai.models.generate_content.call_args.kwargs["contents"]
    assert "EXISTING TASKS FOR CONTEXT" not in prompt


@patch("src.services.client")
def test_analyze_task_returns_none_on_exception(mock_genai):
    mock_genai.models.generate_content.side_effect = Exception("API down")
    assert analyze_task("test") is None


# --- update_notion_task ---

@pytest.mark.asyncio
async def test_update_returns_true_on_200(make_async_client_mock):
    mock_client = make_async_client_mock(200)
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await update_notion_task("page-123", {"category": "Chores", "priority": "Low"})
    assert result is True


@pytest.mark.asyncio
async def test_update_returns_false_on_error(make_async_client_mock):
    mock_client = make_async_client_mock(400, text="Bad Request")
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await update_notion_task("page-123", {"category": "Chores", "priority": "Low"})
    assert result is False


@pytest.mark.asyncio
async def test_update_payload_includes_name_when_summary_present(make_async_client_mock):
    mock_client = make_async_client_mock(200)
    with patch("httpx.AsyncClient", return_value=mock_client):
        await update_notion_task("page-123", {"category": "Chores", "priority": "Low", "summary": "Do dishes"})
    payload = mock_client.patch.call_args.kwargs["json"]
    assert payload["properties"]["Name"]["title"][0]["text"]["content"] == "Do dishes"


@pytest.mark.asyncio
async def test_update_payload_omits_name_when_no_summary(make_async_client_mock):
    mock_client = make_async_client_mock(200)
    with patch("httpx.AsyncClient", return_value=mock_client):
        await update_notion_task("page-123", {"category": "Chores", "priority": "Low"})
    payload = mock_client.patch.call_args.kwargs["json"]
    assert "Name" not in payload["properties"]


@pytest.mark.asyncio
async def test_update_payload_includes_due_date(make_async_client_mock):
    mock_client = make_async_client_mock(200)
    with patch("httpx.AsyncClient", return_value=mock_client):
        await update_notion_task("page-123", {"category": "Chores", "priority": "Low", "due_date_iso": "2026-03-15T23:59:00-04:00"})
    payload = mock_client.patch.call_args.kwargs["json"]
    assert payload["properties"]["Due date"]["date"]["start"] == "2026-03-15T23:59:00-04:00"


@pytest.mark.asyncio
async def test_update_payload_omits_due_date_when_none(make_async_client_mock):
    mock_client = make_async_client_mock(200)
    with patch("httpx.AsyncClient", return_value=mock_client):
        await update_notion_task("page-123", {"category": "Chores", "priority": "Low", "due_date_iso": None})
    payload = mock_client.patch.call_args.kwargs["json"]
    assert "Due date" not in payload["properties"]


# --- query_notion_tasks ---

@pytest.mark.asyncio
async def test_query_returns_related_tasks(make_async_client_mock, mock_notion_response):
    mock_client = make_async_client_mock(200, mock_notion_response)
    with patch("httpx.AsyncClient", return_value=mock_client):
        tasks = await query_notion_tasks(search_query="math")
    assert len(tasks) == 1
    assert tasks[0].title == "Study for math test"
    assert tasks[0].category == "University Work"


@pytest.mark.asyncio
async def test_query_builds_title_contains_filter(make_async_client_mock, mock_notion_response):
    mock_client = make_async_client_mock(200, mock_notion_response)
    with patch("httpx.AsyncClient", return_value=mock_client):
        await query_notion_tasks(search_query="math")
    body = mock_client.post.call_args.kwargs["json"]
    assert body["filter"]["property"] == "Name"
    assert body["filter"]["title"]["contains"] == "math"


@pytest.mark.asyncio
async def test_query_no_search_query_omits_filter(make_async_client_mock, mock_notion_response):
    mock_client = make_async_client_mock(200, mock_notion_response)
    with patch("httpx.AsyncClient", return_value=mock_client):
        await query_notion_tasks(search_query=None)
    body = mock_client.post.call_args.kwargs["json"]
    assert "filter" not in body


@pytest.mark.asyncio
async def test_query_returns_empty_on_api_error(make_async_client_mock):
    mock_client = make_async_client_mock(500, text="Server Error")
    with patch("httpx.AsyncClient", return_value=mock_client):
        tasks = await query_notion_tasks(search_query="math")
    assert tasks == []


@pytest.mark.asyncio
async def test_query_returns_empty_when_no_data_source_id(make_async_client_mock):
    mock_client = make_async_client_mock(200)
    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("src.services.settings") as mock_settings:
        mock_settings.NOTION_DATA_SOURCE_ID = ""
        tasks = await query_notion_tasks(search_query="math")
    assert tasks == []
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_query_handles_missing_optional_properties(make_async_client_mock):
    response = {
        "results": [{
            "id": "page-xyz",
            "properties": {
                "Name": {"title": [{"plain_text": "Minimal task"}]},
            },
        }],
        "has_more": False,
    }
    mock_client = make_async_client_mock(200, response)
    with patch("httpx.AsyncClient", return_value=mock_client):
        tasks = await query_notion_tasks(search_query="minimal")
    assert len(tasks) == 1
    assert tasks[0].title == "Minimal task"
    assert tasks[0].category is None
    assert tasks[0].due_date is None
    assert tasks[0].priority is None


# --- _lines_to_blocks ---

def test_lines_to_blocks_bullet_items():
    notes = "- Step one\n- Step two\n- Step three"
    blocks = _lines_to_blocks(notes)
    assert len(blocks) == 3
    assert all(b["type"] == "bulleted_list_item" for b in blocks)
    assert blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Step one"


def test_lines_to_blocks_asterisk_bullets():
    notes = "* Step one\n* Step two"
    blocks = _lines_to_blocks(notes)
    assert len(blocks) == 2
    assert all(b["type"] == "bulleted_list_item" for b in blocks)


def test_lines_to_blocks_plain_text_becomes_bullet():
    notes = "This is a plain note"
    blocks = _lines_to_blocks(notes)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "bulleted_list_item"


def test_lines_to_blocks_skips_empty_lines():
    notes = "- Step one\n\n- Step two\n   \n- Step three"
    blocks = _lines_to_blocks(notes)
    assert len(blocks) == 3


def test_lines_to_blocks_empty_string():
    assert _lines_to_blocks("") == []


def test_lines_to_blocks_mixed_content():
    notes = "Overview of task:\n- First step\n- Second step"
    blocks = _lines_to_blocks(notes)
    assert len(blocks) == 3
    assert all(b["type"] == "bulleted_list_item" for b in blocks)


def test_lines_to_blocks_inline_bullets():
    """Gemini sometimes returns all bullets on one line separated by ' - '"""
    notes = "Identify concepts to review first. - Gather lecture notes. - Set a timer for study. - Review core services."
    blocks = _lines_to_blocks(notes)
    assert len(blocks) == 4
    assert all(b["type"] == "bulleted_list_item" for b in blocks)
    assert blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Identify concepts to review first."


# --- _clear_page_blocks ---

@pytest.mark.asyncio
async def test_clear_page_blocks_deletes_all():
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.json.return_value = {"results": [{"id": "block-1"}, {"id": "block-2"}], "has_more": False}

    delete_response = MagicMock()
    delete_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = get_response
    mock_client.delete.return_value = delete_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        await _clear_page_blocks("page-123")

    assert mock_client.delete.call_count == 2


@pytest.mark.asyncio
async def test_clear_page_blocks_handles_get_error(make_async_client_mock):
    mock_client = make_async_client_mock(500, text="Error")
    with patch("httpx.AsyncClient", return_value=mock_client):
        await _clear_page_blocks("page-123")
    mock_client.delete.assert_not_called()


@pytest.mark.asyncio
async def test_clear_page_blocks_no_existing_blocks(make_async_client_mock):
    mock_client = make_async_client_mock(200, {"results": [], "has_more": False})
    with patch("httpx.AsyncClient", return_value=mock_client):
        await _clear_page_blocks("page-123")
    mock_client.delete.assert_not_called()


# --- write_action_notes ---

@pytest.mark.asyncio
async def test_write_action_notes_clears_and_writes(make_async_client_mock):
    mock_client = make_async_client_mock(200, {"results": [], "has_more": False})
    with patch("httpx.AsyncClient", return_value=mock_client):
        await write_action_notes("page-123", "- Step one\n- Step two")

    assert mock_client.patch.called
    payload = mock_client.patch.call_args.kwargs["json"]
    assert len(payload["children"]) == 2
    assert payload["children"][0]["type"] == "bulleted_list_item"


@pytest.mark.asyncio
async def test_write_action_notes_skips_write_for_empty_notes():
    with patch("src.services._clear_page_blocks", new_callable=AsyncMock) as mock_clear, \
         patch("httpx.AsyncClient") as mock_http:
        await write_action_notes("page-123", "")
    mock_clear.assert_called_once()
    mock_http.assert_not_called()


@pytest.mark.asyncio
async def test_write_action_notes_handles_write_error(make_async_client_mock):
    mock_client = make_async_client_mock(200, {"results": [], "has_more": False})
    error_resp = MagicMock()
    error_resp.status_code = 400
    error_resp.text = "Bad Request"
    mock_client.patch.return_value = error_resp

    with patch("httpx.AsyncClient", return_value=mock_client):
        # Should not raise
        await write_action_notes("page-123", "- Step one")


@pytest.mark.asyncio
async def test_write_action_notes_handles_list_input(make_async_client_mock):
    mock_client = make_async_client_mock(200, {"results": [], "has_more": False})
    with patch("httpx.AsyncClient", return_value=mock_client):
        await write_action_notes("page-123", ["Step one", "Step two"])

    assert mock_client.patch.called
    payload = mock_client.patch.call_args.kwargs["json"]
    assert len(payload["children"]) == 2
