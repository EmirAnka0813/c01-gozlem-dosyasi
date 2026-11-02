# -*- coding: utf-8 -*-
"""Cinar sitesi kapsamli dogrulama."""
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
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="tr-TR")
    page = ctx.new_page()
    js_errs, console_errs, failed = [], [], []
    page.on("pageerror", lambda e: js_errs.append(str(e)))
    page.on("console",
            lambda m: console_errs.append(m.text) if m.type == "error" else None)
    page.on("requestfailed",
            lambda r: failed.append(r.url.split("/")[-1] + " :: " + str(r.failure)))
    page.goto(URL, wait_until="networkidle")
    time.sleep(2)

    check("baslik C-01", "C-01" in page.title(), page.title())
    check("boot ekrani var", page.evaluate("!!document.getElementById('boot')"))
    check("boot metni doldu",
          page.evaluate("document.getElementById('bootLines').children.length") >= 8)

    page.wait_for_function("!document.getElementById('bootBtn').disabled", timeout=15000)
    page.click("#bootBtn")
    time.sleep(1.5)
    check("boot kapandi",
          page.evaluate("document.getElementById('boot').classList.contains('gone')"))

    check("hero gorunur", page.evaluate("!!document.querySelector('.hero h1')"))
    body = page.evaluate("document.body.innerText")
    check("CINAR adi var", "ÇINAR" in body)
    check("ULASIN adi var", "ULAŞIN" in body)
    check("8 soru basligi var", "SORU 01" in body and "SORU 08" in body)
    check("imza yok", "İMZA" in body or "imza" in body)

    check("canli akis satir artti",
          page.evaluate("document.getElementById('liveLog').children.length") > 2)

    # ---- terminal (ac/kapat butonu ile) ----
    # boot teaser'i terminali acmis olabilir -> JS state ile normalize et
    page.evaluate("C01.close()")
    time.sleep(0.3)
    check("terminal kapali", not page.evaluate(
        "document.getElementById('termPanel').classList.contains('open')"))
    page.click("#termBtn")
    time.sleep(0.5)
    check("terminal acildi",
          page.evaluate("document.getElementById('termPanel').classList.contains('open')"))
    check("C01 dis API var", page.evaluate("typeof C01 === 'object'"))
    check("C01.subject dogru",
          page.evaluate("C01.subject().kayit") == 8)

    page.fill("#termIn", "help")
    page.press("#termIn", "Enter")
    time.sleep(0.4)
    term = page.evaluate("document.getElementById('termOut').innerText")
    check("terminal help calisti", "kayitlar" in term)

    page.fill("#termIn", "subject")
    page.press("#termIn", "Enter")
    time.sleep(0.3)
    term2 = page.evaluate("document.getElementById('termOut').innerText")
    check("terminal subject calisti", "C-01" in term2)

    page.fill("#termIn", "kayitlar")
    page.press("#termIn", "Enter")
    time.sleep(0.3)
    term3 = page.evaluate("document.getElementById('termOut').innerText")
    check("terminal kayitlar 8 kayit", term3.count("REC-") == 8, term3.count("REC-"))

    page.fill("#termIn", "find cinar")
    page.press("#termIn", "Enter")
    time.sleep(0.3)
    term4 = page.evaluate("document.getElementById('termOut').innerText")
    check("terminal find cinar -> 0 eslesme", "0 eşleşme" in term4)

    page.fill("#termIn", "find boşluk")
    page.press("#termIn", "Enter")
    time.sleep(0.3)
    term5 = page.evaluate("document.getElementById('termOut').innerText")
    check("terminal find bosluk -> eslesme", "REC-06" in term5)

    page.fill("#termIn", "who")
    page.press("#termIn", "Enter")
    time.sleep(0.3)
    term6 = page.evaluate("document.getElementById('termOut').innerText")
    check("terminal who -> bilinmiyor", "bilinmiyor" in term6)

    page.evaluate("document.getElementById('termClose').click()")
    time.sleep(0.4)
    check("terminal kapandi",
          not page.evaluate("document.getElementById('termPanel').classList.contains('open')"))

    # ---- arama ----
    page.fill("#q", "boşluk")
    page.click("#qbtn")
    time.sleep(0.3)
    check("arama hit", page.evaluate("!!document.querySelector('#sresult .hit')"))
    page.fill("#q", "xyzzy")
    page.click("#qbtn")
    time.sleep(0.3)
    check("arama miss", page.evaluate("!!document.querySelector('#sresult .miss')"))

    # ---- tanik defteri ----
    page.fill("#gbName", "Test")
    page.fill("#gbText", "Deneme ifade")
    page.click("#gbForm button[type=submit]")
    time.sleep(0.6)
    check("defter kaydi yazildi",
          "Deneme ifade" in page.evaluate("document.getElementById('gbEntries').innerText"))

    # ---- overlay ----
    page.click("#closeBtn")
    time.sleep(0.5)
    check("overlay acildi",
          page.evaluate("document.getElementById('overlay').classList.contains('open')"))
    check("overlay son satir",
          "içeriği belirsiz" in page.evaluate("document.getElementById('overlay').innerText"))
    page.click("#reopenBtn")
    time.sleep(0.3)
    check("overlay kapandi",
          not page.evaluate("document.getElementById('overlay').classList.contains('open')"))

    # ---- medya ----
    imgs = page.evaluate("Array.from(document.querySelectorAll('img')).map(i=>i.naturalWidth>0)")
    check("tum img yuklendi", all(imgs), "{} / {}".format(sum(imgs), len(imgs)))
    check("vid4 kayip isaretli", page.evaluate("!!document.querySelector('.acard.lost')"))

    vids = page.evaluate(
        "Array.from(document.querySelectorAll('.acard video')).map(v=>v.readyState>=1)")
    check("3 video yuklendi", sum(1 for v in vids if v) == 3, vids)
    # ---- tasma ----
    ov = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("yatay tasma yok (1440)", ov <= 0, ov)

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1.4)
    check("reveal aktive", page.evaluate("document.querySelectorAll('.rv.in').length") > 3)

    page.set_viewport_size({"width": 390, "height": 844})
    time.sleep(0.8)
    ov2 = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("yatay tasma yok (390)", ov2 <= 0, ov2)

    page.set_viewport_size({"width": 820, "height": 1180})
    time.sleep(0.8)
    ov3 = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("yatay tasma yok (820)", ov3 <= 0, ov3)

    check("js hatasi yok", len(js_errs) == 0, js_errs[:3])
    # ERR_ABORTED: preload=metadata tarayici Range isteyip iptal eder -> normal,
    # ayrica 404 olmayan tek kaynak (vid4) HTML'den kaldirildi.
    real_fail = [f for f in failed if "ERR_ABORTED" not in f]
    check("basarisiz istek yok", len(real_fail) == 0, real_fail[:3])
    con_404 = [c for c in console_errs if "404" in c]
    check("404 yok", len(con_404) == 0, con_404[:3])

    b.close()

print("\nSONUC: {} gecti, {} kaldi".format(len(P), len(F)))
if F:
    print("KALAN:", F)
    sys.exit(1)
