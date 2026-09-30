# -*- coding: utf-8 -*-
"""Der Inhalt eines Dokuments - gegliedert, bevor gesetzt wird.

Ein Dokument ist Titel, Untertitel und Abschnitte mit Ueberschrift und
Absaetzen. Woher das kommt:

  echt      das Modell gliedert und schreibt aus dem Auftrag (und dem Stoff
            aus dem 2nd Brain, wenn der Verteiler welchen beigelegt hat)
  trocken   der Auftragstext wird selbst zum Inhalt: jede Leerzeile trennt
            einen Absatz, eine Zeile mit '#' davor wird Ueberschrift. So laeuft
            die Strasse ohne Schluessel und ohne einen Cent.

Der Modellaufruf wird gebucht - eine Zeile dahinter (kern/modellkosten.py).
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
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
KERN = e.UNIVERSE / "kern"
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))


@dataclass
class Abschnitt:
    ueberschrift: str
    absaetze: list[str] = field(default_factory=list)


@dataclass
class Dokument:
    titel: str
    untertitel: str = ""
    abschnitte: list[Abschnitt] = field(default_factory=list)

    @property
    def woerter(self) -> int:
        return sum(len(a.split()) for ab in self.abschnitte for a in ab.absaetze)


def aus_text(titel: str, text: str) -> Dokument:
    """Trocken: der Auftragstext ist der Inhalt."""
    doku = Dokument(titel=titel.strip() or "Dokument")
    aktuell = Abschnitt(ueberschrift="")
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("#"):
            if aktuell.absaetze or aktuell.ueberschrift:
                doku.abschnitte.append(aktuell)
            aktuell = Abschnitt(ueberschrift=block.lstrip("# ").strip())
            continue
        aktuell.absaetze.append(" ".join(block.split()))
    if aktuell.absaetze or aktuell.ueberschrift:
        doku.abschnitte.append(aktuell)
    if not doku.abschnitte:
        doku.abschnitte.append(Abschnitt("", [titel]))
    return doku


def aus_json(roh: str, titel: str) -> Dokument:
    """Die Antwort des Modells - ein JSON-Block - in ein Dokument."""
    anfang, ende = roh.find("{"), roh.rfind("}")
    satz = json.loads(roh[anfang:ende + 1])
    doku = Dokument(titel=str(satz.get("titel") or titel).strip(),
                    untertitel=str(satz.get("untertitel") or "").strip())
    for ab in (satz.get("abschnitte") or [])[:e.ABSCHNITTE_MAX]:
        absaetze = [str(a).strip() for a in (ab.get("absaetze") or []) if str(a).strip()]
        doku.abschnitte.append(Abschnitt(str(ab.get("ueberschrift") or "").strip(), absaetze))
    if not doku.abschnitte:
        raise ValueError("Das Modell hat keine Abschnitte geliefert.")
    return doku


def _frage(titel: str, text: str, stoff: dict) -> str:
    teile = [
        "Du bist Setzer bei RepoCity. Gliedere und schreibe aus dem folgenden "
        "Auftrag ein sauberes deutsches Dokument. Antworte NUR mit JSON: "
        '{"titel": "...", "untertitel": "...", "abschnitte": [{"ueberschrift": "...", '
        '"absaetze": ["...", "..."]}]}. Hoechstens %d Abschnitte, jeder mit 1-4 Absaetzen. '
        "Keine Aufzaehlungszeichen, keine Markdown-Auszeichnung, keine Erfindungen: was "
        "der Auftrag nicht hergibt, wird nicht behauptet." % e.ABSCHNITTE_MAX,
        "Titel: " + titel,
        "Auftrag:\n" + text,
    ]
    try:
        import stoff as _stoff
        block = _stoff.als_anweisung(stoff) if stoff else ""
        if block:
            teile.append(block)
    except Exception:
        pass
    return "\n\n".join(teile)


def gliedern(titel: str, text: str, stoff: dict | None = None,
             trocken: bool = True, auftrag_id: str = "") -> tuple[Dokument, str]:
    """Das Dokument und der Weg, auf dem es entstand ('trocken' | 'modell')."""
    if trocken or not os.getenv("ANTHROPIC_API_KEY"):
        return aus_text(titel, text), "trocken"
    import anthropic  # erst hier - trocken laeuft ohne das Paket
    kunde = anthropic.Anthropic()
    antwort = kunde.messages.create(
        model=e.MODELL, max_tokens=6000,
        messages=[{"role": "user", "content": _frage(titel, text, stoff or {})}],
    )
    try:
        import modellkosten
        modellkosten.buchen(antwort, "prod.pdf", e.MODELL, "Dokument gliedern", auftrag_id)
    except Exception:
        pass
    roh = "".join(getattr(b, "text", "") for b in antwort.content)
    return aus_json(roh, titel), "modell"
