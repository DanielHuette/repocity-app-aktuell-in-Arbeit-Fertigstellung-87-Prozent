"""Destillat — der Code liegt in universe/kern/destillat.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern.destillat import (  # noqa: E402,F401
    AUFTRAG,
    NOTIZ,
    SYSTEM,
    _ohne_modell,
    atome_bauen,
    destillieren,
    json_lesen,
    notiz_bauen,
    verfuegbar,
)