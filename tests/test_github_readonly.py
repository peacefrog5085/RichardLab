import io
import urllib.request

import pytest

from ai.integrations.github_readonly import GitHubReadOnlyClient, GitHubReadError


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_client_uses_get_fixed_host_and_does_not_expose_token(monkeypatch):
    captured = {}

    def fake_open(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response(b'{"full_name":"peacefrog5085/RichardLab"}')

    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    token = "pilot-token-value"
    result = GitHubReadOnlyClient(token).repository_metadata()
    request = captured["request"]
    assert result["full_name"] == "peacefrog5085/RichardLab"
    assert request.method == "GET"
    assert request.full_url == "https://api.github.com/repos/peacefrog5085/RichardLab"
    assert token not in request.full_url
    assert captured["timeout"] == 10.0


def test_client_rejects_other_repositories():
    with pytest.raises(ValueError, match="allowlist"):
        GitHubReadOnlyClient("token", repository="someone/else")


def test_client_bounds_pagination(monkeypatch):
    captured = {}

    def fake_open(request, timeout):
        captured["url"] = request.full_url
        return Response(b"[]")

    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    GitHubReadOnlyClient("token").issues(limit=10000)
    assert "per_page=50" in captured["url"]


def test_client_returns_generic_transport_error(monkeypatch):
    def fake_open(request, timeout):
        raise TimeoutError("contains internal details")

    monkeypatch.setattr(urllib.request, "urlopen", fake_open)
    with pytest.raises(GitHubReadError, match="TimeoutError") as error:
        GitHubReadOnlyClient("token").repository_metadata()
    assert "internal details" not in str(error.value)
