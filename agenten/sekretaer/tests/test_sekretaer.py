"""Selbsttests ohne Netz."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
_TEMP = Path(tempfile.mkdtemp(prefix="sekretaer_test_"))
os.environ["UNIVERSE_ZUSTAND"] = str(_TEMP / "zustand")

import einstellungen as e  # noqa: E402

(_TEMP / "zustand").mkdir(parents=True, exist_ok=True)
e.ZUSTAND = _TEMP / "zustand"
e.VORLAGE_DATEI = e.ZUSTAND / "vorlage.json"
e.QUITTIERT_DATEI = e.ZUSTAND / "quittiert.json"

import sammeln  # noqa: E402

sammeln.e = e
FEHLER: list[str] = []


def pruefe(bedingung, name: str) -> None:
    if bedingung:
        print(f"  ok   {name}")
    else:
        FEHLER.append(name)
        print(f"  FEHL {name}")


heute = date.today()
vorgestern = (heute - timedelta(days=2)).isoformat()
lange_her = (heute - timedelta(days=30)).isoformat()

KONFIG = e.laden()
KONFIG["quellen"]["bewerbungen"] = str(_TEMP / "bewerbungen.json")
KONFIG["quellen"]["wohnungen"] = str(_TEMP / "angebote.json")
KONFIG["quellen"]["eingaenge"] = [str(_TEMP / "eingang")]

print("Freigaben aus dem Postausgang")
(e.ZUSTAND / "postausgang.jsonl").write_text("\n".join([
    json.dumps({"absender_agent": "wohnungs-agent", "an": "a@b.de",
                "betreff": "Anfrage", "zustand": "trocken", "vorgang": "w1",
                "angelegt_am": heute.isoformat()}),
    json.dumps({"absender_agent": "wohnungs-agent", "an": "c@d.de",
                "betreff": "Zweite", "zustand": "gesendet", "vorgang": "w2",
                "angelegt_am": heute.isoformat()}),
]) + "\n", encoding="utf-8", newline="")
offen = sammeln.freigaben(KONFIG)
pruefe(len(offen) == 1 and offen[0]["vorgang"] == "w1",
       "nur was nicht raus ist, wartet auf ein Ja")

print("Fristen")
(_TEMP / "bewerbungen.json").write_text(json.dumps([
    {"kennung": "b1", "firma": "Beispiel", "titel": "AI Engineer", "stand": "beworben",
     "verlauf": [{"stand": "beworben", "am": lange_her}]},
    {"kennung": "b2", "firma": "Frisch", "titel": "AI Engineer", "stand": "beworben",
     "verlauf": [{"stand": "beworben", "am": heute.isoformat()}]},
    {"kennung": "b3", "firma": "Abgesagt", "titel": "x", "stand": "absage",
     "verlauf": [{"stand": "absage", "am": lange_her}]},
]), encoding="utf-8", newline="")
(_TEMP / "angebote.json").write_text(json.dumps([
    {"kennung": "n1", "titel": "2 ZKB", "status": "angefragt", "angefragt_am": lange_her},
    {"kennung": "n2", "titel": "3 ZKB", "status": "angefragt", "angefragt_am": heute.isoformat()},
    {"kennung": "n3", "titel": "1 ZKB", "status": "passt", "angefragt_am": ""},
]), encoding="utf-8", newline="")
(_TEMP / "eingang" / f"{vorgestern}_alt").mkdir(parents=True, exist_ok=True)
(_TEMP / "eingang" / f"{heute.isoformat()}_neu").mkdir(parents=True, exist_ok=True)

faellig = sammeln.fristen(KONFIG)
vorgaenge = {f["vorgang"] for f in faellig}
pruefe("b1" in vorgaenge, "alte Bewerbung ist fällig")
pruefe("b2" not in vorgaenge, "frische Bewerbung ist nicht fällig")
pruefe("b3" not in vorgaenge, "abgesagte Bewerbung taucht nicht auf")
pruefe("n1" in vorgaenge, "alte Wohnungsanfrage ist fällig")
pruefe("n2" not in vorgaenge, "frische Wohnungsanfrage ist nicht fällig")
pruefe("n3" not in vorgaenge, "nicht angefragtes Angebot taucht nicht auf")
pruefe(any(f["vorgang"].endswith("_alt") for f in faellig), "liegengebliebener Eingang gemahnt")
pruefe(not any(f["vorgang"].endswith("_neu") for f in faellig), "frischer Eingang nicht gemahnt")

print("Störungen und abgelehnte Abrufe")
jetzt = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
saetze = [{"absender": "email-agent", "art": "stoerung", "text": "Postfach weg",
           "gesendet_am": jetzt},
          {"absender": "kurator", "art": "wissen", "text": "eingepflegt",
           "gesendet_am": jetzt}]
pruefe(len(sammeln.stoerungen(saetze)) == 1, "nur Störungen werden herausgezogen")

(e.ZUSTAND / "abgelehnt.jsonl").write_text("\n".join([
    json.dumps({"url": "https://x/1", "stufe": "robots", "grund": "Disallow", "am": jetzt}),
    json.dumps({"url": "https://x/2", "stufe": "botschutz", "grund": "cloudflare", "am": jetzt}),
]) + "\n", encoding="utf-8", newline="")
pruefe(len(sammeln.abgelehnte_abrufe()) == 2, "abgelehnte Abrufe werden gelesen")

print()
if FEHLER:
    print(f"{len(FEHLER)} Test(s) fehlgeschlagen: " + ", ".join(FEHLER))
    sys.exit(1)
print("alle Tests bestanden")