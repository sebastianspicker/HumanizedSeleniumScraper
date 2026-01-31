from __future__ import annotations

from urllib.parse import urlparse

DEFAULT_ALLOWED_TLDS = (
    ".de",
    ".com",
    ".net",
    ".org",
    ".info",
    ".eu",
    ".co",
    ".at",
    ".ch",
    ".shop",
    ".auto",
    ".website",
    ".online",
)

DEFAULT_DOMAIN_KEYWORD_BLACKLIST = (
    "facebook",
    "instagram",
    "linkedin",
    "stepstone",
    "indeed",
    "twitter",
    "xing",
    "karriere",
    "meinestadt",
    "ebay",
    "booking",
    "youtube",
    "pinterest",
    "autoscout",
    "mobile.de",
    "gelbeseiten",
    "dastelefonbuch",
    ".pdf",
)


def is_relevant_url(
    query: str,
    url: str,
    *,
    allowed_tlds: tuple[str, ...] = DEFAULT_ALLOWED_TLDS,
    domain_keyword_blacklist: tuple[str, ...] = DEFAULT_DOMAIN_KEYWORD_BLACKLIST,
    domain_match: str = "query_part",  # "query_part" | "any"
    min_query_part_len: int = 3,
) -> bool:
    url_lower = url.lower()
    if url_lower.startswith(("blob:", "data:")):
        return False
    if url_lower.endswith(".pdf"):
        return False

    netloc = urlparse(url).netloc.lower()
    host = netloc.split("@")[-1].split(":")[0]

    if not any(host.endswith(tld) for tld in allowed_tlds):
        return False
    if any(keyword in host for keyword in domain_keyword_blacklist):
        return False

    if domain_match == "any":
        return True
    if domain_match != "query_part":
        raise ValueError(f"Unknown domain_match mode: {domain_match!r}")

    query_parts = [p for p in query.lower().split() if len(p) >= min_query_part_len]
    return any(part in host for part in query_parts)
