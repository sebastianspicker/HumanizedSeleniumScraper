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
            dict_reader = csv.DictReader(handle, delimiter=delimiter)
            if dict_reader.fieldnames is None:
                raise ValueError("CSV header requested, but no header row found.")
            for row_dict in dict_reader:
                yield {k: (v or "") for k, v in row_dict.items() if k is not None}
            return

        row_reader = csv.reader(handle, delimiter=delimiter)
        for row_list in row_reader:
            if columns is None:
                cols = [f"col{i + 1}" for i in range(len(row_list))]
            else:
                if len(row_list) != len(columns):
                    raise ValueError(
                        f"Row has {len(row_list)} columns but expected {len(columns)}: {row_list!r}"
                    )
                cols = columns
            yield {cols[i]: (row_list[i] or "") for i in range(len(cols))}


def parse_columns_arg(value: str) -> list[str]:
    cols = [c.strip() for c in value.split(",") if c.strip()]
    if not cols:
        raise ValueError("columns must not be empty")
    if len(set(cols)) != len(cols):
        raise ValueError("columns must be unique")
    return cols
