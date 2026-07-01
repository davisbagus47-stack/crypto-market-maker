import json
from copy import deepcopy

from config import DEFAULT_SETTINGS
from database import execute, fetch_one, now_iso


def deep_merge(base: dict, updates: dict) -> dict:
    merged = deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


async def get_settings() -> dict:
    row = await fetch_one("SELECT value FROM settings WHERE key = ?", ("app_settings",))
    if not row:
        await reset_settings()
        return deepcopy(DEFAULT_SETTINGS)
    try:
        return deep_merge(DEFAULT_SETTINGS, json.loads(row["value"]))
    except json.JSONDecodeError:
        await reset_settings()
        return deepcopy(DEFAULT_SETTINGS)


async def update_settings(updates: dict) -> dict:
    current = await get_settings()
    merged = deep_merge(current, updates)
    await execute(
        """
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        ("app_settings", json.dumps(merged), now_iso()),
    )
    return merged


async def reset_settings() -> dict:
    await execute(
        """
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        ("app_settings", json.dumps(DEFAULT_SETTINGS), now_iso()),
    )
    return deepcopy(DEFAULT_SETTINGS)
