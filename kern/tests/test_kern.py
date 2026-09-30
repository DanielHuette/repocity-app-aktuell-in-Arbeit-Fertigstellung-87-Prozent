"""Selbsttests der gemeinsamen Bausteine — ohne Netz."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WURZEL))

from kern.compliance import detect, has_tdm_optout, parse_robots  # noqa: E402
from kern.compliance.tor import Tor  # noqa: E402
from kern.umgebung import einsetzen, offene_platzhalter, zerlegen  # noqa: E402

FEHLER: list[str] = []


def pruefe(bedingung, name: str) -> None:
    if bedingung:
        print(f"  ok   {name}")
    else:
        FEHLER.append(name)
        print(f"  FEHL {name}")


print("robots.txt auswerten")
REGELN = """User-agent: *
Disallow: /*/anzeige:angebote
Disallow: /*/c*r30
Allow: /*.json$
Disallow: /geheim/
Crawl-delay: 5
"""
gruppe = parse_robots(REGELN, "Universe-Agent/1.0")
pruefe(not gruppe.allows("/s-wohnung-mieten/muenster/anzeige:angebote")[0],
       "Platzhalter mitten im Pfad greift")
pruefe(not gruppe.allows("/s-wohnung-mieten/muenster/c203l929r30")[0],
       "Umkreissuffix ist verboten")
pruefe(gruppe.allows("/s-wohnung-mieten/muenster/c203l929")[0],
       "ohne Umkreissuffix erlaubt")
pruefe(gruppe.allows("/daten/liste.json")[0], "Allow mit Endanker gewinnt")
pruefe(not gruppe.allows("/geheim/x")[0], "verbotener Ordner bleibt verboten")
pruefe(gruppe.crawl_delay == 5.0, "Crawl-delay gelesen")

leer = parse_robots("User-agent: *\nDisallow:\n", "Universe-Agent/1.0")
pruefe(leer.allows("/beliebig")[0], "leeres Disallow erlaubt alles")

print("Bot-Schutz erkennen")
pruefe(bool(detect(403, {"server": "cloudflare"}, "")), "403 von Cloudflare erkannt")
pruefe(bool(detect(429, {}, "")), "429 erkannt")
pruefe(bool(detect(200, {}, "<div class='g-recaptcha'>")), "reCAPTCHA im Text erkannt")
pruefe(bool(detect(200, {"cf-mitigated": "challenge"}, "")), "WAF-Kopfzeile erkannt")
pruefe(not detect(200, {}, "<html><body>Ganz normal</body></html>"),
       "normale Seite gilt nicht als geschützt")

print("Widerspruch gegen Text- und Data-Mining")
ja, beleg = has_tdm_optout('<meta name="robots" content="noai, noindex">')
pruefe(ja and "noai" in beleg, "noai im Kopf erkannt")
ja, _ = has_tdm_optout("", {"tdm-reservation": "1"})
pruefe(ja, "TDM-Kopfzeile erkannt")
ja, _ = has_tdm_optout("<html>nichts dergleichen</html>")
pruefe(not ja, "ohne Widerspruch kein Fehlalarm")

print("Tor: Prüfung vor dem Abruf")
tor = Tor(sperrliste=["gesperrt.example"])
pruefe(not tor.darf("file:///C:/geheim.txt").allowed, "Dateipfad wird abgelehnt")
pruefe(not tor.darf("http://localhost:8000/x").allowed, "eigener Rechner wird abgelehnt")
pruefe(not tor.darf("https://www.linkedin.com/jobs").allowed,
       "Sperrliste aus den Nutzungsbedingungen greift")
pruefe(not tor.darf("https://gesperrt.example/x").allowed, "eigene Sperrliste greift")

nur_dort = Tor(erlaubnisliste=["erlaubt.example"])
pruefe(not nur_dort.darf("https://woanders.example/x").allowed,
       "mit Erlaubnisliste bleibt alles andere draußen")

print("Umgebung: .env auswerten")
werte, fehlerhaft, doppelt = zerlegen(
    '\ufeff# Kommentar\nA=1\nexport B = "zwei"\nGithub login: ohne Gleichheitszeichen\n'
    "A=3\nLEER=\n")
pruefe(werte["A"] == "3", "der letzte Eintrag gewinnt")
pruefe("A" in doppelt, "Doppelung wird gemeldet")
pruefe(werte["B"] == "zwei", "Anführungszeichen und export entfernt")
pruefe(len(fehlerhaft) == 1 and fehlerhaft[0][0] == 4, "Zeile ohne Gleichheitszeichen benannt")
pruefe(werte["LEER"] == "", "leerer Wert bleibt leer")

import os  # noqa: E402
os.environ["PROBE_GEHEIM"] = "s3hr-geheim"
gefuellt = einsetzen({"postfaecher": [{"passwort": "${PROBE_GEHEIM}", "port": 993}]})
pruefe(gefuellt["postfaecher"][0]["passwort"] == "s3hr-geheim", "Platzhalter gefüllt")
pruefe(gefuellt["postfaecher"][0]["port"] == 993, "Zahlen bleiben Zahlen")
pruefe(offene_platzhalter(einsetzen({"x": "${GIBTSNICHT}"})) == ["GIBTSNICHT"],
       "fehlender Wert wird benannt")

print("Posteingang und Meldung")
from kern import meldung, posteingang  # noqa: E402

with tempfile.TemporaryDirectory() as ordner:
    meldung.TAGEBUCH = Path(ordner) / "tagebuch.jsonl"
    meldung.ZUSTAND = Path(ordner)
    meldung.melde("probe-agent", "Etwas geschah", art="fund", zusammenfassung="kurz")
    saetze = meldung.offene_meldungen("probe-agent")
    pruefe(len(saetze) == 1 and saetze[0]["art"] == "fund", "Meldung im Tagebuch")
    pruefe(meldung.offene_meldungen("anderer") == [], "nach Absender gefiltert")

    posteingang.DATEI = Path(ordner) / "posteingang.jsonl"
    posteingang.merken("noreply@immobilienscout24.de", "ImmoScout24",
                       "Neue Treffer", "https://www.immobilienscout24.de/expose/12345")
    posteingang.merken("tante@example.org", "Tante", "Hallo", "Text")
    pruefe(len(posteingang.lesen(von_enthaelt=["immobilienscout24"])) == 1,
           "Posteingang nach Absender gefiltert")
    pruefe(len(posteingang.lesen()) == 2, "alle Einträge lesbar")

print()
if FEHLER:
    print(f"{len(FEHLER)} Test(s) fehlgeschlagen: " + ", ".join(FEHLER))
    sys.exit(1)
print("alle Tests bestanden")