# -*- coding: utf-8 -*-
"""Der Terminkoordinator - die Uhr des Sekretaers.

Er fuehrt keinen eigenen Kalender. Der Kalender steht am Hub, dort traegt der
Nutzer ein (Webseite und App), dort legen die Agenten ein Vorstellungsgespraech
oder eine Besichtigung ab. Hier wird nur nachgesehen, was ansteht, und
rechtzeitig geweckt.

    python universe\\sekretaer\\termine.py stand        was ansteht
    python universe\\sekretaer\\termine.py wecken       faellige Rufe abschicken
    python universe\\sekretaer\\termine.py eintragen "Titel" 2026-09-20T14:30

Zwei Regeln, und beide stehen hier, weil sie beide schon einmal schiefgingen:

1. Zweimal wecken ist schlimmer als gar nicht wecken. Wer um sieben Uhr
   frueh dreimal geweckt wird, schaltet die Meldungen ab - und verpasst dann
   den Termin, um den es ging. Darum wird jeder abgeschickte Ruf gemerkt.

2. Ein Ruf, der zu spaet kommt, ist keiner. Laeuft die Wache eine Stunde
   nicht, holt sie nur nach, was hoechstens VERSPAETUNG_MIN alt ist - was
   laenger her ist, ist vorbei, und darueber wird der Nutzer nicht mitten in
   der Nacht geweckt.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent

#: Wo steht, was schon gerufen wurde. Neben den anderen Zustandsdateien.
GERUFEN = UNIVERSE / "zustand" / "termine_gerufen.json"

#: Was hoechstens nachgeholt wird. Eine halbe Stunde: laenger her heisst,
#: der Termin hat schon begonnen oder ist vorbei.
VERSPAETUNG_MIN = 30

#: Mehr als das wird nie auf einmal gerufen - sonst weckt ein Fehler im
#: Kalender das Handy zwanzigmal hintereinander.
HOECHSTENS_JE_LAUF = 5


def _laden(name: str, datei: str):
    """Ein Modul aus kern\\ ueber den Pfad laden.

    Ueber den Pfad, nicht mit import: im Universe tragen zwoelf Ordner
    gleichnamige Module, und ein gewoehnlicher Import erwischt das falsche.
    """
    schon = sys.modules.get(name)
    if schon is not None:
        return schon
    stelle = importlib.util.spec_from_file_location(name, UNIVERSE / "kern" / datei)
    modul = importlib.util.module_from_spec(stelle)
    sys.modules[name] = modul
    stelle.loader.exec_module(modul)
    return modul


muster = _laden("kern_muster", "muster.py")
weckruf = _laden("kern_weckruf", "weckruf.py")


# ------------------------------------------------------------------ Merken

def _gerufen_lesen() -> dict:
    if not GERUFEN.exists():
        return {}
    try:
        return json.loads(GERUFEN.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _gerufen_schreiben(stand: dict) -> None:
    """Nur behalten, was noch kommen kann - sonst waechst die Datei ewig."""
    grenze = (datetime.now() - timedelta(days=2)).isoformat(timespec="minutes")
    schlank = {k: v for k, v in stand.items() if v >= grenze}
    GERUFEN.parent.mkdir(parents=True, exist_ok=True)
    GERUFEN.write_text(json.dumps(schlank, ensure_ascii=False, indent=1),
                       encoding="utf-8", newline="")


# ------------------------------------------------------------------ Rechnen

def weckzeit(termin: dict) -> datetime | None:
    """Wann geweckt wird. None heisst: gar nicht."""
    minuten = int(termin.get("weckenMin") or 0)
    if minuten <= 0:
        return None
    try:
        beginn = datetime.fromisoformat(str(termin.get("beginn"))[:16])
    except ValueError:
        return None
    return beginn - timedelta(minutes=minuten)


def faellig(termine: list, jetzt: datetime, schon: dict) -> list:
    """Welche Termine jetzt einen Ruf brauchen.

    Faellig ist, was seine Weckzeit erreicht hat und noch nicht gerufen wurde -
    und was nicht laenger als VERSPAETUNG_MIN zurueckliegt.
    """
    aus = []
    for termin in termine:
        kennung = str(termin.get("id") or "")
        if not kennung or kennung in schon:
            continue
        wann = weckzeit(termin)
        if wann is None or wann > jetzt:
            continue
        if wann < jetzt - timedelta(minutes=VERSPAETUNG_MIN):
            continue
        aus.append(termin)
    aus.sort(key=lambda t: str(t.get("beginn", "")))
    return aus[:HOECHSTENS_JE_LAUF]


def _rufText(termin: dict) -> tuple[str, str]:
    beginn = str(termin.get("beginn", ""))
    uhr = beginn[11:16]
    tag = beginn[8:10] + "." + beginn[5:7] + "."
    titel = str(termin.get("titel") or "Termin")
    teile = [tag + " " + uhr + " Uhr"]
    if termin.get("ort"):
        teile.append(str(termin["ort"]))
    return titel, " · ".join(teile)


# ------------------------------------------------------------------ Handeln

def _abnahme(titel: str, text: str, termin: dict) -> dict:
    """Den Ruf messen lassen. Klemmt die Messung, geht er hinaus wie vorher."""
    try:
        abnahme = _laden("lebensabnahme", "lebensabnahme.py")
    except Exception:                                      # noqa: BLE001
        return {"darf_hinaus": True, "maengel": [], "grund": "nicht erreichbar"}
    try:
        return abnahme.ruf_pruefen(titel, text, termin)
    except Exception:                                      # noqa: BLE001
        return {"darf_hinaus": True, "maengel": [], "grund": "Messung nicht gelaufen"}


def wecken(nutzer: str = "", trocken: bool = False) -> dict:
    """Die faelligen Rufe abschicken. Zurueck kommt, was getan wurde."""
    alle, grund = muster.termine(nutzer=nutzer)
    if grund:
        return {"gerufen": 0, "grund": grund}
    schon = _gerufen_lesen()
    jetzt = datetime.now()
    dran = faellig(alle, jetzt, schon)
    if not dran:
        return {"gerufen": 0, "grund": ""}

    gerufen = 0
    uebergangen = 0
    for termin in dran:
        titel, text = _rufText(termin)

        # Erst messen, dann wecken. Ein Ruf ohne Titel oder ohne Zeit weckt
        # jemanden um sieben Uhr frueh fuer nichts - und wer einmal umsonst
        # geweckt wurde, schaltet die Meldungen ab.
        abnahme = _abnahme(titel, text, termin)
        if not abnahme["darf_hinaus"]:
            uebergangen += 1
            continue

        if not trocken:
            ergebnis = weckruf.wecken_nutzer(
                nutzer or "", "termin", titel, text,
                {"auftrag": str(termin.get("id")),
                 "beginn": str(termin.get("beginn", "")),
                 "ort": str(termin.get("ort", "")),
                 "quelle": "kalender"})
            if ergebnis.get("grund") and not ergebnis.get("gerufen"):
                # Kein Geraet, kein Netz: der Ruf liegt jetzt in weckrufe.jsonl
                # und geht beim naechsten Mal mit. Nicht abhaken - sonst waere
                # er endgueltig verloren.
                continue
        schon[str(termin.get("id"))] = jetzt.isoformat(timespec="minutes")
        gerufen += 1
    _gerufen_schreiben(schon)
    return {"gerufen": gerufen, "grund": "", "uebergangen": uebergangen}


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()

    if befehl == "stand":
        alle, grund = muster.termine()
        if grund:
            print("nicht bereit: %s" % grund)
            return 1
        if not alle:
            print("Kein Termin eingetragen.")
            return 0
        jetzt = datetime.now()
        schon = _gerufen_lesen()
        for termin in alle:
            wann = weckzeit(termin)
            hinweis = "-"
            if str(termin.get("id")) in schon:
                hinweis = "gerufen"
            elif wann is not None:
                hinweis = "weckt " + wann.strftime("%d.%m. %H:%M")
            print("  %-16s %-34s %s" % (str(termin.get("beginn", ""))[:16],
                                        str(termin.get("titel", ""))[:34], hinweis))
        print("\n%d Termin(e). Faellig jetzt: %d."
              % (len(alle), len(faellig(alle, jetzt, schon))))
        return 0

    if befehl == "wecken":
        ergebnis = wecken(trocken="--trocken" in argumente)
        if ergebnis["grund"]:
            print("nicht gerufen: %s" % ergebnis["grund"])
            return 1
        print("%d Ruf(e) abgeschickt." % ergebnis["gerufen"])
        return 0

    if befehl == "eintragen" and len(argumente) >= 3:
        termin, grund = muster.termin_ablegen(
            argumente[1], argumente[2],
            art=argumente[3] if len(argumente) > 3 else "sonstiges",
            quelle="sekretaer")
        if grund:
            print("nicht eingetragen: %s" % grund)
            return 1
        print("eingetragen: %s" % termin.get("id"))
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
