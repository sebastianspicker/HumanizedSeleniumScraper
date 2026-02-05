from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

from .config import ScraperConfig
from .url_filter import DEFAULT_ALLOWED_TLDS, DEFAULT_DOMAIN_KEYWORD_BLACKLIST


@dataclass(frozen=True)
class AddressSpec:
    street_field: str = "street"
    zip_field: str = "plz"
    city_field: str = "city"
    min_score: int = 2


@dataclass(frozen=True)
class UrlFilterSpec:
    domain_match: str = "query_part"  # "query_part" | "any"
    allowed_tlds: tuple[str, ...] = DEFAULT_ALLOWED_TLDS
    domain_keyword_blacklist: tuple[str, ...] = DEFAULT_DOMAIN_KEYWORD_BLACKLIST
    min_query_part_len: int = 3


@dataclass(frozen=True)
class NavigationSpec:
    max_google_results: int = 20
    max_links_per_page: int = 30
    subpage_depth: int = 2


@dataclass(frozen=True)
class RelevanceSpec:
    keyword_templates: tuple[str, ...] = ("{name}", "kontakt", "adresse")
    min_total_keyword_hits: int = 6
    require_address: bool = True
    address: AddressSpec = field(default_factory=AddressSpec)


@dataclass(frozen=True)
class SearchSpec:
    query_template: str = "{name} {street} {plz} {city}"
    relevance: RelevanceSpec = field(default_factory=RelevanceSpec)
    url_filter: UrlFilterSpec = field(default_factory=UrlFilterSpec)
    navigation: NavigationSpec = field(default_factory=NavigationSpec)
    extract_phone: bool = True
    extract_email: bool = True

    @staticmethod
    def presets() -> dict[str, SearchSpec]:
        return {
            "contact": SearchSpec(),
            "keywords": SearchSpec(
                query_template="{query}",
                relevance=RelevanceSpec(
                    keyword_templates=("{keyword}",),
                    min_total_keyword_hits=1,
                    require_address=False,
                ),
                url_filter=UrlFilterSpec(domain_match="any"),
            ),
        }

    @classmethod
    def from_toml(cls, path: Path) -> tuple[SearchSpec, ScraperConfig]:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        search_data = _as_dict(data.get("search", {}))
        relevance_data = _as_dict(search_data.pop("relevance", data.get("relevance", {})))
        url_filter_data = _as_dict(search_data.pop("url_filter", data.get("url_filter", {})))
        navigation_data = _as_dict(search_data.pop("navigation", data.get("navigation", {})))

        address_data = _as_dict(relevance_data.pop("address", data.get("address", {})))

        spec = cls(
            query_template=str(search_data.get("query_template", cls().query_template)),
            relevance=RelevanceSpec(
                keyword_templates=tuple(
                    relevance_data.get("keyword_templates", cls().relevance.keyword_templates)
                ),
                min_total_keyword_hits=int(
                    relevance_data.get(
                        "min_total_keyword_hits", cls().relevance.min_total_keyword_hits
                    )
                ),
                require_address=bool(
                    relevance_data.get("require_address", cls().relevance.require_address)
                ),
                address=AddressSpec(
                    street_field=str(
                        address_data.get("street_field", cls().relevance.address.street_field)
                    ),
                    zip_field=str(address_data.get("zip_field", cls().relevance.address.zip_field)),
                    city_field=str(
                        address_data.get("city_field", cls().relevance.address.city_field)
                    ),
                    min_score=int(address_data.get("min_score", cls().relevance.address.min_score)),
                ),
            ),
            url_filter=UrlFilterSpec(
                domain_match=str(
                    url_filter_data.get("domain_match", cls().url_filter.domain_match)
                ),
                allowed_tlds=tuple(
                    url_filter_data.get("allowed_tlds", cls().url_filter.allowed_tlds)
                ),
                domain_keyword_blacklist=tuple(
                    url_filter_data.get(
                        "domain_keyword_blacklist", cls().url_filter.domain_keyword_blacklist
                    )
                ),
                min_query_part_len=int(
                    url_filter_data.get("min_query_part_len", cls().url_filter.min_query_part_len)
                ),
            ),
            navigation=NavigationSpec(
                max_google_results=int(
                    navigation_data.get("max_google_results", cls().navigation.max_google_results)
                ),
                max_links_per_page=int(
                    navigation_data.get("max_links_per_page", cls().navigation.max_links_per_page)
                ),
                subpage_depth=int(
                    navigation_data.get("subpage_depth", cls().navigation.subpage_depth)
                ),
            ),
            extract_phone=bool(search_data.get("extract_phone", cls().extract_phone)),
            extract_email=bool(search_data.get("extract_email", cls().extract_email)),
        )

        scraper_cfg = ScraperConfig.from_mapping(_as_dict(data.get("selenium", {})))
        return spec, scraper_cfg


def render_template(template: str, row: dict[str, str]) -> str:
    try:
        return template.format_map(row)
    except KeyError as exc:
        available = ", ".join(sorted(row.keys()))
        raise ValueError(
            f"Template placeholder {exc!s} not found. Available columns: {available}"
        ) from exc


def render_templates(templates: tuple[str, ...], row: dict[str, str]) -> list[str]:
    return [render_template(t, row) for t in templates]


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
