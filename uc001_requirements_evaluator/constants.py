"""
constants.py — Shared constants for the UC002 pipeline
=======================================================
Single source of truth for:
  - State keys  (keys written to / read from session.state)
  - JSON schemas (the contracts agents must follow)
  - Sample data  (used in run.py and tests)

Why constants instead of inline strings?
─────────────────────────────────────────
If you rename a state key in one agent but forget to update another,
the pipeline silently breaks — the downstream agent reads an empty string.
With StateKey.CRITERIA everywhere, a rename is a one-line change here,
and the wrong name causes a NameError, not a silent failure.
"""

PROJECT_ID = "jvtxdzs-atcp-cec-innov-hub"
LOCATION = "us-central1"
APP_NAME = "projects/261202843504/locations/us-central1/reasoningEngines/8662688726654124032"
BUCKET_NAME = "uc004"
DATASET = "uc004"
USER_ID = "api-account"
APPROVAL_SCORE_THRESHOLD = 8
RUBRIC_TABLE = "rubric"

# ── Session state keys ───────────────────────────────────────────────────────

class StateKey:
#     """Keys for session.state — shared across all agents in the pipeline."""
      EVALUATOR   = "eval_scores"
      OPTIMIZER   = "final_requirement"
      CRITERIA    = "criteria"
      STORY_ID    = "story_id"

# ── Sample user story ────────────────────────────────────────────────────────
# Used by run.py for quick testing. Replace with a real story from your ALM.

EVALUATOR_OUTPUT_SCHEMA = """
{
  "criteria": "{name}",
  "score": <int 1-10>
 }
"""

SAMPLE_USER_STORY = """
User Story: US-047
As a registered user,
I want to reset my password via a one-time email link,
So that I can regain access to my account when I forgot my credentials.

Acceptance Criteria:
  AC-1: Users enter their registered email address to trigger a reset
  AC-2: A reset link must arrive within 30 seconds
  AC-3: The link expires after 60 minutes
  AC-4: Users must wait 5 minutes before requesting another link (rate limit)
  AC-5: New password must be 8-64 characters with at least 1 uppercase,
        1 lowercase, and 1 digit
  AC-6: All active sessions are invalidated after a successful reset
""".strip()


# ── Prior suite (simulated) ──────────────────────────────────────────────────
# In production this is read from Firestore by story_id.
# Used by tools/diff.py for the diff-on-change calculation.

DATA_SCHEMA_OUTPUT = """
{
  "fieldname": {{integer(0,1000)}},
  "fieldname": "{{uuid()}}",
  "fieldname": {{bool()}},
  "fieldname": {{float(0.0, 100.0)}},
  "fieldname": {{date("2020-01-01", "2025-12-31")}},
  "fieldname": {{enum("option1", "option2", "option3")}},
  "fieldname": {{regex("[A-Z]{3}-[0-9]{4}")}},
  "fieldname": {{list("option1", "option2", "option3")}},
  "fieldname": {{dict("key1", "value1", "key2", "value2")}}
}
"""
