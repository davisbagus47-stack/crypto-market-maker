import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SENSITIVE_KEYS = {"password", "accessToken", "refreshToken", "token", "cookie"}


def sanitize(payload: dict[str, Any]) -> dict[str, Any]:
    safe = {}
    for key, value in payload.items():
        if key in SENSITIVE_KEYS:
            safe[key] = "[REDACTED]"
        else:
            safe[key] = value
    return safe


def log_event(log_dir: str | Path, job_id: str, event: str, payload: dict[str, Any]) -> Path:
    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = target_dir / f"{job_id}.jsonl"

    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        "event": event,
        "payload": sanitize(payload),
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return log_path
