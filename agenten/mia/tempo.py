# -*- coding: utf-8 -*-
"""Von jeder Stimmprobe eine zuegigere Fassung - zum Vergleichen.

Warum ueberhaupt: die Maschine spricht von sich aus rund 105 Woerter je
Minute, gemessen am 09.09. Als vertrauenswuerdig gemessen wurden 162-240
(englisch), fuer Deutsch sind 120-180 ueblich. Ob langsam hier warm wirkt
oder schleppend, entscheidet das Ohr - also gibt es beides.

Gerechnet, nicht gesetzt: der Faktor ist Zielwert geteilt durch gemessenen
Wert, je Stimme einzeln. Die Tonhoehe bleibt dabei, wo sie war - `atempo`
dehnt die Zeit, nicht die Stimme.

    python universe/mia/tempo.py            145 Woerter/Minute
    python universe/mia/tempo.py 160        ein anderer Zielwert
"""
from __future__ import annotations

import json
import subprocess

# Kein Konsolenfenster fuer Hilfsprogramme (ffmpeg, node, npm, ...).
# Eine Quelle: universe/kern/ohne_fenster.py - ueber den Pfad geladen,
# weil im Universe zwoelf Ordner gleichnamige Module haben.
import importlib.util as _iu
from pathlib import Path as _P
for _o in _P(__file__).resolve().parents:
    _k = _o / "kern" / "ohne_fenster.py"
    if _k.exists():
        _s = _iu.spec_from_file_location("ohne_fenster", _k)
        _m = _iu.module_from_spec(_s)
        _s.loader.exec_module(_m)
        break
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
PROBEN = HIER / "stimmproben"

ZIEL_WPM = float(sys.argv[1]) if len(sys.argv) > 1 else 145.0


def _dauer(datei: Path) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(datei)],
        capture_output=True, text=True, check=True).stdout.strip())


def _text() -> str:
    f = json.loads((UNIVERSE / "fuehrung.json").read_text(encoding="utf-8"))
    e = f["eroeffnung"]
    return e["gruss"] + " " + e["hinweis"]


if __name__ == "__main__":
    woerter = len(_text().split())
    for datei in sorted(PROBEN.glob("*.mp3")):
        if datei.stem.endswith("_zuegig"):
            continue
        ist = woerter / _dauer(datei) * 60
        faktor = ZIEL_WPM / ist
        ziel = datei.with_name(datei.stem + "_zuegig.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(datei),
             "-filter:a", "atempo=%.4f" % faktor,
             "-c:a", "libmp3lame", "-q:a", "2", str(ziel)],
            check=True)
        print("  %-14s %5.0f -> %5.0f Woerter/Minute   (mal %.2f)   %s"
              % (datei.stem, ist, woerter / _dauer(ziel) * 60, faktor,
                 ziel.name))
