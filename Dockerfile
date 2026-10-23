# ---- frontend build ----
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- runtime ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    FRONTEND_DIST=/app/frontend/dist DATABASE_PATH=/data/veriscope.db STORAGE_PATH=/data/storage
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=web /web/dist /app/frontend/dist
RUN useradd --create-home app && mkdir -p /data && chown -R app /data /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
# One worker: the in-process job runner and rate limiter assume a single process (see docs/DECISIONS.md).
CMD ["sh", "-c", "if [ \"$SEED_DEMO\" = \"true\" ]; then python -m scripts.seed; fi && exec gunicorn -w 1 --threads 8 -b 0.0.0.0:8000 --access-logfile - wsgi:app"]
