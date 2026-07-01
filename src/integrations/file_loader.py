import csv
from pathlib import Path

from src.agent.models import InputRow


def load_csv(path: str | Path) -> list[InputRow]:
    source = Path(path)
    rows: list[InputRow] = []

    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, raw in enumerate(reader, start=2):
            rows.append(InputRow(row_number=index, raw_data=dict(raw)))

    return rows
