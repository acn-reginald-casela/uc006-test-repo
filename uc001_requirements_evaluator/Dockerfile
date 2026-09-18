# Dockerfile for the Flask API (main_flask.py) — separate from `adk deploy`,
# which packages its own image running `adk api_server` instead.
FROM python:3.11-slim
WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser
USER appuser
ENV PATH="/home/appuser/.local/bin:$PATH"

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=appuser:appuser ./ ./uc001_requirements_evaluator/

ENV GOOGLE_GENAI_USE_VERTEXAI=1

# Cloud Run injects $PORT (defaults to 8080); the pipeline can run for
# minutes, so give gunicorn workers no timeout and let Cloud Run's own
# request timeout (set at deploy time, see below) be the real limit.
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 0 uc001_requirements_evaluator.main_runner:app
