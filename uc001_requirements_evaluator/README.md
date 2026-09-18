# uc001_requirements_evaluator

An evaluator–optimizer loop that reviews a requirement at intake, scores it
against a fixed quality rubric, and rewrites it to close the specific
defects — cycling until the bar is met or a guard (`max_iterations`) stops
it. Defects that need a business decision are flagged as open questions
rather than invented. The value is rework prevented: requirement defects
caught at intake instead of surfacing in testing or production, where
remediation costs multiples more.

Served over an HTTP API (Flask) instead of asking an agent to invent its
own input: the caller posts a Jira issue id (or the requirement text
directly), and gets back the refined requirement.

## How it works

`root_agent` is a [Google ADK](https://google.github.io/adk-docs/) `LoopAgent`
(`pipeline.py`) that runs two sub-agents in order, repeatedly, up to
`max_iterations=5`:

1. **Evaluator** (`agents/evaluator.py`, `prompts/evaluator.py`) — a
   `gemini-pro`-tier agent that scores the current requirement against
   each dimension of the rubric (1–10), using a `retrieve_clauses` tool
   (`tools/vertex_search.py`) to pull related/duplicate requirements from a
   Vertex AI Vector Search index for cross-checking. Its
   `after_agent_callback` (`tools/after_evaluate.py`,
   `stop_loop_if_approved`) parses the scores, tracks the best-scoring
   version seen so far in session state, and escalates (stops the loop)
   once every dimension clears `APPROVAL_SCORE_THRESHOLD`.
2. **Optimizer** (`agents/optimizer.py`, `prompts/optimizer.py`) — a
   `gemini-flash`-tier agent that drafts the requirement on the first pass,
   or revises it on later passes per the evaluator's scoring feedback,
   preserving the author's intent and flagging anything needing a business
   decision as an open question instead of inventing it.

State is passed between the two agents via ADK session state, using the
keys defined in `constants.py::StateKey` (`OPTIMIZER` holds the current
requirement text, `EVALUATOR` holds the latest scores, `CRITERIA` holds the
rubric, `STORY_ID`/`ITERATION` are bookkeeping).

## Layout

```
agent.py                    reference LoopAgent wiring (see pipeline.py for the version actually used)
pipeline.py                 build_pipeline() -> the LoopAgent that main_runner.py runs
main_runner.py              Flask app; POST /test-cases entry point
config.py                   env-var-backed settings (reads .env via dotenv)
constants.py                state keys, output schemas, sample/fallback data
requirements.txt            Python dependencies
Dockerfile                  container image for `main_runner:app`, run via gunicorn
cloudrun-env.yaml           env vars for `gcloud run deploy --env-vars-file`
.gcloudignore                excludes .env / cloudrun-env.yaml / caches from deploys

agents/
  evaluator.py               build_evaluator_agent()
  optimizer.py                build_optimizer_agent()
prompts/
  evaluator.py                evaluator instruction template
  optimizer.py                 optimizer instruction template
services/
  clients.py                  cached GCP client factories (bigquery, storage, aiplatform, embedding model)
  bigquery.py                  audit-ledger writer (write_audit_record)
  vector_search.py             RAG retrieval over the policy clause index
tools/
  after_evaluate.py            stop_loop_if_approved after_agent_callback
  bigquery_tools.py            query_table() / insert_row() generic helpers
  formatter.py                 format_to_readable(), clean_json_string()
  jira_tools.py                Jira REST helpers (get/create issue, add comment)
  vertex_search.py             retrieve_clauses tool used by the evaluator agent
  general.py                   (currently empty)
```

## Setup

```bash
pip install -r requirements.txt
```

Auth is Application Default Credentials:

```bash
gcloud auth application-default login
```

Copy `.env.example` → `.env` (or export these directly) and fill in at
least `GOOGLE_CLOUD_PROJECT`. Full list of settings, all read in
`config.py`:

| Variable | Default | Purpose |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | *(required)* | Vertex AI project |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Vertex AI region |
| `FLASH_MODEL` | `gemini-3.6-flash` | Optimizer model |
| `PRO_MODEL` | `gemini-3.6-flash` | Evaluator model |
| `EMBEDDING_MODEL` | `text-embedding-005` | RAG embedding model |
| `EMBEDDING_DIMENSIONS` | `768` | Embedding vector size |
| `JIRA_BASE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` | — | Jira REST auth |
| `RUBRIC_VERSION` | `2026.09` | Which rubric row to load from BigQuery |
| `POLICY_CHUNKS_GCS_URI` | `gs://.../chunks.jsonl` | Policy clause corpus |
| `VECTOR_SEARCH_INDEX_ENDPOINT` / `VECTOR_SEARCH_DEPLOYED_INDEX_ID` / `VECTOR_SEARCH_NEIGHBOR_COUNT` | — / — / `8` | Deployed Vector Search endpoint for RAG |
| `BQ_PROJECT` / `BQ_DATASET` / `BQ_LOCATION` / `BQ_AUDIT_TBL` | project / `uc006_db` / region / `audit` | Audit ledger sink |
| `BQ_ENABLED` | `false` | Toggle the audit ledger sink |

> `config.py` currently ships a live-looking `JIRA_API_TOKEN` default and
> `cloudrun-env.yaml` ships a GitHub PAT in plaintext — both should be
> rotated and sourced only from Secret Manager / env vars before this goes
> anywhere shared.

## Running locally

```bash
python main_runner.py
# then, from another shell:
curl -X POST http://localhost:8080/test-cases \
  -H "Content-Type: application/json" \
  -d '{"story": {"id": "US-142", "requirements": "As a ..., I want ..., so that ..."}, "session_id": "regie_123"}'
```

`story.requirements` is optional — if omitted, the requirement text is
fetched from Jira by `story.id` instead.

`POST /test-cases` runs the evaluator/optimizer loop to convergence (or
`max_iterations`), posts the refined requirement as a comment on the
source Jira issue, writes one row per run to the `results` BigQuery table
(`tools/bigquery_tools.insert_row`), and returns:

```json
{
  "story_id": "US-142",
  "final_requirement": "..."
}
```

## Deployment

The `Dockerfile` builds an image that serves `main_runner:app` via
gunicorn (Cloud Run injects `$PORT`, workers/timeouts are tuned for a
pipeline run that can take minutes). Deploy env vars via
`cloudrun-env.yaml`, e.g.:

```bash
gcloud run deploy uc001-requirements-evaluator \
  --source . \
  --env-vars-file cloudrun-env.yaml
```

## Known gaps

- `agents/evaluator.py` and `services/vector_search.py` both import from
  `tools/vertex_search.py`, which is a near-duplicate of
  `services/vector_search.py` — worth consolidating to one source of truth.
- `agent.py` (root-level) is a standalone reference copy of the LoopAgent
  wiring; `pipeline.py::build_pipeline()` is what `main_runner.py` actually
  runs.
- `tools/general.py` is currently empty.
