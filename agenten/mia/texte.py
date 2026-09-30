# -*- coding: utf-8 -*-
"""Mias Texte zum Umschreiben vorlegen - und wieder einlesen.

Die Quelle bleibt universe/fuehrung.json. Diese Datei macht daraus ein
Arbeitsblatt, in dem jeder Satz mit dem Moment steht, in dem er faellt -
und liest das Arbeitsblatt danach zurueck in die Quelle. Das Blatt ist
Wegwerfware: sobald es zurueckgelesen ist, wird es geloescht, damit nicht
zwei Stellen dasselbe wissen und auseinanderlaufen.

    python universe/mia/texte.py vorlegen     Arbeitsblatt schreiben
    python universe/mia/texte.py zurueck      Arbeitsblatt einlesen, Blatt weg
    python universe/mia/texte.py zurueck -b   einlesen, Blatt behalten

Beim Bearbeiten gilt nur eines: die Zeilen, die mit <!-- ... --> anfangen,
bleiben stehen. Sie sagen, welcher Satz wohin gehoert. Alles dazwischen
darf umgeschrieben werden.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
QUELLE = UNIVERSE / "fuehrung.json"
BEILAGE = (UNIVERSE / "app" / "repocity" / "app" / "src" / "main" / "assets" /
           "fuehrung.json")
BLATT = UNIVERSE.parent / "MIA-TEXTE.md"

MARKE = re.compile(r"^<!--\s*(\S+)\s*-->\s*$")

#: In welchem Moment ein Halt vorkommt. Ohne das liest sich das Blatt wie
#: eine Wortliste, und man schreibt an der Lage vorbei.
WANN = {
    "dashboard":
        "Erster Halt. Die Oberflaeche ist gerade zum Dashboard gesprungen, "
        "die Sprechblase liegt darueber. Er sieht die Auftragsarten, den "
        "Laengenregler und das Eingabefeld hinter der Blase.",
    "life":
        "Zweiter Halt, auf Life Automation. Dahinter liegen Post, Termine, "
        "Bewerbungen und Wohnungssuche.",
    "wissen":
        "Dritter Halt, auf der Wissensdatenbank.",
    "ausbildung":
        "Nur ab Creative Mind. Wer Free hat, bekommt diesen Halt nie zu "
        "sehen.",
    "webseite":
        "Nur ab Full Madness.",
    "trading":
        "Nur ab Full Madness. Der heikelste Halt - hier liegt echtes Geld.",
    "einstellungen":
        "Auf den Einstellungen. Hier sitzt der Schalter trocken/echt, der "
        "darueber entscheidet, ob ueberhaupt etwas Geld kostet.",
    "organigramm":
        "Auf dem Organigramm. Reines Ansehen, nichts einzustellen.",
    "kosten":
        "Auf der Kostenansicht. Hier setzt er sich seine Grenze - oder eben "
        "nicht.",
    "abo":
        "Letzter Halt fuer Free, auf dem Abo-Plan. Danach kommt der "
        "Abschluss.",
}

FELDER = [
    ("titel", "Titel", "Steht fett oben in der Sprechblase. Kurz."),
    ("kurz", "Sofort zu sehen",
     "Der Satz, den er ohne weiteres Tippen liest und hoert. Zwei bis drei "
     "Saetze, nicht mehr."),
    ("einstellen", "Was du hier einstellst",
     "Liste, direkt darunter. Je Punkt eine Zeile mit - davor."),
    ("warum", "Erst auf 'Mehr dazu'",
     "Warum dieser Teil wichtig ist. Kommt nur, wenn er nachfragt."),
    ("mehr", "Auch erst auf 'Mehr dazu'",
     "Der Rest. Kommt nur, wenn er nachfragt."),
]


def _block(marke: str, ueberschrift: str, hinweis: str, wert) -> str:
    aus = ["### %s" % ueberschrift, "*%s*" % hinweis, "",
           "<!-- %s -->" % marke]
    if isinstance(wert, list):
        aus += ["- " + z for z in wert]
    else:
        aus.append(str(wert))
    aus += ["<!-- ende -->", ""]
    return "\n".join(aus)


def vorlegen() -> Path:
    d = json.loads(QUELLE.read_text(encoding="utf-8"))
    t = []
    t.append("# Was Mia sagt")
    t.append("")
    t.append("Arbeitsblatt. Schreib die Saetze um, wie du sie haben willst, "
             "und sag Bescheid - dann wandern sie zurueck nach")
    t.append("`universe\\fuehrung.json`, und dieses Blatt wird geloescht. "
             "Zwei Stellen mit denselben Saetzen laufen auseinander.")
    t.append("")
    t.append("**Beim Bearbeiten:** die Zeilen mit `<!-- ... -->` stehen "
             "lassen. Sie sagen, welcher Satz wohin gehoert.")
    t.append("Alles dazwischen ist deins.")
    t.append("")
    t.append("**Beachte:** diese Saetze werden auch **gesprochen**. Was "
             "geschrieben nur bieder wirkt, klingt vorgelesen betreten.")
    t.append("Kurze Saetze, die ein Mensch in einem Atemzug sagt.")
    t.append("")
    t.append("---")
    t.append("")

    e = d["eroeffnung"]
    t.append("## Der Anfang")
    t.append("")
    t.append("*Beim allerersten Start, nach dem Startbildschirm. Die "
             "Sprechblase geht von selbst auf, die Hauptseite liegt "
             "dahinter.*")
    t.append("*Die Kennzeichnung als KI steht einmal und leise neben ihrem "
             "Namen im Fenster (Artikel 50 EU-KI-Verordnung) - im Gruss wird sie "
             "nicht betont; Mia soll so menschlich wie moeglich klingen "
             "(Daniel, 10.09.).*")
    t.append("")
    t.append(_block("eroeffnung.gruss", "Der Gruss",
                    "Das Allererste, was sie sagt.", e["gruss"]))
    t.append(_block("eroeffnung.hinweis", "Der Nachsatz",
                    "Kleiner darunter.", e["hinweis"]))
    t.append(_block("eroeffnung.weiter", "Knopf: weiter",
                    "Zwei bis drei Woerter.", e["weiter"]))
    t.append(_block("eroeffnung.abbruch", "Knopf: wegschicken",
                    "Zwei bis drei Woerter.", e["abbruch"]))
    t.append("---")
    t.append("")

    for i, h in enumerate(d["halte"], 1):
        t.append("## Halt %d · %s" % (i, h["route"]))
        t.append("")
        t.append("*%s*" % WANN.get(h["route"], ""))
        t.append("*Ab Stufe: %s*" % h["stufe"])
        t.append("")
        for schluessel, ueberschrift, hinweis in FELDER:
            t.append(_block("%s.%s" % (h["route"], schluessel),
                            ueberschrift, hinweis, h.get(schluessel, "")))
        t.append("---")
        t.append("")

    a = d["abschluss"]
    t.append("## Der Schluss")
    t.append("")
    t.append("*Nach dem letzten Halt. Die Oberflaeche ist zurueck auf der "
             "Hauptseite.*")
    t.append("")
    t.append(_block("abschluss.text", "Was sie zum Abschied sagt", "",
                    a["text"]))
    t.append(_block("abschluss.weiter", "Knopf", "", a["weiter"]))
    t.append(_block("abschluss.nochmal", "Knopf bei Mia: noch einmal",
                    "Steht spaeter im Fragefenster.", a["nochmal"]))
    t.append("---")
    t.append("")

    u = d["upgrade"]
    t.append("## Wenn er auf etwas Gesperrtes tippt")
    t.append("")
    t.append("*Einmal je gesperrter Funktion, danach zu dieser nie wieder. "
             "`{funktion}` und `{stufe}` werden eingesetzt -*")
    t.append("*beide muessen im Satz vorkommen, sonst steht dort eine Stufe "
             "ohne Funktion oder umgekehrt.*")
    t.append("")
    t.append(_block("upgrade.text", "Was sie sagt", "", u["text"]))
    t.append(_block("upgrade.knopf", "Knopf hin zum Abo-Plan", "", u["knopf"]))
    t.append(_block("upgrade.abwinken", "Knopf: kein Interesse", "",
                    u["abwinken"]))
    t.append("---")
    t.append("")

    for ab in d["abschnitte"]:
        t.append("## Abschnitt · %s" % ab["kennung"])
        t.append("")
        t.append("*Kein Halt der Fuehrung. Diese Texte liegen bereit, haben "
                 "aber noch keinen Ort in App und Webseite - das ist der "
                 "offene Rest von P24.*")
        t.append("")
        t.append(_block("abschnitt.%s.titel" % ab["kennung"], "Titel", "",
                        ab["titel"]))
        t.append(_block("abschnitt.%s.schritte" % ab["kennung"], "Die Punkte",
                        "Je Punkt eine Zeile mit - davor.", ab["schritte"]))
        t.append("---")
        t.append("")

    BLATT.write_text("\n".join(t), encoding="utf-8", newline="")
    return BLATT


def _lesen() -> dict:
    """Aus dem Blatt zurueck: Marke -> Text oder Liste."""
    werte = {}
    marke = None
    puffer = []
    for zeile in BLATT.read_text(encoding="utf-8").splitlines():
        t = MARKE.match(zeile)
        if t:
            name = t.group(1)
            if name == "ende":
                if marke:
                    werte[marke] = _fassen(puffer)
                marke, puffer = None, []
            else:
                marke, puffer = name, []
            continue
        if marke is not None:
            puffer.append(zeile)
    return werte


def _fassen(zeilen: list):
    zeilen = [z for z in zeilen if z.strip()]
    if zeilen and all(z.lstrip().startswith("- ") for z in zeilen):
        return [z.lstrip()[2:].strip() for z in zeilen]
    return " ".join(z.strip() for z in zeilen).strip()


def zurueck(behalten: bool = False) -> list:
    if not BLATT.exists():
        raise SystemExit("Kein Arbeitsblatt da: %s" % BLATT)
    werte = _lesen()
    d = json.loads(QUELLE.read_text(encoding="utf-8"))
    halte = {h["route"]: h for h in d["halte"]}
    abschnitte = {a["kennung"]: a for a in d["abschnitte"]}
    geaendert = []

    for marke, wert in werte.items():
        teile = marke.split(".")
        alt = None
        if teile[0] == "eroeffnung":
            alt, ziel, feld = d["eroeffnung"].get(teile[1]), d["eroeffnung"], teile[1]
        elif teile[0] == "abschluss":
            alt, ziel, feld = d["abschluss"].get(teile[1]), d["abschluss"], teile[1]
        elif teile[0] == "upgrade":
            alt, ziel, feld = d["upgrade"].get(teile[1]), d["upgrade"], teile[1]
        elif teile[0] == "abschnitt":
            a = abschnitte.get(teile[1])
            if a is None:
                continue
            alt, ziel, feld = a.get(teile[2]), a, teile[2]
        elif teile[0] in halte:
            h = halte[teile[0]]
            alt, ziel, feld = h.get(teile[1]), h, teile[1]
        else:
            continue
        if alt != wert:
            ziel[feld] = wert
            geaendert.append(marke)

    if not geaendert:
        print("Nichts geaendert.")
    else:
        # Byteweise schreiben, nicht als Text: unter Windows wandelt Python
        # beim Textschreiben jedes \n in \r\n um. Dann aendert sich jede
        # Zeile der Datei, obwohl nur ein Satz anders ist - und die Pruefung
        # "Beilage byteweise dieselbe" haengt genau daran.
        QUELLE.write_bytes(
            (json.dumps(d, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        BEILAGE.write_bytes(QUELLE.read_bytes())
        for m in geaendert:
            print("  geaendert:", m)
        print("%d Stellen. Quelle und Beilage der App sind wieder gleich."
              % len(geaendert))
    if not behalten:
        BLATT.unlink(missing_ok=True)
    return geaendert


if __name__ == "__main__":
    befehl = sys.argv[1] if len(sys.argv) > 1 else "vorlegen"
    if befehl == "vorlegen":
        p = vorlegen()
        d = json.loads(QUELLE.read_text(encoding="utf-8"))
        stellen = sum(1 for _ in _lesen())
        print("%s" % p)
        print("%d Halte, %d Stellen zum Umschreiben." % (len(d["halte"]), stellen))
    elif befehl == "zurueck":
        zurueck("-b" in sys.argv)
    else:
        raise SystemExit(__doc__)
