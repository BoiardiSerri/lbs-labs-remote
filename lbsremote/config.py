"""Piccoli file di configurazione JSON nella cartella ~/.lbslabs-remote/."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)


def config_dir() -> Path:
    path = Path.home() / ".lbslabs-remote"
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return path


def load_json(name: str, defaults: dict) -> dict:
    data = dict(defaults)
    path = config_dir() / name
    try:
        with open(path, "r", encoding="utf-8") as fh:
            stored = json.load(fh)
        if isinstance(stored, dict):
            data.update(stored)
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        log.warning("config %s illeggibile (%s): uso i valori predefiniti", path, exc)
    return data


def save_json(name: str, data: dict) -> None:
    path = config_dir() / name
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError as exc:
        log.warning("impossibile salvare %s: %s", path, exc)
