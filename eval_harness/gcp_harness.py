# from vertexai.preview.evaluation import EvalTask
# from vertexai.generative_models import GenerativeModel
import json
import subprocess
import time

import pandas as pd
from flask import Flask, g, jsonify, request
from google.cloud import storage
from ruff import find_ruff_bin
from vertexai import Client, types

from bigquery_tools import query_by_key
PROJECT_ID = "jvtxdzs-atcp-cec-innov-hub"
LOCATION = "us-central1"

client = Client(project=PROJECT_ID, location=LOCATION)
app = Flask(__name__)


@app.before_request
def _start_request_timer():
    print(f"{request.method} {request.path} received")
    g.request_start = time.perf_counter()


@app.after_request
def _log_request_duration(response):
    """Prints how long the whole request took, for every endpoint."""
    elapsed = time.perf_counter() - g.request_start
    print(f"{request.method} {request.path} took {elapsed:.3f}s")
    return response


def lint_gcs_file(bucket_name: str, blob_path: str) -> list[dict]:
    """
    Runs ruff against a Python file stored in GCS, without downloading it to
    disk first -- reads the blob's bytes and pipes them to `ruff check` over
    stdin. Only reports findings (each with its recommended fix, if any,
    under the "fix" key) -- nothing is auto-applied or written back to GCS.
    """
    storage_client = storage.Client()
    source = storage_client.bucket(bucket_name).blob(blob_path).download_as_bytes()

    start = time.perf_counter()
    result = subprocess.run(
        [
            find_ruff_bin(), "check", "-",
            "--stdin-filename", blob_path,
            "--output-format=json",
        ],
        input=source,
        capture_output=True,
    )
    elapsed = time.perf_counter() - start
    print(f"ruff check {blob_path} took {elapsed:.3f}s")

    return json.loads(result.stdout or "[]")


def print_lint_findings(findings: list[dict]) -> None:
    """Prints ruff findings as a readable table instead of raw JSON."""
    if not findings:
        print("No issues found.")
        return

    print(f"\n=== {len(findings)} ISSUE(S) FOUND ===")
    columns = ["line", "col", "code", "message", "fix"]
    rows = [
        {
            "line": str(f["location"]["row"]),
            "col": str(f["location"]["column"]),
            "code": f["code"],
            "message": f["message"],
            "fix": f["fix"]["message"] if f.get("fix") else "-",
        }
        for f in findings
    ]

    widths = {col: max(len(col), *(len(row[col]) for row in rows)) for col in columns}
    print("  ".join(col.upper().ljust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  ".join(row[col].ljust(widths[col]) for col in columns))


def run_quality_eval(session_id: str, table: str, dataset: str) -> dict:
    """
    Fetches the row from `table` whose session_id matches, and scores the
    prompt/response pair already recorded there -- skips run_inference()
    entirely since the response was already generated (e.g. by
    log_inference_to_bigquery / save_generated_schema_to_bq) and just needs
    scoring now.
    Returns a JSON-serializable summary: per-metric averages plus a per-case
    breakdown (prompt, response, metric, score, explanation).
    """
    row = query_by_key(session_id, table=table, column="session_id", dataset=dataset)
    eval_df = pd.DataFrame([{"prompt": row["prompt"], "response": row["response"]}])
    eval_dataset = types.EvaluationDataset(eval_dataset_df=eval_df)
    eval_result = client.evals.evaluate(dataset=eval_dataset)
    return build_eval_summary(eval_result, eval_dataset)


def build_eval_summary(eval_result, eval_dataset) -> dict:
    """Same data print_eval_results renders, but as a JSON-serializable dict for an API response."""
    summary = [
        {
            "metric": m.metric_name,
            "mean_score": round(m.mean_score, 2) if m.mean_score is not None else None,
            "stdev": round(m.stdev_score, 2) if m.stdev_score is not None else None,
            "valid_cases": m.num_cases_valid,
            "error_cases": m.num_cases_error,
        }
        for m in (eval_result.summary_metrics or [])
    ]

    prompts = eval_dataset.eval_dataset_df["prompt"].tolist()
    responses = eval_dataset.eval_dataset_df["response"].tolist()

    detail = []
    for case in eval_result.eval_case_results or []:
        idx = case.eval_case_index
        for candidate in case.response_candidate_results or []:
            for metric_name, result in (candidate.metric_results or {}).items():
                detail.append({
                    "case": idx,
                    "prompt": prompts[idx] if idx is not None else None,
                    "response": responses[idx] if idx is not None else None,
                    "metric": metric_name,
                    "score": result.score,
                    "explanation": result.explanation,
                })

    return {"summary": summary, "detail": detail}


def print_responses(eval_dataset) -> None:
    """Prints each prompt alongside the full LLM response generated for it."""
    df = eval_dataset.eval_dataset_df
    for i, row in df.iterrows():
        print(f"\n--- Case {i} ---")
        print(f"PROMPT:   {row['prompt']}")
        print(f"RESPONSE: {row['response']}")


def _truncate(text, length=80):
    if not text:
        return text
    return text if len(text) <= length else text[:length].rstrip() + "..."


def print_eval_results(eval_result, eval_dataset) -> None:
    """Prints eval_result as two readable tables instead of a raw JSON dump:
    a per-metric summary (mean/stdev across all cases), and a per-case detail
    table (prompt, metric, score, explanation)."""

    print("\n=== SUMMARY (per metric, across all cases) ===")
    summary_rows = [
        {
            "metric": m.metric_name,
            "mean_score": round(m.mean_score, 2) if m.mean_score is not None else None,
            "stdev": round(m.stdev_score, 2) if m.stdev_score is not None else None,
            "valid_cases": m.num_cases_valid,
            "error_cases": m.num_cases_error,
        }
        for m in (eval_result.summary_metrics or [])
    ]
    print(pd.DataFrame(summary_rows).to_string(index=False) if summary_rows else "(no summary metrics)")

    print("\n=== PER-CASE DETAIL ===")
    prompts = eval_dataset.eval_dataset_df["prompt"].tolist()

    detail_rows = []
    for case in eval_result.eval_case_results or []:
        idx = case.eval_case_index
        prompt_preview = _truncate(prompts[idx]) if idx is not None else None
        for candidate in case.response_candidate_results or []:
            for metric_name, result in (candidate.metric_results or {}).items():
                detail_rows.append({
                    "case": idx,
                    "prompt": prompt_preview,
                    "metric": metric_name,
                    "score": result.score,
                    "explanation": _truncate(result.explanation),
                })
    print(pd.DataFrame(detail_rows).to_string(index=False) if detail_rows else "(no per-case results)")

@app.route("/uc001", methods=["POST"])
def uc001_eval():
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id")
    if not session_id:
            return jsonify({"error": "'session_id' is required"}), 400

    llm_findings = run_quality_eval(session_id, "llm_inferences", "uc001_db")

    return jsonify({"llm_findings": llm_findings})



@app.route("/uc004", methods=["POST"])
def uc004_eval():
    """
    Runs both the ruff linter and the LLM quality eval for a given session's
    generated test script, then returns both finding sets together.

    POST body: {"session_id": "run-123"}
    """
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id")
    if not session_id:
        return jsonify({"error": "'session_id' is required"}), 400

    # Matches how uc004's runner.py saves the generated script to GCS:
    # save_file_to_gcs(result[StateKey.TEST_SCRIPTS], f"{run_id}.py", StateKey.TEST_SCRIPTS)
    linter_findings = eval_lint("uc004", f"test_scripts/{session_id}.py")
    llm_findings = run_quality_eval(session_id, "llm_inference", "uc004_result")

    return jsonify({"linter_findings": linter_findings, "llm_findings": llm_findings})

def eval_lint(bucket: str, blob_path: str) -> list[dict]:
    """Runs ruff against a Python file stored in GCS and returns its findings."""
    return lint_gcs_file(bucket, blob_path)


@app.route("/eval/quality", methods=["POST"])
def eval_quality():
    """
    Runs inference + response-quality scoring over a list of prompts.

    POST body: {"prompts": ["...", "..."], "model": "gemini-2.5-flash"}
    ("model" is optional, defaults to gemini-2.5-flash)
    """
    payload = request.get_json(silent=True) or {}
    prompts = payload.get("prompts")
    if not prompts:
        return jsonify({"error": "'prompts' (a non-empty list of strings) is required"}), 400

    model = payload.get("model", "gemini-2.5-flash")
    summary = run_quality_eval(prompts, model=model)
    return jsonify(summary)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True)