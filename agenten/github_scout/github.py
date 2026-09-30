"""Zugang zu GitHub.

Ohne Zugangsschlüssel erlaubt GitHub 10 Suchanfragen je Minute und 60 andere
Anfragen je Stunde. Damit lässt sich ein Wochenlauf machen, wenn man haushaltet
— deshalb zählt dieser Baustein mit und wartet, statt gegen die Wand zu laufen.

Ein Schlüssel in GITHUB_TOKEN oder GH_TOKEN hebt die Grenze auf 5.000 je Stunde.
"""
from __future__ import annotations

import os
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
import time
from dataclasses import dataclass

import requests

WURZEL = "https://api.github.com"


@dataclass
class Repo:
    voller_name: str
    beschreibung: str
    sterne: int
    sprache: str
    aktualisiert: str
    url: str
    thema: str = ""
    punkte: int = 0
    begruendung: list[str] = None

    def __post_init__(self):
        if self.begruendung is None:
            self.begruendung = []


def _schluessel() -> str:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    try:
        roh = subprocess.run(["gh", "auth", "token"], capture_output=True,
                             text=True, timeout=10)
        wert = (roh.stdout or "").strip()
        if wert and not wert.startswith("To get started"):
            return wert
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


class GitHub:
    def __init__(self) -> None:
        self.kopf = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "universe-github-scout",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        schluessel = _schluessel()
        self.angemeldet = bool(schluessel)
        if schluessel:
            self.kopf["Authorization"] = "Bearer " + schluessel
        self.rest = {"search": None, "core": None}

    # -------------------------------------------------------------- Grundlage

    def _ruf(self, weg: str, art: str = "core", **kwargs):
        url = weg if weg.startswith("http") else WURZEL + weg
        for versuch in range(3):
            antwort = requests.get(url, headers={**self.kopf, **kwargs.pop("headers", {})},
                                   timeout=30, **kwargs)
            self.rest[art] = _zahl(antwort.headers.get("x-ratelimit-remaining"))
            if antwort.status_code == 403 and self.rest.get(art) == 0:
                warten = _wartezeit(antwort)
                if warten and warten < 130 and versuch < 2:
                    time.sleep(warten + 2)
                    continue
                raise RuntimeError(
                    "GitHub-Grenze erreicht. Ein Zugangsschlüssel in GITHUB_TOKEN "
                    "hebt sie von 60 auf 5.000 Anfragen je Stunde.")
            if antwort.status_code == 404:
                return None
            if antwort.status_code >= 500 and versuch < 2:
                time.sleep(2 * (versuch + 1))
                continue
            antwort.raise_for_status()
            return antwort
        return None

    # ---------------------------------------------------------------- Abrufe

    def suchen(self, frage: str, seit: str, mindeststerne: int, anzahl: int) -> list[Repo]:
        anfrage = f"{frage} pushed:>{seit} stars:>={mindeststerne}"
        antwort = self._ruf("/search/repositories", art="search",
                            params={"q": anfrage, "sort": "stars", "order": "desc",
                                    "per_page": min(anzahl, 50)})
        if antwort is None:
            return []
        gefunden = []
        for eintrag in antwort.json().get("items", []):
            gefunden.append(Repo(
                voller_name=eintrag["full_name"],
                beschreibung=(eintrag.get("description") or "")[:400],
                sterne=eintrag.get("stargazers_count", 0),
                sprache=eintrag.get("language") or "",
                aktualisiert=(eintrag.get("pushed_at") or "")[:10],
                url=eintrag.get("html_url", ""),
                thema=frage,
            ))
        return gefunden

    def liesmich(self, voller_name: str) -> str:
        antwort = self._ruf(f"/repos/{voller_name}/readme",
                            headers={"Accept": "application/vnd.github.raw"})
        return antwort.text if antwort is not None else ""

    def dateibaum(self, voller_name: str, zweig: str = "") -> list[str]:
        if not zweig:
            antwort = self._ruf(f"/repos/{voller_name}")
            if antwort is None:
                return []
            zweig = antwort.json().get("default_branch", "main")
        antwort = self._ruf(f"/repos/{voller_name}/git/trees/{zweig}",
                            params={"recursive": "1"})
        if antwort is None:
            return []
        daten = antwort.json()
        return [eintrag["path"] for eintrag in daten.get("tree", [])
                if eintrag.get("type") == "blob"][:3000]

    def datei(self, voller_name: str, pfad: str) -> str:
        antwort = self._ruf(f"/repos/{voller_name}/contents/{pfad}",
                            headers={"Accept": "application/vnd.github.raw"})
        return antwort.text if antwort is not None else ""


def _zahl(wert) -> int | None:
    try:
        return int(wert)
    except (TypeError, ValueError):
        return None


def _wartezeit(antwort) -> int:
    zuruecksetzen = _zahl(antwort.headers.get("x-ratelimit-reset"))
    if zuruecksetzen:
        return max(0, zuruecksetzen - int(time.time()))
    return _zahl(antwort.headers.get("retry-after")) or 0