"""Meldeweg des Sicherheitsbeauftragten.

Der Weg selbst liegt in universe/kern/melden.py, damit alle Agenten
denselben gehen. Hier steht nur, unter welcher Kennung dieser Agent meldet.

Die Kennung ist die MODUL-Kennung aus Modul.kt - nicht der Ordnername und
nicht der Agentenname. Vorher meldete sich dieselbe Stelle mal als
"video_agent", mal als "prod.video.clip", mal als "wohnungs-agent". Wer
danach gruppiert - und der Kostenstellenverantwortliche tut das - zaehlt
eine Stelle mehrfach und findet Stillstand, wo keiner ist.

Die Datei im Kern heisst melden.py und nicht meldung.py: elf Agenten haben
eine eigene meldung.py, und Python haelt nur ein Modul je Namen.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern import melden as _melden  # noqa: E402
from kern.melden import (  # noqa: E402,F401
    TAGEBUCH,
    ins_tagebuch,
    offene_meldungen,
)

#: Unter dieser Kennung meldet dieser Agent. Eine Modul-Kennung aus Modul.kt.
MODUL = "system.sicherheit"


def melde(text: str, art: str = "info", zusammenfassung: str = "",
          vorgang: str | None = None, daten: dict | None = None,
          absender: str | None = None) -> bool:
    """Meldet unter der Modul-Kennung dieses Agenten.

    absender  nur setzen, wenn dieser Agent fuer mehrere Module arbeitet -
              der Video-Agent bedient prod.video.clip und prod.video.stueck.
    """
    return _melden.melde(absender or MODUL, text, art=art,
                         zusammenfassung=zusammenfassung, vorgang=vorgang,
                         daten=daten)
