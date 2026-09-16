"""
services/clients.py — Cached GCP client factories
==================================================
The only place in the codebase that constructs a GCP client.

Auth is Application Default Credentials — the same credential that
Vertex AI uses, so `gcloud auth application-default login` covers everything.

SDK imports are deferred into the functions so a run with a sink disabled
never requires that sink's package to be installed.
"""

from functools import lru_cache

from uc001_requirements_evaluator.config import (
    BQ_PROJECT,
    BQ_LOCATION,
    VERTEX_PROJECT,
    VERTEX_LOCATION,
)


@lru_cache(maxsize=1)
def bigquery_client():
    from google.cloud import bigquery
    return bigquery.Client(project=BQ_PROJECT, location=BQ_LOCATION)


@lru_cache(maxsize=1)
def storage_client():
    from google.cloud import storage
    return storage.Client(project=VERTEX_PROJECT)


@lru_cache(maxsize=1)
def embedding_model():
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    from uc001_requirements_evaluator.config import EMBEDDING_MODEL

    vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
    return TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def vector_search_endpoint():
    """The deployed MatchingEngineIndexEndpoint that serves find_neighbors.

    Raises a clear error if the endpoint hasn't been deployed yet — see
    scripts/deploy_index_endpoint.py and deployment.md.
    """
    from google.cloud import aiplatform
    from uc001_requirements_evaluator.config import VECTOR_SEARCH_INDEX_ENDPOINT

    if not VECTOR_SEARCH_INDEX_ENDPOINT:
        raise RuntimeError(
            "VECTOR_SEARCH_INDEX_ENDPOINT is not set. The policy Vector Search "
            "index must be deployed to an endpoint first — run "
            "scripts/deploy_index_endpoint.py or deploy it via the GCP console, "
            "then set VECTOR_SEARCH_INDEX_ENDPOINT to its resource name."
        )

    aiplatform.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
    return aiplatform.MatchingEngineIndexEndpoint(VECTOR_SEARCH_INDEX_ENDPOINT)
