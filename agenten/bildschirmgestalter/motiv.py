# -*- coding: utf-8 -*-
"""Das Motiv - ein Standbild je Format, echt oder trocken.

  echt      fal.ai erzeugt das Bild aus dem Auftrag (gleicher Weg wie die
            Kit-Bilder in marke/kit_bilder.py), gebucht ueber das Verbrauchsbuch
  trocken   ein gerechnetes Bild: Farbverlauf in den Kit-Farben mit feinem
            Korn und einem Lichtpunkt - kein Cent, kein Netz, aber ein
            fertiges, brauchbares Stueck

Beide Wege legen das Bild ein (Regel B): PNG plus Notiz in der
Wissensdatenbank, eine Zeile im Atom-Buch und im Ausgabenbuch.

Sperrbildschirme brauchen oben Platz fuer die Uhr - darum ist das obere
Drittel bei beiden Wegen ruhig gehalten (im Auftrag an das Modell steht es,
beim gerechneten Bild ist es so gebaut).
"""
from __future__ import annotations

import json
import math
import random
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def _eigen(name: str):
    """Einen Baustein dieses Agenten ueber seinen Pfad laden, nicht ueber den
    Suchpfad - einstellungen.py gibt es zwoelfmal im Universe."""
    import importlib.util as _iu
    _p = Path(__file__).resolve().parent
    _spec = _iu.spec_from_file_location("%s_%s" % (_p.name, name), _p / (name + ".py"))
    _m = _iu.module_from_spec(_spec)
    import sys as _sys
    _sys.modules[_spec.name] = _m   # dataclasses brauchen das Modul dort
    _spec.loader.exec_module(_m)
    return _m

e = _eigen("einstellungen")
KERN = e.UNIVERSE / "kern"
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

KITS_JSON = e.UNIVERSE / "marke" / "kits.json"


def kitfarben(kit: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """Grund, Tiefe und Signal eines Kits als RGB - aus kits.json.

    Die Tiefe ist nicht groundDeep (bei hellen Kits fast dasselbe wie der
    Grund), sondern der Grund zur Schriftfarbe hin verdunkelt: so bekommt
    auch ein helles Kit unten Tiefe, und der Bildschirm wirkt nicht wie ein
    leeres Blatt."""
    def rgb(argb: str):
        v = int(argb, 16)
        return ((v >> 16) & 255, (v >> 8) & 255, v & 255)
    try:
        alle = {k["id"]: k for k in json.loads(KITS_JSON.read_text(encoding="utf-8"))["kits"]}
        k = alle.get(kit) or alle["gipfelsturm"]
        grund, schrift, signal = rgb(k["ground"]), rgb(k["text"]), rgb(k["accent"])
        tiefe = tuple(int(grund[i] * 0.45 + schrift[i] * 0.55) for i in range(3))
        return grund, tiefe, signal
    except Exception:
        return (14, 14, 19), (8, 8, 10), (218, 208, 179)


def gerechnet(breite: int, hoehe: int, kit: str, startwert: int) -> Image.Image:
    """Der trockene Weg: ein ruhiger Verlauf mit Korn und einem Lichtpunkt."""
    grund, tief, signal = kitfarben(kit)
    zufall = random.Random(startwert)
    bild = Image.new("RGB", (breite, hoehe))
    px = bild.load()
    for y in range(hoehe):
        t = y / max(1, hoehe - 1)
        # oben der Grund (ruhig, fuer die Uhr), unten der tiefe Ton
        f = tuple(int(grund[i] * (1 - t) + tief[i] * t) for i in range(3))
        for x in range(breite):
            px[x, y] = f
    # Lichtpunkt im unteren Drittel, Signalfarbe, weich
    licht = Image.new("RGB", (breite, hoehe), (0, 0, 0))
    z = ImageDraw.Draw(licht)
    cx, cy = int(breite * (0.3 + 0.4 * zufall.random())), int(hoehe * 0.72)
    r = int(min(breite, hoehe) * 0.28)
    z.ellipse((cx - r, cy - r, cx + r, cy + r), fill=signal)
    licht = licht.filter(ImageFilter.GaussianBlur(r * 0.6))
    bild = Image.blend(bild, Image.composite(licht, bild, licht.convert("L").point(lambda v: min(255, v * 2))), 0.6)
    # feines Korn - eine gekachelte Flaeche, nicht Millionen Einzelpunkte
    korn = Image.effect_noise((256, 256), 18).convert("L")
    kachel = Image.new("L", (breite, hoehe))
    for yy in range(0, hoehe, 256):
        for xx in range(0, breite, 256):
            kachel.paste(korn, (xx, yy))
    # Das Korn liegt nur im unteren Teil: oben, wo die Uhr steht, bleibt es glatt.
    # Von einem Drittel bis zur Haelfte blendet es ein.
    rampe = Image.new("L", (breite, hoehe), 0)
    rz = rampe.load()
    for y in range(hoehe):
        t_ = (y / hoehe - 1 / 3) / (1 / 6)
        wert = 0 if t_ <= 0 else (255 if t_ >= 1 else int(255 * t_))
        for x in range(breite):
            rz[x, y] = wert
    kornmaske = Image.composite(kachel.point(lambda v: 235 + (v - 128) // 6), Image.new("L", (breite, hoehe), 255), rampe)
    bild = Image.composite(bild, Image.new("RGB", (breite, hoehe), tief), kornmaske)
    return bild


def echt(breite: int, hoehe: int, auftrag: str, startwert: int, ziel: Path) -> tuple[Image.Image, float]:
    """fal.ai - derselbe Aufruf wie bei den Kit-Bildern. Gibt Bild und Preis (USD) zurueck."""
    schluessel = ""
    for z in (e.WURZEL / ".env").read_text(encoding="utf-8", errors="ignore").splitlines():
        if z.strip().startswith("FAL_KEY"):
            schluessel = z.split("=", 1)[1].strip().strip('"').strip("'")
    if not schluessel:
        raise RuntimeError("FAL_KEY fehlt in .env - ohne ihn kein echtes Bild (trocken laeuft).")
    last = {"prompt": auftrag, "image_size": {"width": breite, "height": hoehe},
            "num_inference_steps": 28, "num_images": 1, "seed": startwert,
            "enable_safety_checker": False, "output_format": "png"}
    a = urllib.request.Request("https://fal.run/" + e.MODELL, data=json.dumps(last).encode("utf-8"),
                               headers={"Authorization": "Key " + schluessel, "Content-Type": "application/json"})
    with urllib.request.urlopen(a, timeout=300) as r:
        erg = json.loads(r.read().decode("utf-8"))
    with urllib.request.urlopen(erg["images"][0]["url"], timeout=300) as r:
        ziel.write_bytes(r.read())
    try:
        import verbrauch
        satz = verbrauch.fuer_modell("prod.bildschirmschoner", e.MODELL, 1, "Bildschirmschoner %dx%d" % (breite, hoehe))
        preis = float(satz.get("betrag_eur", 0.0)) / float(verbrauch.stammdaten().get("usd_zu_eur", 0.92))
    except Exception:
        preis = 0.0
    return Image.open(ziel).convert("RGB"), preis


def prompt(motiv: str, kit: str, geraet: str) -> str:
    return ("%s. Calm wallpaper for a %s lock screen, the upper third quiet and uncluttered "
            "for a clock, cinematic light, no text, no letters, no watermark, style of the "
            "RepoCity %s design" % (motiv, "phone" if geraet == "handy" else "desktop", kit))


def mit_logo(bild: Image.Image) -> Image.Image:
    """Das RepoCity-Exemplar: Logo unten mittig, ein Fuenftel der Breite, leicht durchscheinend."""
    if not e.LOGO.exists():
        return bild
    logo = Image.open(e.LOGO).convert("RGBA")
    # Das Logo liegt auf Schwarz (die Datei traegt keine Durchsicht): der
    # schwarze Grund wird herausgerechnet - was dunkel ist, wird durchsichtig.
    hell = logo.convert("L").point(lambda v: max(0, min(255, (v - 10) * 5)))
    logo.putalpha(hell)
    b = bild.width // 5
    h = int(logo.height * b / logo.width)
    logo = logo.resize((b, h), Image.LANCZOS)
    alpha = logo.getchannel("A").point(lambda v: int(v * 0.92))
    logo.putalpha(alpha)
    aus = bild.convert("RGBA")
    aus.alpha_composite(logo, ((bild.width - b) // 2, int(bild.height * 0.86) - h))
    return aus.convert("RGB")


def einlagern(bild_pfad: Path, satz: dict) -> Path:
    """Regel B: Bild und Notiz in die Wissensdatenbank, eine Zeile ins Atom-Buch."""
    e.BILDER.mkdir(parents=True, exist_ok=True)
    ziel = e.BILDER / bild_pfad.name
    if ziel.resolve() != bild_pfad.resolve():
        ziel.write_bytes(bild_pfad.read_bytes())
    jetzt = datetime.now().isoformat(timespec="seconds")
    notiz = ziel.with_suffix(".md")
    notiz.write_text(
        "---\nkit: %s\ngeraet: %s\nmodell: %s\nstartwert: %s\ngroesse: %s\nerzeugt: %s\n"
        "kosten_usd: %s\ntyp: bildschirmschoner\nstatus: offen\nweg: %s\n---\n\n![[%s]]\n\n## Bildauftrag\n\n%s\n"
        % (satz.get("kit"), satz.get("geraet"), satz.get("modell"), satz.get("startwert"),
           satz.get("groesse"), jetzt, satz.get("kosten_usd", 0.0), satz.get("weg"),
           ziel.name, satz.get("auftrag", "")),
        encoding="utf-8", newline="")
    for pfad, zeile in ((e.ATOM, {"typ": "bild", "kit": satz.get("kit"), "stufe": "bildschirmschoner",
                                  "startwert": satz.get("startwert"), "modell": satz.get("modell"),
                                  "datei": str(ziel), "notiz": str(notiz), "auftrag": satz.get("auftrag", ""),
                                  "erzeugt": jetzt, "kosten_usd": satz.get("kosten_usd", 0.0),
                                  "groesse": satz.get("groesse")}),
                        (e.BUCH, {"zeit": jetzt, "kit": satz.get("kit"), "stufe": "bildschirmschoner",
                                  "kosten_usd": satz.get("kosten_usd", 0.0)})):
        pfad.parent.mkdir(parents=True, exist_ok=True)
        with pfad.open("a", encoding="utf-8") as f:
            f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
    return ziel
