import json
from pathlib import Path


def load_menu_targets(path: str | Path = "config/siga_menu_targets.json") -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)["targets"]


def get_target(target_key: str, path: str | Path = "config/siga_menu_targets.json") -> dict:
    targets = load_menu_targets(path)
    if target_key not in targets:
        known = ", ".join(sorted(targets))
        raise KeyError(f"Target menu tidak ditemukan: {target_key}. Pilihan: {known}")
    return targets[target_key]
