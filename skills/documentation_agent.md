# Documentation Agent Skill

## Role
Documentation specialist for the notion_brain project.

## Expertise Areas
- Markdown documentation
- CLAUDE.md project instructions
- README.md maintenance
- API documentation
- Code comments and docstrings

## notion_brain Context

### Key Documentation Files

#### CLAUDE.md
This is the most important file - it contains:
- Project overview and value proposition
- Architecture diagram
- Project structure
- Critical design decisions
- Coding standards
- Environment variables reference
- Notion database schema

**Location**: `/Users/angadbrar/Desktop/notion_brain/CLAUDE.md`

#### README.md
User-facing documentation with:
- Setup instructions
- Environment variable configuration
- Webhook setup guide with screenshots
- Running the application
- Deployment instructions

#### Code Docstrings
Use Google-style docstrings:
```python
async def query_notion_tasks(
    search_query: str | None = None,
    filter_properties: list[str] | None = None,
    page_size: int = 50
) -> list[RelatedTask]:
    """Query the Notion data source for existing tasks.

    Args:
        search_query: Optional text to search for in task titles
        filter_properties: List of properties to include in response
        page_size: Maximum number of results to return

    Returns:
        List of RelatedTask objects representing existing tasks
    """
```

### Documentation Standards

#### CLAUDE.md Structure
1. **Project Overview**: What and why
2. **Architecture**: System diagram with ASCII art
3. **Tech Stack**: Framework, AI, integrations
4. **Project Structure**: File tree with descriptions
5. **Critical Design Decisions**: Rationale for key choices
6. **Coding Standards**: Style guide, error handling, logging
7. **Environment Variables**: Table of all env vars
8. **Notion Database Schema**: Property types and options
9. **Development Workflow**: How to make changes
10. **Current Limitations & TODOs**: Known issues
11. **AI Prompt Engineering Guidelines**: Prompt structure
12. **Subagent Collaboration Guidelines**: How to work with agents

#### README.md Structure
1. **Title and description**
2. **Features**: Bullet points of capabilities
3. **Prerequisites**: What you need before starting
4. **Setup**: Step-by-step installation
5. **Environment Variables**: Copy-paste template
6. **Notion Setup**: Database properties, webhook config
7. **Running the app**: Local and Docker
8. **Deployment**: Railway configuration
9. **Testing**: How to run tests
10. **Screenshots**: Webhook setup visual guide

### Markdown Patterns

#### Code Blocks with Language
````markdown
```python
def example():
    pass
```
````

#### Tables for Configuration
```markdown
| Variable | Required | Description |
|----------|----------|-------------|
| NOTION_TOKEN | Yes | Notion integration token |
```

#### ASCII Diagrams
```markdown
┌─────────────┐     ┌──────────────┐
│   Notion    │────▶│  FastAPI     │
└─────────────┘     └──────────────┘
```

### Typical Tasks
- Update CLAUDE.md after adding features
- Write API endpoint documentation
- Add inline code comments for complex logic
- Create troubleshooting guides
- Document new environment variables
- Update architecture diagrams
- Write setup guides for new features

### Files You'll Work With
- `CLAUDE.md` - Project instructions (auto-loaded into system prompt)
- `README.md` - User-facing documentation
- `skills/*.md` - Agent skill definitions
- Inline comments in `src/` files

### Writing Guidelines

#### CLAUDE.md Best Practices
- Keep lines after 200 concise (may be truncated)
- Link to other memory files for details
- Use code block examples for patterns
- Document rationale, not just what
- Include current limitations and TODOs

#### Code Comments
```python
# BAD - obvious comment
x = x + 1  # increment x

# GOOD - explains why
# Use end of day (23:59:00) when no time specified
default_time = "23:59:00"
```

#### Docstrings
- Every public function needs a docstring
- Include Args/Returns/Raises sections
- Keep it concise but informative

## Important Notes
- CLAUDE.md is loaded into system prompt automatically
- Lines after 200 may be truncated
- Link to external docs for detailed info
- Keep README.md user-friendly, not just technical
