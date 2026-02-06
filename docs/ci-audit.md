# CI Audit

Date: 2026-02-06

## Inventory (pre-change)
- Workflow: `.github/workflows/ci.yml`
- Triggers: `push` on all branches, `pull_request`
- Jobs:
  - `lint-test` (matrix: Python 3.10/3.11/3.12)
    - `ruff format --check`, `ruff check`, `mypy`, `pytest`
  - `security`
    - `gitleaks` (working tree scan)
    - `pip-audit -r requirements.txt`
    - `bandit -r humanized_selenium_scraper`
- Permissions: `contents: read`
- Caching: none
- Timeouts: none
- Concurrency: none

## Recent Runs
- GitHub Actions API shows 1 run (2026-02-05) with conclusion `success`.
- No failed runs were found to extract root-cause logs.

## Root Cause / Fix Plan Table
| Workflow | Failure(s) | Root Cause | Fix Plan | Risk | How to Verify |
| --- | --- | --- | --- | --- | --- |
| CI | None observed | Missing CI hardening (timeouts, caching, concurrency). Dependency audit on PRs can cause nondeterministic failures due to newly disclosed CVEs. | Implemented: timeouts, pip cache, concurrency. Moved dependency audit to scheduled workflow; keep static security checks on PRs. | Low risk; changes are CI-only. | Run `CI` on PR and `Security Audit` on schedule/dispatch. |
