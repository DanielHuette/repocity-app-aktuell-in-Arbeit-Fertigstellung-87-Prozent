"""Die Erzaehlerstimme.

edge-tts: Microsofts Stimmen, kein Konto, keine Kosten — dieselbe Loesung
wie in der Video-Werkstatt. Fehlt das Werkzeug oder ist Trockenlauf, bleibt
der Erzaehler stumm und die Schulung laeuft trotzdem: Text steht ohnehin
auf dem Bildschirm.
"""
from __future__ import annotations

import shutil
import subprocess

# Kein Konsolenfenster fuer Hilfsprogramme (ffmpeg, node, npm, ...).
# Eine Quelle: universe/kern/ohne_fenster.py - ueber den Pfad geladen,
# weil im Universe zwoelf Ordner gleichnamige Module haben.
import importlib.util as _iu
from pathlib import Path as _P
for _o in _P(__file__).resolve().parents:
    _k = _o / "kern" / "ohne_fenster.py"
    if _k.exists():
        _s = _iu.spec_from_file_location("ohne_fenster", _k)
        _m = _iu.module_from_spec(_s)
        _s.loader.exec_module(_m)
        break
from pathlib import Path

import einstellungen as e


def verfuegbar() -> bool:
    return shutil.which("edge-tts") is not None


def sprich(text: str, ziel: Path) -> Path | None:
    if not e.STIMME_AN or not text.strip() or not verfuegbar():
        return None
    ziel.parent.mkdir(parents=True, exist_ok=True)
    befehl = ["edge-tts", "--voice", e.STIMME, "--rate", e.SPRECHTEMPO,
              "--text", text, "--write-media", str(ziel)]
    try:
        subprocess.run(befehl, check=True, capture_output=True, timeout=180)
    except Exception:
        return None
    return ziel if ziel.exists() and ziel.stat().st_size > 0 else None
