FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY utils ./utils

ENV DATABASE_URL=/app/db/admins.db

VOLUME ["/app/db-docker"]

EXPOSE 8000

CMD ["uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]