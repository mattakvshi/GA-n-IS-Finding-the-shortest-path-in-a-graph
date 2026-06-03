"""Общие утилиты проекта."""

from __future__ import annotations

from pathlib import Path
import json


def project_root() -> Path:
    """Корневая папка проекта — директория, где лежит main.py."""
    return Path(__file__).resolve().parents[1]


def save_json(payload: dict, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def percent_deviation(value: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return (value - baseline) / baseline * 100.0
