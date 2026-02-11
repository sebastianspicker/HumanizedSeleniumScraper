# HumanizedSeleniumScraper

Human-like Google search scraping with Selenium. The scraper reads CSV rows, builds a query, searches Google, evaluates relevance, optionally explores subpages on the same domain, and extracts phone/email signals.

## Features

- Human-like typing, pauses, and scrolling
- Cookie banner handling with fallback selectors
- URL filtering (TLD allowlist, domain keyword blacklist, query-part matching)
- Relevance scoring with keywords and optional address matching
- Subpage BFS on the same domain
- Phone and email extraction (including basic obfuscation patterns)
- Retry logic with skip-on-repeated-failure
- Incremental CSV output (header written once, rows appended)

## Requirements

- Python 3.10+
- Chrome/Chromium installed (Selenium Manager will fetch a compatible driver at runtime)
- Network access (Google + target sites)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# Windows: .venv\Scripts\activate

python -m pip install -r requirements.txt
```

Development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Quickstart

Headerless CSV with default columns (`name`, `street`, `plz`, `city`; use `zip` or `postal_code` if you prefer):

```bash
python -m humanized_selenium_scraper --input input.csv --output output.csv
```

CSV with header row:

```bash
python -m humanized_selenium_scraper --header --input input.csv --output output.csv
```

Keywords preset (columns `query,keyword`):

```bash
python -m humanized_selenium_scraper --preset keywords --columns query,keyword --input input.csv
```

TOML spec file (see `example_search_spec.toml`):

```bash
python -m humanized_selenium_scraper --spec example_search_spec.toml --header --input input.csv
```

For all CLI options:

```bash
python -m humanized_selenium_scraper --help
```

## Configuration

You can configure behavior via CLI flags or a TOML spec file:

- `--google-domain` to set the Google TLD (e.g., `google.com`)
- `--query-template` and `--keyword-template` to shape queries and relevance checks
- `--require-address` / `--no-require-address` to enable/disable address matching
- URL filtering and navigation settings via `--spec`

The spec file supports these sections:

- `[selenium]`: `google_domain`, `restart_threshold`, `max_retries`
- `[search]`: `query_template`, `extract_phone`, `extract_email`
- `[relevance]`: keyword templates and thresholds
- `[url_filter]`: domain match, TLD allowlist, blacklist
- `[navigation]`: Google result count, per-page links, BFS depth

Refer to `example_search_spec.toml` for a full example.

## Output

- Output columns are the input columns plus `Website`, `Phone`, `Email`.
- The output file is created/overwritten on the first row and then appended per row.
- For empty input files, no output is written.

## Logging & Privacy

- Logs are written to `scraper.log`.
- Query contents are redacted in logs (length and token count only).
- Output data may include phone/email; handle it according to your privacy requirements.

## Development

Fast loop:

```bash
ruff format .
ruff check .
pytest -q
```

Type checking:

```bash
mypy humanized_selenium_scraper
```

Tests are offline by design and should not launch a browser.

See `CONTRIBUTING.md` for contributor guidelines and `docs/RUNBOOK.md` for the full command set.

## Security

CI runs:
- Secret scan: gitleaks
- Dependency audit: pip-audit
- SAST: bandit (medium+ severity)

See `docs/RUNBOOK.md` for local commands.

For responsible disclosure, see `SECURITY.md`.

## Troubleshooting

- Driver issues: ensure Chrome/Chromium is installed and on PATH. If Selenium Manager fails, install a compatible ChromeDriver and add it to PATH.
- Captchas/throttling: increase delays, reduce query volume, and keep concurrency low.
- Cookie banners: update selectors in `click_cookie_consent_if_present()` if needed, including iframe handling.
- Element not interactable: use waits and the robust click helper (`click_element_robust`).
- Timeouts: increase page load timeout or reduce BFS depth/links per page.

## Disclaimer

Automated scraping of Google may violate Google’s Terms of Service. Use responsibly and ensure you have permission to scrape target sites. This project is for educational purposes and does not provide any guarantee of success or access.

## License

See `LICENSE`.
