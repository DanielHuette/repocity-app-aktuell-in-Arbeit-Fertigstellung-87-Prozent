"""Aus Rohtext werden zwei Dinge: eine Wissensnotiz und Atome.

Atom = eine belegte Einzelaussage. Sie steht für sich, nennt ihren Beleg
wörtlich und ihre Quelle. Zusammenfassungen sind keine Atome.

Ohne Modellschlüssel arbeitet ein einfacher Ausschnitt-Weg: Sätze, die die
Frage berühren, werden als Atome mit Sicherheit "roh" abgelegt. Der Kurator
sieht am Feld, was noch geprüft gehört.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

# Das Modell kennt nur eine Stelle: universe/kern/modellwahl.py. Ueber den
# Pfad geladen, nicht importiert - im Universe tragen mehrere Ordner
# gleichnamige Module, ein normaler Import erwischt das falsche.
import importlib.util as _iu
_mw = _iu.spec_from_file_location(
    "kern_modellwahl", Path(__file__).resolve().parent / "modellwahl.py")
modellwahl = _iu.module_from_spec(_mw)
_mw.loader.exec_module(modellwahl)

# Der Fremdtext-Zaun: universe/kern/zaun.py, ueber den Pfad geladen und unter
# einem eigenen Namen angemeldet - im Universe tragen mehrere Ordner
# gleichnamige Module, und ein Modul mit @dataclass braucht seinen Eintrag.
import importlib.util as _iu_zaun
import sys as _sys_zaun
_zs = _iu_zaun.spec_from_file_location(
    "kern_zaun", Path(__file__).resolve().parent / "zaun.py")
zaun = _sys_zaun.modules.get("kern_zaun")
if zaun is None:
    zaun = _iu_zaun.module_from_spec(_zs)
    _sys_zaun.modules["kern_zaun"] = zaun
    _zs.loader.exec_module(zaun)

SYSTEM = """Du bereitest gefundenen Webtext für ein 2nd brain auf, das Agenten lesen.

Zwei Ausgaben in einem Zug:

1. Eine Wissensnotiz — was ein Agent später braucht, um die Sache anzuwenden:
   Mechanismus, Zusammenhänge, Werkzeuge, Code. Keine Werbesprache, keine
   Einleitungsfloskeln, kein "in diesem Artikel".

2. Atome — belegte Einzelaussagen. Regeln, an die du dich hältst:
   - Eine Aussage je Atom, in sich verständlich, ohne Rückbezug auf Nachbarsätze.
   - Der Beleg ist ein wörtliches Zitat aus dem Text, höchstens 300 Zeichen.
   - Steht es nicht im Text, wird es auch nicht zum Atom. Nichts ergänzen.
   - Meinungen und Werbung werden nicht zu Atomen.
   - sicherheit: "hoch" wenn der Text es klar behauptet, "mittel" wenn es
     abgeleitet oder eingeschränkt ist.

Antworte ausschließlich mit einem JSON-Objekt, ohne Rahmen und ohne Text davor."""

AUFTRAG = """Leitfrage: {frage}

Quelle: {titel}
Adresse: {url}

TEXT
{text}
TEXT

Antworte mit:

{{
 "brauchbar": true oder false,
 "grund": "wenn unbrauchbar: warum, ein Satz",
 "titel": "sechs bis vierzehn Woerter, hoechstens 120 Zeichen: die Sache oder das Werkzeug zuerst, Doppelpunkt, dann zwei bis drei konkrete Punkte aus dem Text. Sagt, WAS drinsteht, nicht wie die Quelle hiess. Keine doppelten Anfuehrungszeichen, keine Firmennamen als Aufhaenger, keine Werbeversprechen.",
 "tags": ["drei bis sechs Schlagworte, klein geschrieben"],
 "zusammenfassung": "sechs bis zwölf Sätze: der Mechanismus, nicht der Anlass",
 "kernkonzepte": ["was man verstanden haben muss"],
 "werkzeuge": ["genannte Werkzeuge, Bibliotheken, Schnittstellen"],
 "code": "Codeblöcke oder Befehle aus dem Text, sonst leer",
 "atome": [
   {{"aussage": "", "beleg": "wörtliches Zitat", "stichworte": [], "sicherheit": "hoch"}}
 ]
}}"""

NOTIZ = """---
title: "{titel}"
tags: [{tags}]
typ: tech-wissen
thema: {thema}
quellen:
- {url}
erfasst_am: {datum}
erfasst_von: {agent}
hinweis: "Aus öffentlich zugänglichem Webtext destilliert. Die Quelle steht oben."
---

# {titel}

## Technische Zusammenfassung
{zusammenfassung}

## Kernkonzepte & Logik
{kernkonzepte}

## Erwähnte Tools & APIs
{werkzeuge}

## Technische Implementierung & Code
{code}
"""


def verfuegbar(konfiguration: dict) -> bool:
    return bool(os.environ.get(
        konfiguration["modell"].get("schluessel_umgebung", "ANTHROPIC_API_KEY")))


def destillieren(frage: str, titel: str, url: str, text: str,
                 konfiguration: dict) -> dict:
    if verfuegbar(konfiguration):
        try:
            return _mit_modell(frage, titel, url, text, konfiguration)
        except Exception as fehler:
            print(f"  Modell nicht verwendbar ({fehler}) — Ausschnitt-Weg")
    return _ohne_modell(frage, titel, text)


def _mit_modell(frage: str, titel: str, url: str, text: str,
                konfiguration: dict) -> dict:
    import anthropic
    einstellung = konfiguration["modell"]
    kunde = anthropic.Anthropic(
        api_key=os.environ[einstellung.get("schluessel_umgebung", "ANTHROPIC_API_KEY")])
    antwort = kunde.messages.create(
        model=einstellung.get("name") or modellwahl.MODELL,
        # 4000 waren zu wenig: der Aktionaersbrief-Versuch am 13.09. brach mit
        # stop_reason "max_tokens" mitten im JSON ab, und der ganze Modellweg fiel
        # stillschweigend auf den groben Ausschnitt-Weg zurueck. Eine Notiz mit
        # zwoelf Atomen und woertlichen Belegen braucht Platz.
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": AUFTRAG.format(
            frage=frage, titel=titel, url=url,
            text=zaun.fuer_prompt(text[:24000], url or titel, absender="wissen.kurator",
                                  hoechstens_zeichen=24000))}],
    )
    _buchen(antwort, einstellung.get("name") or modellwahl.MODELL, "Destillat")
    roh = "".join(teil.text for teil in antwort.content if teil.type == "text")
    ergebnis = json_lesen(roh)
    ergebnis["weg"] = "modell"
    if antwort.stop_reason == "max_tokens":
        # Die Antwort war zu lang fuer das Fenster. json_lesen hat gerettet, was
        # vollstaendig war; das gehoert sichtbar in den Befund, nicht verschwiegen.
        ergebnis["abgeschnitten"] = True
    return ergebnis


def _ohne_modell(frage: str, titel: str, text: str) -> dict:
    stich = [wort for wort in re.findall(r"[A-Za-zÄÖÜäöüß]{4,}", frage.lower())]
    # Absätze zu Fließtext glätten, damit Sätze nicht mitten im Umbruch reißen.
    flach = re.sub(r"\s+", " ", text.replace("\n", " "))
    saetze = re.split(r"(?<=[.!?])\s+", flach)
    treffer = [
        satz.strip() for satz in saetze
        if 80 < len(satz) < 400
        and len(satz.split()) >= 10
        and satz.rstrip().endswith((".", "!", "?"))
        and any(wort in satz.lower() for wort in stich)
    ]
    return {
        "brauchbar": bool(treffer),
        "grund": "" if treffer else "keine Sätze zur Frage gefunden",
        # Ohne Modell entsteht kein Sachtitel. Statt einen zu erfinden, wird der
        # Quelltitel lesbar gemacht und als solcher gekennzeichnet - der Kurator
        # sieht am "weg: ausschnitt", dass hier noch jemand draufsehen muss.
        "titel": re.sub(r"[_]+", " ", titel).strip()[:120],
        "tags": stich[:5],
        "zusammenfassung": " ".join(treffer[:8]),
        "kernkonzepte": [],
        "werkzeuge": [],
        "code": "",
        "atome": [{"aussage": satz, "beleg": satz, "stichworte": stich[:4],
                   "sicherheit": "roh"} for satz in treffer[:12]],
        "weg": "ausschnitt",
    }


def notiz_bauen(inhalt: dict, url: str, thema: str, agent: str = "deep-researcher") -> str:
    return NOTIZ.format(
        agent=agent,
        titel=inhalt.get("titel", "ohne Titel").replace('"', "'"),
        tags=", ".join(inhalt.get("tags", [])),
        thema=thema,
        url=url,
        datum=date.today().isoformat(),
        zusammenfassung=inhalt.get("zusammenfassung", "").strip() or "-",
        kernkonzepte=_liste(inhalt.get("kernkonzepte", [])),
        werkzeuge=_liste(inhalt.get("werkzeuge", [])),
        code=(inhalt.get("code") or "").strip() or "-",
    )


def atome_bauen(inhalt: dict, url: str, quelltitel: str, thema: str,
                agent: str = "deep-researcher") -> list[dict]:
    heute = date.today().isoformat()
    gebaut = []
    for atom in inhalt.get("atome", []):
        aussage = (atom.get("aussage") or "").strip()
        if len(aussage) < 20:
            continue
        gebaut.append({
            "aussage": aussage,
            "beleg": (atom.get("beleg") or "")[:300],
            "quelle": url,
            "quelltitel": quelltitel,
            "thema": thema,
            "stichworte": atom.get("stichworte", []),
            "sicherheit": atom.get("sicherheit", "mittel"),
            "erfasst_am": heute,
            "erfasst_von": agent,
        })
    return gebaut


def _liste(werte) -> str:
    if not werte:
        return "-"
    return "\n".join(f"- {wert}" for wert in werte)


def json_lesen(roh: str) -> dict:
    roh = re.sub(r"^```(?:json)?|```$", "", roh.strip(), flags=re.MULTILINE).strip()
    anfang = roh.find("{")
    if anfang == -1:
        raise ValueError("kein JSON in der Antwort")
    ende = roh.rfind("}")
    if ende != -1:
        try:
            return json.loads(roh[anfang:ende + 1])
        except json.JSONDecodeError:
            pass
    # Abgeschnitten. Statt alles wegzuwerfen: bis zum letzten vollstaendigen
    # Stueck zuruecktreten und die offenen Klammern schliessen. So bleiben die
    # Notiz und die Atome erhalten, die es ganz durch die Leitung geschafft
    # haben - der Rest fehlt eben, und das Feld "abgeschnitten" sagt es.
    geflickt = _abgeschnittenes_json(roh[anfang:])
    if geflickt is None:
        raise ValueError("kein JSON in der Antwort")
    return geflickt


def _abgeschnittenes_json(text: str):
    """Aus einem mitten im Satz endenden JSON-Text das Vollstaendige retten.

    Laeuft einmal durch und merkt sich, wo zuletzt ein Wert sauber zu Ende war
    (eine schliessende Klammer ausserhalb einer Zeichenkette). Dort wird
    abgeschnitten, ein haengendes Komma entfernt und der Klammerstapel in
    umgekehrter Reihenfolge geschlossen.
    """
    stapel: list[str] = []
    in_kette = False
    schutz = False
    sicher = -1                       # Stelle nach dem letzten fertigen Wert
    stapel_bei_sicher: list[str] = []
    for i, zeichen in enumerate(text):
        if in_kette:
            if schutz:
                schutz = False
            elif zeichen == "\\":
                schutz = True
            elif zeichen == '"':
                in_kette = False
            continue
        if zeichen == '"':
            in_kette = True
        elif zeichen in "{[":
            stapel.append("}" if zeichen == "{" else "]")
        elif zeichen in "}]":
            if not stapel:
                break
            stapel.pop()
            if stapel:                # ein fertiges Teilstueck, nicht das Ganze
                sicher, stapel_bei_sicher = i + 1, list(stapel)
            else:                     # vollstaendig - haette oben schon geklappt
                sicher, stapel_bei_sicher = i + 1, []
    if sicher == -1:
        return None
    stueck = text[:sicher].rstrip().rstrip(",")
    stueck += "".join(reversed(stapel_bei_sicher))
    try:
        return json.loads(stueck)
    except json.JSONDecodeError:
        return None


def _buchen(antwort, modell, wofuer):
    """Modellaufruf verbuchen. Nie eine Ausnahme nach aussen - eine
    verlorene Buchung ist besser als ein abgebrochener Lauf."""
    try:
        import sys as _sys
        from pathlib import Path as _Path

        kern = str(_Path(__file__).resolve().parent / "kern")
        if kern not in _sys.path:
            _sys.path.append(kern)
        import modellkosten

        modellkosten.buchen(antwort, "wissen.kurator", modell, wofuer)
    except Exception:
        pass
