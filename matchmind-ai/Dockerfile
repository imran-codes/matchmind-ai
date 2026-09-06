FROM node:22-alpine AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080 \
    ARTIFACT_DIR=/app/artifacts STATIC_DIR=/app/static AGENT_ENABLED=false \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORKDIR /app
COPY backend/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock
COPY backend/app ./app
COPY backend/artifacts ./artifacts
COPY --from=frontend /web/dist ./static
# Fail the build if the approved artifacts cannot be loaded by this runtime.
RUN python -c "from pathlib import Path; from app.prediction import PredictionService; PredictionService(Path('artifacts'))"
RUN useradd --uid 10001 --create-home appuser
USER 10001
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --no-access-log"]
