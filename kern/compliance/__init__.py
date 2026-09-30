"""Das Tor, durch das jeder Abruf nach draußen geht.

Übernommen aus Indexer_scraper_ingestor (robots.py, policy.py,
bot_detection.py) und um das Tor selbst ergänzt. Die Regel dahinter:
Wo ein Betreiber maschinellen Zugriff erkennbar nicht will, wird nicht
zugegriffen — und schon gar nicht wird eine Sperre umgangen.
"""
from .bot_detection import BotProtectionVerdict, detect, has_tdm_optout
from .policy import CompliancePolicy, PolicyDecision
from .robots import RobotsCache, RobotsDecision, parse_robots
from .tor import Antwort, Tor, TorFehler

__all__ = [
    "Antwort", "Tor", "TorFehler",
    "CompliancePolicy", "PolicyDecision",
    "RobotsCache", "RobotsDecision", "parse_robots",
    "BotProtectionVerdict", "detect", "has_tdm_optout",
]