"""Pruefungen des Sicherheitsbeauftragten. Alles trocken, alles kostenlos.

Gearbeitet wird mit erfundenen Schluesseln in einem Wegwerf-Ordner. Die
echte .env wird nie gelesen, und kein Wert taucht in einer Ausgabe auf.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, TROCKEN  # noqa: E402

import pruefer as P  # noqa: E402

#: Ein erfundener Schluessel, lang genug, um als Geheimnis zu gelten.
GEHEIM = "sk-pruefstand-0000-nur-fuer-die-pruefung-nicht-echt"


@contextmanager
def wegwerf_haus(env_zeilen: str = "", einstellungen: dict | None = None):
    """Ein kleines Haus mit eigener .env, in dem gesucht werden darf."""
    import json

    ordner = Path(tempfile.mkdtemp(prefix="sicherheit_"))
    (ordner / "universe").mkdir()
    (ordner / ".env").write_text(
        env_zeilen or ("PRUEF_SCHLUESSEL=%s\n" % GEHEIM), encoding="utf-8", newline="")
    (ordner / "universe" / "sicherheit.json").write_text(
        json.dumps(einstellungen or {}, ensure_ascii=False), encoding="utf-8", newline="")

    alt = (P.NEUSTART, P.ENV, P.SICHERHEITSDATEI, P.UNIVERSE)
    P.NEUSTART = ordner
    P.ENV = ordner / ".env"
    P.UNIVERSE = ordner / "universe"
    P.SICHERHEITSDATEI = ordner / "universe" / "sicherheit.json"
    try:
        yield ordner
    finally:
        P.NEUSTART, P.ENV, P.SICHERHEITSDATEI, P.UNIVERSE = alt
        shutil.rmtree(ordner, ignore_errors=True)


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


# ================================================================== Schluessel

@anmelden("sicherheit.findet-schluessel-im-klartext", "system.sicherheit",
          "Ein Schluessel ausserhalb der .env wird gefunden", TROCKEN,
          "dass ein versehentlich hineinkopierter Schluessel auffaellt",
          blind_fuer="Schluessel unter 16 Zeichen - die gelten als Wort")
def findet_schluessel_im_klartext():
    with wegwerf_haus() as haus:
        bericht = P.Bericht()
        P.schluessel_suchen(bericht)
        _gleich(bericht.befunde, [], "sauberes Haus")

        (haus / "universe" / "einstellungen.py").write_text(
            'SCHLUESSEL = "%s"\n' % GEHEIM, encoding="utf-8", newline="")
        bericht = P.Bericht()
        P.schluessel_suchen(bericht)
        _gleich(len(bericht.befunde), 1, "ein Befund")
        _gleich(bericht.befunde[0].schwere, P.SCHWER, "schwer")
        return "Schluessel in einer Codedatei gefunden und als schwer gemeldet"


@anmelden("sicherheit.gibt-keinen-wert-aus", "system.sicherheit",
          "Kein Befund enthaelt je einen Schluesselwert", TROCKEN,
          "dass der Sicherheitsbericht nicht selbst das Leck ist")
def gibt_keinen_wert_aus():
    with wegwerf_haus() as haus:
        (haus / "universe" / "x.py").write_text(
            'K = "%s"\n' % GEHEIM, encoding="utf-8", newline="")
        bericht = P.Bericht()
        P.schluessel_suchen(bericht)
        for b in bericht.befunde:
            ganze_zeile = b.zeile()
            if GEHEIM in ganze_zeile:
                raise AssertionError("der Befund enthaelt den Schluessel selbst")
            if "PRUEF_SCHLUESSEL" not in ganze_zeile:
                raise AssertionError("der Befund nennt nicht einmal den Namen")
        return "Befund nennt den Namen, nie den Wert"


@anmelden("sicherheit.kurzes-ist-kein-geheimnis", "system.sicherheit",
          "Ein 'ja' in der .env loest keinen Alarm aus", TROCKEN,
          "dass der Rundgang nicht bei jeder Einstellung laut wird")
def kurzes_ist_kein_geheimnis():
    with wegwerf_haus("UNIVERSE_TROCKEN=ja\nUNIVERSE_MODELL=claude-opus\n"
                      "ECHTER=%s\n" % GEHEIM):
        namen = set(P.geheimnisse())
        _gleich(namen, {"ECHTER"}, "nur der lange Wert gilt als Geheimnis")
        return "kurze Einstellungen ignoriert, der Schluessel erkannt"


# ================================================================== Zugaenge

@anmelden("sicherheit.fehlender-zugang-faellt-auf", "system.sicherheit",
          "Ein leerer Zugang wird mit seiner Folge gemeldet", TROCKEN,
          "dass ein stiller Ausfall benannt wird, nicht nur ein leeres Feld")
def fehlender_zugang_faellt_auf():
    with wegwerf_haus("VORHANDEN=%s\nFEHLT=\n" % GEHEIM,
                      {"zugaenge": {
                          "FEHLT": {"modul": "prod.video.clip",
                                    "schwere": "mittel",
                                    "folge": "Dann nimmt die Strasse Platzhalter."},
                          "VORHANDEN": {"modul": "wissen"}}}):
        bericht = P.Bericht()
        P.vollzaehligkeit_pruefen(bericht)
        _gleich(len(bericht.befunde), 1, "ein Befund")
        if "Platzhalter" not in bericht.befunde[0].rat:
            raise AssertionError("die Folge wird nicht genannt")
        return "fehlender Zugang gemeldet, samt dem, was er lahmlegt"


@anmelden("sicherheit.ablauf-wird-vorher-gemeldet", "system.sicherheit",
          "Ein Schluessel wird vor dem Ablauf gemeldet, nicht danach", TROCKEN,
          "dass niemand tagelang am falschen Ende sucht")
def ablauf_wird_vorher_gemeldet():
    with wegwerf_haus("K=%s\n" % GEHEIM,
                      {"ablauf_vorlauf_tage": 21,
                       "ablaeuft": {"BALD": "2026-10-02",
                                    "LAENGST": "2026-08-01",
                                    "SPAETER": "2027-01-01"}}):
        bericht = P.Bericht()
        P.ablauf_pruefen(bericht, heute=date(2026, 9, 20))
        schwere = sorted(b.schwere for b in bericht.befunde)
        _gleich(schwere, [P.MITTEL, P.SCHWER], "einer bald, einer abgelaufen")
        namen = " ".join(b.was for b in bericht.befunde)
        if "SPAETER" in namen:
            raise AssertionError("ein Schluessel in vier Monaten ist kein Thema")
        return "abgelaufen als schwer, in 12 Tagen als bald, ferner Termin still"


# ================================================================== Ablage

@anmelden("sicherheit.env-muss-geschuetzt-sein", "system.sicherheit",
          "Eine ungeschuetzte .env ist ein schwerer Befund", TROCKEN,
          "dass der wichtigste Schutz nicht unbemerkt wegfaellt",
          blind_fuer="ob die .gitignore auch fuer Unterordner greift")
def env_muss_geschuetzt_sein():
    with wegwerf_haus():
        # Im Wegwerf-Haus gibt es kein Git - check-ignore schlaegt fehl,
        # und genau das soll als schwerer Befund gelten.
        bericht = P.Bericht()
        P.ablage_pruefen(bericht)
        schwer = bericht.nach_schwere(P.SCHWER)
        if not schwer:
            raise AssertionError("eine ungeschuetzte .env wurde nicht gemeldet")
        if "gitignore" not in schwer[0].rat.lower():
            raise AssertionError("der Rat nennt die .gitignore nicht")
        return "ungeschuetzte .env als schwer gemeldet, mit dem richtigen Rat"


@anmelden("sicherheit.echte-env-ist-geschuetzt", "system.sicherheit",
          "Die echte .env ist vor Git sicher und war es immer", TROCKEN,
          "dass die Schluessel dieses Projekts nie im Repo lagen")
def echte_env_ist_geschuetzt():
    bericht = P.Bericht()
    P.ablage_pruefen(bericht)
    schwer = bericht.nach_schwere(P.SCHWER)
    if schwer:
        raise AssertionError("; ".join(b.was for b in schwer))
    return "die .env ist ignoriert und war nie im Verlauf"


# ================================================================== Tuer

@anmelden("sicherheit.tuer-wird-bewacht", "system.sicherheit",
          "Ein Zugriff an der Tuer vorbei wird gefunden", TROCKEN,
          "dass niemand die Steckbriefe umgeht")
def tuer_wird_bewacht():
    with wegwerf_haus() as haus:
        (haus / "universe" / "eigenmaechtig").mkdir()
        (haus / "universe" / "eigenmaechtig" / "x.py").write_text(
            "import chromadb\n", encoding="utf-8", newline="")
        bericht = P.Bericht()
        P.tuer_pruefen(bericht)
        _gleich(len(bericht.befunde), 1, "ein Befund")
        _gleich(bericht.befunde[0].bereich, "Tuer", "Bereich")

        # Der Kern darf es.
        (haus / "universe" / "kern").mkdir()
        (haus / "universe" / "kern" / "vektor.py").write_text(
            "import chromadb\n", encoding="utf-8", newline="")
        bericht = P.Bericht()
        P.tuer_pruefen(bericht)
        _gleich(len(bericht.befunde), 1, "der Kern loest keinen Befund aus")
        return "fremder Zugriff gemeldet, der Kern darf es"


# ================================================================== Ausgang

@anmelden("sicherheit.abgeholt-ohne-freigabe", "system.sicherheit",
          "Ein abgeholtes Stueck ohne Freigabe ist ein schwerer Befund",
          TROCKEN,
          "dass deine Freigabe die einzige Stelle bleibt, an der du entscheidest")
def abgeholt_ohne_freigabe():
    with wegwerf_haus() as haus:
        ausgang = haus / "vault" / "warenausgang"
        ausgang.mkdir(parents=True)
        (ausgang / "W0001_x.md").write_text(
            "---\nkennung: W0001\nfreigegeben_von: \"\"\n"
            "abgeholt_von: social_media_manager\n---\n", encoding="utf-8", newline="")
        (ausgang / "W0002_y.md").write_text(
            "---\nkennung: W0002\nfreigegeben_von: daniel\n"
            "abgeholt_von: social_media_manager\n---\n", encoding="utf-8", newline="")
        bericht = P.Bericht()
        P.ausgang_pruefen(bericht)
        _gleich(len(bericht.befunde), 1, "nur das ungefreigegebene faellt auf")
        if "W0001" not in bericht.befunde[0].was:
            raise AssertionError("der falsche Vorgang wurde gemeldet")
        return "W0001 gemeldet, W0002 mit Freigabe durchgelassen"


@anmelden("sicherheit.der-name-entscheidet", "system.sicherheit",
          "Ein kurzes Passwort wird trotzdem bewacht", TROCKEN,
          "dass die Laengengrenze keine Luecke mehr ist",
          blind_fuer="Geheimnisse, deren Name keines der Schluesselworte traegt")
def der_name_entscheidet():
    """Frueher entschied nur die Laenge: alles unter sechzehn Zeichen galt
    als Wort. Passwoerter mit zwoelf Zeichen fielen darunter - waere eines
    irgendwo gelandet, haette es niemand gefunden. Der Name weiss es
    besser als die Laenge."""
    with wegwerf_haus("LINKEDIN_PASSWORT=zwoelfzeich\n"
                      "IRGENDEIN_KEY=achtzeic\n"
                      "UNIVERSE_TROCKEN=ja\n"
                      "PFAD=C:/kurz/genug\n"
                      "PLATZHALTER_PASSWORT=x\n"):
        namen = set(P.geheimnisse())
        _gleich(namen, {"LINKEDIN_PASSWORT", "IRGENDEIN_KEY"},
                "Passwort und Schluessel bewacht, Pfad und Platzhalter nicht")
        return ("12-Zeichen-Passwort bewacht, 'ja' und ein Pfad nicht, "
                "ein einzelnes Zeichen als Platzhalter auch nicht")


@anmelden("sicherheit.passwoerter-werden-gesucht", "system.sicherheit",
          "Auch die echten Passwoerter stehen unter Aufsicht", TROCKEN,
          "dass die Luecke bei den 12-Zeichen-Passwoertern zu ist")
def passwoerter_werden_gesucht():
    bewacht = set(P.geheimnisse())
    alle = P.alle_eintraege()
    ungewacht = [n for n, w in alle.items()
                 if "PASSWORT" in n.upper() and len(w) >= 8
                 and n not in bewacht]
    if ungewacht:
        raise AssertionError("nicht bewacht: " + ", ".join(sorted(ungewacht)))
    return "%d Werte unter Aufsicht, darunter jedes gesetzte Passwort" % len(bewacht)
