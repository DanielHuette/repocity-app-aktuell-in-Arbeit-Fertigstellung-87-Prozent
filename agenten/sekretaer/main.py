"""Sekretär — die Stelle zwischen den Agenten und der RepoCity App.

Er arbeitet nicht selbst. Er sieht nach, was die Agenten hinterlassen haben,
und macht daraus eine Vorlage: was entschieden werden muss, was fällig ist,
was gefunden wurde, was schiefging.

  python main.py stand                Übersicht in der Konsole
  python main.py vorlegen             Vorlage bauen und an die App melden
  python main.py vorlage              die letzte Vorlage anzeigen
  python main.py quittieren <vorgang> einen Punkt als erledigt abhaken
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import einstellungen as e
import meldung
import sammeln

AGENT = "sekretaer"


def _quittiert() -> set[str]:
    if not Path(e.QUITTIERT_DATEI).exists():
        return set()
    try:
        return set(json.loads(Path(e.QUITTIERT_DATEI).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return set()


def _quittiert_sichern(vorgaenge: set[str]) -> None:
    Path(e.QUITTIERT_DATEI).parent.mkdir(parents=True, exist_ok=True)
    Path(e.QUITTIERT_DATEI).write_text(json.dumps(sorted(vorgaenge), ensure_ascii=False),
                                       encoding="utf-8", newline="")


def _vorlage_bauen(konfig: dict) -> dict:
    erledigt = _quittiert()
    saetze = sammeln.meldungen()
    vorlage = {
        "erstellt_am": datetime.now().isoformat(timespec="seconds"),
        "freigaben": [f for f in sammeln.freigaben(konfig)
                      if f.get("vorgang") not in erledigt],
        "fristen": [f for f in sammeln.fristen(konfig)
                    if f.get("vorgang") not in erledigt],
        "stoerungen": sammeln.stoerungen(saetze),
        "funde": [s for s in saetze if s.get("art") in ("fund", "wissen")],
        "abgelehnte_abrufe": sammeln.abgelehnte_abrufe(),
    }
    vorlage["offen"] = len(vorlage["freigaben"]) + len(vorlage["fristen"]) + len(vorlage["stoerungen"])
    return vorlage


def befehl_stand(args) -> int:
    konfig = e.laden()
    vorlage = _vorlage_bauen(konfig)

    if vorlage["stoerungen"]:
        print("STÖRUNGEN")
        for satz in vorlage["stoerungen"][:10]:
            print(f"  {satz.get('absender',''):18} {satz.get('text','')[:80]}")
        print()

    if vorlage["freigaben"]:
        print("WARTET AUF DEIN JA")
        for satz in vorlage["freigaben"][:15]:
            print(f"  [{satz['zustand']:8}] {satz['von']:16} an {satz['an'][:32]:34} "
                  f"{satz['was'][:44]}")
        print()

    if vorlage["fristen"]:
        print("FÄLLIG")
        for satz in vorlage["fristen"][:15]:
            print(f"  {satz['tage']:3} Tage  {satz['bereich']:10} {satz['was'][:70]}")
        print()

    if vorlage["funde"]:
        print("GEFUNDEN")
        for satz in vorlage["funde"][:10]:
            print(f"  {satz.get('absender',''):18} {satz.get('zusammenfassung','')[:74]}")
        print()

    if vorlage["abgelehnte_abrufe"]:
        print("ABGELEHNTE ABRUFE (robots.txt, Bot-Schutz, TDM-Widerspruch)")
        nach_stufe: dict[str, int] = {}
        for satz in vorlage["abgelehnte_abrufe"]:
            nach_stufe[satz.get("stufe", "?")] = nach_stufe.get(satz.get("stufe", "?"), 0) + 1
        for stufe, anzahl in sorted(nach_stufe.items()):
            print(f"  {anzahl:4}× {stufe}")
        print()

    if not vorlage["offen"]:
        print("Nichts offen.")
    else:
        print(f"{vorlage['offen']} Punkte offen.")
    return 0


def befehl_vorlegen(args) -> int:
    konfig = e.laden()
    vorlage = _vorlage_bauen(konfig)
    Path(e.VORLAGE_DATEI).parent.mkdir(parents=True, exist_ok=True)
    Path(e.VORLAGE_DATEI).write_text(
        json.dumps(vorlage, ensure_ascii=False, indent=1), encoding="utf-8", newline="")

    zeilen = []
    for satz in vorlage["stoerungen"][:5]:
        zeilen.append(f"Störung — {satz.get('absender','')}: {satz.get('text','')[:90]}")
    for satz in vorlage["freigaben"][:8]:
        zeilen.append(f"Freigabe — {satz['von']}: {satz['was'][:70]} an {satz['an']}")
    for satz in vorlage["fristen"][:8]:
        zeilen.append(f"Fällig seit {satz['tage']} Tagen — {satz['was'][:70]}")
    for satz in vorlage["funde"][:5]:
        zeilen.append(f"Fund — {satz.get('absender','')}: {satz.get('zusammenfassung','')[:80]}")

    angekommen = False
    if konfig.get("melden"):
        angekommen = meldung.melde(
            absender=AGENT, art="vorlage",
            zusammenfassung=(f"{len(vorlage['freigaben'])} Freigaben, "
                             f"{len(vorlage['fristen'])} Fristen, "
                             f"{len(vorlage['stoerungen'])} Störungen"),
            text="\n".join(zeilen) or "Nichts offen.",
            daten={"offen": vorlage["offen"], "vorlage": str(e.VORLAGE_DATEI)})

    print(e.VORLAGE_DATEI)
    print(f"{vorlage['offen']} Punkte offen. "
          + ("An die App gemeldet." if angekommen
             else "Kein Hub eingerichtet — die Vorlage liegt im Tagebuch."))
    return 0


def befehl_vorlage(args) -> int:
    if not Path(e.VORLAGE_DATEI).exists():
        print("Noch keine Vorlage. Erst 'vorlegen' aufrufen.")
        return 0
    print(Path(e.VORLAGE_DATEI).read_text(encoding="utf-8"))
    return 0


def befehl_quittieren(args) -> int:
    erledigt = _quittiert()
    erledigt.add(args.vorgang)
    _quittiert_sichern(erledigt)
    print(f"{args.vorgang}: abgehakt")
    return 0


def hauptprogramm(argumente=None) -> int:
    zerleger = argparse.ArgumentParser(prog="sekretaer", description=__doc__)
    unter = zerleger.add_subparsers(dest="befehl", required=True)

    unter.add_parser("stand").set_defaults(funktion=befehl_stand)
    unter.add_parser("vorlegen").set_defaults(funktion=befehl_vorlegen)
    unter.add_parser("vorlage").set_defaults(funktion=befehl_vorlage)

    quittieren = unter.add_parser("quittieren")
    quittieren.add_argument("vorgang")
    quittieren.set_defaults(funktion=befehl_quittieren)

    args = zerleger.parse_args(argumente)
    return args.funktion(args)


if __name__ == "__main__":
    sys.exit(hauptprogramm())