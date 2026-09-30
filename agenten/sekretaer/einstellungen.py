"""Pfade und Fristen des Sekretärs."""
from __future__ import annotations

import json
import os
from pathlib import Path

import umgebung

umgebung.laden()

BASIS = Path(os.environ.get("SEKRETAER_BASIS", Path(__file__).resolve().parent))
UNIVERSE = BASIS.parent
ZUSTAND = Path(os.environ.get("UNIVERSE_ZUSTAND", UNIVERSE / "zustand"))
KONFIG_DATEI = BASIS / "konfiguration.json"

VORLAGE_DATEI = ZUSTAND / "vorlage.json"
QUITTIERT_DATEI = ZUSTAND / "quittiert.json"

STANDARD: dict = {
    "fristen": {
        "bewerbung_nachfassen_tage": 14,
        "wohnung_nachfassen_tage": 5,
        "eingang_liegen_tage": 2,
        "postausgang_liegen_stunden": 12,
    },
    "quellen": {
        "bewerbungen": str(UNIVERSE / "bewerbungs_agent" / "daten" / "bewerbungen.json"),
        "wohnungen": str(UNIVERSE / "wohnungs_agent" / "daten" / "angebote.json"),
        "eingaenge": [
            r"C:\AI_Projekte\Neustart\mein_ki_gehirn\eingang\deep_researcher",
            r"C:\AI_Projekte\Neustart\mein_ki_gehirn\eingang\github_scout",
        ],
    },
    "melden": True,
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