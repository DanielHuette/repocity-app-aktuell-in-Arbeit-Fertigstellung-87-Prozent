# -*- coding: utf-8 -*-
"""Einstellungen des Setzers - der PDF-Strasse (Daniels 105).

Alles, was sich von aussen einstellen laesst, steht hier; gelesen wird aus
der Umgebung (.env am Wurzelverzeichnis, geladen von kern/umgebung.py).
"""
from __future__ import annotations

import os
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent

# Das Modell kennt nur eine Stelle: universe/kern/modellwahl.py. Ueber den
# Pfad geladen, nicht importiert - im Universe tragen mehrere Ordner
# gleichnamige Module, ein normaler Import erwischt das falsche.
import importlib.util as _iu
_mw = _iu.spec_from_file_location(
    "kern_modellwahl", Path(__file__).resolve().parent.parent / "kern" / "modellwahl.py")
modellwahl = _iu.module_from_spec(_mw)
_mw.loader.exec_module(modellwahl)
WURZEL = UNIVERSE.parent
ZUSTAND = UNIVERSE / "zustand"

#: Wo der Sekretaer die Auftraege ablegt (auftragsarten.json: wer_arbeitet).
EINGANG = ZUSTAND / "setzer_eingang"
#: Arbeitsordner je Auftrag und die fertigen Dokumente.
WERKSTATT = ZUSTAND / "setzer"
AUSGABE = ZUSTAND / "setzer_fertig"

#: Trocken: kein Modellaufruf, der Text des Auftrags wird gesetzt, wie er ist.
TROCKEN = os.getenv("UNIVERSE_TROCKEN", "ja").strip().lower() in ("1", "ja", "true", "yes")
#: Das Modell, das die Gliederung schreibt - dasselbe wie im ganzen Universe.
MODELL = modellwahl.MODELL

#: Seitenformat und Raender in Punkt (1 Punkt = 1/72 Zoll). A4.
SEITE = (595.28, 841.89)
RAND = 56.0

#: Hoechstens so viele Abschnitte - ein Dokument, kein Buch.
ABSCHNITTE_MAX = 12

#: Welches Kit die Farben liefert, wenn der Auftrag keins nennt.
KIT_STANDARD = "stadtkrone"
