"""Den Grundstock der Beobachtungsliste aus der Repo-Prüfung säen.

Daniel hat 1.570 Funde von Hand durchgesehen und 331 mit "ja" bewertet.
Diese Arbeit wird nicht wiederholt — sie wird übernommen.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

PRUEFUNG = Path(r"C:\AI_Projekte\Neustart\repo_pruefung.json")


def gewaehlte_repos(pfad: Path | None = None) -> list[dict]:
    datei = pfad or PRUEFUNG
    if not datei.exists():
        return []
    try:
        daten = json.loads(datei.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    gewaehlt = []
    for eintrag in daten.get("eintraege", []):
        if eintrag.get("urteil") != "ja":
            continue
        github = eintrag.get("github") or {}
        if github.get("status") != "da":
            continue
        gewaehlt.append({
            "voller_name": github.get("name") or eintrag.get("repo", ""),
            "sterne": github.get("sterne") or 0,
            "aktualisiert": (github.get("letzter_push") or "")[:10],
            "beschreibung": (github.get("beschreibung") or "")[:300],
            "sprache": github.get("sprache") or "",
            "kanaele": eintrag.get("kanaele", []),
            "nennungen": eintrag.get("nennungen", 0),
        })
    return gewaehlt


def saeen(liste: dict, pfad: Path | None = None) -> tuple[dict, int]:
    """Trägt die von Hand gewählten Repos ein, ohne Vorhandenes zu überschreiben."""
    neu = 0
    heute = date.today().isoformat()
    for repo in gewaehlte_repos(pfad):
        name = repo["voller_name"]
        if not name or name in liste:
            continue
        liste[name] = {
            "sterne": repo["sterne"],
            "aktualisiert": repo["aktualisiert"],
            "punkte": 0,
            "thema": "von Hand gewählt",
            "herkunft": "repo_pruefung.json (Urteil: ja)",
            "kanaele": repo["kanaele"][:5],
            "nennungen": repo["nennungen"],
            "zuletzt_gesehen": heute,
        }
        neu += 1
    return liste, neu