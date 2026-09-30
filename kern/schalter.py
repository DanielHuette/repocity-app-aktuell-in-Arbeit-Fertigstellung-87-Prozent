# -*- coding: utf-8 -*-
"""Die Schalterstellung eines Nutzers — vom Hub geholt, nicht geraten.

Die Schalter stehen in der App und auf der Webseite. Gespeichert werden sie am
Hub, im Konto des Nutzers. Der Rechner fragt hier nach, bevor er etwas tut, das
Geld kostet.

DIE VORSICHTSREGEL: Kommt keine Antwort — Hub nicht erreichbar, kein Konto,
keine Angabe, kaputte Antwort —, gilt der Schalter als **aus**. Im Zweifel
nicht arbeiten ist billiger als im Zweifel abrechnen. Jede Antwort trägt
deshalb ihren Grund mit, damit ein Aus nie stumm bleibt.

Gebraucht werden drei Angaben aus der Umgebung:

    UNIVERSE_HUB_URL              wo der Hub liegt
    UNIVERSE_CONTAINER_SCHLUESSEL der Ausweis des Rechners
    UNIVERSE_NUTZER               für wen dieser Rechner arbeitet

Ansehen:
    python universe\\kern\\schalter.py stand
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent

#: Wer klopft. Cloudflare weist Anfragen ohne Absender mit einem nackten 403 ab -
#: am 09.09.2026 hat genau das den Postboten stillgelegt.
KENNUNG = "RepoCity/1.0 (+https://speedofthespirit.dev)"

#: Was ein Schalter bedeutet, wenn niemand ihn je angefasst hat. Beide aus:
#: eine Suche kostet, also wird sie eingeschaltet und nicht ausgeschaltet.
VORGABE = {"an": False, "ueberKontingent": False}


def _umgebung_laden() -> None:
    if str(UNIVERSE) not in sys.path:
        sys.path.insert(0, str(UNIVERSE))
    try:
        from kern import umgebung  # noqa: PLC0415
        umgebung.laden()
    except Exception:
        pass


def _holen(nutzer: str) -> tuple[dict, str]:
    """Die Einstellungen eines Kontos. Zurück kommt (einstellungen, grund)."""
    hub = os.environ.get("UNIVERSE_HUB_URL", "").rstrip("/")
    ausweis = os.environ.get("UNIVERSE_CONTAINER_SCHLUESSEL", "")
    if not hub:
        return {}, "UNIVERSE_HUB_URL fehlt"
    if not ausweis:
        return {}, "UNIVERSE_CONTAINER_SCHLUESSEL fehlt"
    if not nutzer:
        return {}, "UNIVERSE_NUTZER fehlt - der Rechner weiss nicht, fuer wen er arbeitet"

    adresse = (hub + "/api/konten/einstellungen?nutzer="
               + urllib.parse.quote(nutzer))
    anfrage = urllib.request.Request(
        adresse,
        headers={"User-Agent": KENNUNG, "Authorization": "Bearer " + ausweis},
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=15) as antwort:
            satz = json.loads(antwort.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as fehler:
        return {}, "Der Hub antwortet mit %d" % fehler.code
    except (urllib.error.URLError, OSError) as fehler:
        return {}, "Der Hub ist nicht erreichbar: %s" % str(fehler)[:120]
    except json.JSONDecodeError:
        return {}, "Der Hub antwortet unlesbar"
    if not isinstance(satz.get("einstellungen"), dict):
        return {}, "Der Hub nennt keine Einstellungen zu %s" % nutzer
    return satz["einstellungen"], ""


def tiefenrecherche(nutzer: str = "") -> dict:
    """Wie die beiden Schalter der Tiefenrecherche stehen.

    Immer mit `grund`: leer heisst, die Stellung kommt wirklich vom Hub.
    Steht dort etwas, ist beides aus, weil nicht nachzusehen war."""
    _umgebung_laden()
    nutzer = nutzer or os.environ.get("UNIVERSE_NUTZER", "")
    einstellungen, grund = _holen(nutzer)
    if grund:
        return {**VORGABE, "grund": grund, "nutzer": nutzer}
    satz = einstellungen.get("tiefenrecherche")
    if not isinstance(satz, dict):
        return {**VORGABE, "grund": "", "nutzer": nutzer,
                "hinweis": "noch nie eingeschaltet"}
    return {
        "an": bool(satz.get("an")),
        "ueberKontingent": bool(satz.get("ueberKontingent")),
        "grund": "",
        "nutzer": nutzer,
    }


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    if befehl == "stand":
        s = tiefenrecherche()
        print(json.dumps(s, ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
