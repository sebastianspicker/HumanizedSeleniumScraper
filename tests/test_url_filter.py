from humanized_selenium_scraper.url_filter import is_relevant_url


def test_is_relevant_url_filters_blacklist() -> None:
    assert is_relevant_url("firma berlin", "https://www.facebook.com/firma") is False


def test_is_relevant_url_requires_tld_and_query_part() -> None:
    assert is_relevant_url("firma berlin", "https://example.invalid/") is False
    assert is_relevant_url("firma berlin", "https://firma-berlin.de/kontakt") is True
