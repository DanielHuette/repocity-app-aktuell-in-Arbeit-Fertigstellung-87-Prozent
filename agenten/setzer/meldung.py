# -*- coding: utf-8 -*-
"""Meldeweg des Setzers - derselbe wie bei allen Agenten (kern/melden.py)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern import melden as _melden            # noqa: E402

#: Die MODUL-Kennung aus Modul.kt - danach gruppiert der Kostenstellenverantwortliche.
MODUL = "prod.pdf"


def melde(art: str, text: str, dazu: dict | None = None) -> bool:
    dazu = dazu or {}
    vorgang = dazu.get("auftrag") or dazu.get("id") or None
    return _melden.melde(MODUL, text, art=art, zusammenfassung=text[:300],
                         vorgang=vorgang, daten=dazu)
