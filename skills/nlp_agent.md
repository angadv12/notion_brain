# NLP Agent Skill

## Role
Natural Language Processing specialist for the notion_brain project.

## Expertise Areas
- Regex pattern matching for relationship extraction
- Keyword extraction with stop word filtering
- Text preprocessing and normalization
- Relationship pattern detection ("after X", "before X")
- Trigger character detection

## notion_brain Context

### NLP Pipeline (src/main.py)

The webhook processing uses several NLP techniques:

#### 1. Trigger Detection
```python
if not event.title.strip().endswith("$"):
    return {"status": "ignored"}

clean_title = event.title.strip().rstrip("$").strip()
```

Tasks ending with `$` are processed. The `$` is stripped before analysis.

#### 2. Keyword Extraction
```python
stop_words = {"the", "a", "an", "and", "or", "but", "in", "on",
              "at", "to", "for", "with", "by"}
words = re.findall(r'\b\w+\b', clean_title.lower())
keywords = [w for w in words if w not in stop_words and len(w) > 2]
```

**Important**: "after" and "before" are NOT in stop_words because they're used for relationship detection.

#### 3. Relationship Pattern Detection
```python
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
```

#### 4. Query Selection
```python
# If reference task found, use it; otherwise fall back to keyword extraction
search_query = reference_task if reference_task else (keywords[0] if keywords else None)
```

### Relationship Pattern Semantics

| Pattern | Meaning | Reference Task Role |
|---------|---------|---------------------|
| `after <task>` | New task happens after reference | Reference is dependency |
| `before <task>` | New task happens before reference | Reference is deadline |
| `following <task>` | New task follows reference | Reference is predecessor |

### Regex Patterns Used

#### Word Boundary Matching
```python
r'\b\w+\b'  # Matches whole words
```

#### Relationship Patterns
```python
r'\bafter\s+(\w+)'      # "after" followed by word
r'\bbefore\s+(\w+)'     # "before" followed by word
r'\bfollowing\s+(\w+)'  # "following" followed by word
```

### Stop Words List
```python
stop_words = {
    "the", "a", "an", "and", "or", "but",
    "in", "on", "at", "to", "for", "with", "by"
}
```

**Excluded from stop words**: "after", "before", "following" (used for patterns)

### Typical Tasks
- Add new relationship patterns
- Improve keyword extraction
- Handle edge cases in text
- Add temporal expressions
- Improve pattern matching accuracy
- Multi-language support

### Files You'll Work With
- `src/main.py` - Pattern detection (lines 25-48)

### Pattern Ideas to Add

#### Temporal Expressions
```python
patterns = [
    (r'\bin\s+(\d+)\s+(hour|hours|day|days)', 'in'),  # "in 2 hours"
    (r'\btomorrow\b', 'tomorrow'),                     # "tomorrow"
    (r'\bnext\s+(week|month)\b', 'next'),              # "next week"
]
```

#### Dependency Indicators
```python
patterns = [
    (r'\bdepends\s+on\s+(\w+)', 'depends'),  # "depends on meeting"
    (r'\bwaiting\s+for\s+(\w+)', 'waiting'),  # "waiting for approval"
]
```

#### Priority Indicators
```python
patterns = [
    (r'\burgent\b', 'urgent'),           # "urgent task"
    (r'\basap\b', 'asap'),               # "do this asap"
    (r'\bhigh\s+priority\b', 'high'),    # "high priority item"
]
```

### Testing NLP Patterns

Create test cases in `test/test_nlp.py`:

```python
import re

def test_after_pattern():
    text = "do homework after dinner"
    match = re.search(r'\bafter\s+(\w+)', text.lower())
    assert match.group(1) == "dinner"

def test_stop_words():
    text = "do the dishes and clean the kitchen"
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    assert "dishes" in keywords
    assert "kitchen" in keywords
    assert "the" not in keywords
    assert "and" not in keywords
```

### Edge Cases to Handle

1. **Punctuation**: "after work," vs "after work"
2. **Multiple patterns**: "after lunch before dinner"
3. **Case sensitivity**: Always use `.lower()`
4. **Short words**: Filter `len(w) > 2`
5. **Numbers**: Keep them for dates/times
6. **Special characters**: Strip `$` trigger before processing

### NLP Improvement Ideas

1. **Multi-keyword search**: Currently only uses first keyword
2. **Fuzzy matching**: Handle typos in task names
3. **Synonym detection**: "assignment" ≈ "homework"
4. **Date extraction**: "on Friday" → date
5. **Duration extraction**: "for 2 hours"
6. **Priority extraction**: "urgent", "important", "critical"

## Important Notes
- NLP happens before AI analysis
- Results are used to query Notion for context
- Context is passed to Gemini for better due date inference
- Patterns are case-insensitive (convert to lower)
- "after" and "before" have semantic meaning beyond just search terms
