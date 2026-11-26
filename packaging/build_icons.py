"""Genera la grafica dei pacchetti in packaging/icons/, dallo stile LBS (LBS-Stile-Grafico/):

- LBSLabsRemote.png / .ico / .icns     icona dell'app (logo/lbs-icona-app-1024.png)
- wizard-large*.bmp, wizard-small*.bmp immagini dell'installer Windows (Inno Setup)
- dmg-background.png, dmg-background@2x.png   sfondo della finestra del DMG (macOS)

Colori dai token (tokens/lbs-tokens.json), testi in Barlow Semi Condensed (font/).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STYLE = ROOT / "LBS-Stile-Grafico"
OUT = Path(__file__).resolve().parent / "icons"
TOKENS = json.loads((STYLE / "tokens" / "lbs-tokens.json").read_text(encoding="utf-8"))


def c(name: str, alpha: int = 255) -> tuple[int, int, int, int]:
    h = TOKENS["color"][name].lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def font(weight: str, px: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(STYLE / "font" / f"BarlowSemiCondensed-{weight}.ttf"), max(1, round(px)))


def app_icon() -> Image.Image:
    return Image.open(STYLE / "logo" / "lbs-icona-app-1024.png").convert("RGBA")


def logo_disc(size: int) -> Image.Image:
    """Marchio LBS ritagliato dall'icona dell'app (disco: centro 512, raggio ~298)."""
    disc = app_icon().crop((214, 214, 810, 810))
    mask = Image.new("L", disc.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, disc.size[0] - 1, disc.size[1] - 1), fill=255)
    disc.putalpha(mask)
    return disc.resize((size, size), Image.LANCZOS)


def vgradient(w: int, h: int, stops: list[tuple[float, tuple]]) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            (t0, c0), (t1, c1) = stops[i], stops[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / max(1e-6, t1 - t0)
                col = tuple(round(c0[j] + (c1[j] - c0[j]) * k) for j in range(4))
                break
        for x in range(w):
            px[x, y] = col
    return img


def text_tracked(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill, tracking_em: float,
                 anchor_center: bool = True) -> None:
    """Testo MAIUSCOLO spaziato (come i ruoli heading/eyebrow dello stile)."""
    spacing = fnt.size * tracking_em
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + spacing


def stripes(img: Image.Image, x0: float, top: float, bottom: float, s: float) -> None:
    """Fascia a righe oblique ambra della barra di stato LBS (parallelogramma largo 70 px)."""
    sw = 70 * s
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shift = (bottom - top) / math.tan(math.radians(60))
    p = x0 - shift
    while p < x0 + sw + shift:
        d.line([(p, bottom), (p + shift, top)], fill=c("accent", 115), width=max(1, round(2 * s)))
        p += 9 * s
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([(x0 + sw * 0.3, top), (x0 + sw, top), (x0 + sw * 0.7, bottom), (x0, bottom)], fill=255)
    img.alpha_composite(Image.composite(layer, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask))


def iobar(img: Image.Image, h: float, s: float) -> None:
    """Barra di stato in basso: fondo io-bar, filo edge-lo + edge-hi, due fasce ambra al 30 % e 70 %."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    top = H - h
    d.rectangle((0, top, W, H), fill=c("bg-io-bar"))
    d.line([(0, top), (W, top)], fill=c("edge-lo"), width=max(1, round(s)))
    d.line([(0, top + s), (W, top + s)], fill=c("edge-hi"), width=max(1, round(s)))
    for at in (0.3, 0.7):
        stripes(img, W * at, top + 2 * s, H, s)


# ------------------------------------------------------------------------------------------
def wizard_large(s: float) -> Image.Image:
    """Immagine laterale dell'installer (164×314 a scala 1)."""
    W, H = round(164 * s), round(314 * s)
    img = vgradient(W, H, [(0, c("bg-panel-top")), (0.25, c("bg-panel")), (1, c("bg-window"))])
    d = ImageDraw.Draw(img)
    logo = logo_disc(round(84 * s))
    img.alpha_composite(logo, ((W - logo.width) // 2, round(56 * s)))
    text_tracked(d, (W / 2, 160 * s), "LBS LABS", font("SemiBold", 10.67 * s), c("text-muted"), 0.0949)
    text_tracked(d, (W / 2, 176 * s), "REMOTE", font("SemiBold", 17.33 * s), c("text"), 0.0569)
    d.rounded_rectangle((W / 2 - 34 * s, 206 * s, W / 2 + 34 * s, 209 * s), radius=1.5 * s, fill=c("accent"))
    iobar(img, 32 * s, s)
    return img.convert("RGB")


def wizard_small(s: float) -> Image.Image:
    """Icona in alto a destra nelle pagine dell'installer (55×55 a scala 1)."""
    W = round(55 * s)
    img = Image.new("RGBA", (W, W), c("bg-window"))
    icon = app_icon().resize((W, W), Image.LANCZOS)
    img.alpha_composite(icon)
    return img.convert("RGB")


def dmg_background(s: float) -> Image.Image:
    """Sfondo della finestra del DMG (640×420 a scala 1). Posizioni delle icone in dmg_settings.py."""
    W, H = round(640 * s), round(420 * s)
    img = vgradient(W, H, [(0, c("bg-topbar-top")), (0.12, c("bg-topbar-bottom")), (0.121, c("bg-window")), (1, c("bg-window"))])
    d = ImageDraw.Draw(img)
    # barra superiore 48: logo 32 + nome del programma
    d.line([(0, 48 * s), (W, 48 * s)], fill=c("edge-lo"), width=max(1, round(s)))
    logo = logo_disc(round(32 * s))
    img.alpha_composite(logo, (round(12 * s), round(8 * s)))
    text_tracked(d, (52 * s, 15 * s), "LBS LABS REMOTE", font("Regular", 14.67 * s), c("text-2"), 0.0832, anchor_center=False)
    # pannello con viti dietro alle due icone
    px0, py0, px1, py1 = 40 * s, 76 * s, W - 40 * s, 316 * s
    d.rounded_rectangle((px0, py0 + 2 * s, px1, py1 + 2 * s), radius=14 * s, fill=c("shadow", 70))
    panel = vgradient(round(px1 - px0), round(py1 - py0), [(0, c("bg-panel-top")), (0.17, c("bg-panel")), (1, c("bg-panel-bottom"))])
    pmask = Image.new("L", panel.size, 0)
    ImageDraw.Draw(pmask).rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), radius=14 * s, fill=255)
    img.paste(panel, (round(px0), round(py0)), pmask)
    d.rounded_rectangle((px0, py0, px1, py1), radius=14 * s, outline=c("edge-lo"), width=max(1, round(s)))
    d.line([(px0 + 14 * s, py0 + s), (px1 - 14 * s, py0 + s)], fill=c("edge-hi"), width=max(1, round(s)))
    for sx, sy in ((px0 + 10 * s, py0 + 10 * s), (px1 - 10 * s, py0 + 10 * s), (px0 + 10 * s, py1 - 10 * s), (px1 - 10 * s, py1 - 10 * s)):
        r = 2.4 * s
        d.ellipse((sx - r, sy - r + 0.6 * s, sx + r, sy + r + 0.6 * s), fill=c("ink", 90))
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=c("screw"))
    # freccia ambra tra l'app (x 190) e Applicazioni (x 450), all'altezza delle icone (y 172)
    ay = 172 * s
    d.line([(258 * s, ay), (372 * s, ay)], fill=c("accent"), width=round(3 * s))
    d.polygon([(388 * s, ay), (368 * s, ay - 10 * s), (368 * s, ay + 10 * s)], fill=c("accent"))
    # targhette chiare sotto i nomi delle icone (leggibili sia con testo nero sia bianco)
    for cx in (190, 450):
        d.rounded_rectangle(((cx - 80) * s, 228 * s, (cx + 80) * s, 254 * s), radius=13 * s, fill=c("control"))
    text_tracked(d, (W / 2, 276 * s), "DRAG LBS LABS REMOTE ONTO APPLICATIONS", font("SemiBold", 10.67 * s), c("text-2"), 0.0949)
    # istruzioni per il primo avvio
    cap = font("Regular", 12 * s)
    for i, line in enumerate(("Then open LBS Labs Remote from Applications.",
                              "First time only: if macOS cannot verify the app, open System Settings ›",
                              "Privacy & Security and click Open Anyway.")):
        tw = d.textlength(line, font=cap)
        d.text(((W - tw) / 2, (326 + i * 17) * s), line, font=cap, fill=c("text-muted"))
    iobar(img, 32 * s, s)
    return img.convert("RGB")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    icon = app_icon()
    icon.save(OUT / "LBSLabsRemote.png")
    icon.save(OUT / "LBSLabsRemote.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                                                (128, 128), (256, 256)])
    icon.save(OUT / "LBSLabsRemote.icns")
    for s, suffix in ((1, ""), (2, "-2x")):
        wizard_large(s).save(OUT / f"wizard-large{suffix}.bmp")
        wizard_small(s).save(OUT / f"wizard-small{suffix}.bmp")
    dmg_background(1).save(OUT / "dmg-background.png")
    dmg_background(2).save(OUT / "dmg-background@2x.png")
    print("grafica creata in", OUT)


if __name__ == "__main__":
    main()
