from fastapi import FastAPI
import uvicorn
from src.schemas import NotionEvent
import src.services as services
import re

app = FastAPI()
	
# NOTION WEBHOOK LISTENER
@app.post("/webhook")
async def receive_webhook(payload: dict):
	raw_data = services.parse_notion_payload(payload)
	if not raw_data:
		return {"status": "ignored"}
	
	event = NotionEvent(**raw_data)

	if not event.title.strip().endswith("$"):
		return {"status": "ignored"}

	clean_title = event.title.strip().rstrip("$").strip()

	print(f"\n--- New Input: {clean_title} ---")

	# Extract keywords from the title to find related tasks
	# Remove common stop words and extract meaningful terms
	# Note: "after" and "before" are NOT in stop_words - they are used for relationship detection
	stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by"}
	words = re.findall(r'\b\w+\b', clean_title.lower())
	keywords = [w for w in words if w not in stop_words and len(w) > 2]

	# Extract reference task from relationship patterns
	reference_task = None
	patterns = [
		(r'\bafter\s+(\w+)', 'after'),      # "after laundry"
		(r'\bbefore\s+(\w+)', 'before'),    # "before class"
		(r'\bfollowing\s+(\w+)', 'following'),  # "following finals"
	]

	for pattern, relation in patterns:
		match = re.search(pattern, clean_title.lower())
		if match:
			reference_task = match.group(1)
			print(f"Detected '{relation}' pattern, reference task: '{reference_task}'")
			break

	# If reference task found, use it; otherwise fall back to keyword extraction
	search_query = reference_task if reference_task else (keywords[0] if keywords else None)
	context_tasks = []
	if search_query:
		context_tasks = await services.query_notion_tasks(
			search_query=search_query,
			filter_properties=["Name", "Category", "Due date", "Priority", "Status"],
			page_size=10
		)

	ai_decision = services.analyze_task(clean_title, context_tasks=context_tasks)

	if ai_decision:
		await services.update_notion_task(event.id, ai_decision)
		if ai_decision.get("action_notes"):
			await services.write_action_notes(event.id, ai_decision["action_notes"])

	return {"status": "received"}	

@app.get("/")
async def root():
	return {"message": "Server is running..."}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)