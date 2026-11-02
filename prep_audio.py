# -*- coding: utf-8 -*-
"""Hayko Cepkin mp3'ini siteye kopyalar ve 128kbit'e sikistirir.

Turkce karakter iceren dosya adlari ffmpeg'e dogrudan verilemiyor
(MSYS yol donusumu bozuluyor) -> once Python ile kopyalanir, sonra ffmpeg.
"""
import glob
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "public", "hayko.mp3")
TMP = os.path.join(BASE, "_hayko_src.mp3")


def find_source():
    pats = [
        os.path.join(os.path.expanduser("~"), "Downloads", "Hayko Cepkin*.mp3"),
        os.path.join(os.path.expanduser("~"), "Downloads", "*Hayko*.mp3"),
        os.path.join(os.path.expanduser("~"), "Downloads", "*Hayvaaa*.mp3"),
    ]
    for p in pats:
        hits = glob.glob(p)
        if hits:
            return max(hits, key=os.path.getsize)
    return None


def main():
    src = find_source()
    if not src:
        raise SystemExit("kaynak mp3 bulunamadi (Downloads/Hayko*.mp3)")
    print("kaynak:", src, "%.1f MB" % (os.path.getsize(src) / 1024 / 1024))

    shutil.copy2(src, TMP)
    try:
        # 96kbps mono -> 6 dakikalik parca ~4MB yerine ~2.5MB.
        # Telefonda/mobilde tek dosya yuklemesi hizli acilsin diye.
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", TMP,
             "-codec:a", "libmp3lame", "-b:a", "96k", "-ac", "1", "-ar", "44100",
             "-map_metadata", "0", OUT],
            check=True)
    finally:
        if os.path.exists(TMP):
            os.remove(TMP)

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate",
         "-of", "default=noprint_wrappers=1", OUT],
        capture_output=True, text=True).stdout.strip()
    print("cikti: public/hayko.mp3  %.1f MB" % (os.path.getsize(OUT) / 1024 / 1024))
    print(dur)


if __name__ == "__main__":
    main()
