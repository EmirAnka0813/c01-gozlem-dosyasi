# -*- coding: utf-8 -*-
"""Cinar fotograflarini site icin hazirlar.

- Instagram story ekran goruntulerindeki siyah ust bar otomatik kirpilir
- Maks. 900px genislik, JPEG kalite 86
- photos/photo1..6.jpg olarak yazilir
"""
import os

from PIL import Image

SRC_DIR = os.path.join(
    os.path.expanduser("~"), "AppData", "Roaming", "Hermes", "composer-images")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos")

SOURCES = [
    "composer_2026-11-02_17-41-55-207_a29d37.png",  # motosiklet
    "composer_2026-11-02_17-42-29-994_ce2d9b.png",  # ayakta
    "composer_2026-11-02_17-42-50-867_f09cd8.png",  # kirmizi isik
    "composer_2026-11-02_17-43-04-970_765e2a.png",  # ic mekan
    "composer_2026-11-02_17-43-18-494_c29b51.png",  # takim elbise
    "composer_2026-11-02_17-43-33-914_e495b2.png",  # kanepe
]


def crop_black_bar(im):
    """Ustteki duz siyah story barini kirp (varsa)."""
    w, h = im.size
    px = im.convert("RGB").load()
    row_dark = 0
    for y in range(0, int(h * 0.14)):
        dark = sum(1 for x in range(0, w, max(1, w // 40))
                   if max(px[x, y]) < 26)
        if dark > (w // max(1, w // 40)) * 0.9:
            row_dark += 1
        else:
            break
    if row_dark > 8:
        return im.crop((0, row_dark, w, h)), row_dark
    return im, 0


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, name in enumerate(SOURCES, 1):
        src = os.path.join(SRC_DIR, name)
        if not os.path.exists(src):
            raise SystemExit("kaynak yok: " + src)
        im = Image.open(src)
        before = im.size
        im, cut = crop_black_bar(im)
        if im.width > 900:
            im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
        dst = os.path.join(OUT, "photo%d.jpg" % i)
        im.convert("RGB").save(dst, "JPEG", quality=86, optimize=True)
        print("photo%d.jpg  %s -> %s  (kirpilan bar: %dpx, %.0f KB)"
              % (i, "%dx%d" % before, "%dx%d" % im.size, cut,
                 os.path.getsize(dst) / 1024))


if __name__ == "__main__":
    main()
