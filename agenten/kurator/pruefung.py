"""Was in die Säulen darf, und was zurückgeht.

Der Kurator ist die einzige Stelle, die schreibt. Deshalb prüft er:
fehlt der Kopf, fehlt die Quelle, ist die Notiz zu dünn oder steht sie schon
im Bestand — dann wird nicht eingepflegt, sondern vermerkt.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

KOPF = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


@dataclass
class Befund:
    ok: bool
    gruende: list[str] = field(default_factory=list)


def kopf_lesen(text: str) -> dict:
    treffer = KOPF.match(text)
    if not treffer:
        return {}
    felder: dict[str, str] = {}
    for zeile in treffer.group(1).splitlines():
        if ":" in zeile and not zeile.startswith((" ", "-")):
            schluessel, _, wert = zeile.partition(":")
            felder[schluessel.strip()] = wert.strip().strip('"').strip("'")
    return felder


def notiz_pruefen(text: str, regeln: dict, dateiname: str = "") -> Befund:
    gruende: list[str] = []
    kopf = kopf_lesen(text)
    if not kopf:
        gruende.append("kein Kopf mit Frontmatter")
    for feld in regeln.get("pflichtfelder", []):
        if not kopf.get(feld):
            gruende.append(f"Feld fehlt: {feld}")
    if "quellen" not in text and "quelle" not in kopf:
        gruende.append("keine Quelle angegeben")
    koerper = KOPF.sub("", text).strip()
    if len(koerper) < regeln.get("mindestzeichen_notiz", 400):
        gruende.append(f"zu dünn ({len(koerper)} Zeichen)")
    gruende += _titel_pruefen(kopf.get("title", ""), regeln, dateiname)
    return Befund(not gruende, gruende)


def _titel_pruefen(titel: str, regeln: dict, dateiname: str = "") -> list[str]:
    """Sagt der Titel, worum es geht?

    Bis zum 13.09.2026 stand bei 6.640 von 6.668 Notizen der Dateiname als Titel
    ("0_300k_subscribers_with_1_video_transcript"). Der Kurator hat sie trotzdem
    angenommen, weil er nur prüfte, DASS ein Titel dasteht. Wer die Trefferliste
    einer Bedeutungssuche liest, sah damit nur Dateinamen.

    Geprüft wird deshalb hier, an der einen Stelle, die in die Säulen schreibt —
    egal, welcher Agent liefert.
    """
    gruende: list[str] = []
    titel = (titel or "").strip()
    if not titel:
        return gruende                       # das fehlende Feld ist schon gemeldet

    mindestens = regeln.get("titel_mindestwoerter", 4)
    hoechstens = regeln.get("titel_hoechstzeichen", 120)
    if len(titel.split()) < mindestens:
        gruende.append(f"Titel sagt nichts ({len(titel.split())} Wörter, "
                       f"mindestens {mindestens}): {titel[:50]!r}")
    if len(titel) > hoechstens:
        gruende.append(f"Titel zu lang ({len(titel)} Zeichen, höchstens {hoechstens})")
    if "_" in titel:
        gruende.append(f"Unterstrich im Titel — das ist ein Dateiname: {titel[:50]!r}")
    for wort in regeln.get("titel_verbotene_reste", ["transcript", "untitled", "ohne titel"]):
        if wort in titel.lower():
            gruende.append(f"Dateinamenrest im Titel: {wort!r}")
    if dateiname:
        stamm = dateiname.rsplit(".", 1)[0]
        if titel == stamm or titel.replace(" ", "_") == stamm:
            gruende.append("Titel ist der Dateiname")
    return gruende


def atom_pruefen(atom: dict, regeln: dict) -> Befund:
    gruende: list[str] = []
    if len((atom.get("aussage") or "").strip()) < regeln.get("atom_mindestzeichen", 20):
        gruende.append("Aussage zu kurz")
    if not atom.get("quelle"):
        gruende.append("keine Quelle")
    if not (atom.get("beleg") or "").strip():
        gruende.append("kein Beleg")
    return Befund(not gruende, gruende)


def _fingerabdruck(text: str) -> str:
    sauber = re.sub(r"\W+", " ", (text or "").lower()).strip()
    return " ".join(sauber.split()[:40])


class Bestand:
    """Was schon in den Säulen liegt — für die Doppelungsprüfung."""

    def __init__(self, wissen: Path, atome: Path) -> None:
        self.titel: set[str] = set()
        self.quellen: set[str] = set()
        self.aussagen: set[str] = set()

        if wissen.exists():
            for datei in wissen.rglob("*.md"):
                try:
                    inhalt = datei.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                kopf = kopf_lesen(inhalt)
                if kopf.get("title"):
                    self.titel.add(_fingerabdruck(kopf["title"]))
                for verweis in re.findall(r"https?://\S+", inhalt[:1500]):
                    self.quellen.add(verweis.rstrip(").,"))

        if atome.exists():
            for datei in atome.rglob("*.jsonl"):
                try:
                    with datei.open(encoding="utf-8") as offen:
                        for zeile in offen:
                            zeile = zeile.strip()
                            if not zeile:
                                continue
                            try:
                                atom = json.loads(zeile)
                            except json.JSONDecodeError:
                                continue
                            self.aussagen.add(_fingerabdruck(atom.get("aussage", "")))
                except OSError:
                    continue

    def kennt_notiz(self, text: str) -> str:
        kopf = kopf_lesen(text)
        if kopf.get("title") and _fingerabdruck(kopf["title"]) in self.titel:
            return "Titel schon im Bestand"
        for verweis in re.findall(r"https?://\S+", text[:1500]):
            if verweis.rstrip(").,") in self.quellen:
                return "Quelle schon im Bestand"
        return ""

    def kennt_atom(self, atom: dict) -> str:
        return ("Aussage schon im Bestand"
                if _fingerabdruck(atom.get("aussage", "")) in self.aussagen else "")

    def merken_notiz(self, text: str) -> None:
        kopf = kopf_lesen(text)
        if kopf.get("title"):
            self.titel.add(_fingerabdruck(kopf["title"]))
        for verweis in re.findall(r"https?://\S+", text[:1500]):
            self.quellen.add(verweis.rstrip(").,"))

    def merken_atom(self, atom: dict) -> None:
        self.aussagen.add(_fingerabdruck(atom.get("aussage", "")))