"""
services/bigquery.py — Control-operation audit ledger
========================================================
Writes one row per evaluated PR to the configured dataset. This table is
the audit evidence for the control — PR ref, policy_version(s) checked,
data ops extracted, clauses retrieved, findings posted, and a timestamp.

The dataset/table are created on first write, so no manual DDL is needed —
but the dataset itself (BQ_DATASET) must already exist; BigQuery does not
auto-create datasets the way load jobs auto-create tables.
"""

from uc001_requirements_evaluator.config import BQ_PROJECT, BQ_DATASET, BQ_AUDIT_TBL
from uc001_requirements_evaluator.services.clients import bigquery_client


def _audit_schema():
    from google.cloud import bigquery
    return [
        bigquery.SchemaField("run_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("pr_ref", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("evaluated_at", "TIMESTAMP"),
        bigquery.SchemaField("policy_versions", "STRING", mode="REPEATED"),
        bigquery.SchemaField("data_ops_json", "STRING"),
        bigquery.SchemaField("clauses_checked", "STRING", mode="REPEATED"),
        bigquery.SchemaField("findings_json", "STRING"),
        bigquery.SchemaField("findings_count", "INTEGER"),
        bigquery.SchemaField("comments_posted", "INTEGER"),
        bigquery.SchemaField("token_usage", "STRING"),
        bigquery.SchemaField("embedding_usage", "STRING"),
    ]


def write_audit_record(row: dict) -> str:
    """
    Append one audit row for a completed PR evaluation.

    Uses a load job rather than streaming inserts — no streaming buffer means
    the table is queryable immediately and creatable on first write. Raises
    on failure; the caller (comment_and_log) is expected to catch and log it
    without blocking the PR comment path.
    """
    from google.cloud import bigquery

    job = bigquery_client().load_table_from_json(
        [row],
        f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_AUDIT_TBL}",
        job_config=bigquery.LoadJobConfig(
            schema=_audit_schema(),
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
        ),
    )
    job.result()  # blocks until the load finishes so errors surface here
    return f"Wrote audit record to {BQ_PROJECT}.{BQ_DATASET}.{BQ_AUDIT_TBL}"
