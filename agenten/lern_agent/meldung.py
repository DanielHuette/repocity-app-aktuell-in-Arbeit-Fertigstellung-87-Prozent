"""Meldeweg der Lern-Werkstatt zum Sekretär und zur RepoCity App.

Der Weg selbst steht in universe/kern/melden.py, damit alle Agenten
denselben gehen. Hier steht nur, unter welcher Kennung diese Werkstatt
meldet und wie ihre Aufrufe aussehen.

Bis zum 09.09.2026 rief diese Datei den Hub selbst an, unter der Adresse
`/api/meldung`. Die hat es dort nie gegeben - der Hub kennt `/api/hub/push`.
Jede Meldung dieser Werkstatt fiel in den Fehlerzweig und landete in einem
Ordner `_meldungen` neben der Werkstatt, den niemand liest. Zwei Wege für
dieselbe Sache, einer davon ins Leere; zusammengelegt.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern import melden as _melden            # noqa: E402
from kern.melden import (                     # noqa: E402,F401
    TAGEBUCH,
    ins_tagebuch,
    offene_meldungen,
)

#: Unter dieser Kennung meldet dieser Agent - die MODUL-Kennung aus
#: Modul.kt, nicht der Ordnername und nicht der Agentenname. Vorher hiess
#: dieselbe Stelle mal "video_agent", mal "prod.video.clip", mal
#: "wohnungs-agent"; wer danach gruppiert - und der
#: Kostenstellenverantwortliche tut das - zaehlt eine Stelle mehrfach.
MODUL = "prod.lernen"


def melde(art: str, text: str, dazu: dict | None = None) -> bool:
    """Eine Meldung der Werkstatt. True, wenn der Hub sie angenommen hat.

    ``art`` ist der Schritt (start, angenommen, fertig, fehler, halt),
    ``dazu`` sind die Messwerte. Steht in ``dazu`` ein ``auftrag``, wird er
    als Vorgang mitgegeben - daran haengt die App ihre Fortschrittsanzeige
    auf.
    """
    dazu = dazu or {}
    vorgang = dazu.get("auftrag") or dazu.get("id") or None
    return _melden.melde(MODUL, text, art=art, zusammenfassung=text[:300],
                         vorgang=vorgang, daten=dazu)
