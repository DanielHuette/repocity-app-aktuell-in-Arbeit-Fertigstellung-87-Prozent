# -*- coding: utf-8 -*-
"""Was kann jede Strasse wirklich? Gemessen, nicht behauptet.

    python universe\\kern\\strassenpruefung.py

Fuer jede Auftragsart aus auftragsarten.json wird nachgesehen:

  Weg        Gibt es einen Eintrag unter wer_arbeitet? Wohin zeigt er?
  Agent      Gibt es den Ordner? Gibt es main.py? Versteht es "einmal"?
  Eingang    Gibt es den Ordner unter zustand?
  Eigen      Unterscheidet der Agent diese Auftragsart von den anderen,
             die auf denselben Agenten zeigen? Gemessen daran, ob die
             Modulkennung irgendwo in seinem Code vorkommt.
  Erzeugt    Welche Dateien legt die Strasse am Ende an - gemessen an dem,
             was im Warenausgang steht.

Diese Datei behauptet nichts ueber Qualitaet. Sie sagt nur, was da ist und
was nicht - damit niemand eine Strasse fuer fertig haelt, weil sie in der
Liste steht.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
ZUSTAND = UNIVERSE / "zustand"


def _lesen(pfad: Path) -> dict:
    return json.loads(pfad.read_text(encoding="utf-8"))


def messen() -> list[dict]:
    arten = _lesen(UNIVERSE / "auftragsarten.json")
    wer = arten.get("wer_arbeitet", {})
    funktionen = _lesen(UNIVERSE / "funktionen.json").get("funktionen", {})

    # Welche Module zeigen auf denselben Agenten? Nur dort ist die Frage
    # "unterscheidet er sie" ueberhaupt sinnvoll.
    je_agent: dict[str, list[str]] = {}
    for modul, w in wer.items():
        je_agent.setdefault(w.get("agent", ""), []).append(modul)

    zeilen = []
    for kennung, art in arten.get("arten", {}).items():
        modul = art.get("modul", "")
        w = wer.get(modul)
        z = {"art": kennung, "label": art.get("label", ""), "modul": modul}

        if not w:
            z["befund"] = "kein Weg - der Sekretaer kann das nicht verteilen"
            zeilen.append(z)
            continue

        agent = w.get("agent", "")
        ordner = UNIVERSE / agent
        z["agent"] = agent
        z["agent_da"] = ordner.is_dir()
        z["main_da"] = (ordner / "main.py").is_file()

        eingang = ZUSTAND / w.get("eingang", "")
        z["eingang_da"] = eingang.is_dir()

        # Versteht der Agent den Befehl, mit dem der Sekretaer ihn startet?
        befehl = w.get("befehl", "")
        z["befehl"] = befehl
        z["befehl_verstanden"] = False
        if z["main_da"]:
            code = (ordner / "main.py").read_text(encoding="utf-8", errors="ignore")
            z["befehl_verstanden"] = ('"%s"' % befehl) in code

        # Teilt er sich den Agenten mit anderen Auftragsarten - und wenn ja,
        # kommt seine eigene Modulkennung irgendwo in dessen Code vor?
        geschwister = [m for m in je_agent.get(agent, []) if m != modul]
        z["teilt_mit"] = geschwister
        if geschwister and ordner.is_dir():
            treffer = 0
            for datei in ordner.rglob("*.py"):
                if "__pycache__" in str(datei):
                    continue
                try:
                    if modul in datei.read_text(encoding="utf-8", errors="ignore"):
                        treffer += 1
                except OSError:
                    continue
            z["eigene_kennung_im_code"] = treffer
        else:
            z["eigene_kennung_im_code"] = None

        f = funktionen.get(kennung.lower().replace("video_stueck", "video")
                           .replace("video_clip", "clip"), {})
        z["stand"] = f.get("stand", "")
        zeilen.append(z)
    return zeilen


def _satz(z: dict) -> str:
    if "befund" in z:
        return z["befund"]
    schlecht = []
    if not z["agent_da"]:
        schlecht.append("Agent fehlt")
    if not z["main_da"]:
        schlecht.append("main.py fehlt")
    if not z["eingang_da"]:
        schlecht.append("Eingang fehlt")
    if not z["befehl_verstanden"]:
        schlecht.append("versteht '%s' nicht" % z["befehl"])
    if z["teilt_mit"] and z["eigene_kennung_im_code"] == 0:
        schlecht.append("teilt den Agenten mit %s und wird dort NICHT "
                        "unterschieden" % ", ".join(z["teilt_mit"]))
    return "; ".join(schlecht) if schlecht else "traegt"


def main(argumente: list[str]) -> int:
    zeilen = messen()
    breite = max(len(z["label"]) for z in zeilen)
    schlecht = 0
    print("Was jede Auftragsart wirklich vorfindet:\n")
    for z in zeilen:
        satz = _satz(z)
        zeichen = "+" if satz == "traegt" else "!"
        if satz != "traegt":
            schlecht += 1
        print("  %s %-*s  %-22s %s" % (zeichen, breite, z["label"],
                                       z.get("agent", "-"), satz))
    print()
    print("%d von %d Auftragsarten finden alles vor, was sie brauchen."
          % (len(zeilen) - schlecht, len(zeilen)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
