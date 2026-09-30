"""Meldeweg zum Sekretär und zur RepoCity App.

Der Code liegt in universe/kern/melden.py, damit alle Agenten denselben Weg gehen.
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


#: Unter dieser Kennung meldet dieser Agent - die MODUL-Kennung aus
#: Modul.kt, nicht der Ordnername und nicht der Agentenname. Vorher hiess
#: dieselbe Stelle mal "video_agent", mal "prod.video.clip", mal
#: "wohnungs-agent"; wer danach gruppiert - und der
#: Kostenstellenverantwortliche tut das - zaehlt eine Stelle mehrfach.
MODUL = "wissen.research"


def melde(text: str, art: str = "info", zusammenfassung: str = "",
          vorgang: str | None = None, daten: dict | None = None,
          absender: str | None = None) -> bool:
    """Meldet unter der Modul-Kennung dieses Agenten."""
    return _melden.melde(absender or MODUL, text, art=art,
                         zusammenfassung=zusammenfassung, vorgang=vorgang,
                         daten=daten)
