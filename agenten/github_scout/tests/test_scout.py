"""Selbsttests ohne Netz."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
_TEMP = tempfile.mkdtemp(prefix="scout_test_")
os.environ["SCOUT_DATEN"] = _TEMP

import ablage  # noqa: E402
import beobachtung  # noqa: E402
import bewertung  # noqa: E402
import destillat  # noqa: E402
import einstellungen  # noqa: E402
import ernte  # noqa: E402
from github import Repo  # noqa: E402

KONFIG = einstellungen.laden()
KONFIG["ablage"]["eingang"] = str(Path(_TEMP) / "eingang")
FEHLER: list[str] = []


def pruefe(bedingung, name: str) -> None:
    if bedingung:
        print(f"  ok   {name}")
    else:
        FEHLER.append(name)
        print(f"  FEHL {name}")


def repo(name, beschreibung="", sterne=100, tage_her=3):
    return Repo(voller_name=name, beschreibung=beschreibung, sterne=sterne,
                sprache="Python",
                aktualisiert=(date.today() - timedelta(days=tage_her)).isoformat(),
                url="https://github.com/" + name)


print("Bewertung")
gut = bewertung.bewerten(
    repo("affaan-m/ECC", "Claude Code agent harness with skills, subagents and evals",
         sterne=245912), KONFIG["bewertung"])
pruefe(gut.punkte >= KONFIG["bewertung"]["mindestpunkte"], "Agentenharness kommt durch")

sammel = bewertung.bewerten(
    repo("someone/awesome-ai-tutorial", "awesome- list and course roadmap for interview prep",
         sterne=50000), KONFIG["bewertung"])
pruefe(sammel.punkte < gut.punkte, "Sammelseite liegt hinter echtem Werkzeug")

alt = bewertung.bewerten(
    repo("x/agent-memory", "long term agent memory", sterne=200, tage_her=400),
    KONFIG["bewertung"])
frisch = bewertung.bewerten(
    repo("y/agent-memory", "long term agent memory", sterne=200, tage_her=2),
    KONFIG["bewertung"])
pruefe(frisch.punkte > alt.punkte, "frisch bewegt zählt mehr als lange still")
pruefe(any("still" in g for g in alt.begruendung), "Stillstand wird begründet")

print("Agentenspuren")
spuren = bewertung.nachahmenswert([
    "README.md", "AGENTS.md", ".claude/settings.json", "skills/recherche/SKILL.md",
    "src/main.py", "evals/run.py"])
for erwartet in ("AGENTS.md", ".claude-Ordner", "Skill-Dateien", "skills-Ordner", "Auswertung"):
    pruefe(erwartet in spuren, f"Spur erkannt: {erwartet}")
pruefe(bewertung.nachahmenswert(["README.md", "index.html"]) == [], "keine Spuren, keine Meldung")

print("Dateiauswahl und Aufbau")
dateien = ["README.md", "AGENTS.md", "CLAUDE.md", "src/a.py", "src/b.py", "src/c.py",
           ".claude/settings.json", "skills/eins/SKILL.md", "skills/zwei/SKILL.md",
           "skills/drei/SKILL.md", "docs/x.md"]
gewaehlt = ernte._dateien_waehlen(dateien, KONFIG["ernte"])
pruefe("AGENTS.md" in gewaehlt and "CLAUDE.md" in gewaehlt, "Schlüsseldateien gewählt")
pruefe("README.md" not in gewaehlt, "LIESMICH kommt getrennt, nicht doppelt")
pruefe(len(gewaehlt) <= KONFIG["ernte"].get("hoechstens_dateien", 8),
       "die Zahl der Zusatzdateien bleibt gedeckelt")
baum = ernte._baum_kuerzen(dateien)
pruefe(any(eintrag.startswith("src/") for eintrag in baum), "Aufbau zeigt die Ordner")
pruefe(len(baum) < len(dateien), "Aufbau ist gekürzt")

print("Beobachtungsliste")
liste = {}
erste = [repo("a/eins"), repo("b/zwei")]
for r in erste:
    bewertung.bewerten(r, KONFIG["bewertung"])
unbekannt, bewegt = beobachtung.einordnen(erste, liste)
pruefe(len(unbekannt) == 2 and not bewegt, "beim ersten Mal ist alles neu")
liste = beobachtung.fortschreiben(liste, erste, {"a/eins"})
beobachtung.speichern(liste)
pruefe(beobachtung.laden()["a/eins"]["zuletzt_geerntet"] == date.today().isoformat(),
       "Ernte wird vermerkt")
pruefe("zuletzt_geerntet" not in beobachtung.laden()["b/zwei"], "nicht Geerntetes bleibt offen")

zweite = [repo("a/eins", tage_her=0), repo("b/zwei", tage_her=3), repo("c/drei")]
unbekannt2, bewegt2 = beobachtung.einordnen(zweite, beobachtung.laden())
pruefe([r.voller_name for r in unbekannt2] == ["c/drei"], "nur das wirklich Neue ist neu")
pruefe([r.voller_name for r in bewegt2] == ["a/eins"], "bewegt wird erkannt")

print("Destillat und Ablage")
inhalt = destillat._ohne_modell(
    "Was ist an x/y nachahmenswert für ein Multi-Agenten-System?", "x/y",
    "Das Projekt beschreibt ein Multi-Agenten-System, in dem ein Supervisor die "
    "Aufgaben an spezialisierte Agenten verteilt und die Ergebnisse zusammenführt. "
    "Jeder Agent bekommt seine eigene Wissensbasis und meldet zurück, was er gelernt hat.")
pruefe(inhalt["brauchbar"], "Ausschnitt-Weg findet etwas")
notiz = destillat.notiz_bauen(inhalt, "https://github.com/x/y", "x-y", agent="github-scout")
pruefe("erfasst_von: github-scout" in notiz, "Notiz nennt den Scout als Herkunft")
atome = destillat.atome_bauen(inhalt, "https://github.com/x/y", "x/y", "x-y",
                              agent="github-scout")
pruefe(atome and atome[0]["erfasst_von"] == "github-scout", "Atome nennen den Scout")

ziel = ablage.ordner_anlegen(KONFIG, "github-fund")
ablage.notiz_schreiben(ziel, "x-y", notiz)
ablage.atome_anhaengen(ziel, atome)
quellen = [{"url": "https://github.com/x/y", "titel": "x/y", "ausgang": "verwendet"}]
ablage.quellen_schreiben(ziel, quellen)
ablage.uebergabe_schreiben(ziel, "GitHub-Fund", quellen, 1, len(atome), agent="github-scout")
uebergabe = (ziel / "UEBERGABE.md").read_text(encoding="utf-8")
pruefe("von: github-scout" in uebergabe, "Übergabe nennt den Absender")
pruefe("an: kurator" in uebergabe, "Übergabe geht an den Kurator")
pruefe((ziel / "wissen" / "x-y.md").exists(), "Notiz liegt am richtigen Ort")
zeilen = (ziel / "atome.jsonl").read_text(encoding="utf-8").strip().splitlines()
pruefe(json.loads(zeilen[0])["quelle"] == "https://github.com/x/y", "Atom kennt seine Quelle")

print()
if FEHLER:
    print(f"{len(FEHLER)} Test(s) fehlgeschlagen: " + ", ".join(FEHLER))
    sys.exit(1)
print("alle Tests bestanden")