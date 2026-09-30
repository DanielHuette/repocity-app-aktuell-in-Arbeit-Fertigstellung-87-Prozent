# -*- coding: utf-8 -*-
"""Muster, Vorlagen, Entwuerfe und Termine - die Seite des Rechners.

Der Nutzer traegt in der App und auf der Webseite ein, wonach gearbeitet
werden soll. Hier wird es geholt. Umgekehrt legt der Rechner hier ab, was er
gebaut hat - und es wartet, bis der Nutzer es freigibt.

    muster(art)                wie er schreibt: bewerbung, wohnung,
                               email-formell, email-normal, email-casual,
                               kalender
    vorlagen(wofuer)           was er hinterlegt hat (Koepfe, ohne Inhalt)
    vorlage_holen(kennung)     eine davon, als Bytes
    entwurf_ablegen(...)       was der Agent gebaut hat - wartet auf sein Ja
    freigegebene(wofuer)       was er freigegeben hat: das darf hinaus
    termine(von, bis)          der Kalender
    termin_ablegen(...)        einen Termin eintragen

DIE VORSICHTSREGEL, wie beim Schalter: kommt keine Antwort, gibt es kein
Muster - und dann wird nicht geraten, sondern vorgelegt. Jede Funktion sagt
mit, warum sie leer ist.

Gebraucht werden dieselben drei Angaben wie ueberall:
    UNIVERSE_HUB_URL, UNIVERSE_CONTAINER_SCHLUESSEL, UNIVERSE_NUTZER

Ansehen:
    python universe\\kern\\muster.py stand
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent

KENNUNG = "RepoCity/1.0 (+https://speedofthespirit.dev)"

ARTEN = ("bewerbung", "wohnung", "email-formell", "email-normal",
         "email-casual", "kalender")


def _umgebung_laden() -> None:
    if str(UNIVERSE) not in sys.path:
        sys.path.insert(0, str(UNIVERSE))
    try:
        from kern import umgebung  # noqa: PLC0415
        umgebung.laden()
    except Exception:
        pass


def _zugang(nutzer: str = "") -> tuple[str, str, str]:
    _umgebung_laden()
    hub = os.environ.get("UNIVERSE_HUB_URL", "").rstrip("/")
    ausweis = os.environ.get("UNIVERSE_CONTAINER_SCHLUESSEL", "")
    wer = nutzer or os.environ.get("UNIVERSE_NUTZER", "")
    return hub, ausweis, wer


def _ruf(weg: str, nutzer: str = "", nutzlast: dict | None = None,
         zeitlimit: int = 30) -> tuple[dict, str]:
    """Zurueck kommt (antwort, grund). Grund leer heisst: hat geklappt."""
    hub, ausweis, wer = _zugang(nutzer)
    if not hub:
        return {}, "UNIVERSE_HUB_URL fehlt"
    if not ausweis:
        return {}, "UNIVERSE_CONTAINER_SCHLUESSEL fehlt"
    if not wer:
        return {}, "UNIVERSE_NUTZER fehlt - der Rechner weiss nicht, fuer wen er arbeitet"

    trenner = "&" if "?" in weg else "?"
    adresse = hub + weg + trenner + "nutzer=" + urllib.parse.quote(wer)
    kopf = {"User-Agent": KENNUNG, "Authorization": "Bearer " + ausweis}
    daten = None
    if nutzlast is not None:
        daten = json.dumps(nutzlast).encode("utf-8")
        kopf["Content-Type"] = "application/json"

    anfrage = urllib.request.Request(adresse, data=daten, headers=kopf,
                                     method="POST" if daten is not None else "GET")
    try:
        with urllib.request.urlopen(anfrage, timeout=zeitlimit) as antwort:
            return json.loads(antwort.read().decode("utf-8") or "{}"), ""
    except urllib.error.HTTPError as fehler:
        return {}, "Der Hub antwortet mit %d auf %s" % (fehler.code, weg)
    except (urllib.error.URLError, OSError) as fehler:
        return {}, "Der Hub ist nicht erreichbar: %s" % str(fehler)[:120]
    except json.JSONDecodeError:
        return {}, "Der Hub antwortet unlesbar"


# ------------------------------------------------------------------ Muster

def muster(art: str, nutzer: str = "") -> tuple[str, str]:
    """Das Muster einer Art. Zurueck: (text, grund)."""
    if art not in ARTEN:
        return "", "unbekannte Art %r - es gibt %s" % (art, ", ".join(ARTEN))
    antwort, grund = _ruf("/api/muster", nutzer)
    if grund:
        return "", grund
    satz = (antwort.get("muster") or {}).get(art) or {}
    text = satz.get("text") or ""
    if not text.strip():
        return "", "Der Nutzer hat fuer %s noch kein Muster hinterlegt" % art
    return text, ""


def alle_muster(nutzer: str = "") -> tuple[dict, str]:
    antwort, grund = _ruf("/api/muster", nutzer)
    if grund:
        return {}, grund
    roh = antwort.get("muster") or {}
    return {k: (v or {}).get("text", "") for k, v in roh.items()}, ""


def als_anweisung(art: str, nutzer: str = "") -> str:
    """Der Block fuers Modell. Leer heisst: es gibt kein Muster, also wird
    nicht so getan, als gaebe es eines."""
    text, grund = muster(art, nutzer)
    if not text:
        return ""
    return ("So schreibt der Nutzer. Halte dich daran - Aufbau, Anrede, Laenge,\n"
            "Wortwahl. Erfinde nichts dazu, was er nicht selbst schreiben wuerde.\n"
            "\n--- Sein Muster ---\n%s\n--- Ende ---\n" % text.strip())


# ---------------------------------------------------------------- Dateien

def vorlagen(wofuer: str = "", nutzer: str = "") -> tuple[list, str]:
    """Die Koepfe der Vorlagen, die der Nutzer hinterlegt hat."""
    antwort, grund = _ruf("/api/dateien?art=vorlage", nutzer)
    if grund:
        return [], grund
    aus = antwort.get("dateien") or []
    if wofuer:
        aus = [d for d in aus if d.get("wofuer") == wofuer]
    return aus, ""


def freigegebene(wofuer: str = "", nutzer: str = "") -> tuple[list, str]:
    """Entwuerfe, die der Nutzer freigegeben hat. Nur die duerfen hinaus."""
    antwort, grund = _ruf("/api/dateien?art=entwurf", nutzer)
    if grund:
        return [], grund
    aus = [d for d in (antwort.get("dateien") or [])
           if d.get("stand") == "freigegeben"]
    if wofuer:
        aus = [d for d in aus if d.get("wofuer") == wofuer]
    return aus, ""


def datei_holen(kennung: str, nutzer: str = "") -> tuple[bytes, str]:
    antwort, grund = _ruf("/api/dateien/holen/" + urllib.parse.quote(kennung), nutzer)
    if grund:
        return b"", grund
    inhalt = (antwort.get("datei") or {}).get("inhalt") or ""
    if not inhalt:
        return b"", "leer"
    try:
        return base64.b64decode(inhalt), ""
    except Exception as fehler:  # noqa: BLE001
        return b"", "nicht lesbar: %s" % fehler


def entwurf_ablegen(name: str, inhalt: bytes, wofuer: str,
                    typ: str = "application/pdf", nutzer: str = "") -> tuple[dict, str]:
    """Was der Agent gebaut hat - es wartet auf das Ja des Nutzers.

    Nichts geht hinaus, bevor er es gesehen hat. Das ist keine Hoeflichkeit,
    sondern die Regel: eine Bewerbung mit einem falschen Satz ist schlimmer
    als eine, die einen Tag spaeter kommt."""
    antwort, grund = _ruf("/api/dateien/ablegen", nutzer, {
        "art": "entwurf",
        "wofuer": wofuer,
        "name": name,
        "typ": typ,
        "stand": "wartet",
        "inhalt": base64.b64encode(inhalt).decode("ascii"),
    })
    if grund:
        return {}, grund
    return antwort.get("datei") or {}, ""


# ---------------------------------------------------------------- Termine

def termine(von: str = "", bis: str = "", nutzer: str = "") -> tuple[list, str]:
    teile = []
    if von:
        teile.append("von=" + urllib.parse.quote(von))
    if bis:
        teile.append("bis=" + urllib.parse.quote(bis))
    weg = "/api/termine" + ("?" + "&".join(teile) if teile else "")
    antwort, grund = _ruf(weg, nutzer)
    if grund:
        return [], grund
    return antwort.get("termine") or [], ""


def termin_ablegen(titel: str, beginn: str, art: str = "sonstiges",
                   ende: str = "", ort: str = "", beschreibung: str = "",
                   wecken_min: int = 60, quelle: str = "agent",
                   nutzer: str = "") -> tuple[dict, str]:
    antwort, grund = _ruf("/api/termine", nutzer, {
        "titel": titel, "beginn": beginn, "art": art, "ende": ende,
        "ort": ort, "beschreibung": beschreibung,
        "weckenMin": wecken_min, "quelle": quelle,
    })
    if grund:
        return {}, grund
    return antwort.get("termin") or {}, ""


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    if befehl == "stand":
        alle, grund = alle_muster()
        if grund:
            print("nicht bereit: %s" % grund)
            return 1
        print("Muster:")
        for art in ARTEN:
            text = alle.get(art, "")
            print("  %-16s %s" % (art, ("%d Zeichen" % len(text)) if text else "-"))
        for was in ("bewerbung", "wohnung", "email"):
            v, g = vorlagen(was)
            print("  Vorlagen %-8s %s" % (was, g or "%d" % len(v)))
        t, g = termine()
        print("  Termine          %s" % (g or "%d" % len(t)))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
