"""Websuche über Tavily.

Nur Tavily. Der Rückfall auf Bing über einen stillen Browser und auf Wikipedia
ist am 14.09.2026 herausgenommen worden — Daniel: *"ich will kein fallback auf
bing und wikipedia das ist beides müll"*. Ohne Tavily wird nicht gesucht, und
das wird gesagt, nicht verschwiegen: `suchen()` wirft dann `SucheGesperrt` mit
dem Grund.

DIE GRENZE — gerechnet, nicht geschätzt:
Tavily gibt beim Pay-as-you-go 1.500 Credits je Monat frei (Stand 14.09.2026,
Anzeige beim Anlegen des Kontos). Eine Suche mit `search_depth=advanced` kostet
2 Credits. 1.500 ÷ 2 = **750 Suchen je Monat**. Danach hält die Suche an, statt
weiterzulaufen und abgerechnet zu werden.

Gezählt wird über das Verbrauchsbuch (`kern/verbrauch.py`), das jede Suche schon
bisher verbucht hat. Die Credits setzen sich am Monatsersten zurück — genau so
rechnet `kontingent_stand()`.

Eine Suche ist ein Aufruf mit einer Frage, nicht das Öffnen einer Webseite: ein
Aufruf bringt alle angeforderten Treffer samt Textauszügen auf einmal.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import requests

#: Was Tavily je Monat frei hat, in Credits. Steht auch in kosten.json - dort
#: für den Kostenbericht, hier für die Bremse.
CREDITS_JE_MONAT = 1500
#: Was eine Suche kostet. advanced = 2, basic = 1 (Angabe des Anbieters).
CREDITS_JE_SUCHE = 2
#: 1500 / 2 = 750.
SUCHEN_JE_MONAT = CREDITS_JE_MONAT // CREDITS_JE_SUCHE


class SucheGesperrt(Exception):
    """Es wird nicht gesucht - und hier steht, warum."""


@dataclass
class Treffer:
    titel: str
    url: str
    anriss: str = ""
    quelle: str = "tavily"


def _verbrauch():
    """Das Verbrauchsbuch. Fehlt es, gibt es keine Bremse - und dann wird
    nicht gesucht, statt ungezählt Geld auszugeben."""
    kern = str(Path(__file__).resolve().parent.parent / "kern")
    if kern not in sys.path:
        sys.path.append(kern)
    import verbrauch  # noqa: PLC0415
    return verbrauch


def stand() -> dict:
    """Wie viele Suchen dieser Monat noch hergibt."""
    try:
        verbrauch = _verbrauch()
        gebucht = verbrauch.kontingent_stand("tavily").get("in_diesem_monat", 0)
    except Exception as fehler:  # noqa: BLE001
        raise SucheGesperrt(
            "Das Verbrauchsbuch ist nicht lesbar (%s) - ohne Zählung wird nicht "
            "gesucht." % str(fehler)[:150]) from fehler
    verbraucht = gebucht // CREDITS_JE_SUCHE
    return {
        "suchen_je_monat": SUCHEN_JE_MONAT,
        "verbraucht": verbraucht,
        "frei": max(0, SUCHEN_JE_MONAT - verbraucht),
        "credits_gebucht": gebucht,
    }


def _schalter():
    """Die Schalterstellung vom Hub. Fehlt das Modul, gilt aus."""
    kern = str(Path(__file__).resolve().parent.parent / "kern")
    if kern not in sys.path:
        sys.path.append(kern)
    import schalter  # noqa: PLC0415
    return schalter.tiefenrecherche()


def suchen(frage: str, anzahl: int, sperrliste: list[str]) -> list[Treffer]:
    """Eine Suche über Tavily. Wirft SucheGesperrt, wenn nicht gesucht wird.

    Drei Tore, in dieser Reihenfolge: der Schalter des Nutzers, der Schlüssel,
    das Kontingent. Der Schalter zuerst, damit ein ausgeschalteter Nutzer gar
    nicht erst erfährt, ob ein Schlüssel da ist."""
    try:
        steht = _schalter()
    except Exception as fehler:  # noqa: BLE001
        raise SucheGesperrt(
            "Die Schalterstellung ist nicht zu lesen (%s) - ohne sie wird nicht "
            "gesucht." % str(fehler)[:150]) from fehler

    if not steht.get("an"):
        raise SucheGesperrt(
            "Die Tiefenrecherche steht aus%s. Einzuschalten in der App oder auf "
            "der Webseite unter Einstellungen."
            % (" (%s)" % steht["grund"] if steht.get("grund") else ""))

    if not os.environ.get("TAVILY_API_KEY"):
        raise SucheGesperrt(
            "Es fehlt TAVILY_API_KEY. Ohne Schlüssel wird nicht gesucht - einen "
            "Rückfall auf eine andere Suchmaschine gibt es nicht mehr.")

    offen = stand()
    if offen["frei"] <= 0 and not steht.get("ueberKontingent"):
        raise SucheGesperrt(
            "Die %d freien Suchen dieses Monats sind aufgebraucht (%d Credits "
            "gebucht). Am Monatsersten geht es von selbst weiter - oder du "
            "erlaubst das kostenpflichtige Weitersuchen in den Einstellungen."
            % (SUCHEN_JE_MONAT, offen["credits_gebucht"]))

    gefunden = _tavily(frage, anzahl)
    return filtern(gefunden, sperrliste, anzahl)


def filtern(treffer: list[Treffer], sperrliste: list[str], anzahl: int) -> list[Treffer]:
    """Nur echte Adressen, nichts von der Sperrliste, jede Seite einmal."""
    gesehen: set[str] = set()
    sauber: list[Treffer] = []
    for eintrag in treffer:
        if not eintrag.url.startswith("http"):
            continue
        if any(sperre in eintrag.url for sperre in sperrliste):
            continue
        schluessel = re.sub(r"[#?].*$", "", eintrag.url).rstrip("/")
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        sauber.append(eintrag)
    return sauber[:anzahl + 2]


def _tavily(frage: str, anzahl: int) -> list[Treffer]:
    schluessel = os.environ["TAVILY_API_KEY"]
    try:
        antwort = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": schluessel, "query": frage, "max_results": anzahl,
                  "search_depth": "advanced"},
            timeout=30)
        antwort.raise_for_status()
    except Exception as fehler:  # noqa: BLE001 - der Grund gehoert genannt
        raise SucheGesperrt("Tavily antwortet nicht: %s" % str(fehler)[:200]) from fehler

    # Erst buchen, dann herausgeben: eine Suche, die gezaehlt wird, ist bezahlt,
    # auch wenn danach etwas schiefgeht. Andersherum liefe die Bremse hinterher.
    try:
        verbrauch = _verbrauch()
        verbrauch.kontingent("tavily", "wissen.research", CREDITS_JE_SUCHE,
                             wofuer="Websuche (advanced)")
    except Exception as fehler:  # noqa: BLE001
        raise SucheGesperrt(
            "Die Suche lief, liess sich aber nicht verbuchen (%s) - damit steht "
            "die Bremse still, also wird angehalten." % str(fehler)[:150]) from fehler

    return [Treffer(t.get("title", ""), t.get("url", ""),
                    t.get("content", "")[:400], "tavily")
            for t in antwort.json().get("results", [])]
