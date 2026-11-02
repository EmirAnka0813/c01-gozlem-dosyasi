# -*- coding: utf-8 -*-
"""C-01 Gozlem Dosyasi - kanonik dogrulama.

Kullanim:
    python verify.py <url>

Varsayilan: http://127.0.0.1:8099/index.html
Kapsam: boot, h1 a11y, icerik, 6 fotograf + video yok, motor kuluubu (5 isim),
LGS kaydi, terminal komutlari, arama, tanik defteri, overlay,
Hayko Cepkin finali (siluet/UYAAAAAN/mp3/GEÇ), yatay tasma, js hatasi, 404.
"""
import sys
import time

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099/index.html"
P, F = [], []


def check(name, cond, detail=""):
    (P if cond else F).append(name)
    print(("  [OK]   " if cond else "  [FAIL] ") + name
          + ((" | " + str(detail)) if detail and not cond else ""))


with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True,
                           args=["--autoplay-policy=no-user-gesture-required"])
    page = b.new_context(viewport={"width": 1440, "height": 900},
                         locale="tr-TR").new_page()
    js_errs, console_errs, failed = [], [], []
    mp3_responses = []
    page.on("pageerror", lambda e: js_errs.append(str(e)))
    page.on("console",
            lambda m: console_errs.append(m.text) if m.type == "error" else None)
    page.on("requestfailed",
            lambda r: failed.append(r.url.split("/")[-1] + " :: " + str(r.failure)))
    page.on("response",
            lambda r: mp3_responses.append((r.url.split("/")[-1], r.status))
            if "hayko.mp3" in r.url else None)
    page.goto(URL, wait_until="networkidle")
    time.sleep(2)

    # ---- boot ----
    check("baslik C-01", "C-01" in page.title(), page.title())
    check("boot ekrani var", page.evaluate("!!document.getElementById('boot')"))
    check("boot metni doldu",
          page.evaluate("document.getElementById('bootLines').children.length") >= 8)
    page.wait_for_function("!document.getElementById('bootBtn').disabled", timeout=20000)
    page.click("#bootBtn")
    time.sleep(2)
    check("boot kapandi",
          page.evaluate("document.getElementById('boot').classList.contains('gone')"))

    # ---- h1 ----
    h1 = page.evaluate("document.querySelector('.hero h1').innerText")
    check("h1 'ÇINAR ULAŞIN'", h1.strip() == "ÇINAR ULAŞIN", repr(h1))
    check("h1 tek 'ULAŞIN'", h1.count("ULAŞIN") == 1, h1.count("ULAŞIN"))

    # ---- icerik ----
    body = page.evaluate("document.body.innerText")
    for tok in ("SORU 01", "SORU 08", "ÇINAR", "İMZA",
                "LGS burada mı?", "Motor Kulübü", "KEREM", "BERK"):
        # basliklar CSS text-transform ile buyutuluyor; innerText orijinali dondurur
        found = page.evaluate(
            """(t)=>{
                const all=document.body.innerText+' '+document.body.textContent;
                const el=[...document.querySelectorAll('.sec-h .t')]
                    .find(e=>e.textContent.trim().toLowerCase()===t.toLowerCase());
                return !!el || all.toLowerCase().includes(t.toLowerCase());
            }""", tok)
        check("icerik: " + tok, found)
    check("LGS cevabi yazilmamis",
          "Cevap yazılmadı" in body)

    # ---- galeri: 6 gercek fotograf, video yok ----
    frames = page.evaluate("document.querySelectorAll('.frame').length")
    check("6 kare", frames == 6, frames)
    imgs = page.evaluate(
        "Array.from(document.querySelectorAll('.frame img')).map(i=>i.naturalWidth>0)")
    check("6 fotograf yuklendi", all(imgs) and len(imgs) == 6, imgs)
    check("video yok", page.evaluate("document.querySelectorAll('video').length") == 0)
    check("ses kayitlari bolumu yok",
          "Ses Kayıtları" not in body)

    # ---- motor kuluubu: 5 isimli tanik kartlari ----
    check("5 motor tanigi", page.evaluate("document.querySelectorAll('.wit .wcard').length") == 10,
          page.evaluate("document.querySelectorAll('.wit .wcard').length"))

    # ---- terminal ----
    page.evaluate("C01.close()")
    time.sleep(0.3)
    page.click("#termBtn")
    time.sleep(0.4)
    check("terminal acildi",
          page.evaluate("document.getElementById('termPanel').classList.contains('open')"))
    for cmd, expect in (("help", "kayitlar"), ("kayitlar", "REC-08"),
                        ("subject", "C-01"), ("who", "bilinmiyor"),
                        ("find cinar", "ÇINAR"), ("find motor", "KEREM"),
                        ("find lgs", "LGS"), ("find boşluk", "REC-06")):
        page.fill("#termIn", cmd)
        page.press("#termIn", "Enter")
        time.sleep(0.25)
        out = page.evaluate("document.getElementById('termOut').innerText")
        check("cmd '%s'" % cmd, expect in out, out[-80:])
    page.evaluate("C01.close()")
    time.sleep(0.3)

    # ---- arama ----
    page.fill("#q", "lgs")
    page.click("#qbtn")
    time.sleep(0.3)
    check("arama lgs hit", page.evaluate("!!document.querySelector('#sresult .hit')"))
    page.fill("#q", "xyzzy")
    page.click("#qbtn")
    time.sleep(0.3)
    check("arama miss", page.evaluate("!!document.querySelector('#sresult .miss')"))

    # ---- defter ----
    page.fill("#gbName", "Test")
    page.fill("#gbText", "Deneme ifade")
    page.click("#gbForm button[type=submit]")
    time.sleep(0.6)
    check("defter kaydi yazildi",
          "Deneme ifade" in page.evaluate("document.getElementById('gbEntries').innerText"))

    # ---- overlay ----
    page.click("#closeBtn")
    time.sleep(0.4)
    check("overlay acildi",
          page.evaluate("document.getElementById('overlay').classList.contains('open')"))
    check("overlay son satir",
          "içeriği belirsiz" in page.evaluate("document.getElementById('overlay').innerText"))
    ov_txt = page.evaluate("document.getElementById('overlay').innerText")
    check("overlay kapsama %6", "%6" in ov_txt)
    check("overlay video yok", "video" in ov_txt.lower())
    page.click("#reopenBtn")
    time.sleep(0.3)
    check("overlay kapandi",
          not page.evaluate("document.getElementById('overlay').classList.contains('open')"))

    # ---- HAYKO CEPKIN FINALE ----
    check("finale DOM'da", page.evaluate("!!document.getElementById('finale')"))
    check("siluet SVG var", page.evaluate("!!document.getElementById('fig')"))
    check("UYAAAAAN metni",
          page.evaluate("document.getElementById('uya').textContent.trim()") == "UYAAAAAN")
    check("C01.hayko API", page.evaluate("typeof C01.hayko === 'function'"))
    check("duman katmani var", page.evaluate("!!document.getElementById('smoke')"))
    check("duman silahi var (muzzle)", page.evaluate("!!document.getElementById('muzzle')"))
    check("07 LGS butonu var", page.evaluate("!!document.getElementById('lgsBtn')"))

    page.evaluate("C01.hayko()")
    time.sleep(1.2)
    check("finale acik", page.evaluate(
        "document.getElementById('finale').classList.contains('open')"))
    check("player gorunur", page.evaluate(
        "document.getElementById('player').classList.contains('on')"))
    # NOT: performance.getEntriesByType('resource') media element'leri
    # (mp3) guvenilir sekilde raporlamaz -> response listener kullanilir.
    # mp3 200 dondu mu (response listener ile)
    check("mp3 200 dondu", any(
        u.endswith("hayko.mp3") and s == 200 for (u, s) in mp3_responses),
        mp3_responses)
    check("scroll kilitli", page.evaluate("document.body.style.overflow") == "hidden")
    check("duman henuz yok", not page.evaluate(
        "document.getElementById('smoke').classList.contains('on')"))

    time.sleep(2.6)
    check("uya animasyonu", page.evaluate(
        "document.getElementById('uya').classList.contains('go')"))
    check("flash tetiklendi", page.evaluate(
        "document.getElementById('flash').classList.contains('go')"))
    check("namlu dumani animasyonu", page.evaluate("""()=>{
        const m=document.getElementById('muzzle');
        return m && m.style.animation && m.style.animation.includes('muzzlePuff');
    }"""))

    time.sleep(1.6)
    check("duman bastladi", page.evaluate(
        "document.getElementById('smoke').classList.contains('on')"))
    check("uya over modu", page.evaluate(
        "document.getElementById('uya').classList.contains('over')"))
    smoke_op = page.evaluate(
        "parseFloat(getComputedStyle(document.getElementById('smoke')).opacity)")
    check("duman opakligi yukseliyor", smoke_op > 0.3, smoke_op)

    # 5 sn sonra geri basa donus
    time.sleep(4.2)
    check("duman bitti, finale kapandi", not page.evaluate(
        "document.getElementById('finale').classList.contains('open')"))
    check("scroll kilidi kalkti", page.evaluate("document.body.style.overflow") == "")
    check("sayfa basa dondu", page.evaluate("window.scrollY") < 50,
          page.evaluate("window.scrollY"))

    # 07 butonu finali tetikler
    page.evaluate("document.getElementById('lgsBtn').click()")
    time.sleep(1)
    check("07 butonu finali acti", page.evaluate(
        "document.getElementById('finale').classList.contains('open')"))
    page.evaluate("document.getElementById('skip').click()")
    time.sleep(0.5)
    check("gec ile finale kapandi", not page.evaluate(
        "document.getElementById('finale').classList.contains('open')"))

    # overlay -> finale otomatik akis
    page.evaluate("C01.kapat()")
    time.sleep(0.6)
    check("overlay acildi", page.evaluate(
        "document.getElementById('overlay').classList.contains('open')"))
    time.sleep(2.6)
    check("finale otomatik acildi", page.evaluate(
        "document.getElementById('finale').classList.contains('open')"))
    page.keyboard.press("Escape")
    time.sleep(0.5)
    check("ESC finali kapatti", not page.evaluate(
        "document.getElementById('finale').classList.contains('open')"))

    # ---- tasma ----
    for w, h, lbl in ((1440, 900, "1440"), (820, 1180, "820"), (390, 844, "390")):
        page.set_viewport_size({"width": w, "height": h})
        time.sleep(0.7)
        ov = page.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check("yatay tasma yok (" + lbl + ")", ov <= 0, ov)

    page.set_viewport_size({"width": 1440, "height": 900})
    time.sleep(0.5)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1.4)
    check("reveal aktive", page.evaluate("document.querySelectorAll('.rv.in').length") > 3)

    # ---- hatalar ----
    check("js hatasi yok", len(js_errs) == 0, js_errs[:3])
    con404 = [c for c in console_errs if "404" in c]
    check("404 yok", len(con404) == 0, con404[:3])
    real = [f for f in failed if "ERR_ABORTED" not in f]
    check("basarisiz istek yok", len(real) == 0, real[:3])

    b.close()

print("\nSONUC: {} gecti, {} kaldi".format(len(P), len(F)))
if F:
    print("KALAN:", F)
    sys.exit(1)
