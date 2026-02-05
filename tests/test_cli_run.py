from __future__ import annotations

import csv
from pathlib import Path

from humanized_selenium_scraper import cli
from humanized_selenium_scraper.config import ScraperConfig
from humanized_selenium_scraper.exceptions import SkipEntryError
from humanized_selenium_scraper.spec import SearchSpec


class DummySession:
    @classmethod
    def create(cls, config: ScraperConfig, *, profile_dir: Path):
        return cls()

    def close(self) -> None:
        return None

    def search(self, *, query: str, row: dict[str, str], spec: SearchSpec, attempt: int = 1):
        if "skip" in query.lower():
            raise SkipEntryError("skip row")
        if "error" in query.lower():
            raise RuntimeError("boom")
        return "https://example.com", "123", "a@b.com"


def test_run_writes_output_and_handles_errors(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "Session", DummySession)
    monkeypatch.setattr(cli, "random_pause", lambda *_a, **_k: None)

    input_path = tmp_path / "input.csv"
    input_path.write_text("GoodCo\nSkipCo\nErrorCo\n", encoding="utf-8")

    output_path = tmp_path / "output.csv"

    spec = SearchSpec(query_template="{name}")
    config = ScraperConfig()

    exit_code = cli.run(
        input_file=input_path,
        output_file=output_path,
        config=config,
        spec=spec,
        delimiter=",",
        has_header=False,
        columns=["name"],
    )

    assert exit_code == 0

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["name", "Website", "Phone", "Email"]
    assert rows[1] == ["GoodCo", "https://example.com", "123", "a@b.com"]
    assert rows[2] == ["SkipCo", "", "", ""]
    assert rows[3] == ["ErrorCo", "", "", ""]
