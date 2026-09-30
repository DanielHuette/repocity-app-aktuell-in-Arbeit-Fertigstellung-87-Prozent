# -*- coding: utf-8 -*-
"""Die Zugangsprobe - sie tippt an, statt zu vermuten.

Der Waechter (``zugangswaechter.py``) liest nur, was hinterlegt ist und was
zuletzt getragen hat. Das reicht nicht: eine Anmeldung laeuft ab, ein
Schluessel wird zurueckgezogen, ein Passwort geaendert - und niemand merkt
es, bis ein Auftrag daran scheitert.

Darum tippt diese Probe die Zugaenge wirklich an:

    probiere(nutzer, "postfach")   ->  Befund
    alle(nutzer)                   ->  alle auf einmal

**Sie kostet nichts.** Jeder Weg hier ist ein Aufruf, der beim Anbieter
gratis ist: eine IMAP-Anmeldung, eine Liste der verfuegbaren Modelle, die
Auskunft ueber das eigene Konto. Kein Modell denkt, kein Bild entsteht.
Gemessen am 09.09.2026 - wer einen Weg hinzufuegt, prueft das nach und
schreibt es dazu.

**Was sie NICHT kann**, und das sagt sie auch: Portale wie LinkedIn oder
ImmoScout sperren Programme aus. Dort laesst sich eine Anmeldung nicht
antippen, ohne wie ein Einbruchsversuch auszusehen. Fuer solche Zugaenge
bleibt es beim Befund des Agenten, der zuletzt damit gearbeitet hat -
und die App bietet stattdessen den Weg zur Anmeldeseite an.

Der Befund geht in den Tresor (``tresor.befund``), damit die App ihn sieht.

Aufruf von Hand:
    python universe/kern/zugangsprobe.py anna@beispiel.de
    python universe/kern/zugangsprobe.py anna@beispiel.de postfach
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
if str(HIER) not in sys.path:
    sys.path.insert(0, str(HIER))

import tresor  # noqa: E402

DIENSTE = UNIVERSE / "dienste.json"
GEDULD_SEK = 20


@dataclass
class Probe:
    dienst: str
    #: "in Ordnung" | "abgelehnt" | "nicht pruefbar" | "nichts hinterlegt"
    stand: str
    satz: str = ""

    @property
    def gut(self) -> bool:
        return self.stand == "in Ordnung"


def _liste() -> dict:
    return json.loads(DIENSTE.read_text(encoding="utf-8"))


def _dienst(kennung: str) -> dict | None:
    for d in _liste().get("dienste", []):
        if d["kennung"] == kennung:
            return d
    return None


def _ruf(adresse: str, kopf: dict, verfahren: str = "GET") -> tuple[int, str]:
    anfrage = urllib.request.Request(adresse, method=verfahren, headers=kopf)
    try:
        with urllib.request.urlopen(anfrage, timeout=GEDULD_SEK) as antwort:
            return antwort.status, antwort.read(400).decode("utf-8", "replace")
    except urllib.error.HTTPError as f:
        return f.code, ""
    except Exception as f:                                  # noqa: BLE001
        return -1, str(f)[:200]


# ------------------------------------------------------------ die Wege
#
# Je Dienst ein Aufruf, der beim Anbieter nichts kostet. Die Zeile dahinter
# sagt, welcher - damit niemand raten muss, was die Probe tut.

def _probe_postfach(werte: dict) -> Probe:
    """Eine IMAP-Anmeldung. Kostet nichts und dauert unter einer Sekunde."""
    import imaplib
    import ssl

    # Kein sys.path.insert auf den E-Mail-Manager: postfach.py wird gleich
    # ueber seinen Pfad geladen, und wer einen fremden Agentenordner vorne
    # in den Suchpfad legt, beschert dem naechsten Import ein fremdes Modul.
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "postfach_fuer_probe", UNIVERSE / "email_manager" / "postfach.py")
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        konto = modul.konto_aus_zugang(werte)
    except Exception as f:                                  # noqa: BLE001
        return Probe("postfach", "abgelehnt", str(f)[:200])

    try:
        with imaplib.IMAP4_SSL(konto.imap_server, konto.imap_port,
                               ssl_context=ssl.create_default_context()) as m:
            m.login(konto.benutzer, konto.passwort)
            m.logout()
        return Probe("postfach", "in Ordnung",
                     "Anmeldung bei %s hat funktioniert" % konto.imap_server)
    except imaplib.IMAP4.error as f:
        return Probe("postfach", "abgelehnt",
                     "Das Postfach hat die Anmeldung abgelehnt: %s" % str(f)[:120])
    except Exception as f:                                  # noqa: BLE001
        return Probe("postfach", "nicht pruefbar",
                     "Der Server war nicht erreichbar: %s" % str(f)[:120])


def _probe_anthropic(schluessel: str) -> Probe:
    """Die Liste der Modelle. Kostenlos - es denkt kein Modell."""
    code, _ = _ruf("https://api.anthropic.com/v1/models?limit=1",
                   {"x-api-key": schluessel, "anthropic-version": "2023-06-01"})
    return _urteil("anthropic", code)


def _probe_openai(schluessel: str) -> Probe:
    code, _ = _ruf("https://api.openai.com/v1/models",
                   {"Authorization": "Bearer " + schluessel})
    return _urteil("openai", code)


def _probe_github(schluessel: str) -> Probe:
    code, _ = _ruf("https://api.github.com/user",
                   {"Authorization": "Bearer " + schluessel,
                    "User-Agent": "RepoCity"})
    return _urteil("github", code)


def _probe_pexels(schluessel: str) -> Probe:
    code, _ = _ruf("https://api.pexels.com/v1/search?query=a&per_page=1",
                   {"Authorization": schluessel})
    return _urteil("pexels", code)


def _probe_fal(schluessel: str) -> Probe:
    """Der Kontostand. Kostenlos - es entsteht kein Bild."""
    code, _ = _ruf("https://rest.alpha.fal.ai/billing/user_balance",
                   {"Authorization": "Key " + schluessel})
    return _urteil("fal", code)


def _urteil(dienst: str, code: int) -> Probe:
    if code == -1:
        return Probe(dienst, "nicht pruefbar", "kein Netz zum Anbieter")
    if code in (401, 403):
        return Probe(dienst, "abgelehnt",
                     "Der Schluessel wurde abgelehnt (%d). Er ist abgelaufen, "
                     "zurueckgezogen oder falsch eingetragen." % code)
    if 200 <= code < 300:
        return Probe(dienst, "in Ordnung", "Der Schluessel gilt")
    return Probe(dienst, "nicht pruefbar",
                 "Der Anbieter antwortete mit %d - das sagt nichts ueber den "
                 "Schluessel." % code)


#: Wo der Schluessel des Betreibers steht, wenn er ihn selbst mitbringt.
VOM_BETREIBER = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "fal": "FAL_KEY",
    "pexels": "PEXELS_API_KEY",
    "github": "GITHUB_TOKEN",
}

SCHLUESSELWEGE = {
    "anthropic": _probe_anthropic,
    "openai": _probe_openai,
    "github": _probe_github,
    "pexels": _probe_pexels,
    "fal": _probe_fal,
}


def probiere(nutzer: str, kennung: str, melden: bool = True) -> Probe:
    """Einen Zugang antippen. ``melden`` traegt den Befund in den Tresor."""
    beschreibung = _dienst(kennung)
    if beschreibung is None:
        return Probe(kennung, "nicht pruefbar", "kenne ich nicht")

    art = beschreibung.get("art", "")
    if art in ("ohne_zugang",):
        return Probe(kennung, "in Ordnung", "hier ist nichts anzumelden")
    if art == "sitzung":
        return Probe(kennung, "nicht pruefbar",
                     "Eine Anmeldung, die ablaeuft - antippen wuerde eine "
                     "neue verlangen. Das geht nur im Browser.")

    # Erst der eigene Zugang des Nutzers, dann der des Betreibers.
    werte = tresor.hole(nutzer, kennung) if nutzer else {}
    schluessel = ""
    if werte:
        schluessel = str(werte.get("schluessel", "") or "")
    elif kennung in VOM_BETREIBER:
        schluessel = (os.environ.get(VOM_BETREIBER[kennung]) or "").strip()
        if not schluessel:
            return Probe(kennung, "nichts hinterlegt", "kein Schluessel gesetzt")
    else:
        return Probe(kennung, "nichts hinterlegt", "nichts eingetragen")

    if kennung == "postfach":
        p = _probe_postfach(werte)
    elif kennung in SCHLUESSELWEGE and schluessel:
        p = SCHLUESSELWEGE[kennung](schluessel)
    else:
        p = Probe(kennung, "nicht pruefbar",
                  "Dieser Anbieter laesst sich nicht antippen, ohne wie ein "
                  "Einbruchsversuch auszusehen. Was zuletzt damit gearbeitet "
                  "hat, zaehlt.")

    # Nur echte Urteile werden gemeldet. "nicht pruefbar" darf einen guten
    # Befund nicht ueberschreiben - sonst stuende nach einem Funkloch ueberall
    # ein Fragezeichen.
    if melden and nutzer and werte and p.stand in ("in Ordnung", "abgelehnt"):
        tresor.befund(nutzer, kennung, p.gut, "" if p.gut else p.satz)
    return p


def alle(nutzer: str = "") -> dict:
    """Jeden Zugang antippen, den es zu diesem Nutzer gibt."""
    aus = {}
    for d in _liste().get("dienste", []):
        aus[d["kennung"]] = probiere(nutzer, d["kennung"])
    return aus


def _main(argumente: list[str]) -> int:
    try:
        import umgebung
        umgebung.laden()
    except Exception:                                       # noqa: BLE001
        pass

    nutzer = argumente[0] if argumente else ""
    if len(argumente) > 1:
        p = probiere(nutzer, argumente[1])
        print("%-14s %-16s %s" % (p.dienst, p.stand, p.satz))
        return 0 if p.gut else 1

    for kennung, p in alle(nutzer).items():
        print("%-14s %-16s %s" % (kennung, p.stand, p.satz))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
