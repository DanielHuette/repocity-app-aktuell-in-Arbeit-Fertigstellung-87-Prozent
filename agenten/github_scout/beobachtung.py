"""Die Beobachtungsliste: was schon gesehen wurde und was sich seither bewegt hat."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from einstellungen import BEOBACHTUNG_DATEI
from github import Repo


def laden() -> dict:
    if not Path(BEOBACHTUNG_DATEI).exists():
        return {}
    try:
        return json.loads(Path(BEOBACHTUNG_DATEI).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def speichern(liste: dict) -> None:
    Path(BEOBACHTUNG_DATEI).parent.mkdir(parents=True, exist_ok=True)
    Path(BEOBACHTUNG_DATEI).write_text(
        json.dumps(liste, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8", newline="")


def einordnen(repos: list[Repo], liste: dict) -> tuple[list[Repo], list[Repo]]:
    """Trennt in unbekannt und bewegt-seit-dem-letzten-Mal."""
    unbekannt: list[Repo] = []
    bewegt: list[Repo] = []
    for repo in repos:
        alt = liste.get(repo.voller_name)
        if alt is None:
            unbekannt.append(repo)
        elif repo.aktualisiert > alt.get("aktualisiert", ""):
            bewegt.append(repo)
    return unbekannt, bewegt


def fortschreiben(liste: dict, repos: list[Repo], geerntet: set[str]) -> dict:
    heute = date.today().isoformat()
    for repo in repos:
        eintrag = liste.get(repo.voller_name, {})
        eintrag.update({
            "sterne": repo.sterne,
            "aktualisiert": repo.aktualisiert,
            "punkte": repo.punkte,
            "thema": repo.thema,
            "zuletzt_gesehen": heute,
        })
        if repo.voller_name in geerntet:
            eintrag["zuletzt_geerntet"] = heute
        liste[repo.voller_name] = eintrag
    return liste