"""Pfade und Stellschrauben des Kurators."""
from __future__ import annotations

import json
import os
from pathlib import Path

import umgebung  # liest die .env, damit Schlüssel aus einer Hand kommen

umgebung.laden()

BASIS = Path(os.environ.get("KURATOR_BASIS", Path(__file__).resolve().parent))
DATEN = Path(os.environ.get("KURATOR_DATEN", BASIS / "daten"))
KONFIG_DATEI = BASIS / "konfiguration.json"

STANDARD: dict = {
    "eingaenge": [
        r"C:\AI_Projekte\Neustart\mein_ki_gehirn\eingang\deep_researcher",
        r"C:\AI_Projekte\Neustart\mein_ki_gehirn\eingang\github_scout",
    ],
    "saeulen": {
        "wissen": r"C:\AI_Projekte\Neustart\mein_ki_gehirn\wissen",
        "atome": r"C:\AI_Projekte\Neustart\mein_ki_gehirn\atome",
        "vektor": r"C:\AI_Projekte\Neustart\mein_ki_gehirn\chroma",
        "verbesserung": r"C:\AI_Projekte\Neustart\mein_ki_gehirn\verbesserung",
    },
    "vektor": {
        "schreiben": True,
        # Ein Regal fuer alle Schreiber. Getrennte Sammlungen hatten den Preis,
        # dass das Gehirn die Eintraege des Kurators nie zu sehen bekam.
        "sammlung": "wissen",
        "modell": "text-embedding-3-small",
        "schluessel_umgebung": "OPENAI_API_KEY",
        "haeppchen_zeichen": 1800,
        "ueberlappung": 250,
    },
    "pruefung": {
        "pflichtfelder": ["title", "typ", "erfasst_von"],
        "mindestzeichen_notiz": 400,
        # Der Titel muss sagen, worum es geht - nicht, wie die Datei heisst.
        # Vier Woerter, weil drei fuer einen Sachtitel nie reichen und fuenf
        # brauchbare Titel wie "Obsidian: Notizen, Verlinkung, Graphansicht"
        # ausschliessen wuerden. 120 Zeichen, weil eine Trefferliste sonst umbricht.
        "titel_mindestwoerter": 4,
        "titel_hoechstzeichen": 120,
        "titel_verbotene_reste": ["transcript", "untitled", "ohne titel"],
        "atom_mindestzeichen": 20,
        "doppelung_schwelle": 0.92,
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


def ordner_anlegen() -> None:
    DATEN.mkdir(parents=True, exist_ok=True)