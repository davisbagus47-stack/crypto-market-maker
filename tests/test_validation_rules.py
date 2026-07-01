from src.agent.models import InputRow
from src.validation.rules import validate_rows


def test_validate_required_fields_marks_error():
    rows = [InputRow(row_number=2, raw_data={}, mapped_data={"nama": ""})]
    mapping = {"required_fields": ["nama"], "unique_keys": []}

    result = validate_rows(rows, mapping)

    assert result[0].status == "error"
    assert "Field wajib kosong: nama" in result[0].errors
