from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScraperConfig:
    google_domain: str = "google.com"
    restart_threshold: int = 30
    max_retries: int = 3

    user_agents: list[str] = field(
        default_factory=lambda: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/110.0.5481.100 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; rv:117.0) Gecko/20100101 Firefox/117.0",
            "Mozilla/5.0 (X11; Linux i686; rv:88.0) Gecko/20100101 Firefox/88.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/16.0 Safari/605.1.15",
        ]
    )
    window_sizes: list[tuple[int, int]] = field(
        default_factory=lambda: [
            (1280, 720),
            (1366, 768),
            (1920, 1080),
            (1536, 864),
            (1440, 900),
            (1600, 900),
        ]
    )

    chrome_profile_root: Path = Path("chrome_profile")
    page_load_timeout_s: int = 20
    implicit_wait_s: int = 5

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ScraperConfig:
        if not data:
            return cls()
        defaults = cls()

        def _int(key: str, default: int) -> int:
            val = data.get(key, default)
            if isinstance(val, int) and not isinstance(val, bool):
                return val
            try:
                return int(val) if val is not None else default
            except (TypeError, ValueError):
                return default

        def _path(key: str) -> Path | None:
            if key not in data:
                return None
            val = data[key]
            if isinstance(val, (str, Path)) or (hasattr(val, "__fspath__")):
                return Path(val)
            return None

        chrome_root = _path("chrome_profile_root")
        return cls(
            google_domain=str(data.get("google_domain", defaults.google_domain)),
            restart_threshold=_int("restart_threshold", defaults.restart_threshold),
            max_retries=_int("max_retries", defaults.max_retries),
            chrome_profile_root=chrome_root if chrome_root is not None else defaults.chrome_profile_root,
            page_load_timeout_s=_int("page_load_timeout_s", defaults.page_load_timeout_s),
            implicit_wait_s=_int("implicit_wait_s", defaults.implicit_wait_s),
        )
