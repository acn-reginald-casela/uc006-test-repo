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
DATASET = "uc001_db"
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
      ITERATION   = "iteration"

# ── Sample user story ────────────────────────────────────────────────────────
# Used by run.py for quick testing. Replace with a real story from your ALM.

EVALUATOR_OUTPUT_SCHEMA = """
{
  "criteria": "name",
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
SAMPLE_READABLE_CRITERIA = """
- unambiguous: The requirement has exactly one reasonable interpretation. Flag vague qualifiers (fast, user-friendly, appropriate, robust, seamless) that have no measurable definition attached.
  Fail example: The system should respond quickly to user requests.
  Pass example: The system must return a search response within 500ms at the 95th percentile under normal load.

- complete: All information needed to implement and test the requirement is present: actor, trigger/condition, expected outcome, and relevant constraints. Nothing critical is left implied.
  Fail example: Users can cancel an order.
  Pass example: A logged-in customer can cancel an order within 15 minutes of placing it, provided the order has not yet been marked as shipped.

- consistent: Does not contradict sibling requirements retrieved from the backlog. Check stated numbers, timeframes, and rules against related requirements for the same feature area.
  Fail example: Refunds must be processed within 3 business days. (contradicts REQ-2004: 'Refunds must be issued within 5 business days.')
  Pass example: Refunds must be processed within 5 business days, consistent with the existing refund policy (REQ-2004).

- verifiable: A tester could write a concrete pass/fail test case directly from the wording alone, with no subjective judgment call required.
  Fail example: The dashboard should load in a reasonable amount of time.
  Pass example: The dashboard must fully render within 2 seconds on a standard broadband connection (10 Mbps+).

- atomic: Expresses exactly one requirement. Sentences joined by 'and'/'or' that bundle two independently testable rules should be flagged and split into separate requirements.
  Fail example: Users can edit their profile and admins can deactivate accounts.
  Pass example: Users can edit their own profile information (name, email, avatar) while logged in.

- feasible: Does not demand something technically or practically impossible given stated or known system constraints. Lower confidence dimension — an LLM cannot fully verify feasibility without deep system context, so treat borderline callsas OPEN_QUESTIONS rather than hard fails.
  Fail example: The system must guarantee zero downtime with zero cost and instant global consistency across all regions.
  Pass example: The system must maintain 99.9 percent uptime per calendar month, measured across all production regions.
  """

SAMPLE_REQUIREMENT = "An evaluator–optimizer loop reviews each requirement at intake. An Evaluator scores it against an explicit quality rubric — unambiguous, complete, consistent, testable, atomic — and an Optimizer rewrites it to close the specific defects, cycling until the bar is met or a guard stops it. Defects that need a business decision are flagged as open questions rather than invented. The value is rework prevented: requirement defects caught at intake instead of surfacing in testing orproduction, where remediation costs multiples more."