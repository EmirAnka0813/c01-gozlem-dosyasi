# -*- coding: utf-8 -*-
"""Cinar sitesi icin placeholder medya uretir.
- photos/photo1..8.jpg : karanlik CCTV/kayip-kare dokusu (kamera kapsama %0 temali)
- public/vid1..3.mp4    : kisa, sessiz kayit parcalari
- public/vid4.mp4      : YAPILMAZ - "kayip kanal" bilincli olarak bos birakilir
"""
import os
import random
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(BASE, "photos")
PUBLIC = os.path.join(BASE, "public")
os.makedirs(PHOTOS, exist_ok=True)
os.makedirs(PUBLIC, exist_ok=True)

from PIL import Image, ImageDraw, ImageFilter

W, H = 800, 800


def make_frame(idx):
    random.seed(1000 + idx)
    img = Image.new("RGB", (W, H), (6, 9, 12))
    px = img.load()

    for y in range(H):
        for x in range(W):
            n = random.randint(0, 22)
            v = 4 + n
            px[x, y] = (v, v + 2, v + 4)

    d = ImageDraw.Draw(img)

    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(11, 16, 20), width=1)

    for _ in range(14):
        cx = random.randint(0, W)
        cy = random.randint(0, H)
        r = random.randint(30, 150)
        d.ellipse((cx - r, cy - r, cx + r, cy + r),
                  fill=(random.randint(14, 26), random.randint(16, 28), random.randint(18, 32)))

    sx = random.randint(0, W - 60)
    d.rectangle((sx, 0, sx + random.randint(20, 70), H), fill=(28, 34, 40))

    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    d = ImageDraw.Draw(img)

    m, L = 26, 54
    amber = (255, 180, 84)
    for (ox, oy, dx, dy) in ((m, m, 1, 1), (W - m, m, -1, 1),
                             (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.line([(ox, oy), (ox + dx * L, oy)], fill=amber, width=2)
        d.line([(ox, oy), (ox, oy + dy * L)], fill=amber, width=2)

    stamp = "2019-11-02  09:14:%02d" % (idx * 7 % 60)
    d.rectangle((30, H - 74, 298, H - 42), fill=(0, 0, 0))
    d.text((38, H - 71), stamp, fill=(94, 242, 160))

    label = "CAM-%02d   F-%02d   KAPSAMA: %%0" % (idx + 1, idx + 1)
    d.rectangle((30, 34, 360, 58), fill=(0, 0, 0))
    d.text((38, 39), label, fill=(255, 180, 84))

    d.text((W // 2 - 150, H // 2), "S I N Y A L   Y O K", fill=(60, 74, 82))

    out = os.path.join(PHOTOS, "photo%d.jpg" % idx)
    img.save(out, "JPEG", quality=78)
    return out


def make_video(idx, seconds=6):
    out = os.path.join(PUBLIC, "vid%d.mp4" % idx)
    if os.path.exists(out):
        os.remove(out)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i",
        "testsrc2=size=640x360:rate=12:duration=%d" % seconds,
        "-f", "lavfi", "-i",
        "sine=frequency=%d:sample_rate=44100:duration=%d" % (120 + idx * 40, seconds),
        "-vf", "hue=s=0,eq=contrast=1.4:brightness=-0.22,noise=alls=22:allf=t+u,"
               "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.18:t=fill",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart",
        out,
    ]
    subprocess.run(cmd, check=True)
    return out


if __name__ == "__main__":
    for i in range(1, 9):
        print("photo:", make_frame(i))
    for i in (1, 2, 3):
        print("video:", make_video(i))
    p4 = os.path.join(PUBLIC, "vid4.mp4")
    if os.path.exists(p4):
        os.remove(p4)
    print("vid4: bilincli olarak yok (kayip kanal)")
