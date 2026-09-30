"""Mias Kosten aus dem Hub abholen und im Universe verbuchen.

Gezaehlt wird im Worker - dort faellt die Frage an, dort steht die
Tokenzahl. Gebucht wird hier, ueber verbrauch.py, damit Geld weiterhin
durch genau eine Stelle geht und im Bericht des Kostenstellenverantwortlichen
auftaucht.

Abgeholtes wird im Hub geloescht. Jede Frage wird genau einmal gebucht.

    python universe\\mia\\kosten_abholen.py            holen und buchen
    python universe\\mia\\kosten_abholen.py stand      nur nachsehen
"""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(KERN))

import hub          # noqa: E402
import umgebung     # noqa: E402
import verbrauch    # noqa: E402

umgebung.laden()

WEG = "/api/hub/mia/buchungen"


def holen() -> list[dict]:
    """Holt die Buchungen ab. POST, weil das Abholen sie im Hub loescht."""
    antwort = hub._rufen(WEG, {}, "POST")
    return antwort.get("buchungen", []) or []


def buchen(saetze: list[dict]) -> dict:
    summe = 0.0
    abgelehnt = 0
    for s in saetze:
        betrag = float(s.get("betrag_eur", 0.0))
        kostenstelle = s.get("kostenstelle") or "fragefenster"
        text = "Frage von %s (%d Token ein / %d aus)" % (
            s.get("kennung", "gast"), s.get("token_ein", 0), s.get("token_aus", 0))
        if s.get("abgelehnt"):
            text += " - Antwort verworfen: " + str(s.get("ablehnungsgrund", ""))
            abgelehnt += 1
        verbrauch.buchen(kostenstelle, betrag, text,
                         menge=int(s.get("token_ein", 0)) + int(s.get("token_aus", 0)),
                         modell=s.get("modell", ""), dienst="anthropic")
        summe += betrag
    return {"gebucht": len(saetze), "eur": round(summe, 6), "abgelehnt": abgelehnt}


def _main(argumente: list[str]) -> int:
    if not hub.eingerichtet():
        print("Kein Hub eingerichtet - UNIVERSE_HUB_URL fehlt.")
        return 1
    try:
        saetze = holen()
    except Exception as fehler:
        print("Hub nicht erreichbar:", fehler)
        return 1

    if argumente and argumente[0] == "stand":
        summe = sum(float(s.get("betrag_eur", 0)) for s in saetze)
        print("%d Buchungen, %.5f EUR - NICHT gebucht (nur nachgesehen)."
              % (len(saetze), summe))
        print("Achtung: das Abholen hat sie im Hub geloescht.")
        return 0

    if not saetze:
        print("Nichts abzuholen.")
        return 0
    z = buchen(saetze)
    print("%d Fragen gebucht, %.5f EUR, davon %d mit verworfener Antwort."
          % (z["gebucht"], z["eur"], z["abgelehnt"]))
    print("Kostenstelle fragefenster - nachsehen mit: "
          "python universe\\kern\\verbrauch.py stand")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
