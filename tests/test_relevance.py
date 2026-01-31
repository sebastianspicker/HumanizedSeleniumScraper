from humanized_selenium_scraper.relevance import (
    address_score,
    evaluate_page,
    normalize_address_part,
)


def test_normalize_address_part_umlauts_and_strasse() -> None:
    assert normalize_address_part("Müllerstraße 1") == "mullerstraße 1"
    assert normalize_address_part("Mullerstr. 1") == "mullerstraße 1"
    assert normalize_address_part("Mullerstrasse 1") == "mullerstraße 1"


def test_address_score_zip_city_street() -> None:
    html = "Kontakt: Musterstraße 12, 12345 Berlin"
    assert address_score(html, "Musterstraße 12", "12345", "Berlin") == 3


def test_evaluate_page_threshold() -> None:
    html = "Kontakt Kontakt Kontakt Kontakt Kontakt Kontakt Musterstraße 12 12345 Berlin"
    assert (
        evaluate_page(
            html,
            keywords=["kontakt"],
            min_keyword_hits=6,
            require_address=True,
            street="Musterstraße 12",
            plz="12345",
            city="Berlin",
            address_min_score=2,
        )
        is True
    )
