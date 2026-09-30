"""Der Takt - woran man Stillstand von Ruhe unterscheidet.

Ein Controller, der nur Geld zaehlt, meldet am Monatsende "0,00 EUR
verbraucht". Das kann heissen, dass alles sparsam lief - oder dass seit
drei Wochen nichts mehr laeuft und es niemand gemerkt hat. Das Teuerste
in einem unbeaufsichtigten System ist nicht der teure Lauf, sondern der
Prozess, der still stehengeblieben ist.

Darum lernt der Controller je Kostenstelle, in welchem Abstand sie sich
normalerweise meldet, und schlaegt Alarm, wenn dieser Abstand deutlich
ueberschritten wird.

Gelernt wird aus dem Tagebuch, in dem jeder Agent seine Meldungen
hinterlaesst. Erst ab einer Woche Beobachtung und drei Meldungen wird
ueberhaupt ein Takt festgelegt - vorher gilt "noch unbekannt", und das ist
ehrlicher als eine Zahl aus zwei Datenpunkten.

Ein Befund, der das noetig macht: Die Absender im Tagebuch heissen
video_agent, prod.video.clip, wohnungs-agent, github-scout - mal der
Agent, mal das Modul, mal mit Bindestrich, mal mit Unterstrich. Wer
danach gruppiert, zaehlt falsch. _kostenstelle() raeumt das auf.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path

UNIVERSE = Path(__file__).resolve().parent.parent
TAGEBUCH = UNIVERSE / "zustand" / "tagebuch.jsonl"

#: Erst ab so vielen Tagen Beobachtung wird ein Takt festgelegt.
MINDESTBEOBACHTUNG_TAGE = 7
#: Und erst ab so vielen Meldungen.
MINDESTMELDUNGEN = 3
#: Ab diesem Vielfachen des ueblichen Abstands gilt eine Stelle als still.
STILL_AB = 2.5

#: ALTLAST. Seit dem 05.09.2026 meldet jeder Agent unter seiner
#: Modul-Kennung (siehe <agent>/meldung.py, Konstante MODUL). Diese Liste
#: uebersetzt nur noch, was VOR der Umstellung ins Tagebuch geschrieben
#: wurde - sonst zaehlte dieselbe Stelle zweimal, einmal als "video_agent"
#: und einmal als "prod.video.clip".
#:
#: Neue Eintraege gehoeren hier NICHT hinein. Wer eine Kennung ergaenzen
#: will, setzt sie in der meldung.py des Agenten.
ALIAS = {
    "video_agent": "prod.video.clip",
    "video-agent": "prod.video.clip",
    "musik_agent": "prod.musik",
    "lern_agent": "prod.lernen",
    "social_media_manager": "prod.social",
    "social-media-manager": "prod.social",
    "marketing": "prod.marketing",
    "gestalter": "prod.praesentation",
    "implementierer": "prod.app",
    "architekt": "prod.app",
    "github_scout": "wissen.scout",
    "github-scout": "wissen.scout",
    "deep_researcher": "wissen.research",
    "deep-researcher": "wissen.research",
    "kurator": "wissen.kurator",
    "ausbilder": "ausbildung",
    "qualitaetsmanager": "system.qm",
    "sicherheitsbeauftragter": "system.sicherheit",
    "admin_master": "system.kosten",
    "kostenstellenverantwortlicher": "system.kosten",
    "email_manager": "post",
    "email-manager": "post",
    "bewerbungsagent": "bewerbung",
    "bewerbungs-agent": "bewerbung",
    "bewerbungs_agent": "bewerbung",
    "wohnungssucher": "wohnung",
    "wohnungs-agent": "wohnung",
    "wohnungs_agent": "wohnung",
    "sekretaer": "kalender",
    "webseiten_betreuer": "webseite",
    "sk_trading_agent": "trading",
}


def _kostenstelle(absender: str) -> str:
    """Aus einem Absender die Modul-Kennung machen."""
    name = (absender or "").strip()
    if not name:
        return "unbekannt"
    if "." in name:        # heisst schon wie ein Modul
        return name
    schluessel = name.lower().replace(" ", "_")
    if schluessel in ALIAS:
        return ALIAS[schluessel]
    return ALIAS.get(schluessel.replace("-", "_"), name)


def meldungen() -> dict[str, list[datetime]]:
    """Wann sich welche Kostenstelle gemeldet hat."""
    aus: dict[str, list[datetime]] = {}
    if not TAGEBUCH.exists():
        return aus
    try:
        with TAGEBUCH.open(encoding="utf-8") as datei:
            for zeile in datei:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    satz = json.loads(zeile)
                except json.JSONDecodeError:
                    continue
                roh = satz.get("gesendet_am") or satz.get("zeit") or ""
                try:
                    wann = datetime.fromisoformat(roh)
                except ValueError:
                    continue
                stelle = _kostenstelle(satz.get("absender", ""))
                aus.setdefault(stelle, []).append(wann)
    except OSError:
        return aus
    for liste in aus.values():
        liste.sort()
    return aus


def lernen(jetzt: datetime | None = None) -> dict[str, dict]:
    """Was normal ist, je Kostenstelle. Wird woechentlich neu gerechnet."""
    jetzt = jetzt or datetime.now()
    aus: dict[str, dict] = {}
    for stelle, zeiten in meldungen().items():
        spanne_tage = (zeiten[-1] - zeiten[0]).total_seconds() / 86400
        seit_letzter = (jetzt - zeiten[-1]).total_seconds() / 3600

        eintrag = {
            "kostenstelle": stelle,
            "meldungen": len(zeiten),
            "beobachtet_tage": round(spanne_tage, 1),
            "zuletzt": zeiten[-1].isoformat(timespec="minutes"),
            "stunden_still": round(seit_letzter, 1),
            "takt": "noch unbekannt",
            "abstand_stunden": None,
            "still": False,
            "warum": "",
        }

        if len(zeiten) < MINDESTMELDUNGEN or spanne_tage < MINDESTBEOBACHTUNG_TAGE:
            eintrag["warum"] = (
                "erst %d Meldungen ueber %.1f Tage - ab %d Meldungen und "
                "%d Tagen wird ein Takt festgelegt"
                % (len(zeiten), spanne_tage, MINDESTMELDUNGEN,
                   MINDESTBEOBACHTUNG_TAGE))
            aus[stelle] = eintrag
            continue

        abstaende = [(b - a).total_seconds() / 3600
                     for a, b in zip(zeiten, zeiten[1:])]
        # Der Median, nicht der Durchschnitt: ein einzelner langer Abstand
        # ueber Weihnachten soll den Takt nicht verbiegen.
        mitte = statistics.median(abstaende)
        eintrag["abstand_stunden"] = round(mitte, 2)
        eintrag["takt"] = _benennen(mitte)
        eintrag["still"] = seit_letzter > mitte * STILL_AB
        if eintrag["still"]:
            eintrag["warum"] = (
                "meldet sich sonst etwa alle %s, schweigt aber seit %s"
                % (_dauer(mitte), _dauer(seit_letzter)))
        else:
            eintrag["warum"] = "im gewohnten Takt (etwa alle %s)" % _dauer(mitte)
        aus[stelle] = eintrag
    return aus


def _benennen(stunden: float) -> str:
    if stunden < 2:
        return "dauerhaft"
    if stunden < 36:
        return "taeglich"
    if stunden < 24 * 10:
        return "woechentlich"
    if stunden < 24 * 45:
        return "monatlich"
    return "selten"


def _dauer(stunden: float) -> str:
    if stunden < 1:
        return "%d Minuten" % round(stunden * 60)
    if stunden < 48:
        return "%.0f Stunden" % stunden
    return "%.0f Tage" % (stunden / 24)


def stillstand(jetzt: datetime | None = None) -> list[dict]:
    """Nur die Stellen, die laenger schweigen als gewohnt."""
    return [e for e in lernen(jetzt).values() if e["still"]]


def nie_gemeldet(alle_module: list[str]) -> list[str]:
    """Module, von denen noch nie eine Meldung kam.

    Das ist kein Stillstand, sondern ein Teil, den es nur auf dem Papier
    gibt. Der Unterschied gehoert benannt: das eine ist kaputt, das andere
    ist ungebaut.
    """
    gehoert = set(meldungen())
    return sorted(m for m in alle_module if m not in gehoert)
