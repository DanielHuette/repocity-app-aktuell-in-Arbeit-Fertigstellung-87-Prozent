"""Posteingang für andere Agenten — der Code liegt in universe/kern/posteingang.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern.posteingang import DATEI, lesen, merken  # noqa: E402,F401