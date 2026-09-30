# -*- coding: utf-8 -*-
"""Werkzeug fuer die Titelkur: Zusammenfassungen ausgeben und Titel einsetzen.

Der Titel selbst entsteht nicht hier - den schreibt ein Modell. Diese Datei
macht nur die zwei mechanischen Haelften drumherum:

    python _titel_stapel.py lesen  --von 0 --bis 20 --ziel stapel_00.json
    python _titel_stapel.py setzen --datei stapel_00.json

`lesen` schreibt eine JSON-Liste mit Dateiname und Zusammenfassung. `setzen`
nimmt dieselbe Datei zurueck, erwartet zu jedem Eintrag ein Feld "titel" und
traegt es in den Kopf der Notiz ein. Alles andere am Kopf bleibt, wie es ist.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WISSEN = Path(r"C:\AI_Projekte\Neustart\mein_ki_gehirn\wissen")
KOPF = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
KAPPE = 1200


def _zusammenfassung(text: str) -> str:
    m = re.search(r"## Technische Zusammenfassung\s*\n(.*?)(?:\n## |\Z)", text, re.S)
    roh = (m.group(1) if m else KOPF.sub("", text)).strip()
    return re.sub(r"\s+", " ", roh)[:KAPPE]


def lesen(von: int, bis: int, ziel: Path) -> int:
    dateien = sorted(WISSEN.rglob("*.md"))[von:bis]
    heraus = []
    for d in dateien:
        try:
            t = d.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        heraus.append({"datei": d.name, "zusammenfassung": _zusammenfassung(t), "titel": ""})
    ziel.write_text(json.dumps(heraus, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="")
    print("%d Notizen nach %s" % (len(heraus), ziel))
    return 0


def setzen(datei: Path) -> int:
    eintraege = json.loads(datei.read_text(encoding="utf-8"))
    gesetzt = uebersprungen = 0
    for e in eintraege:
        titel = (e.get("titel") or "").strip()
        if not titel:
            uebersprungen += 1
            continue
        pfad = WISSEN / e["datei"]
        if not pfad.exists():
            uebersprungen += 1
            continue
        text = pfad.read_text(encoding="utf-8", errors="ignore")
        kopf = KOPF.match(text)
        if not kopf:
            uebersprungen += 1
            continue
        neuer_kopf = re.sub(r'(?m)^title:.*$', 'title: "%s"' % titel.replace('"', "'"),
                            kopf.group(1))
        if "title:" not in neuer_kopf:
            neuer_kopf = 'title: "%s"\n%s' % (titel.replace('"', "'"), neuer_kopf)
        pfad.write_text("---\n" + neuer_kopf + "\n---\n" + text[kopf.end():],
                        encoding="utf-8", newline="")
        gesetzt += 1
    print("gesetzt: %d, uebersprungen: %d" % (gesetzt, uebersprungen))
    return 0


def _main(argumente):
    z = argparse.ArgumentParser()
    unter = z.add_subparsers(dest="befehl", required=True)
    a = unter.add_parser("lesen")
    a.add_argument("--von", type=int, default=0)
    a.add_argument("--bis", type=int, default=20)
    a.add_argument("--ziel", required=True)
    b = unter.add_parser("setzen")
    b.add_argument("--datei", required=True)
    w = z.parse_args(argumente)
    if w.befehl == "lesen":
        return lesen(w.von, w.bis, Path(w.ziel))
    return setzen(Path(w.datei))


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
