"""Pfade und Stellschrauben des GitHub Scouts."""
from __future__ import annotations

import json
import os
from pathlib import Path

import umgebung  # liest die .env, damit Schlüssel aus einer Hand kommen

umgebung.laden()

# Das Modell kennt nur eine Stelle: universe/kern/modellwahl.py. Ueber den
# Pfad geladen, nicht importiert - im Universe tragen mehrere Ordner
# gleichnamige Module, ein normaler Import erwischt das falsche.
import importlib.util as _iu
_mw = _iu.spec_from_file_location(
    "kern_modellwahl", Path(__file__).resolve().parent.parent / "kern" / "modellwahl.py")
modellwahl = _iu.module_from_spec(_mw)
_mw.loader.exec_module(modellwahl)

BASIS = Path(os.environ.get("SCOUT_BASIS", Path(__file__).resolve().parent))
DATEN = Path(os.environ.get("SCOUT_DATEN", BASIS / "daten"))
KONFIG_DATEI = BASIS / "konfiguration.json"
BEOBACHTUNG_DATEI = DATEN / "beobachtung.json"

STANDARD: dict = {
    "suche": {
        "themen": [
            "claude code agents skills",
            "multi-agent system framework python",
            "model context protocol mcp server",
            "RAG knowledge base agents",
            "obsidian second brain automation",
            "self-improving agent evaluation harness",
            "agent orchestration langgraph",
            "prompt engineering context engineering",
            "n8n workflow automation ai",
            "agent memory long term"
        ],
        "seit_tagen": 30,
        "mindeststerne": 30,
        "je_thema": 12,
        "hoechstens_ernten": 5
    },
    "bewertung": {
        "themenwoerter": {
            "agent": 6, "agents": 6, "multi-agent": 8, "swarm": 5,
            "claude": 6, "mcp": 6, "skill": 5, "subagent": 6,
            "rag": 6, "vector": 4, "embedding": 4, "memory": 5,
            "obsidian": 6, "second brain": 8, "knowledge": 4,
            "orchestr": 5, "langgraph": 5, "workflow": 3, "n8n": 5,
            "eval": 5, "benchmark": 4, "self-improv": 8, "harness": 5,
            "prompt": 4, "context engineering": 6, "hook": 3
        },
        "abzugswoerter": {
            "awesome-": 4, "tutorial": 3, "course": 4, "roadmap": 4,
            "interview": 5, "leetcode": 8, "wallpaper": 8, "cheatsheet": 3
        },
        "mindestpunkte": 10,
        "sterne_stufen": [[100, 2], [1000, 4], [10000, 6]]
    },
    "ernte": {
        "schluesseldateien": [
            "AGENTS.md", "CLAUDE.md", "AGENT.md", "SKILL.md", "README.md",
            ".claude/settings.json", "docs/architecture.md", "ARCHITECTURE.md"
        ],
        "ordner": [".claude", "skills", "agents", "prompts", "commands"],
        "hoechstens_zeichen": 40000
    },
    "ablage": {
        "eingang": r"C:\AI_Projekte\Neustart\mein_ki_gehirn\eingang\github_scout"
    },
    "modell": {
        "name": modellwahl.MODELL,
        "schluessel_umgebung": "ANTHROPIC_API_KEY"
    },
    "melden": True
}


def _mischen(basis: dict, neu: dict) -> dict:
    ergebnis = dict(basis)
    for schluessel, wert in neu.items():
        if isinstance(wert, dict) and isinstance(ergebnis.get(schluessel), dict):
            ergebnis[schluessel] = _mischen(ergebnis[schluessel], wert)
        else:
            ergebnis[schluessel] = wert
    return ergebnis


def laden() -> dict:
    if KONFIG_DATEI.exists():
        return _mischen(STANDARD, json.loads(KONFIG_DATEI.read_text(encoding="utf-8")))
    return json.loads(json.dumps(STANDARD))


def ordner_anlegen() -> None:
    DATEN.mkdir(parents=True, exist_ok=True)