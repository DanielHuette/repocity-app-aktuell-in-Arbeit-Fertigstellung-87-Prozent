"""Pruefungen der Lern-Werkstatt. Alles trocken, kostenlos, kein Netz.

Zwei Sachen tragen diese Strasse: **erst das Curriculum, dann die
Erzeugung** - und **eine einzige Datei, die man oeffnet**. Beides wird
hier geprueft, dazu die Grenze, ab der ein Medium nicht mehr eingebettet,
sondern danebengelegt wird.

Geschrieben wird nur in ein Wegwerf-Verzeichnis.
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

# Gleichnamige Dateien gibt es im Universe reihenweise: einstellungen.py
# zehnmal, gehirn.py neunmal, meldung.py elfmal. Was hier unter einem
# schlichten Namen belegt wird, muss danach wieder frei sein - sonst holt
# sich ein spaeter geladener Agent unsere Fassung statt seiner eigenen.
_belegt = {name: sys.modules.get(name) for name in ('einstellungen', 'modelle')}

# einstellungen.py und modelle.py gibt es im Universe mehrfach - vor dem
# Laden wird jeder Name ausdruecklich auf DIESEN Ordner gesetzt.
einstellungen = laden(HIER / "einstellungen.py", "einstellungen")
modelle = laden(HIER / "modelle.py", "modelle")
curriculum = laden(HIER / "curriculum.py", "lern_curriculum")
kurs = laden(HIER / "kurs.py", "lern_kurs")

#: Dieselbe Kennung, unter der er meldet (siehe auftragsarten.json).
MODUL = "prod.lernen"

#: Bis hierhin wandert ein Medium in die HTML-Datei, darueber legt es sich
#: daneben. Dieselbe Zahl wie kurs.EINBETTEN_MAX - hier noch einmal genannt,
#: damit eine Verschiebung der Grenze auffaellt statt mitzuwandern.
GRENZE = 2_500_000


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


@contextmanager
def wegwerf_ordner():
    ordner = Path(tempfile.mkdtemp(prefix="lernen_"))
    try:
        yield ordner
    finally:
        shutil.rmtree(ordner, ignore_errors=True)


@contextmanager
def modell_gesperrt():
    """Wer hier ein Modell fragt, faellt durch - trocken heisst trocken."""
    echt = curriculum._mit_modell

    def nicht(*_a, **_k):
        raise AssertionError("es wurde ein Modell gefragt, obwohl trocken gearbeitet wird")

    curriculum._mit_modell = nicht
    try:
        yield
    finally:
        curriculum._mit_modell = echt


# ================================================================== Curriculum

@anmelden("prod.lernen.trocken-fragt-kein-modell", MODUL,
          "Ein trockener Auftrag erzeugt ein Geruest, ohne ein Modell zu fragen",
          TROCKEN,
          "dass die ganze Leitung ohne Schluessel und ohne Kosten durchlaeuft")
def trocken_fragt_kein_modell():
    with modell_gesperrt():
        auftrag = modelle.Auftrag(thema="Brandschutz im Buero", level_anzahl=5,
                                  trocken=True)
        c = curriculum.entwirf(auftrag)
    _gleich(len(c.level), 5, "Anzahl der Level")
    _gleich(c.titel, "Brandschutz im Buero", "Titel")
    if "Geruest" not in c.level[0].lehrtext:
        raise AssertionError("das Geruest sagt nicht, dass es ein Geruest ist")
    text = curriculum.als_text(c)
    for muss in ("# Brandschutz im Buero", "## Level 1", "Lernziel", "Erzaehler"):
        if muss not in text:
            raise AssertionError("im Lesetext fehlt: " + muss)
    return "5 Level ohne Modellaufruf, das Geruest weist sich selbst als vorlaeufig aus"


@anmelden("prod.lernen.jedes-level-hat-eine-aufgabe", MODUL,
          "Jedes Level hat genau eine Aufgabe, und die Arten wechseln sich ab",
          TROCKEN,
          "dass es ohne geloeste Aufgabe kein Weiterkommen gibt")
def jedes_level_hat_eine_aufgabe():
    with modell_gesperrt():
        c = curriculum.entwirf(modelle.Auftrag(thema="Datenschutz", level_anzahl=6,
                                               trocken=True))
    arten = []
    for level in c.level:
        if level.aufgabe is None:
            raise AssertionError("Level %d hat keine Aufgabe" % level.nr)
        if level.aufgabe.art not in modelle.AUFGABENARTEN:
            raise AssertionError("unbekannte Aufgabenart: " + level.aufgabe.art)
        if not level.aufgabe.daten or "loesung" not in level.aufgabe.daten:
            raise AssertionError("Level %d hat eine Aufgabe ohne Loesung" % level.nr)
        if not level.aufgabe.hinweis:
            raise AssertionError("Level %d gibt bei einem Fehler keinen Hinweis"
                                 % level.nr)
        arten.append(level.aufgabe.art)
    _gleich(len(set(arten[:4])), 4, "verschiedene Arten in den ersten vier Leveln")
    _gleich(arten[4], arten[0], "danach faengt die Reihe wieder von vorn an")

    # Jede Art bringt die Daten mit, die ihre Bedienung braucht.
    noetig = {"wahl": ("antworten",), "zuordnen": ("begriffe", "faecher"),
              "regler": ("von", "bis", "toleranz"), "reihenfolge": ("schritte",)}
    for level in c.level:
        for feld in noetig[level.aufgabe.art]:
            if feld not in level.aufgabe.daten:
                raise AssertionError("der Aufgabe '%s' fehlt das Feld %s"
                                     % (level.aufgabe.art, feld))
    return ("6 Level, 6 Aufgaben, alle vier Arten kommen vor und bringen ihre "
            "Bedienfelder mit")


# ================================================================== Der Kurs

@anmelden("prod.lernen.eine-datei-die-man-oeffnet", MODUL,
          "Der ganze Kurs steht in einer einzigen HTML-Datei", TROCKEN,
          "dass niemand einen Server braucht, um die Schulung zu machen")
def eine_datei_die_man_oeffnet():
    with modell_gesperrt(), wegwerf_ordner() as ordner:
        c = curriculum.entwirf(modelle.Auftrag(thema="Erste Hilfe", level_anzahl=2,
                                               trocken=True))
        # Ein Lehrtext, der versucht, aus dem Datenblock auszubrechen.
        c.level[0].lehrtext = "Vorsicht: </script><script>boese()</script>"
        ziel = kurs.baue(c, "kurs-1", ordner / "kurs.html")

        _gleich(sorted(p.name for p in ordner.iterdir()), ["kurs.html"],
                "was neben der Datei liegt")
        html = ziel.read_text(encoding="utf-8")
        if "</script><script>boese()" in html:
            raise AssertionError("der Datenblock laesst sich von innen aufbrechen")
        if "<\\/script>" not in html:
            raise AssertionError("die schliessende Marke wurde nicht entschaerft")
        for muss in ("Erste Hilfe", "kurs-1", "Level 2"):
            if muss not in html:
                raise AssertionError("in der Kursdatei fehlt: " + muss)
        _gleich(kurs._sicher('Titel mit <b> & "Anfuehrung"'),
                "Titel mit &lt;b&gt; &amp; &quot;Anfuehrung&quot;", "Titel abgesichert")
    return ("eine Datei, kein Beiwerk; ein Lehrtext mit '</script>' kann den "
            "Datenblock nicht aufbrechen")


@anmelden("prod.lernen.grosse-medien-bleiben-daneben", MODUL,
          "Kleine Medien wandern in die Datei, grosse legen sich daneben", TROCKEN,
          "dass keine unbenutzbar grosse HTML-Datei entsteht")
def grosse_medien_bleiben_daneben():
    """Geprueft wird auf beiden Seiten der Grenze: 1 KB wird eingebettet,
    ein Byte ueber der Grenze nicht - sonst ist die Grenze nur eine Zahl im
    Code. Die Grenze steht hier als Zahl und nicht als Verweis auf
    kurs.EINBETTEN_MAX: eine Pruefung, die sich der Aenderung anpasst,
    kann nie rot werden."""
    _gleich(kurs.EINBETTEN_MAX, GRENZE, "die Grenze in kurs.py")
    grenze = GRENZE
    with modell_gesperrt(), wegwerf_ordner() as ordner:
        klein = ordner / "klein.mp3"
        klein.write_bytes(b"\0" * 1024)
        gross = ordner / "gross.mp4"
        gross.write_bytes(b"\0" * (grenze + 1))

        c = curriculum.entwirf(modelle.Auftrag(thema="Medien", level_anzahl=2,
                                               trocken=True))
        ziel = kurs.baue(c, "kurs-2", ordner / "ausgabe" / "kurs.html",
                         medien={1: {"ton": klein}, 2: {"video": gross}})
        html = ziel.read_text(encoding="utf-8")
        if "data:" not in html:
            raise AssertionError("die kleine Datei wurde nicht eingebettet")
        if "medien/gross.mp4" not in html:
            raise AssertionError("die grosse Datei wird nicht daneben verwiesen")
        daneben = ziel.parent / "medien" / "gross.mp4"
        if not daneben.exists():
            raise AssertionError("die grosse Datei liegt nicht daneben: %s" % daneben)
        _gleich(daneben.stat().st_size, grenze + 1, "Groesse der abgelegten Datei")
        if len(html) > grenze:
            raise AssertionError("die grosse Datei ist doch in der HTML-Datei gelandet")
    return ("1 KB wird eingebettet, %d Byte (ein Byte ueber der Grenze) landen "
            "als medien/gross.mp4 daneben" % (grenze + 1))

# Aufraeumen (siehe oben): Modulnamen zurueckgeben und diesen Ordner aus dem
# Suchpfad nehmen. Die oben geladenen Module halten ihre Fassungen selbst
# fest und arbeiten weiter.
for _name, _modul in _belegt.items():
    if _modul is None:
        sys.modules.pop(_name, None)
    else:
        sys.modules[_name] = _modul
while str(HIER) in sys.path:
    sys.path.remove(str(HIER))
