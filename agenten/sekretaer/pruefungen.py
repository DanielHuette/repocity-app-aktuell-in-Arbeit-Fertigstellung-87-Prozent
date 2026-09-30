"""Pruefungen der Vernetzung: Verteiler, Zeitplan, Auftragsarten.

Alles trocken. Der Hub wird dabei nicht angerufen - stattdessen tritt ein
Doppel an seine Stelle, das aufschreibt, was ihm gesagt wurde. So laesst
sich pruefen, was der Sekretaer meldet, ohne dass etwas ins Netz geht.
"""
from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

verteiler = laden(HIER / "verteiler.py", "sekretaer_verteiler")
zeitplan = laden(KERN / "zeitplan.py", "kern_zeitplan")
laenge = laden(KERN / "laenge.py", "kern_laenge")
verbrauch = laden(KERN / "verbrauch.py", "kern_verbrauch")


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


class HubDoppel:
    """Steht an der Stelle des Hubs und schreibt auf, was ihm gesagt wird."""

    def __init__(self, offen=None, wartend=None, antworten=None):
        self.offen = offen or []
        self.wartend = wartend or []          # Auftraege im Zustand "rueckfrage"
        self.antworten = antworten or []      # Meldungen mit Entscheidung ja/nein
        self.gemeldet = []
        self.meldungen_hinein = []            # was melden() bekam

    def eingerichtet(self):
        return True

    def offene_auftraege(self):
        return list(self.offen)

    def auftraege(self, zustand=None):
        alle = list(self.offen) + list(self.wartend)
        return [a for a in alle if zustand is None or a.get("zustand") == zustand]

    def melden(self, absender, text, art="info", zusammenfassung="",
               vorgang=None, daten=None, nutzer=""):
        self.meldungen_hinein.append({
            "absender": absender, "text": text, "art": art,
            "zusammenfassung": zusammenfassung, "vorgang": vorgang,
            "daten": daten or {}, "nutzer": nutzer})
        return True

    def entscheidungen(self):
        return [m for m in self.antworten if m.get("entscheidung") in ("ja", "nein")]

    def zustand_melden(self, kennung, zustand, rueckmeldung="",
                       fortschritt=None, warenausgang=""):
        self.gemeldet.append({"id": kennung, "zustand": zustand,
                              "rueckmeldung": rueckmeldung})
        return True

    def letzter(self):
        return self.gemeldet[-1] if self.gemeldet else {}


@contextmanager
def hub_doppel(offen=None, wartend=None, antworten=None):
    echt = verteiler.hub_modul
    doppel = HubDoppel(offen, wartend, antworten)
    verteiler.hub_modul = doppel
    try:
        yield doppel
    finally:
        verteiler.hub_modul = echt


@contextmanager
def starter_doppel(gelaufen=True, grund="gelaufen"):
    """Keine Werkstatt wird wirklich angestossen - nur festgehalten, wer drankaeme.

    Seit dem 10.09.2026 stoesst der Verteiler an, statt zu warten
    (starter.anstossen statt starter.starten). Die Attrappe deckt beide
    Wege ab: der alte darf nicht spurlos verschwinden, sonst faellt
    niemandem auf, wenn ihn jemand wieder einbaut.
    """
    echt_starten = verteiler.starter.starten
    echt_anstossen = verteiler.starter.anstossen
    gestartet = []

    class Lauf:
        def __init__(self):
            self.gelaufen = gelaufen
            self.dauer = 0.4
            self.grund = grund
            self.ausgabe = ""

    class Anstoss:
        def __init__(self):
            self.agent = ""
            self.gestartet = gelaufen
            self.schon_da = False
            self.pid = 4242 if gelaufen else 0
            self.grund = grund

    def falsch_starten(agent, *argumente, **rest):
        gestartet.append((agent, argumente))
        return Lauf()

    def falsch_anstossen(agent, *argumente, **rest):
        gestartet.append((agent, argumente))
        return Anstoss()

    verteiler.starter.starten = falsch_starten
    verteiler.starter.anstossen = falsch_anstossen
    try:
        yield gestartet
    finally:
        verteiler.starter.starten = echt_starten
        verteiler.starter.anstossen = echt_anstossen


# ================================================================== Tabellen

@anmelden("vernetzung.arten-stimmen-mit-der-app", "kalender",
          "Die Auftragsarten sind in App und Sekretaer dieselben", TROCKEN,
          "dass die App etwas anbietet, das der Sekretaer auch verteilen kann",
          blind_fuer="Aenderungen, die in beiden Dateien gleich falsch sind")
def arten_stimmen_mit_der_app():
    """Auftrag.kt und auftragsarten.json sind zwei Kopien derselben
    Tabelle - die App braucht sie zur Anzeige, der Sekretaer zum
    Verteilen. Laufen sie auseinander, bietet die App eine Art an, mit
    der niemand etwas anfangen kann."""
    import re

    kt = (UNIVERSE / "app" / "repocity" / "app" / "src" / "main" / "java" /
          "dev" / "speedofthespirit" / "repocity" / "kern" / "Auftrag.kt")
    if not kt.exists():
        raise AssertionError("Auftrag.kt nicht gefunden: %s" % kt)
    aus_kotlin = dict(re.findall(
        r'^\s*([A-Z_]+)\("([^"]+)",\s*"([^"]+)"\),?\s*;?\s*$',
        kt.read_text(encoding="utf-8"), re.M) and
        [(k, m) for k, _l, m in re.findall(
            r'^\s*([A-Z_]+)\("([^"]+)",\s*"([^"]+)"\)',
            kt.read_text(encoding="utf-8"), re.M)])

    arten, _ = verteiler.tabellen()
    aus_json = {k: a["modul"] for k, a in arten.items()}

    fehlt_json = sorted(set(aus_kotlin) - set(aus_json))
    fehlt_kt = sorted(set(aus_json) - set(aus_kotlin))
    anders = sorted(k for k in set(aus_kotlin) & set(aus_json)
                    if aus_kotlin[k] != aus_json[k])
    if fehlt_json or fehlt_kt or anders:
        raise AssertionError(
            "in der App, nicht beim Sekretaer: %s; beim Sekretaer, nicht in "
            "der App: %s; verschiedene Module: %s"
            % (fehlt_json or "-", fehlt_kt or "-", anders or "-"))
    return "%d Auftragsarten, in App und Sekretaer identisch" % len(aus_json)


@anmelden("vernetzung.regler-stimmen-mit-der-app", "kalender",
          "Die Laengenregler sind in App und Sekretaer dieselben", TROCKEN,
          "dass der Regler auf dem Handy dasselbe hergibt wie die Bestellung",
          blind_fuer="Grenzen, die in beiden Dateien gleich falsch sind")
def regler_stimmen_mit_der_app():
    """Laenge.kt und auftragsarten.json sind zwei Kopien derselben
    Tabelle - die App braucht sie zum Anzeigen, laenge.py zum Messen.
    Laufen sie auseinander, bestellt der Nutzer 30 Minuten und der
    Qualitaetsmanager misst gegen 20."""
    import re

    kt = (UNIVERSE / "app" / "repocity" / "app" / "src" / "main" / "java" /
          "dev" / "speedofthespirit" / "repocity" / "kern" / "Laenge.kt")
    if not kt.exists():
        raise AssertionError("Laenge.kt nicht gefunden: %s" % kt)
    quelle = kt.read_text(encoding="utf-8")

    # Jeder Eintrag der Tabelle: "prod.video.clip" to Regler( ... ),
    # bis zur schliessenden Klammer, die allein auf ihrer Zeile steht.
    bloecke = re.findall(r'"([a-z][a-z0-9.]*)" to Regler\((.*?)\n        \)',
                         quelle, re.S)
    if not bloecke:
        raise AssertionError("in Laenge.kt keinen einzigen Regler gefunden - "
                             "entweder ist die Tabelle leer oder anders "
                             "geschrieben als hier gesucht")

    def zahl(text, feld):
        t = re.search(r'\b%s = (\d+)' % feld, text)
        return int(t.group(1)) if t else None

    def flagge(text, feld):
        return bool(re.search(r'\b%s = true' % feld, text))

    aus_kotlin = {}
    for modul, block in bloecke:
        aus_kotlin[modul] = {
            "von": zahl(block, "von"),
            "bis": zahl(block, "bis"),
            "schritt": zahl(block, "schritt"),
            "voreinstellung": zahl(block, "voreinstellung"),
            "kosten_sichtbar": flagge(block, "kostenSichtbar"),
            "vortragsdauer": flagge(block, "vortragsdauer"),
        }

    aus_json = {}
    for modul, r in laenge.alle_regler().items():
        aus_json[modul] = {
            "von": int(r["von"]),
            "bis": int(r["bis"]),
            "schritt": int(r["schritt"]),
            "voreinstellung": int(r["voreinstellung"]),
            "kosten_sichtbar": bool(r.get("kosten_sichtbar")),
            "vortragsdauer": r.get("art") == "vortragsdauer",
        }

    fehlt_json = sorted(set(aus_kotlin) - set(aus_json))
    fehlt_kt = sorted(set(aus_json) - set(aus_kotlin))
    anders = sorted(k for k in set(aus_kotlin) & set(aus_json)
                    if aus_kotlin[k] != aus_json[k])
    if fehlt_json or fehlt_kt or anders:
        naeher = "; ".join(
            "%s: App %r, Sekretaer %r" % (k, aus_kotlin[k], aus_json[k])
            for k in anders)
        raise AssertionError(
            "in der App, nicht beim Sekretaer: %s; beim Sekretaer, nicht in "
            "der App: %s; verschiedene Grenzen: %s"
            % (fehlt_json or "-", fehlt_kt or "-", naeher or "-"))
    return "%d Regler, in App und Sekretaer identisch" % len(aus_json)


@anmelden("vernetzung.endbildpreis-stimmt-mit-der-app", "kalender",
          "Der Preis je Endbild ist in App und Kostenliste derselbe", TROCKEN,
          "dass der Preis auf dem Handy der gemessene ist, kein alter",
          blind_fuer="einen Preis, der in beiden Dateien gleich falsch ist")
def endbildpreis_stimmt_mit_der_app():
    """Die App zeigt vor dem Absenden, was ein Video ungefaehr kostet.
    Die Zahl dafuer steht als Konstante in Laenge.kt, weil das Handy
    ohne Netz rechnen koennen muss. Gemessen wird sie in kosten.json -
    und wenn dort ein neuer Messwert steht, muss die Konstante mit."""
    import re

    kt = (UNIVERSE / "app" / "repocity" / "app" / "src" / "main" / "java" /
          "dev" / "speedofthespirit" / "repocity" / "kern" / "Laenge.kt")
    quelle = kt.read_text(encoding="utf-8")

    t = re.search(r'ENDBILD_EUR = ([0-9.]+)', quelle)
    if not t:
        raise AssertionError("ENDBILD_EUR steht nicht in Laenge.kt")
    aus_app = float(t.group(1))

    t = re.search(r'SZENE_SEKUNDEN = ([0-9.]+)', quelle)
    if not t:
        raise AssertionError("SZENE_SEKUNDEN steht nicht in Laenge.kt")
    szene_app = float(t.group(1))

    gemessen = verbrauch.preis(laenge.ENDBILD_MODELL)
    # Die App rundet auf sechs Stellen - mehr zeigt sie ohnehin nie an.
    if round(aus_app, 6) != round(gemessen, 6):
        raise AssertionError(
            "App rechnet mit %.6f EUR je Endbild, gemessen sind %.6f EUR "
            "(%s aus kosten.json). Konstante in Laenge.kt nachziehen."
            % (aus_app, gemessen, laenge.ENDBILD_MODELL))
    if szene_app != laenge.SZENE_SEKUNDEN:
        raise AssertionError(
            "App rechnet mit %.1f Sekunden je Szene, laenge.py mit %.1f"
            % (szene_app, laenge.SZENE_SEKUNDEN))
    return ("%.6f EUR je Endbild und %.0f Sekunden je Szene, in App und "
            "Kostenliste identisch" % (gemessen, szene_app))


@anmelden("vernetzung.jeder-agent-existiert", "kalender",
          "Jeder genannte Agent gibt es auch", TROCKEN,
          "dass der Verteiler niemanden anspricht, den es nicht gibt")
def jeder_agent_existiert():
    _, wer = verteiler.tabellen()
    fehlt = [(modul, s["agent"]) for modul, s in wer.items()
             if not (UNIVERSE / s["agent"] / "main.py").exists()]
    if fehlt:
        raise AssertionError("kein main.py fuer: "
                             + ", ".join("%s -> %s" % p for p in fehlt))
    return "%d Module, jedes mit einem Agenten, den es gibt" % len(wer)


# ================================================================== Verteilen

@anmelden("vernetzung.auftrag-erreicht-den-agenten", "kalender",
          "Ein Auftrag wird dem richtigen Agenten zugestellt", TROCKEN,
          "dass aus einem Auftrag vom Handy wirklich Arbeit wird")
def auftrag_erreicht_den_agenten():
    auftrag = {"id": "auftrag:probe1", "art": "VIDEO_CLIP",
               "text": "Ein Probeclip", "trocken": True}
    with hub_doppel([auftrag]) as doppel, starter_doppel() as gestartet:
        ergebnisse = verteiler.alle_verteilen()
        _gleich(len(ergebnisse), 1, "ein Auftrag verteilt")
        _gleich(ergebnisse[0]["agent"], "video_agent", "richtiger Agent")
        _gleich(gestartet[0][0], "video_agent", "wirklich gestartet")
        zustaende = [m["zustand"] for m in doppel.gemeldet]
        if "angenommen" not in zustaende:
            raise AssertionError("der Hub erfuhr nicht, dass es losging")
        return "VIDEO_CLIP an den video_agent, Zustand an den Hub gemeldet"


@anmelden("vernetzung.auftrag-per-beschriftung", "kalender",
          "Auch die Beschriftung aus der App wird verstanden", TROCKEN,
          "dass die App keine Kennungen kennen muss")
def auftrag_per_beschriftung():
    auftrag = {"id": "auftrag:probe2", "art": "Kurze einfache Clips",
               "text": "x", "trocken": True}
    with hub_doppel([auftrag]), starter_doppel() as gestartet:
        ergebnisse = verteiler.alle_verteilen()
        _gleich(ergebnisse[0]["modul"], "prod.video.clip", "Modul erkannt")
        _gleich(gestartet[0][0], "video_agent", "Agent gestartet")
        return "'Kurze einfache Clips' als prod.video.clip erkannt"


@anmelden("vernetzung.ohne-agent-gibt-es-absage", "kalender",
          "Ein Auftrag ohne Agenten wird abgelehnt, nicht liegengelassen",
          TROCKEN,
          "dass niemand auf ein Ergebnis wartet, das nie kommt")
def ohne_agent_gibt_es_absage():
    """Die Luecke wird hier selbst hergestellt.

    Frueher stand hier die Praesentation als Beispiel fuer ein Modul ohne
    Agenten. Seit der Gestalter gebaut ist, gibt es kein solches Modul
    mehr - und die Pruefung fiel durch, obwohl der Verteiler richtig
    arbeitet.
    """
    auftrag = {"id": "auftrag:probe3", "art": "PRAESENTATION", "text": "x"}
    arten, wer = verteiler.tabellen()
    ohne = {k: v for k, v in wer.items() if k != "prod.praesentation"}
    echt = verteiler.tabellen
    verteiler.tabellen = lambda: (arten, ohne)
    try:
        return _absage_pruefen(auftrag)
    finally:
        verteiler.tabellen = echt


def _absage_pruefen(auftrag):
    with hub_doppel([auftrag]) as doppel, starter_doppel() as gestartet:
        ergebnisse = verteiler.alle_verteilen()
        _gleich(ergebnisse[0]["ergebnis"], "abgelehnt", "abgelehnt")
        _gleich(gestartet, [], "nichts gestartet")
        letzte = doppel.letzter()
        _gleich(letzte["zustand"], "abgebrochen", "Zustand beim Hub")
        if "kein" not in letzte["rueckmeldung"].lower():
            raise AssertionError("die Absage sagt nicht, warum")
        return "Praesentation abgelehnt, mit Begruendung, nichts gestartet"


@anmelden("vernetzung.unbekannte-art-wird-abgelehnt", "kalender",
          "Eine unbekannte Auftragsart wird abgelehnt", TROCKEN,
          "dass ein Tippfehler nicht als stiller Ausfall endet")
def unbekannte_art_wird_abgelehnt():
    with hub_doppel([{"id": "auftrag:x", "art": "Katzenvideo", "text": "x"}]) \
            as doppel, starter_doppel() as gestartet:
        ergebnisse = verteiler.alle_verteilen()
        _gleich(ergebnisse[0]["ergebnis"], "abgelehnt", "abgelehnt")
        _gleich(gestartet, [], "nichts gestartet")
        if "kenne ich nicht" not in doppel.letzter()["rueckmeldung"]:
            raise AssertionError("die Absage nennt den Grund nicht")
        return "unbekannte Art abgelehnt, bekannte Arten aufgezaehlt"


@anmelden("vernetzung.fehlschlag-wird-gemeldet", "kalender",
          "Eine Werkstatt, die nicht anlaeuft, wird dem Hub gemeldet", TROCKEN,
          "dass ein Auftrag nicht stumm liegenbleibt, wenn ihn niemand annimmt",
          blind_fuer="einen Fehler, den die Werkstatt erst beim Arbeiten "
                     "macht - den meldet sie selbst")
def fehlschlag_wird_gemeldet():
    """Was hier ein Fehlschlag ist, hat sich am 10.09.2026 geaendert.

    Vorher wartete der Sekretaer bis zum Ende und las den Rueckgabewert.
    Eine Werkstatt, die drei Auftraege abarbeitet und beim dritten
    stolpert, liess damit auch die ersten beiden rot dastehen - genau so
    ist ein fertiges Video rot geworden. Jetzt urteilt er nur ueber das,
    was seine Sache ist: ob die Werkstatt ueberhaupt anlaeuft.
    """
    auftrag = {"id": "auftrag:probe4", "art": "VIDEO_CLIP", "text": "x"}
    with hub_doppel([auftrag]) as doppel, \
            starter_doppel(gelaufen=False, grund="main.py gibt es nicht"):
        ergebnisse = verteiler.alle_verteilen()
        _gleich(ergebnisse[0]["ergebnis"], "nicht angestossen", "Ergebnis")
        _gleich(doppel.letzter()["zustand"], "fehler", "Zustand beim Hub")
        if "main.py" not in doppel.letzter()["rueckmeldung"]:
            raise AssertionError("die Meldung sagt nicht, woran es lag")
        return "Werkstatt lief nicht an - als 'fehler' gemeldet, mit Grund"


@anmelden("vernetzung.sekretaer-wartet-nicht-auf-die-werkstatt", "kalender",
          "Der Sekretaer uebergibt und geht weiter", TROCKEN,
          "dass ein langer Lauf nicht alles andere anhaelt - und dass kein "
          "Rueckgabewert einer Werkstatt ueber fremde Auftraege entscheidet")
def sekretaer_wartet_nicht():
    """Am 10.09.2026 wurde ein fertiges Video rot, weil die Werkstatt
    danach ueber eine Karteileiche stolperte und der Sekretaer deren
    Rueckgabewert auf den fertigen Auftrag schrieb. Seither ruft er
    starter.starten() gar nicht mehr an dieser Stelle. Diese Pruefung
    wird rot, sobald es jemand wieder einbaut.
    """
    auftrag = {"id": "auftrag:probe6", "art": "VIDEO_CLIP", "text": "x",
               "trocken": True}

    def darf_nicht(*a, **k):
        raise AssertionError("der Sekretaer wartet wieder auf die Werkstatt")

    with hub_doppel([auftrag]) as doppel, starter_doppel() as gestartet:
        verteiler.starter.starten = darf_nicht
        ergebnisse = verteiler.alle_verteilen()

    _gleich(ergebnisse[0]["ergebnis"], "uebergeben", "Ergebnis")
    _gleich(gestartet[0][0], "video_agent", "angestossen")
    _gleich(doppel.letzter()["zustand"], "laeuft", "Zustand beim Hub")
    return "uebergeben statt gewartet - starten() wird hier nicht mehr gerufen"


@anmelden("vernetzung.auftrag-landet-im-eingang", "kalender",
          "Der Auftrag liegt danach im Eingang des Agenten", TROCKEN,
          "dass der Agent den Auftrag findet, ohne dass wir ihn umbauen")
def auftrag_landet_im_eingang():
    import shutil
    import tempfile

    auftrag = {"id": "auftrag:probe5", "art": "VIDEO_CLIP",
               "text": "Warum Agenten sich pruefen", "trocken": True}
    ordner = Path(tempfile.mkdtemp(prefix="eingang_"))
    echt = verteiler.ZUSTAND
    verteiler.ZUSTAND = ordner
    try:
        with hub_doppel([auftrag]), starter_doppel():
            verteiler.alle_verteilen()
        dateien = list((ordner / "video_eingang").glob("*.json"))
        _gleich(len(dateien), 1, "eine Datei im Eingang")
        satz = json.loads(dateien[0].read_text(encoding="utf-8"))
        _gleich(satz["thema"], "Warum Agenten sich pruefen", "Thema")
        _gleich(satz["modul"], "prod.video.clip", "Modul")
        _gleich(satz["trocken"], True, "Trockenlauf uebernommen")
        return "Auftrag als JSON im video_eingang, mit Thema und Modul"
    finally:
        verteiler.ZUSTAND = echt
        shutil.rmtree(ordner, ignore_errors=True)


# ================================================================== Rueckfrage

@contextmanager
def _zustand_in_tempordner():
    import shutil
    import tempfile

    ordner = Path(tempfile.mkdtemp(prefix="rueckfrage_"))
    echt = verteiler.ZUSTAND
    verteiler.ZUSTAND = ordner
    try:
        yield ordner
    finally:
        verteiler.ZUSTAND = echt
        shutil.rmtree(ordner, ignore_errors=True)


@anmelden("vernetzung.leerer-auftrag-wird-gefragt", "kalender",
          "Ein Auftrag ohne ein Wort wird gefragt, nicht gebaut", TROCKEN,
          "dass die Strasse nicht ueber ein Thema raet, das nie gemeint war",
          blind_fuer="Unklarheiten, die nur das Modell sieht - das laeuft hier nicht")
def leerer_auftrag_wird_gefragt():
    auftrag = {"id": "auftrag:probe7", "art": "VIDEO_CLIP", "text": "",
               "trocken": True, "nutzer": "daniel"}
    with _zustand_in_tempordner() as ordner, hub_doppel([auftrag]) as doppel, \
            starter_doppel() as gestartet:
        ergebnisse = verteiler.alle_verteilen()
        _gleich(ergebnisse[0]["ergebnis"], "rueckfrage", "Ergebnis")
        _gleich(gestartet, [], "nichts gestartet")
        _gleich(len(doppel.meldungen_hinein), 1, "eine Meldung ins Fach")
        m = doppel.meldungen_hinein[0]
        _gleich(m["art"], "rueckfrage", "Meldungsart")
        _gleich(m["nutzer"], "daniel", "ins Fach des Auftraggebers")
        _gleich(m["vorgang"], "auftrag:probe7", "Vorgang ist der Auftrag")
        if "?" not in m["text"]:
            raise AssertionError("die Rueckfrage enthaelt keine Frage")
        _gleich(doppel.letzter()["zustand"], "rueckfrage", "Zustand beim Hub")
        _gleich(len(list((ordner / "rueckfragen").glob("*.json"))), 1, "Merkzettel")
        return "leerer Auftrag: Rueckfrage ins Fach, Auftrag wartet, nichts gestartet"


@anmelden("vernetzung.antwort-laesst-den-auftrag-laufen", "kalender",
          "Die Antwort auf eine Rueckfrage bringt den Auftrag in die Strasse", TROCKEN,
          "dass ein beantworteter Auftrag nicht ewig auf 'rueckfrage' steht")
def antwort_laesst_den_auftrag_laufen():
    wartend = [{"id": "auftrag:probe8", "art": "VIDEO_CLIP", "text": "",
                "trocken": True, "nutzer": "daniel", "zustand": "rueckfrage"},
               {"id": "auftrag:probe9", "art": "VIDEO_CLIP", "text": "",
                "trocken": True, "nutzer": "daniel", "zustand": "rueckfrage"}]
    antworten = [{"id": "meldung:1", "art": "rueckfrage", "vorgang": "auftrag:probe8",
                  "entscheidung": "ja", "grund": "Ein Clip ueber Bienen im Garten",
                  "daten": {"fragen": ["Worum soll es gehen?"], "annahmen": []}},
                 {"id": "meldung:2", "art": "rueckfrage", "vorgang": "auftrag:probe9",
                  "entscheidung": "nein", "grund": "war ein Versehen"},
                 {"id": "meldung:3", "art": "freigabe", "vorgang": "auftrag:probe8",
                  "entscheidung": "nein", "grund": "gehoert nicht hierher"}]
    with _zustand_in_tempordner() as ordner, \
            hub_doppel(wartend=wartend, antworten=antworten) as doppel, \
            starter_doppel() as gestartet:
        ergebnisse = verteiler.alle_verteilen()
        nach = {e["kennung"]: e for e in ergebnisse}
        _gleich(nach["auftrag:probe8"]["ergebnis"], "uebergeben", "Ja: uebergeben")
        _gleich(nach["auftrag:probe9"]["ergebnis"], "abgelehnt", "Nein: abgesagt")
        _gleich([g[0] for g in gestartet], ["video_agent"], "genau einer gestartet")
        datei = next((ordner / "video_eingang").glob("*probe8*.json"))
        satz = json.loads(datei.read_text(encoding="utf-8"))
        if "Bienen" not in satz["text"] or "Worum soll es gehen" not in satz["text"]:
            raise AssertionError("Frage und Antwort stehen nicht im Auftragstext: %r" % satz["text"])
        _gleich(len(doppel.meldungen_hinein), 0, "nicht noch einmal gefragt")
        return "Ja mit Antwort -> laeuft mit Frage und Antwort im Text; Nein -> abgesagt"


# ================================================================== Zeitplan

@anmelden("zeitplan.faellig-nur-was-dran-ist", "kalender",
          "Nur was seinen Takt erreicht hat, wird faellig", TROCKEN,
          "dass nicht jeder Aufruf alles startet")
def faellig_nur_was_dran_ist():
    import shutil
    import tempfile

    ordner = Path(tempfile.mkdtemp(prefix="zeitplan_"))
    echt_plan, echt_stand = zeitplan.PLANDATEI, zeitplan.STANDDATEI
    zeitplan.PLANDATEI = ordner / "zeitplan.json"
    zeitplan.STANDDATEI = ordner / "stand.json"
    try:
        zeitplan.PLANDATEI.write_text(json.dumps({"eintraege": {
            "oft": {"agent": "a", "befehl": "x", "alle_minuten": 5},
            "selten": {"agent": "b", "befehl": "x", "alle_minuten": 1440},
            "aus": {"agent": "c", "befehl": "x", "alle_minuten": 5, "an": False},
        }}), encoding="utf-8", newline="")

        jetzt = datetime(2026, 9, 6, 12, 0)
        namen = sorted(n for n, _ in zeitplan.faellig(jetzt))
        _gleich(namen, ["oft", "selten"],
                "beim ersten Mal alles ausser dem Ausgeschalteten")

        zeitplan.STANDDATEI.write_text(json.dumps({
            "oft": {"zuletzt": (jetzt - timedelta(minutes=10)).isoformat()},
            "selten": {"zuletzt": (jetzt - timedelta(minutes=10)).isoformat()},
        }), encoding="utf-8", newline="")
        namen = sorted(n for n, _ in zeitplan.faellig(jetzt))
        _gleich(namen, ["oft"], "nach 10 Minuten nur der Fuenf-Minuten-Takt")
        return "Takt beachtet, Ausgeschaltetes bleibt aus"
    finally:
        zeitplan.PLANDATEI, zeitplan.STANDDATEI = echt_plan, echt_stand
        shutil.rmtree(ordner, ignore_errors=True)


@anmelden("zeitplan.eintraege-zeigen-auf-echte-agenten", "kalender",
          "Jeder Eintrag im Zeitplan meint einen Agenten, den es gibt",
          TROCKEN,
          "dass der Zeitplan nicht ins Leere laeuft")
def eintraege_zeigen_auf_echte_agenten():
    fehlt = []
    for name, eintrag in zeitplan.plan().items():
        agent = eintrag.get("agent", "")
        datei = eintrag.get("datei", "main.py")
        if not (UNIVERSE / agent / datei).exists():
            fehlt.append("%s -> %s/%s" % (name, agent, datei))
    if fehlt:
        raise AssertionError("; ".join(fehlt))
    return "%d Eintraege, jeder zeigt auf eine Datei, die es gibt" % len(
        zeitplan.plan())
