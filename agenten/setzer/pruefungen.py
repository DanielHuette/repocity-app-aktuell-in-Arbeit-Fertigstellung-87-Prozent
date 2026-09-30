# -*- coding: utf-8 -*-
"""Pruefungen des Setzers - alles trocken, alles ohne Netz und Geld."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

inhalt = laden(HIER / "inhalt.py", "setzer_inhalt")
pruefung = laden(HIER / "pruefung.py", "setzer_pruefung")
satz = laden(HIER / "satz.py", "setzer_satz")

MODUL = "prod.pdf"

TEXT = ("# Worum es geht\n\nDer Setzer macht aus einem Auftrag ein Dokument mit Titelseite "
        "und Abschnitten.\n\nEin zweiter Absatz gehoert zum selben Abschnitt.\n\n"
        "# Zweiter Teil\n\nHier steht der zweite Teil.")


@anmelden("setzer.trocken-gliedert-aus-dem-text", MODUL,
          "Trocken wird der Auftragstext zum Dokument: Ueberschriften und Absaetze", TROCKEN,
          "dass die Strasse ohne Schluessel und ohne einen Cent laeuft")
def trocken_gliedert():
    doku, weg = inhalt.gliedern("Probe", TEXT, trocken=True)
    if weg != "trocken":
        raise AssertionError("Weg war %r, nicht trocken" % weg)
    if [a.ueberschrift for a in doku.abschnitte] != ["Worum es geht", "Zweiter Teil"]:
        raise AssertionError("Ueberschriften falsch: %r" % [a.ueberschrift for a in doku.abschnitte])
    if len(doku.abschnitte[0].absaetze) != 2:
        raise AssertionError("erster Abschnitt hat %d Absaetze, nicht 2" % len(doku.abschnitte[0].absaetze))
    return "2 Abschnitte, 3 Absaetze, %d Woerter" % doku.woerter


@anmelden("setzer.setzt-eine-pdf-mit-titel-und-seiten", MODUL,
          "Aus dem Dokument wird eine PDF mit Titelseite, Inhalt und Seitenzahlen", TROCKEN,
          "dass das Ergebnis eine echte, lesbare PDF ist - gemessen an der Datei")
def setzt_eine_pdf():
    ordner = Path(tempfile.mkdtemp(prefix="setzer_"))
    try:
        doku, _ = inhalt.gliedern("Probe mit Umlaut äöü", TEXT, trocken=True)
        pdf = satz.setzen(doku, ordner / "probe.pdf", kit="stadtkrone", auftrag_id="p1")
        b = pruefung.pruefe(doku, pdf)
        if not b.bestanden:
            raise AssertionError("Abnahme durchgefallen: " + "; ".join(b.gruende))
        if b.seiten != 2:
            raise AssertionError("%d Seiten statt 2" % b.seiten)
        return "PDF mit %d Seiten, %d Bytes, Titel drin" % (b.seiten, b.bytes)
    finally:
        shutil.rmtree(ordner, ignore_errors=True)


@anmelden("setzer.abnahme-faellt-bei-leerem-dokument-durch", MODUL,
          "Ein Dokument ohne Inhalt kommt nicht durch die Abnahme", TROCKEN,
          "dass die Abnahme rot werden kann - sonst ist sie wertlos")
def abnahme_faellt_durch():
    ordner = Path(tempfile.mkdtemp(prefix="setzer_"))
    try:
        doku = inhalt.Dokument(titel="Leer", abschnitte=[inhalt.Abschnitt("", ["x"])])
        pdf = satz.setzen(doku, ordner / "leer.pdf")
        b = pruefung.pruefe(doku, pdf)
        if b.bestanden:
            raise AssertionError("ein Dokument mit einem Wort ist durchgekommen")
        return "durchgefallen wie verlangt: " + "; ".join(b.gruende)
    finally:
        shutil.rmtree(ordner, ignore_errors=True)


@anmelden("setzer.kitfarben-aus-kits-json", MODUL,
          "Die Farben kommen aus kits.json, unbekanntes Kit faellt auf das Standardkit", TROCKEN,
          "dass kein Kit eine eigene Farbtabelle im Setzer braucht")
def kitfarben():
    a = satz.farben("stadtkrone")
    b = satz.farben("gibt-es-nicht")
    if not a["akzent"].startswith("#") or len(a["akzent"]) != 7:
        raise AssertionError("Akzent ist keine Farbe: %r" % a["akzent"])
    if b != satz.farben(satz.e.KIT_STANDARD):
        raise AssertionError("unbekanntes Kit faellt nicht auf das Standardkit zurueck")
    return "stadtkrone %s, Rueckfall auf %s" % (a["akzent"], satz.e.KIT_STANDARD)
