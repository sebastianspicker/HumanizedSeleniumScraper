from __future__ import annotations

from humanized_selenium_scraper.spec import SearchSpec


def test_searchspec_from_toml_overrides(tmp_path) -> None:
    toml_content = """
[selenium]
google_domain = "google.com"
restart_threshold = 10
max_retries = 5

[search]
query_template = "{name} {city} kontakt"
extract_phone = false
extract_email = true

[relevance]
keyword_templates = ["{name}", "kontakt"]
min_total_keyword_hits = 2
require_address = false

[url_filter]
domain_match = "any"
allowed_tlds = [".com", ".org"]
domain_keyword_blacklist = ["facebook"]
min_query_part_len = 4

[navigation]
max_google_results = 5
max_links_per_page = 10
subpage_depth = 1
"""
    path = tmp_path / "spec.toml"
    path.write_text(toml_content, encoding="utf-8")

    spec, config = SearchSpec.from_toml(path)
    assert config.google_domain == "google.com"
    assert config.restart_threshold == 10
    assert config.max_retries == 5

    assert spec.query_template == "{name} {city} kontakt"
    assert spec.extract_phone is False
    assert spec.extract_email is True

    assert spec.relevance.keyword_templates == ("{name}", "kontakt")
    assert spec.relevance.min_total_keyword_hits == 2
    assert spec.relevance.require_address is False

    assert spec.url_filter.domain_match == "any"
    assert spec.url_filter.allowed_tlds == (".com", ".org")
    assert spec.url_filter.domain_keyword_blacklist == ("facebook",)
    assert spec.url_filter.min_query_part_len == 4

    assert spec.navigation.max_google_results == 5
    assert spec.navigation.max_links_per_page == 10
    assert spec.navigation.subpage_depth == 1


def test_searchspec_from_toml_single_string_list_fields(tmp_path) -> None:
    """Single string in TOML for list fields becomes one-element tuple, not tuple of chars."""
    toml_content = """
[search]
query_template = "{name}"

[relevance]
keyword_templates = "{name}"

[url_filter]
allowed_tlds = ".de"
domain_keyword_blacklist = "facebook"
"""
    path = tmp_path / "spec.toml"
    path.write_text(toml_content, encoding="utf-8")

    spec, _ = SearchSpec.from_toml(path)
    assert spec.relevance.keyword_templates == ("{name}",)
    assert spec.url_filter.allowed_tlds == (".de",)
    assert spec.url_filter.domain_keyword_blacklist == ("facebook",)
