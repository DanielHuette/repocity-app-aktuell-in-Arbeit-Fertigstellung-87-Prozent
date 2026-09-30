# -*- coding: utf-8 -*-
"""Baut universe/verzeichnis.json - das Nachschlagewerk des Wegweisers.

    python universe\\kern\\verzeichnis.py            neu bauen
    python universe\\kern\\verzeichnis.py pruefen    steht es auf dem letzten Stand?

Warum es das gibt: Mia bekommt die Seitentexte NICHT mitgeschickt - das haette
bei 121.957 Zeichen Seitentext 0,0276 EUR je Frage gekostet, gegen 0,0056 EUR
heute. Stattdessen sucht der Worker die Stelle selbst und gibt den Verweis
aus. Suchen kostet nichts; nur das Vorlegen von Text kostet.

Was hier hineinkommt und was nicht:

  - die Ueberschriften der Funktionsdokumentation, samt Sprungmarke. Erzeugt
    von funktionsdoku.py aus funktionen.json - hier wird nur gelesen, was
    dort schon steht.
  - die Ueberschriften der uebrigen Seiten, soweit sie eine Marke tragen.
  - die Bereiche der Oberflaeche aus bereiche.ts, damit "wo stelle ich das
    Design um" auf den Bildschirm zeigt und nicht auf einen Text darueber.

  NICHT die Frageliste. Die steht in faq.json und wird vom Wegweiser
  zusaetzlich gelesen. Zweimal dasselbe abzulegen hiesse, dass eine der
  beiden Stellen irgendwann falsch ist und niemand weiss welche.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

UNIVERSE = Path(__file__).resolve().parent.parent
WEBSEITE = UNIVERSE / "webseite"
DOKU = WEBSEITE / "src" / "daten" / "funktionsdokumentation.html"
SEITEN = WEBSEITE / "src" / "pages"
BEREICHE = WEBSEITE / "src" / "daten" / "bereiche.ts"
ZIEL = UNIVERSE / "verzeichnis.json"
FAQ = UNIVERSE / "faq.json"
#: Die Frageliste liegt dem App-Paket als Beilage bei, weil die App auch ohne
#: Netz antworten koennen muss - genau wie Mias Fuehrung. Kopie ja, zweite
#: Fassung nein: die Pruefung mia.faq-liegt-der-app-bei vergleicht byteweise.
FAQ_BEILAGE = (UNIVERSE / "app" / "repocity" / "app" / "src" / "main" /
               "assets" / "faq.json")
#: Ebenso der Gesetzestext: Rechtstexte muessen auch ohne Netz lesbar sein.
GESETZ = UNIVERSE / "ki-verordnung.json"
GESETZ_BEILAGE = FAQ_BEILAGE.parent / "ki-verordnung.json"

#: Woerter, die in jeder zweiten Frage stehen und darum nichts unterscheiden.
#: Sie fliegen aus den Stichwortlisten - nicht aus der Frage des Nutzers, dort
#: schadet ihre Anwesenheit nichts.
STOPP = {
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem",
    "eines", "einer", "und", "oder", "aber", "wie", "was", "wo", "wer", "wann",
    "warum", "wieso", "welche", "welcher", "welches", "ist", "sind", "war",
    "waren", "wird", "werden", "wurde", "hat", "habe", "haben", "hatte", "kann",
    "kannst", "koennen", "muss", "muessen", "soll", "sollen", "darf", "duerfen",
    "ich", "du", "er", "sie", "es", "wir", "ihr", "mein", "meine", "meinen",
    "dein", "deine", "sich", "mir", "mich", "dir", "dich", "man", "auf", "in",
    "im", "an", "am", "zu", "zum", "zur", "von", "vom", "mit", "bei", "fuer",
    "ueber", "unter", "nach", "vor", "aus", "durch", "gegen", "ohne", "um",
    "nicht", "kein", "keine", "auch", "noch", "schon", "nur", "sehr", "mehr",
    "hier", "dort", "da", "dann", "wenn", "als", "so", "dass", "gibt", "geht",
    "machen", "macht", "tun", "sein", "seine", "etwas", "alles", "man", "denn",
}

_UM = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
       "Ä": "ae", "Ö": "oe", "Ü": "ue"}


def worte(text: str) -> list[str]:
    """Text zu vergleichbaren Woertern - dieselbe Rechnung wie im Wegweiser.

    Wer hier etwas aendert, aendert es auch in mia/wegweiser.js. Die Pruefung
    verzeichnis.wortzerlegung-stimmt-ueberein haelt beide zusammen: sie zerlegt
    dieselben Saetze mit beiden und vergleicht.
    """
    s = text.lower()
    for a, b in _UM.items():
        s = s.replace(a, b)
    roh = [w for w in re.split(r"[^a-z0-9]+", s) if len(w) >= 2]
    gesiebt = [w for w in roh if w not in STOPP]
    return [stamm(w) for w in (gesiebt or roh)]


#: Endungen, die abgeschnitten werden, damit "Farben" und "Farbe" dasselbe
#: Wort sind. Keine Grammatik, sondern eine Abkuerzung - beide Seiten
#: schneiden gleich falsch ab und treffen sich trotzdem. Steht wortgleich in
#: mia/wegweiser.js; die Pruefung haelt beide zusammen.
ENDUNGEN = ["ungen", "erin", "chen", "lein", "enden", "ende", "ern",
            "est", "end", "ung", "et", "en", "er", "es", "em", "st",
            "e", "n", "s"]


def stamm(wort: str) -> str:
    """So lange kuerzen, bis nichts mehr passt - nie unter vier Zeichen.

    Einmal kuerzen reicht nicht: "Preise" wuerde "preis", "Preis" wuerde
    "prei" - dieselbe Sache, zwei Ergebnisse. Bis zum Ende gekuerzt landen
    beide auf "prei".
    """
    w = wort
    for _ in range(4):
        gekuerzt = False
        for e in ENDUNGEN:
            if len(w) - len(e) >= 4 and w.endswith(e):
                w = w[:len(w) - len(e)]
                gekuerzt = True
                break
        if not gekuerzt:
            break
    return w


def _titel_saeubern(roh: str) -> str:
    s = re.sub(r"<[^>]+>", "", roh)
    return re.sub(r"\s+", " ", s).strip()


def aus_doku() -> list[dict]:
    """Kapitel und Abschnitte der Funktionsdokumentation."""
    if not DOKU.exists():
        raise SystemExit("fehlt: %s - erst funktionsdoku.py laufen lassen" % DOKU)
    text = DOKU.read_text(encoding="utf-8")
    stuecke = re.findall(r'<h([23]) id="([^"]+)">(.*?)</h\1>(.*?)(?=<h[123]|\Z)',
                         text, re.S)
    aus = []
    for stufe, kennung, titel, koerper in stuecke:
        titel = _titel_saeubern(titel)
        # Der erste Absatz sagt, worum es geht - er liefert die Stichworte.
        ersterAbsatz = ""
        m = re.search(r"<p>(.*?)</p>", koerper, re.S)
        if m:
            ersterAbsatz = _titel_saeubern(m.group(1))[:400]
        aus.append({
            "art": "kapitel" if stufe == "2" else "abschnitt",
            "titel": titel,
            "ziel": "/funktionsweise/",
            "marke": kennung,
            "app": "funktionsweise",
            "worte": sorted(set(worte(titel) + worte(ersterAbsatz))),
            "gewicht": 3 if stufe == "2" else 2,
        })
    return aus


def aus_seiten() -> list[dict]:
    """Ueberschriften der uebrigen Seiten, soweit sie eine Marke tragen."""
    aus = []
    for datei in sorted(SEITEN.glob("*.astro")):
        weg = "/" + datei.stem + "/"
        if datei.stem == "index":
            weg = "/"
        inhalt = datei.read_text(encoding="utf-8")
        for stufe, kopf, titel in re.findall(r"<h([23])([^>]*)>(.*?)</h\1>",
                                             inhalt, re.S):
            m = re.search(r'id="([^"]+)"', kopf)
            if not m:
                continue
            titel = _titel_saeubern(titel)
            titel = re.sub(r"^\d+(\.\d+)*\.?\s*", "", titel)   # "6.2 " weg
            aus.append({
                "art": "abschnitt", "titel": titel, "ziel": weg,
                "marke": m.group(1), "app": datei.stem,
                "worte": sorted(set(worte(titel))), "gewicht": 2,
            })
    return aus


def aus_bereichen() -> list[dict]:
    """Die Bildschirme der Oberflaeche - dieselbe Quelle wie die Leiste."""
    if not BEREICHE.exists():
        raise SystemExit("fehlt: %s" % BEREICHE)
    text = BEREICHE.read_text(encoding="utf-8")
    aus = []
    for route, titel, zeile in re.findall(
            r'route:\s*"([^"]+)",\s*titel:\s*"([^"]+)",[^}]*?zeile:\s*"([^"]+)"',
            text, re.S):
        aus.append({
            "art": "bildschirm", "titel": titel, "ziel": "/app/%s/" % route,
            "marke": "", "app": route,
            "worte": sorted(set(worte(titel) + worte(zeile))), "gewicht": 3,
        })
    return aus


def bauen() -> dict:
    eintraege = aus_doku() + aus_seiten() + aus_bereichen()
    # Zwei Eintraege auf dieselbe Stelle waeren zwei Antworten auf dieselbe
    # Frage - der zweite faellt weg.
    gesehen, sauber = set(), []
    for e in eintraege:
        schluessel = (e["ziel"], e["marke"])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        if e["worte"]:
            sauber.append(e)
    return {
        "_hinweis": (
            "Erzeugt von universe/kern/verzeichnis.py. Von Hand geaendert geht "
            "beim naechsten Lauf verloren.\n\n"
            "Das Nachschlagewerk des Wegweisers: wo auf Webseite und in der App "
            "etwas steht. Der Worker sucht hier, bevor er das Modell fragt - "
            "findet er etwas, kostet die Antwort nichts.\n\n"
            "Die Frageliste steht NICHT hier, sondern in faq.json. Der "
            "Wegweiser liest beide."
        ),
        "fassung": 1,
        "eintraege": sauber,
    }


#: Was dem App-Paket beiliegt: Quelle -> Beilage. Beides muss byteweise
#: gleich sein, sonst traegt die App eine andere Fassung mit sich herum.
BEILAGEN = ((FAQ, FAQ_BEILAGE), (GESETZ, GESETZ_BEILAGE))


def beilage_stimmt() -> tuple:
    """Sind die Beilagen im App-Paket byteweise dieselben Dateien?"""
    saetze = []
    for quelle, beilage in BEILAGEN:
        if not quelle.exists():
            return False, "%s gibt es nicht" % quelle
        if not beilage.exists():
            return False, "die Beilage %s gibt es nicht" % beilage.name
        hier, dort = quelle.read_bytes(), beilage.read_bytes()
        if hier != dort:
            return False, ("die Beilage %s ist eine andere Fassung (%d gegen "
                           "%d Bytes) - erst 'python universe\\kern\\"
                           "verzeichnis.py' laufen lassen"
                           % (beilage.name, len(dort), len(hier)))
        saetze.append("%s %d Bytes" % (beilage.name, len(hier)))
    return True, "byteweise gleich: " + ", ".join(saetze)


def spiegeln() -> str:
    """Die Beilagen ins App-Paket legen - byteweise, ohne Umweg ueber Text.

    Byteweise, weil Text lesen und schreiben auf Windows die Zeilenenden
    umschreibt: die Datei waere inhaltlich dieselbe und byteweise eine
    andere, und die Pruefung wuerde rot, ohne dass jemand etwas geaendert
    haette. Am 09.09.2026 an anderer Stelle genau so passiert.
    """
    saetze = []
    for quelle, beilage in BEILAGEN:
        if not quelle.exists():
            continue
        beilage.parent.mkdir(parents=True, exist_ok=True)
        beilage.write_bytes(quelle.read_bytes())
        saetze.append("%s (%d Bytes)" % (beilage.name, beilage.stat().st_size))
    return "gespiegelt: " + ", ".join(saetze)


def schreiben() -> int:
    daten = bauen()
    text = json.dumps(daten, ensure_ascii=False, indent=2) + "\n"
    with ZIEL.open("w", encoding="utf-8", newline="\n") as datei:
        datei.write(text)
    arten = {}
    for e in daten["eintraege"]:
        arten[e["art"]] = arten.get(e["art"], 0) + 1
    print("geschrieben: %s (%d Eintraege: %s)" % (
        ZIEL, len(daten["eintraege"]),
        ", ".join("%d %s" % (v, k) for k, v in sorted(arten.items()))))
    print(spiegeln())
    return 0


def pruefen() -> int:
    if not ZIEL.exists():
        print("fehlt: %s" % ZIEL)
        return 1
    soll = json.dumps(bauen(), ensure_ascii=False, indent=2) + "\n"
    if ZIEL.read_text(encoding="utf-8") != soll:
        print("veraltet: %s - erst 'python universe\\kern\\verzeichnis.py'" % ZIEL)
        return 1
    gut, satz = beilage_stimmt()
    print("aktuell: %s" % ZIEL)
    print("Beilage: %s" % satz)
    return 0 if gut else 1


def main(argumente: list[str]) -> int:
    if argumente and argumente[0] == "pruefen":
        return pruefen()
    return schreiben()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
