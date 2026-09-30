"""Ein Abruf nach draußen, mit allen Prüfungen davor und danach.

Vorher:  Schema, private Adressen, Sperrliste, Erlaubnisliste, robots.txt
Danach:  Bot-Schutz erkannt? Widerspruch gegen Text- und Data-Mining gesetzt?

Wird etwas davon gefunden, gibt es keinen Inhalt, sondern einen Grund. Der
Grund wird mitgeschrieben, damit später nachvollziehbar ist, warum eine
Quelle fehlt. Eine stille Sperre wäre schlimmer als gar keine.

Warum nicht umgehen: Das Aushebeln einer technischen Zugangssperre kann
unerlaubter Zugriff nach § 202a StGB sein und nimmt der Kopie die
Schranke aus Artikel 4 der DSM-Richtlinie, die sie sonst erlaubt.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from .bot_detection import detect, has_tdm_optout
from .policy import CompliancePolicy

EHRLICH = ("Universe-Agent/1.0 (+https://github.com/DanielHuette; privates Vorhaben; "
           "Kontakt dhuette@gmx.net)")
BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")


class TorFehler(Exception):
    """Der Abruf wurde abgelehnt. Der Text nennt die Stufe und den Grund."""

    def __init__(self, stufe: str, grund: str, url: str) -> None:
        super().__init__(f"{stufe}: {grund}")
        self.stufe = stufe
        self.grund = grund
        self.url = url


@dataclass
class Antwort:
    url: str
    status: int
    text: str
    kopf: dict
    gewartet: float = 0.0


@dataclass
class Tor:
    """Ein Tor je Agent. Es merkt sich robots.txt und den Takt je Gastgeber."""

    kennung: str = EHRLICH
    robots_beachten: bool = True
    grundtakt: float = 2.0
    bei_botschutz_abbrechen: bool = True
    tdm_widerspruch_beachten: bool = True
    zeitlimit: float = 25.0
    sperrliste: list[str] = field(default_factory=list)
    erlaubnisliste: list[str] = field(default_factory=list)
    tagebuch: Path | None = None

    def __post_init__(self) -> None:
        self._regel = CompliancePolicy(
            user_agent=self.kennung,
            respect_robots=self.robots_beachten,
            default_delay=self.grundtakt,
            denylist=self.sperrliste,
            allowlist=self.erlaubnisliste,
            timeout=self.zeitlimit,
        )
        self.abgelehnt: list[dict] = []

    # ------------------------------------------------------------- prüfen

    def darf(self, url: str):
        """Nur die Prüfung vor dem Abruf. Gibt die Entscheidung zurück."""
        return self._regel.check(url)

    # ------------------------------------------------------------- holen

    def holen(self, url: str, **kwargs) -> Antwort:
        entscheidung = self._regel.check(url)
        if not entscheidung.allowed:
            self._merken(url, entscheidung.stage, entscheidung.reason)
            raise TorFehler(entscheidung.stage, entscheidung.reason, url)

        gewartet = self._regel.wait(url, entscheidung.crawl_delay or self.grundtakt)

        kopf = {"User-Agent": self.kennung,
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"}
        kopf.update(kwargs.pop("headers", {}))
        antwort = requests.get(url, headers=kopf, timeout=self.zeitlimit, **kwargs)
        text = antwort.text if "text" in antwort.headers.get("Content-Type", "text") else ""

        schutz = detect(antwort.status_code, dict(antwort.headers), text)
        if schutz and self.bei_botschutz_abbrechen:
            self._merken(url, "botschutz", f"{schutz.kind}: {schutz.evidence}")
            raise TorFehler("botschutz", f"{schutz.kind} — {schutz.evidence}", url)

        if self.tdm_widerspruch_beachten:
            widerspruch, beleg = has_tdm_optout(text, dict(antwort.headers))
            if widerspruch:
                self._merken(url, "tdm-widerspruch", beleg)
                raise TorFehler("tdm-widerspruch", beleg, url)

        return Antwort(url=url, status=antwort.status_code, text=text,
                       kopf=dict(antwort.headers), gewartet=gewartet)

    def versuchen(self, url: str, **kwargs) -> tuple[Antwort | None, str]:
        """Wie holen, gibt aber (None, Grund) zurück statt zu werfen."""
        try:
            return self.holen(url, **kwargs), ""
        except TorFehler as fehler:
            return None, f"{fehler.stufe}: {fehler.grund}"
        except requests.RequestException as fehler:
            return None, f"netz: {fehler}"

    # ------------------------------------------------------------ merken

    def _merken(self, url: str, stufe: str, grund: str) -> None:
        satz = {"url": url, "stufe": stufe, "grund": grund,
                "am": time.strftime("%Y-%m-%dT%H:%M:%S")}
        self.abgelehnt.append(satz)
        if self.tagebuch:
            try:
                import json
                self.tagebuch.parent.mkdir(parents=True, exist_ok=True)
                with self.tagebuch.open("a", encoding="utf-8") as datei:
                    datei.write(json.dumps(satz, ensure_ascii=False) + "\n")
            except OSError:
                pass

    def bericht(self) -> str:
        if not self.abgelehnt:
            return "Nichts abgelehnt."
        nach_stufe: dict[str, int] = {}
        for satz in self.abgelehnt:
            nach_stufe[satz["stufe"]] = nach_stufe.get(satz["stufe"], 0) + 1
        return "Abgelehnt: " + ", ".join(f"{anzahl}× {stufe}"
                                         for stufe, anzahl in sorted(nach_stufe.items()))