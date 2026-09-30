"""Ablage — der Code liegt in universe/kern/uebergabe.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern.uebergabe import (  # noqa: E402,F401
    atome_anhaengen,
    fall_ablegen,
    notiz_schreiben,
    ordner_anlegen,
    quellen_schreiben,
    schluessel,
    uebergabe_schreiben,
)