# -*- coding: utf-8 -*-
"""Einstellungen des Bildschirmgestalters - Anmelde- und Sperrbildschirme,
Bildschirmschoner fuer PC und Handy (Daniels 102)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
WURZEL = UNIVERSE.parent
ZUSTAND = UNIVERSE / "zustand"

EINGANG = ZUSTAND / "bildschirm_eingang"
WERKSTATT = ZUSTAND / "bildschirm"
AUSGABE = ZUSTAND / "bildschirm_fertig"

#: Regel B: jedes erzeugte Bild kommt in die Wissensdatenbank - hierhin.
BILDER = WURZEL / "mein_ki_gehirn" / "bilder" / "bildschirmschoner"
ATOM = WURZEL / "mein_ki_gehirn" / "atome" / "bilder-kits.jsonl"
BUCH = WURZEL / "mein_ki_gehirn" / "bilder" / "_ausgaben.jsonl"

TROCKEN = os.getenv("UNIVERSE_TROCKEN", "ja").strip().lower() in ("1", "ja", "true", "yes")

#: Die Formate - je Geraet eines. Zahlen sind Bildpunkte.
FORMATE = {
    "pc": (1920, 1080),
    "handy": (1080, 2400),
}

#: Das Bildmodell bei fal.ai - dasselbe wie bei den Kit-Bildern, mit Preis in kosten.json.
MODELL = "fal-ai/flux/dev"

#: Wie lang der bewegte Schoner ist, in Sekunden, und wie stark er hineinzoomt.
BEWEGT_SEKUNDEN = 12
BEWEGT_ZOOM = 1.08
BILDER_JE_SEKUNDE = 30

#: Das Logo fuer das RepoCity-Exemplar - liegt bei der Marke, freigestellt.
LOGO = UNIVERSE / "marke" / "repocity_logo_frei_1920.png"


def ffmpeg() -> str | None:
    """Wo ffmpeg liegt - aus der Umgebung oder dem Suchpfad. None: kein Film."""
    weg = os.getenv("FFMPEG", "").strip()
    if weg and Path(weg).exists():
        return weg
    return shutil.which("ffmpeg")
