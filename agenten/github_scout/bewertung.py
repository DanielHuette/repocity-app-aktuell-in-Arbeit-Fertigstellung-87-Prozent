"""Ist dieses Repository nachahmungswürdig?

Gewertet wird, was im Namen und in der Beschreibung steht, wie verbreitet es ist
und wie frisch. Sammelseiten und Kurslisten ziehen ab — davon lernt kein Agent.
"""
from __future__ import annotations

from datetime import date

from github import Repo


def bewerten(repo: Repo, regeln: dict) -> Repo:
    text = f"{repo.voller_name} {repo.beschreibung}".lower()
    punkte = 0
    begruendung: list[str] = []

    for wort, gewicht in regeln.get("themenwoerter", {}).items():
        if wort in text:
            punkte += gewicht
            begruendung.append(f"+{gewicht} {wort}")

    for wort, gewicht in regeln.get("abzugswoerter", {}).items():
        if wort in text:
            punkte -= gewicht
            begruendung.append(f"-{gewicht} {wort}")

    for grenze, gewicht in regeln.get("sterne_stufen", []):
        if repo.sterne >= grenze:
            punkte += gewicht
            begruendung.append(f"+{gewicht} ab {grenze} Sternen")

    alter = _alter_in_tagen(repo.aktualisiert)
    if alter is not None:
        if alter <= 7:
            punkte += 4
            begruendung.append("+4 diese Woche bewegt")
        elif alter <= 30:
            punkte += 2
            begruendung.append("+2 diesen Monat bewegt")
        elif alter > 180:
            punkte -= 4
            begruendung.append("-4 ein halbes Jahr still")

    repo.punkte = punkte
    repo.begruendung = begruendung
    return repo


def nachahmenswert(dateien: list[str]) -> list[str]:
    """Dateien, die zeigen, dass hier an Agenten gearbeitet wird."""
    marken = []
    # Mit fuehrendem Schraegstrich, damit "skills/..." genauso trifft wie "src/skills/..."
    kleine = ["/" + d.lower() for d in dateien]
    for marke, was in (
        ("agents.md", "AGENTS.md"), ("claude.md", "CLAUDE.md"),
        (".claude/", ".claude-Ordner"), ("skill.md", "Skill-Dateien"),
        ("/skills/", "skills-Ordner"), ("/agents/", "agents-Ordner"),
        ("/commands/", "commands-Ordner"), ("mcp", "MCP-Anbindung"),
        ("eval", "Auswertung"), ("hooks", "Hooks"),
    ):
        if any(marke in datei for datei in kleine):
            marken.append(was)
    return marken


def _alter_in_tagen(datum: str) -> int | None:
    try:
        return (date.today() - date.fromisoformat(datum)).days
    except (ValueError, TypeError):
        return None