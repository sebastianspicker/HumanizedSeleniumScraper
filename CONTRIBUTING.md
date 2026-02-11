# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# Windows: .venv\\Scripts\\activate

python -m pip install -e ".[dev]"
```

## Quality gates

```bash
ruff format .
ruff check .
mypy humanized_selenium_scraper
pytest -q
bandit -r humanized_selenium_scraper -x tests --severity-level medium
pip-audit -r requirements.txt
```

## Commit checklist

- No generated files committed (`*.egg-info/`, `.ruff_cache/`, `.pytest_cache/`, `chrome_profile/`, `scraper.log`, `input.csv`, `output.csv`)
- `ruff check .`, `mypy humanized_selenium_scraper`, `pytest -q` are green
