"""Selbsttests ohne Netz und ohne Modell."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
_TEMP = tempfile.mkdtemp(prefix="recherche_test_")

import ablage  # noqa: E402
import destillat  # noqa: E402
import einstellungen  # noqa: E402
import holen  # noqa: E402
import suche  # noqa: E402

KONFIG = einstellungen.laden()
KONFIG["ablage"]["eingang"] = str(Path(_TEMP) / "eingang")
FEHLER: list[str] = []


def pruefe(bedingung, name: str) -> None:
    if bedingung:
        print(f"  ok   {name}")
    else:
        FEHLER.append(name)
        print(f"  FEHL {name}")


print("Die Bremse vor der Suche")
import os  # noqa: E402
pruefe(suche.SUCHEN_JE_MONAT == 750, "750 Suchen je Monat (1.500 Credits / 2)")

_vorher = os.environ.pop("TAVILY_API_KEY", None)
_schalter_echt = suche._schalter
_stand_echt = suche.stand
try:
    # Erstes Tor: der Schalter. Steht er aus, kommt niemand weiter - auch
    # nicht mit Schlüssel und leerem Kontingent.
    os.environ["TAVILY_API_KEY"] = "nur-fuer-den-test"
    suche._schalter = lambda: {"an": False, "ueberKontingent": False, "grund": ""}
    try:
        suche.suchen("beliebig", 3, [])
        pruefe(False, "bei ausgeschaltetem Schalter wird nicht gesucht")
    except suche.SucheGesperrt as _grund:
        pruefe("steht aus" in str(_grund), "bei ausgeschaltetem Schalter wird nicht gesucht")

    # Ab hier steht der Schalter an, damit die Tore dahinter prüfbar sind.
    suche._schalter = lambda: {"an": True, "ueberKontingent": False, "grund": ""}

    os.environ.pop("TAVILY_API_KEY", None)
    try:
        suche.suchen("beliebig", 3, [])
        pruefe(False, "ohne Schlüssel wird nicht gesucht")
    except suche.SucheGesperrt as _grund:
        pruefe("TAVILY_API_KEY" in str(_grund), "ohne Schlüssel wird nicht gesucht")

    os.environ["TAVILY_API_KEY"] = "nur-fuer-den-test"
    suche.stand = lambda: {"suchen_je_monat": 750, "verbraucht": 750,
                           "frei": 0, "credits_gebucht": 1500}
    try:
        suche.suchen("beliebig", 3, [])
        pruefe(False, "bei vollem Kontingent wird nicht gesucht")
    except suche.SucheGesperrt as _grund:
        pruefe("aufgebraucht" in str(_grund), "bei vollem Kontingent wird nicht gesucht")

    # Zweiter Schalter: erlaubt er das Weitersuchen, hält das Kontingent nicht
    # mehr auf - dann scheitert es erst am Netz, nicht mehr an der Grenze.
    suche._schalter = lambda: {"an": True, "ueberKontingent": True, "grund": ""}
    try:
        suche.suchen("beliebig", 3, [])
        pruefe(False, "mit Erlaubnis geht es über das Kontingent hinaus")
    except suche.SucheGesperrt as _grund:
        pruefe("aufgebraucht" not in str(_grund),
               "mit Erlaubnis geht es über das Kontingent hinaus")
finally:
    suche._schalter = _schalter_echt
    suche.stand = _stand_echt
    os.environ.pop("TAVILY_API_KEY", None)
    if _vorher is not None:
        os.environ["TAVILY_API_KEY"] = _vorher

print("Haupttext herausschälen")
html = """<html><head><title>Testseite</title></head><body>
<nav>Menü Start Kontakt Impressum</nav>
<script>var x = 1;</script>
<article><h1>LangGraph</h1>
<p>LangGraph ist ein Rahmenwerk fuer zustandsbehaftete Agenten mit Graphen.
Ein Supervisor verteilt Aufgaben an spezialisierte Agenten und sammelt Ergebnisse ein.</p>
<p>Der Zustand wird zwischen den Knoten weitergereicht und laesst sich pruefen.</p>
</article><footer>Copyright</footer></body></html>"""
text = holen._herausschaelen(html)
pruefe("Supervisor" in text, "Haupttext gefunden")
pruefe("var x" not in text and "Impressum" not in text, "Beiwerk entfernt")
pruefe(holen.titel_holen(html, "-") == "Testseite", "Titel gelesen")

print("Destillat ohne Modell")
roh = ("LangGraph ist ein Rahmenwerk fuer Agenten mit Zustand und Graphen, das "
       "Ablaeufe nachvollziehbar macht. " * 3 +
       "Ein Supervisor verteilt Aufgaben an spezialisierte Agenten und fuehrt die "
       "Ergebnisse wieder zusammen, was die Architektur uebersichtlich haelt.")
inhalt = destillat._ohne_modell("LangGraph Supervisor Architektur", "Testquelle", roh)
pruefe(inhalt["brauchbar"], "Ausschnitt-Weg findet etwas")
pruefe(inhalt["weg"] == "ausschnitt", "Weg vermerkt")
pruefe(all(a["sicherheit"] == "roh" for a in inhalt["atome"]),
       "ungeprüfte Atome sind als roh gekennzeichnet")

print("Notiz und Atome")
notiz = destillat.notiz_bauen(
    {"titel": "LangGraph", "tags": ["agenten", "graph"],
     "zusammenfassung": "Ein Rahmenwerk.", "kernkonzepte": ["Zustand"],
     "werkzeuge": ["LangGraph"], "code": "pip install langgraph"},
    "https://example.org/a", "langgraph")
for marke in ("title:", "tags: [agenten, graph]", "thema: langgraph",
              "erfasst_von: deep-researcher", "## Kernkonzepte & Logik"):
    pruefe(marke in notiz, f"Notiz enthält {marke}")

atome = destillat.atome_bauen(
    {"atome": [
        {"aussage": "Ein Supervisor verteilt Aufgaben an Unteragenten.",
         "beleg": "Der Supervisor verteilt Aufgaben.", "stichworte": ["supervisor"],
         "sicherheit": "hoch"},
        {"aussage": "zu kurz", "beleg": "x"},
    ]}, "https://example.org/a", "Testquelle", "langgraph")
pruefe(len(atome) == 1, "zu kurze Aussagen fallen weg")
pruefe(atome[0]["quelle"] == "https://example.org/a", "Quelle am Atom")
pruefe(atome[0]["thema"] == "langgraph", "Thema am Atom")
pruefe("erfasst_am" in atome[0] and atome[0]["erfasst_von"] == "deep-researcher",
       "Herkunft am Atom")

print("Ablage")
ziel = ablage.ordner_anlegen(KONFIG, "LangGraph Supervisor Muster")
pruefe(ziel.exists(), "Eingangsordner angelegt")
pruefe("langgraph-supervisor-muster" in ziel.name, "Ordnername aus der Frage")
ablage.notiz_schreiben(ziel, "LangGraph Übersicht", notiz)
pruefe((ziel / "wissen" / "langgraph-uebersicht.md").exists(), "Notiz abgelegt")
ablage.atome_anhaengen(ziel, atome)
ablage.atome_anhaengen(ziel, atome)
zeilen = (ziel / "atome.jsonl").read_text(encoding="utf-8").strip().splitlines()
pruefe(len(zeilen) == 2, "Atome werden angehängt, nicht überschrieben")
pruefe(json.loads(zeilen[0])["aussage"].startswith("Ein Supervisor"), "Atomzeile lesbar")

quellen = [{"url": "https://example.org/a", "titel": "A", "ausgang": "verwendet"},
           {"url": "https://example.org/b", "titel": "B", "ausgang": "zu wenig Text"}]
ablage.quellen_schreiben(ziel, quellen)
ablage.uebergabe_schreiben(ziel, "LangGraph Supervisor Muster", quellen, 1, 2)
uebergabe = (ziel / "UEBERGABE.md").read_text(encoding="utf-8")
pruefe("an: kurator" in uebergabe, "Übergabe nennt den Empfänger")
pruefe("Atome einem Thema zuordnen" in uebergabe, "offener Punkt steht drin")
pruefe("https://example.org/b" in uebergabe, "auch verworfene Quellen sind aufgeführt")

print("Sperrliste und Dopplungen")
roh_treffer = [
    suche.Treffer("A", "https://gut.example.org/a"),
    suche.Treffer("A nochmal", "https://gut.example.org/a/?utm=1"),
    suche.Treffer("Bild", "https://pinterest.de/pin/1"),
    suche.Treffer("kaputt", "javascript:void(0)"),
    suche.Treffer("B", "https://gut.example.org/b"),
]
sauber = suche.filtern(roh_treffer, KONFIG["suche"]["sperrliste"], 10)
pruefe(len(sauber) == 2, "Dopplung, Sperrliste und Nicht-Adresse fallen weg")
pruefe([t.url for t in sauber] == ["https://gut.example.org/a", "https://gut.example.org/b"],
       "Reihenfolge bleibt erhalten")
pruefe(len(suche.filtern(roh_treffer, [], 1)) == 3, "Obergrenze greift")

print()
if FEHLER:
    print(f"{len(FEHLER)} Test(s) fehlgeschlagen: " + ", ".join(FEHLER))
    sys.exit(1)
print("alle Tests bestanden")