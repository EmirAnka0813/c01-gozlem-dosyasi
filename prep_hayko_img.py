# -*- coding: utf-8 -*-
"""Hayko Cepkin gorselini hazirlar.

Kaynak: video-hayko-*.mp4 -> en kontrastli kare (yerel standart sapma).
Beyaza yikanmis (dusuk kontrastli) kareler elenir.

Cikti: public/hayko.jpg
"""
import glob
import os
import shutil
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "public", "hayko.jpg")
TMP = os.path.join(BASE, "_hayko_work")

W, H = 900, 1200          # 3:4 dikey


def find_video():
    pats = [
        os.path.join(os.path.expanduser("~"), "OneDrive", "Masaüstü", "video-hayko-*.mp4"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "video-hayko-*.mp4"),
        os.path.join(os.path.expanduser("~"), "Desktop", "video-hayko-*.mp4"),
        os.path.join(os.path.expanduser("~"), "Downloads", "video-hayko-*.mp4"),
        os.path.join(os.path.expanduser("~"), "Videos", "video-hayko-*.mp4"),
    ]
    for p in pats:
        hits = glob.glob(p)
        if hits:
            return max(hits, key=os.path.getsize)
    return None


def find_images():
    pat = os.path.join(os.path.expanduser("~"), "AppData", "Roaming",
                       "Hermes", "composer-images", "composer_*19-35*.jpg")
    return sorted(glob.glob(pat), key=os.path.getmtime, reverse=True)


def contrast(path):
    """Yerel standart sapma -> netlik/konu ayirt edilebilirligi.

    Yuksek = net, belirgin. Dusuk = bulanik veya beyaza yikanmis.
    """
    from PIL import Image, ImageStat
    im = Image.open(path).convert("L")
    tiles = []
    tw, th = im.size[0] // 8, im.size[1] // 8
    for y in range(8):
        for x in range(8):
            tiles.append(ImageStat.Stat(im.crop((x * tw, y * th,
                                                  (x + 1) * tw, (y + 1) * th))).stddev[0])
    tiles.sort()
    return sum(tiles) / len(tiles)      # ortalama tile stddev


def brightness(path):
    from PIL import Image, ImageStat
    return ImageStat.Stat(Image.open(path).convert("L")).mean[0]


def best_frame_from(video):
    os.makedirs(TMP, exist_ok=True)
    local = os.path.join(TMP, "src.mp4")
    shutil.copy2(video, local)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", local,
         "-vf", "fps=4", "-q:v", "3", os.path.join(TMP, "f%04d.jpg")],
        check=True)
    frames = sorted(glob.glob(os.path.join(TMP, "f*.jpg")))
    scored = sorted(((contrast(f), brightness(f), f) for f in frames), reverse=True)
    print("kare adedi: %d" % len(frames))
    for c, b, f in scored[:6]:
        print("  %s  kontrast=%5.1f  parlaklik=%5.1f" % (os.path.basename(f), c, b))
    # kontrastli ama cok parlak (beyaza yikanmis) olmayan ilk kare
    for c, b, f in scored:
        if 18 < b < 150:
            return f
    return scored[0][2]


def process(src):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    ow, oh = im.size
    target = W / H
    if ow / oh > target:                       # genis -> orta dikey kirp
        nw = int(oh * target)
        im = im.crop(((ow - nw) // 2, 0, (ow - nw) // 2 + nw, oh))
    else:                                      # dar -> ustten biraz kirp
        nh = int(ow / target)
        top = max(0, int((oh - nh) * 0.10))
        im = im.crop((0, top, ow, min(oh, top + nh)))
    im = im.resize((W, H), Image.LANCZOS)
    im.save(OUT, "JPEG", quality=88, optimize=True)
    print("cikti: public/hayko.jpg  %dx%d  %.0f KB"
          % (W, H, os.path.getsize(OUT) / 1024))


def main():
    try:
        video = find_video()
        if video:
            print("video:", video)
            best = best_frame_from(video)
            print("secilen kare:", os.path.basename(best))
            process(best)
        else:
            imgs = find_images()
            if not imgs:
                raise SystemExit("ne video ne gorsel bulunamadi")
            print("gorsel:", imgs[0])
            process(imgs[0])
    finally:
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
