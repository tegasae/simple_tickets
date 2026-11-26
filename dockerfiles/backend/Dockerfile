FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY utils ./utils

# Тестовая база этого релиза, НЕ рабочая база.
COPY db/admins.db /app/bootstrap/admins.db

# Рабочая БД монтируется с application-server.
ENV DATABASE_URL=/app/db/admins.db

EXPOSE 8000

CMD ["uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
