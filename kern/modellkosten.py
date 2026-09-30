"""Modellaufrufe verbuchen - eine Zeile hinter jedem Aufruf.

Sieben Stellen im Universe fragen ein Modell: der Ausbilder, der
Bewerbungsagent (zweimal), der E-Mail-Manager, das Destillat, das
Drehbuch der Videostrasse. Keine davon buchte, und damit fehlte im
Bericht des Controllers ausgerechnet der Posten, der am schnellsten
waechst.

Der Grundsatz hier: **Token werden gezaehlt, nicht geschaetzt.** Jede
Antwort eines Modells sagt genau, wie viele Token hinein- und
herausgegangen sind. Diese Zahlen werden gebucht. Der Euro-Betrag wird
daraus mit der Preistabelle in kosten.json gerechnet - und die ist
Listenpreis, nicht Messung. Wer dort einen Preis korrigiert, bekommt
sofort richtige Betraege, ohne dass eine Buchung angefasst werden muss.

So wird es benutzt - eine Zeile, direkt hinter dem Aufruf:

    antwort = kunde.messages.create(model=MODELL, ...)
    modellkosten.buchen(antwort, "bewerbung", MODELL, "Anschreiben")

Faellt dabei etwas aus, wird geschwiegen und weitergearbeitet. Eine
verlorene Buchung ist aergerlich; ein Bewerbungsschreiben, das an einer
Buchhaltung scheitert, waere schlimmer.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import verbrauch


def preise(modell: str) -> tuple[float, float, bool]:
    """(ein, aus) in USD je Million Token, und ob das Modell bekannt ist."""
    tabelle = verbrauch.stammdaten().get("preise_je_million_token", {})
    eintrag = tabelle.get(modell)
    if eintrag is None:
        # Auch eine Fassung wie "claude-opus-5-20260801" soll passen.
        for name, werte in tabelle.items():
            if not name.startswith("_") and modell.startswith(name):
                return float(werte["ein"]), float(werte["aus"]), True
        ersatz = tabelle.get("_unbekannt", {"ein": 3.0, "aus": 15.0})
        return float(ersatz["ein"]), float(ersatz["aus"]), False
    return float(eintrag["ein"]), float(eintrag["aus"]), True


def kosten(modell: str, ein_token: int, aus_token: int) -> float:
    """Was dieser Aufruf gekostet hat, in Euro."""
    ein, aus, _ = preise(modell)
    usd = (ein_token * ein + aus_token * aus) / 1_000_000
    return verbrauch.eur(usd)


def _token(antwort) -> tuple[int, int]:
    """Liest die Tokenzahlen - egal ob Anthropic oder OpenAI antwortet."""
    nutzung = getattr(antwort, "usage", None)
    if nutzung is None and isinstance(antwort, dict):
        nutzung = antwort.get("usage")
    if nutzung is None:
        return 0, 0

    def hol(*namen):
        for name in namen:
            wert = getattr(nutzung, name, None)
            if wert is None and isinstance(nutzung, dict):
                wert = nutzung.get(name)
            if wert is not None:
                return int(wert)
        return 0

    return (hol("input_tokens", "prompt_tokens"),
            hol("output_tokens", "completion_tokens"))


def buchen(antwort, kostenstelle: str, modell: str, wofuer: str = "",
           auftrag: str = "") -> dict | None:
    """Die eine Zeile hinter jedem Modellaufruf. Nie eine Ausnahme nach aussen."""
    try:
        ein_token, aus_token = _token(antwort)
        if not ein_token and not aus_token:
            return None
        _, _, bekannt = preise(modell)
        betrag = kosten(modell, ein_token, aus_token)
        text = "%s (%d ein / %d aus)" % (wofuer or "Modellaufruf",
                                         ein_token, aus_token)
        if not bekannt:
            text += " - Preis geschaetzt, Modell steht nicht in der Tabelle"
        return verbrauch.buchen(kostenstelle, betrag, text,
                                menge=ein_token + aus_token,
                                modell=modell, auftrag=auftrag,
                                dienst="anthropic" if "claude" in modell.lower()
                                else "openai")
    except Exception:
        return None
