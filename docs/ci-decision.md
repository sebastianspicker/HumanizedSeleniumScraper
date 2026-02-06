# CI Decision

Date: 2026-02-06

## Decision
FULL CI for core quality gates on `push` to `main` and on `pull_request`, plus a scheduled security audit workflow.

## Rationale
- The repo is a Python library with unit tests and static checks that are fast and deterministic.
- No jobs require production secrets or live infrastructure access.
- Selenium runtime/browser integration is not exercised in tests, so CI can run on GitHub-hosted runners.
- Dependency vulnerability checks can fail due to newly disclosed CVEs outside code changes, so they run on a schedule (not on every PR) to keep PR CI stable and actionable.

## What Runs Where
- `pull_request`:
  - Ruff format check
  - Ruff lint
  - Mypy type check
  - Pytest
  - Gitleaks (working tree scan)
  - Bandit SAST
- `push` to `main`:
  - Same as `pull_request`
- `schedule` (weekly) and `workflow_dispatch`:
  - pip-audit dependency audit

## Threat Model (CI)
- PRs from forks are untrusted; no secrets are used and `pull_request` is used (not `pull_request_target`).
- Workflow permissions are set to `contents: read` and do not require write scopes.
- Gitleaks scans only the checked-out working tree (`--no-git`) to avoid history scans on untrusted PRs.

## If We Later Want “Fuller” CI
- Add a dependency lockfile (via `uv` or `pip-tools`) and switch CI installs to `--frozen`/locked mode.
- Add integration tests that run Selenium against a browser (likely via self-hosted runners or containerized browsers).
- Add secrets-backed integration tests only on `push` to `main` or `workflow_dispatch` with explicit guards.
