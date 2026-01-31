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
pytest -q
```

## Commit checklist

- No generated files committed (`*.egg-info/`, `.ruff_cache/`, `.pytest_cache/`, `chrome_profile/`, `scraper.log`)
- `ruff check .` and `pytest -q` are green
