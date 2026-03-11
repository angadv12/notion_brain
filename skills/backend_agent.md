# Backend Agent Skill

## Role
Backend development specialist for the notion_brain project.

## Expertise Areas
- FastAPI application architecture
- Async/await patterns in Python
- Service layer design and separation of concerns
- REST API endpoints and webhook handling
- Type hints with Python 3.13+ union syntax (`|` operator)
- Pydantic models for validation

## notion_brain Context

### Tech Stack
- **Framework**: FastAPI with Uvicorn server
- **Async HTTP**: httpx for all I/O operations
- **Validation**: Pydantic v2 models
- **Config**: pydantic-settings for environment management

### Key Architecture Patterns

#### Webhook Processing Flow (src/main.py)
1. Receive Notion webhook payload
2. Parse and validate with `parse_notion_payload()`
3. Check for `$` trigger suffix
4. Extract keywords/relationship patterns
5. Query related tasks via `query_notion_tasks()`
6. Analyze with Gemini via `analyze_task()`
7. Update Notion with `update_notion_task()`

#### Service Layer (src/services.py)
- All external API calls live in services
- Functions return tuples `(success, error_message)` or results
- Error handling: log and return None/empty list, never crash
- Use async/await for all httpx calls

#### Configuration (src/config.py)
- Use `pydantic_settings.BaseSettings`
- Environment variables loaded from `.env`
- Properties for computed values (e.g., `sms_enabled`)

### Code Style Guidelines
- Use `str | None` instead of `Optional[str]`
- Use `list[str]` instead of `List[str]`
- Keep functions under 30 lines when possible
- One responsibility per function
- Async functions for all I/O

### Error Handling Standards
```python
# Webhook: Always return 200, log errors
@app.post("/webhook")
async def receive_webhook(payload: dict):
    try:
        # process
        return {"status": "received"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error"}

# Services: Log and return empty/default
async def some_service_call() -> list[Task]:
    try:
        # api call
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []
```

### Typical Tasks
- Add new API endpoints
- Refactor service functions
- Implement new webhook triggers
- Add configuration options
- Improve error handling

### Files You'll Work With
- `src/main.py` - FastAPI app, webhook endpoint
- `src/services.py` - AI analysis, Notion API calls
- `src/config.py` - Configuration management
- `src/notification_service.py` - Notification delivery
- `src/task_queries.py` - Task query functions

## Important Notes
- Notion uses Data Sources API (v2025-09-03), not database API
- All timestamps must be timezone-aware (US Eastern)
- Never block the webhook - processing should be fast
- Tests use pytest, see `test/` directory
