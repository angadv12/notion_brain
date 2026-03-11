import httpx
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai
from google.genai import types
import typing_extensions as typing

from src.config import settings
from src.schemas import TaskExtraction, RelatedTask

headers = {
    "Authorization": f"Bearer {settings.NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2025-09-03"
}

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def analyze_task(text: str, context_tasks: list[RelatedTask] | None = None) -> TaskExtraction:
	eastern_tz = ZoneInfo("America/New_York")
	now = datetime.now(eastern_tz)
	current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
	day_of_week = now.strftime("%A")

	# Build context string from existing tasks
	context_str = ""
	if context_tasks:
		context_str = "\n\n**EXISTING TASKS FOR CONTEXT:**\n"
		for i, task in enumerate(context_tasks, 1):
			task_info = f"{i}. {task.title}"
			if task.due_date:
				task_info += f" (Due: {task.due_date})"
			if task.category:
				task_info += f" [{task.category}]"
			context_str += task_info + "\n"

	prompt = f"""
	You are an elite Chief of Staff. Analyze this raw thought from your boss:
	"{text}"{context_str}

	**CRITICAL CONTEXT:**
	- Current Date/Time: {current_time_str} ({day_of_week})
	- Timezone: US Eastern Time (New York)

	**INSTRUCTIONS:**
	1. **Category**: Pick one of ["Errand/Planning", "Health & Life", "University Work", "Extracurricular Work", "Chores",
		   		"Hobby", "Social Event", "Physical Activity"].
	2. **Priority**: Pick one of ["High", "Medium", "Low"] using this rubric.
	   - High: hard deadline within a day or slightly more, serious consequences, or blocks others.
	   - Medium: deadline within a week, or important but not time-critical.
	   - Low: either no deadline, optional "someday" tasks, or seem low impact.
	   - If ambiguous or no deadline, default to Low (not Medium).
	3. **Due Date**: Extract the absolute ISO 8601 date/time (YYYY-MM-DDTHH:MM:SS).
	   - Assume "tomorrow" is relative to the current date.
	   - If a time is mentioned (e.g., "at 5pm"), include it.
	   - If NO time is mentioned, default to 23:59:00 (End of Day).
	   - Return null if no date is found.
	   - **IMPORTANT**: Use the existing tasks listed above as context. If the new task references or relates to an existing task
	     (e.g., "do practice problems after math test" when "study for math test" exists), use the related task's due date to
	     infer an appropriate due date for the new task.
	4. **Summary**: A crisp 3-7 word title for the task.
	5. **Urgency Level**: Integer 1-5 (1 = not time-sensitive, 5 = immediate/overdue).
	6. **Importance Level**: Integer 1-5 (1 = low impact, 5 = high impact).
	7. **Priority Rationale** (internal reasoning only — not shown to user): One sentence tying urgency, importance, and timeframe to the priority. This helps you decide the priority, it is not displayed.
	8. **Action Notes**: Write 3-10 concise, actionable bullet lines of guidance to help accomplish this task.
	   - Format every line starting with "- ".
	   - Be practical and specific to THIS task, not generic productivity advice.
	   - Don't be dense in your rewording. Example: If the task is "do the dishes", write steps to do the dishes, not "complete the dishes task".
    """

	try:
		response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=TaskExtraction,
                temperature=0.1
            )
        )

		data = json.loads(response.text)

		if data.get("due_date_iso"):
			naive_dt = datetime.fromisoformat(data["due_date_iso"])
			aware_dt = naive_dt.replace(tzinfo=eastern_tz)
			data["due_date_iso"] = aware_dt.isoformat()

		print(f"Gemini 3 Thought: {data}")
		return data
	except Exception as e:
		print(f"AI Error: {e}")
		return None


async def update_notion_task(page_id: str, data: dict) -> bool:
	url = f"https://api.notion.com/v1/pages/{page_id}"
	properties = {
		"Category": { "select": {"name": data.get("category", "Chores") } },
		"Priority": { "select": {"name": data.get("priority", "Medium") } },
	}
	if data.get("summary"):
		properties["Name"] = { "title": [{ "text": { "content": data['summary'] } }] }

	if data.get("due_date_iso"):
		properties["Due date"] = {
			"date": { "start": data["due_date_iso"] }
		}

	payload = { "properties": properties }

	async with httpx.AsyncClient() as http_client:
		response = await http_client.patch(url, json=payload, headers=headers)
		if response.status_code != 200:
			print(f"Notion Error: {response.text}")
		else:
			print("Notion Updated Successfully")
		return (response.status_code == 200)


async def query_notion_tasks(
	search_query: str | None = None,
	filter_properties: list[str] | None = None,
	page_size: int = 50
) -> list[RelatedTask]:
	"""
	Query the Notion data source for existing tasks.

	Args:
		search_query: Optional text to search for in task titles
		filter_properties: List of properties to include in response (e.g., ["title", "category", "Due date"])
		page_size: Maximum number of results to return (default: 50)

	Returns:
		List of RelatedTask objects representing existing tasks
	"""
	if not settings.NOTION_DATA_SOURCE_ID:
		print("Warning: NOTION_DATA_SOURCE_ID not set, skipping task query")
		return []

	url = f"https://api.notion.com/v1/data_sources/{settings.NOTION_DATA_SOURCE_ID}/query"

	# Build query parameters for filtering properties
	params = {}
	if filter_properties:
		params["filter_properties"] = filter_properties

	# Build the request body
	body = {"page_size": page_size}

	# If a search query is provided, use the title contains filter
	if search_query:
		body["filter"] = {
			"property": "Name",
			"title": {"contains": search_query}
		}

	# Note: Data sources API doesn't support timestamp sorting, so we skip sort
	# Results will be returned in default order

	async with httpx.AsyncClient() as http_client:
		try:
			response = await http_client.post(url, json=body, params=params, headers=headers)
			if response.status_code != 200:
				print(f"Notion Query Error: {response.text}")
				return []

			data = response.json()
			results = data.get("results", [])

			tasks = []
			for result in results:
				# Extract task properties
				props = result.get("properties", {})

				# Extract title (Name property)
				name_list = props.get("Name", {}).get("title", [])
				title = "".join([t.get("plain_text", "") for t in name_list])

				# Extract category (select property)
				category_obj = props.get("Category", {}).get("select")
				category = category_obj.get("name") if category_obj else None

				# Extract due date (date property)
				due_date_obj = props.get("Due date", {}).get("date")
				due_date = due_date_obj.get("start") if due_date_obj else None

				# Extract priority (select property)
				priority_obj = props.get("Priority", {}).get("select")
				priority = priority_obj.get("name") if priority_obj else None

				# Extract status (select property)
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

			print(f"Found {len(tasks)} related tasks for query: '{search_query}'")
			return tasks

		except Exception as e:
			print(f"Error querying Notion: {e}")
			return []


# normalization layer - cleans notion payload JSON
def parse_notion_payload(payload: dict):
	try:
		data = payload.get("data", {})
		page_id = data.get('id', "")

		props = data.get('properties', {})
		name_list = props.get("Name", {}).get("title", [])
		raw_text = "".join([t.get("plain_text", "") for t in name_list])

		if not page_id or not raw_text:
			return None

		return {'id': page_id, "title": raw_text}
	except Exception as e:
		print(f"Error parsing: {e}")
		return None


def _normalize_notes(notes: str) -> list[str]:
	import re
	lines = notes.splitlines()
	# If Gemini returned everything on one line, split on inline bullet patterns
	if len(lines) <= 1 and notes.strip():
		parts = re.split(r'\s*(?:^|\s)-\s', notes.strip())
		return [p.strip() for p in parts if p.strip()]
	return [l.strip() for l in lines if l.strip()]


def _lines_to_blocks(notes: str) -> list[dict]:
	blocks = []
	for line in _normalize_notes(notes):
		if line.startswith("- ") or line.startswith("* "):
			block_type = "bulleted_list_item"
			content = line[2:]
		else:
			block_type = "bulleted_list_item"
			content = line
		blocks.append({
			"object": "block",
			"type": block_type,
			block_type: {"rich_text": [{"type": "text", "text": {"content": content}}]}
		})
	return blocks


async def _clear_page_blocks(page_id: str) -> None:
	url = f"https://api.notion.com/v1/blocks/{page_id}/children"
	try:
		async with httpx.AsyncClient() as http_client:
			block_ids = []
			cursor = None
			while True:
				params = {"start_cursor": cursor} if cursor else {}
				response = await http_client.get(url, headers=headers, params=params)
				if response.status_code != 200:
					print(f"Notion Block Fetch Error: {response.text}")
					return
				data = response.json()
				block_ids += [b["id"] for b in data.get("results", [])]
				if not data.get("has_more"):
					break
				cursor = data.get("next_cursor")
			for block_id in block_ids:
				del_resp = await http_client.delete(
					f"https://api.notion.com/v1/blocks/{block_id}", headers=headers
				)
				if del_resp.status_code not in (200, 404):
					print(f"Notion Block Delete Error ({block_id}): {del_resp.text}")
			print(f"Cleared {len(block_ids)} existing blocks")
	except Exception as e:
		print(f"Clear Blocks Error: {e}")


async def write_action_notes(page_id: str, notes: str) -> None:
	try:
		if isinstance(notes, list):
			notes = "\n".join(notes)
		await _clear_page_blocks(page_id)
		blocks = _lines_to_blocks(notes)
		if not blocks:
			return
		url = f"https://api.notion.com/v1/blocks/{page_id}/children"
		async with httpx.AsyncClient() as http_client:
			response = await http_client.patch(url, json={"children": blocks}, headers=headers)
			if response.status_code != 200:
				print(f"Notion Block Write Error: {response.text}")
			else:
				print("Action notes written to page body")
	except Exception as e:
		print(f"Action Notes Error: {e}")
