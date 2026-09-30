"""Animationen ueber HyperFrames.

HyperFrames macht aus HTML/CSS/JS ein MP4 — deterministisch, gleiche Eingabe,
gleiches Ergebnis. Es kostet nichts ausser Rechenzeit. Node und ffmpeg
muessen da sein.

Das ist das Werkzeug aus dem Vorbild. Bleibt es aus, zeigt der Kurs statt
des Videos einen beschrifteten Platz — die Schulung funktioniert trotzdem.
"""
from __future__ import annotations

import json
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
    return shutil.which("node") is not None and shutil.which("ffmpeg") is not None


def baue(szene_html: str, ziel: Path, sekunden: float = 8.0) -> Path | None:
    if not e.HYPERFRAMES_AN or not verfuegbar():
        return None
    ziel.parent.mkdir(parents=True, exist_ok=True)
    arbeit = ziel.parent / "_szene"
    arbeit.mkdir(parents=True, exist_ok=True)
    (arbeit / "index.html").write_text(szene_html, encoding="utf-8", newline="")
    (arbeit / "hyperframes.json").write_text(
        json.dumps({"duration": sekunden, "fps": 30, "width": 1280, "height": 720}),
        encoding="utf-8", newline="")
    befehl = e.HYPERFRAMES_BEFEHL.split() + ["render", str(arbeit), "--out", str(ziel)]
    try:
        subprocess.run(befehl, check=True, capture_output=True, timeout=900)
    except Exception:
        return None
    return ziel if ziel.exists() else None


def szene(titel: str, punkte: list[str], hinweis: str) -> str:
    """Eine schlichte Szene im Markenlicht: Titel, dann Punkt fuer Punkt.

    Bewusst einfach gehalten — was zaehlt, ist die Uebereinstimmung mit dem
    gesprochenen Wort, nicht der Effekt.
    """
    zeilen = "".join(
        f'<li style="animation-delay:{0.8 + i * 1.4}s">{p}</li>' for i, p in enumerate(punkte)
    )
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
      body{{margin:0;width:1280px;height:720px;background:#030304;color:#EDF2F8;
        font:28px/1.5 system-ui,sans-serif;display:flex;flex-direction:column;
        justify-content:center;padding:0 90px}}
      h1{{font-size:52px;margin:0 0 34px;color:#F0B463;
        animation:auf .8s cubic-bezier(.16,1,.3,1) both}}
      li{{margin:0 0 20px;opacity:0;animation:auf .7s cubic-bezier(.16,1,.3,1) both}}
      ul{{list-style:none;padding:0;margin:0}}
      .hinweis{{position:absolute;bottom:44px;left:90px;font-size:16px;color:#5E6875}}
      @keyframes auf{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:none}}}}
    </style></head><body>
      <h1>{titel}</h1><ul>{zeilen}</ul>
      <div class="hinweis">{hinweis}</div>
    </body></html>"""
