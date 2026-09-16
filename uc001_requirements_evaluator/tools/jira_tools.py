import os
import sys

if __name__ == "__main__":
    # Run directly (e.g. `py .\jira_tools.py`), so uc001_requirements_evaluator
    # isn't on sys.path yet -- add the repo root (two levels up from this file).
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import requests
from uc001_requirements_evaluator.config import JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN

# JIRA_BASE_URL = os.environ["JIRA_BASE_URL"]  # e.g. https://avclaudex2026.atlassian.net
# JIRA_EMAIL = os.environ["JIRA_EMAIL"]
# JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]

def list_projects() -> list:
    """List all projects visible to this token, with their keys."""
    url = f"{JIRA_BASE_URL}/rest/api/3/project/search"
    response = requests.get(
        url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    return [(p["key"], p["name"]) for p in response.json()["values"]]


def create_jira_issue(project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> dict:
    """Create a Jira issue and return the response, including its generated 'key' (e.g. KAN-3)."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
    }
    if description:
        payload["fields"]["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}],
                }
            ],
        }
    response = requests.post(
        url,
        json=payload,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Accept": "application/json"},
    )
    if not response.ok:
        print(response.text)
    response.raise_for_status()
    return response.json()


def _adf_to_text(adf_node) -> str:
    """Flatten Atlassian Document Format (the 'description' field's shape) into plain text."""
    if not adf_node:
        return ""
    parts = []
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                parts.append(node.get("text", ""))
            for child in node.get("content", []):
                walk(child)
            if node.get("type") in ("paragraph", "heading"):
                parts.append("\n")
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(adf_node)
    return "".join(parts).strip()


def _summarize_linked_issue(linked: dict) -> dict:
    """Shrink a linked/sub-task issue object down to the fields worth keeping."""
    return {
        "key": linked.get("key"),
        "summary": linked.get("fields", {}).get("summary", ""),
        "status": linked.get("fields", {}).get("status", {}).get("name"),
        "issue_type": linked.get("fields", {}).get("issuetype", {}).get("name"),
    }


def get_jira_issue(issue_key: str) -> dict:
    """Fetch a Jira issue and return its key fields as a plain dict.

    Returns: {"key", "summary", "description", "status", "issue_type",
    "subtasks", "linked_issues"} — description is flattened from Atlassian
    Document Format to plain text; subtasks/linked_issues are lists of
    {"key", "summary", "status", "issue_type"} (linked_issues also carries
    "relationship", e.g. "blocks" / "is blocked by" / "relates to").
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    response = requests.get(
        url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    fields = response.json()["fields"]

    subtasks = [_summarize_linked_issue(st) for st in fields.get("subtasks", [])]

    linked_issues = []
    for link in fields.get("issuelinks", []):
        other = link.get("outwardIssue") or link.get("inwardIssue")
        if not other:
            continue
        relationship = (
            link["type"]["outward"] if "outwardIssue" in link else link["type"]["inward"]
        )
        summary = _summarize_linked_issue(other)
        summary["relationship"] = relationship
        linked_issues.append(summary)

    return {
        "key": issue_key,
        "summary": fields.get("summary", ""),
        "description": _adf_to_text(fields.get("description")),
        "status": fields.get("status", {}).get("name"),
        "issue_type": fields.get("issuetype", {}).get("name"),
        "subtasks": subtasks,
        "linked_issues": linked_issues,
    }


def add_jira_comment(issue_key: str, comment: str) -> dict:
    """Add a comment to a Jira issue via the REST API."""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment}],
                }
            ],
        }
    }
    response = requests.post(
        url,
        json=payload,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # print(list_projects())
    # created = create_jira_issue("LANDISGYR", summary="Test issue from Python API")
    # issue_key = created["key"]  # e.g. "KAN-3"
    # print(issue_key)
    # https://avclaudex2026.atlassian.net/browse/LANDISGYR-4
    issue_key = "LANDISGYR-1"

    # result = add_jira_comment(issue_key, "Test comment")
    # print(result)

    issue = get_jira_issue(issue_key)
    print(issue)
