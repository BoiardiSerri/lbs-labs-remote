"""Genera le icone dell'app (PNG, .ico per Windows, .icns per macOS) in packaging/icons/."""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "icons"


def app_icon(size: int = 1024) -> Image.Image:
    s = size / 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40 * s, 40 * s, 984 * s, 984 * s), radius=200 * s, fill=(37, 99, 235, 255))
    white = (255, 255, 255, 255)
    d.rounded_rectangle((190 * s, 250 * s, 834 * s, 670 * s), radius=40 * s, fill=white)
    d.rectangle((240 * s, 300 * s, 784 * s, 620 * s), fill=(30, 64, 175, 255))
    d.rectangle((462 * s, 670 * s, 562 * s, 760 * s), fill=white)
    d.rounded_rectangle((330 * s, 750 * s, 694 * s, 800 * s), radius=25 * s, fill=white)
    # freccia del mouse stilizzata
    d.polygon([(470 * s, 360 * s), (470 * s, 560 * s), (520 * s, 515 * s), (555 * s, 590 * s),
               (590 * s, 575 * s), (555 * s, 500 * s), (620 * s, 495 * s)], fill=white)
    return img


def main() -> None:
    OUT.mkdir(exist_ok=True)
    icon = app_icon()
    icon.save(OUT / "LBSLabsRemote.png")
    icon.save(OUT / "LBSLabsRemote.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                                            (128, 128), (256, 256)])
    icon.save(OUT / "LBSLabsRemote.icns")
    print("icone create in", OUT)


if __name__ == "__main__":
    main()
