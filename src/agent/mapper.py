from src.agent.models import InputRow


def map_rows(rows: list[InputRow], field_mapping: dict) -> list[InputRow]:
    fields = field_mapping.get("fields", {})
    normalization = field_mapping.get("normalization", {})
    uppercase_fields = set(normalization.get("uppercase_fields", []))
    trim_text = bool(normalization.get("trim_text", True))

    for row in rows:
        mapped = {}
        for source_name, target_name in fields.items():
            value = row.raw_data.get(source_name, "")
            if isinstance(value, str) and trim_text:
                value = value.strip()
            if isinstance(value, str) and target_name in uppercase_fields:
                value = value.upper()
            mapped[target_name] = value
        row.mapped_data = mapped
        row.status = "mapped"

    return rows
