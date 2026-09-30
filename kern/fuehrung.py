# -*- coding: utf-8 -*-
"""Mias Fuehrung - eine Datei, zwei Leser.

Was Mia beim ersten Start sagt, steht in ``universe/fuehrung.json``. Diese
Datei liest sie, prueft sie gegen die anderen Quellen und beantwortet die
zwei Fragen, die App und Webseite stellen:

    import fuehrung
    fuehrung.halte("free")          welche Halte diese Stufe sieht
    fuehrung.abschnitt("agb")       ein einzelner Abschnitt
    fuehrung.pruefen()              was nicht stimmt, als Liste von Saetzen

Warum eine eigene Datei und keine dritte Kopie: die App bekommt
``fuehrung.json`` als Beilage ins Paket gelegt
(``app/.../assets/fuehrung.json``), die Webseite liest sie beim Bauen. Eine
Pruefung haelt fest, dass die Beilage byteweise dieselbe Datei ist. So steht
kein Satz zweimal und keiner kann wegdriften.

Angebunden ist sie an drei Stellen, und keine davon wird hier nachgebaut:

    webseite/src/daten/bereiche.ts   welche Felder es gibt und ab welcher
                                     Stufe jedes offen ist
    webseite/src/daten/abo.ts        die Reihenfolge der Stufen
    universe/funktionen.json         welche Strassen es gibt

Aufruf:
    python universe/kern/fuehrung.py            die Fuehrung nachlesen
    python universe/kern/fuehrung.py pruefen    nur pruefen
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
DATEI = UNIVERSE / "fuehrung.json"
BEILAGE = (UNIVERSE / "app" / "repocity" / "app" / "src" / "main" / "assets" /
           "fuehrung.json")
BEREICHE_TS = UNIVERSE / "webseite" / "src" / "daten" / "bereiche.ts"
ABO_TS = UNIVERSE / "webseite" / "src" / "daten" / "abo.ts"
FUNKTIONEN = UNIVERSE / "funktionen.json"

_zwischenspeicher: dict = {}


def alles() -> dict:
    """Die Fuehrung, wie sie in der Datei steht."""
    if "fuehrung" not in _zwischenspeicher:
        _zwischenspeicher["fuehrung"] = json.loads(
            DATEI.read_text(encoding="utf-8"))
    return _zwischenspeicher["fuehrung"]


def neu_lesen() -> None:
    """Den Zwischenspeicher wegwerfen. Nur Pruefungen brauchen das."""
    _zwischenspeicher.clear()


# ------------------------------------------------------------- die Quellen
# Gelesen, nicht nachgebaut: beide Dateien sind TypeScript und bleiben die
# Quelle. Hier wird nur herausgezogen, was gebraucht wird.

def stufen_rang() -> dict:
    """Die Reihenfolge der Abo-Stufen, aus abo.ts."""
    text = ABO_TS.read_text(encoding="utf-8")
    paare = re.findall(r'schluessel:\s*"([a-z]+)",.*?rang:\s*(\d+)',
                       text, re.S)
    return {s: int(r) for s, r in paare}


def bereiche() -> dict:
    """Welches Feld ab welcher Stufe offen ist, aus bereiche.ts."""
    text = BEREICHE_TS.read_text(encoding="utf-8")
    # Ein Eintrag geht von 'route:' bis zum naechsten 'stufe:' - dazwischen
    # stehen Titel und ein Kommentar mit der Begruendung.
    paare = re.findall(r'route:\s*"([a-z]+)".*?stufe:\s*"([a-z]+)"',
                       text, re.S)
    return dict(paare)


def strassen() -> set:
    """Die Kennungen aller Strassen, aus funktionen.json."""
    d = json.loads(FUNKTIONEN.read_text(encoding="utf-8"))
    return set(d.get("funktionen", {}))


# ------------------------------------------------------------ was gefragt wird

def halte(stufe: str = "free") -> list:
    """Die Halte, die diese Stufe sehen darf - in ihrer Reihenfolge.

    Ein Halt zu einem gesperrten Feld wird nicht gezeigt. Er waere eine
    Fuehrung durch eine Tuer, die zu ist.
    """
    raenge = stufen_rang()
    meiner = raenge.get(stufe, 0)
    return [h for h in alles()["halte"]
            if raenge.get(h["stufe"], 0) <= meiner]


def abschnitt(kennung: str) -> dict | None:
    for a in alles().get("abschnitte", []):
        if a["kennung"] == kennung:
            return a
    return None


def upgradesatz(funktion: str, stufe: str) -> str:
    """Der eine Satz, den Mia zu einer gesperrten Funktion sagt."""
    v = alles()["upgrade"]
    return v["text"].replace("{funktion}", funktion).replace("{stufe}", stufe)


# ----------------------------------------------------------------- pruefen

def pruefen() -> list:
    """Was nicht stimmt, als Liste von Saetzen. Leer heisst: alles gut."""
    f = alles()
    fehler = []

    aus_ts = bereiche()
    raenge = stufen_rang()
    alle_strassen = strassen()

    gesehen = []
    for h in f["halte"]:
        r = h["route"]
        gesehen.append(r)
        if r not in aus_ts:
            fehler.append(
                "Halt %d fuehrt zu '%s' - das Feld gibt es in bereiche.ts nicht"
                % (h["nr"], r))
            continue
        if h["stufe"] != aus_ts[r]:
            fehler.append(
                "Halt '%s' nennt Stufe '%s', bereiche.ts sagt '%s'"
                % (r, h["stufe"], aus_ts[r]))
        if h["stufe"] not in raenge:
            fehler.append("Halt '%s' nennt die Stufe '%s', die es in abo.ts "
                          "nicht gibt" % (r, h["stufe"]))
        for s in h.get("strassen", []):
            if s not in alle_strassen:
                fehler.append("Halt '%s' nennt die Strasse '%s' - die steht "
                              "nicht in funktionen.json" % (r, s))
        for feld in ("titel", "kurz", "warum", "mehr"):
            if not str(h.get(feld, "")).strip():
                fehler.append("Halt '%s' hat kein '%s'" % (r, feld))

    fehlt = sorted(set(aus_ts) - set(gesehen))
    doppelt = sorted(r for r in set(gesehen) if gesehen.count(r) > 1)
    if fehlt:
        fehler.append("ohne Halt, also unerklaert: %s" % ", ".join(fehlt))
    if doppelt:
        fehler.append("zweimal in der Fuehrung: %s" % ", ".join(doppelt))

    nummern = [h["nr"] for h in f["halte"]]
    if nummern != sorted(nummern):
        fehler.append("die Halte stehen nicht in ihrer Reihenfolge: %s"
                      % nummern)

    v = f.get("upgrade", {})
    for platzhalter in ("{funktion}", "{stufe}"):
        if platzhalter not in v.get("text", ""):
            fehler.append("der Upgrade-Satz nennt %s nicht - dann steht dort "
                          "eine Stufe ohne Funktion oder umgekehrt"
                          % platzhalter)
    return fehler


def beilage_stimmt() -> tuple:
    """Ist die Beilage im App-Paket byteweise dieselbe Datei?"""
    if not BEILAGE.exists():
        return False, "die Beilage %s gibt es nicht" % BEILAGE.name
    hier = DATEI.read_bytes()
    dort = BEILAGE.read_bytes()
    if hier != dort:
        wie = ("%d gegen %d Bytes" % (len(dort), len(hier))
               if len(hier) != len(dort)
               else "gleich lang, aber anderer Inhalt")
        return False, ("die Beilage im App-Paket ist eine andere Fassung "
                       "(%s) - kopieren, nicht nachtippen" % wie)
    return True, "%d Bytes, byteweise dieselbe Datei" % len(hier)


if __name__ == "__main__":
    import sys as _sys

    schlecht = pruefen()
    gut, satz = beilage_stimmt()
    if len(_sys.argv) > 1 and _sys.argv[1] == "pruefen":
        for s in schlecht:
            print("  fehlt:", s)
        print("  Beilage:", satz)
        raise SystemExit(0 if (not schlecht and gut) else 1)

    for h in halte("madness"):
        print("%2d. %-14s [%s] %s" % (h["nr"], h["route"], h["stufe"],
                                      h["titel"]))
        print("    %s" % h["kurz"])
    print()
    print("Free sieht %d von %d Halten." % (len(halte("free")),
                                            len(alles()["halte"])))
    print("Beilage:", satz)
    if schlecht:
        print("NICHT IN ORDNUNG:")
        for s in schlecht:
            print("  -", s)
