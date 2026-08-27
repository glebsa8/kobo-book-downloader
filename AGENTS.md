# Project agent guide

- Use `uv` for Python versions, dependency management, commands, builds, and tests. The project-local cache is configured in `pyproject.toml`.
- Keep direct dependencies pinned in `pyproject.toml` and commit the matching `uv.lock` file.
- Keep application code in focused modules under `kobo_book_downloader`; do not collapse it into a single script.
- Preserve the existing `requests` and `argparse` integrations unless a task deliberately migrates them. For new standalone integrations, prefer `httpx`, `typer`, `pydantic`, `polars`, and `loguru` where they fit.
- Add or update tests for behavior changes. Run `make test` for normal checks and `make validate` before release-oriented changes.
- Keep the README and Docker examples aligned with the actual CLI.
- Never commit Kobo tokens, user keys, downloaded books, or local configuration directories.
