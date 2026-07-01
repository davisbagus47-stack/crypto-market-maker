import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LocationIntent:
    provinsi: str | None = None
    kabupaten: str | None = None
    kecamatan: str | None = None
    desa: str | None = None
    dusun: str | None = None
    rw: str | None = None
    rt: str | None = None


@dataclass
class DataEntryIntent:
    raw_text: str
    action: str | None = None
    target_menu: str | None = None
    method: str | None = None
    quantity: int | None = None
    participant_status: str | None = None
    source: str | None = None
    submit_policy: str | None = None
    location: LocationIntent = field(default_factory=LocationIntent)
    needs_confirmation: bool = False
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_vocabulary(path: str | Path = "config/intent_vocabulary.json") -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_command(
    text: str,
    vocabulary_path: str | Path = "config/intent_vocabulary.json",
) -> DataEntryIntent:
    vocab = load_vocabulary(vocabulary_path)
    normalized = _normalize_text(text)
    intent = DataEntryIntent(raw_text=text)

    defaults = vocab.get("default_intent", {})
    intent.target_menu = defaults.get("target_menu")
    intent.source = defaults.get("source")
    intent.submit_policy = defaults.get("submit_policy")
    intent.participant_status = defaults.get("participant_status")

    intent.action = _detect_action(normalized, vocab)
    intent.method = _detect_method(normalized, vocab)
    explicit_status = _detect_participant_status(normalized, vocab)
    if explicit_status:
        intent.participant_status = explicit_status
    intent.quantity = _detect_quantity(normalized)
    intent.location = _detect_location(normalized)

    _mark_missing_and_warnings(intent, normalized)
    return intent


def build_execution_plan(intent: DataEntryIntent) -> list[str]:
    method = intent.method or "[metode belum jelas]"
    quantity = intent.quantity or "[jumlah belum jelas]"
    location = _location_summary(intent.location)

    return [
        "Login ke SIGA.",
        "Buka menu YAN KB / PELKON > Register > Pelayanan KB.",
        "Klik tombol Cari pada bagian Data Peserta.",
        "Baca opsi wilayah yang tersedia di SIGA.",
        f"Cocokkan filter wilayah dari instruksi user: {location}.",
        "Klik Cari pada popup pencarian.",
        "Baca tabel hasil dan pilih hanya baris dengan PUS = Ya.",
        f"Kumpulkan {quantity} data peserta.",
        "Jika halaman saat ini belum cukup, lanjut ke halaman berikutnya.",
        f"Isi pelayanan KB dengan metode {method}.",
        "Simpan sementara setiap data yang valid.",
        "Buat preview hasil input.",
        "Tunggu approval sebelum submit final.",
    ]


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.replace("/", " ")
    lowered = re.sub(r"[,;:()]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _detect_action(text: str, vocab: dict[str, Any]) -> str | None:
    for action, aliases in vocab.get("actions", {}).items():
        if any(_contains_word(text, alias) for alias in aliases):
            return action
    return None


def _detect_method(text: str, vocab: dict[str, Any]) -> str | None:
    for method, aliases in vocab.get("methods", {}).items():
        if any(_contains_word(text, alias) for alias in aliases):
            return method
    return None


def _detect_participant_status(text: str, vocab: dict[str, Any]) -> str | None:
    for status, aliases in vocab.get("participant_statuses", {}).items():
        if any(_contains_word(text, alias) for alias in aliases):
            return status
    return None


def _detect_quantity(text: str) -> int | None:
    patterns = [
        r"\b(\d{1,4})\s*(?:orang|data|peserta|pus)\b",
        r"\bsebanyak\s*(\d{1,4})\b",
        r"\bambil\s*(\d{1,4})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def _detect_location(text: str) -> LocationIntent:
    return LocationIntent(
        provinsi=_extract_named_area(text, ["provinsi", "propinsi"]),
        kabupaten=_extract_named_area(text, ["kabupaten", "kab", "kota"]),
        kecamatan=_extract_named_area(text, ["kecamatan", "kec"]),
        desa=_extract_named_area(text, ["desa", "kelurahan", "kel"]),
        dusun=_extract_named_area(text, ["dusun", "lingkungan"]),
        rw=_extract_number_area(text, ["rw"]),
        rt=_extract_number_area(text, ["rt"]),
    )


def _extract_named_area(text: str, labels: list[str]) -> str | None:
    stop_words = (
        " rt ",
        " rw ",
        " dusun ",
        " lingkungan ",
        " desa ",
        " kelurahan ",
        " kel ",
        " kecamatan ",
        " kec ",
        " kabupaten ",
        " kab ",
        " kota ",
        " provinsi ",
        " propinsi ",
        " pus ",
        " orang ",
        " data ",
        " peserta ",
    )
    label_group = "|".join(re.escape(label) for label in labels)
    match = re.search(rf"\b(?:{label_group})\.?\s+([a-z0-9'\- ]+)", text)
    if not match:
        return None

    value = f" {match.group(1).strip()} "
    cut_at = len(value)
    for stop_word in stop_words:
        index = value.find(stop_word)
        if index > 0:
            cut_at = min(cut_at, index)

    cleaned = value[:cut_at].strip()
    if not cleaned:
        return None
    return cleaned.upper()


def _extract_number_area(text: str, labels: list[str]) -> str | None:
    label_group = "|".join(re.escape(label) for label in labels)
    match = re.search(rf"\b(?:{label_group})\.?\s*0*(\d{{1,3}})\b", text)
    if not match:
        return None
    return match.group(1).zfill(3)


def _mark_missing_and_warnings(intent: DataEntryIntent, normalized: str) -> None:
    if not intent.action:
        intent.missing_fields.append("action")
    if not intent.method:
        intent.missing_fields.append("method")
    if not intent.quantity:
        intent.missing_fields.append("quantity")
    if not _has_any_location(intent.location):
        intent.missing_fields.append("location")

    if intent.quantity and intent.quantity > 50:
        intent.warnings.append("Jumlah data besar, disarankan mulai batch kecil.")

    if "submit" in normalized and "preview" not in normalized:
        intent.warnings.append("Instruksi menyebut submit tanpa preview eksplisit.")

    if _has_unlabeled_area_after_from(normalized) and not (
        intent.location.desa or intent.location.kecamatan
    ):
        intent.warnings.append("Nama wilayah tanpa label desa/kecamatan berpotensi ambigu.")

    intent.needs_confirmation = bool(intent.missing_fields or intent.warnings)


def _has_any_location(location: LocationIntent) -> bool:
    return any(
        [
            location.provinsi,
            location.kabupaten,
            location.kecamatan,
            location.desa,
            location.dusun,
            location.rw,
            location.rt,
        ]
    )


def _has_unlabeled_area_after_from(text: str) -> bool:
    return bool(re.search(r"\b(?:dari|di)\s+[a-z]+", text)) and not bool(
        re.search(r"\b(?:desa|kelurahan|kel|kecamatan|kec|kabupaten|kab|kota)\b", text)
    )


def _contains_word(text: str, phrase: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(phrase.lower())}(?![a-z0-9])", text))


def _location_summary(location: LocationIntent) -> str:
    parts = []
    for label, value in [
        ("provinsi", location.provinsi),
        ("kabupaten", location.kabupaten),
        ("kecamatan", location.kecamatan),
        ("desa", location.desa),
        ("dusun", location.dusun),
        ("rw", location.rw),
        ("rt", location.rt),
    ]:
        if value:
            parts.append(f"{label}={value}")
    return ", ".join(parts) if parts else "[wilayah belum jelas]"
