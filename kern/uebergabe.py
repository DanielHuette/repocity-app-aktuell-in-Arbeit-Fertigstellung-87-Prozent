"""Ergebnisse ablegen — im Eingang für den Kurator, Fälle in der Verbesserung.

Dasselbe Format für jeden Agenten, der Wissen anliefert. Der Kurator muss nur
eine Form kennen."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from . import gehirn


def ordner_anlegen(konfiguration: dict, thema: str) -> Path:
    eingang = Path(konfiguration["ablage"]["eingang"])
    ziel = eingang / f"{date.today().isoformat()}_{schluessel(thema)}"
    ziel.mkdir(parents=True, exist_ok=True)
    return ziel


def schluessel(text: str) -> str:
    for alt, neu in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        text = text.lower().replace(alt, neu)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:60] or "ohne-thema"


def notiz_schreiben(ziel: Path, name: str, text: str) -> Path:
    pfad = ziel / "wissen" / f"{schluessel(name)}.md"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(text, encoding="utf-8", newline="")
    return pfad


def atome_anhaengen(ziel: Path, atome: list[dict]) -> Path:
    pfad = ziel / "atome.jsonl"
    with pfad.open("a", encoding="utf-8") as datei:
        for atom in atome:
            datei.write(json.dumps(atom, ensure_ascii=False) + "\n")
    return pfad


def quellen_schreiben(ziel: Path, quellen: list[dict]) -> Path:
    pfad = ziel / "quellen.json"
    pfad.write_text(json.dumps(quellen, ensure_ascii=False, indent=1), encoding="utf-8", newline="")
    return pfad


def uebergabe_schreiben(ziel: Path, frage: str, quellen: list[dict],
                        anzahl_notizen: int, anzahl_atome: int,
                        agent: str = "deep-researcher") -> Path:
    """Was der Kurator wissen muss, um das hier einzupflegen."""
    zeilen = [
        "---",
        "typ: uebergabe",
        f"von: {agent}",
        "an: kurator",
        f"datum: {date.today().isoformat()}",
        f'frage: "{frage}"',
        f"notizen: {anzahl_notizen}",
        f"atome: {anzahl_atome}",
        "status: offen",
        "---",
        "",
        f"# {frage}",
        "",
        "## Was hier liegt",
        f"- `wissen/` — {anzahl_notizen} Notizen, Format wie die vorhandenen Wissensdateien",
        f"- `atome.jsonl` — {anzahl_atome} belegte Einzelaussagen, je Zeile eine",
        "- `quellen.json` — jede Adresse mit Zeichenzahl und Ausgang",
        "",
        "## Noch zu tun",
        "- Atome einem Thema zuordnen (Feld `thema` ist vorbelegt, Zuordnung steht aus)",
        "- Notizen und Atome in die Vektorsäule einspeisen",
        "- Doppelungen gegen den vorhandenen Bestand prüfen",
        "",
        "## Quellen",
    ]
    for quelle in quellen:
        zeilen.append(f"- [{quelle.get('ausgang','?')}] {quelle.get('titel','')} — {quelle.get('url','')}")
    pfad = ziel / "UEBERGABE.md"
    pfad.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="")
    return pfad


def fall_ablegen(frage: str, quellen: list[dict], notizen: int, atome: int,
                 ziel: Path, agent: str = "deep-researcher") -> None:
    brauchbar = [q for q in quellen if q.get("ausgang") == "verwendet"]
    verworfen = [q for q in quellen if q.get("ausgang") != "verwendet"]
    regel = ""
    if verworfen:
        haeufig = {}
        for quelle in verworfen:
            haeufig[quelle.get("ausgang", "?")] = haeufig.get(quelle.get("ausgang", "?"), 0) + 1
        regel = "Verworfen wegen: " + ", ".join(f"{k} ({v})" for k, v in haeufig.items())
    try:
        gehirn.lernen(
            None, kennung=schluessel(frage)[:20], titel=frage, firma="web",
            url="", ergebnis="recherchiert",
            fall=f"{agent}: {frage}. {len(quellen)} Quellen gesichtet.",
            getan=f"{len(brauchbar)} Quellen verwendet, {notizen} Notizen und "
                  f"{atome} Atome nach {ziel} gelegt.",
            ergebnis_text="; ".join(q.get("url", "") for q in brauchbar[:6]),
            regel=regel,
            stichworte=[agent] + schluessel(frage).split("-")[:4],
        )
    except Exception:
        return