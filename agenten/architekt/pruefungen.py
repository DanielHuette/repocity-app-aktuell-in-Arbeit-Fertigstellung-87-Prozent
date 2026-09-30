"""Pruefungen des Architekten. Alles trocken, alles kostenlos, kein Netz.

Der Architekt plant, er baut nicht. Geprueft wird darum, was ein Bauplan
zusagt: dass ohne Modell keine Datei erfunden wird, dass eine Hub-Kennung
mit Doppelpunkt einen Ordner bekommt, den Windows auch anlegt, dass die
Antwort des Modells auch mit Zaun herum noch gelesen wird, und dass der
fertige Plan die vier Stuecke nennt, aus denen er besteht.

Geschrieben wird nur in ein Wegwerf-Verzeichnis; universe/zustand/bau
wird nie angefasst.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

entwurf = laden(HIER / "entwurf.py", "architekt_entwurf")

#: Dieselbe Kennung, unter der er meldet und bucht (siehe auftragsarten.json).
MODUL = entwurf.MODUL


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


@contextmanager
def wegwerf_bauplatz():
    """Plaene landen in einem Wegwerf-Verzeichnis, nicht im Universe.

    Das Vorwissen wird dabei festgelegt, damit die Pruefung nicht davon
    abhaengt, was zufaellig gerade im Vault steht.
    """
    ordner = Path(tempfile.mkdtemp(prefix="architekt_"))
    echt_universe = entwurf.UNIVERSE
    echt_vorwissen = entwurf._vorwissen
    entwurf.UNIVERSE = ordner
    entwurf._vorwissen = lambda: "Beim letzten Mal fehlte die Pruefung."
    try:
        yield ordner
    finally:
        entwurf.UNIVERSE = echt_universe
        entwurf._vorwissen = echt_vorwissen
        shutil.rmtree(ordner, ignore_errors=True)


@contextmanager
def modell_gesperrt():
    """Wer hier ein Modell fragt, faellt durch - trocken heisst trocken."""
    echt = entwurf._durch_modell

    def nicht(*_a, **_k):
        raise AssertionError("es wurde ein Modell gefragt, obwohl niemand fragen darf")

    entwurf._durch_modell = nicht
    try:
        yield
    finally:
        entwurf._durch_modell = echt


# ================================================================== Notplan

@anmelden("prod.app.ohne-modell-keine-erfundene-datei", MODUL,
          "Ohne Modell nennt der Plan keine Datei und sagt das auch", TROCKEN,
          "dass kein Bauplan Dateinamen erfindet, die niemand geprueft hat",
          blind_fuer="ob ein Plan mit Modell brauchbare Dateien nennt")
def ohne_modell_keine_erfundene_datei():
    with wegwerf_bauplatz(), modell_gesperrt():
        plan = entwurf.entwerfen(
            {"id": "B1", "text": "Der Verteiler soll Auftraege nach Modul sortieren."},
            mit_modell=False)
        _gleich(plan.mit_modell, False, "ohne Modell entstanden")
        _gleich(plan.kosten, 0.0, "hat nichts gekostet")
        _gleich([d["pfad"] for d in plan.dateien], ["(offen)"], "genannte Dateien")
        if not any("ohne Modell" in r for r in plan.risiken):
            raise AssertionError("der Plan sagt nicht, dass er ohne Modell entstand")
        if not any("pruefstand" in p.lower() for p in plan.pruefungen):
            raise AssertionError("der Notplan verlangt keinen Pruefstandlauf")
        return "Notplan nennt '(offen)' statt erfundener Dateien und benennt sein Manko"


# ================================================================== Ordnername

@anmelden("prod.app.doppelpunkt-wird-entschaerft", MODUL,
          "Eine Hub-Kennung mit Doppelpunkt bekommt einen Ordner, den es gibt",
          TROCKEN,
          "dass ein Bauplan nicht spurlos in einem Windows-Datenstrom verschwindet")
def doppelpunkt_wird_entschaerft():
    """Windows deutet den Doppelpunkt als Trenner zu einem versteckten
    Datenstrom. Derselbe Fund wie beim Verteiler."""
    with wegwerf_bauplatz(), modell_gesperrt():
        kennung = "auftrag:2026-09-06T12:00"
        ziel = entwurf.ordner(kennung)
        if ":" in ziel.name:
            raise AssertionError("im Ordnernamen steht noch ein Doppelpunkt: " + ziel.name)

        plan = entwurf.entwerfen({"id": kennung, "text": "Kleiner Umbau."},
                                 mit_modell=False)
        datei = entwurf.speichern(plan)
        if not datei.exists():
            raise AssertionError("die Datei wurde nicht angelegt: %s" % datei)

        zurueck = entwurf.laden(kennung)
        if zurueck is None:
            raise AssertionError("der gespeicherte Plan liess sich nicht wiederfinden")
        _gleich(zurueck.auftrag, kennung, "Kennung nach dem Wiederlesen")
        return "'%s' wird zu '%s' - angelegt und wiedergefunden" % (kennung, ziel.name)


# ================================================================== Antwortform

@anmelden("prod.app.json-aus-der-antwort", MODUL,
          "Das JSON wird auch mit Zaun oder Vorrede herausgeholt", TROCKEN,
          "dass ein Plan nicht daran scheitert, wie das Modell sein JSON verpackt")
def json_aus_der_antwort():
    mit_zaun = '```json\n{"ziel": "a", "dateien": []}\n```'
    _gleich(entwurf._json_heraus(mit_zaun), {"ziel": "a", "dateien": []},
            "mit Zaun")
    mit_vorrede = 'Gern! Hier der Plan:\n{"ziel": "b"}\nViel Erfolg.'
    _gleich(entwurf._json_heraus(mit_vorrede), {"ziel": "b"}, "mit Vorrede")
    _gleich(entwurf._json_heraus("gar kein JSON"), None, "ohne JSON")
    _gleich(entwurf._json_heraus("{kaputt,,}"), None, "kaputtes JSON")
    return "Zaun und Vorrede werden abgeraeumt, Unlesbares gibt ehrlich None"


# ================================================================== Der Plan

@anmelden("prod.app.plan-nennt-die-vier-stuecke", MODUL,
          "Jeder Bauplan nennt Ziel, Dateien, Pruefungen und Risiken", TROCKEN,
          "dass ein Plan lesbar ist und sagt, dass er selbst nichts baut",
          blind_fuer="ob der Inhalt der vier Stuecke etwas taugt")
def plan_nennt_die_vier_stuecke():
    with wegwerf_bauplatz(), modell_gesperrt():
        plan = entwurf.entwerfen({"id": "B2", "text": "Zweiter Umbau."},
                                 mit_modell=False)
        text = entwurf.als_markdown(plan)
        for muss in ("## Ziel", "## Dateien", "## Pruefungen", "## Risiken",
                     "modul: " + MODUL, "kosten_eur: 0.0000",
                     "Beim letzten Mal fehlte die Pruefung."):
            if muss not in text:
                raise AssertionError("im Bauplan fehlt: " + muss)
        if "baut nichts" not in text:
            raise AssertionError("der Plan sagt nicht, dass er nichts baut")
        return ("vier Abschnitte, Modulkennung %s, Kosten und der Satz, "
                "dass erst deine Freigabe kommt" % MODUL)

# Aufraeumen: diesen Ordner aus dem Suchpfad nehmen. Er enthaelt Dateien, die
# es im Universe mehrfach gibt; bleibt er vorn im Suchpfad, holt sich ein
# spaeter geladener Agent unsere Fassung statt seiner eigenen.
while str(HIER) in sys.path:
    sys.path.remove(str(HIER))
