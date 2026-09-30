"""Ein Repository abernten: LIESMICH, Dateibaum und die Dateien, die zählen."""
from __future__ import annotations

from bewertung import nachahmenswert
from github import GitHub, Repo


def ernten(zugang: GitHub, repo: Repo, regeln: dict) -> dict:
    """Sammelt den Text, aus dem das Destillat entsteht."""
    liesmich = zugang.liesmich(repo.voller_name)
    dateien = zugang.dateibaum(repo.voller_name)
    marken = nachahmenswert(dateien)

    stuecke = [
        f"# {repo.voller_name}",
        f"{repo.beschreibung}",
        f"Sterne: {repo.sterne} · Sprache: {repo.sprache} · zuletzt bewegt: {repo.aktualisiert}",
        f"Agentenspuren: {', '.join(marken) if marken else 'keine'}",
        "",
        "## LIESMICH",
        liesmich[:20000],
    ]

    for pfad in _dateien_waehlen(dateien, regeln):
        inhalt = zugang.datei(repo.voller_name, pfad)
        if inhalt.strip():
            stuecke += ["", f"## Datei: {pfad}", inhalt[:8000]]

    if dateien:
        stuecke += ["", "## Aufbau",
                    "\n".join(_baum_kuerzen(dateien))]

    text = "\n".join(stuecke)
    return {
        "text": text[:regeln.get("hoechstens_zeichen", 40000)],
        "marken": marken,
        "dateien": len(dateien),
    }


def _dateien_waehlen(dateien: list[str], regeln: dict) -> list[str]:
    """Die Schlüsseldateien und höchstens vier Dateien aus den Agentenordnern."""
    gewaehlt: list[str] = []
    vorhandene = set(dateien)
    for name in regeln.get("schluesseldateien", []):
        if name in vorhandene and name.lower() != "readme.md":
            gewaehlt.append(name)
    zusaetzlich = 0
    for ordner in regeln.get("ordner", []):
        for datei in dateien:
            if f"/{ordner}/" in "/" + datei and datei.endswith((".md", ".json", ".yaml", ".yml")):
                if datei not in gewaehlt:
                    gewaehlt.append(datei)
                    zusaetzlich += 1
            if zusaetzlich >= 4:
                break
        if zusaetzlich >= 4:
            break
    return gewaehlt[:8]


def _baum_kuerzen(dateien: list[str], hoechstens: int = 60) -> list[str]:
    """Nur die oberen Ebenen — der ganze Baum sagt weniger als seine Form."""
    oben: dict[str, int] = {}
    for datei in dateien:
        teile = datei.split("/")
        schluessel = teile[0] + "/" if len(teile) > 1 else teile[0]
        oben[schluessel] = oben.get(schluessel, 0) + 1
    gereiht = sorted(oben.items(), key=lambda paar: -paar[1])[:hoechstens]
    return [f"{pfad} ({anzahl})" if anzahl > 1 else pfad for pfad, anzahl in gereiht]