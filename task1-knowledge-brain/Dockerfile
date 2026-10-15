FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY task1-knowledge-brain/ /app/
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings \
    sqlalchemy \
    asyncpg \
    greenlet \
    httpx \
    beautifulsoup4 \
    lxml \
    anthropic \
    pgvector \
    apscheduler \
    aiosqlite \
    pytest \
    pytest-asyncio

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
