from __future__ import annotations

import argparse
import csv
import logging
import threading
from dataclasses import replace
from pathlib import Path

from .config import ScraperConfig
from .exceptions import SkipEntryError
from .human import random_pause
from .io import parse_columns_arg, read_csv_rows
from .scraper import Session
from .spec import SearchSpec, render_template

write_lock = threading.Lock()


def _write_results(path: Path, *, header: list[str], rows: list[list[str]]) -> None:
    with write_lock:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)


def run(
    *,
    input_file: Path,
    output_file: Path,
    config: ScraperConfig,
    spec: SearchSpec,
    delimiter: str,
    has_header: bool,
    columns: list[str] | None,
) -> int:
    results: list[list[str]] = []
    input_columns = columns or []
    if has_header:
        with input_file.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            header = next(reader, None)
            if not header:
                raise ValueError("Input CSV is empty.")
            input_columns = [h.strip() for h in header if h.strip()]

    out_header = [*input_columns, "Website", "Phone", "Email"]
    session = Session.create(config, profile_dir=config.chrome_profile_root)
    try:
        for row in read_csv_rows(
            input_file, delimiter=delimiter, has_header=has_header, columns=input_columns or columns
        ):
            try:
                query = render_template(spec.query_template, row).strip()
                if not query:
                    raise ValueError("Rendered query is empty.")
                logging.info("Processing query => %s", query)

                found_url, phone, email = session.search(query=query, row=row, spec=spec)
                results.append(
                    [
                        *(row.get(col, "") for col in input_columns),
                        found_url or "",
                        phone or "",
                        email or "",
                    ]
                )
            except SkipEntryError as exc:
                logging.warning("SKIP => %s", exc)
                results.append([*(row.get(col, "") for col in input_columns), "", "", ""])
            except Exception as exc:
                logging.warning("process_row failed: %s", exc)
                results.append([*(row.get(col, "") for col in input_columns), "", "", ""])

            _write_results(output_file, header=out_header, rows=results)
            random_pause(1, 2)
    finally:
        session.close()

    logging.info("All rows done => %s", output_file)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Humanized Selenium scraper (configurable, offline-testable core)."
    )
    parser.add_argument("--input", default="adressen.csv", help="Input CSV path.")
    parser.add_argument("--output", default="ergebnisse.csv", help="Output CSV path.")
    parser.add_argument("--google-domain", help="e.g. google.de or google.com")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter (default: ',').")
    parser.add_argument(
        "--header",
        action="store_true",
        help="Treat the first row as a header (DictReader).",
    )
    parser.add_argument(
        "--columns",
        default="name,street,plz,city",
        help="Column names for headerless CSV (comma-separated).",
    )
    parser.add_argument(
        "--preset",
        choices=sorted(SearchSpec.presets().keys()),
        default="contact",
        help="Built-in use case preset.",
    )
    parser.add_argument("--spec", help="Path to a TOML spec file.")
    parser.add_argument(
        "--query-template",
        help="Python format template, e.g. '{name} {city} kontakt'.",
    )
    parser.add_argument(
        "--keyword-template",
        action="append",
        default=[],
        help="Keyword template(s) for relevance checks (repeatable).",
    )
    parser.add_argument(
        "--min-keyword-hits",
        type=int,
        help="Minimum total keyword hits across all keywords.",
    )
    parser.add_argument(
        "--require-address",
        action="store_true",
        default=None,
        help="Require address match (street/zip/city) for relevance.",
    )
    parser.add_argument(
        "--no-require-address",
        action="store_false",
        dest="require_address",
        default=None,
        help="Disable address requirement (keywords-only relevance).",
    )
    parser.add_argument("--street-field", help="Row column for street (address relevance).")
    parser.add_argument("--zip-field", help="Row column for zip/postal code (address relevance).")
    parser.add_argument("--city-field", help="Row column for city (address relevance).")
    parser.add_argument("--address-min-score", type=int, help="Minimum address score (default: 2).")
    parser.add_argument(
        "--domain-match",
        choices=["query_part", "any"],
        help=(
            "URL filter: require query part in domain or accept any domain "
            "(still TLD+blacklist filtered)."
        ),
    )
    parser.add_argument(
        "--allowed-tld",
        action="append",
        default=[],
        help="Allowed TLD (repeatable), e.g. --allowed-tld .de --allowed-tld .com",
    )
    parser.add_argument(
        "--blacklist-domain-keyword",
        action="append",
        default=[],
        help="Domain blacklist keyword (repeatable), e.g. --blacklist-domain-keyword facebook",
    )
    parser.add_argument(
        "--min-domain-query-part-len",
        type=int,
        help="Ignore query tokens shorter than this when domain_match=query_part.",
    )
    parser.add_argument(
        "--max-google-results", type=int, help="How many Google result links to scan."
    )
    parser.add_argument(
        "--max-links-per-page", type=int, help="How many <a> links to scan on a page."
    )
    parser.add_argument("--subpage-depth", type=int, help="Subpage BFS depth (0 disables).")
    parser.add_argument("--no-phone", action="store_true", help="Do not extract phone numbers.")
    parser.add_argument("--no-email", action="store_true", help="Do not extract emails.")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        filename="scraper.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    spec = SearchSpec.presets()[args.preset]
    config = ScraperConfig(google_domain=args.google_domain or "google.de")

    if args.spec:
        spec, config_from_spec = SearchSpec.from_toml(Path(args.spec))
        config = replace(
            config_from_spec, google_domain=args.google_domain or config_from_spec.google_domain
        )

    if args.query_template:
        spec = replace(spec, query_template=args.query_template)

    if args.keyword_template:
        spec = replace(
            spec, relevance=replace(spec.relevance, keyword_templates=tuple(args.keyword_template))
        )

    if args.min_keyword_hits is not None:
        spec = replace(
            spec,
            relevance=replace(spec.relevance, min_total_keyword_hits=args.min_keyword_hits),
        )

    if args.domain_match is not None:
        spec = replace(spec, url_filter=replace(spec.url_filter, domain_match=args.domain_match))

    if args.require_address is not None:
        spec = replace(
            spec, relevance=replace(spec.relevance, require_address=args.require_address)
        )

    if args.street_field or args.zip_field or args.city_field or args.address_min_score is not None:
        address = spec.relevance.address
        address = replace(
            address,
            street_field=args.street_field or address.street_field,
            zip_field=args.zip_field or address.zip_field,
            city_field=args.city_field or address.city_field,
            min_score=args.address_min_score
            if args.address_min_score is not None
            else address.min_score,
        )
        spec = replace(spec, relevance=replace(spec.relevance, address=address))

    if args.allowed_tld:
        spec = replace(
            spec, url_filter=replace(spec.url_filter, allowed_tlds=tuple(args.allowed_tld))
        )
    if args.blacklist_domain_keyword:
        spec = replace(
            spec,
            url_filter=replace(
                spec.url_filter, domain_keyword_blacklist=tuple(args.blacklist_domain_keyword)
            ),
        )
    if args.min_domain_query_part_len is not None:
        spec = replace(
            spec,
            url_filter=replace(spec.url_filter, min_query_part_len=args.min_domain_query_part_len),
        )

    if (
        args.max_google_results is not None
        or args.max_links_per_page is not None
        or args.subpage_depth is not None
    ):
        nav = spec.navigation
        nav = replace(
            nav,
            max_google_results=args.max_google_results
            if args.max_google_results is not None
            else nav.max_google_results,
            max_links_per_page=args.max_links_per_page
            if args.max_links_per_page is not None
            else nav.max_links_per_page,
            subpage_depth=args.subpage_depth
            if args.subpage_depth is not None
            else nav.subpage_depth,
        )
        spec = replace(spec, navigation=nav)

    if args.no_phone:
        spec = replace(spec, extract_phone=False)
    if args.no_email:
        spec = replace(spec, extract_email=False)

    columns = parse_columns_arg(args.columns) if not args.header else None
    return run(
        input_file=Path(args.input),
        output_file=Path(args.output),
        config=config,
        spec=spec,
        delimiter=args.delimiter,
        has_header=args.header,
        columns=columns,
    )
