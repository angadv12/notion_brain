# Feature Card: Improve Priority Ranking in Task Analysis

## Problem
- "is_urgent" boolean is too coarse and leads to most tasks being Medium/High, rarely Low.

## Goals
- Produce a realistic distribution of priorities with a clear rubric.
- Capture urgency and importance separately to support ranking and debugging.
- Keep Notion update behavior unchanged.

## Non-Goals
- Changing Notion properties or schema.
- Building a new ranking service outside the existing Gemini prompt.

## Proposed Changes
- Update `TaskExtraction` schema to replace `is_urgent` with `urgency_level`, `importance_level`, and `priority_rationale`.
- Adjust the `analyze_task` prompt to include an explicit priority rubric and default-to-low guidance.
- Keep `update_notion_task` mapping as-is (Category, Priority, Summary, Due date).

## Acceptance Criteria
- Tasks with no deadline and low impact are labeled Low.
- Tasks with immediate deadlines or high stakes are labeled High.
- JSON responses include the new fields and validate against the schema.
- No regressions in webhook flow.

## Test Plan
- Run manual samples:
  - "Maybe read a book sometime" -> Low.
  - "Submit lab report by tomorrow 5pm" -> High.
  - "Prepare slides for next week meeting" -> Medium.
