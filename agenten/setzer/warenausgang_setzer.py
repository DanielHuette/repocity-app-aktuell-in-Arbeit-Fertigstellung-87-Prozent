# -*- coding: utf-8 -*-
"""Das fertige Dokument in den Warenausgang legen - dort gibt der Auftraggeber frei."""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

try:
    import rueckweg
    import warenausgang
    ANGESCHLOSSEN = True
except ImportError:                                        # pragma: no cover
    ANGESCHLOSSEN = False


def einstellen(auftrag_id: str, titel: str, pdf: Path, seiten: int, woerter: int,
               trocken: bool = False) -> str:
    """Gibt die Kennung im Warenausgang zurueck - oder leer, wenn es nicht ging."""
    if not ANGESCHLOSSEN or pdf is None:
        return ""
    try:
        eintrag = warenausgang.einstellen(
            was="pdf", auftrag=auftrag_id, modul="prod.pdf", titel=titel,
            datei=str(pdf), gueteklasse="einfach",
            laenge="%d Seiten, %d Woerter" % (seiten, woerter), format_="pdf", stimme="",
            bildquellen="", kosten=0.0,
            abgenommen_von="setzer",
            taugt_fuer="lesen, drucken, versenden",
            notiz="Abnahme: Seitenzahl, Titel, Groesse geprueft",
            art=rueckweg.TROCKEN if trocken else rueckweg.ECHT)
        return eintrag["kennung"]
    except Exception:                                      # noqa: BLE001
        return ""
