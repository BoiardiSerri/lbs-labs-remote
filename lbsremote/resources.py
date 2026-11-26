"""Percorsi delle risorse (interfaccia web e stile grafico LBS) e lettura dei token di stile."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path


def resource_root() -> Path:
    """Cartella che contiene lbsremote/ui e LBS-Stile-Grafico (sorgenti o app impacchettata)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


UI_DIR = resource_root() / "lbsremote" / "ui"
STYLE_DIR = resource_root() / "LBS-Stile-Grafico"


@lru_cache(maxsize=1)
def _tokens() -> dict:
    try:
        with open(STYLE_DIR / "tokens" / "lbs-tokens.json", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def style_token(group: str, name: str, default: str) -> str:
    """Valore di un token dello stile LBS (tokens/lbs-tokens.json), es. ("color", "accent")."""
    return _tokens().get(group, {}).get(name, default)


def token_rgb(name: str, default: str = "#808080") -> tuple[int, int, int]:
    """Colore di un token come (r, g, b)."""
    value = style_token("color", name, default).lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
