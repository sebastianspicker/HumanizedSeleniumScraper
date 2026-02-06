# CI Guide

## Overview
This repo uses two GitHub Actions workflows:
- `CI` (`.github/workflows/ci.yml`)
  - Triggers: `pull_request`, `push` to `main`, `workflow_dispatch`
  - Jobs:
    - `Lint + Test` (Python 3.10/3.11/3.12): ruff format check, ruff lint, mypy, pytest
    - `Security` (Python 3.12): gitleaks working-tree scan, bandit SAST
- `Security Audit` (`.github/workflows/security.yml`)
  - Triggers: weekly schedule (Monday 06:00 UTC) and `workflow_dispatch`
  - Job: pip-audit dependency audit

## Local Runs
Create/activate a virtual environment and install dev deps:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the same checks as CI:

```bash
make ci
```

Optional security checks:

```bash
make security
make dependency-audit
```

## Secrets & Repo Settings
- No repository secrets are required for CI.
- Default `GITHUB_TOKEN` with `contents: read` is sufficient.

## Adding/Extending Jobs
- Prefer adding new checks to the `CI` workflow if they are fast, deterministic, and do not require secrets.
- Heavy or externally volatile checks belong in scheduled or manual workflows.
- Follow the existing patterns: pin action major versions, add `timeout-minutes`, `concurrency`, and cache language dependencies.

## Optional `act` Usage
You can run workflows locally with `act` if you have it installed. For example:

```bash
act -W .github/workflows/ci.yml
```

Keep in mind that `act` can diverge from GitHub-hosted runners; treat it as a convenience, not a source of truth.
