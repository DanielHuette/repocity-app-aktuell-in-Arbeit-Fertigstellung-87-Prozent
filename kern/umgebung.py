"""Die .env einlesen, damit jeder Agent dieselben Zugangsdaten findet.

Gesucht wird zuerst neben dem Universe, dann eine Ebene darüber:
  universe/.env
  Neustart/.env

Was schon in der Umgebung steht, bleibt stehen — eine gesetzte Variable schlägt
die Datei. So kann ein Container seine Werte mitbringen, ohne dass eine
vergessene Datei dazwischenfunkt.

Aufrufen mit `python kern/umgebung.py`, dann sagt er, was er gefunden hat und
was an der Datei nicht stimmt. Werte zeigt er nie an.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

UNIVERSE = Path(__file__).resolve().parent.parent
ORTE = [UNIVERSE / ".env", UNIVERSE.parent / ".env"]

GEHEIM = re.compile(r"key|token|pass|secret|schluessel|schlüssel|pw\b", re.IGNORECASE)


def datei_finden() -> Path | None:
    for ort in ORTE:
        if ort.exists():
            return ort
    return None


def zerlegen(roh: str) -> tuple[dict, list, list]:
    """Gibt Werte, fehlerhafte Zeilen und doppelte Schlüssel zurück."""
    werte: dict[str, str] = {}
    fehlerhaft: list[tuple[int, str]] = []
    doppelt: list[str] = []

    for nummer, zeile in enumerate(roh.splitlines(), 1):
        text = zeile.strip().lstrip("\ufeff")
        if not text or text.startswith("#"):
            continue
        if text.lower().startswith("export "):
            text = text[7:].lstrip()
        if "=" not in text:
            fehlerhaft.append((nummer, text))
            continue
        schluessel, wert = text.split("=", 1)
        schluessel = schluessel.strip().lstrip("\ufeff")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schluessel):
            fehlerhaft.append((nummer, text))
            continue
        wert = wert.strip()
        if len(wert) >= 2 and wert[0] == wert[-1] and wert[0] in "\"'":
            wert = wert[1:-1]
        if schluessel in werte:
            doppelt.append(schluessel)
        werte[schluessel] = wert
    return werte, fehlerhaft, doppelt


def laden(pfad: Path | None = None, ueberschreiben: bool = False) -> dict:
    ziel = pfad or datei_finden()
    if ziel is None:
        return {"datei": None, "gesetzt": [], "vorhanden": [], "leer": [],
                "fehlerhaft": [], "doppelt": []}
    roh = ziel.read_text(encoding="utf-8-sig", errors="replace")
    werte, fehlerhaft, doppelt = zerlegen(roh)

    gesetzt, vorhanden, leer = [], [], []
    for schluessel, wert in werte.items():
        if not wert:
            leer.append(schluessel)
            continue
        if schluessel in os.environ and not ueberschreiben:
            vorhanden.append(schluessel)
            continue
        os.environ[schluessel] = wert
        gesetzt.append(schluessel)

    return {"datei": ziel, "gesetzt": gesetzt, "vorhanden": vorhanden, "leer": leer,
            "fehlerhaft": fehlerhaft, "doppelt": doppelt}


def bericht() -> str:
    ergebnis = laden()
    if ergebnis["datei"] is None:
        return "Keine .env gefunden. Gesucht: " + ", ".join(str(o) for o in ORTE)

    zeilen = [f"Gelesen: {ergebnis['datei']}", ""]
    if ergebnis["gesetzt"]:
        zeilen.append("Gesetzt:")
        zeilen += [f"  {name}  ({'geheim' if GEHEIM.search(name) else 'offen'})"
                   for name in ergebnis["gesetzt"]]
    if ergebnis["vorhanden"]:
        zeilen.append("Stand schon in der Umgebung, Datei ignoriert: "
                      + ", ".join(ergebnis["vorhanden"]))
    if ergebnis["leer"]:
        zeilen.append("Leer, wird übersprungen: " + ", ".join(ergebnis["leer"]))
    if ergebnis["doppelt"]:
        zeilen.append("")
        zeilen.append("ACHTUNG doppelt vergeben, der letzte Eintrag gewinnt: "
                      + ", ".join(sorted(set(ergebnis["doppelt"]))))
    if ergebnis["fehlerhaft"]:
        zeilen.append("")
        zeilen.append("Zeilen ohne Gleichheitszeichen oder mit ungültigem Namen — "
                      "die kann kein Programm lesen:")
        zeilen += [f"  Zeile {nummer}: {_kurz(text)}" for nummer, text in ergebnis["fehlerhaft"]]
    return "\n".join(zeilen)


def _kurz(text: str) -> str:
    """Zeigt die Form der Zeile, nicht ihren Inhalt."""
    return (text[:18] + " …") if len(text) > 18 else text


PLATZHALTER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def einsetzen(gebilde, streng: bool = False):
    """Ersetzt ${NAME} durch den Wert aus der Umgebung — in Text, Listen und Zuordnungen.

    So steht die Struktur in einer Datei, die niemandem schadet, und das Geheimnis
    nur in der .env. Fehlt ein Wert, bleibt der Platzhalter stehen; mit streng=True
    gibt es stattdessen einen Fehler.
    """
    laden()
    if isinstance(gebilde, str):
        def ersetzen(treffer):
            name = treffer.group(1)
            wert = os.environ.get(name)
            if wert is None:
                if streng:
                    raise KeyError(f"{name} fehlt in der Umgebung")
                return treffer.group(0)
            return wert
        return PLATZHALTER.sub(ersetzen, gebilde)
    if isinstance(gebilde, dict):
        return {k: einsetzen(v, streng) for k, v in gebilde.items()}
    if isinstance(gebilde, list):
        return [einsetzen(v, streng) for v in gebilde]
    return gebilde


def offene_platzhalter(gebilde) -> list[str]:
    """Welche ${NAME} nach dem Einsetzen noch offen sind."""
    import json as _json
    return sorted(set(PLATZHALTER.findall(_json.dumps(gebilde, ensure_ascii=False))))


def fehlt(*namen: str) -> list[str]:
    """Welche der genannten Variablen nach dem Laden immer noch fehlen."""
    laden()
    return [name for name in namen if not os.environ.get(name)]


if __name__ == "__main__":
    print(bericht())