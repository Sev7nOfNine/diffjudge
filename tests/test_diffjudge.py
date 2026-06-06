"""Offline unit tests for diffjudge. No network: HTTP openers are faked."""

import io
import json

import pytest

from diffjudge import github, llm, prompts
from diffjudge.cli import build_parser
from diffjudge.review import format_comment, truncate_diff


# --- llm ----------------------------------------------------------------------


def test_extract_message_ok():
    data = {"choices": [{"message": {"content": "  hello  "}}]}
    assert llm.extract_message(data) == "hello"


def test_extract_message_bad_shape():
    with pytest.raises(llm.LLMError):
        llm.extract_message({"nope": 1})


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._payload


def test_chat_completion_uses_opener_and_parses():
    captured = {}

    def fake_opener(req, timeout=0):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["auth"] = req.get_header("Authorization")
        return _FakeResponse(
            json.dumps({"choices": [{"message": {"content": "looks good"}}]})
        )

    out = llm.chat_completion(
        [{"role": "user", "content": "hi"}],
        model="gpt-4o-mini",
        api_key="sk-test",
        base_url="https://example.com/v1",
        opener=fake_opener,
    )
    assert out == "looks good"
    assert captured["url"] == "https://example.com/v1/chat/completions"
    assert captured["body"]["model"] == "gpt-4o-mini"
    assert captured["auth"] == "Bearer sk-test"


# --- github -------------------------------------------------------------------


def test_url_builders():
    assert github.pr_url("me/proj", 7) == "https://api.github.com/repos/me/proj/pulls/7"
    assert (
        github.comments_url("me/proj", 7)
        == "https://api.github.com/repos/me/proj/issues/7/comments"
    )


def test_get_pr_diff_sets_diff_accept_header():
    captured = {}

    def fake_opener(req, timeout=0):
        captured["accept"] = req.get_header("Accept")
        return _FakeResponse("diff --git a/x b/x")

    out = github.get_pr_diff("me/proj", 1, token="t", opener=fake_opener)
    assert out.startswith("diff --git")
    assert captured["accept"] == "application/vnd.github.v3.diff"


def test_post_comment_returns_html_url():
    def fake_opener(req, timeout=0):
        assert req.method == "POST"
        return _FakeResponse(json.dumps({"html_url": "https://github.com/c/1"}))

    url = github.post_comment("me/proj", 1, "body", token="t", opener=fake_opener)
    assert url == "https://github.com/c/1"


# --- prompts ------------------------------------------------------------------


def test_build_messages_includes_diff_and_title():
    msgs = prompts.build_messages("diff body", title="Fix bug")
    assert msgs[0]["role"] == "system"
    assert "senior software engineer" in msgs[0]["content"]
    assert "Fix bug" in msgs[1]["content"]
    assert "diff body" in msgs[1]["content"]


def test_build_messages_truncation_note():
    msgs = prompts.build_messages("d", truncated=True)
    assert "truncated" in msgs[1]["content"]


# --- review -------------------------------------------------------------------


def test_truncate_diff_under_limit():
    text, truncated = truncate_diff("abc", 100)
    assert text == "abc"
    assert truncated is False


def test_truncate_diff_over_limit():
    text, truncated = truncate_diff("a" * 200, 50)
    assert truncated is True
    assert len(text.encode("utf-8")) <= 50


def test_format_comment_has_header():
    out = format_comment("  the review  ")
    assert out.startswith("## diffjudge review")
    assert "the review" in out


# --- cli ----------------------------------------------------------------------


def test_parser_requires_repo_and_pr():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_parses_core_args():
    parser = build_parser()
    args = parser.parse_args(["--repo", "me/proj", "--pr", "12", "--post"])
    assert args.repo == "me/proj"
    assert args.pr == 12
    assert args.post is True
