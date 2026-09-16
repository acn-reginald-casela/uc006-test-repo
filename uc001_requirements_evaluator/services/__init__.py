"""GCP / external-system adapters. All I/O with external systems lives here."""

from uc001_requirements_evaluator.services.bigquery import write_audit_record
from uc001_requirements_evaluator.services.vector_search import retrieve_clauses

__all__ = ["write_audit_record", "post_pr_comments", "retrieve_clauses"]
