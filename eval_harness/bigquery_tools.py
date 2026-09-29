"""
bigquery_tools.py — BigQuery lookups for the eval harness
==========================================================
Generic "fetch a row by key" helper, shared by anything in eval_harness that
needs to pull config (rubrics, prompts, etc.) out of BigQuery by a key column.

Auth: Application Default Credentials (same as the rest of the app)
    gcloud auth application-default login
"""

import time

from google.cloud import bigquery

PROJECT_ID = "jvtxdzs-atcp-cec-innov-hub"
DATASET = "uc006_db"

# One bigquery.Client per project, reused across calls instead of reconnecting
# (re-discovering ADC, opening a new transport) on every query_by_key() call.
_clients: dict[str, bigquery.Client] = {}


def _get_client(project: str) -> bigquery.Client:
    if project not in _clients:
        _clients[project] = bigquery.Client(project=project)
    return _clients[project]


def query_by_key(
    key: str,
    table: str,
    column: str = "key",
    dataset: str = DATASET,
    project: str = PROJECT_ID,
) -> dict:
    """
    Fetches the single row from `table` whose `column` equals `key`.

    Raises LookupError if no row matches.
    """
    start = time.perf_counter()
    client = _get_client(project)
    query = f"SELECT * FROM `{project}.{dataset}.{table}` WHERE `{column}` = @key LIMIT 1"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("key", "STRING", key)]
    )
    # query_and_wait uses BigQuery's synchronous jobs.query fast path instead
    # of query()+result()'s separate job-insert/poll/get-results round trips --
    # meaningfully faster for small, quick lookups like this one.
    rows = list(client.query_and_wait(query, job_config=job_config))
    elapsed = time.perf_counter() - start
    print(f"BigQuery query_by_key({table}, {column}={key!r}) took {elapsed:.3f}s")

    if not rows:
        raise LookupError(f"No row found where {column} = {key!r} in {project}.{dataset}.{table}")

    return dict(rows[0])
