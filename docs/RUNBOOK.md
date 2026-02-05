# RUNBOOK

## Setup

Prereqs:
- Python 3.10+
- Chrome or Chromium installed (Selenium Manager will fetch a compatible driver at runtime).

Create and activate a virtualenv, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# Windows: .venv\Scripts\activate

python -m pip install -e ".[dev]"
```

Runtime-only install (if you do not need lint/tests):

```bash
python -m pip install -r requirements.txt
```

## Format

```bash
ruff format .
```

## Lint

```bash
ruff check .
```

## Typecheck

```bash
mypy humanized_selenium_scraper
```

## Tests

```bash
pytest -q
```

## Build (optional)

This project uses setuptools. If you have `build` installed:

```bash
python -m build
```

## Security (baseline)

CI runs a secret scan and dependency audit. To run locally:

```bash
# Secret scan (gitleaks)
gitleaks detect --source . --no-git --redact

# Dependency audit (pip-audit)
pip-audit -r requirements.txt

# SAST (bandit)
bandit -r humanized_selenium_scraper -x tests --severity-level medium
```

## Fast loop

```bash
ruff format .
ruff check .
pytest -q
```

## Full loop

```bash
ruff format .
ruff check .
mypy humanized_selenium_scraper
pytest -q
```

## Troubleshooting

- Selenium driver issues:
  - Ensure Chrome/Chromium is installed and on PATH.
  - If Selenium Manager cannot fetch a driver, install a compatible ChromeDriver and ensure it is on PATH.
- Tests are offline by design and should not launch a browser. If a test tries to access the network, treat it as a regression.
