# -*- coding: utf-8 -*-
"""Der Zugangswaechter - er sieht nach, BEVOR etwas Geld kostet.

Ein Auftrag, der mittendrin abbricht, weil eine Anmeldung abgelaufen ist,
hat schon bezahlt: das Modell hat gedacht, die Bilder sind gerechnet, und
der Nutzer hat nichts in der Hand. Genau das soll hier nicht passieren.

    waechter.pruefen("video", nutzer)  ->  Befund

Der Befund sagt drei Dinge:

    laeuft         kann der Auftrag los
    fehlt          welche Zugaenge gebraucht werden und nicht da sind
    unsicher       welche da sind, aber noch nie getragen haben

Woher er weiss, was eine Strasse braucht: aus ``universe/dienste.json``,
Abschnitt ``strassen`` - dort steht je Strasse, welcher Zugang noetig ist
und welcher sie nur besser macht. Die Zuordnung ist am 09.09. aus dem Code
erhoben worden, nicht geschaetzt.

Woher er weiss, ob ein Zugang da ist: aus dem Tresor des Nutzers
(``kern/tresor.py``). Was RepoCity selbst mitbringt - das Modell, die
Bildquellen -, steht in der Umgebung dieses Rechners; dafuer wird dort
nachgesehen.

**Was hier NICHT passiert: sich anmelden.** Der Waechter probiert keine
Passwoerter aus und ruft keinen fremden Dienst. Er sieht nach, was
hinterlegt ist und was zuletzt getragen hat. Ob ein Zugang wirklich
traegt, weiss nur der, der ihn benutzt hat - darum meldet der Agent es
zurueck (``tresor.befund``), und der Waechter liest das.

Aufruf von Hand:
    python universe/kern/zugangswaechter.py video anna@beispiel.de
    python universe/kern/zugangswaechter.py --alle anna@beispiel.de
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
if str(HIER) not in sys.path:
    sys.path.insert(0, str(HIER))

import tresor  # noqa: E402

DIENSTE = UNIVERSE / "dienste.json"

#: Welcher Zugang aus welchem Umgebungswert kommt, wenn RepoCity ihn selbst
#: mitbringt. Steht der Wert da, gilt der Dienst als vorhanden - fuer alle
#: Nutzer, denn es ist der Zugang des Betreibers.
VOM_BETREIBER = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "fal": "FAL_KEY",
    "pexels": "PEXELS_API_KEY",
    "github": "GITHUB_TOKEN",
    "cloudflare": "CLOUFLARE_BENUTZER",
}


@dataclass
class Befund:
    strasse: str
    nutzer: str
    fehlt: list = field(default_factory=list)
    unsicher: list = field(default_factory=list)
    abgelehnt: list = field(default_factory=list)
    #: Zugaenge, die nur die Qualitaet verbessern und nicht da sind.
    schade: list = field(default_factory=list)

    @property
    def laeuft(self) -> bool:
        """Darf der Auftrag los? Nur wenn nichts Notwendiges fehlt."""
        return not self.fehlt and not self.abgelehnt

    def satz(self) -> str:
        """Ein Satz in Alltagssprache - genau das, was die App anzeigt."""
        if self.abgelehnt:
            return ("Diese Zugaenge haben zuletzt nicht funktioniert: %s. "
                    "Trag sie neu ein, sonst bricht der Auftrag mittendrin ab."
                    % ", ".join(self.abgelehnt))
        if self.fehlt:
            return ("Dafuer fehlt: %s. Ohne das kann der Auftrag nicht laufen."
                    % ", ".join(self.fehlt))
        if self.unsicher:
            return ("Es ist alles hinterlegt, aber %s hat noch nie "
                    "gearbeitet. Wenn es hakt, liegt es wahrscheinlich daran."
                    % ", ".join(self.unsicher))
        if self.schade:
            return ("Laeuft. Ohne %s faellt das Ergebnis allerdings "
                    "einfacher aus, als es koennte." % ", ".join(self.schade))
        return "Alles da."


def _liste() -> dict:
    return json.loads(DIENSTE.read_text(encoding="utf-8"))


def _name(daten: dict, kennung: str) -> str:
    for d in daten.get("dienste", []):
        if d["kennung"] == kennung:
            return d.get("name", kennung)
    return kennung


def strassen() -> dict:
    """Was jede Strasse braucht - aus der einen Quelle."""
    return _liste().get("strassen", {})


def pruefen(strasse: str, nutzer: str = "") -> Befund:
    """Nachsehen, ob diese Strasse fuer diesen Nutzer loslaufen kann."""
    daten = _liste()
    plan = daten.get("strassen", {}).get(strasse)
    b = Befund(strasse=strasse, nutzer=nutzer)
    if plan is None:
        # Eine Strasse ohne Eintrag ist kein Freibrief: dann weiss niemand,
        # was sie braucht, und das ist selbst ein Befund.
        b.fehlt.append("die Zuordnung dieser Strasse in dienste.json")
        return b

    stand = {e.get("dienst"): e.get("geprueft", "unbekannt")
             for e in (tresor.was_liegt_da(nutzer) if nutzer else [])}

    def da(kennung: str) -> str:
        """'ja', 'nein' oder der Befund des letzten Laufs."""
        umgebung = VOM_BETREIBER.get(kennung)
        if umgebung and (os.environ.get(umgebung) or "").strip():
            return "in Ordnung"          # der Betreiber bringt ihn mit
        if kennung in stand:
            return stand[kennung]
        return "nein"

    for kennung in plan.get("braucht", []):
        zustand = da(kennung)
        if zustand == "nein":
            b.fehlt.append(_name(daten, kennung))
        elif zustand == "abgelehnt":
            b.abgelehnt.append(_name(daten, kennung))
        elif zustand == "unbekannt":
            b.unsicher.append(_name(daten, kennung))

    for kennung in plan.get("kann_nutzen", []):
        if da(kennung) in ("nein", "abgelehnt"):
            b.schade.append(_name(daten, kennung))

    return b


def alle(nutzer: str = "") -> dict:
    """Der Durchgang ueber alle Strassen - fuer den taeglichen Check."""
    return {name: pruefen(name, nutzer) for name in strassen()}


def _main(argumente: list[str]) -> int:
    try:
        import umgebung
        umgebung.laden()
    except Exception:                                   # noqa: BLE001
        pass

    if argumente and argumente[0] == "--alle":
        nutzer = argumente[1] if len(argumente) > 1 else ""
        for name, b in alle(nutzer).items():
            print("%-16s %-6s %s" % (name, "laeuft" if b.laeuft else "haelt",
                                     b.satz()))
        return 0
    if argumente:
        b = pruefen(argumente[0], argumente[1] if len(argumente) > 1 else "")
        print(b.satz())
        return 0 if b.laeuft else 1
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
