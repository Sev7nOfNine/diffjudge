# diffjudge

**AI-powered pull request reviewer — with zero dependencies.**

`diffjudge` fetches a pull request's diff, asks a language model to review it, and
either prints the review or posts it back as a PR comment. It works with any
OpenAI-compatible API: the OpenAI platform, OpenRouter, or a local
`llama.cpp` / Ollama server. The whole thing is built on the Python standard
library — no `requests`, no SDKs, nothing to audit but a few hundred lines.

Use it as a CLI for ad-hoc reviews, or drop the bundled GitHub Action into a
workflow to get an automatic review on every pull request.

## What a review looks like

```markdown
## diffjudge review

## Summary
Adds retry handling to the upload client and a backoff helper.

## Findings
- **major** `client.py`: the retry loop never breaks on a 4xx response, so a bad
  request is retried 5 times before failing.
- **minor** `client.py`: `backoff()` ignores the `jitter` argument.

## Suggestions
- Consider adding a test for the 4xx-no-retry path.
```

## Install

```bash
pip install diffjudge
# or, for an isolated CLI:
pipx install diffjudge
```

Requires Python 3.8+.

## CLI usage

```bash
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...        # only needed to fetch private diffs or to --post

# Print a review to your terminal
diffjudge --repo octocat/hello-world --pr 42

# Post the review as a comment on the PR
diffjudge --repo octocat/hello-world --pr 42 --post

# Use a different model or provider
diffjudge --repo octocat/hello-world --pr 42 --model gpt-4o
diffjudge --repo me/proj --pr 7 --base-url http://localhost:8080/v1 --model local-model
```

### Options

| Flag | Description |
| --- | --- |
| `--repo OWNER/NAME` | Repository to review (required). |
| `--pr N` | Pull request number (required). |
| `--model NAME` | Model name (default `gpt-4o-mini`, or `$DIFFJUDGE_MODEL`). |
| `--base-url URL` | OpenAI-compatible base URL (default `$OPENAI_BASE_URL` or OpenAI). |
| `--api-key KEY` | LLM API key (default `$OPENAI_API_KEY`). |
| `--github-token TOKEN` | GitHub token (default `$GITHUB_TOKEN`). |
| `--max-diff-bytes N` | Truncate diffs larger than this (default 60000). |
| `--post` | Post the review as a PR comment instead of printing it. |

## GitHub Action

Add a workflow that reviews every pull request. Store your provider key as a
repository secret (e.g. `OPENAI_API_KEY`):

```yaml
name: diffjudge
on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: Sev7nOfNine/diffjudge@v0.1.0
        with:
          api-key: ${{ secrets.OPENAI_API_KEY }}
          model: gpt-4o-mini
```

Point `base-url` at any OpenAI-compatible endpoint to use a different provider or
a self-hosted model.

## Privacy note

`diffjudge` sends the pull request diff to whatever provider you configure. Only
point it at providers you trust with your code, and prefer a self-hosted model
(`--base-url`) for private repositories where that matters.

## Development

```bash
pip install -e ".[test]"
python -m pytest
```

The HTTP layers accept an injectable opener, so the whole suite runs offline
with no real API calls.

## License

MIT — see [LICENSE](LICENSE).
