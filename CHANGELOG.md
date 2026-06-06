# Changelog

## v0.1.0

### Features
- review a pull request diff with any OpenAI-compatible model
- post the review back to the PR as a comment, or print it to stdout
- provider-agnostic: OpenAI, OpenRouter, or a local llama.cpp server via `--base-url`
- ship as a composite GitHub Action for one-step CI integration
- truncate oversized diffs with `--max-diff-bytes`
- zero runtime dependencies (standard library only)

Initial release.
