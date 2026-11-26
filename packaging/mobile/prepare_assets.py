"""Prepara i file generati delle app per tablet (Android e iPad) dall'interfaccia e dallo stile LBS.

    python packaging/mobile/prepare_assets.py android
    python packaging/mobile/prepare_assets.py ios

Niente viene duplicato nel repository: l'interfaccia (lbsremote/ui) e lo stile grafico
(LBS-Stile-Grafico) restano l'unica fonte e vengono copiati nelle app a ogni build.
Stampa la versione dell'app (da lbsremote/__init__.py).
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "lbsremote" / "ui"
STYLE = ROOT / "LBS-Stile-Grafico"
STYLE_PARTS = ("tokens", "css", "font", "logo", "icone")
TOKENS = json.loads((STYLE / "tokens" / "lbs-tokens.json").read_text(encoding="utf-8"))["color"]


def version() -> tuple[str, int]:
    text = (ROOT / "lbsremote" / "__init__.py").read_text(encoding="utf-8")
    v = re.search(r'__version__ = "([^"]+)"', text).group(1)
    major, minor, patch = (int(x) for x in (v.split(".") + ["0", "0"])[:3])
    return v, major * 10000 + minor * 100 + patch


def copy_www(dest: Path) -> None:
    """Interfaccia web + stile LBS, con la stessa disposizione che usa il desktop (lbs/...)."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for f in UI.iterdir():
        if f.is_file():
            shutil.copy2(f, dest / f.name)
    for part in STYLE_PARTS:
        shutil.copytree(STYLE / part, dest / "lbs" / part)


def app_icon() -> Image.Image:
    return Image.open(STYLE / "logo" / "lbs-icona-app-1024.png").convert("RGBA")


def android() -> None:
    base = ROOT / "android" / "app" / "src" / "main"
    copy_www(base / "assets" / "www")
    # colori del tema dai token
    colors = {"bg_window": TOKENS["bg-window"], "bg_topbar": TOKENS["bg-topbar-top"]}
    xml = ['<?xml version="1.0" encoding="utf-8"?>', "<!-- generato da packaging/mobile/prepare_assets.py -->", "<resources>"]
    xml += [f'    <color name="{k}">{v}</color>' for k, v in colors.items()]
    xml.append("</resources>")
    (base / "res" / "values" / "colors.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    # icona dell'app per ogni densità
    icon = app_icon()
    for name, px in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        d = base / "res" / f"mipmap-{name}"
        d.mkdir(parents=True, exist_ok=True)
        icon.resize((px, px), Image.LANCZOS).save(d / "ic_launcher.png")
    v, code = version()
    (ROOT / "android" / "version.properties").write_text(f"versionName={v}\nversionCode={code}\n", encoding="utf-8")


def ios() -> None:
    base = ROOT / "ios" / "App"
    copy_www(base / "www")
    # icona 1024 senza trasparenza (richiesta da iOS), appoggiata sul colore della finestra
    icon = app_icon()
    h = TOKENS["bg-window"].lstrip("#")
    flat = Image.new("RGB", icon.size, tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    flat.paste(icon, (0, 0), icon)
    flat.save(base / "Assets.xcassets" / "AppIcon.appiconset" / "icon-1024.png")
    # colore della schermata di avvio dai token
    h = TOKENS["bg-window"].lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    colorset = base / "Assets.xcassets" / "LaunchBackground.colorset"
    colorset.mkdir(parents=True, exist_ok=True)
    (colorset / "Contents.json").write_text(json.dumps({
        "colors": [{"idiom": "universal", "color": {"color-space": "srgb", "components": {
            "red": f"{r:.4f}", "green": f"{g:.4f}", "blue": f"{b:.4f}", "alpha": "1.000"}}}],
        "info": {"author": "xcode", "version": 1}}, indent=2) + "\n", encoding="utf-8")
    # colori del codice Swift dai token
    gen = base / "Generated"
    gen.mkdir(exist_ok=True)
    lines = ["// generato da packaging/mobile/prepare_assets.py dai token dello stile LBS", "enum LBSTokens {"]
    for name in ("bg-window", "bg-topbar-top"):
        swift = re.sub(r"-(\w)", lambda m: m.group(1).upper(), name)
        lines.append(f"    static let {swift}: UInt32 = 0x{TOKENS[name].lstrip('#').upper()}")
    lines.append("}")
    (gen / "Tokens.swift").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    if target not in ("android", "ios"):
        sys.exit("uso: prepare_assets.py android|ios")
    {"android": android, "ios": ios}[target]()
    print(version()[0])
