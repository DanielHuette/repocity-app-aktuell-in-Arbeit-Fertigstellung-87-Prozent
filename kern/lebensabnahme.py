# -*- coding: utf-8 -*-
"""Die Abnahme fuer die Life Automation - eine Stelle fuer alle vier Strassen.

Bis zum 15.09.2026 ging in der Life Automation alles ungeprueft hinaus: der
Qualitaetsmanager wurde von sieben Werkstatt-Agenten gerufen, von
bewerbungs_agent, wohnungs_agent, email_manager und sekretaer aber von
keinem. Gemessen am 14.09.2026, nicht vermutet.

Was hier drankommt, ist derselbe Weg wie in der Kreativwerkstatt - gebaut wie
`musik_agent/warenausgang_musik.py`, damit es einen Weg gibt und nicht zwei:

    Agent hat den Text fertig
        -> harte Messung        Laenge, Pflichtfelder, verbliebene Platzhalter
        -> Beipackzettel        alle Pflichtfelder da
        -> Lehrsaetze           was aus frueheren Neins gelernt wurde
        -> bestanden?
             ja   -> in den Warenausgang, Meldung an den Hub, weiter wie bisher
             nein -> geht NICHT hinaus; Meldung mit den Maengeln
             dreimal -> Erfahrung auf der Halde, aus der der Ausbilder lernt

Der Lernweg haengt damit von selbst dran: `warenausgang.einstellen` meldet an
den Hub, `warenausgang.ablehnen` verlangt einen Grund und legt ihn ueber
`rueckweg.verwerfen` ab, und aus drei gleichen Urteilen wird ein Lehrsatz, den
der Qualitaetsmanager beim naechsten Mal schon anwendet.

Eine Ausnahme: der Weckruf des Terminkoordinators. Ein Ruf ist kein
Erzeugnis - er wird gemessen und gemeldet, aber nicht in den Warenausgang
gelegt. Dafuer gibt es `ruf_pruefen`.

Bricht nie ab. Klemmt der Qualitaetsmanager, laeuft die Strasse weiter, als
waere er nicht da - ein fertiges Anschreiben soll nicht daran scheitern, dass
eine Messung nicht lief. Was dann fehlt, steht im Grund.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent

#: Welche Strasse welche Modul-Kennung und welche Messart hat.
#: Die Modul-Kennungen stehen so in universe/auftragsarten.json.
STRASSEN = {
    "bewerbung": {"modul": "bewerbung", "art": "anschreiben", "was_text": "Anschreiben"},
    "wohnung": {"modul": "wohnung", "art": "wohnungsanfrage", "was_text": "Wohnungsanfrage"},
    "post": {"modul": "post", "art": "mailantwort", "was_text": "E-Mail-Antwort"},
    "termin": {"modul": "post", "art": "termin", "was_text": "Weckruf"},
}


def _laden(name: str, pfad: Path):
    """Ein Modul ueber den Pfad laden.

    Ueber den Pfad, nicht mit import: im Universe tragen mehrere Ordner
    gleichnamige Module, und ein gewoehnlicher Import erwischt das falsche.
    """
    schon = sys.modules.get(name)
    if schon is not None:
        return schon
    stelle = importlib.util.spec_from_file_location(name, pfad)
    modul = importlib.util.module_from_spec(stelle)
    sys.modules[name] = modul
    stelle.loader.exec_module(modul)
    return modul


def _qm():
    """Der Qualitaetsmanager. Er braucht seinen eigenen Ordner im Pfad,
    weil er pruefliste neben sich liegen hat."""
    ordner = UNIVERSE / "qualitaetsmanager"
    if str(ordner) not in sys.path:
        sys.path.insert(0, str(ordner))
    if str(UNIVERSE / "kern") not in sys.path:
        sys.path.insert(0, str(UNIVERSE / "kern"))
    return _laden("qm_main", ordner / "main.py")


def abnehmen(strasse: str, text: str, auftrag: str, titel: str,
             zettel: dict | None = None, kosten: float = 0.0,
             durchlaeufe: int = 1, trocken: bool = False) -> dict:
    """Abnehmen, bevor etwas hinausgeht.

    Zurueck kommt immer ein Wörterbuch mit:
        darf_hinaus   True/False - danach richtet sich die Strasse
        urteil        vorlegen / zurueck / liegen_lassen / uebersprungen
        maengel       Liste in Alltagssprache, leer wenn nichts fehlt
        warenausgang  die Kennung, unter der es liegt (leer, wenn nicht)
        grund         warum die Abnahme uebersprungen wurde (sonst leer)

    Klemmt der Qualitaetsmanager, ist darf_hinaus True und der Grund gesetzt.
    Ein Anschreiben soll nicht daran scheitern, dass eine Messung nicht lief.
    """
    angaben = STRASSEN.get(strasse)
    if angaben is None:
        return {"darf_hinaus": True, "urteil": "uebersprungen", "maengel": [],
                "warenausgang": "", "grund": "unbekannte Strasse: %s" % strasse}
    try:
        qm = _qm()
        rueckweg = _laden("rueckweg", UNIVERSE / "kern" / "rueckweg.py")
    except Exception as fehler:                            # noqa: BLE001
        return {"darf_hinaus": True, "urteil": "uebersprungen", "maengel": [],
                "warenausgang": "", "grund": "Qualitaetsmanager nicht erreichbar: %s"
                                             % str(fehler)[:140]}

    voll = dict(zettel or {})
    voll.setdefault("was", angaben["art"])
    voll.setdefault("titel", titel)
    voll.setdefault("gueteklasse", "einfach")
    voll.setdefault("taugt_fuer", angaben["was_text"])

    try:
        ergebnis = qm.abnehmen(
            was=angaben["art"], datei=text, auftrag=auftrag,
            modul=angaben["modul"], titel=titel, durchlaeufe=durchlaeufe,
            zettel=voll, kosten=kosten,
            art=rueckweg.TROCKEN if trocken else rueckweg.ECHT)
    except Exception as fehler:                            # noqa: BLE001
        return {"darf_hinaus": True, "urteil": "uebersprungen", "maengel": [],
                "warenausgang": "", "grund": "Abnahme nicht gelaufen: %s"
                                             % str(fehler)[:140]}

    befund = ergebnis.get("befund")
    maengel = list(getattr(befund, "maengel", []) or [])
    urteil = ergebnis.get("urteil", "")
    return {"darf_hinaus": urteil == qm.Urteil.VORLEGEN,
            "urteil": urteil,
            "maengel": maengel,
            "warenausgang": ergebnis.get("warenausgang", ""),
            "grund": ""}


def ruf_pruefen(titel: str, text: str, termin: dict) -> dict:
    """Den Weckruf messen, bevor er hinausgeht - ohne Warenausgang.

    Ein Ruf ist kein Erzeugnis: er wird nicht freigegeben, nicht abgeholt und
    nicht veroeffentlicht. Gemessen wird er trotzdem, denn ein Ruf ohne Titel
    oder ohne Zeit weckt jemanden um sieben Uhr frueh fuer nichts.
    """
    try:
        qm = _qm()
    except Exception as fehler:                            # noqa: BLE001
        return {"darf_hinaus": True, "maengel": [],
                "grund": "Qualitaetsmanager nicht erreichbar: %s" % str(fehler)[:140]}
    zettel = {"was": "termin", "titel": titel, "auftrag": str(termin.get("id", "")),
              "modul": STRASSEN["termin"]["modul"], "abgenommen_von": "qualitaetsmanager",
              "beginn": str(termin.get("beginn", "")), "text": text}
    try:
        befund = qm.pruefen("termin", zettel, STRASSEN["termin"]["modul"], zettel)
    except Exception as fehler:                            # noqa: BLE001
        return {"darf_hinaus": True, "maengel": [],
                "grund": "Messung nicht gelaufen: %s" % str(fehler)[:140]}
    return {"darf_hinaus": befund.bestanden, "maengel": list(befund.maengel),
            "grund": ""}


def satz(ergebnis: dict) -> str:
    """Ein Satz fuer die Meldung - in Alltagssprache, ohne Fachwoerter."""
    if ergebnis.get("grund"):
        return "ohne Abnahme (%s)" % ergebnis["grund"]
    if ergebnis.get("darf_hinaus"):
        k = ergebnis.get("warenausgang")
        return "abgenommen" + (" (%s)" % k if k else "")
    return "nicht abgenommen: " + "; ".join(ergebnis.get("maengel") or ["kein Grund genannt"])
