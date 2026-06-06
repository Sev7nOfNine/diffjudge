"""Minimal client for OpenAI-compatible chat-completion APIs, using only stdlib.

Works against the OpenAI API, OpenRouter, a local llama.cpp server, or anything
else exposing a ``/chat/completions`` endpoint.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

Message = Dict[str, str]
Opener = Callable[..., Any]


class LLMError(RuntimeError):
    """Raised when the LLM request fails or returns an unexpected shape."""


def extract_message(data: Dict[str, Any]) -> str:
    """Pull the assistant message text out of a chat-completions response."""
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise LLMError(
            "unexpected LLM response shape: {0}".format(json.dumps(data)[:300])
        )
    if not isinstance(content, str):
        raise LLMError("LLM returned non-text content")
    return content.strip()


def chat_completion(
    messages: List[Message],
    *,
    model: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    temperature: float = 0.2,
    timeout: int = 120,
    opener: Optional[Opener] = None,
) -> str:
    """Call an OpenAI-compatible chat-completions endpoint and return the text."""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature}
    ).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + api_key)

    do_open = opener or urllib.request.urlopen
    try:
        with do_open(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise LLMError(
            "LLM request failed (HTTP {0}): {1}".format(exc.code, body[:500])
        )
    except urllib.error.URLError as exc:
        raise LLMError("LLM request failed: {0}".format(exc.reason))

    return extract_message(json.loads(raw))
