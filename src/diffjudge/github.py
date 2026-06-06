"""Tiny GitHub REST client (stdlib only): fetch a PR diff and post a comment."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

API_ROOT = "https://api.github.com"
Opener = Callable[..., Any]


class GitHubError(RuntimeError):
    """Raised when a GitHub API request fails."""


def pr_url(repo: str, pr: int) -> str:
    return "{0}/repos/{1}/pulls/{2}".format(API_ROOT, repo, pr)


def comments_url(repo: str, pr: int) -> str:
    return "{0}/repos/{1}/issues/{2}/comments".format(API_ROOT, repo, pr)


def _request(
    url: str,
    *,
    token: Optional[str] = None,
    method: str = "GET",
    accept: str = "application/vnd.github+json",
    data: Optional[bytes] = None,
    opener: Optional[Opener] = None,
    timeout: int = 60,
) -> bytes:
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "diffjudge")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if data is not None:
        req.add_header("Content-Type", "application/json")

    do_open = opener or urllib.request.urlopen
    try:
        with do_open(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise GitHubError(
            "GitHub API error (HTTP {0}): {1}".format(exc.code, body[:300])
        )
    except urllib.error.URLError as exc:
        raise GitHubError("GitHub request failed: {0}".format(exc.reason))


def get_pr_diff(
    repo: str, pr: int, *, token: Optional[str] = None, opener: Optional[Opener] = None
) -> str:
    """Return the unified diff for a pull request."""
    raw = _request(
        pr_url(repo, pr),
        token=token,
        accept="application/vnd.github.v3.diff",
        opener=opener,
    )
    return raw.decode("utf-8", "replace")


def get_pr_title(
    repo: str, pr: int, *, token: Optional[str] = None, opener: Optional[Opener] = None
) -> str:
    """Return the pull request title (best effort, empty string on absence)."""
    raw = _request(pr_url(repo, pr), token=token, opener=opener)
    data = json.loads(raw.decode("utf-8"))
    return data.get("title", "") or ""


def post_comment(
    repo: str,
    pr: int,
    body: str,
    *,
    token: str,
    opener: Optional[Opener] = None,
) -> str:
    """Post a comment on a pull request, returning the created comment URL."""
    payload = json.dumps({"body": body}).encode("utf-8")
    raw = _request(
        comments_url(repo, pr),
        token=token,
        method="POST",
        data=payload,
        opener=opener,
    )
    return json.loads(raw.decode("utf-8")).get("html_url", "")
