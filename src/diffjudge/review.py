"""Orchestration: fetch a PR diff, ask the model, return the review markdown."""

from __future__ import annotations

from typing import Optional, Tuple

from . import github, llm, prompts

DEFAULT_MAX_DIFF_BYTES = 60_000
COMMENT_HEADER = "## diffjudge review\n\n"


def truncate_diff(diff: str, max_bytes: int) -> Tuple[str, bool]:
    """Truncate a diff to at most ``max_bytes`` UTF-8 bytes.

    Returns the (possibly shortened) text and whether truncation happened.
    """
    encoded = diff.encode("utf-8")
    if len(encoded) <= max_bytes:
        return diff, False
    clipped = encoded[:max_bytes].decode("utf-8", "ignore")
    return clipped, True


def review_pr(
    repo: str,
    pr: int,
    *,
    model: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    github_token: Optional[str] = None,
    max_diff_bytes: int = DEFAULT_MAX_DIFF_BYTES,
) -> str:
    """Produce a markdown review for a pull request."""
    diff = github.get_pr_diff(repo, pr, token=github_token)
    if not diff.strip():
        return "_diffjudge: this pull request has an empty diff, nothing to review._"

    title = github.get_pr_title(repo, pr, token=github_token)
    text, truncated = truncate_diff(diff, max_diff_bytes)
    messages = prompts.build_messages(text, title=title, truncated=truncated)
    return llm.chat_completion(
        messages, model=model, api_key=api_key, base_url=base_url
    )


def format_comment(review: str) -> str:
    """Wrap a review in the comment header used when posting to a PR."""
    return COMMENT_HEADER + review.strip() + "\n"
