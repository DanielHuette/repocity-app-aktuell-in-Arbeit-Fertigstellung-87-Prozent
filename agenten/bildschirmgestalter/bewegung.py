# -*- coding: utf-8 -*-
"""Der bewegte Schoner - eine langsame Kamerafahrt ueber das Standbild.

ffmpeg zoomt ueber die eingestellte Dauer sanft hinein (zoompan), ohne Ton,
als MP4, das jeder Bildschirmschoner und jedes Handy abspielt. Ohne ffmpeg
gibt es keinen Film - das Standbild bleibt trotzdem ein fertiges Stueck.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _eigen(name: str):
    """Einen Baustein dieses Agenten ueber seinen Pfad laden, nicht ueber den
    Suchpfad - einstellungen.py gibt es zwoelfmal im Universe."""
    import importlib.util as _iu
    _p = Path(__file__).resolve().parent
    _spec = _iu.spec_from_file_location("%s_%s" % (_p.name, name), _p / (name + ".py"))
    _m = _iu.module_from_spec(_spec)
    import sys as _sys
    _sys.modules[_spec.name] = _m   # dataclasses brauchen das Modul dort
    _spec.loader.exec_module(_m)
    return _m



e = _eigen("einstellungen")


def film(standbild: Path, ziel: Path) -> Path | None:
    weg = e.ffmpeg()
    if not weg:
        return None
    bilder = e.BEWEGT_SEKUNDEN * e.BILDER_JE_SEKUNDE
    # zoompan: z waechst je Bild um (ZOOM-1)/bilder, die Kamera bleibt mittig.
    filter_ = ("scale=iw*2:ih*2,zoompan=z='min(zoom+%.6f,%.4f)':d=%d:"
               "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=%dx%d:fps=%d,format=yuv420p"
               % ((e.BEWEGT_ZOOM - 1) / bilder, e.BEWEGT_ZOOM, bilder,
                  _gerade(_groesse(standbild)[0]), _gerade(_groesse(standbild)[1]), e.BILDER_JE_SEKUNDE))
    befehl = [weg, "-y", "-loglevel", "error", "-loop", "1", "-i", str(standbild),
              "-vf", filter_, "-t", str(e.BEWEGT_SEKUNDEN), "-c:v", "libx264", "-preset", "medium",
              "-crf", "20", "-movflags", "+faststart", "-an", str(ziel)]
    try:
        import ohne_fenster  # noqa: F401  - kein Konsolenfenster (kern/ohne_fenster.py)
    except Exception:
        pass
    lauf = subprocess.run(befehl, capture_output=True, text=True, timeout=600)
    if lauf.returncode != 0 or not ziel.exists():
        raise RuntimeError("ffmpeg: " + (lauf.stderr or "").strip()[-400:])
    return ziel


def _groesse(pfad: Path) -> tuple[int, int]:
    from PIL import Image
    with Image.open(pfad) as b:
        return b.size


def _gerade(n: int) -> int:
    return n if n % 2 == 0 else n - 1
