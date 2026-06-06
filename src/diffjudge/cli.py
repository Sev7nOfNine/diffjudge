"""Command-line interface for diffjudge."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import __version__, github
from .llm import LLMError
from .github import GitHubError
from .review import DEFAULT_MAX_DIFF_BYTES, format_comment, review_pr


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diffjudge",
        description="AI-powered pull request reviewer.",
    )
    parser.add_argument(
        "--repo",
        required=True,
        metavar="OWNER/NAME",
        help="GitHub repository slug, e.g. octocat/hello-world.",
    )
    parser.add_argument(
        "--pr",
        required=True,
        type=int,
        metavar="N",
        help="pull request number to review.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("DIFFJUDGE_MODEL", "gpt-4o-mini"),
        metavar="NAME",
        help="model name (default: gpt-4o-mini, or $DIFFJUDGE_MODEL).",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        metavar="URL",
        help="OpenAI-compatible base URL (default: $OPENAI_BASE_URL or OpenAI).",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY"),
        metavar="KEY",
        help="LLM API key (default: $OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        metavar="TOKEN",
        help="GitHub token for fetching the diff and posting (default: $GITHUB_TOKEN).",
    )
    parser.add_argument(
        "--max-diff-bytes",
        type=int,
        default=DEFAULT_MAX_DIFF_BYTES,
        metavar="N",
        help="truncate diffs larger than this many bytes (default: {0}).".format(
            DEFAULT_MAX_DIFF_BYTES
        ),
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="post the review as a PR comment instead of printing it.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {0}".format(__version__),
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.api_key:
        parser.exit(2, "diffjudge: no API key (set $OPENAI_API_KEY or --api-key)\n")
    if args.post and not args.github_token:
        parser.exit(2, "diffjudge: --post needs a GitHub token (set $GITHUB_TOKEN)\n")

    try:
        review = review_pr(
            args.repo,
            args.pr,
            model=args.model,
            api_key=args.api_key,
            base_url=args.base_url,
            github_token=args.github_token,
            max_diff_bytes=args.max_diff_bytes,
        )
    except (LLMError, GitHubError) as exc:
        parser.exit(1, "diffjudge: {0}\n".format(exc))

    if args.post:
        try:
            url = github.post_comment(
                args.repo, args.pr, format_comment(review), token=args.github_token
            )
        except GitHubError as exc:
            parser.exit(1, "diffjudge: {0}\n".format(exc))
        sys.stderr.write("diffjudge: posted review -> {0}\n".format(url))
    else:
        sys.stdout.write(review.rstrip() + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
