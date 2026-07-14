# Stage 1: Frontend static export
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + static assets
FROM python:3.12-slim AS runtime
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY backend/pyproject.toml backend/uv.lock backend/README.md ./backend/
COPY backend/app ./backend/app
WORKDIR /app/backend
RUN uv sync --frozen --no-dev

COPY --from=frontend /frontend/out ./static

ENV DB_PATH=/app/db/finally.db
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
VOLUME ["/app/db"]

WORKDIR /app/backend
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
