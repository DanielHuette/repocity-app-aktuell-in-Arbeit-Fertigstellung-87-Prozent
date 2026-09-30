"""Trockenlauf: `python probe.py "Thema"`.

Baut eine vollstaendige Schulung ohne Netz, ohne Schluessel, ohne Modell.
Das Ergebnis ist eine HTML-Datei, die man oeffnen und wirklich durchklicken
kann — mit Aufgaben, Sperre und XP. Nur die Inhalte sind Platzhalter.

Das prueft die Leitung, nicht den Lehrstoff.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    thema = " ".join(sys.argv[1:]) or "Sicherer Umgang mit KI im Arbeitsalltag"

    hier = Path(__file__).resolve().parent
    os.environ.setdefault("UNIVERSE_ZUSTAND", str(hier / "_probe"))
    os.environ["UNIVERSE_TROCKEN"] = "ja"

    import einstellungen as e
    import animation
    import erzaehler
    import strasse
    from modelle import Auftrag

    print(f"Thema:     {thema}")
    print(f"Ablage:    {e.ZUSTAND}")
    print(f"Erzähler:  {'edge-tts da' if erzaehler.verfuegbar() else 'kein edge-tts, bleibt stumm'}")
    print(f"Animation: {'HyperFrames an' if e.HYPERFRAMES_AN and animation.verfuegbar() else 'aus'}")

    auftrag = Auftrag(thema=thema, level_anzahl=4, minuten=20, trocken=True)
    ergebnis = strasse.produzieren(auftrag)

    print()
    print("Zustand: " + ergebnis.zustand.value)
    for zeile in ergebnis.protokoll:
        print("  " + zeile)
    if ergebnis.fehler:
        print("Fehler:  " + ergebnis.fehler)
    if ergebnis.curriculum:
        print(f"Level:   {len(ergebnis.curriculum.level)}")
        print("Arten:   " + ", ".join(
            l.aufgabe.art for l in ergebnis.curriculum.level if l.aufgabe))
    if ergebnis.kurs:
        print("Kurs:    " + str(ergebnis.kurs))
        print("         (im Browser oeffnen und durchklicken)")
    return 0 if ergebnis.kurs else 1


if __name__ == "__main__":
    raise SystemExit(main())
