"""Pruefungen des Deep Researchers. Alles trocken, kostenlos, kein Netz.

Es wird keine Seite abgerufen. Geprueft wird, was der Researcher mit dem
macht, was hereinkommt: Feeds lesen, Treffer sieben, vor der Suche auf die
Bremse sehen - und dass sein Quellenkatalog vollstaendig ist.
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
_belegt = {name: sys.modules.get(name) for name in ('umgebung', 'einstellungen')}

# Gleichnamige Module gibt es mehrfach - jeder Name wird vor dem Laden
# ausdruecklich auf DIESEN Ordner gesetzt.
laden(HIER / "umgebung.py", "umgebung")
laden(HIER / "einstellungen.py", "einstellungen")
katalog = laden(HIER / "katalog.py", "research_katalog")
feeds = laden(HIER / "feeds.py", "research_feeds")
suche = laden(HIER / "suche.py", "research_suche")

#: Dieselbe Kennung, unter der er meldet (siehe auftragsarten.json).
MODUL = "wissen.research"


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


@contextmanager
def wegwerf_katalog(eintraege: list):
    """Der Katalog zeigt auf eine Wegwerf-Datei, nicht auf den echten."""
    ordner = Path(tempfile.mkdtemp(prefix="research_"))
    datei = ordner / "quellen.json"
    datei.write_text(json.dumps({"quellen": eintraege}, ensure_ascii=False),
                     encoding="utf-8", newline="")
    echt = katalog.KATALOG_DATEI
    katalog.KATALOG_DATEI = datei
    try:
        yield datei
    finally:
        katalog.KATALOG_DATEI = echt
        shutil.rmtree(ordner, ignore_errors=True)


# ================================================================== Feeds

_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item>
    <title>Erster Beitrag</title>
    <link>https://beispiel.invalid/eins</link>
    <pubDate>Mon, 01 Sep 2026 08:00:00 +0000</pubDate>
    <description>&lt;p&gt;Ein Absatz mit &lt;b&gt;Auszeichnung&lt;/b&gt;.&lt;/p&gt;</description>
  </item>
  <item>
    <title>Ohne Verweis</title>
    <description>Dieser Eintrag hat keine Adresse.</description>
  </item>
</channel></rss>"""

_ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Atom-Beitrag</title>
    <link rel="alternate" href="https://beispiel.invalid/atom"/>
    <updated>2026-09-02T10:00:00Z</updated>
    <summary>Kurzfassung</summary>
  </entry>
</feed>"""


@anmelden("wissen.research.feeds-beide-formate", MODUL,
          "RSS und Atom werden beide gelesen, Auszeichnungen fallen weg", TROCKEN,
          "dass ein Rundgang ueber Feeds nicht am Format der Quelle scheitert",
          blind_fuer="Feeds mit ungewoehnlichen Namensraeumen")
def feeds_beide_formate():
    rss = feeds.lesen(_RSS, "beispiel")
    _gleich(len(rss), 1, "verwertbare RSS-Eintraege (einer ohne Adresse faellt weg)")
    _gleich(rss[0].url, "https://beispiel.invalid/eins", "Adresse")
    _gleich(rss[0].datum, "2026-09-01", "Datum")
    if "<" in rss[0].anriss or ">" in rss[0].anriss:
        raise AssertionError("im Anriss stehen noch Auszeichnungen: " + rss[0].anriss)
    # Die Marken werden durch ein Leerzeichen ersetzt, darum steht vor dem
    # Punkt eines - der Anriss ist kein Fliesstext, sondern eine Vorschau.
    _gleich(rss[0].anriss, "Ein Absatz mit Auszeichnung .", "entkleideter Anriss")

    atom = feeds.lesen(_ATOM, "beispiel")
    _gleich(len(atom), 1, "Atom-Eintraege")
    _gleich(atom[0].url, "https://beispiel.invalid/atom", "Atom-Adresse")
    _gleich(atom[0].datum, "2026-09-02", "Atom-Datum")

    _gleich(feeds.lesen("kein XML"), [], "kaputter Feed gibt eine leere Liste")
    return "RSS und Atom gelesen, Eintrag ohne Adresse verworfen, Anriss entkleidet"


@anmelden("wissen.research.altes-faellt-raus-undatiertes-bleibt", MODUL,
          "Zu alte Beitraege fallen weg, undatierte bleiben drin", TROCKEN,
          "dass ein Feed ohne Datumsangabe nicht stillschweigend verschwindet")
def altes_faellt_raus_undatiertes_bleibt():
    heute = date.today()
    beitraege = [
        feeds.Beitrag("frisch", "https://a.invalid", (heute - timedelta(days=2)).isoformat(), ""),
        feeds.Beitrag("alt", "https://b.invalid", (heute - timedelta(days=40)).isoformat(), ""),
        feeds.Beitrag("ohne Datum", "https://c.invalid", "", ""),
    ]
    behalten = [b.titel for b in feeds.neuer_als(beitraege, 7)]
    _gleich(behalten, ["frisch", "ohne Datum"], "was uebrig bleibt")
    return "40 Tage alt faellt weg, 2 Tage alt und ohne Datum bleiben"


# ================================================================== Treffer sieben

@anmelden("wissen.research.sperrliste-und-doppelte", MODUL,
          "Gesperrte Seiten fliegen raus, jede Adresse bleibt einmal uebrig",
          TROCKEN,
          "dass derselbe Text nicht zweimal geholt und zweimal bezahlt wird")
def sperrliste_und_doppelte():
    treffer = [
        suche.Treffer("gut", "https://gut.invalid/artikel"),
        suche.Treffer("gut noch einmal", "https://gut.invalid/artikel?utm=1"),
        suche.Treffer("gut mit Sprungmarke", "https://gut.invalid/artikel#unten"),
        suche.Treffer("gesperrt", "https://pinterest.com/pin/1"),
        suche.Treffer("kein Netzverweis", "javascript:void(0)"),
        suche.Treffer("zweite Seite", "https://andere.invalid/x/"),
    ]
    sauber = suche.filtern(treffer, ["pinterest.", "facebook.com"], anzahl=10)
    _gleich([t.url for t in sauber],
            ["https://gut.invalid/artikel", "https://andere.invalid/x/"],
            "was uebrig bleibt")
    return ("drei Schreibweisen derselben Seite werden zu einer, "
            "Gesperrtes und Nicht-Adressen fallen weg")


@anmelden("wissen.research.bremse-haelt", MODUL,
          "Nach 750 Suchen im Monat wird nicht weitergesucht", TROCKEN,
          "dass keine Suche abgerechnet wird, die ueber das freie Kontingent hinausgeht")
def bremse_haelt():
    import os

    _gleich(suche.SUCHEN_JE_MONAT, 750, "750 Suchen je Monat (1.500 Credits / 2)")

    vorher = os.environ.pop("TAVILY_API_KEY", None)
    schalter_echt = suche._schalter
    stand_echt = suche.stand
    try:
        # Erstes Tor: der Schalter des Nutzers. Steht er aus, kommt niemand
        # weiter - auch nicht mit Schluessel.
        os.environ["TAVILY_API_KEY"] = "nur-fuer-die-pruefung"
        suche._schalter = lambda: {"an": False, "ueberKontingent": False, "grund": ""}
        try:
            suche.suchen("beliebig", 3, [])
            raise AssertionError("bei ausgeschaltetem Schalter wurde gesucht")
        except suche.SucheGesperrt as grund:
            _gleich("steht aus" in str(grund), True, "der Grund nennt den Schalter")

        suche._schalter = lambda: {"an": True, "ueberKontingent": False, "grund": ""}

        # Zweites Tor: der Schluessel.
        os.environ.pop("TAVILY_API_KEY", None)
        try:
            suche.suchen("beliebig", 3, [])
            raise AssertionError("ohne Schluessel wurde trotzdem gesucht")
        except suche.SucheGesperrt as grund:
            _gleich("TAVILY_API_KEY" in str(grund), True, "der Grund nennt den fehlenden Schluessel")

        # Drittes Tor: das Kontingent.
        os.environ["TAVILY_API_KEY"] = "nur-fuer-die-pruefung"
        suche.stand = lambda: {"suchen_je_monat": 750, "verbraucht": 750,
                               "frei": 0, "credits_gebucht": 1500}
        try:
            suche.suchen("beliebig", 3, [])
            raise AssertionError("bei vollem Kontingent wurde trotzdem gesucht")
        except suche.SucheGesperrt as grund:
            _gleich("aufgebraucht" in str(grund), True, "der Grund nennt das leere Kontingent")

        # Der zweite Schalter hebt genau dieses Tor auf - und nur dieses.
        suche._schalter = lambda: {"an": True, "ueberKontingent": True, "grund": ""}
        try:
            suche.suchen("beliebig", 3, [])
            raise AssertionError("die Suche lief trotz Attrappe durch")
        except suche.SucheGesperrt as grund:
            _gleich("aufgebraucht" not in str(grund), True,
                    "mit Erlaubnis haelt das Kontingent nicht mehr auf")
    finally:
        suche._schalter = schalter_echt
        suche.stand = stand_echt
        os.environ.pop("TAVILY_API_KEY", None)
        if vorher is not None:
            os.environ["TAVILY_API_KEY"] = vorher

    return ("Schalter aus, fehlender Schluessel und volles Kontingent halten je "
            "fuer sich an; die Erlaubnis hebt nur das Kontingent auf")


# ================================================================== Katalog

@anmelden("wissen.research.katalog-filtert", MODUL,
          "Abgeschaltete Quellen und fremde Kategorien bleiben draussen", TROCKEN,
          "dass eine abgeschaltete Quelle wirklich nicht mehr abgerufen wird")
def katalog_filtert():
    with wegwerf_katalog([
        {"name": "A", "art": "feed", "url": "https://a.invalid/feed",
         "kategorie": "forschung", "themen": ["ki"], "aktiv": True},
        {"name": "B", "art": "seite", "url": "https://b.invalid",
         "kategorie": "forschung", "themen": [], "aktiv": False},
        {"name": "C", "art": "feed", "url": "https://c.invalid/feed",
         "kategorie": "werkzeuge", "themen": [], "aktiv": True},
    ]):
        _gleich([q.name for q in katalog.laden()], ["A", "C"], "nur aktive")
        _gleich([q.name for q in katalog.laden(nur_aktive=False)], ["A", "B", "C"],
                "alle, wenn ausdruecklich verlangt")
        _gleich([q.name for q in katalog.laden(kategorien=["werkzeuge"])], ["C"],
                "nach Kategorie")
        _gleich(katalog.kategorien(), ["forschung", "werkzeuge"], "Kategorien")
    return "abgeschaltete Quelle bleibt draussen, Kategoriefilter greift"


@anmelden("wissen.research.echter-katalog-ist-vollstaendig", MODUL,
          "Jede Quelle im echten Katalog hat Adresse und Kategorie", TROCKEN,
          "dass kein Rundgang an einem halb ausgefuellten Eintrag scheitert",
          blind_fuer="ob die Adressen auch antworten - das braeuchte Netz")
def echter_katalog_ist_vollstaendig():
    quellen = katalog.laden(nur_aktive=False)
    if len(quellen) < 5:
        raise AssertionError("nur %d Quellen im Katalog - das ist kein Katalog"
                             % len(quellen))
    luecken = []
    for quelle in quellen:
        if not quelle.url.startswith("http"):
            luecken.append("%s hat keine Adresse" % (quelle.name or "(ohne Namen)"))
        if not quelle.kategorie:
            luecken.append("%s hat keine Kategorie" % (quelle.name or "(ohne Namen)"))
        if not quelle.name:
            luecken.append("eine Quelle hat keinen Namen: " + quelle.url)
    if luecken:
        raise AssertionError("; ".join(luecken[:5]))
    return "%d Quellen, jede mit Namen, Adresse und Kategorie" % len(quellen)

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
