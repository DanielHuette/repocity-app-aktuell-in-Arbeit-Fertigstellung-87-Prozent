# -*- coding: utf-8 -*-
"""Der Weckruf - der Hub sagt der App, dass sie etwas tun soll.

Ohne ihn kann RepoCity dem Nutzer nie von sich aus etwas sagen: nicht beim
Wohnungsalarm, nicht bei einer Bewerbung, nicht bei einem Termin. Deshalb ist
das hier nicht wohnungsspezifisch, sondern der Weg fuer alles, was die App
tun soll, ohne dass jemand sie oeffnet.

Geschickt wird eine dringende Meldung (Firebase Cloud Messaging, hohe
Prioritaet). Die kommt auch durch, wenn das Handy im Schlafmodus liegt.

Gebraucht werden zwei Dinge: die Kennung des Projekts in FIREBASE_PROJEKT und
die Dienstkonto-Datei von Firebase unter secrets\\firebase-dienstkonto.json.
Die Datei verfaellt nicht. Das Zugriffstoken, das daraus entsteht, gilt rund
eine Stunde - es wird hier geholt und selbst erneuert, nie abgelegt. Einen
dauerhaften Schluessel gibt es fuer dieses Verfahren nicht mehr; der alte
Server-Key von Firebase ist am 20.06.2024 abgeschaltet worden.

Fehlt eines von beiden, wird nichts geschickt - und das wird gesagt, nicht
verschwiegen. Was nicht zugestellt werden kann, bleibt liegen und geht beim
naechsten Versuch mit.

    python weckruf.py pruefen        ist der Schluessel da?
    python weckruf.py liegend        was auf Zustellung wartet
    python weckruf.py nachholen      liegende Rufe erneut versuchen
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
LIEGEND = UNIVERSE / "zustand" / "weckrufe.jsonl"

#: Wohin ein Weckruf geht. Das v1-Verfahren von Firebase erwartet ein
#: Dienstkonto; die Kennung des Projekts steht neben dem Schluessel.
ADRESSE = "https://fcm.googleapis.com/v1/projects/%s/messages:send"

#: Dringlichkeit. „high“ heisst: auch im Schlafmodus zustellen. Genau dafuer
#: ist diese Stufe da - ein Wohnungsangebot um drei Uhr nachts ist der Fall,
#: fuer den es sie gibt.
DRINGLICHKEIT = "high"


#: Wofuer das Token gilt. Weniger geht nicht, mehr braucht es nicht.
BEREICH = "https://www.googleapis.com/auth/firebase.messaging"

#: Einmal geholte Zugangsdaten. Sie tragen das Token und wissen selbst, wann
#: es abgelaufen ist - deshalb wird hier nichts mit Uhrzeiten nachgerechnet.
_zugang = None


def _umgebung_laden() -> None:
    sys.path.insert(0, str(UNIVERSE))
    try:
        from kern import umgebung  # noqa: PLC0415
        umgebung.laden()
    except Exception:
        pass


def dienstkonto() -> Path:
    """Die Dienstkonto-Datei. Erst nach dem Laden der .env aufrufen."""
    eigen = os.environ.get("FIREBASE_DIENSTKONTO", "")
    if eigen:
        return Path(eigen)
    return UNIVERSE.parent / "secrets" / "firebase-dienstkonto.json"


def _token() -> tuple[str, str]:
    """Holt ein gueltiges Zugriffstoken. Zurueck kommt (token, grund)."""
    global _zugang
    datei = dienstkonto()
    if not datei.exists():
        return "", "Die Dienstkonto-Datei fehlt: %s" % datei
    try:
        from google.auth.transport.requests import Request  # noqa: PLC0415
        from google.oauth2 import service_account  # noqa: PLC0415
    except ImportError:
        return "", "Es fehlt die Bibliothek google-auth (python -m pip install google-auth)"
    try:
        if _zugang is None:
            _zugang = service_account.Credentials.from_service_account_file(
                str(datei), scopes=[BEREICH])
        if not _zugang.valid:
            _zugang.refresh(Request())
    except Exception as fehler:  # noqa: BLE001 - jeder Grund gehoert gemeldet
        _zugang = None
        return "", "Die Dienstkonto-Datei wird abgelehnt: %s" % str(fehler)[:200]
    return _zugang.token or "", ""


def schluessel() -> dict:
    _umgebung_laden()
    token, _ = _token()
    return {
        "projekt": os.environ.get("FIREBASE_PROJEKT", ""),
        "token": token,
    }


def kann_wecken() -> tuple[bool, str]:
    _umgebung_laden()
    projekt = os.environ.get("FIREBASE_PROJEKT", "")
    if not projekt:
        return False, ("Es fehlt FIREBASE_PROJEKT in der .env - die Kennung des "
                       "Firebase-Projekts. Bis dahin bleiben Weckrufe liegen.")
    token, grund = _token()
    if not token:
        return False, "%s. Bis dahin bleiben Weckrufe liegen." % grund
    return True, "Weckruf bereit, Projekt %s" % projekt


def _liegend_lesen() -> list[dict]:
    if not LIEGEND.exists():
        return []
    aus = []
    with LIEGEND.open(encoding="utf-8") as datei:
        for zeile in datei:
            zeile = zeile.strip()
            if zeile:
                try:
                    aus.append(json.loads(zeile))
                except json.JSONDecodeError:
                    continue
    return aus


def _liegend_schreiben(rufe: list[dict]) -> None:
    LIEGEND.parent.mkdir(parents=True, exist_ok=True)
    with LIEGEND.open("w", encoding="utf-8", newline="\n") as datei:
        for ruf in rufe:
            datei.write(json.dumps(ruf, ensure_ascii=False) + "\n")


def _hinlegen(ruf: dict) -> None:
    LIEGEND.parent.mkdir(parents=True, exist_ok=True)
    with LIEGEND.open("a", encoding="utf-8", newline="\n") as datei:
        datei.write(json.dumps(ruf, ensure_ascii=False) + "\n")


def wecken(geraet: str, art: str, titel: str, text: str,
           daten: dict | None = None) -> dict:
    """Die App wecken.

    [art] sagt der App, was sie tun soll - "wohnungsalarm" laesst sie die
    Anfrage abschicken, "hinweis" zeigt nur etwas an. [daten] traegt alles
    mit, was die App dafuer braucht: Link, fertiger Text, Kenndaten.

    Kommt der Ruf nicht durch, geht er nicht verloren: er wird hingelegt und
    beim naechsten Mal mitgenommen.
    """
    ruf = {
        "zeit": datetime.now().isoformat(timespec="seconds"),
        "geraet": geraet, "art": art, "titel": titel, "text": text,
        "daten": daten or {},
    }
    darf, grund = kann_wecken()
    if not darf:
        ruf["stand"] = "liegt"
        ruf["grund"] = grund
        _hinlegen(ruf)
        return ruf

    s = schluessel()
    # Nur Daten, keine fertige Anzeige. Der Grund ist kein Geschmack: schickt
    # man ein "notification"-Feld mit, baut Android die Meldung selbst - und
    # ruft die App gar nicht erst auf, solange sie im Hintergrund ist. Dann
    # steht zwar etwas auf dem Bildschirm, aber niemand hat es gelesen: kein
    # Wecker klingelt, kein Angebot wird beantwortet. Mit reinen Daten kommt
    # der Ruf immer im Rufdienst an, und der baut die Meldung - mit Ton, auf
    # dem Sperrbildschirm, mit den Knoepfen, die dazugehoeren.
    nachricht = {"message": {
        "token": geraet,
        "android": {"priority": DRINGLICHKEIT},
        "data": {
            "art": art, "titel": titel, "text": text,
            "gesendet": str(int(time.time() * 1000)),
            **{k: str(v) for k, v in (daten or {}).items()},
        },
    }}

    anfrage = urllib.request.Request(
        ADRESSE % s["projekt"],
        data=json.dumps(nachricht).encode("utf-8"),
        headers={"Authorization": "Bearer " + s["token"],
                 "Content-Type": "application/json",
                 "User-Agent": "RepoCity-Universe"},
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=10) as antwort:
            ruf["stand"] = "zugestellt" if antwort.status == 200 else "abgewiesen"
            ruf["antwort"] = antwort.status
    except (urllib.error.URLError, OSError) as fehler:
        ruf["stand"] = "liegt"
        ruf["grund"] = str(fehler)
        _hinlegen(ruf)
    return ruf


def geraete(nutzer: str = "") -> tuple[list, str]:
    """Wohin fuer diesen Nutzer gerufen werden darf.

    Der Hub weiss es - das Handy hat es dort hinterlegt (worker/hub.js,
    Weg /api/hub/geraete). Kommt keine Auskunft, wird nicht geraten: dann
    gibt es kein Geraet, und der Ruf bleibt liegen statt ins Leere zu gehen.
    """
    _umgebung_laden()
    wer = nutzer or os.environ.get("UNIVERSE_NUTZER", "")
    if not wer:
        return [], "Es steht nicht fest, wessen Geraete gemeint sind (UNIVERSE_NUTZER)"
    # Ueber kern/hub.py, nicht mit einer eigenen Leitung: der Weg zum Hub steht
    # an einer Stelle. Eine zweite daneben wird nicht mitgepflegt und faellt
    # erst auf, wenn nichts mehr ankommt.
    if str(UNIVERSE) not in sys.path:
        sys.path.insert(0, str(UNIVERSE))
    try:
        from kern import hub as kern_hub  # noqa: PLC0415
        satz_liste = kern_hub.geraete(wer)
    except Exception as fehler:  # noqa: BLE001 - jeder Grund gehoert genannt
        return [], "Der Hub gibt keine Geraete her: %s" % str(fehler)[:150]
    liste = [g for g in (satz_liste or []) if g.get("marke")]
    if not liste:
        return [], ("%s hat kein Geraet angemeldet - die App meldet ihre "
                    "Adresse beim Start" % wer)
    return liste, ""


def wecken_nutzer(nutzer: str, art: str, titel: str, text: str,
                  daten: dict | None = None) -> dict:
    """Alle Geraete eines Nutzers wecken.

    Alle, nicht eines: wer Handy und Tablet hat, soll den Termin auf beiden
    sehen. Was nicht durchkommt, liegt danach in weckrufe.jsonl und geht beim
    naechsten Versuch mit - auch dann, wenn gar kein Geraet bekannt ist.
    """
    liste, grund = geraete(nutzer)
    if grund:
        ruf = {
            "zeit": datetime.now().isoformat(timespec="seconds"),
            "geraet": "", "nutzer": nutzer, "art": art, "titel": titel,
            "text": text, "daten": daten or {}, "stand": "liegt", "grund": grund,
        }
        _hinlegen(ruf)
        return {"gerufen": 0, "zugestellt": 0, "grund": grund}
    zugestellt = 0
    for eintrag in liste:
        ergebnis = wecken(eintrag["marke"], art, titel, text, daten)
        if ergebnis.get("stand") == "zugestellt":
            zugestellt += 1
    return {"gerufen": len(liste), "zugestellt": zugestellt, "grund": ""}


def nachholen() -> dict:
    """Liegengebliebene Weckrufe erneut versuchen."""
    darf, grund = kann_wecken()
    if not darf:
        return {"versucht": 0, "zugestellt": 0, "grund": grund}

    liegend = _liegend_lesen()
    if not liegend:
        return {"versucht": 0, "zugestellt": 0, "grund": "nichts liegt"}

    _liegend_schreiben([])
    zugestellt = 0
    for ruf in liegend:
        # Lag er, weil kein Geraet bekannt war, wird jetzt noch einmal
        # nachgesehen - vielleicht hat die App sich inzwischen gemeldet.
        if not ruf.get("geraet") and ruf.get("nutzer"):
            ergebnis = wecken_nutzer(ruf["nutzer"], ruf["art"], ruf["titel"],
                                     ruf["text"], ruf.get("daten"))
            zugestellt += ergebnis.get("zugestellt", 0)
            continue
        if not ruf.get("geraet"):
            continue
        ergebnis = wecken(ruf["geraet"], ruf["art"], ruf["titel"], ruf["text"],
                          ruf.get("daten"))
        if ergebnis.get("stand") == "zugestellt":
            zugestellt += 1
    return {"versucht": len(liegend), "zugestellt": zugestellt, "grund": ""}


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "pruefen").lower()
    if befehl == "pruefen":
        darf, grund = kann_wecken()
        print("%s: %s" % ("bereit" if darf else "nicht bereit", grund))
        return 0 if darf else 1
    if befehl == "liegend":
        liegend = _liegend_lesen()
        if not liegend:
            print("Nichts liegt.")
            return 0
        for ruf in liegend:
            print("  %s  %-14s %s" % (ruf["zeit"][:16], ruf["art"], ruf["titel"]))
        print("\n%d Weckruf(e) warten auf den Schlüssel." % len(liegend))
        return 0
    if befehl == "geraete":
        liste, grund = geraete(argumente[1] if len(argumente) > 1 else "")
        if grund:
            print("kein Geraet: %s" % grund)
            return 1
        for g in liste:
            print("  %-10s %-18s zuletzt %s  %s..."
                  % (g.get("art", ""), g.get("name", ""),
                     str(g.get("zuletzt", ""))[:16], str(g.get("marke", ""))[:12]))
        return 0
    if befehl == "nachholen":
        print(json.dumps(nachholen(), ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
