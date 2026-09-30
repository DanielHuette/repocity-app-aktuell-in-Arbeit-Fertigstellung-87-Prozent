# -*- coding: utf-8 -*-
"""Die Kostenbremse des Nutzers.

Es gibt keine Grenze, die RepoCity dem Nutzer setzt. Was er ausgibt,
entscheidet er. Die App zeigt ihm laufend, was jede Kette kostet, und er
kann sich selbst eine Marke setzen – je Produktionsstraße und je Kette,
getrennt. Voreinstellung: keine Marke, es läuft.

Wenn er eine gesetzt hat:

    bei 80 % der Marke     eine Warnung. Es läuft weiter.
    an der Marke           kein neuer Lauf mehr. Ein angefangener läuft
                           zu Ende – ein halbes Video ist niemandem gedient.
    beim Doppelten         auch der angefangene Lauf bricht ab. Sonst wäre
                           „läuft zu Ende“ ein Blankoscheck.

Die Marken stehen in universe/kostenbremse.json. Geschrieben werden sie
von der App, nicht von Hand.

    python universe\\kern\\bremse.py stand
    python universe\\kern\\bremse.py setzen wohnungsalarm --monat 5 --lauf 0.5
    python universe\\kern\\bremse.py loesen wohnungsalarm
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

UNIVERSE = Path(__file__).resolve().parent.parent
DATEI = UNIVERSE / "kostenbremse.json"

FREI = "frei"
WARNUNG = "warnung"
STOPP = "stopp"
ABBRUCH = "abbruch"

#: Ab diesem Anteil der Marke wird gewarnt. Von Daniel am 07.09. festgelegt.
WARNSCHWELLE = 0.80

#: Beim Vielfachen der Lauf-Marke bricht auch ein laufender Auftrag ab.
ABBRUCH_FAKTOR = 2.0

LEER = {
    "_hinweis": (
        "Die Kostenbremsen des Nutzers. RepoCity setzt keine Grenzen – der Nutzer "
        "setzt sie sich selbst, je Produktionsstraße und je Kette. Steht hier nichts, "
        "gibt es keine Grenze. Geschrieben wird diese Datei von der App."
    ),
    "_stufen": {
        "80 % der Marke": "Warnung, es läuft weiter",
        "die Marke": "kein neuer Lauf mehr, angefangene laufen zu Ende",
        "das Doppelte der Lauf-Marke": "auch der angefangene Lauf bricht ab",
    },
    "version": 1,
    "bremsen": {},
}


def laden() -> dict:
    try:
        return json.loads(DATEI.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(LEER)


def speichern(daten: dict) -> None:
    DATEI.parent.mkdir(parents=True, exist_ok=True)
    with DATEI.open("w", encoding="utf-8", newline="\n") as datei:
        json.dump(daten, datei, ensure_ascii=False, indent=1)
        datei.write("\n")


def fuer(kennung: str) -> dict | None:
    """Die Marke für diese Kette oder Kostenstelle – oder None.

    Gesucht wird von genau nach allgemein: 'prod.video.clip', dann
    'prod.video', dann 'prod'. So kann der Nutzer eine Marke für alle
    Videos setzen, ohne jede einzelne Straße anzufassen.
    """
    bremsen = laden().get("bremsen", {})
    teil = kennung
    while teil:
        eintrag = bremsen.get(teil)
        if eintrag and eintrag.get("aktiv"):
            return {**eintrag, "gilt_fuer": teil}
        if "." not in teil:
            return None
        teil = teil.rsplit(".", 1)[0]
    return None


def setzen(kennung: str, monat_eur: float | None = None,
           lauf_eur: float | None = None, aktiv: bool = True,
           von: str = "nutzer") -> dict:
    """Eine Marke setzen. Ruft die App über den Hub auf."""
    daten = laden()
    daten.setdefault("bremsen", {})
    eintrag = daten["bremsen"].get(kennung, {})
    eintrag.update({
        "aktiv": aktiv,
        "gesetzt_von": von,
        "gesetzt_am": datetime.now().isoformat(timespec="seconds"),
    })
    if monat_eur is not None:
        eintrag["marke_monat_eur"] = round(float(monat_eur), 4)
    if lauf_eur is not None:
        eintrag["marke_lauf_eur"] = round(float(lauf_eur), 4)
    daten["bremsen"][kennung] = eintrag
    speichern(daten)
    return eintrag


def loesen(kennung: str) -> bool:
    """Marke abschalten. Der Wert bleibt stehen, damit er nicht neu getippt wird."""
    daten = laden()
    eintrag = daten.get("bremsen", {}).get(kennung)
    if not eintrag:
        return False
    eintrag["aktiv"] = False
    eintrag["geloest_am"] = datetime.now().isoformat(timespec="seconds")
    speichern(daten)
    return True


def marke(kennung: str, je: str = "lauf") -> float:
    """Die geltende Marke in EUR. 0.0 heißt: keine Grenze."""
    eintrag = fuer(kennung)
    if not eintrag:
        return 0.0
    schluessel = "marke_lauf_eur" if je == "lauf" else "marke_monat_eur"
    return float(eintrag.get(schluessel, 0.0) or 0.0)


def stufe(kennung: str, betrag_eur: float, schon_im_lauf: float = 0.0,
          verbraucht_im_monat: float = 0.0) -> tuple[str, str]:
    """Welche Stufe gilt für diese Handlung? Gibt (Stufe, Klartext) zurück.

    Stufen: frei | warnung | stopp | abbruch. 'warnung' heißt: es läuft
    weiter, aber der Nutzer soll es sehen.
    """
    eintrag = fuer(kennung)
    if not eintrag:
        return FREI, "keine Marke gesetzt – der Nutzer entscheidet"

    gilt = eintrag["gilt_fuer"]
    m_lauf = float(eintrag.get("marke_lauf_eur", 0.0) or 0.0)
    m_monat = float(eintrag.get("marke_monat_eur", 0.0) or 0.0)
    im_lauf = schon_im_lauf + betrag_eur
    im_monat = verbraucht_im_monat + betrag_eur

    if m_lauf and im_lauf > m_lauf * ABBRUCH_FAKTOR:
        return ABBRUCH, (
            "Dieser Lauf käme auf %.2f €. Das ist mehr als das Doppelte deiner Marke "
            "von %.2f € (%s) – hier bricht auch ein angefangener Lauf ab."
            % (im_lauf, m_lauf, gilt))

    if m_monat and im_monat > m_monat:
        if schon_im_lauf > 0:
            return WARNUNG, (
                "Du bist über deiner Monatsmarke von %.2f € (%s): %.2f €. Der "
                "angefangene Lauf wird noch fertig." % (m_monat, gilt, im_monat))
        return STOPP, (
            "Monatsmarke erreicht: %.2f € von %.2f € (%s). Hier fängt nichts Neues "
            "mehr an, bis du die Marke änderst." % (verbraucht_im_monat, m_monat, gilt))

    if m_lauf and im_lauf > m_lauf:
        if schon_im_lauf > 0:
            return WARNUNG, (
                "Dieser Lauf ist über deiner Marke von %.2f € (%s): %.2f €. "
                "Angefangen ist angefangen, er läuft zu Ende." % (m_lauf, gilt, im_lauf))
        return STOPP, (
            "Ein einzelner Schritt über deiner Lauf-Marke von %.2f € (%s) – so etwas "
            "fängt nicht an." % (m_lauf, gilt))

    if m_monat and im_monat >= m_monat * WARNSCHWELLE:
        return WARNUNG, (
            "%.0f %% deiner Monatsmarke verbraucht: %.2f € von %.2f € (%s)."
            % (im_monat / m_monat * 100, im_monat, m_monat, gilt))

    if m_lauf and im_lauf >= m_lauf * WARNSCHWELLE:
        return WARNUNG, (
            "%.0f %% deiner Lauf-Marke verbraucht: %.2f € von %.2f € (%s)."
            % (im_lauf / m_lauf * 100, im_lauf, m_lauf, gilt))

    return FREI, "im Rahmen deiner Marke"


def darf(stufe_name: str) -> bool:
    """Läuft es weiter? Nur stopp und abbruch halten an."""
    return stufe_name in (FREI, WARNUNG)


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    if befehl == "stand":
        daten = laden()
        bremsen = {k: v for k, v in daten.get("bremsen", {}).items()
                   if not k.startswith("_")}
        if not bremsen:
            print("Keine Marke gesetzt. Es gibt keine Grenze – so ist es gewollt.")
            return 0
        print("%-26s %10s %10s %8s" % ("gilt für", "je Lauf", "je Monat", "aktiv"))
        print("-" * 58)
        for kennung, e in bremsen.items():
            print("%-26s %9.2f€ %9.2f€ %8s"
                  % (kennung, e.get("marke_lauf_eur", 0.0),
                     e.get("marke_monat_eur", 0.0),
                     "ja" if e.get("aktiv") else "nein"))
        return 0
    if befehl == "setzen" and len(argumente) > 1:
        kennung = argumente[1]
        monat = lauf = None
        for i, wort in enumerate(argumente):
            if wort == "--monat" and i + 1 < len(argumente):
                monat = float(argumente[i + 1])
            if wort == "--lauf" and i + 1 < len(argumente):
                lauf = float(argumente[i + 1])
        print(json.dumps(setzen(kennung, monat, lauf), ensure_ascii=False, indent=1))
        return 0
    if befehl == "loesen" and len(argumente) > 1:
        print("gelöst" if loesen(argumente[1]) else "keine Marke unter diesem Namen")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
