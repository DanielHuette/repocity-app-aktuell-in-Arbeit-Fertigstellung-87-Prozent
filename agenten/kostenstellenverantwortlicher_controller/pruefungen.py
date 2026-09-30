"""Pruefungen des Kostenstellenverantwortlichen. Alles trocken, alles kostenlos.

Jede Buchungspruefung schreibt in ein Wegwerf-Buch. Das echte Verbrauchsbuch
wird nie angefasst - genau der Fehler, den diese Pruefungen verhindern
sollen: ein Pruefstandlauf hat einmal 4,00 EUR ins echte Buch geschrieben,
die nie geflossen sind.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

import takt as takt_lernen  # noqa: E402
import verbrauch  # noqa: E402

controller = laden(HIER / "main.py", "kostenstellenverantwortlicher_main")


@contextmanager
def wegwerf_buch():
    ordner = Path(tempfile.mkdtemp(prefix="kosten_"))
    echt = verbrauch.BUCH
    verbrauch.BUCH = ordner / "verbrauch.jsonl"
    try:
        yield ordner
    finally:
        verbrauch.BUCH = echt
        shutil.rmtree(ordner, ignore_errors=True)


@contextmanager
def wegwerf_bremse():
    """Ein leeres Bremsenheft - die Marken des Nutzers werden nicht angefasst."""
    import bremse
    ordner = Path(tempfile.mkdtemp(prefix="bremse_"))
    echt = bremse.DATEI
    bremse.DATEI = ordner / "kostenbremse.json"
    try:
        yield bremse
    finally:
        bremse.DATEI = echt
        shutil.rmtree(ordner, ignore_errors=True)


@contextmanager
def wegwerf_tagebuch(zeilen: str):
    ordner = Path(tempfile.mkdtemp(prefix="tagebuch_"))
    datei = ordner / "tagebuch.jsonl"
    datei.write_text(zeilen, encoding="utf-8", newline="")
    echt = takt_lernen.TAGEBUCH
    takt_lernen.TAGEBUCH = datei
    try:
        yield datei
    finally:
        takt_lernen.TAGEBUCH = echt
        shutil.rmtree(ordner, ignore_errors=True)


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


# ================================================================== Buchen

@anmelden("kosten.buchen-und-zaehlen", "system.kosten",
          "Was gebucht wird, taucht im Kassensturz auf", TROCKEN,
          "dass der Controller zaehlt, was tatsaechlich ausgegeben wurde")
def buchen_und_zaehlen():
    with wegwerf_buch():
        verbrauch.buchen("prod.video.stueck", 0.30, "sechs Endbilder")
        verbrauch.buchen("marke", 0.05, "ein Kit-Bild")
        _gleich(verbrauch.verbraucht(topf="hochwertige_videos"), 0.3,
                "Topf hochwertige_videos")
        _gleich(verbrauch.verbraucht(kostenstelle="marke"), 0.05, "Kostenstelle marke")
        return "0,30 EUR und 0,05 EUR gebucht, beide richtig zugeordnet"


@anmelden("kosten.pruefung-verfaelscht-nicht", "system.kosten",
          "Eine Pruefbuchung zaehlt nicht als Ausgabe", TROCKEN,
          "dass keine Zahl eine Ausgabe behauptet, die nie stattfand",
          blind_fuer="Buchungen, die gar nicht erst gemacht werden")
def pruefung_verfaelscht_nicht():
    with wegwerf_buch():
        verbrauch.buchen("prod.video.stueck", 4.00, "Pruefstand",
                         herkunft=verbrauch.PRUEFUNG)
        verbrauch.buchen("prod.video.stueck", 0.30, "echter Lauf")
        _gleich(verbrauch.verbraucht(topf="hochwertige_videos"), 0.3,
                "nur die echte Ausgabe zaehlt")
        alle = verbrauch.buchungen(herkunft=None)
        _gleich(len(alle), 2, "sichtbar bleiben beide")
        return "4,00 EUR Pruefbuchung sichtbar, aber nicht gezaehlt"


@anmelden("kosten.kostenstelle-findet-topf", "system.kosten",
          "Jede Kostenstelle findet ihren Topf", TROCKEN,
          "dass keine Ausgabe im falschen Topf landet")
def kostenstelle_findet_topf():
    _gleich(verbrauch.topf_von("prod.video.stueck"), "hochwertige_videos", "teuer")
    _gleich(verbrauch.topf_von("prod.video.clip"), "clips_und_bilder", "guenstig")
    _gleich(verbrauch.topf_von("ausbildung"), "denken", "denken")
    # Unbekannte Kennung faellt auf ihren Stamm zurueck.
    _gleich(verbrauch.topf_von("prod.video.clip.neu"), "clips_und_bilder",
            "unbekannte Unterkennung")
    return "vier Kennungen, jede im richtigen Topf"


# ================================================================== Bremse

@anmelden("kosten.ohne-marke-keine-grenze", "system.kosten",
          "Hat der Nutzer keine Marke gesetzt, laeuft alles durch", TROCKEN,
          "dass niemand heimlich eine Grenze einbaut. Von Daniel am 07.09. "
          "entschieden: 'die entscheidung wieviel der user ausgibt, soll nur "
          "dem user unterliegen'.")
def ohne_marke_keine_grenze():
    with wegwerf_buch(), wegwerf_bremse():
        verbrauch.buchen("prod.video.stueck", 500.00, "sehr viel verbraucht")
        ja, grund = verbrauch.darf("prod.video.stueck", 100.00)
        _gleich(ja, True, "ohne Marke laeuft auch ein grosser Betrag durch")
        if "keine Marke" not in grund:
            raise AssertionError("die Begruendung sagt nicht, warum: " + grund)
        return "500 EUR im Buch, 100 EUR mehr - erlaubt, weil keine Marke gesetzt ist"


@anmelden("kosten.marke-sperrt-neuen-lauf", "system.kosten",
          "Die Marke des Nutzers macht zu, wenn sie erreicht ist", TROCKEN,
          "dass eine gesetzte Marke wirklich haelt und nicht nur angezeigt wird")
def marke_sperrt_neuen_lauf():
    with wegwerf_buch(), wegwerf_bremse() as bremse:
        bremse.setzen("prod.video.stueck", monat_eur=25.00, lauf_eur=5.00)
        verbrauch.buchen("prod.video.stueck", 24.90, "fast alles verbraucht")
        ja, grund = verbrauch.darf("prod.video.stueck", 0.30)
        _gleich(ja, False, "neuer Lauf gesperrt")
        if "Monatsmarke" not in grund:
            raise AssertionError("die Begruendung nennt den Grund nicht: " + grund)
        return "Marke 25,00 EUR, 24,90 verbraucht - nichts Neues faengt mehr an"


@anmelden("kosten.warnung-bei-80-prozent", "system.kosten",
          "Bei 80 Prozent der Marke wird gewarnt, aber nicht angehalten", TROCKEN,
          "dass die Warnung frueh genug kommt und den Lauf nicht abwuergt. "
          "Von Daniel am 07.09. so entschieden.")
def warnung_bei_80_prozent():
    with wegwerf_buch(), wegwerf_bremse() as bremse:
        bremse.setzen("prod.video.stueck", monat_eur=10.00)
        verbrauch.buchen("prod.video.stueck", 7.00, "sieben Euro verbraucht")

        stufe, grund = verbrauch.stufe("prod.video.stueck", 0.50)
        _gleich(stufe, "frei", "bei 75 Prozent noch keine Warnung")

        stufe, grund = verbrauch.stufe("prod.video.stueck", 1.10)
        _gleich(stufe, "warnung", "bei 81 Prozent wird gewarnt")
        ja, _ = verbrauch.darf("prod.video.stueck", 1.10)
        _gleich(ja, True, "die Warnung haelt nichts an")
        if "%" not in grund:
            raise AssertionError("die Warnung nennt den Anteil nicht: " + grund)
        return "bei 7,50 von 10 EUR still, bei 8,10 EUR Warnung - und es laeuft weiter"


@anmelden("kosten.angefangenes-laeuft-zu-ende", "system.kosten",
          "Ein laufender Auftrag darf fertig werden", TROCKEN,
          "dass kein halbes Video liegen bleibt - so entschieden")
def angefangenes_laeuft_zu_ende():
    with wegwerf_buch(), wegwerf_bremse() as bremse:
        bremse.setzen("prod.video.stueck", monat_eur=25.00, lauf_eur=5.00)
        verbrauch.buchen("prod.video.stueck", 24.90, "fast alles verbraucht")
        ja, grund = verbrauch.darf("prod.video.stueck", 0.30, schon_im_lauf=0.60)
        _gleich(ja, True, "angefangener Lauf darf weiter")
        if "fertig" not in grund and "zu Ende" not in grund:
            raise AssertionError("die Begruendung passt nicht: " + grund)
        return "angefangener Lauf laeuft ueber die Marke hinaus zu Ende"


@anmelden("kosten.marke-doppelt-bricht-ab", "system.kosten",
          "Beim Doppelten der Lauf-Marke bricht auch ein laufender Auftrag ab",
          TROCKEN,
          "dass 'zu Ende laufen lassen' kein Blankoscheck ist")
def marke_doppelt_bricht_ab():
    with wegwerf_buch(), wegwerf_bremse() as bremse:
        # Lauf-Marke 5,00 EUR, Abbruch also bei 10,00 EUR.
        bremse.setzen("prod.video.stueck", monat_eur=100.00, lauf_eur=5.00)
        ja, grund = verbrauch.darf("prod.video.stueck", 1.00, schon_im_lauf=9.50)
        _gleich(ja, False, "beim Doppelten bricht es ab")
        if "Doppelte" not in grund:
            raise AssertionError("die Begruendung nennt den Grund nicht: " + grund)
        ja, _ = verbrauch.darf("prod.video.stueck", 1.00, schon_im_lauf=6.00)
        _gleich(ja, True, "darunter laeuft es weiter")
        return "bei 10,50 EUR abgebrochen, bei 7,00 EUR noch erlaubt"


# ================================================================== Takt

_T0 = datetime(2026, 9, 1, 8, 0)


def _tagebuch(eintraege) -> str:
    import json
    return "\n".join(json.dumps({"absender": a,
                                 "gesendet_am": (_T0 + timedelta(hours=h)).isoformat()},
                                ensure_ascii=False)
                     for a, h in eintraege) + "\n"


@anmelden("takt.absender-vereinheitlicht", "system.kosten",
          "Verschiedene Schreibweisen zaehlen als eine Stelle", TROCKEN,
          "dass der Controller nicht dieselbe Stelle mehrfach zaehlt",
          blind_fuer="Absender, die in keiner Alias-Liste stehen")
def absender_vereinheitlicht():
    _gleich(takt_lernen._kostenstelle("video_agent"), "prod.video.clip", "Agentname")
    _gleich(takt_lernen._kostenstelle("github-scout"), "wissen.scout", "Bindestrich")
    _gleich(takt_lernen._kostenstelle("wohnungs-agent"), "wohnung", "Bindestrich 2")
    _gleich(takt_lernen._kostenstelle("prod.video.clip"), "prod.video.clip",
            "schon eine Modulkennung")
    return "vier Schreibweisen, drei Kostenstellen - keine doppelt"


@anmelden("takt.zu-wenig-daten-schweigt", "system.kosten",
          "Aus zwei Meldungen wird kein Takt behauptet", TROCKEN,
          "dass keine Zahl entsteht, die auf nichts beruht")
def zu_wenig_daten_schweigt():
    with wegwerf_tagebuch(_tagebuch([("video_agent", 0), ("video_agent", 24)])):
        e = takt_lernen.lernen(_T0 + timedelta(hours=30))["prod.video.clip"]
        _gleich(e["takt"], "noch unbekannt", "Takt")
        _gleich(e["still"], False, "kein falscher Alarm")
        return "zwei Meldungen ueber einen Tag - kein Takt behauptet"


@anmelden("takt.stillstand-wird-erkannt", "system.kosten",
          "Wer laenger schweigt als gewohnt, faellt auf", TROCKEN,
          "dass ein stiller Ausfall nicht als Sparerfolg durchgeht")
def stillstand_wird_erkannt():
    # Zehn Meldungen im Tagesabstand, dann acht Tage Ruhe.
    eintraege = [("video_agent", tag * 24) for tag in range(10)]
    with wegwerf_tagebuch(_tagebuch(eintraege)):
        e = takt_lernen.lernen(_T0 + timedelta(days=9 + 8))["prod.video.clip"]
        _gleich(e["takt"], "taeglich", "gelernter Takt")
        _gleich(e["still"], True, "als still erkannt")
        if "schweigt" not in e["warum"]:
            raise AssertionError("die Begruendung sagt nicht, was los ist")
        return "taeglicher Takt gelernt, acht Tage Schweigen als Alarm erkannt"


@anmelden("takt.ruhe-ist-kein-alarm", "system.kosten",
          "Ein Modul im gewohnten Takt schlaegt keinen Alarm", TROCKEN,
          "dass der Controller nicht bei jeder Pause laut wird")
def ruhe_ist_kein_alarm():
    eintraege = [("github-scout", tag * 24 * 7) for tag in range(4)]
    with wegwerf_tagebuch(_tagebuch(eintraege)):
        e = takt_lernen.lernen(_T0 + timedelta(days=21 + 5))["wissen.scout"]
        _gleich(e["takt"], "woechentlich", "gelernter Takt")
        _gleich(e["still"], False, "fuenf Tage sind bei woechentlich normal")
        return "woechentlicher Takt, fuenf Tage Ruhe - kein Alarm"


@anmelden("takt.ungebaut-ist-kein-stillstand", "system.kosten",
          "Nie gemeldet heisst ungebaut, nicht kaputt", TROCKEN,
          "dass der Unterschied benannt wird statt als Ausfall zu erscheinen")
def ungebaut_ist_kein_stillstand():
    with wegwerf_tagebuch(_tagebuch([("video_agent", 0)])):
        nie = takt_lernen.nie_gemeldet(["prod.video.clip", "trading", "webseite"])
        _gleich(nie, ["trading", "webseite"], "nie gemeldet")
        _gleich(takt_lernen.stillstand(_T0 + timedelta(days=90)), [],
                "keiner davon gilt als Stillstand")
        return "zwei ungebaute Module benannt, keines als Ausfall gemeldet"


# ================================================================== Bericht

@anmelden("kosten.bericht-laeuft", "system.kosten",
          "Der Bericht laeuft und nennt alle vier Groessen", TROCKEN,
          "dass der Controller lesbar ausgibt, was er weiss",
          blind_fuer="ob die Zahlen inhaltlich richtig sind")
def bericht_laeuft():
    with wegwerf_buch():
        verbrauch.buchen("prod.video.stueck", 0.29, "sechs Endbilder")
        text = controller.bericht()
        for muss in ("GELD", "TAKT", "KONTINGENTE", "VERSCHWENDUNG",
                     "DEINE EINGRIFFE"):
            if muss not in text:
                raise AssertionError("im Bericht fehlt: " + muss)
        if "0.2900" not in text and "0.29" not in text:
            raise AssertionError("die gebuchten 0,29 EUR stehen nicht im Bericht")
        return "alle vier Groessen im Bericht, die Ausgabe taucht auf"


# ================================================================== Absender

@anmelden("takt.agenten-melden-ihre-kennung", "system.kosten",
          "Jeder Agent meldet unter seiner Modul-Kennung", TROCKEN,
          "dass keine Stelle doppelt gezaehlt wird",
          blind_fuer="Agenten, die gar keine meldung.py haben")
def agenten_melden_ihre_kennung():
    """Frueher hiess dieselbe Stelle mal video_agent, mal prod.video.clip,
    mal wohnungs-agent. Der Controller gruppiert danach - und fand
    Stillstand, wo keiner war."""
    import json

    universe = HIER.parent
    module = set(json.loads((universe / "gehirn.json").read_text(
        encoding="utf-8")).get("steckbriefe", {}))
    module.discard("standard")

    geprueft, falsch = 0, []
    for datei in sorted(universe.glob("*/meldung.py")):
        text = datei.read_text(encoding="utf-8")
        zeile = [z for z in text.splitlines() if z.startswith("MODUL = ")]
        if not zeile:
            falsch.append("%s nennt keine MODUL-Kennung" % datei.parent.name)
            continue
        kennung = zeile[0].split("=", 1)[1].strip().strip('"').strip("'")
        if kennung not in module:
            falsch.append("%s meldet als %r - das ist keine Modul-Kennung"
                          % (datei.parent.name, kennung))
        geprueft += 1
    if falsch:
        raise AssertionError("; ".join(falsch))
    if geprueft < 8:
        raise AssertionError("nur %d Agenten geprueft - das sind zu wenige"
                             % geprueft)
    return "%d Agenten melden unter einer gueltigen Modul-Kennung" % geprueft


@anmelden("takt.meldeweg-des-kerns-erreichbar", "system.kosten",
          "Jeder Agent erreicht den Meldeweg des Kerns", TROCKEN,
          "dass eine Umbenennung im Kern keinen Agenten stumm schaltet",
          blind_fuer="ob der Hub die Meldung dann auch annimmt")
def meldeweg_erreichbar():
    """Die Datei im Kern hiess einmal meldung.py und heisst jetzt melden.py.
    Sieben Agenten haben sie mit 'from kern.meldung import' geholt und
    waren damit stumm, ohne dass es jemand gemerkt haette."""
    import importlib.util

    universe = HIER.parent
    stumm = []
    for datei in sorted(universe.glob("*/meldung.py")):
        name = "meldeweg_" + datei.parent.name
        try:
            beschreibung = importlib.util.spec_from_file_location(name, datei)
            modul = importlib.util.module_from_spec(beschreibung)
            beschreibung.loader.exec_module(modul)
            if not callable(getattr(modul, "melde", None)):
                stumm.append(datei.parent.name + " hat kein melde()")
        except Exception as fehler:
            stumm.append("%s: %s" % (datei.parent.name, fehler))
    if stumm:
        raise AssertionError("; ".join(stumm))
    return "alle Meldewege laden und haben ein melde()"


@anmelden("takt.meldeweg-behaelt-seine-funktionen", "system.kosten",
          "Kein Meldeweg verliert eine Funktion, die benutzt wird", TROCKEN,
          "dass eine Umstellung am Meldeweg keinen Aufrufer stumm schaltet",
          blind_fuer="Funktionen, die nur zur Laufzeit gesucht werden")
def meldeweg_behaelt_seine_funktionen():
    """Beim Vereinheitlichen der Absender ist meldung.schritt() verloren
    gegangen - die Funktion, mit der die Videostrasse jeden Arbeitsschritt
    meldet. Der ganze Lauf brach ab. Diese Pruefung sucht in jedem
    Agentenordner nach meldung.<name>( und stellt sicher, dass es das
    gibt."""
    import importlib.util
    import re

    universe = HIER.parent
    fehlt = []
    for meldeweg in sorted(universe.glob("*/meldung.py")):
        ordner = meldeweg.parent
        name = "meldeweg_pruefung_" + ordner.name
        try:
            b = importlib.util.spec_from_file_location(name, meldeweg)
            modul = importlib.util.module_from_spec(b)
            b.loader.exec_module(modul)
        except Exception as f:
            fehlt.append("%s laedt nicht: %s" % (ordner.name, f))
            continue
        gebraucht = set()
        for datei in ordner.rglob("*.py"):
            if datei.name in ("meldung.py", "pruefungen.py"):
                continue
            try:
                text = datei.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            gebraucht.update(re.findall(r"\bmeldung\.([a-z_]+)\s*\(", text))
        for funktion in sorted(gebraucht):
            if not hasattr(modul, funktion):
                fehlt.append("%s ruft meldung.%s() auf - gibt es nicht"
                             % (ordner.name, funktion))
    if fehlt:
        raise AssertionError("; ".join(fehlt))
    return "jeder Aufruf an einen Meldeweg findet seine Funktion"



# ================================================================== Modellkosten

@anmelden("kosten.modellaufruf-wird-gebucht", "system.kosten",
          "Ein Modellaufruf landet mit seinen Tokenzahlen im Buch", TROCKEN,
          "dass der teuerste Posten nicht mehr unsichtbar ist",
          blind_fuer="ob die Listenpreise stimmen - Token sind gezaehlt, "
                     "Preise sind Liste")
def modellaufruf_wird_gebucht():
    """Sieben Stellen im Universe fragen ein Modell. Keine davon buchte -
    und damit fehlte im Bericht ausgerechnet der Posten, der am
    schnellsten waechst."""
    import sys as _sys

    _sys.path.insert(0, str(HIER.parent / "kern"))
    import modellkosten

    class Nutzung:
        input_tokens = 1000
        output_tokens = 500

    class Antwort:
        usage = Nutzung()

    with wegwerf_buch():
        satz = modellkosten.buchen(Antwort(), "ausbildung", "claude-opus-5",
                                   "Lehrsatz formulieren")
        if satz is None:
            raise AssertionError("nichts gebucht")
        _gleich(satz["menge"], 1500, "Token gezaehlt")
        _gleich(satz["modell"], "claude-opus-5", "Modell vermerkt")
        # 1000 x 5 + 500 x 25 = 17.500 / 1e6 = 0,0175 USD x 0,92 = 0,0161 EUR (Opus 5, Liste 11.09.2026)
        if not (0.015 < satz["betrag_eur"] < 0.017):
            raise AssertionError("Betrag unplausibel: %s" % satz["betrag_eur"])
        _gleich(verbrauch.verbraucht(kostenstelle="ausbildung"),
                satz["betrag_eur"], "im Kassensturz sichtbar")
        return ("1500 Token gebucht, %.4f EUR, auf der richtigen Kostenstelle"
                % satz["betrag_eur"])


@anmelden("kosten.openai-antwort-wird-verstanden", "system.kosten",
          "Auch eine OpenAI-Antwort wird richtig gelesen", TROCKEN,
          "dass die Buchung nicht an der Form der Antwort scheitert")
def openai_antwort_wird_verstanden():
    import sys as _sys

    _sys.path.insert(0, str(HIER.parent / "kern"))
    import modellkosten

    class Nutzung:
        prompt_tokens = 800
        completion_tokens = 200

    class Antwort:
        usage = Nutzung()

    with wegwerf_buch():
        satz = modellkosten.buchen(Antwort(), "post", "claude-opus-5", "Mail")
        _gleich(satz["menge"], 1000, "Token aus prompt_/completion_tokens")
        return "OpenAI-Form gelesen, 1000 Token gebucht"


@anmelden("kosten.unbekanntes-modell-wird-benannt", "system.kosten",
          "Ein unbekanntes Modell wird geschaetzt und als solches vermerkt",
          TROCKEN,
          "dass keine Zahl Genauigkeit vortaeuscht, die sie nicht hat")
def unbekanntes_modell_wird_benannt():
    import sys as _sys

    _sys.path.insert(0, str(HIER.parent / "kern"))
    import modellkosten

    class Nutzung:
        input_tokens = 100
        output_tokens = 100

    class Antwort:
        usage = Nutzung()

    with wegwerf_buch():
        satz = modellkosten.buchen(Antwort(), "post", "gibt-es-nicht", "Probe")
        if "geschaetzt" not in satz["wofuer"]:
            raise AssertionError("die Schaetzung wird nicht kenntlich gemacht")
        return "unbekanntes Modell gerechnet und in der Buchung als Schaetzung benannt"


@anmelden("kosten.jeder-modellaufruf-bucht", "system.kosten",
          "Keine Stelle fragt ein Modell, ohne zu buchen", TROCKEN,
          "dass keine neue Ausgabe unsichtbar bleibt",
          blind_fuer="Aufrufe ueber eine andere Bibliothek als anthropic/openai")
def jeder_modellaufruf_bucht():
    """Wer kuenftig einen Modellaufruf einbaut und das Buchen vergisst,
    faellt hier durch."""
    import re

    universe = HIER.parent
    ohne = []
    for datei in universe.rglob("*.py"):
        if any(t in datei.parts for t in ("node_modules", "_archiv", "repos",
                                          "__pycache__")):
            continue
        if datei.name in ("modellkosten.py", "pruefungen.py"):
            continue
        try:
            text = datei.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not re.search(r"\.messages\.create\(|\.chat\.completions\.create\(", text):
            continue
        if "_buchen(" not in text and "modellkosten" not in text:
            ohne.append(str(datei.relative_to(universe)))
    if ohne:
        raise AssertionError("fragt ein Modell, ohne zu buchen: " + ", ".join(ohne))
    return "jede Stelle, die ein Modell fragt, bucht auch"


# ================================================================== App und Universe

#: Wo die Kotlin-Seite der Kostenbremse liegt, von universe/ aus gesehen.
_KOSTENBREMSE_KT = ("app/repocity/app/src/main/java/dev/speedofthespirit/"
                    "repocity/kern/Kostenbremse.kt")
_KETTE_KT = ("app/repocity/app/src/main/java/dev/speedofthespirit/"
             "repocity/kern/Kette.kt")


def _lies(unterhalb_universe: str) -> str:
    """Eine Datei aus dem Baum lesen. Fehlt sie, faellt die Pruefung durch."""
    from pathlib import Path
    pfad = Path(__file__).resolve().parent.parent / unterhalb_universe
    if not pfad.exists():
        raise AssertionError("Datei fehlt: %s" % pfad)
    return pfad.read_text(encoding="utf-8")


@anmelden("kosten.app-und-universe-gleiche-schwellen", "system.kosten",
          "Die Schwellen der Kostenbremse stehen in Kotlin und Python gleich",
          TROCKEN,
          "dass die App keine andere Grenze anzeigt als die, an der der Hub "
          "wirklich anhaelt. Diese Pruefung steht hier und nicht in der App: "
          "Gradle merkt nicht, wenn sich eine Python-Datei aendert, und "
          "ueberspringt den Test dann stillschweigend. Der Pruefstand laeuft "
          "jedes Mal ganz.")
def app_und_universe_gleiche_schwellen():
    """Beide Werte aus den DATEIEN lesen, nicht aus dem geladenen Modul.

    Genau daran ist der erste Anlauf gescheitert: die Pruefung las
    `bremse.WARNSCHWELLE` aus dem Modul im Speicher. Aendert jemand die
    Datei, merkt sie es nicht - Python liest sie nicht neu. Die Gegenprobe
    hat das gefangen; sie blieb gruen, obwohl die Datei kaputt war.
    """
    import re

    py = _lies("kern/bremse.py")
    kt = _lies(_KOSTENBREMSE_KT)

    gemeldet = []
    for name in ("WARNSCHWELLE", "ABBRUCH_FAKTOR"):
        a = re.search(r"^%s = ([0-9.]+)" % name, py, re.MULTILINE)
        if not a:
            raise AssertionError("%s steht nicht in bremse.py" % name)
        b = re.search(r"const val %s = ([0-9.]+)" % name, kt)
        if not b:
            raise AssertionError("%s steht nicht in Kostenbremse.kt" % name)
        hier, dort = float(a.group(1)), float(b.group(1))
        if abs(hier - dort) > 1e-9:
            raise AssertionError(
                "%s laeuft auseinander: bremse.py sagt %s, Kostenbremse.kt sagt %s"
                % (name, hier, dort))
        gemeldet.append("%s %g" % (name, hier))
    return "gleich in Kotlin und Python: " + ", ".join(gemeldet)


@anmelden("kosten.ketten-in-app-und-universe", "system.kosten",
          "Jede Kette aus funktionen.json kennt auch die App", TROCKEN,
          "dass eine neue Kette nicht ohne Kostenzeile bleibt - sonst kann "
          "der Nutzer fuer sie keine Marke setzen, ohne dass es auffaellt")
def ketten_in_app_und_universe():
    import json
    import re

    im_universe = set(json.loads(_lies("funktionen.json"))["funktionen"].keys())
    if not im_universe:
        raise AssertionError("funktionen.json nennt keine einzige Kette")

    kt = _lies(_KETTE_KT)
    in_der_app = set(re.findall(r'kennung = "([a-z0-9_-]+)"', kt))

    fehlt = im_universe - in_der_app
    if fehlt:
        raise AssertionError(
            "Die App kennt diese Kette(n) nicht: %s - in Kette.kt nachtragen"
            % ", ".join(sorted(fehlt)))
    zuviel = in_der_app - im_universe
    if zuviel:
        raise AssertionError(
            "Die App kennt Ketten, die es im Universe nicht gibt: %s"
            % ", ".join(sorted(zuviel)))
    return "%d Kette(n), in App und Universe dieselben: %s" % (
        len(im_universe), ", ".join(sorted(im_universe)))


# ================================================================== Die Strasse (Daniels 32/56, 10.09.)

#: Woran man einen Aufruf erkennt, der Geld oder ein Kontingent kostet - und
#: womit die Datei dann buchen muss. Wer eine neue Stelle einbaut, ohne zu
#: buchen, wird hier rot, nicht erst im Bericht des Controllers.
_RUFT = ("messages.create(", "api.anthropic.com/v1/messages", "chat/completions",
         "fal.run/", "api.tavily.com", "edge_tts.Communicate(")
_BUCHT = ("modellkosten.buchen(", "verbrauch.buchen(", "verbrauch.fuer_modell(",
          "verbrauch.kontingent(")
_AUSSEN = ("Betatests", "pruefungen.py", "modellkosten.py", "verbrauch.py",
           "zugangsprobe.py", "zugangswaechter.py", "einrichten.py", "kosten_abholen.py")


def _rufende_dateien() -> list[Path]:
    universe = HIER.parent
    aus = []
    for datei in universe.rglob("*.py"):
        rel = str(datei.relative_to(universe))
        if any(a in rel for a in _AUSSEN) or "node_modules" in rel or "build" in rel.split("\\"):
            continue
        try:
            text = datei.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(r in text for r in _RUFT):
            aus.append(datei)
    return aus


@anmelden("kosten.jede-rufende-stelle-bucht", "system.kosten",
          "Jede Datei, die ein Modell oder einen bezahlten Dienst ruft, bucht auch", TROCKEN,
          "dass keine Ausgabe am Verbrauchsbuch vorbei laeuft - Daniel 32/56: "
          "'alle kosten erfassen'")
def jede_rufende_stelle_bucht():
    stumm = []
    dateien = _rufende_dateien()
    for datei in dateien:
        text = datei.read_text(encoding="utf-8")
        if not any(b in text for b in _BUCHT):
            stumm.append(str(datei.relative_to(HIER.parent)))
    if not dateien:
        raise AssertionError("keine einzige rufende Stelle gefunden - die Suche ist kaputt")
    if stumm:
        raise AssertionError("ruft, bucht aber nicht: " + ", ".join(sorted(stumm)))
    return "%d rufende Dateien, alle buchen" % len(dateien)


@anmelden("kosten.kein-modell-unter-opus", "system.kosten",
          "Kein Modell unter Opus - weder fest im Code noch in der .env", TROCKEN,
          "dass nie wieder ein Haiku oder Sonnet irgendwo im Universe eine Aufgabe hat - "
          "Daniel, 11.09.2026: 'minimum model muss opus 5 sein, ueberall'")
def kein_modell_unter_opus():
    """Bis zum 11.09.2026 standen sieben Stellen mit Haiku 3.5 fest im Code und
    neun mit Sonnet 4.5 als Voreinstellung. Seitdem kennt nur kern/modellwahl.py
    den Namen; diese Pruefung haelt das nach. Gegenprobe:
    Betatests/gegenprobe_modellwahl.py."""
    import sys as _sys

    _sys.path.insert(0, str(HIER.parent / "kern"))
    import modellwahl

    treffer = modellwahl.unter_opus_im_code()
    if treffer:
        raise AssertionError("Modell unter Opus im Code: " + ", ".join(treffer[:10]))
    gilt = modellwahl.modell()   # bricht ab, wenn die .env ein Modell unter Opus nennt
    return "kein Modell unter Opus im Code; es gilt %s" % gilt


@anmelden("kosten.zusammenfassung-traegt-betrieb", "system.kosten",
          "Die Zusammenfassung rechnet Kategorien und die festen Betriebskosten", TROCKEN,
          "dass die Kostenseite Sprachmodell, Produktion und Betrieb getrennt zeigen kann")
def zusammenfassung_traegt_betrieb():
    with wegwerf_buch():
        verbrauch.buchen("prod.video.stueck", 0.30, "sechs Endbilder", modell="fal-ai/flux/dev")
        verbrauch.buchen("bewerbung", 0.02, "Anschreiben", modell="claude-x", dienst="anthropic")
        verbrauch.kontingent("pexels", "prod.video.clip", 3, wofuer="Bildsuche")
        verbrauch.buchen("prod.praesentation", 0.0, "Bild", modell="fal-ai/unbekannt")
        z = verbrauch.zusammenfassung(seit="2000-01-01")
        _gleich(z["je_kategorie"].get("modell"), 0.02, "Kategorie modell")
        _gleich(z["je_kategorie"].get("produktion"), 0.30, "Kategorie produktion")
        _gleich(z["kontingent_zuege"].get("pexels"), 3.0, "Kontingent-Zuege")
        _gleich(list(z["ohne_preis"].keys()), ["fal-ai/unbekannt"], "ohne Preis")
        betrieb, posten = verbrauch.betriebskosten_monat()
        if not posten or any(not p_["quelle"] for p_ in posten):
            raise AssertionError("Betriebskosten ohne Quelle oder leer")
        _gleich(z["betrieb_eur"], betrieb, "Betrieb in der Zusammenfassung")
        _gleich(z["gesamt_eur"], round(0.32 + betrieb, 6), "gesamt = laufend + Betrieb")
        return "modell 0,02 / produktion 0,30 / Betrieb %.2f EUR mit Quelle, 1 Modell ohne Preis" % betrieb


@anmelden("kosten.betriebskosten-belegt", "system.kosten",
          "Jeder feste Posten in kosten.json traegt Betrag und Quelle", TROCKEN,
          "dass keine geratene Zahl als Betriebskosten mitlaeuft")
def betriebskosten_belegt():
    posten = verbrauch.stammdaten(neu_lesen=True).get("betriebskosten", {})
    echte = {n: e for n, e in posten.items() if not n.startswith("_")}
    if not echte:
        raise AssertionError("kosten.json nennt keine Betriebskosten")
    for name, e in echte.items():
        if not isinstance(e, dict) or not e.get("quelle"):
            raise AssertionError("%s ohne Quelle" % name)
        if "usd_je_monat" not in e and "eur_je_monat" not in e:
            raise AssertionError("%s ohne Betrag" % name)
    return "%d Posten, alle mit Betrag und Quelle: %s" % (len(echte), ", ".join(sorted(echte)))

