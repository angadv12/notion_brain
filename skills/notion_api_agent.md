# Notion API Agent Skill

## Role
Notion API specialist for the notion_brain project.

## Expertise Areas
- Notion Data Sources API (v2025-09-03)
- Compound filters with AND/OR logic
- Property filtering (title, select, date)
- Query optimization and pagination
- Property name case-sensitivity

## notion_brain Context

### API Version & Endpoint
- **Version**: Notion-Version: 2025-09-03
- **Endpoint**: `/v1/data_sources/{data_source_id}/query`
- **Important**: This is NOT the database API

### Authentication
```python
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2025-09-03"
}
```

### Property Types in Notion Database

| Property | Type | API Access Pattern |
|----------|------|-------------------|
| Name | title | `props.get("Name", {}).get("title", [])` |
| Category | select | `props.get("Category", {}).get("select").get("name")` |
| Priority | select | `props.get("Priority", {}).get("select").get("name")` |
| Due date | date | `props.get("Due date", {}).get("date").get("start")` |
| Status | select | `props.get("Status", {}).get("select").get("name")` |

### Compound Filter Examples

#### Overdue Tasks
```python
filter_dict = {
    "and": [
        {"property": "Due date", "date": {"before": now_iso}},
        {"property": "Status", "select": {"does_not_equal": "Done"}}
    ]
}
```

#### Urgent Tasks (within 4 hours)
```python
filter_dict = {
    "and": [
        {"property": "Due date", "date": {"on_or_before": cutoff_iso}},
        {"property": "Due date", "date": {"on_or_after": now_iso}},
        {"property": "Status", "select": {"does_not_equal": "Done"}}
    ]
}
```

#### High Priority Due Soon
```python
filter_dict = {
    "and": [
        {"property": "Priority", "select": {"equals": "High"}},
        {"property": "Due date", "date": {"on_or_before": cutoff_iso}},
        {"property": "Due date", "date": {"on_or_after": now_iso}},
        {"property": "Status", "select": {"does_not_equal": "Done"}}
    ]
}
```

### Filter Operators

#### Date Operators
- `before`: Date is before specified value
- `after`: Date is after specified value
- `on_or_before`: Date is on or before
- `on_or_after`: Date is on or after
- `equals`: Exact date match

#### Select Operators
- `equals`: Exact match
- `does_not_equal`: Not equal to
- `is_empty`: Property is empty
- `is_not_empty`: Property has value

#### Title Operators
- `contains`: Title contains substring
- `does_not_contain`: Title doesn't contain substring
- `starts_with`: Title starts with
- `ends_with`: Title ends with

### Property Extraction Pattern
```python
for result in results:
    props = result.get("properties", {})

    # Title (Name property)
    name_list = props.get("Name", {}).get("title", [])
    title = "".join([t.get("plain_text", "") for t in name_list])

    # Select property
    category_obj = props.get("Category", {}).get("select")
    category = category_obj.get("name") if category_obj else None

    # Date property
    due_date_obj = props.get("Due date", {}).get("date")
    due_date = due_date_obj.get("start") if due_date_obj else None
```

### Query Parameters
```python
params = {}
if filter_properties:
    params["filter_properties"] = filter_properties  # e.g. ["Name", "Category", "Due date"]

body = {
    "page_size": 50,
    "filter": filter_dict
}

response = await client.post(url, json=body, params=params, headers=headers)
```

### Important Limitations
1. **No timestamp sorting**: Data sources API doesn't support sorting by created/edited time
2. **Case-sensitive properties**: Property names must match exactly ("Name" not "name")
3. **Pagination required** for >100 results (use `next_cursor`)
4. **Rate limiting**: Notion has rate limits, implement backoff if needed

### Typical Tasks
- Add new query filters
- Optimize query performance
- Add new property types
- Implement pagination
- Debug filter logic
- Add sorting workarounds

### Files You'll Work With
- `src/services.py` - `query_notion_tasks()` base function
- `src/task_queries.py` - All notification-specific queries
- `src/schemas.py` - RelatedTask model

## Environment Variables
- `NOTION_TOKEN` - Integration token
- `NOTION_DATA_SOURCE_ID` - To-do data source ID

## Important Notes
- Always use async/await with httpx
- Log query results for debugging
- Return empty list on error, never crash
- Status property must exist in Notion for notifications
