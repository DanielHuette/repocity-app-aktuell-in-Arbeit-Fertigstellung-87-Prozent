# -*- coding: utf-8 -*-
"""Was bestellt werden kann - die Laenge je Strasse, an einer Stelle.

Bisher hat der Qualitaetsmanager gegen feste Grenzen gemessen, die fuer alle
gleich waren: mindestens 3, hoechstens 180 Sekunden. Wer 45 Sekunden bestellte
und 5 bekam, sah das nirgends - 5 ist ja ueber 3.

Hier steht stattdessen, was der Nutzer je Strasse einstellen kann. Ein Regler,
harte Grenzen, und daraus wird der Sollwert, gegen den gemessen wird. Zwei
Stellen, die dasselbe wissen, laufen auseinander - deshalb diese eine.

    import laenge
    laenge.regler("prod.video.clip")        was der Regler hergibt
    laenge.pruefen("prod.video.clip", 45)   (False, "hoechstens 30 Sekunden")
    laenge.als_soll("prod.video.clip", 20)  {"sekunden_min": 18, "sekunden_max": 22}

Die Praesentation ist der Sonderfall: dort meint "15 Minuten" nicht die Laenge
einer Datei, sondern die Zeit, die ein Mensch zum Vortragen braucht. Deshalb
rechnet sie unten in einen Wortvorrat um, nicht in Sekunden Material.
"""
from __future__ import annotations

import json
from pathlib import Path

#: Wie genau eine Strasse ihre Bestellung treffen muss.
#:
#: Gesetzt, nicht gemessen - und das steht hier, damit es niemand fuer einen
#: Messwert haelt: zehn Prozent, mindestens zwei Sekunden. Darunter kann keine
#: Produktion zuverlaessig treffen (ein Schnitt liegt selten auf der Sekunde),
#: darueber faellt dem Besteller der Unterschied auf. Sobald genug echte
#: Durchlaeufe vorliegen, wird die Zahl gemessen statt gesetzt.
TOLERANZ_ANTEIL = 0.10
TOLERANZ_MINDESTENS_SEK = 2.0

#: Woerter je Minute Vortrag.
#:
#: Nicht geraten: VirtualSpeech nennt 100-150 Woerter je Minute als angenehmes
#: Vortragstempo und zitiert das National Center for Voice and Speech mit rund
#: 150 Woertern je Minute fuer amerikanisches Alltagsenglisch; unter den
#: meistgesehenen TED-Vortraegen liegt der Schnitt bei 173.
#: Quelle: https://virtualspeech.com/blog/average-speaking-rate-words-per-minute
#: Gerechnet wird mit der Mitte des angenehmen Bereichs: (100 + 150) / 2 = 125,
#: aufgerundet auf 130, weil ein vorbereiteter Vortrag etwas zuegiger laeuft
#: als die Untergrenze. Sobald ein Vortrag wirklich gehalten und gestoppt
#: wurde, ersetzt der gemessene Wert diesen hier.
WOERTER_JE_MINUTE = 130

#: Der Regler je Strasse steht in universe/auftragsarten.json - derselben
#: Datei, aus der App und Webseite ohnehin schon die Auftragsarten lesen. Hier
#: wird sie nur gelesen. Eine zweite Liste hier waere die zweite Wahrheit.
ARTEN_DATEI = Path(__file__).resolve().parent.parent / "auftragsarten.json"

_ALT_REGLER = {
    # Von Daniel am 09.09. gesetzt: "ich möchte das ein clip zwischen 10 und
    # 30 sekunden ist."
    "prod.video.clip": {
        "von": 10, "bis": 30, "schritt": 1, "voreinstellung": 20,
        "einheit": "sekunden",
        "was": "Wie lang der Clip wird.",
    },
    # "vllt werte zwischen 1 minute und 30 minuten" - und gekoppelt an die
    # geschaetzten Kosten: laenger heisst teurer, und das soll man sehen.
    "prod.video.stueck": {
        "von": 60, "bis": 1800, "schritt": 30, "voreinstellung": 300,
        "einheit": "minuten", "kosten_sichtbar": True,
        "was": "Wie lang das Video wird. Laenger kostet mehr - der Betrag "
               "steht daneben.",
    },
    # "zwischen 3:30 kurzes musikstück bis mixes die 1 Stunde maximal gehen"
    "prod.musik": {
        "von": 210, "bis": 3600, "schritt": 30, "voreinstellung": 210,
        "einheit": "minuten",
        "was": "Wie lang das Stueck wird - von einem kurzen Stueck bis zum Mix.",
    },
    # Der Sonderfall: hier ist die Zahl die VORTRAGSDAUER, nicht die Laenge
    # einer Datei. Der Bereich ist noch nicht von Daniel bestaetigt.
    "prod.praesentation": {
        "von": 300, "bis": 3600, "schritt": 300, "voreinstellung": 900,
        "einheit": "minuten", "art": "vortragsdauer",
        "was": "Wie lange der Vortrag dauern soll. Daraus ergibt sich, wie "
               "viel Text auf die Folien darf.",
    },
}


def _stammdaten() -> dict:
    try:
        return json.loads(ARTEN_DATEI.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def alle_regler() -> dict:
    """Alle Regler, wie sie in auftragsarten.json stehen."""
    aus = _stammdaten().get("regler")
    return aus if isinstance(aus, dict) and aus else dict(_ALT_REGLER)


def regler(modul: str) -> dict | None:
    """Was der Regler dieser Strasse hergibt. None heisst: kein Regler."""
    return alle_regler().get(modul)


def voreinstellung(modul: str) -> float | None:
    r = regler(modul)
    return float(r["voreinstellung"]) if r else None


def pruefen(modul: str, sekunden: float) -> tuple[bool, str]:
    """Darf das bestellt werden? Die Grenzen sind hart.

    Von Daniel am 09.09. so entschieden: "Hart - der Regler geht nicht
    darueber hinaus." Ein Wunsch ausserhalb wird also nicht stillschweigend
    zurechtgebogen, sondern abgewiesen, mit dem Bereich im Klartext.
    """
    r = regler(modul)
    if r is None:
        return True, "fuer %s ist keine Laenge einstellbar" % modul
    try:
        wert = float(sekunden)
    except (TypeError, ValueError):
        return False, "das ist keine Laenge: %r" % (sekunden,)
    if wert < r["von"]:
        return False, "mindestens %s" % _lesbar(r["von"], r["einheit"])
    if wert > r["bis"]:
        return False, "hoechstens %s" % _lesbar(r["bis"], r["einheit"])
    return True, "%s liegt im Bereich %s bis %s" % (
        _lesbar(wert, r["einheit"]), _lesbar(r["von"], r["einheit"]),
        _lesbar(r["bis"], r["einheit"]))


def als_soll(modul: str, sekunden: float) -> dict:
    """Der Sollwert fuer den Qualitaetsmanager - die BESTELLUNG als Grenze.

    Damit misst er nicht mehr gegen eine feste Spanne fuer alle, sondern
    gegen das, was dieser eine Auftrag wollte.
    """
    r = regler(modul)
    if r is None or not sekunden:
        return {}
    wert = float(sekunden)
    if r.get("art") == "vortragsdauer":
        # Eine Praesentation ist keine Datei von 15 Minuten Laenge. Gemessen
        # wird der Wortvorrat, nicht die Spielzeit.
        return {"woerter_min": int(woerter_fuer(wert) * (1 - TOLERANZ_ANTEIL)),
                "woerter_max": int(woerter_fuer(wert) * (1 + TOLERANZ_ANTEIL))}
    luft = max(wert * TOLERANZ_ANTEIL, TOLERANZ_MINDESTENS_SEK)
    return {"sekunden_min": round(max(wert - luft, 0.0), 1),
            "sekunden_max": round(wert + luft, 1)}


def woerter_fuer(sekunden: float) -> int:
    """Wie viel Text in diese Vortragsdauer passt. Siehe WOERTER_JE_MINUTE."""
    return int(round(float(sekunden) / 60.0 * WOERTER_JE_MINUTE))


def vortragsdauer_fuer(woerter: int) -> float:
    """Die Gegenrichtung: wie lange dieser Text zu sprechen dauert, in Sekunden."""
    return round(float(woerter) / WOERTER_JE_MINUTE * 60.0, 1)


def _lesbar(sekunden: float, einheit: str) -> str:
    if einheit == "sekunden" or sekunden < 60:
        return "%d Sekunden" % round(sekunden)
    minuten = sekunden / 60.0
    if abs(minuten - round(minuten)) < 0.01:
        return "1 Minute" if round(minuten) == 1 else "%d Minuten" % round(minuten)
    return "%d:%02d Minuten" % (int(minuten), round((minuten % 1) * 60))


def alle() -> dict:
    """Alle Regler - fuer App und Webseite, damit dort nichts nachgebaut wird."""
    return {modul: dict(r, lesbar_von=_lesbar(r["von"], r["einheit"]),
                        lesbar_bis=_lesbar(r["bis"], r["einheit"]))
            for modul, r in alle_regler().items()}


# ------------------------------------------------------------ Was es kostet

#: Wie lang eine Szene im Video ist - dieselbe Zahl wie in der Videowerkstatt
#: (`video_agent/einstellungen.py: SZENE_SEKUNDEN`). Sie bestimmt, wie viele
#: Endbilder ein Video braucht, und damit den groessten Teil seines Preises.
SZENE_SEKUNDEN = 4.0

#: Womit die Endbilder erzeugt werden. Der Preis dazu steht in kosten.json -
#: gemessen, nicht geschaetzt.
ENDBILD_MODELL = "fal-ai/flux/dev"


def schaetzung(modul: str, sekunden: float) -> dict:
    """Was diese Laenge ungefaehr kostet - mit der Rechnung daneben.

    Gerechnet wird nur, was sich wirklich rechnen laesst: die Endbilder. Ein
    Video braucht je Szene eines, und eine Szene ist %.0f Sekunden lang. Der
    Modellaufruf fuer das Drehbuch kommt dazu; er waechst mit der Laenge kaum
    und steht deshalb nicht in der Zahl, sondern in der Rechnung.
    """ % SZENE_SEKUNDEN
    r = regler(modul)
    if r is None or not r.get("kosten_sichtbar"):
        return {}
    try:
        import verbrauch
    except ImportError:                              # pragma: no cover
        return {}
    szenen = max(1, int(round(float(sekunden) / SZENE_SEKUNDEN)))
    je_bild = verbrauch.preis(ENDBILD_MODELL)
    betrag = round(szenen * je_bild, 4)
    return {
        "betrag_eur": betrag,
        "rechnung": ("%d Sekunden / %.0f Sekunden je Szene = %d Szenen, "
                     "je ein Endbild zu %.4f EUR = %.2f EUR. Dazu der "
                     "Modellaufruf fuer das Drehbuch, der mit der Laenge kaum "
                     "waechst." % (sekunden, SZENE_SEKUNDEN, szenen, je_bild, betrag)),
        "szenen": szenen,
    }


if __name__ == "__main__":
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    for modul, r in alle().items():
        print("%-22s %s bis %s, Voreinstellung %s"
              % (modul, r["lesbar_von"], r["lesbar_bis"],
                 _lesbar(r["voreinstellung"], r["einheit"])))
    print()
    for probe in (60, 300, 1800):
        s = schaetzung("prod.video.stueck", probe)
        if s:
            print("%4d s Video: %.2f EUR - %s" % (probe, s["betrag_eur"], s["rechnung"]))
    print()
    print("15 Minuten Vortrag = %d Woerter" % woerter_fuer(900))
    print("1000 Woerter       = %.0f Sekunden Vortrag" % vortragsdauer_fuer(1000))
