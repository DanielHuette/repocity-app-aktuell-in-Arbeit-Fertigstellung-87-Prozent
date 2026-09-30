"""Was durch die Lern-Werkstatt wandert.

Das Curriculum ist die eigentliche Sache: es wird zuerst geschrieben, von
Daniel gelesen und abgenommen, und erst danach wird etwas erzeugt.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class Zustand(str, Enum):
    ANGENOMMEN = "angenommen"
    BRIEFING = "briefing"
    CURRICULUM = "curriculum"
    WARTET_AUF_ABNAHME = "wartet_auf_abnahme"
    ERZEUGUNG = "erzeugung"
    ZUSAMMENBAU = "zusammenbau"
    VORLAGE = "vorlage"
    FERTIG = "fertig"
    FEHLER = "fehler"


# Die Aufgabenarten aus dem Vorbild. Mehr braucht es nicht — mit diesen
# vier laesst sich fast jeder Lernstoff abfragen.
AUFGABENARTEN = ("zuordnen", "regler", "wahl", "reihenfolge")


@dataclass
class Aufgabe:
    art: str = "wahl"
    frage: str = ""
    # zuordnen: {"begriffe": [...], "faecher": [...], "loesung": {"begriff": "fach"}}
    # regler:   {"von": 0, "bis": 100, "einheit": "%", "loesung": 30, "toleranz": 10}
    # wahl:     {"antworten": [...], "loesung": 2}
    # reihenfolge: {"schritte": [...], "loesung": [2,0,1]}
    daten: dict = field(default_factory=dict)
    hinweis: str = ""
    punkte: int = 10


@dataclass
class Level:
    nr: int = 1
    titel: str = ""
    lernziel: str = ""
    lehrtext: str = ""          # was auf dem Bildschirm steht
    sprechertext: str = ""      # was der Erzaehler sagt
    aufgabe: Aufgabe | None = None
    bild_hinweis: str = ""      # woraus die Animation gebaut wird


@dataclass
class Curriculum:
    titel: str = ""
    untertitel: str = ""
    zielgruppe: str = ""
    vorwissen: str = ""
    minuten: int = 25
    level: list[Level] = field(default_factory=list)


@dataclass
class Auftrag:
    thema: str
    zielgruppe: str = "Mitarbeiter ohne Vorkenntnisse"
    vorwissen: str = "keines"
    minuten: int = 25
    level_anzahl: int = 5
    stil: str = "3D-Render, ruhig, sachlich"
    trocken: bool = True
    #: Was der Kurator zum Thema herausgegeben hat. Legt der Verteiler hinein.
    stoff: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    angelegt: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Ergebnis:
    auftrag: Auftrag
    zustand: Zustand = Zustand.ANGENOMMEN
    curriculum: Curriculum | None = None
    kurs: Path | None = None
    protokoll: list[str] = field(default_factory=list)
    fehler: str = ""

    def merke(self, zeile: str) -> None:
        marke = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.protokoll.append(f"{marke}  {zeile}")
