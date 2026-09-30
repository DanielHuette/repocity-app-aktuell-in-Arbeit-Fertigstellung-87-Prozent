"""Der Quellenkatalog: was der Researcher regelmäßig abgeht."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from einstellungen import BASIS

KATALOG_DATEI = BASIS / "quellen_katalog.json"


@dataclass
class Quelle:
    name: str
    art: str
    url: str
    kategorie: str
    themen: list
    lizenz: str = ""
    aktiv: bool = True


def laden(nur_aktive: bool = True, kategorien: list[str] | None = None) -> list[Quelle]:
    if not KATALOG_DATEI.exists():
        return []
    roh = json.loads(KATALOG_DATEI.read_text(encoding="utf-8"))
    quellen = []
    for eintrag in roh.get("quellen", []):
        quelle = Quelle(
            name=eintrag.get("name", ""), art=eintrag.get("art", "seite"),
            url=eintrag.get("url", ""), kategorie=eintrag.get("kategorie", ""),
            themen=eintrag.get("themen", []), lizenz=eintrag.get("lizenz", ""),
            aktiv=bool(eintrag.get("aktiv", True)))
        if nur_aktive and not quelle.aktiv:
            continue
        if kategorien and quelle.kategorie not in kategorien:
            continue
        quellen.append(quelle)
    return quellen


def kategorien() -> list[str]:
    return sorted({quelle.kategorie for quelle in laden(nur_aktive=False)})