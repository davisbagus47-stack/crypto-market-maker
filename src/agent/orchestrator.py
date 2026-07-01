import json
import uuid
from pathlib import Path

from src.agent.audit_logger import log_event
from src.agent.mapper import map_rows
from src.agent.models import JobResult
from src.agent.review_gate import can_submit, write_preview
from src.integrations.file_loader import load_csv
from src.siga.menu import get_target
from src.validation.rules import validate_rows
from src.workflows.registry import get_workflow


def load_json(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run_job(
    input_path: str | Path,
    mapping_path: str | Path,
    config_path: str | Path,
    target_key: str | None = None,
    approved: bool = False,
) -> JobResult:
    config = load_json(config_path)
    field_mapping = load_json(mapping_path)
    target_menu = target_key or config["default_target_menu"]
    job_id = f"siga-{uuid.uuid4().hex[:12]}"
    output_dir = config["paths"]["output_dir"]
    log_dir = config["paths"]["log_dir"]
    dry_run = bool(config.get("dry_run", True))

    target = get_target(target_menu)
    workflow = get_workflow(target_menu)

    log_event(
        log_dir,
        job_id,
        "job_started",
        {
            "target_menu": target_menu,
            "target_name": target["name"],
            "route": target["url"],
            "workflow": workflow.definition.name,
            "input_path": str(input_path),
            "dry_run": dry_run,
        },
    )

    rows = load_csv(input_path)
    rows = map_rows(rows, field_mapping)
    rows = validate_rows(rows, field_mapping)

    preview_path = write_preview(rows, output_dir, job_id)
    allowed, reason = can_submit(rows, dry_run=dry_run, approved=approved)

    log_event(
        log_dir,
        job_id,
        "preview_created",
        {
            "preview_path": str(preview_path),
            "can_submit": allowed,
            "submit_block_reason": reason,
        },
    )

    # Skeleton aman: belum melakukan submit nyata ke SIGA.
    if allowed:
        log_event(
            log_dir,
            job_id,
            "submit_skipped_in_skeleton",
            {"reason": "Connector SIGA belum diaktifkan"},
        )

    valid_rows = sum(row.status == "valid" for row in rows)
    warning_rows = sum(row.status == "warning" for row in rows)
    error_rows = sum(row.status == "error" for row in rows)

    return JobResult(
        job_id=job_id,
        target_menu=target_menu,
        total_rows=len(rows),
        valid_rows=valid_rows,
        warning_rows=warning_rows,
        error_rows=error_rows,
        dry_run=dry_run,
        output_path=str(preview_path),
    )
