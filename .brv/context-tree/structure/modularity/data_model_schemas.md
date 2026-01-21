## Relations
@structure/modularity/server_entry_point_and_controller.md
@structure/modularity/business_logic_services.md

## Raw Concept
**Task:**
Define data models and schemas

**Changes:**
- Centralized definition of data structures for type safety and validation

**Files:**
- schemas.py

**Flow:**
Used by both main.py and services.py to ensure data consistency

**Timestamp:** 2026-01-21

## Narrative
### Structure
- `schemas.py`: Data model definitions

### Dependencies
- `pydantic` for data validation
- `typing` for type hints

### Features
- `NotionEvent`: Pydantic model for incoming Notion data
- `TaskExtraction`: TypedDict for AI-generated task data
