"""Zugang zu den vier Säulen des 2nd brain.

Der Code liegt in universe/kern/gehirn.py, damit alle Agenten dieselbe
Fassung benutzen. Die Pfade stehen in universe/gehirn.json.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern.gehirn import (  # noqa: E402,F401
    Fund,
    STANDARD_PFADE,
    als_kontext,
    ergebnis_nachtragen,
    lernen,
    lesen,
    standard_konfiguration,
)