# DevOps Agent Skill

## Role
DevOps specialist for the notion_brain project.

## Expertise Areas
- Docker containerization
- Railway deployment and configuration
- Environment variable management
- Cron job scheduling for workers
- Multi-service architecture

## notion_brain Context

### Architecture
Two services running on Railway:

1. **Webhook Service** (main)
   - FastAPI app listening for Notion webhooks
   - Processes tasks with Gemini AI
   - Updates Notion with enriched data

2. **Worker Service** (notifications)
   - Background jobs for task check-ins
   - Sends SMS/Telegram notifications
   - Runs on scheduled intervals

### Docker Configuration

#### Main Service (Dockerfile)
```dockerfile
FROM python:3.13
WORKDIR /usr/local/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -m app
COPY --chown=app:app src/ .
USER app
EXPOSE 8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}'"]
```

#### Worker Service (Dockerfile.worker)
```dockerfile
FROM python:3.13
WORKDIR /usr/local/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -m app
COPY --chown=app:app src/ worker/ .
USER app
CMD ["sh", "-c", "python -m worker.main ${TRIGGER_TYPE:-today}"]
```

### Railway Configuration

#### railway.json
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "sh -c 'uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}'",
    "healthcheckPath": "/"
  }
}
```

### Railway Cron Jobs for Worker

Configure in Railway dashboard for worker service:

| Job Name | Schedule | Command | Description |
|----------|----------|---------|-------------|
| overdue_check | Hourly | `TRIGGER_TYPE=overdue` | Check overdue tasks |
| urgent_check | Hourly | `TRIGGER_TYPE=urgent` | Check tasks due within 4 hours |
| today_digest | 9 AM EST | `TRIGGER_TYPE=today` | Daily digest of today's tasks |
| tomorrow_digest | 8 PM EST | `TRIGGER_TYPE=tomorrow` | Preview of tomorrow's tasks |
| high_priority_check | Noon EST | `TRIGGER_TYPE=high_priority` | High priority due soon |

### Environment Variables

#### Required Variables (Both Services)
```bash
NOTION_TOKEN=your_notion_token
NOTION_DATA_SOURCE_ID=your_data_source_id
GEMINI_API_KEY=your_gemini_key
```

#### Notification Variables (Worker Only)
```bash
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+0987654321
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

#### Behavior Variables (Worker Only)
```bash
NOTIFICATION_ENABLED=true
QUIET_HOURS_ENABLED=true
QUIET_HOURS_START=22:00
QUIET_HOURS_END=08:00
TIMEZONE=America/New_York
NOTIFICATION_CHANNELS=sms,telegram
```

### Railway Service Setup

1. **Create Main Service**
   - Connect GitHub repo
   - Set root directory to `/`
   - Use `Dockerfile`
   - Add environment variables
   - Deploy

2. **Create Worker Service**
   - From Railway project, click "New Service"
   - Select "Empty Service"
   - Set root directory to `/`
   - Use `Dockerfile.worker`
   - Add environment variables
   - Set up cron jobs
   - Deploy

### Health Checks

#### Main Service
```python
@app.get("/")
async def root():
    return {"message": "Server is running..."}
```

Health check path: `/`

#### Worker Service
Worker exits after each run. Railway restarts it based on cron schedule.

### Logs & Monitoring

**Viewing Logs:**
```bash
# Railway CLI
railway logs

# Or use Railway dashboard
```

**Key Log Messages:**
```
--- New Input: {task_title} ---
Detected '{relation}' pattern, reference task: '{task}'
Found {n} related tasks for query: '{query}'
Gemini 3 Thought: {data}
Notion Updated Successfully
Notification Worker: {trigger_type}
```

### Deployment Workflow

1. Push to `main` branch
2. Railway auto-deploys both services
3. Check logs for errors
4. Test webhook with sample task
5. Test worker with manual trigger

### Typical Tasks
- Set up Railway services
- Configure cron jobs
- Add new environment variables
- Debug deployment issues
- Optimize Docker images
- Set up monitoring/alerts
- Handle Railway-specific issues

### Files You'll Work With
- `Dockerfile` - Main service container
- `Dockerfile.worker` - Worker service container
- `railway.json` - Railway configuration
- `requirements.txt` - Python dependencies
- `.env` - Local environment variables (not in git)

### Common Issues

#### Port Already in Use
Railway assigns PORT dynamically. Use `${PORT:-8080}` in CMD.

#### Worker Not Running
Check TRIGGER_TYPE environment variable in cron configuration.

#### Import Errors in Worker
Worker uses `sys.path.insert(0, "/usr/local/app/src")` for imports.

#### Memory Issues
Railway free tier has limits. Consider:
- Reducing page_size in queries
- Increasing Railway plan
- Adding request timeouts

## Important Notes
- Never commit `.env` to git
- Use Railway's variable secrets for sensitive data
- Worker runs as non-root `app` user
- Both services use same codebase (src/)
- Logs are essential for debugging
