# -*- coding: utf-8 -*-
"""Ein Zeilenende fuer alles - nachsehen und geradeziehen.

Am Ende jeder Zeile einer Textdatei steht ein unsichtbares Zeichen. Windows
setzt dort zwei, alle anderen Systeme eines. Beide bedeuten dasselbe - aber
wer ueber zwei Zeilen sucht und die andere Variante erwartet, findet nichts.
Genau daran sind am 09.09.2026 sechs Gegenproben gestorben, ohne dass eine
einzige Pruefung rot wurde, und eine Sicherheitssperre im Worker blieb
abgeschaltet liegen.

Deshalb gilt im ganzen Projekt das eine Zeichen. Regel 1 in START.md.

    python universe/kern/zeilenenden.py            nachsehen, nichts aendern
    python universe/kern/zeilenenden.py geradeziehen
"""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
WURZEL = UNIVERSE.parent

#: Was als Textdatei gilt. Bilder, Klaenge und Pakete bleiben unangetastet.
ARTEN = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".kt", ".kts", ".json",
         ".jsonc", ".md", ".css", ".html", ".astro", ".svg", ".txt", ".yml",
         ".yaml", ".toml", ".xml", ".gradle", ".properties", ".env",
         ".jsonl", ".pine", ".sh", ".bat", ".ps1")

#: Ordner, die niemandem gehoeren: fremder Code, Zwischenstaende, Ablage.
AUSSEN = {"node_modules", "__pycache__", ".git", ".gradle", "build",
          "_archiv", "dist", ".venv", "venv", "zeichenbrett", "chroma"}

#: Diese beiden Dateiarten will Windows wirklich mit zwei Zeichen.
#: Eine .bat mit dem einen Zeichen fuehrt Befehle falsch aus.
WINDOWS_BRAUCHT = (".bat", ".cmd")


def _gehoert_dazu(datei: Path) -> bool:
    if datei.suffix.lower() not in ARTEN:
        return False
    if datei.suffix.lower() in WINDOWS_BRAUCHT:
        return False
    return not (AUSSEN & set(datei.parts))


def ausreisser(wurzel: Path) -> list[Path]:
    """Jede Textdatei, die zwei Zeichen benutzt statt einem."""
    gefunden = []
    for datei in sorted(wurzel.rglob("*")):
        if not datei.is_file() or not _gehoert_dazu(datei):
            continue
        try:
            if b"\r\n" in datei.read_bytes():
                gefunden.append(datei)
        except OSError:
            continue
    return gefunden


def geradeziehen(dateien: list[Path]) -> int:
    """Byteweise umschreiben - der Inhalt bleibt Zeichen fuer Zeichen gleich."""
    getan = 0
    for datei in dateien:
        roh = datei.read_bytes()
        datei.write_bytes(roh.replace(b"\r\n", b"\n"))
        getan += 1
    return getan


def _main(argumente: list[str]) -> int:
    ziel = UNIVERSE
    tun = argumente and argumente[0] == "geradeziehen"

    liste = ausreisser(ziel)
    if not liste:
        print("Alle Textdateien benutzen dasselbe Zeilenende.")
        return 0

    print("%d Dateien scheren aus:" % len(liste))
    for datei in liste[:40]:
        print("   %s" % datei.relative_to(WURZEL))
    if len(liste) > 40:
        print("   ... und %d weitere" % (len(liste) - 40))

    if not tun:
        print("\nZum Geradeziehen:")
        print("   python universe/kern/zeilenenden.py geradeziehen")
        return 1

    print("\n%d Dateien geradegezogen." % geradeziehen(liste))
    rest = ausreisser(ziel)
    if rest:
        print("ACHTUNG: %d scheren immer noch aus." % len(rest))
        return 1
    print("Jetzt benutzen alle dasselbe Zeilenende.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
