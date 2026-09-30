"""Der Rundgang: den Katalog abgehen, Neues mitnehmen.

Ein Feed ist der höflichste Weg an neue Beiträge — der Betreiber stellt ihn
bereit, damit er gelesen wird. Ein Abruf je Quelle statt eines Streifzugs über
die ganze Seite.

Was einmal verarbeitet wurde, steht in daten/gesehen.json und kommt nicht wieder.
So wird jeder Rundgang kleiner statt größer.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import feeds
import holen
import katalog
from einstellungen import DATEN

GESEHEN_DATEI = DATEN / "gesehen.json"


def gesehen_laden() -> set[str]:
    if not Path(GESEHEN_DATEI).exists():
        return set()
    try:
        return set(json.loads(Path(GESEHEN_DATEI).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return set()


def gesehen_sichern(gesehen: set[str]) -> None:
    Path(GESEHEN_DATEI).parent.mkdir(parents=True, exist_ok=True)
    Path(GESEHEN_DATEI).write_text(
        json.dumps(sorted(gesehen)[-20000:], ensure_ascii=False), encoding="utf-8", newline="")


def neues_sammeln(quellen: list, tage: int, je_quelle: int,
                  gesehen: set[str]) -> tuple[list, list[dict]]:
    """Gibt die neuen Beiträge und die Notizen über abgelehnte Quellen zurück."""
    gefunden: list = []
    vermerke: list[dict] = []

    for quelle in quellen:
        if quelle.art == "feed":
            antwort, grund = holen.tor().versuchen(quelle.url)
            if antwort is None:
                vermerke.append({"quelle": quelle.name, "url": quelle.url,
                                 "ausgang": grund})
                continue
            beitraege = feeds.neuer_als(feeds.lesen(antwort.text, quelle.name), tage)
        elif quelle.art == "seite":
            beitraege = [feeds.Beitrag(titel=quelle.name, url=quelle.url,
                                       datum=date.today().isoformat(),
                                       anriss="", quelle=quelle.name)]
        else:
            # Schnittstellen holt der Rundgang nicht ab - die haben eigene Wege.
            continue

        frisch = [b for b in beitraege if b.url not in gesehen][:je_quelle]
        if not frisch:
            vermerke.append({"quelle": quelle.name, "url": quelle.url,
                             "ausgang": "nichts Neues"})
        for beitrag in frisch:
            beitrag.quelle = quelle.name
            gefunden.append((beitrag, quelle))
    return gefunden, vermerke