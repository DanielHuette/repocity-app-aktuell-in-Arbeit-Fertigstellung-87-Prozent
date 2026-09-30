"""Pfade und Stellschrauben des Deep Researchers."""
from __future__ import annotations

import json
import os
from pathlib import Path

import umgebung  # liest die .env, damit Schlüssel aus einer Hand kommen

umgebung.laden()

# Das Modell kennt nur eine Stelle: universe/kern/modellwahl.py. Ueber den
# Pfad geladen, nicht importiert - im Universe tragen mehrere Ordner
# gleichnamige Module, ein normaler Import erwischt das falsche.
import importlib.util as _iu
_mw = _iu.spec_from_file_location(
    "kern_modellwahl", Path(__file__).resolve().parent.parent / "kern" / "modellwahl.py")
modellwahl = _iu.module_from_spec(_mw)
_mw.loader.exec_module(modellwahl)

BASIS = Path(os.environ.get("RECHERCHE_BASIS", Path(__file__).resolve().parent))
KONFIG_DATEI = BASIS / "konfiguration.json"
DATEN = Path(os.environ.get("RECHERCHE_DATEN", BASIS / "daten"))

STANDARD: dict = {
    "suche": {
        "maschine": "bing",
        "quellen_je_frage": 8,
        "sprachen": ["de", "en"],
        "sperrliste": ["pinterest.", "facebook.com", "instagram.com", "x.com",
                       "tiktok.com", "quora.com"],
        "mindestzeichen": 800
    },
    "ablage": {
        "eingang": r"C:\AI_Projekte\Neustart\mein_ki_gehirn\eingang\deep_researcher",
        "ausgang": str(BASIS / "ausgang")
    },
    "modell": {
        "name": modellwahl.MODELL,
        "schluessel_umgebung": "ANTHROPIC_API_KEY"
    }
}


def _mischen(basis: dict, neu: dict) -> dict:
    ergebnis = dict(basis)
    for schluessel, wert in neu.items():
        if isinstance(wert, dict) and isinstance(ergebnis.get(schluessel), dict):
            ergebnis[schluessel] = _mischen(ergebnis[schluessel], wert)
        else:
            ergebnis[schluessel] = wert
    return ergebnis


def laden() -> dict:
    if KONFIG_DATEI.exists():
        return _mischen(STANDARD, json.loads(KONFIG_DATEI.read_text(encoding="utf-8")))
    return json.loads(json.dumps(STANDARD))