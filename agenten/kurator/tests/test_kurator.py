"""Selbsttests ohne Netz und ohne Einbettung."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
_TEMP = Path(tempfile.mkdtemp(prefix="kurator_test_"))
os.environ["KURATOR_DATEN"] = str(_TEMP / "daten")

import einstellungen  # noqa: E402
import pruefung  # noqa: E402
from vektor import haeppchen  # noqa: E402

KONFIG = einstellungen.laden()
KONFIG["saeulen"] = {"wissen": str(_TEMP / "wissen"), "atome": str(_TEMP / "atome"),
                     "vektor": str(_TEMP / "chroma"),
                     "verbesserung": str(_TEMP / "verbesserung")}
KONFIG["eingaenge"] = [str(_TEMP / "eingang")]
KONFIG["vektor"]["schreiben"] = False
FEHLER: list[str] = []


def pruefe(bedingung, name: str) -> None:
    if bedingung:
        print(f"  ok   {name}")
    else:
        FEHLER.append(name)
        print(f"  FEHL {name}")


GUT = """---
title: "LangGraph Supervisor"
tags: [agenten, graph]
typ: tech-wissen
thema: langgraph
quellen:
- https://example.org/a
erfasst_von: deep-researcher
---

# LangGraph Supervisor

## Technische Zusammenfassung
""" + ("Ein Supervisor verteilt Aufgaben an spezialisierte Agenten und führt "
       "die Ergebnisse zusammen. " * 12)

print("Kopf lesen")
kopf = pruefung.kopf_lesen(GUT)
pruefe(kopf.get("title") == "LangGraph Supervisor", "Titel aus dem Kopf")
pruefe(kopf.get("erfasst_von") == "deep-researcher", "Herkunft aus dem Kopf")
pruefe(pruefung.kopf_lesen("kein Kopf hier") == {}, "ohne Kopf leeres Ergebnis")

print("Notizen prüfen")
pruefe(pruefung.notiz_pruefen(GUT, KONFIG["pruefung"]).ok, "gute Notiz kommt durch")

ohne_kopf = GUT.split("---", 2)[2]
befund = pruefung.notiz_pruefen(ohne_kopf, KONFIG["pruefung"])
pruefe(not befund.ok and any("Kopf" in g for g in befund.gruende), "ohne Kopf abgelehnt")

duenn = GUT[:GUT.index("# LangGraph")] + "# Titel\n\nZu wenig."
befund = pruefung.notiz_pruefen(duenn, KONFIG["pruefung"])
pruefe(not befund.ok and any("dünn" in g for g in befund.gruende), "zu dünne Notiz abgelehnt")

ohne_feld = GUT.replace("erfasst_von: deep-researcher\n", "")
befund = pruefung.notiz_pruefen(ohne_feld, KONFIG["pruefung"])
pruefe(not befund.ok and any("erfasst_von" in g for g in befund.gruende),
       "fehlendes Pflichtfeld benannt")

print("Atome prüfen")
gutes_atom = {"aussage": "Ein Supervisor verteilt Aufgaben an Unteragenten.",
              "beleg": "Der Supervisor verteilt Aufgaben.", "quelle": "https://example.org/a"}
pruefe(pruefung.atom_pruefen(gutes_atom, KONFIG["pruefung"]).ok, "gutes Atom kommt durch")
pruefe(not pruefung.atom_pruefen({**gutes_atom, "quelle": ""}, KONFIG["pruefung"]).ok,
       "Atom ohne Quelle abgelehnt")
pruefe(not pruefung.atom_pruefen({**gutes_atom, "beleg": ""}, KONFIG["pruefung"]).ok,
       "Atom ohne Beleg abgelehnt")
pruefe(not pruefung.atom_pruefen({**gutes_atom, "aussage": "kurz"}, KONFIG["pruefung"]).ok,
       "zu kurze Aussage abgelehnt")

print("Doppelungen")
(_TEMP / "wissen").mkdir(parents=True, exist_ok=True)
(_TEMP / "wissen" / "vorhanden.md").write_text(GUT, encoding="utf-8", newline="")
(_TEMP / "atome").mkdir(parents=True, exist_ok=True)
(_TEMP / "atome" / "langgraph.jsonl").write_text(
    json.dumps(gutes_atom, ensure_ascii=False) + "\n", encoding="utf-8", newline="")

bestand = pruefung.Bestand(_TEMP / "wissen", _TEMP / "atome")
pruefe(bestand.kennt_notiz(GUT) != "", "gleiche Notiz wird erkannt")
pruefe(bestand.kennt_atom(gutes_atom) != "", "gleiches Atom wird erkannt")
neu = GUT.replace("LangGraph Supervisor", "Etwas ganz anderes").replace(
    "https://example.org/a", "https://example.org/b")
pruefe(bestand.kennt_notiz(neu) == "", "andere Notiz kommt durch")
bestand.merken_notiz(neu)
pruefe(bestand.kennt_notiz(neu) != "", "gemerkte Notiz gilt danach als bekannt")

print("Häppchen")
lang = "Absatz eins.\n\n" + ("Ein Satz mit Inhalt. " * 200)
stuecke = haeppchen(lang, 1800, 250)
pruefe(len(stuecke) > 1, "langer Text wird zerlegt")
pruefe(all(len(s) <= 1900 for s in stuecke), "kein Stück wird zu groß")
pruefe(haeppchen("kurz") == ["kurz"], "kurzer Text bleibt ein Stück")
pruefe(haeppchen("") == [], "leerer Text ergibt nichts")

print()
if FEHLER:
    print(f"{len(FEHLER)} Test(s) fehlgeschlagen: " + ", ".join(FEHLER))
    sys.exit(1)
print("alle Tests bestanden")