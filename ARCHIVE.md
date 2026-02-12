# Archive Status

This repository was cleaned up for archiving (as of 2026-02-12).

## Contents

- **Runnable code:** Package `humanized_selenium_scraper/`, entrypoint `HumanizedSeleniumScraper.py`, tests in `tests/`, example spec `example_search_spec.toml`.
- **Minimal documentation:** `README.md` (usage, configuration, validation), `SECURITY.md` (responsible disclosure), `LICENSE`.

## Removed (WIP / process)

- `.github/` (CI, security workflow, issue/PR templates)
- `CONTRIBUTING.md`
- `docs/` (ci.md, RUNBOOK.md, REPO_MAP.md)
- `archive/` (removed entirely)

## Validation

See README, “Development & validation” section. Short version:

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e ".[dev]"

# Build (optional)
python -m build

# Format & lint
ruff format . && ruff check .

# Types
mypy humanized_selenium_scraper

# Tests
pytest -q

# Run (example)
python -m humanized_selenium_scraper --help
```

## License

Unchanged; see `LICENSE`.
