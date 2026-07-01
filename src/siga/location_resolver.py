import re
from dataclasses import asdict, dataclass
from typing import Any

from src.agent.intent_parser import LocationIntent


@dataclass
class LocationMatch:
    field: str
    query: str | None
    selected: str | None
    confidence: str
    candidates: list[str]
    needs_confirmation: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_location(
    location: LocationIntent,
    siga_options: dict[str, list[str | dict[str, Any]]],
) -> dict[str, LocationMatch]:
    """Resolve parsed location values against actual SIGA dropdown options.

    `siga_options` harus berasal dari pilihan yang sedang tampil di SIGA, bukan
    dari daftar statis. Contoh opsi SIGA: "2001 - TEGALSARI", "001 - RT 001".
    """
    matches: dict[str, LocationMatch] = {}

    for field in ["provinsi", "kabupaten", "kecamatan", "desa", "dusun", "rw", "rt"]:
        query = getattr(location, field)
        if not query:
            continue

        options = [_option_label(option) for option in siga_options.get(field, [])]
        matches[field] = match_location_value(field, query, options)

    return matches


def match_location_value(field: str, query: str, options: list[str]) -> LocationMatch:
    if not options:
        return LocationMatch(
            field=field,
            query=query,
            selected=None,
            confidence="none",
            candidates=[],
            needs_confirmation=True,
            reason="Opsi SIGA belum tersedia untuk field ini.",
        )

    normalized_query = _normalize_location_text(query)
    normalized_numeric = _normalize_numeric_query(query)
    scored: list[tuple[int, str]] = []

    for option in options:
        option_text = _normalize_location_text(option)
        option_without_code = _normalize_location_text(_remove_code_prefix(option))
        option_numbers = _extract_numbers(option)

        score = 0
        if normalized_query == option_text or normalized_query == option_without_code:
            score = 100
        elif normalized_numeric and normalized_numeric in option_numbers:
            score = 95
        elif normalized_query and normalized_query in option_without_code:
            score = 90
        elif normalized_query and normalized_query in option_text:
            score = 85
        elif option_without_code and option_without_code in normalized_query:
            score = 80

        if score:
            scored.append((score, option))

    scored.sort(key=lambda item: item[0], reverse=True)
    candidates = [option for _, option in scored[:5]]

    if not scored:
        return LocationMatch(
            field=field,
            query=query,
            selected=None,
            confidence="none",
            candidates=[],
            needs_confirmation=True,
            reason="Tidak ada opsi SIGA yang cocok.",
        )

    best_score = scored[0][0]
    best_options = [option for score, option in scored if score == best_score]
    selected = best_options[0]

    if len(best_options) > 1:
        return LocationMatch(
            field=field,
            query=query,
            selected=selected,
            confidence="ambiguous",
            candidates=best_options[:5],
            needs_confirmation=True,
            reason="Lebih dari satu opsi SIGA cocok.",
        )

    confidence = "high" if best_score >= 95 else "medium"
    return LocationMatch(
        field=field,
        query=query,
        selected=selected,
        confidence=confidence,
        candidates=candidates,
        needs_confirmation=False,
    )


def _option_label(option: str | dict[str, Any]) -> str:
    if isinstance(option, str):
        return option
    for key in ["label", "text", "name", "nama", "value"]:
        value = option.get(key)
        if value:
            return str(value)
    return str(option)


def _normalize_location_text(value: str) -> str:
    normalized = value.upper()
    normalized = re.sub(r"[^A-Z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _remove_code_prefix(value: str) -> str:
    return re.sub(r"^\s*\d+\s*-\s*", "", value).strip()


def _extract_numbers(value: str) -> set[str]:
    numbers = set()
    for number in re.findall(r"\d+", value):
        numbers.add(number)
        numbers.add(number.zfill(3))
    return numbers


def _normalize_numeric_query(value: str) -> str | None:
    match = re.search(r"\d+", value)
    if not match:
        return None
    return match.group(0).zfill(3)
