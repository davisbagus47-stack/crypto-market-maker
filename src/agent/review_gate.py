import csv
import json
from pathlib import Path

from src.agent.models import InputRow


def write_preview(rows: list[InputRow], output_dir: str | Path, job_id: str) -> Path:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{job_id}_preview.csv"

    field_names = sorted({key for row in rows for key in row.mapped_data.keys()})
    headers = ["row_number", "status", "errors", "warnings", *field_names]

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "row_number": row.row_number,
                    "status": row.status,
                    "errors": json.dumps(row.errors, ensure_ascii=False),
                    "warnings": json.dumps(row.warnings, ensure_ascii=False),
                    **row.mapped_data,
                }
            )

    return output_path


def can_submit(rows: list[InputRow], dry_run: bool, approved: bool) -> tuple[bool, str]:
    if dry_run:
        return False, "Mode dry_run aktif"
    if not approved:
        return False, "Approval belum diberikan"
    if any(row.status == "error" for row in rows):
        return False, "Masih ada data berstatus error"
    return True, "Data boleh disubmit"
