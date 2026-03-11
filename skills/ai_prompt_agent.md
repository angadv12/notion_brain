# AI & Prompt Engineering Agent Skill

## Role
AI and prompt engineering specialist for the notion_brain project.

## Expertise Areas
- Google Gemini 3 Flash API integration
- Structured output with JSON schemas
- Prompt engineering for consistent results
- Temperature tuning for model behavior
- Context injection with related tasks

## notion_brain Context

### AI Configuration
```python
model='gemini-3-flash-preview'
temperature=0.1  # Low for consistent outputs
response_mime_type='application/json'
response_schema=TaskExtraction
```

### Prompt Structure (src/services.py:44-73)

The prompt follows this structure:

1. **Role Definition**: "elite Chief of Staff"
2. **Input**: Raw task text from user
3. **Context Section**: Related tasks with due dates
4. **Critical Context**: Current date/time in US Eastern
5. **Instructions**: 8 specific outputs required

### Critical Prompt Rules

#### Priority Defaults
- Default to **"Low"** (NOT Medium) if ambiguous
- Use urgency + importance rubric

#### Due Date Handling
- Relative dates use current time as reference
- Use 23:59:00 (end of day) when no time specified
- Infer from related tasks for context-aware dates

#### Summary Guidelines
- Keep it 3-7 words
- Don't be dense in rewording
- "do dishes" → "do dishes" (not "complete dishes")

### TaskExtraction Schema
```python
class TaskExtraction(TypedDict):
    category: str           # One of 8 predefined
    priority: str           # High/Medium/Low
    due_date_iso: str | None
    summary: str
    urgency_level: int      # 1-5
    importance_level: int   # 1-5
    priority_rationale: str
```

### Category Options
```python
["Errand/Planning", "Health & Life", "University Work",
 "Extracurricular Work", "Chores", "Hobby", "Social Event",
 "Physical Activity"]
```

### Context Building Pattern
```python
context_str = "\n\n**EXISTING TASKS FOR CONTEXT:**\n"
for i, task in enumerate(context_tasks, 1):
    task_info = f"{i}. {task.title}"
    if task.due_date:
        task_info += f" (Due: {task.due_date})"
    if task.category:
        task_info += f" [{task.category}]"
    context_str += task_info + "\n"
```

### Typical Tasks
- Improve prompt for better accuracy
- Add new AI analysis features
- Fine-tune temperature and parameters
- Add structured output fields
- Improve context injection logic

### Files You'll Work With
- `src/services.py` - `analyze_task()` function (lines 26-97)
- `src/schemas.py` - TaskExtraction schema

## Prompt Engineering Tips

1. **Be Explicit**: Never assume the model knows implicit rules
2. **Use Examples**: Show desired output format in prompt
3. **Negative Examples**: Specify what NOT to do
4. **Context First**: Always inject current date/time
5. **Test Iteratively**: Small prompt changes, measure results

## Important Notes
- Timezone handling is critical - always use US Eastern
- The `$` trigger is stripped before analysis
- Relationship patterns ("after X", "before X") are detected in main.py
