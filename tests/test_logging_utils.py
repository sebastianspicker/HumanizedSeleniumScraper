from humanized_selenium_scraper.logging_utils import redact_query


def test_redact_query_does_not_include_input() -> None:
    query = "ACME Musterstraße 12 12345 Berlin kontakt"
    redacted = redact_query(query)
    assert query not in redacted
    assert "len=" in redacted
    assert "tokens=" in redacted


def test_redact_query_empty() -> None:
    redacted = redact_query("")
    assert redacted == "<redacted len=0 tokens=0>"
