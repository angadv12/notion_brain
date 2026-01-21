## Relations
@structure/modularity/business_logic_services.md
@structure/modularity/data_model_schemas.md

## Raw Concept
**Task:**
Implement server entry point/controller

**Changes:**
- Separation of concerns between routing and business logic

**Files:**
- main.py

**Flow:**
receive_webhook -> parse_notion_payload -> analyze_task -> update_notion_task

**Timestamp:** 2026-01-21

## Narrative
### Structure
- `main.py`: Entry point and route definitions

### Dependencies
- FastAPI for API management
- Uvicorn as the ASGI server
- `services.py` for business logic
- `schemas.py` for data models

### Features
- Acts as the server entry point and controller
- Handles POST requests to `/webhook` for Notion events
- Coordinates the flow from payload parsing to AI analysis and Notion update
