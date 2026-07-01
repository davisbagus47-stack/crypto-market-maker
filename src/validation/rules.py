import re
from collections import defaultdict

from src.agent.models import InputRow


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s]{8,20}$")


def validate_rows(rows: list[InputRow], field_mapping: dict) -> list[InputRow]:
    required_fields = field_mapping.get("required_fields", [])
    unique_keys = field_mapping.get("unique_keys", [])
    seen_values: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        row.errors = []
        row.warnings = []

        for field_name in required_fields:
            if not str(row.mapped_data.get(field_name, "")).strip():
                row.errors.append(f"Field wajib kosong: {field_name}")

        email = str(row.mapped_data.get("email", "")).strip()
        if email and not EMAIL_RE.match(email):
            row.errors.append("Format email tidak valid")

        phone = str(row.mapped_data.get("no_telepon", "")).strip()
        if phone and not PHONE_RE.match(phone):
            row.warnings.append("Format nomor telepon perlu dicek")

        for key in unique_keys:
            value = str(row.mapped_data.get(key, "")).strip()
            if not value:
                continue
            if value in seen_values[key]:
                row.errors.append(f"Duplikat dalam file input: {key}={value}")
            seen_values[key].add(value)

        if row.errors:
            row.status = "error"
        elif row.warnings:
            row.status = "warning"
        else:
            row.status = "valid"

    return rows
