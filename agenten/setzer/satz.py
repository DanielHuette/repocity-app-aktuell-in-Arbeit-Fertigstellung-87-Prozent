# -*- coding: utf-8 -*-
"""Der Satz - aus dem gegliederten Inhalt wird eine PDF-Datei.

Gesetzt wird mit reportlab, in den Farben eines Kits (universe/marke/kits.json
fuer die fuenf neuen; die sechs aelteren stehen nur in Kit.kt/kits.css und
fallen hier auf das Standardkit zurueck). Titelseite, laufende Ueberschriften,
Seitenzahlen, eine Fusszeile mit RepoCity - kein fremder Name (Regel 1).

Die Schriften sind die eingebauten von reportlab (Helvetica). Sie tragen
Umlaute, brauchen keine Datei und sehen auf jedem Rechner gleich aus.
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer)


def _eigen(name: str):
    """Einen Baustein dieses Agenten ueber seinen Pfad laden, nicht ueber den
    Suchpfad - einstellungen.py gibt es zwoelfmal im Universe."""
    import importlib.util as _iu
    _p = Path(__file__).resolve().parent
    _spec = _iu.spec_from_file_location("%s_%s" % (_p.name, name), _p / (name + ".py"))
    _m = _iu.module_from_spec(_spec)
    import sys as _sys
    _sys.modules[_spec.name] = _m   # dataclasses brauchen das Modul dort
    _spec.loader.exec_module(_m)
    return _m

from pathlib import Path as _Pfad

e = _eigen("einstellungen")
KITS_JSON = e.UNIVERSE / "marke" / "kits.json"


def farben(kit: str) -> dict:
    """Grund, Schrift, Signal und gedaempfte Schrift eines Kits als '#RRGGBB'."""
    def hexe(argb: str) -> str:
        return "#" + argb[-6:]
    try:
        alle = {k["id"]: k for k in json.loads(KITS_JSON.read_text(encoding="utf-8"))["kits"]}
    except (OSError, ValueError, KeyError):
        alle = {}
    k = alle.get(kit) or alle.get(e.KIT_STANDARD)
    if not k:
        return {"grund": "#EEE5D2", "schrift": "#171B23", "akzent": "#765E49", "leise": "#60605F"}
    return {"grund": hexe(k["ground"]), "schrift": hexe(k["text"]),
            "akzent": hexe(k["accent"]), "leise": hexe(k["textMuted"])}


def _stile(f: dict) -> dict:
    return {
        "titel": ParagraphStyle("titel", fontName="Helvetica-Bold", fontSize=30, leading=36,
                                textColor=f["schrift"], spaceAfter=10, alignment=TA_LEFT),
        "untertitel": ParagraphStyle("untertitel", fontName="Helvetica", fontSize=14, leading=18,
                                     textColor=f["akzent"], spaceAfter=6),
        "h": ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=15, leading=19,
                            textColor=f["akzent"], spaceBefore=14, spaceAfter=6),
        "p": ParagraphStyle("p", fontName="Helvetica", fontSize=10.5, leading=15,
                            textColor=f["schrift"], spaceAfter=7),
        "fein": ParagraphStyle("fein", fontName="Helvetica", fontSize=8.5, leading=11,
                               textColor=f["leise"]),
    }


def _entschaerfen(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def setzen(doku, ziel: Path, kit: str = "", auftrag_id: str = "") -> Path:
    f = farben(kit or e.KIT_STANDARD)
    st = _stile(f)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    breite, hoehe = e.SEITE

    def seite(canvas, doc):
        canvas.saveState()
        # Grundfarbe des Kits als schmaler Streifen oben - das Kit ist erkennbar,
        # das Blatt bleibt weiss und druckbar.
        canvas.setFillColor(f["akzent"])
        canvas.rect(0, hoehe - 6 * mm, breite, 6 * mm, stroke=0, fill=1)
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(f["leise"])
        canvas.drawString(e.RAND, 12 * mm, "RepoCity · " + doku.titel[:70])
        canvas.drawRightString(breite - e.RAND, 12 * mm, "Seite %d" % doc.page)
        canvas.restoreState()

    bau = SimpleDocTemplate(str(ziel), pagesize=e.SEITE,
                            leftMargin=e.RAND, rightMargin=e.RAND,
                            topMargin=e.RAND + 8 * mm, bottomMargin=e.RAND,
                            title=doku.titel, author="RepoCity",
                            subject=doku.untertitel or doku.titel)
    fluss = [Spacer(1, 60 * mm), Paragraph(_entschaerfen(doku.titel), st["titel"])]
    if doku.untertitel:
        fluss.append(Paragraph(_entschaerfen(doku.untertitel), st["untertitel"]))
    fluss.append(Spacer(1, 8 * mm))
    fluss.append(Paragraph(_entschaerfen("Gesetzt von RepoCity" + (" · Auftrag " + auftrag_id if auftrag_id else "")), st["fein"]))
    fluss.append(PageBreak())
    for ab in doku.abschnitte:
        if ab.ueberschrift:
            fluss.append(Paragraph(_entschaerfen(ab.ueberschrift), st["h"]))
        for absatz in ab.absaetze:
            fluss.append(Paragraph(_entschaerfen(absatz), st["p"]))
    bau.build(fluss, onFirstPage=seite, onLaterPages=seite)
    return ziel
