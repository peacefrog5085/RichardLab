from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


API_ORIGIN = "https://api.github.com"
ALLOWED_REPOSITORY = "peacefrog5085/RichardLab"


class GitHubReadError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubReadOnlyClient:
    token: str
    repository: str = ALLOWED_REPOSITORY
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if self.repository != ALLOWED_REPOSITORY:
            raise ValueError("Repository is outside the pilot allowlist")
        if not self.token.strip():
            raise ValueError("GitHub read token is required")

    def repository_metadata(self) -> dict[str, Any]:
        return self._get(f"/repos/{self.repository}")

    def pull_requests(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._get_collection("pulls", limit)

    def issues(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._get_collection("issues", limit)

    def check_runs(self, ref: str = "master", limit: int = 10) -> list[dict[str, Any]]:
        if not ref.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid Git reference")
        data = self._get(
            f"/repos/{self.repository}/commits/{ref}/check-runs",
            {"per_page": self._bounded_limit(limit)},
        )
        return list(data.get("check_runs", []))

    def _get_collection(self, resource: str, limit: int) -> list[dict[str, Any]]:
        return self._get(
            f"/repos/{self.repository}/{resource}",
            {"state": "all", "per_page": self._bounded_limit(limit)},
        )

    @staticmethod
    def _bounded_limit(limit: int) -> int:
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError("Limit must be an integer")
        return max(1, min(limit, 50))

    def _get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        if not path.startswith(f"/repos/{ALLOWED_REPOSITORY}"):
            raise ValueError("GitHub path is outside the pilot allowlist")
        url = f"{API_ORIGIN}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "RichardLab-Echo-readonly-pilot",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise GitHubReadError(f"GitHub read failed with HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise GitHubReadError(f"GitHub read failed: {type(exc).__name__}") from exc
