from dataclasses import dataclass, field
from typing import Any


@dataclass
class InputRow:
    row_number: int
    raw_data: dict[str, Any]
    mapped_data: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class JobResult:
    job_id: str
    target_menu: str
    total_rows: int
    valid_rows: int
    warning_rows: int
    error_rows: int
    dry_run: bool
    output_path: str
