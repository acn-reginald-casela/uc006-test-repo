import os
import requests
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ.get("GITHUB_TOKEN")
OWNER = os.environ.get("OWNER")
REPO = os.environ.get("REPO")
HEADERS = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        }
BASE_API = f"https://api.github.com/repos/{OWNER}/{REPO}"
BASE_URL = f"https://github.com/{OWNER}/{REPO}"

def get_pr_diff(pull_number: str | int):
    url = f"{BASE_URL}/pull/{pull_number}.diff"
    response = requests.get(url, headers=HEADERS)
    return response.text

def construct_body(components: dict):
    body = f"CLAUSE {components.get("clause_id")}\nSEVERITY: {components.get("severity", "N\\A")}\n{components.get("comment")}"
    return body

def post_pr_comments(pull_number, findings: list[dict]):
    url = f"{BASE_API}/pulls/{pull_number}"

    #   GET CURRENT COMMIT_SHA FOR PULL REQUEST
    response = requests.get(url, headers=HEADERS)
    commit_sha = response.json()["head"]["sha"]
    for finding in findings:
        post_pr_line_comment(url,
                             body=construct_body(finding),
                             commit_sha=commit_sha,
                             path = finding.get("filename"),
                             line=finding.get("line_number")
                               )
def post_pr_line_comment(
    url: str,
    body: str,
    commit_sha: str,
    path: str,
    line: int,
    side: str = "RIGHT",
    start_line: int = None,
    start_side: str = None,
):
    """
    Post an inline review comment on a specific line of a file in a pull request.

    Docs: https://docs.github.com/en/rest/pulls/comments#create-a-review-comment-for-a-pull-request

    Args:
        url:    API endpoint of the specific pull request
        commit_sha: The SHA of the commit being commented on. Should be the
                    PR's latest commit SHA, or your comment may render as
                    outdated if a later commit touches that line.
        body: The comment text
        path: Relative path of the file, e.g. "src/main.py"
        line: The line number in the file (in the PR's diff) to comment on.
              This must correspond to a line that appears in the diff
              (added, or unchanged context shown near a change).
        side: Which side of the diff `line` refers to.
              "RIGHT" = the new/added version of the file (most common case).
              "LEFT" = the old/removed version of the file (for commenting
              on a deleted line).
        start_line: Optional. If set, creates a multi-line comment spanning
                    from `start_line` to `line`.
        start_side: Optional. Side for `start_line` in a multi-line comment
                    (defaults to `side` if not given).
        token: GitHub token with repo access (or set GITHUB_TOKEN env var)

    Returns:
        The JSON response from GitHub (the created review comment object).
    """
    if not TOKEN:
        raise ValueError("A GitHub token is required (pass `token=` or set GITHUB_TOKEN).")

    comment_url = f"{url}/comments"
    payload = {
        "body": body,
        "commit_id": commit_sha,
        "path": path,
        "line": line,
        "side": side,
    }

    if start_line is not None:
        payload["start_line"] = start_line
        payload["start_side"] = start_side or side

    response = requests.post(comment_url, headers=HEADERS, json=payload)
    if not response.ok:
        print(f"GitHub API error: {response.status_code}")
        print(response.text)
        response.raise_for_status()

    result = response.json()
    return result

# ## Example usage:
if __name__ == "__main__":
    pull_number = 1
    findings = [{
        "clause_id": "1a",
        "severity": "MEDIUM",
        "comment": "This is a sample comment",
        "line_number": 3,
        "filename": "sample2.py"
    }]
    post_pr_comments(pull_number, findings)

    # print(f"Comments posted on .../pulls/{pull_number}")
    # get_pr_diff(1)

