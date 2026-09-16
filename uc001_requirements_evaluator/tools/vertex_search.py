"""
services/vector_search.py — RAG retrieval over the policy clause index
========================================================================
Vector Search's find_neighbors only returns neighbor ids + distances, not
text. So retrieve_clauses() does three things:
  1. Embed the query text with the same model used at ingestion time
     (text-embedding-005, 768 dims — see uc006-vector-index/build_index.py).
  2. Call the deployed Index Endpoint's find_neighbors for those ids.
  3. Join the ids against the chunks.jsonl lookup (clause text/category/
     policy_version) loaded once from GCS.

TODO: the chunks.jsonl lookup below is a module-level in-memory dict loaded
from GCS on first use. This is fine for a policy corpus of a few hundred
clauses. Once clause volume grows, move this to Firestore (get by id) or a
BigQuery lookup table instead of re-parsing one flat file into memory.
"""

import json
import logging
import time
from functools import lru_cache

from google.api_core.exceptions import ServiceUnavailable

from uc001_requirements_evaluator.config import (
    POLICY_CHUNKS_GCS_URI,
    VECTOR_SEARCH_DEPLOYED_INDEX_ID,
    VECTOR_SEARCH_NEIGHBOR_COUNT,
)
from uc001_requirements_evaluator.services.clients import embedding_model, storage_client, vector_search_endpoint

logger = logging.getLogger(__name__)

# vector_search_endpoint() is cached for the process lifetime (services/
# clients.py), so it holds one long-lived gRPC connection. On a corporate
# network/VPN, an idle connection can get silently reset by a firewall/NAT —
# the SDK only discovers this mid-call, as a ServiceUnavailable "Stream
# removed" error. One retry is normally enough: the underlying gRPC channel
# reconnects on the next attempt.
_FIND_NEIGHBORS_MAX_ATTEMPTS = 3
_FIND_NEIGHBORS_RETRY_DELAY_SECONDS = 1.5


def _find_neighbors_with_retry(endpoint, **kwargs):
    for attempt in range(1, _FIND_NEIGHBORS_MAX_ATTEMPTS + 1):
        try:
            return endpoint.find_neighbors(**kwargs)
        except ServiceUnavailable as error:
            if attempt == _FIND_NEIGHBORS_MAX_ATTEMPTS:
                raise
            logger.warning(
                "find_neighbors attempt %d/%d hit a transient connection error, retrying: %s",
                attempt, _FIND_NEIGHBORS_MAX_ATTEMPTS, error,
            )
            time.sleep(_FIND_NEIGHBORS_RETRY_DELAY_SECONDS)


def _parse_gcs_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError(f"Not a gs:// URI: {uri}")
    bucket_and_blob = uri[len("gs://"):]
    bucket_name, _, blob_name = bucket_and_blob.partition("/")
    return bucket_name, blob_name


@lru_cache(maxsize=1)
def _clause_lookup() -> dict[str, dict]:
    """Load chunks.jsonl from GCS once and cache it as {clause_id: clause}."""
    bucket_name, blob_name = _parse_gcs_uri(POLICY_CHUNKS_GCS_URI)
    blob = storage_client().bucket(bucket_name).blob(blob_name)
    raw = blob.download_as_text(encoding="utf-8")

    lookup: dict[str, dict] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        lookup[record["id"]] = record

    logger.info("Loaded %d policy clauses from %s", len(lookup), POLICY_CHUNKS_GCS_URI)
    return lookup


def _join_clauses(neighbors) -> list[dict]:
    lookup = _clause_lookup()
    clauses: list[dict] = []
    for neighbor in neighbors:
        clause = lookup.get(neighbor.id)
        if clause is None:
            logger.warning("Neighbor id %s has no chunks.jsonl entry — skipping", neighbor.id)
            continue
        clauses.append({**clause, "distance": neighbor.distance})
    return clauses


def _embedding_usage(embeddings) -> dict:
    """
    Token usage for one get_embeddings() call. Kept separate from
    callbacks/token_usage.py's TOKEN_USAGE (Gemini LlmAgent calls) — this is
    a plain Vertex AI SDK call made from a deterministic BaseAgent
    (policy_retriever), not an ADK LlmAgent, so it has no after_model_callback
    to hook into.
    """
    token_count = sum(getattr(e.statistics, "token_count", 0) or 0 for e in embeddings)
    return {"token_count": token_count, "embedding_calls": 1, "texts_embedded": len(embeddings)}


def retrieve_clauses_batch(query_texts: list[str], top_k: int | None = None) -> tuple[list[list[dict]], dict]:
    """
    Like retrieve_clauses(), but for multiple independent queries in one
    round trip: one batched embedding call, one find_neighbors call with
    multiple query vectors (the API supports this natively — one call, not
    N). Returns (one clause list per input query text, same order; the
    embedding token usage for this call).

    Use this instead of concatenating multiple queries into one query_text —
    merging op1 + op2 + ... into a single blended embedding dilutes each
    op's own signal and caps the whole diff to top_k clauses shared across
    every op, silently starving ops whose relevant clauses don't make that
    one shared top_k. Querying per-op keeps each op's own top_k.
    """
    if not query_texts:
        return [], {}
    if not VECTOR_SEARCH_DEPLOYED_INDEX_ID:
        raise RuntimeError(
            "VECTOR_SEARCH_DEPLOYED_INDEX_ID is not set. Set it to the "
            "deployed_index_id used when the policy index was deployed to "
            "its endpoint (see scripts/deploy_index_endpoint.py)."
        )

    from vertexai.language_models import TextEmbeddingInput

    model = embedding_model()
    embeddings = model.get_embeddings(
        [TextEmbeddingInput(text=text, task_type="RETRIEVAL_QUERY") for text in query_texts]
    )
    usage = _embedding_usage(embeddings)

    endpoint = vector_search_endpoint()
    neighbor_count = top_k or VECTOR_SEARCH_NEIGHBOR_COUNT
    response = _find_neighbors_with_retry(
        endpoint,
        deployed_index_id=VECTOR_SEARCH_DEPLOYED_INDEX_ID,
        queries=[e.values for e in embeddings],
        num_neighbors=neighbor_count,
    )

    clause_lists = [_join_clauses(neighbors) for neighbors in response] if response else [[] for _ in query_texts]
    return clause_lists, usage


def retrieve_clauses(query_text: str, top_k: int | None = None) -> list[dict]:
    """
    Embed `query_text`, query the deployed Vector Search endpoint, and
    return the matched clauses joined with their text/category/policy_version.

    Returns a list of {id, distance, source, category, policy_version, text}
    ordered by relevance (closest first). Returns [] if the query embeds to
    no neighbors, but raises if the endpoint or lookup file is unreachable —
    an evaluation must not silently run ungrounded.
    """
    [clauses], _usage = retrieve_clauses_batch([query_text], top_k=top_k)
    return clauses
