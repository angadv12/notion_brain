FROM python:3.13
WORKDIR /usr/local/app

# Prevents Python from writing .pyc files to disc (equivalent to python -B)
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr (equivalent to python -u)
ENV PYTHONUNBUFFERED=1

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create the app user
RUN useradd app

# Copy in the source code
# We map 'src' to './app' so that the module path 'app.main' works correctly
COPY --chown=app:app src ./app

EXPOSE 8080

# Switch to non-root user
USER app

# Use shell form to allow Railway to inject the $PORT environment variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
