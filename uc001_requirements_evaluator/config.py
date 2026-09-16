"""
config.py — Environment settings for the UC002 Test Designer
=============================================================
Reads from environment variables (populated by .env via dotenv).
Call validate() once at startup — it exits immediately with a clear
message if required config is missing, rather than failing mid-run.

Authentication: Application Default Credentials (ADC)
  gcloud auth application-default login
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ── Required ────────────────────────────────────────────────────────────────
VERTEX_PROJECT  = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

# ── Optional (sensible defaults) ────────────────────────────────────────────
VERTEX_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

# ── Model selection ─────────────────────────────────────────────────────────
# Flash  → three parallel designers (fast, low cost)
# Pro    → analyzer + consolidator (heavier reasoning)
# Both point to Flash here; swap PRO_MODEL to "gemini-1.5-pro" for production.
FLASH_MODEL = os.environ.get("FLASH_MODEL", "gemini-3.6-flash")
PRO_MODEL   = os.environ.get("PRO_MODEL",   "gemini-3.6-flash")

# ── Policy corpus / RAG ──────────────────────────────────────────────────────
EMBEDDING_MODEL     = os.environ.get("EMBEDDING_MODEL", "text-embedding-005")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "768"))

# ── JIRA CREDENTIALS ──────────────────────────────────────────────────────
JIRA_BASE_URL   = os.environ.get("JIRA_BASE_URL","https://avclaudex2026.atlassian.net")
JIRA_EMAIL      = os.environ.get("JIRA_EMAIL","av.claudex2026@gmail.com")
JIRA_API_TOKEN  = os.environ.get("JIRA_API_TOKEN", "ATATT3xFfGF0vuSxzT2uwxAvb60XqQKPA0CPBjdQm-zD6dXCDQZXru7sE1IhwcXsai4tBux1FnPH0cjZUvkGhqpejIJu40riyz0jUFZpyDYjmBD50jffZZR0T5unmWF7R88tunnNdRu21cUF1bOoVY6qkwL7N9MBjWs-hXL5OD2fun2YH5B5XSA=9A751348")

RUBRIC_VERSION  = os.environ.get("RUBRIC_VERSION", "2026.09")

# gs://<bucket>/<prefix>/chunks.jsonl — {id, source, category, policy_version, text}
# written by uc006-vector-index/build_index.py. Loaded once into memory as a
# clause_id -> clause lookup (see services/vector_search.py).
POLICY_CHUNKS_GCS_URI = os.environ.get(
    "POLICY_CHUNKS_GCS_URI",
    "gs://atcp-cec-innov-hub-ucase-lng/UC006/chunks/chunks.jsonl",
)

# The deployed Vector Search Index Endpoint that serves find_neighbors over
# gs://atcp-cec-innov-hub-ucase-lng/UC006/embeddings/embeddings.jsonl.
# Nothing here can create this — it must be deployed first (see
# scripts/deploy_index_endpoint.py or deployment.md).
VECTOR_SEARCH_INDEX_ENDPOINT   = os.environ.get("VECTOR_SEARCH_INDEX_ENDPOINT", "")
VECTOR_SEARCH_DEPLOYED_INDEX_ID = os.environ.get("VECTOR_SEARCH_DEPLOYED_INDEX_ID", "")
VECTOR_SEARCH_NEIGHBOR_COUNT   = int(os.environ.get("VECTOR_SEARCH_NEIGHBOR_COUNT", "8"))

# ── GCP sinks ─────────────────────────────────────────────────────────────
BQ_PROJECT  = os.environ.get("BQ_PROJECT", VERTEX_PROJECT)
BQ_DATASET  = os.environ.get("BQ_DATASET", "uc006_db")
BQ_LOCATION = os.environ.get("BQ_LOCATION", VERTEX_LOCATION)
BQ_ENABLED  = os.environ.get("BQ_ENABLED", "false").strip().lower() == "true"
BQ_AUDIT_TBL = os.environ.get("BQ_AUDIT_TBL", "audit")

def validate() -> None:
    """
    Validate that all required environment variables are present.
    Exits with a human-readable error if anything is missing.
    Call this at the top of run.py before importing agents.
    """
    missing = []
    if not VERTEX_PROJECT:
        missing.append("GOOGLE_CLOUD_PROJECT")

    if missing:
        sys.exit(
            f"\n❌  Missing required environment variables: {', '.join(missing)}\n\n"
            "Fix:\n"
            "  1. Copy .env.example → .env\n"
            f"  2. Set {missing[0]}=your-project-id in .env\n"
        )
