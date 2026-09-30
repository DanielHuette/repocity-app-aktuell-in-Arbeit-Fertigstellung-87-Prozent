"""Einstellungen der Lern-Werkstatt.

Nachgebaut nach dem Verfahren aus dem Transkript "So erstellst du interaktive
Schulungen mit Claude Code auf Knopfdruck" (Julian Ivanov) — mit einem
Unterschied: die teuren Teile sind abschaltbar und standardmaessig aus.

  Erzaehlerstimme   edge-tts, kostenlos, kein Konto (wie in der Video-Werkstatt)
  Animationen       HyperFrames: HTML rein, MP4 raus, kostenlos
  KI-Videos         nur wenn ausdruecklich eingeschaltet — 5 bis 6 Euro je Clip

Das Ergebnis ist dasselbe: **eine einzige HTML-Datei**, die den ganzen Kurs
enthaelt. Man oeffnet sie, gibt seinen Namen ein und laeuft Level fuer Level
durch. Ohne geloeste Aufgabe geht es nicht weiter.
"""

import os
from pathlib import Path

# Das Modell kennt nur eine Stelle: universe/kern/modellwahl.py. Ueber den
# Pfad geladen, nicht importiert - im Universe tragen mehrere Ordner
# gleichnamige Module, ein normaler Import erwischt das falsche.
import importlib.util as _iu
_mw = _iu.spec_from_file_location(
    "kern_modellwahl", Path(__file__).resolve().parent.parent / "kern" / "modellwahl.py")
modellwahl = _iu.module_from_spec(_mw)
_mw.loader.exec_module(modellwahl)


def _ja(name: str, standard: str) -> bool:
    return os.getenv(name, standard).strip().lower() in ("ja", "1", "true", "yes", "an")


# --- Hub -------------------------------------------------------------------
def _adresse(roh: str) -> str:
    """Eine Adresse ohne https:// ist keine Adresse - urllib wirft dann
    einen Fehler, der nichts mit dem Netz zu tun hat. Hier wird das
    Schema ergaenzt, statt es jedem abzuverlangen, der die .env pflegt."""
    roh = (roh or "").strip().rstrip("/")
    if roh and "://" not in roh:
        roh = "https://" + roh
    return roh


HUB_URL = _adresse(os.getenv("UNIVERSE_HUB_URL", ""))
CONTAINER_SCHLUESSEL = os.getenv("UNIVERSE_CONTAINER_SCHLUESSEL", "")


# --- Ablage ----------------------------------------------------------------
ZUSTAND = Path(os.getenv("UNIVERSE_ZUSTAND", "/daten"))
WERKSTATT = Path(os.getenv("UNIVERSE_LERN_WERKSTATT", str(ZUSTAND / "lern")))
AUSGABE = Path(os.getenv("UNIVERSE_LERN_AUSGABE", str(ZUSTAND / "lern_fertig")))


# --- Betrieb ---------------------------------------------------------------
TAKT_SEKUNDEN = int(os.getenv("UNIVERSE_TAKT_SEKUNDEN", "60"))
TROCKEN = _ja("UNIVERSE_TROCKEN", "ja")

# Nichts wird erzeugt, bevor das Curriculum abgenommen ist. Das ist keine
# Foermlichkeit: danach faengt an, was Geld und Zeit kostet.
CURRICULUM_ABNAHME = _ja("UNIVERSE_LERN_ABNAHME", "ja")


# --- Umfang ----------------------------------------------------------------
LEVEL_STANDARD = int(os.getenv("UNIVERSE_LERN_LEVEL", "5"))
LEVEL_MAX = int(os.getenv("UNIVERSE_LERN_LEVEL_MAX", "12"))
MINUTEN_STANDARD = int(os.getenv("UNIVERSE_LERN_MINUTEN", "25"))
SPRACHE = os.getenv("UNIVERSE_LERN_SPRACHE", "Deutsch")


# --- Erzaehler -------------------------------------------------------------
# edge-tts: Microsofts Stimmen, kein Konto, keine Kosten.
STIMME = os.getenv("UNIVERSE_LERN_STIMME", "de-DE-KatjaNeural")
SPRECHTEMPO = os.getenv("UNIVERSE_LERN_SPRECHTEMPO", "+0%")
STIMME_AN = _ja("UNIVERSE_LERN_STIMME_AN", "ja")


# --- Animationen -----------------------------------------------------------
# HyperFrames: HTML/CSS/JS wird zu MP4. Node und ffmpeg noetig.
HYPERFRAMES_AN = _ja("UNIVERSE_LERN_HYPERFRAMES", "nein")
HYPERFRAMES_BEFEHL = os.getenv("UNIVERSE_LERN_HYPERFRAMES_BEFEHL", "npx hyperframes")

# KI-Videos. Teuer — bleibt aus, bis es jemand einschaltet.
KI_VIDEO_AN = _ja("UNIVERSE_LERN_KI_VIDEO", "nein")
KI_VIDEO_MAX = int(os.getenv("UNIVERSE_LERN_KI_VIDEO_MAX", "0"))


# --- Sprachmodell ----------------------------------------------------------
LLM_BASISURL = os.getenv("UNIVERSE_LLM_BASISURL", "").rstrip("/")
LLM_SCHLUESSEL = os.getenv("UNIVERSE_LLM_SCHLUESSEL", "")
MODELL = modellwahl.MODELL


# --- Aussehen --------------------------------------------------------------
# Der Kurs traegt das Brand Kit. Die Werte kommen aus derselben Quelle wie
# App und Webseite — nicht nachempfunden, uebernommen.
KIT = os.getenv("UNIVERSE_LERN_KIT", "blende")


def fehlende_schluessel() -> list[str]:
    fehlt = []
    if not LLM_BASISURL and not os.getenv("ANTHROPIC_API_KEY"):
        fehlt.append("ANTHROPIC_API_KEY oder UNIVERSE_LLM_BASISURL")
    return fehlt
