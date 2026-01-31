from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path


def read_csv_rows(
    path: Path,
    *,
    delimiter: str = ",",
    has_header: bool = False,
    columns: list[str] | None = None,
) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        if has_header:
            reader = csv.DictReader(handle, delimiter=delimiter)
            if reader.fieldnames is None:
                raise ValueError("CSV header requested, but no header row found.")
            for row in reader:
                yield {k: (v or "") for k, v in row.items() if k is not None}
            return

        reader = csv.reader(handle, delimiter=delimiter)
        for row in reader:
            if columns is None:
                cols = [f"col{i + 1}" for i in range(len(row))]
            else:
                if len(row) != len(columns):
                    raise ValueError(
                        f"Row has {len(row)} columns but expected {len(columns)}: {row!r}"
                    )
                cols = columns
            yield {cols[i]: (row[i] or "") for i in range(len(cols))}


def parse_columns_arg(value: str) -> list[str]:
    cols = [c.strip() for c in value.split(",") if c.strip()]
    if not cols:
        raise ValueError("columns must not be empty")
    if len(set(cols)) != len(cols):
        raise ValueError("columns must be unique")
    return cols
