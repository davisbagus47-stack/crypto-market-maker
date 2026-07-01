from src.agent.intent_parser import build_execution_plan, parse_command


def test_parse_implant_command_with_location():
    intent = parse_command("input data implant 10 orang dari desa ambulu rt.2 rw.6")

    assert intent.action == "input_pelayanan_kb"
    assert intent.method == "IMPLAN"
    assert intent.quantity == 10
    assert intent.participant_status == "PUS"
    assert intent.target_menu == "yankb_pelkon.pelayanan_kb"
    assert intent.source == "search_button"
    assert intent.location.desa == "AMBULU"
    assert intent.location.rt == "002"
    assert intent.location.rw == "006"
    assert intent.missing_fields == []


def test_parse_command_builds_plan():
    intent = parse_command("masukkan implan 5 pus dari desa tegalsari rw 01 rt 001")
    plan = build_execution_plan(intent)

    assert "Buka menu YAN KB / PELKON > Register > Pelayanan KB." in plan
    assert any("metode IMPLAN" in step for step in plan)
