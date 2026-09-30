# -*- coding: utf-8 -*-
"""Wie der Nutzer schreibt - in drei Tonlagen.

Er traegt es auf der Webseite und in der App ein: eine Schriftprobe je
Tonlage. Der Agent schreibt danach, statt sich einen Ton auszudenken.

Kommt keine Auskunft, gibt es kein Muster - und dann wird nicht geraten,
sondern nach den eingebauten Regeln geschrieben. Gesagt wird es trotzdem.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

UNIVERSE = Path(__file__).resolve().parent.parent

#: Die Tonlagen und das Fach, in dem ihre Schriftprobe liegt.
TONLAGEN = {
    "foermlich": "email-formell",
    "normal": "email-normal",
    "casual": "email-casual",
}


def _kern_muster():
    schon = sys.modules.get("kern_muster")
    if schon is not None:
        return schon
    stelle = importlib.util.spec_from_file_location(
        "kern_muster", UNIVERSE / "kern" / "muster.py")
    modul = importlib.util.module_from_spec(stelle)
    sys.modules["kern_muster"] = modul
    stelle.loader.exec_module(modul)
    return modul


def alle(nutzer: str = "") -> tuple[dict, str]:
    """Die hinterlegten Schriftproben je Tonlage. Leere Faecher fallen weg."""
    try:
        roh, grund = _kern_muster().alle_muster(nutzer)
    except Exception as fehler:  # noqa: BLE001 - ohne Hub laeuft der Agent weiter
        return {}, "Muster nicht abrufbar: %s" % str(fehler)[:120]
    if grund:
        return {}, grund
    aus = {}
    for tonlage, fach in TONLAGEN.items():
        text = (roh.get(fach) or "").strip()
        if text:
            aus[tonlage] = text
    return aus, ""


def als_anweisung(nutzer: str = "") -> str:
    """Der Block fuer das Modell. Leer heisst: der Nutzer hat nichts hinterlegt.

    Absichtlich leer statt mit einem Ersatztext: eine erfundene Schriftprobe
    waere schlimmer als keine - der Agent wuerde dann sicher im falschen Ton
    schreiben statt unsicher im eigenen.
    """
    muster, _ = alle(nutzer)
    if not muster:
        return ""
    stuecke = ["## Wie DIESER Nutzer schreibt",
               "",
               "Das Folgende hat er selbst hinterlegt. Es steht ueber den",
               "allgemeinen Schreibregeln: wo sein Muster anders klingt als die",
               "Regel, gilt sein Muster. Uebernimm Anrede, Satzlaenge, Wortwahl",
               "und Grussformel-Naehe - nicht den Inhalt.", ""]
    for tonlage in ("foermlich", "normal", "casual"):
        if tonlage in muster:
            stuecke.append("### Seine Schriftprobe fuer die Tonlage %s" % tonlage)
            stuecke.append("")
            stuecke.append(muster[tonlage][:8000])
            stuecke.append("")
    return "\n".join(stuecke)
