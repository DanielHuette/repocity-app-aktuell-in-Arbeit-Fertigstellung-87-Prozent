"""Der Zusammenbau: aus dem Curriculum wird eine einzige HTML-Datei.

Das ist der Kern des Verfahrens aus dem Vorbild — nicht ein Kurs, der aus
zwanzig Dateien besteht und einen Server braucht, sondern **eine Datei, die
man oeffnet**. Sie merkt sich den Fortschritt im Browser, sperrt das
Weiterkommen ohne geloeste Aufgabe und vergibt XP.

Medien werden eingebettet, solange sie klein sind — sonst liegen sie daneben
und die Datei verweist auf sie. Eine 300-MB-HTML-Datei hilft niemandem.
"""
from __future__ import annotations

import base64
import json
import mimetypes
from dataclasses import asdict
from pathlib import Path

import einstellungen as e
from modelle import Curriculum

# Bis hierhin wird eingebettet. Darueber bleibt die Datei daneben liegen.
EINBETTEN_MAX = 2_500_000


def _daten_url(pfad: Path) -> str:
    art = mimetypes.guess_type(str(pfad))[0] or "application/octet-stream"
    roh = base64.b64encode(pfad.read_bytes()).decode("ascii")
    return f"data:{art};base64,{roh}"


def baue(c: Curriculum, kurs_id: str, ziel: Path, medien: dict[int, dict] | None = None) -> Path:
    medien = medien or {}
    vorlage = (Path(__file__).resolve().parent / "vorlagen" / "kurs.html").read_text(encoding="utf-8")

    level = []
    for l in c.level:
        eintrag = {
            "titel": l.titel,
            "lernziel": l.lernziel,
            "lehrtext": l.lehrtext,
            "bild_hinweis": l.bild_hinweis,
        }
        if l.aufgabe:
            eintrag["aufgabe"] = asdict(l.aufgabe)

        m = medien.get(l.nr, {})
        for name, schluessel in (("video", "video"), ("ton", "ton")):
            pfad = m.get(schluessel)
            if not pfad:
                continue
            pfad = Path(pfad)
            if not pfad.exists():
                continue
            if pfad.stat().st_size <= EINBETTEN_MAX:
                eintrag[name] = _daten_url(pfad)
            else:
                daneben = ziel.parent / "medien" / pfad.name
                daneben.parent.mkdir(parents=True, exist_ok=True)
                if pfad.resolve() != daneben.resolve():
                    daneben.write_bytes(pfad.read_bytes())
                eintrag[name] = f"medien/{pfad.name}"
        level.append(eintrag)

    daten = {
        "id": kurs_id,
        "titel": c.titel,
        "untertitel": c.untertitel,
        "einleitung": getattr(c, "einleitung", ""),
        "abschluss": getattr(c, "abschluss", ""),
        "level": level,
    }

    html = (vorlage
            .replace("__TITEL__", _sicher(c.titel))
            .replace("__FUSS__", "RepoCity · speedofthespirit.dev")
            .replace("__DATEN__", json.dumps(daten, ensure_ascii=False)
                     .replace("</", "<\\/")))

    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(html, encoding="utf-8", newline="")
    return ziel


def _sicher(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))
