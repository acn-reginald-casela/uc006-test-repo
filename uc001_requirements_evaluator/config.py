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

JIRA_BASE_URL   = os.environ.get("JIRA_BASE_URL","https://avclaudex2026.atlassian.net")
JIRA_EMAIL      = os.environ.get("JIRA_EMAIL","av.claudex2026@gmail.com")
JIRA_API_TOKEN  = os.environ.get("JIRA_API_TOKEN", "ATATT3xFfGF0vuSxzT2uwxAvb60XqQKPA0CPBjdQm-zD6dXCDQZXru7sE1IhwcXsai4tBux1FnPH0cjZUvkGhqpejIJu40riyz0jUFZpyDYjmBD50jffZZR0T5unmWF7R88tunnNdRu21cUF1bOoVY6qkwL7N9MBjWs-hXL5OD2fun2YH5B5XSA=9A751348")

RUBRIC_VERSION  = os.environ.get("RUBRIC_VERSION", "2026.09")

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
