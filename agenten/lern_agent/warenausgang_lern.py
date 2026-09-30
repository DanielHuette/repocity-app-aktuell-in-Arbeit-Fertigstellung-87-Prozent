# -*- coding: utf-8 -*-
"""Das fertige Stueck in den Warenausgang legen.

Bis zum 09.09.2026 endete die Lern-Werkstatt beim fertigen Kurs: er lag
in `zustand/lern_fertig` und niemand erfuhr davon. Der Warenausgang ist
die Stelle, an der Daniel freigibt - und erst danach darf ein anderer Agent
es abholen, etwa Social Media fuer einen Beitrag. Ohne diesen Schritt war
die Lern-Strasse eine Sackgasse.

Gebaut wie beim Video-Agenten (`video_agent/anschluss.py`), damit es einen
Weg gibt und nicht zwei.
"""
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


def einstellen(auftrag_id: str, titel: str, stueck: Path, sekunden: float,
               zweck: str, kosten: float, befund_text: str,
               trocken: bool = False) -> str:
    """Gibt die Kennung im Warenausgang zurueck - oder leer, wenn es nicht ging.

    Bricht nie ab: ein Stueck, das fertig ist, soll nicht daran scheitern,
    dass der Warenausgang klemmt. Es liegt dann eben nur in der Ablage.
    """
    if not ANGESCHLOSSEN or stueck is None:
        return ""
    try:
        eintrag = warenausgang.einstellen(
            was="lernprogramm", auftrag=auftrag_id, modul="prod.lernen", titel=titel,
            datei=str(stueck), gueteklasse="einfach",
            laenge="%.0f s" % sekunden, format_="html", stimme="",
            bildquellen="", kosten=kosten,
            abgenommen_von="qualitaetsmanager",
            taugt_fuer=zweck or "hintergrund",
            notiz=befund_text,
            art=rueckweg.TROCKEN if trocken else rueckweg.ECHT)
        return eintrag["kennung"]
    except Exception:                                      # noqa: BLE001
        return ""
