# -*- coding: utf-8 -*-
"""Pruefungen des Bildschirmgestalters - trocken, ohne fal.ai, ohne einen Cent.
Der Film (ffmpeg) wird nur geprueft, wenn ffmpeg da ist - sonst ist das kein
Fehler der Strasse, sondern ein fehlendes Werkzeug, und das sagt 'stand'."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

e = laden(HIER / "einstellungen.py", "bildschirm_einstellungen")
motiv = laden(HIER / "motiv.py", "bildschirm_motiv")

MODUL = "prod.bildschirmschoner"


@anmelden("bildschirm.gerechnetes-bild-hat-das-format", MODUL,
          "Trocken entsteht je Geraet ein Bild in genau seinem Format", TROCKEN,
          "dass PC und Handy je ihr Mass bekommen - 1920x1080 und 1080x2400")
def gerechnetes_bild_hat_das_format():
    for geraet, (b, h) in e.FORMATE.items():
        bild = motiv.gerechnet(b, h, "gipfelsturm", 7)
        if bild.size != (b, h):
            raise AssertionError("%s: %r statt %r" % (geraet, bild.size, (b, h)))
    return "pc 1920x1080, handy 1080x2400"


@anmelden("bildschirm.oberes-drittel-bleibt-ruhig", MODUL,
          "Das obere Drittel ist ruhiger als das untere - Platz fuer die Uhr", TROCKEN,
          "dass der Sperrbildschirm oben lesbar bleibt")
def oberes_drittel_ruhig():
    from PIL import ImageChops, ImageFilter, ImageStat
    bild = motiv.gerechnet(640, 1200, "gipfelsturm", 3).convert("L")
    # Ruhig heisst: wenig Zeichnung, nicht wenig Verlauf. Gemessen wird der
    # Unterschied zum weichgezeichneten Bild - was ein Verlauf ist, faellt raus.
    zeichnung = ImageChops.difference(bild, bild.filter(ImageFilter.GaussianBlur(12)))
    oben = ImageStat.Stat(zeichnung.crop((0, 0, 640, 400))).mean[0]
    unten = ImageStat.Stat(zeichnung.crop((0, 700, 640, 1100))).mean[0]
    if oben > unten:
        raise AssertionError("oben unruhiger (%.2f) als unten (%.2f)" % (oben, unten))
    return "Zeichnung oben %.2f, unten %.2f" % (oben, unten)


@anmelden("bildschirm.logo-liegt-ohne-schwarzen-kasten-auf", MODUL,
          "Das RepoCity-Logo liegt freigestellt auf, nicht als schwarzer Kasten", TROCKEN,
          "dass das Brand-Exemplar wie ein Logo aussieht und nicht wie ein Aufkleber")
def logo_freigestellt():
    if not e.LOGO.exists():
        raise AssertionError("Logo fehlt: %s" % e.LOGO)
    bild = motiv.gerechnet(800, 450, "gipfelsturm", 5)
    mit = motiv.mit_logo(bild)
    # Ecke des Logo-Kastens: bei einem schwarzen Kasten waere sie fast schwarz.
    b = mit.width // 5
    x0, y0 = (mit.width - b) // 2, int(mit.height * 0.86) - int(b * 1172 / 1920)
    ecke = mit.getpixel((x0 + 2, y0 + 2))
    if sum(ecke) < 120:
        raise AssertionError("Ecke des Logos ist dunkel %r - der schwarze Grund steht noch" % (ecke,))
    return "Ecke des Logos zeigt den Hintergrund: %r" % (ecke,)


@anmelden("bildschirm.einlagern-schreibt-bild-notiz-und-atom", MODUL,
          "Jedes Bild landet mit Notiz in der Wissensdatenbank und als Zeile im Atom-Buch", TROCKEN,
          "Regel B: jedes erzeugte Bild kommt in die Wissensdatenbank")
def einlagern_schreibt():
    ordner = Path(tempfile.mkdtemp(prefix="bildschirm_"))
    me = motiv.e   # die Einstellungen, die motiv wirklich benutzt
    echt = (me.BILDER, me.ATOM, me.BUCH)
    me.BILDER, me.ATOM, me.BUCH = ordner / "bilder", ordner / "atom.jsonl", ordner / "buch.jsonl"
    try:
        bild = motiv.gerechnet(320, 180, "gipfelsturm", 1)
        quelle = ordner / "probe-pc-1.png"
        bild.save(quelle)
        ziel = motiv.einlagern(quelle, {"kit": "gipfelsturm", "geraet": "pc", "modell": "gerechnet",
                                        "startwert": 1, "groesse": "320x180", "weg": "trocken", "auftrag": "Probe"})
        if not ziel.exists() or not ziel.with_suffix(".md").exists():
            raise AssertionError("Bild oder Notiz fehlt")
        if me.ATOM.read_text(encoding="utf-8").count("\n") != 1 or me.BUCH.read_text(encoding="utf-8").count("\n") != 1:
            raise AssertionError("Atom- oder Ausgabenbuch hat nicht genau eine Zeile")
        return "Bild, Notiz, eine Atomzeile, eine Buchzeile"
    finally:
        me.BILDER, me.ATOM, me.BUCH = echt
        shutil.rmtree(ordner, ignore_errors=True)
