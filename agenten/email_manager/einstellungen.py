"""Einstellungen. Nichts steht fest im Code - alles kommt von aussen herein.

Damit laeuft derselbe Container zu Hause und in jeder Cloud.
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
# Wo der Hub liegt. Fehlt er, laeuft der Manager im Pruefbetrieb und liest die
# Zugangsdaten aus einer lokalen Datei.
def _adresse(roh: str) -> str:
    """Eine Adresse ohne https:// ist keine Adresse - urllib wirft dann
    einen Fehler, der nichts mit dem Netz zu tun hat. Hier wird das
    Schema ergaenzt, statt es jedem abzuverlangen, der die .env pflegt."""
    roh = (roh or "").strip().rstrip("/")
    if roh and "://" not in roh:
        roh = "https://" + roh
    return roh


HUB_URL = _adresse(os.getenv("UNIVERSE_HUB_URL", ""))

# Der Ausweis des Containers. Er berechtigt nur zum Fragen, nicht zum Bekommen -
# herausgegeben wird erst nach Daniels Ja in der RepoCity App.
CONTAINER_SCHLUESSEL = os.getenv("UNIVERSE_CONTAINER_SCHLUESSEL", "")

# So lange wird auf die Freigabe in der App gewartet.
FREIGABE_WARTEN_SEK = int(os.getenv("UNIVERSE_FREIGABE_WARTEN_SEK", "300"))


# --- Ablage ----------------------------------------------------------------
# Muss ausserhalb des Containers liegen, sonst ist sie beim naechsten Start weg.
ZUSTAND = Path(os.getenv("UNIVERSE_ZUSTAND", "/daten"))

# Nur fuer den Pruefbetrieb ohne Hub.
LOKALE_ZUGANGSDATEN = Path(
    os.getenv("UNIVERSE_ZUGANGSDATEN", str(ZUSTAND / "zugangsdaten.json"))
)
LOKALE_EMPFAENGERLISTE = Path(
    os.getenv("UNIVERSE_EMPFAENGERLISTE", str(ZUSTAND / "empfaengerliste.json"))
)


# --- Betrieb ---------------------------------------------------------------
TAKT_SEKUNDEN = int(os.getenv("UNIVERSE_TAKT_SEKUNDEN", "1800"))
MODELL = modellwahl.MODELL
MAX_MAILS_JE_LAUF = int(os.getenv("UNIVERSE_MAX_MAILS_JE_LAUF", "25"))

# Spam-Ordner nach der Meldung leeren.
SPAM_LEEREN = _ja("UNIVERSE_SPAM_LEEREN", "ja")

# Trockenlauf: alles wird getan und gemeldet, nur nicht gesendet und nicht geloescht.
TROCKEN = _ja("UNIVERSE_TROCKEN", "nein")