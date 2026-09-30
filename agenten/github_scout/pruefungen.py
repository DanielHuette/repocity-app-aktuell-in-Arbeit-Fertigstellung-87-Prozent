"""Pruefungen des GitHub Scouts. Alles trocken, kostenlos, kein Netz.

Es wird keine Anfrage an GitHub gestellt. Geprueft wird, wie der Scout
urteilt, wenn ihm ein Fund vorliegt: dass Frische zaehlt, dass Kurslisten
und Sammelseiten abgezogen bekommen, dass er die Spuren echter Agentenarbeit
auch in Unterordnern findet - und dass Daniels 1.570 von Hand durchgesehene
Funde uebernommen und nicht noch einmal bewertet werden.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import date, timedelta
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
_belegt = {name: sys.modules.get(name) for name in ('umgebung', 'einstellungen', 'github')}

# Gleichnamige Module gibt es mehrfach - jeder Name wird vor dem Laden
# ausdruecklich auf DIESEN Ordner gesetzt.
laden(HIER / "umgebung.py", "umgebung")
einstellungen = laden(HIER / "einstellungen.py", "einstellungen")
laden(HIER / "github.py", "github")
bewertung = laden(HIER / "bewertung.py", "scout_bewertung")
saat = laden(HIER / "saat.py", "scout_saat")

# Der Name "github" gehoert sonst einem fremden Paket - nach dem Laden wieder
# freigeben, damit ihn niemand hier erbt. bewertung haelt seine Fassung selbst.

#: Dieselbe Kennung, unter der er meldet (siehe auftragsarten.json).
MODUL = "wissen.scout"

REGELN = einstellungen.laden()["bewertung"]
REPO = bewertung.Repo


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


def _repo(name="jemand/agenten-schwarm", beschreibung="multi-agent framework",
          sterne=150, vor_tagen=1):
    return REPO(voller_name=name, beschreibung=beschreibung, sterne=sterne,
                sprache="Python",
                aktualisiert=(date.today() - timedelta(days=vor_tagen)).isoformat(),
                url="https://github.invalid/" + name)


@contextmanager
def wegwerf_pruefliste(eintraege: list):
    """Daniels Urteilsliste als Wegwerf-Datei - die echte bleibt unberuehrt."""
    ordner = Path(tempfile.mkdtemp(prefix="scout_"))
    datei = ordner / "repo_pruefung.json"
    datei.write_text(json.dumps({"eintraege": eintraege}, ensure_ascii=False),
                     encoding="utf-8", newline="")
    try:
        yield datei
    finally:
        shutil.rmtree(ordner, ignore_errors=True)


# ================================================================== Frische

@anmelden("wissen.scout.frische-zaehlt", MODUL,
          "Ein bewegtes Repository steht besser da als ein liegengebliebenes",
          TROCKEN,
          "dass der Scout keine seit Jahren stillen Baustellen empfiehlt")
def frische_zaehlt():
    """Rechnung aus bewertung.py: diese Woche bewegt gibt +4, laenger als
    ein halbes Jahr still gibt -4. Der Unterschied ist also genau 8 Punkte."""
    frisch = bewertung.bewerten(_repo(vor_tagen=1), REGELN)
    monat = bewertung.bewerten(_repo(vor_tagen=20), REGELN)
    still = bewertung.bewerten(_repo(vor_tagen=200), REGELN)

    _gleich(frisch.punkte - still.punkte, 8, "Unterschied frisch zu still")
    _gleich(frisch.punkte - monat.punkte, 2, "Unterschied Woche zu Monat")
    if not any("diese Woche" in g for g in frisch.begruendung):
        raise AssertionError("die Begruendung nennt die Frische nicht")
    if not any("still" in g for g in still.begruendung):
        raise AssertionError("die Begruendung nennt den Stillstand nicht")
    # Ein unlesbares Datum darf nicht zum Absturz fuehren, sondern gar nicht zaehlen.
    ohne = REPO(voller_name="x/y", beschreibung="agent", sterne=0,
                sprache="", aktualisiert="unbekannt", url="")
    bewertung.bewerten(ohne, REGELN)
    if any("bewegt" in g or "still" in g for g in ohne.begruendung):
        raise AssertionError("ein unlesbares Datum wurde trotzdem gewertet")
    return "dieselbe Sache: 8 Punkte Unterschied zwischen dieser Woche und 200 Tagen Ruhe"


@anmelden("wissen.scout.sammelseite-zieht-ab", MODUL,
          "Kurslisten und Sammelseiten bekommen Abzug", TROCKEN,
          "dass der Scout Vorlagen zum Nachbauen sucht und keine Linksammlungen")
def sammelseite_zieht_ab():
    # Beide Male derselbe Name und dieselben Themenwoerter - nur die
    # Sammelseiten-Woerter kommen dazu. Sonst misst man die Woerter im Namen mit.
    sache = bewertung.bewerten(_repo(name="jemand/agent-memory",
                                     beschreibung="agent memory rag"), REGELN)
    liste = bewertung.bewerten(
        _repo(name="jemand/agent-memory",
              beschreibung="agent memory rag awesome-list tutorial"), REGELN)
    if liste.punkte >= sache.punkte:
        raise AssertionError("die Sammelseite steht nicht schlechter da "
                             "(%d gegen %d)" % (liste.punkte, sache.punkte))
    abzuege = [g for g in liste.begruendung if g.startswith("-")]
    if len(abzuege) < 2:
        raise AssertionError("es fehlt ein Abzug: " + ", ".join(liste.begruendung))
    # Rechnung aus konfiguration/einstellungen: awesome- kostet 4, tutorial 3.
    _gleich(sache.punkte - liste.punkte,
            REGELN["abzugswoerter"]["awesome-"] + REGELN["abzugswoerter"]["tutorial"],
            "Summe der Abzuege")
    return ("'awesome-...' mit 'tutorial' verliert %d Punkte gegen dieselbe Sache "
            "ohne diese Woerter"
            % (REGELN["abzugswoerter"]["awesome-"] + REGELN["abzugswoerter"]["tutorial"]))


# ================================================================== Spuren

@anmelden("wissen.scout.spuren-auch-in-unterordnern", MODUL,
          "Die Spuren echter Agentenarbeit werden auch tief im Baum gefunden",
          TROCKEN,
          "dass ein Repository nicht uebersehen wird, weil es aufgeraeumt ist")
def spuren_auch_in_unterordnern():
    marken = bewertung.nachahmenswert([
        "src/skills/schreiben.md", "packages/agents/lauf.py",
        "docs/AGENTS.md", ".claude/settings.json",
    ])
    for muss in ("skills-Ordner", "agents-Ordner", "AGENTS.md", ".claude-Ordner"):
        if muss not in marken:
            raise AssertionError("nicht gefunden: " + muss)

    # Der fuehrende Schraegstrich verhindert falsche Treffer: "myskills/"
    # ist kein skills-Ordner.
    daneben = bewertung.nachahmenswert(["myskills/x.py", "noagents/y.py"])
    if "skills-Ordner" in daneben or "agents-Ordner" in daneben:
        raise AssertionError("ein Ordner wurde faelschlich als Spur gewertet: "
                             + ", ".join(daneben))
    return "vier Spuren in Unterordnern gefunden, 'myskills' faellt nicht darauf herein"


# ================================================================== Saat

@anmelden("wissen.scout.saat-uebernimmt-nur-das-ja", MODUL,
          "Aus der Urteilsliste kommt nur, was ein Ja hat und wirklich existiert",
          TROCKEN,
          "dass Daniels Handarbeit uebernommen und nicht wiederholt wird")
def saat_uebernimmt_nur_das_ja():
    with wegwerf_pruefliste([
        {"repo": "a/ja", "urteil": "ja", "nennungen": 3, "kanaele": ["k1"],
         "github": {"status": "da", "name": "a/ja", "sterne": 120,
                    "letzter_push": "2026-08-01T10:00:00Z", "beschreibung": "gut",
                    "sprache": "Python"}},
        {"repo": "b/nein", "urteil": "nein",
         "github": {"status": "da", "name": "b/nein", "sterne": 900}},
        {"repo": "c/weg", "urteil": "ja",
         "github": {"status": "weg", "name": "c/weg", "sterne": 900}},
    ]) as datei:
        _gleich([r["voller_name"] for r in saat.gewaehlte_repos(datei)], ["a/ja"],
                "uebernommene Repos")

        liste = {}
        liste, neu = saat.saeen(liste, datei)
        _gleich(neu, 1, "neu eingetragen")
        _gleich(liste["a/ja"]["sterne"], 120, "Sterne uebernommen")
        _gleich(liste["a/ja"]["aktualisiert"], "2026-08-01", "Datum gekuerzt")
        if "Hand" not in liste["a/ja"]["thema"]:
            raise AssertionError("die Herkunft 'von Hand gewaehlt' fehlt")

        # Zweiter Lauf: nichts Vorhandenes wird ueberschrieben.
        liste["a/ja"]["punkte"] = 42
        liste, noch_neu = saat.saeen(liste, datei)
        _gleich(noch_neu, 0, "beim zweiten Lauf neu")
        _gleich(liste["a/ja"]["punkte"], 42, "vorhandener Eintrag unveraendert")

    _gleich(saat.gewaehlte_repos(Path("gibt-es-nicht.json")), [],
            "fehlende Datei gibt eine leere Liste")
    return ("nur das Ja mit vorhandenem Repo wird gesaet, ein zweiter Lauf "
            "aendert nichts mehr")

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


# ============================================================ Ausschlussliste

@anmelden("wissen.scout.verworfenes-kommt-nicht-zurueck", MODUL,
          "Was Daniel verworfen hat, holt der Scout nicht wieder", TROCKEN,
          "dass die am 13.09.2026 aussortierten Repositorien beim naechsten "
          "Lauf still zurueckkommen - geloescht waeren sie dann umsonst")
def verworfenes_kommt_nicht_zurueck():
    # Die Liste steht in ausschluss.txt, nicht in der Konfiguration: 1.293 Zeilen
    # machten die Konfiguration unlesbar, und ein Repositoriumsname mit
    # "Claude-3" darin liess `kosten.kein-modell-unter-opus` anschlagen - die
    # Pruefung durchsucht JSON nach Modellnamen und kann einen Repo-Namen nicht
    # von einer Modellwahl unterscheiden. Eine .txt wird nicht durchsucht.
    datei = HIER / "ausschluss.txt"
    if not datei.exists():
        raise AssertionError("ausschluss.txt fehlt")
    liste = [z.strip() for z in datei.read_text(encoding="utf-8").splitlines()
             if z.strip() and not z.strip().startswith("#")]
    if len(liste) < 1000:
        raise AssertionError("die Ausschlussliste hat nur %d Eintraege" % len(liste))
    for name in liste[:50]:
        if "/" not in name:
            raise AssertionError("kein Repositoriumsname: %r" % name)
    if any(n != n.lower() for n in liste):
        raise AssertionError("Eintraege muessen klein geschrieben sein")

    # Die Liste taugt nur, wenn main.py sie auch anwendet - und zwar VOR der
    # Bewertung, sonst landet ein ausgeschlossenes Repository in der
    # Beobachtungsliste und kommt beim naechsten Lauf als "bewegt" zurueck.
    quelltext = (HIER / "main.py").read_text(encoding="utf-8")
    if "def _ausschluss(" not in quelltext:
        raise AssertionError("main.py hat keine Funktion, die ausschluss.txt liest")
    if "ausschluss.txt" not in quelltext:
        raise AssertionError("main.py nennt ausschluss.txt nirgends")
    stelle_ausschluss = quelltext.find("ausschluss = _ausschluss()")
    stelle_bewerten = quelltext.find("bewertung.bewerten(repo, konfig")
    if stelle_ausschluss == -1:
        raise AssertionError("main.py liest die Ausschlussliste nicht")
    if stelle_bewerten == -1 or stelle_ausschluss > stelle_bewerten:
        raise AssertionError("die Ausschlussliste greift erst nach der Bewertung")

    # Und die Gegenprobe: die vier namentlich behaltenen duerfen NICHT darauf
    # stehen. Eine Sperrliste, die auch das Gewollte sperrt, ist schlimmer als
    # keine.
    behalten = ("petergyang/no-ai-slop", "browser-use/video-use",
                "chroma-core/chroma", "anthropics/claude-code")
    kleine = {n.lower() for n in liste}
    faelschlich = [b for b in behalten if b.lower() in kleine]
    if faelschlich:
        raise AssertionError("faelschlich gesperrt: " + ", ".join(faelschlich))

    # Ebenso: was noch im Cache liegt, darf nicht gesperrt sein.
    cache = HIER.parent.parent / "github_cache"
    if cache.exists():
        gesperrt_aber_da = [q.name for q in cache.iterdir()
                            if q.is_dir()
                            and q.name.replace("_", "/").lower() in kleine]
        if gesperrt_aber_da:
            raise AssertionError("liegt im Cache und ist trotzdem gesperrt: "
                                 + ", ".join(gesperrt_aber_da[:3]))
    return ("%d Repositorien gesperrt, greift vor der Bewertung, die vier "
            "Behaltenen sind frei" % len(liste))
