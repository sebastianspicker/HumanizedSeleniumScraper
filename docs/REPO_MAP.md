# REPO_MAP

## Top-level

- `humanized_selenium_scraper/`: main package
- `HumanizedSeleniumScraper.py`: backward-compatible entrypoint
- `tests/`: offline unit tests
- `example_search_spec.toml`: sample spec configuration
- `pyproject.toml`: packaging, ruff, mypy, pytest config
- `requirements.txt`: runtime dependency (selenium)

## Entry points

- `python -m humanized_selenium_scraper` -> `humanized_selenium_scraper/__main__.py` -> `humanized_selenium_scraper/cli.py:main`
- `python HumanizedSeleniumScraper.py` -> same as above

## Core flow (CLI)

1. `cli.main()` parses arguments and builds a `SearchSpec` + `ScraperConfig`.
2. `cli.run()` reads CSV rows via `io.read_csv_rows()`.
3. `Session.create()` builds a Selenium driver (`driver.create_driver()`).
4. `Session.search()` performs Google search, filters URLs, evaluates relevance, optionally BFS subpages.
5. `extract_selenium.parse_phone_email_deep()` extracts phone/email from DOM + page source.
6. Results are written to CSV incrementally.

## Modules

- `config.py`: `ScraperConfig` defaults, selenium retry config, user agents.
- `spec.py`: `SearchSpec` + TOML loading + template rendering.
- `io.py`: CSV input and column parsing.
- `logging_utils.py`: PII-safe logging helpers.
- `scraper.py`: orchestrates browsing, BFS, relevance evaluation, and extraction.
- `driver.py`: Chrome WebDriver setup (user agent, window size, profile dir).
- `selenium_ops.py`: robust click and `safe_get()` with retries.
- `url_filter.py`: URL allowlist/blacklist + query-part matching.
- `relevance.py`: keyword and address matching logic.
- `extract_text.py`: regex parsing for email/phone/obfuscation.
- `extract_selenium.py`: DOM-based email/phone extraction.
- `human.py`: human-like delays and scrolling.
- `exceptions.py`: `SkipEntryError` for skip control flow.

## Tests

- `tests/test_extract_text.py`: email/phone parsing, obfuscation decode.
- `tests/test_relevance.py`: address normalization and relevance checks.
- `tests/test_spec.py`: template rendering error message.
- `tests/test_io.py`: column parsing validation.
- `tests/test_url_filter.py`: URL filtering behavior.

## Hot spots / risk areas

- Selenium navigation and retries: `scraper.py`, `selenium_ops.py`.
- CSV reading/writing and column mapping: `cli.py`, `io.py`.
- Recursion depth and subpage BFS: `scraper.py`.
- URL filtering heuristics: `url_filter.py`.
