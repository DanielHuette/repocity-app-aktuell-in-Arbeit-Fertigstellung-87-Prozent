"""Zugangsdaten aus der .env — der Code liegt in universe/kern/umgebung.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern.umgebung import (  # noqa: E402,F401
    bericht,
    datei_finden,
    einsetzen,
    fehlt,
    laden,
    offene_platzhalter,
)

laden()