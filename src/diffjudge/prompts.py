"""Prompt construction for the reviewer."""

from __future__ import annotations

from typing import Dict, List, Optional

Message = Dict[str, str]

SYSTEM_PROMPT = (
    "You are a meticulous senior software engineer reviewing a pull request. "
    "Review the unified diff and give a focused, useful review.\n\n"
    "Priorities, in order:\n"
    "1. Correctness bugs and logic errors introduced by the change.\n"
    "2. Security issues (injection, auth, secrets, unsafe input handling).\n"
    "3. Missing edge cases, error handling, or tests for new behavior.\n"
    "4. Clear, concrete improvements.\n\n"
    "Rules:\n"
    "- Be specific: reference file names and, where you can, the relevant lines.\n"
    "- Do not nitpick formatting or style unless it affects correctness.\n"
    "- Do not invent issues. If the change looks good, say so plainly.\n"
    "- Keep it concise. No filler.\n\n"
    "Respond in GitHub-flavored markdown with exactly these sections:\n"
    "## Summary\n"
    "A two or three sentence overview of what the PR does.\n\n"
    "## Findings\n"
    "A bullet list of concrete issues, each prefixed with a severity "
    "(**blocker** / **major** / **minor** / **nit**). Write 'No significant "
    "issues found.' if there are none.\n\n"
    "## Suggestions\n"
    "Optional improvements that are nice-to-have, or 'None.'"
)


def build_messages(
    diff: str, *, title: Optional[str] = None, truncated: bool = False
) -> List[Message]:
    """Build the chat messages for reviewing a diff."""
    header = "Pull request"
    if title:
        header += ': "{0}"'.format(title)

    note = ""
    if truncated:
        note = (
            "\n\nNote: the diff was truncated because it is large. Review what is "
            "shown and say so if you cannot assess the whole change."
        )

    user = "{0}\n\nUnified diff:\n\n```diff\n{1}\n```{2}".format(header, diff, note)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
