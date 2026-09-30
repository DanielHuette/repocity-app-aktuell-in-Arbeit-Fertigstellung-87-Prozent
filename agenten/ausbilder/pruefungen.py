"""Pruefungen des Ausbilders. Alles trocken, alles kostenlos, kein Netz.

Der Ausbilder liest abgelegte Erfahrungen und schlaegt daraus Lehrsaetze
vor. Geprueft wird genau die Kette, auf der das ganze Lernen beruht:
Erfahrung -> Schwelle -> Vorschlag -> dein Ja -> Vorwissen des Agenten.

Jede Pruefung laeuft in einem Wegwerf-Vault. Der echte vault wird nie
angefasst - ein Pruefstandlauf, der einen erfundenen Lehrsatz ins echte
Gedaechtnis schreibt, waere schlimmer als gar keine Pruefung.
"""
from __future__ import annotations

import json
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

import rueckweg  # noqa: E402

# main.py gibt es zwoelfmal im Universe - darum ueber laden() mit eigenem Namen.
ausbilder = laden(HIER / "main.py", "ausbilder_main")

#: Dieselbe Kennung, unter der er meldet und bucht (siehe auftragsarten.json).
MODUL = ausbilder.MODUL


@contextmanager
def wegwerf_vault():
    """Vault, Vektorschicht und Meldeweg abklemmen.

    rueckweg holt seine Pfade aus universe/gehirn.json. Hier zeigt diese
    Datei auf ein Wegwerf-Verzeichnis, das am Ende geloescht wird. Die
    Vektorschicht wird stillgelegt, weil eine Einbettung Netz und Geld
    kostet; der Meldeweg, weil eine Pruefung nichts an den Hub melden soll.
    """
    ordner = Path(tempfile.mkdtemp(prefix="ausbilder_"))
    (ordner / "gehirn.json").write_text(
        json.dumps({"vault": str(ordner / "vault"),
                    "vektor": str(ordner / "chroma")}), encoding="utf-8", newline="")
    echt_pfad = rueckweg.PFADDATEI
    echt_vektor = rueckweg._vektor
    echt_meldung = ausbilder.meldung
    rueckweg.PFADDATEI = ordner / "gehirn.json"
    rueckweg._vektor = None
    ausbilder.meldung = None
    try:
        yield ordner
    finally:
        rueckweg.PFADDATEI = echt_pfad
        rueckweg._vektor = echt_vektor
        ausbilder.meldung = echt_meldung
        shutil.rmtree(ordner, ignore_errors=True)


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


def _neins(anzahl: int, grund: str, ab: int = 1) -> None:
    """So viele gleichartige Neins ablegen, wie genannt."""
    for nummer in range(ab, ab + anzahl):
        rueckweg.erfahrung_ablegen(
            auftrag="A%03d" % nummer, modul=MODUL,
            was_versucht="ein Stueck fuer die Pruefung",
            urteil="nein", grund=grund)


def _vorschlaege() -> list:
    return rueckweg.lehrsaetze(None, "vorschlag")


# ================================================================== Schwelle

@anmelden("ausbildung.schwelle-haelt", MODUL,
          "Aus zwei gleichen Neins wird keine Regel, aus dreien eine", TROCKEN,
          "dass eine einzelne Ruege nie zur Dauerregel wird",
          blind_fuer="ob der vorgeschlagene Satz inhaltlich taugt")
def schwelle_haelt():
    """Ohne Schwelle bekommt man einen Agenten voller Aberglauben: einmal
    ein Nein fuer eine Kleinigkeit kassiert und die Sache fortan gemieden.
    Die Schwelle steht in rueckweg.SCHWELLE."""
    with wegwerf_vault():
        _neins(2, "Der Aufhaenger ist zu lang geraten.")
        ausbilder.befehl_sichten([MODUL], formulieren=False, genau=False)
        _gleich(len(_vorschlaege()), 0, "nach zwei Neins")

        _neins(1, "Der Aufhaenger ist zu lang geraten.", ab=3)
        ausbilder.befehl_sichten([MODUL], formulieren=False, genau=False)
        _gleich(len(_vorschlaege()), 1, "nach drei Neins")
        return ("bei %d gleichen Neins entsteht der erste Vorschlag, vorher keiner"
                % rueckweg.SCHWELLE)


@anmelden("ausbildung.kein-doppelter-vorschlag", MODUL,
          "Derselbe Haufen wird kein zweites Mal vorgeschlagen", TROCKEN,
          "dass ein zweiter Durchgang keine Doppelung anlegt")
def kein_doppelter_vorschlag():
    with wegwerf_vault():
        _neins(3, "Die Musik uebertoent die Stimme.")
        ausbilder.befehl_sichten([MODUL], formulieren=False, genau=False)
        ausbilder.befehl_sichten([MODUL], formulieren=False, genau=False)
        ausbilder.befehl_sichten([MODUL], formulieren=False, genau=False)
        _gleich(len(_vorschlaege()), 1, "nach drei Durchgaengen")
        return "drei Durchgaenge, ein Vorschlag - der Haufen gilt als behandelt"


# ================================================================== Nein mit Grund

@anmelden("ausbildung.nein-ohne-grund-wird-abgewiesen", MODUL,
          "Ein Nein ohne Begruendung wird nicht angenommen", TROCKEN,
          "dass jedes Nein etwas lehrt, statt nur zu missfallen")
def nein_ohne_grund_wird_abgewiesen():
    with wegwerf_vault():
        try:
            rueckweg.erfahrung_ablegen(auftrag="A900", modul=MODUL,
                                       was_versucht="Probe",
                                       urteil="nein", grund="   ")
        except ValueError:
            pass
        else:
            raise AssertionError("ein Nein ohne Grund wurde angenommen")

        _neins(3, "Der Ton ist zu leise gegenueber der Musik.")
        ausbilder.befehl_sichten([MODUL], formulieren=False, genau=False)
        kennung = _vorschlaege()[0]["kennung"]

        _gleich(ausbilder.befehl_ablehnen(kennung, "   "), 2,
                "Ablehnen ohne Grund")
        _gleich(_vorschlaege()[0]["kennung"], kennung,
                "der Vorschlag steht unveraendert da")
        return ("Erfahrung und Ablehnung verlangen beide einen Grund - "
                "ohne Grund aendert sich nichts")


# ================================================================== Wirkung

@anmelden("ausbildung.bestaetigter-satz-steht-in-der-anweisung", MODUL,
          "Was du bestaetigst, bekommt der Agent beim naechsten Mal mit",
          TROCKEN,
          "die Stelle, an der das 2nd Brain zum ersten Mal etwas tut, "
          "statt nur zu lagern",
          blind_fuer="ob der Agent sich dann auch daran haelt")
def bestaetigter_satz_steht_in_der_anweisung():
    with wegwerf_vault():
        _neins(3, "Die Quelle fehlt in der Notiz.")
        ausbilder.befehl_sichten([MODUL], formulieren=False, genau=False)
        kennung = _vorschlaege()[0]["kennung"]

        # Solange nur vorgeschlagen, gibt es den Block mit den geltenden
        # Lehrsaetzen gar nicht. Die Erfahrungen selbst stehen schon da -
        # sie sind Vergangenheit, kein Gebot.
        if "Geltende Lehrsaetze" in rueckweg.vorwissen(MODUL):
            raise AssertionError("ein blosser Vorschlag gilt schon als Lehrsatz")

        _gleich(ausbilder.befehl_bestaetigen(kennung), 0, "bestaetigen")
        text = rueckweg.vorwissen(MODUL)
        if "Geltende Lehrsaetze" not in text:
            raise AssertionError("der bestaetigte Lehrsatz fehlt in der Anweisung")
        if "Quelle fehlt in der Notiz" not in text:
            raise AssertionError("der Lehrsatz steht ohne seinen Inhalt da")
        if kennung not in text:
            raise AssertionError("der Lehrsatz steht ohne seine Kennung da")
        return ("%s taucht erst nach dem Ja in der Anweisung des Agenten auf"
                % kennung)

# Aufraeumen: diesen Ordner aus dem Suchpfad nehmen. Er enthaelt Dateien, die
# es im Universe mehrfach gibt; bleibt er vorn im Suchpfad, holt sich ein
# spaeter geladener Agent unsere Fassung statt seiner eigenen.
while str(HIER) in sys.path:
    sys.path.remove(str(HIER))
