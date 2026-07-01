from src.agent.intent_parser import parse_command
from src.siga.location_resolver import resolve_location


def test_resolve_desa_against_siga_options():
    intent = parse_command("input data implan 10 orang dari desa tegalsari rt 2 rw 6")
    options = {
        "desa": ["1001 - AMBULU", "2001 - TEGALSARI", "2002 - SUMBERREJO"],
        "rt": ["001 - RT 001", "002 - RT 002", "003 - RT 003"],
        "rw": ["004 - RW 004", "005 - RW 005", "006 - RW 006"],
    }

    result = resolve_location(intent.location, options)

    assert result["desa"].selected == "2001 - TEGALSARI"
    assert result["rt"].selected == "002 - RT 002"
    assert result["rw"].selected == "006 - RW 006"
    assert not result["desa"].needs_confirmation


def test_resolve_unknown_desa_requires_confirmation():
    intent = parse_command("input data implan 10 orang dari desa tidakada rt 2")
    options = {"desa": ["2001 - TEGALSARI"], "rt": ["002 - RT 002"]}

    result = resolve_location(intent.location, options)

    assert result["desa"].selected is None
    assert result["desa"].needs_confirmation
