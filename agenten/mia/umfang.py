# -*- coding: utf-8 -*-
"""Wieviel spricht Mia ueberhaupt? Gezaehlt, nicht geschaetzt."""
import json, re
from pathlib import Path

UNIVERSE = Path(r"C:\AI_Projekte\Neustart\universe")

TEXT = {"gruss","hinweis","weiter","abbruch","titel","kurz","warum","mehr",
        "text","nochmal","knopf","abwinken","einstellen","schritte"}

def saetze(o, feld=None):
    if isinstance(o, dict):
        for k, v in o.items():
            if k.startswith("_"): continue
            yield from saetze(v, k)
    elif isinstance(o, list):
        for x in o: yield from saetze(x, feld)
    elif isinstance(o, str) and feld in TEXT:
        yield o

teile = {}

f = json.loads((UNIVERSE / "fuehrung.json").read_text(encoding="utf-8"))
teile["Fuehrung (Halte, Eroeffnung, Abschluss, Abschnitte)"] = list(saetze(f))

r = json.loads((UNIVERSE / "mia" / "regeln.json").read_text(encoding="utf-8"))
std = list(r.get("standardantworten", {}).values())
std.append(r.get("offenlegung", {}).get("text_erste_antwort", ""))
teile["Standardantworten und Offenlegung"] = [s for s in std if s]

gesamt_z = 0
gesamt_w = 0
print("%-52s %7s %7s" % ("", "Zeichen", "Woerter"))
for name, liste in teile.items():
    z = sum(len(s) for s in liste)
    w = sum(len(s.split()) for s in liste)
    gesamt_z += z; gesamt_w += w
    print("%-52s %7d %7d   (%d Stuecke)" % (name, z, w, len(liste)))
print("%-52s %7d %7d" % ("zusammen", gesamt_z, gesamt_w))

# Sprechzeit: gemessene 165 Woerter/Minute (Zielwert der Regie)
minuten = gesamt_w / 165
print("\nSprechzeit bei 165 Woertern/Minute: %.1f Minuten" % minuten)

print("\nWas das kostet, je Anbieter (Preis je 1 Mio. Zeichen):")
preise = [
    ("ElevenLabs v3 (Creator-Abo 22 $/100k)", 220.0),
    ("ElevenLabs v3 (API-Grosstarif)", 100.0),
    ("Cartesia Sonic 3.6", 49.0),
    ("Google Gemini 3.1 Flash TTS", 18.3),
    ("Inworld Realtime TTS-2", 20.8),
]
for name, je_mio in preise:
    usd = gesamt_z / 1_000_000 * je_mio
    print("  %-42s %6.2f $   (%.2f $ je Neuaufnahme)" % (name, usd, usd))
print("\nEine Neuaufnahme heisst: alles noch einmal, weil ein Text sich geaendert hat.")
