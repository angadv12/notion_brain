# Notion Brain - Project Guidelines

## Project Overview

**Notion Brain** is an intelligent task management system that automates the processing of raw thoughts/tasks entered into Notion. It uses AI (Google Gemini 3 Flash) to analyze, categorize, and enrich tasks automatically through webhook integration.

### Core Value Proposition
Transform unstructured task input ("study for math test after laundry") into organized, actionable task data with:
- Intelligent categorization
- Priority assessment based on urgency/importance
- Context-aware due date inference (using related tasks)
- Automatic timezone handling (US Eastern)

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Notion    │────▶│  FastAPI     │────▶│   Gemini    │
│   Webhook   │     │  /webhook    │     │   AI Model  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                      ┌──────────────┐
                      │  Notion API  │
                      │   Update     │
                      └──────────────┘
```

### Tech Stack
- **Framework**: FastAPI + Uvicorn
- **AI**: Google Gemini 3 Flash
- **Integrations**: Notion API v2025-09-03 (data sources endpoint)
- **Data**: Pydantic for validation
- **HTTP**: httpx (async)
- **Deployment**: Docker + Railway

---

## Project Structure

```
notion_brain/
├── src/
│   ├── main.py          # FastAPI app, webhook endpoint, keyword extraction
│   ├── services.py      # AI analysis, Notion API calls (query + update)
│   └── schemas.py       # Pydantic models (NotionEvent, TaskExtraction, RelatedTask)
├── test/
│   └── test_main.py     # Webhook trigger/ignore logic tests
├── .env                 # NOTION_TOKEN, NOTION_DATA_SOURCE_ID, GEMINI_API_KEY
├── Dockerfile           # Python 3.13, non-root user, port 8080
├── requirements.txt
└── README.md            # Setup instructions with webhook config screenshots
```

---

## Critical Design Decisions

### 1. Task Trigger System
- Only tasks ending with `$` are processed
- The `$` is stripped before analysis
- **Rationale**: Explicit opt-in prevents unwanted processing of routine tasks

### 2. Context-Aware Querying
- Extracts keywords and relationship patterns ("after X", "before X")
- Queries Notion data source for related tasks
- Passes context to Gemini for better due date inference
- **Rationale**: "practice problems after math test" needs to reference the test's due date

### 3. Relationship Pattern Detection
Current patterns (main.py:34-38):
- `after <task>` → reference task is the dependency
- `before <task>` → reference task is the deadline
- `following <task>` → reference task is the predecessor

### 4. Notion API Version
- Uses `/v1/data_sources/{data_source_id}/query` (NOT database endpoint)
- **Important**: Data sources API has different capabilities than legacy database API
- No timestamp sorting supported
- `filter_properties` requires exact property names (case-sensitive)

---

## Coding Standards

### Python Style
- Use `|` for type unions: `str | None` instead of `Optional[str]`
- Prefer async/await for all I/O operations
- Keep functions focused and under 30 lines when possible

### Error Handling
- **Webhook**: Always return 200 OK, log errors, don't crash
- **Notion API**: Log errors, return empty list/False, continue processing
- **Gemini API**: Log errors, return None from `analyze_task()`

### Logging
- Use print statements for now (simple, works with Railway logs)
- Format: `"--- New Input: {clean_title} ---"`
- Key logs:
  - `"Detected '{relation}' pattern, reference task: '{task}'"`
  - `"Found {n} related tasks for query: '{query}'"`
  - `"Gemini 3 Thought: {data}"`
  - `"Notion Updated Successfully"` / `"Notion Error: {text}"`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOTION_TOKEN` | Yes | Notion integration token (Bearer auth) |
| `NOTION_DATA_SOURCE_ID` | Yes | To-do data source ID for querying tasks |
| `GEMINI_API_KEY` | Yes | Google Gemini API key for AI analysis |

---

## Notion Database Schema

The Notion to-do data source must have these properties:

| Property | Type | Used For |
|----------|------|----------|
| `Name` | title | Task title (updated with AI summary) |
| `Category` | select | Task category (8 predefined options) |
| `Priority` | select | High/Medium/Low |
| `Due date` | date | ISO 8601 with timezone |

### Category Options
```python
["Errand/Planning", "Health & Life", "University Work",
 "Extracurricular Work", "Chores", "Hobby", "Social Event", "Physical Activity"]
```

---

## Development Workflow

### 1. Making Changes
1. Read the file(s) you'll modify
2. Make your changes
3. Test locally if possible
4. Deploy (git push → Railway auto-deploys)

### 2. Testing
- Run tests: `python -m pytest test/`
- Current test coverage: Webhook trigger/ignore logic only
- **TODO**: Add tests for query_notion_tasks, relationship detection

### 3. Deployment
- Push to `main` branch
- Railway auto-deploys from Dockerfile
- Check Railway logs for errors

---

## Current Limitations & TODOs

### Known Issues
- [ ] Query only searches first keyword or single reference task (could search multiple)
- [ ] No caching of Notion queries (repeated queries hit API)
- [ ] No deduplication of similar tasks
- [ ] Limited error recovery if Notion API fails

### Future Enhancements
- [ ] Support for recurring tasks
- [ ] Task dependency tracking
- [ ] Bulk task processing
- [ ] Natural language date parsing improvements
- [ ] Multi-language support
- [ ] Task completion notifications

---

## AI Prompt Engineering Guidelines

### Gemini 3 Flash Configuration
```python
model='gemini-3-flash-preview'
temperature=0.1  # Low temperature for consistent outputs
response_mime_type='application/json'
response_schema=TaskExtraction
```

### Prompt Structure
1. **Role**: "elite Chief of Staff"
2. **Input**: Raw task text + existing tasks context
3. **Critical Context**: Current date/time in US Eastern
4. **Instructions**: Category, Priority, Due Date, Summary, Urgency, Importance, Rationale, Additional Notes

### Key Prompt Rules
- Default to "Low" priority if ambiguous (NOT Medium)
- Use 23:59:00 (end of day) when no time specified
- Don't be dense in rewording (e.g., "do dishes" → "complete dishes" is bad)
- Use context tasks to infer relative due dates

---

## Subagent Collaboration Guidelines

When working with subagents, provide:
1. **Clear context**: What we're building and why
2. **Specific task**: What needs to be done
3. **Constraints**: Tech stack, patterns, error handling
4. **Success criteria**: How to verify it works

Example brief:
> "We need to add multi-keyword search to query_notion_tasks(). The function is in src/services.py starting at line 124. Currently it only searches one keyword. We need to search the top 3 keywords and combine results. Must handle pagination and avoid duplicates. Return list[RelatedTask]."
