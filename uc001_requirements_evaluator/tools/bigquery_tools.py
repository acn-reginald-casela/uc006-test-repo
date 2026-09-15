import re

from google.cloud import bigquery

from uc001_requirements_evaluator.constants import PROJECT_ID, DATASET

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def _bq_param_type(value) -> str:
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, int):
        return "INT64"
    if isinstance(value, float):
        return "FLOAT64"
    return "STRING"


def query_table(
    table: str,
    dataset: str = DATASET,
    project: str = PROJECT_ID,
    where: dict | None = None,
    limit: int = 1000,
) -> list[dict]:
    """
    Query rows from a BigQuery table.

    Args:
        table: Name of the table to query.
        dataset: Dataset containing the table. Defaults to DATASET.
        project: GCP project the dataset lives in. Defaults to PROJECT_ID.
        where: Optional mapping of column -> value; conditions are ANDed
            together as equality filters, e.g. {"status": "open"}.
        limit: Maximum number of rows to return.

    Returns:
        list[dict]: The query result rows, each as a dict of column -> value.
    """
    for identifier in (project, dataset, table):
        if not _IDENTIFIER_RE.match(identifier):
            raise ValueError(f"Invalid BigQuery identifier: {identifier!r}")

    query = f"SELECT * FROM `{project}.{dataset}.{table}`"
    query_parameters = []
    if where:
        conditions = []
        for i, (column, value) in enumerate(where.items()):
            if not _IDENTIFIER_RE.match(column):
                raise ValueError(f"Invalid BigQuery identifier: {column!r}")
            param_name = f"where_{i}"
            conditions.append(f"`{column}` = @{param_name}")
            query_parameters.append(bigquery.ScalarQueryParameter(param_name, _bq_param_type(value), value))
        query += " WHERE " + " AND ".join(conditions)
    query += f" LIMIT {limit}"

    client = bigquery.Client(project=project)
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
    rows = client.query(query, job_config=job_config).result()
    return [dict(row) for row in rows]
