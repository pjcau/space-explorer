FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Keep `backend` as a real Python package so `from backend.X import Y` works
# under `uvicorn backend.main:app`.
COPY backend/ /app/backend/

# Mount point for the persisted SQLite DB (matches docker-compose volume).
RUN mkdir -p /app/data

# Startup: (1) ensure DB schema + seed (idempotent), (2) launch uvicorn.
CMD ["sh", "-c", "python -m backend.seed || true; exec uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
