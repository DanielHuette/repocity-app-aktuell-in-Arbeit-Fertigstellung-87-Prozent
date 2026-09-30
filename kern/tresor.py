# -*- coding: utf-8 -*-
"""Der Tresor - die Zugangsdaten der Nutzer, von hier aus gesehen.

Was ein Nutzer bei der Einrichtung eingibt - sein Postfach, seine Portale,
seine Schluessel -, liegt verschluesselt beim Hub (webseite/worker/tresor.js).
Die Agenten hier brauchen es, um in seinem Auftrag zu arbeiten: ohne sein
Postfach liest der E-Mail-Manager nichts, ohne sein Portalkonto fragt der
Wohnungsagent nichts an.

    tresor.hole("anna@beispiel.de", "postfach")   -> {"benutzer": ..., ...}
    tresor.was_liegt_da("anna@beispiel.de")       -> nur die Kennungen
    tresor.befund("anna@beispiel.de", "postfach", True)

Zwei Dinge stehen hier NICHT drin und kommen auch nie hierher:

    die Zugaenge zu den Handelsplaetzen   sie bleiben im Schluesselspeicher
                                          des Handys (dienste.json: nur_geraet)
    Zahlungsdaten                         die sieht nur der Bezahlanbieter

Und eines gilt immer: was hier geholt wird, wird benutzt und weggeworfen.
Es wird nicht in eine Datei geschrieben, nicht ins Tagebuch gelegt und
nicht an ein Modell gegeben. Ein Zugang, der in einem Prompt landet, ist
nicht mehr geheim.

Aufruf von Hand:
    python universe/kern/tresor.py stand anna@beispiel.de
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent
if str(HIER) not in sys.path:
    sys.path.insert(0, str(HIER))

import hub as hub_verbindung  # noqa: E402

GEDULD_SEK = 20


class NichtErreichbar(RuntimeError):
    """Der Tresor antwortet nicht."""


def _rufen(weg: str, nutzer: str, daten: dict | None = None,
           verfahren: str = "GET") -> dict:
    adresse, schluessel = hub_verbindung._zugang()
    if not adresse:
        raise NichtErreichbar("UNIVERSE_HUB_URL ist nicht gesetzt")
    if not schluessel:
        raise NichtErreichbar(
            "UNIVERSE_CONTAINER_SCHLUESSEL fehlt - ohne Ausweis macht der "
            "Tresor nicht auf")
    if not nutzer:
        raise NichtErreichbar(
            "Ohne Nutzer kein Fach. Der Rechner arbeitet immer fuer "
            "jemanden - wer das ist, steht im Auftrag.")

    ziel = (adresse + "/api/tresor" + weg + "?nutzer=" +
            urllib.parse.quote(nutzer))
    anfrage = urllib.request.Request(
        ziel,
        data=json.dumps(daten).encode("utf-8") if daten is not None else None,
        method=verfahren,
        headers={"Content-Type": "application/json",
                 "User-Agent": hub_verbindung.KENNUNG,
                 "Authorization": "Bearer " + schluessel})
    try:
        with urllib.request.urlopen(anfrage, timeout=GEDULD_SEK) as antwort:
            return json.loads(antwort.read().decode("utf-8"))
    except urllib.error.HTTPError as fehler:
        try:
            inhalt = json.loads(fehler.read().decode("utf-8"))
        except Exception:
            inhalt = {}
        raise NichtErreichbar("%s: %s" % (
            fehler.code, inhalt.get("fehler", fehler.reason))) from fehler
    except Exception as fehler:
        raise NichtErreichbar(str(fehler)) from fehler


def hole(nutzer: str, dienst: str) -> dict:
    """Die Zugangsdaten eines Nutzers zu einem Dienst.

    Leeres Ergebnis heisst: nichts hinterlegt oder der Tresor ist nicht da.
    Beides bedeutet dasselbe fuer den Agenten - er kann nicht arbeiten und
    sagt das, statt es zu raten.
    """
    try:
        return _rufen("/holen/" + urllib.parse.quote(dienst), nutzer).get("werte", {})
    except NichtErreichbar:
        return {}


def was_liegt_da(nutzer: str) -> list[dict]:
    """Welche Dienste eingerichtet sind - ohne die Werte."""
    try:
        return _rufen("/stand", nutzer).get("eintraege", [])
    except NichtErreichbar:
        return []


def befund(nutzer: str, dienst: str, in_ordnung: bool, fehler: str = "") -> bool:
    """Zurueckmelden, ob ein Zugang wirklich funktioniert hat.

    Nur wer es versucht hat, darf das sagen - darum meldet es der Rechner
    und nicht die App. Solange niemand es versucht hat, steht dort
    "unbekannt" und nicht "in Ordnung".
    """
    try:
        return bool(_rufen("/befund", nutzer, {
            "dienst": dienst, "inOrdnung": bool(in_ordnung),
            "fehler": fehler[:300]}, "POST").get("angenommen"))
    except NichtErreichbar:
        return False


def _main(argumente: list[str]) -> int:
    if len(argumente) >= 2 and argumente[0] == "stand":
        for e in was_liegt_da(argumente[1]):
            print("  %-16s %-12s %s" % (
                e.get("dienst", "?"), e.get("geprueft", "unbekannt"),
                e.get("geaendert", "")))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
