"""Das Curriculum — der Teil, der vor allem anderen kommt.

Aus dem Vorbild uebernommen und zwar als harte Regel: **erst das Curriculum,
dann die Abnahme, dann die Erzeugung.** Der Grund steht im Transkript und
gilt hier genauso: was danach kommt, kostet Zeit und Geld.

Ohne Sprachmodell greift ein Geruest. Es ist nicht klug, aber es hat die
richtige Form — damit laesst sich die ganze Leitung pruefen.
"""
from __future__ import annotations

import json

import einstellungen as e
from modelle import Aufgabe, Auftrag, Curriculum, Level

ANWEISUNG = """Du entwirfst eine interaktive Schulung.

Antworte NUR mit JSON, ohne Vorwort:

{
  "titel": "...",
  "untertitel": "...",
  "einleitung": "zwei Saetze, die abholen",
  "abschluss": "ein Satz zum Schluss",
  "level": [
    {
      "titel": "...",
      "lernziel": "ein Satz: was kann man danach",
      "lehrtext": "was auf dem Bildschirm steht, 60-120 Woerter, Absaetze durch Leerzeile",
      "sprechertext": "was der Erzaehler sagt, 50-90 Woerter, gesprochene Sprache",
      "bild_hinweis": "was die Animation zeigt, ein Satz",
      "aufgabe": {
        "art": "zuordnen | regler | wahl | reihenfolge",
        "frage": "...",
        "hinweis": "was man sagt, wenn es falsch war - ohne die Loesung zu verraten",
        "punkte": 10,
        "daten": {}
      }
    }
  ]
}

Die Aufgabenarten und ihre daten:
  zuordnen     {"begriffe": ["a","b"], "faecher": ["X","Y"], "loesung": {"a":"X","b":"Y"}}
  regler       {"von":0,"bis":100,"einheit":"%","loesung":30,"toleranz":10}
  wahl         {"antworten": ["...","..."], "loesung": 1}
  reihenfolge  {"schritte": ["erst","dann","zuletzt"], "loesung": [0,1,2]}

Regeln:
- Jedes Level braucht genau eine Aufgabe. Ohne Aufgabe kein Weiterkommen.
- Die Aufgabe prueft das, was im Level steht - nichts Neues.
- Wechsle die Aufgabenarten ab.
- Sprache: {sprache}. Ansprache: Sie.
- Kein Marketing-Ton. Keine Woerter wie revolutionaer, nahtlos, Game-Changer.
"""


def entwirf(auftrag: Auftrag) -> Curriculum:
    if auftrag.trocken or e.fehlende_schluessel():
        return _geruest(auftrag)
    try:
        return _mit_modell(auftrag)
    except Exception as fehler:
        _technik(getattr(auftrag, "id", "") or auftrag.thema, "dienst-nicht-erreichbar", str(fehler))
        return _geruest(auftrag)


def _mit_modell(auftrag: Auftrag) -> Curriculum:
    import os
    import urllib.request

    frage = (
        ANWEISUNG.format(sprache=e.SPRACHE)
        + f"\n\nThema: {auftrag.thema}\nZielgruppe: {auftrag.zielgruppe}\n"
        f"Vorwissen: {auftrag.vorwissen}\nDauer: {auftrag.minuten} Minuten\n"
        f"Level: {auftrag.level_anzahl}\nVisueller Stil: {auftrag.stil}"
    )

    stoff = _stoffblock(auftrag)
    if stoff:
        frage += "\n\n" + stoff

    if e.LLM_BASISURL:
        kopf = {"content-type": "application/json"}
        if e.LLM_SCHLUESSEL:
            kopf["authorization"] = f"Bearer {e.LLM_SCHLUESSEL}"
        satz = _post(f"{e.LLM_BASISURL}/chat/completions",
                     {"model": e.MODELL, "messages": [{"role": "user", "content": frage}]},
                     kopf)
        _buchen(satz, e.MODELL, auftrag)
        roh = satz["choices"][0]["message"]["content"]
    else:
        kopf = {"content-type": "application/json",
                "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01"}
        satz = _post("https://api.anthropic.com/v1/messages",
                     {"model": e.MODELL, "max_tokens": 8000,
                      "messages": [{"role": "user", "content": frage}]},
                     kopf)
        _buchen(satz, e.MODELL, auftrag)
        roh = satz["content"][0]["text"]

    return _aus_json(roh, auftrag)


def _buchen(satz: dict, modell: str, auftrag) -> None:
    """Die eine Zeile hinter dem Modellaufruf - Token gezaehlt, nicht geschaetzt.
    Fehlte bis zum 10.09.: der Lehrplan war der eine Modellaufruf, der im
    Verbrauchsbuch nicht stand."""
    try:
        import sys as _sys
        from pathlib import Path as _Path
        kern = str(_Path(__file__).resolve().parent.parent / "kern")
        if kern not in _sys.path:
            _sys.path.append(kern)
        import modellkosten
        modellkosten.buchen(satz, "prod.lernen", modell, "Lehrplan",
                            getattr(auftrag, "id", "") or "")
    except Exception:
        pass


def _technik(auftrag: str, klasse: str, einzelheit: str = "") -> None:
    """Ein Prozessfehler als Erfahrung - getrennt von den Urteilen ueber das
    Stueck, damit der Ausbilder sieht, wo die Maschinerie hakt. Nie eine
    Ausnahme nach aussen: ein fehlender Vermerk ist besser als ein Abbruch."""
    try:
        import sys as _sys
        from pathlib import Path as _Path
        kern = str(_Path(__file__).resolve().parent.parent / "kern")
        if kern not in _sys.path:
            _sys.path.append(kern)
        import rueckweg
        rueckweg.technik_vermerken(str(auftrag), "prod.lernen", klasse, einzelheit)
    except Exception:
        pass


# --- Stoff aus dem 2nd Brain -------------------------------------------------


def _stoffblock(auftrag) -> str:
    """Was der Kurator zum Thema herausgegeben hat - als Block fuer die Frage.

    Der Stoff steht im Auftrag; hineingelegt hat ihn der Verteiler, bevor die
    Strasse losgelaufen ist. Ohne Kern gibt es keinen Stoff - dann bleibt der
    Block leer und es wird gefragt wie bisher.
    """
    import sys as _sys
    from pathlib import Path as _Path
    kern = str(_Path(__file__).resolve().parent.parent / "kern")
    if kern not in _sys.path:
        _sys.path.append(kern)
    try:
        import stoff as _stoff
        return _stoff.als_anweisung(_stoff.aus_auftrag(auftrag))
    except Exception:
        return ""


def _post(url: str, rumpf: dict, kopf: dict) -> dict:
    import urllib.request
    daten = json.dumps(rumpf).encode("utf-8")
    anfrage = urllib.request.Request(url, data=daten, headers=kopf, method="POST")
    with urllib.request.urlopen(anfrage, timeout=180) as antwort:
        return json.loads(antwort.read().decode("utf-8"))


def _aus_json(roh: str, auftrag: Auftrag) -> Curriculum:
    anfang, ende = roh.find("{"), roh.rfind("}")
    satz = json.loads(roh[anfang:ende + 1])
    level = []
    for i, l in enumerate(satz.get("level", []), start=1):
        a = l.get("aufgabe") or {}
        level.append(Level(
            nr=i,
            titel=l.get("titel", f"Level {i}"),
            lernziel=l.get("lernziel", ""),
            lehrtext=l.get("lehrtext", ""),
            sprechertext=l.get("sprechertext", ""),
            bild_hinweis=l.get("bild_hinweis", ""),
            aufgabe=Aufgabe(
                art=a.get("art", "wahl"),
                frage=a.get("frage", ""),
                daten=a.get("daten", {}),
                hinweis=a.get("hinweis", ""),
                punkte=int(a.get("punkte", 10)),
            ) if a else None,
        ))
    c = Curriculum(
        titel=satz.get("titel", auftrag.thema),
        untertitel=satz.get("untertitel", ""),
        zielgruppe=auftrag.zielgruppe,
        vorwissen=auftrag.vorwissen,
        minuten=auftrag.minuten,
        level=level,
    )
    c.einleitung = satz.get("einleitung", "")     # type: ignore[attr-defined]
    c.abschluss = satz.get("abschluss", "")       # type: ignore[attr-defined]
    return c


def _geruest(auftrag: Auftrag) -> Curriculum:
    """Ohne Sprachmodell: die richtige Form, ein sichtbar vorlaeufiger Inhalt."""
    thema = auftrag.thema
    level = []
    arten = ["wahl", "zuordnen", "regler", "reihenfolge"]
    for i in range(1, max(1, auftrag.level_anzahl) + 1):
        art = arten[(i - 1) % len(arten)]
        daten = {
            "wahl": {"antworten": [f"{thema}: erste Annahme", f"{thema}: zweite Annahme",
                                   f"{thema}: dritte Annahme"], "loesung": 1},
            "zuordnen": {"begriffe": ["Begriff A", "Begriff B"],
                         "faecher": ["Fach eins", "Fach zwei"],
                         "loesung": {"Begriff A": "Fach eins", "Begriff B": "Fach zwei"}},
            "regler": {"von": 0, "bis": 100, "einheit": " %", "loesung": 40, "toleranz": 10},
            "reihenfolge": {"schritte": ["zuerst", "danach", "zuletzt"], "loesung": [0, 1, 2]},
        }[art]
        level.append(Level(
            nr=i,
            titel=f"Level {i}: {thema}",
            lernziel="Platzhalter — hier steht spaeter das Lernziel.",
            lehrtext=("Dies ist ein Geruest ohne Sprachmodell. Es hat die richtige Form, "
                      "aber noch keinen Inhalt.\n\nMit Schluessel schreibt hier das Modell "
                      f"den Lehrtext zu: {thema}."),
            sprechertext=f"Willkommen zu Level {i} ueber {thema}.",
            bild_hinweis=f"Animation zu {thema}, Level {i}",
            aufgabe=Aufgabe(art=art, frage="Was passt hier?", daten=daten,
                            hinweis="Sieh dir den Text oben noch einmal an."),
        ))
    c = Curriculum(titel=thema, untertitel="Schulung", zielgruppe=auftrag.zielgruppe,
                   vorwissen=auftrag.vorwissen, minuten=auftrag.minuten, level=level)
    c.einleitung = f"In dieser Schulung geht es um {thema}."     # type: ignore[attr-defined]
    c.abschluss = "Damit ist die Schulung abgeschlossen."        # type: ignore[attr-defined]
    return c


def als_text(c: Curriculum) -> str:
    """Zum Lesen und Abnehmen — nicht zum Rendern."""
    zeilen = [f"# {c.titel}", ""]
    if getattr(c, "einleitung", ""):
        zeilen += [c.einleitung, ""]
    zeilen += [f"Zielgruppe: {c.zielgruppe} · Vorwissen: {c.vorwissen} · "
               f"{c.minuten} Minuten · {len(c.level)} Level", ""]
    for l in c.level:
        zeilen += [f"## Level {l.nr}: {l.titel}", f"*Lernziel:* {l.lernziel}", "",
                   l.lehrtext, "", f"**Erzaehler:** {l.sprechertext}", ""]
        if l.aufgabe:
            zeilen += [f"**Aufgabe ({l.aufgabe.art}):** {l.aufgabe.frage}", ""]
    return "\n".join(zeilen)
