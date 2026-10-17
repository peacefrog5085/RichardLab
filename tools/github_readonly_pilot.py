#!/usr/bin/env python3
"""Run bounded GitHub GET requests without printing credentials or content."""

import json
import os

from ai.integrations.github_readonly import GitHubReadOnlyClient


def main() -> int:
    token = os.environ.get("RICHARDLAB_GITHUB_READ_TOKEN", "")
    client = GitHubReadOnlyClient(token=token)
    repository = client.repository_metadata()
    pulls = client.pull_requests(limit=5)
    issues = client.issues(limit=5)
    checks = client.check_runs(limit=10)
    evidence = {
        "pilot": "github-read-only",
        "repository": repository.get("full_name"),
        "default_branch": repository.get("default_branch"),
        "private": repository.get("private"),
        "reads": {
            "metadata": True,
            "pull_requests": len(pulls),
            "issues": len(issues),
            "check_runs": len(checks),
        },
        "writes_attempted": 0,
        "token_logged": False,
    }
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
