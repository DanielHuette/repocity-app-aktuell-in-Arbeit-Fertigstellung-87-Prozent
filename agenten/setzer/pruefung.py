# -*- coding: utf-8 -*-
"""Die Abnahme eines gesetzten Dokuments - vor der Vorlage, nicht danach.

Gemessen wird an der Datei, nicht am guten Willen: ist es eine PDF, hat sie
mindestens zwei Seiten (Titel und Inhalt), traegt sie den Titel, und ist sie
nicht leer. Was durchfaellt, sieht der Auftraggeber nicht.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path



@dataclass
class Befund:
    seiten: int = 0
    bytes: int = 0
    woerter: int = 0
    bestanden: bool = False
    gruende: list[str] = field(default_factory=list)


def seitenzahl(pdf: Path) -> int:
    """Seiten zaehlen, ohne fremdes Paket: reportlab schreibt je Seite ein
    Objekt '/Type /Page' (das '/Pages' des Baums zaehlt nicht mit)."""
    roh = pdf.read_bytes()
    return len(re.findall(rb"/Type\s*/Page(?![s/])", roh))


def pruefe(doku, pdf: Path) -> Befund:
    b = Befund(woerter=doku.woerter)
    if not pdf.exists():
        b.gruende.append("Die PDF-Datei fehlt.")
        return b
    roh = pdf.read_bytes()
    b.bytes = len(roh)
    if not roh.startswith(b"%PDF-"):
        b.gruende.append("Die Datei ist keine PDF.")
    b.seiten = seitenzahl(pdf)
    if b.seiten < 2:
        b.gruende.append("Weniger als zwei Seiten - Titelseite oder Inhalt fehlt.")
    if b.bytes < 1500:
        b.gruende.append("Die Datei ist zu klein, um ein Dokument zu sein.")
    if doku.woerter < 5:
        b.gruende.append("Der Inhalt hat weniger als fuenf Woerter.")
    # reportlab legt den Titel als Metadatum ab (/Title) - der muss drinstehen.
    # Umlaute schreibt es als Oktal-Fluchten (\\344), darum wird nur der
    # reine ASCII-Anfang des Titels gesucht.
    m = re.match(r"[A-Za-z0-9 ,.\-]+", doku.titel)
    kurz = (m.group(0) if m else "").strip()[:20]
    if len(kurz) < 3:
        kurz = doku.titel[:1].encode("latin-1", "ignore").decode("latin-1")
    if kurz and kurz.encode("latin-1", "ignore") not in roh:
        b.gruende.append("Der Titel steht nicht in der Datei.")
    b.bestanden = not b.gruende
    return b
