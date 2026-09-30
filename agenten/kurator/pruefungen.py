"""Pruefungen des Kurators. Alles trocken, kostenlos, kein Netz.

Der Kurator ist die einzige Stelle, die in die Saeulen des 2nd Brain
schreibt. Genau deshalb wird hier geprueft, was er abweist: eine Notiz ohne
Kopf, ohne Quelle oder zu duenn; ein Atom ohne Beleg; und alles, was schon
im Bestand liegt.

Die echten Saeulen werden nicht angefasst. Die Doppelungspruefung laeuft
gegen einen Wegwerf-Bestand, der danach geloescht wird.
"""
from __future__ import annotations

import re
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
_belegt = {name: sys.modules.get(name) for name in ('umgebung', 'einstellungen')}

# pruefung.py und einstellungen.py gibt es im Universe mehrfach - vor dem
# Laden wird jeder Name ausdruecklich auf DIESEN Ordner gesetzt.
laden(HIER / "umgebung.py", "umgebung")
einstellungen = laden(HIER / "einstellungen.py", "einstellungen")
pruefung = laden(HIER / "pruefung.py", "kurator_pruefung")

#: Dieselbe Kennung, unter der er meldet (siehe auftragsarten.json).
MODUL = "wissen.kurator"

REGELN = einstellungen.laden()["pruefung"]


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


def _notiz(titel="Wie ein Schwarm sich selbst prueft", quelle="https://beispiel.invalid/a",
           zeichen=None, ohne_kopf=False, ohne_feld="") -> str:
    """Eine Notiz, die durchgeht - jeder Baustein einzeln abschaltbar."""
    laenge = REGELN["mindestzeichen_notiz"] + 40 if zeichen is None else zeichen
    koerper = ("Ein Satz ueber die Sache. " * 200)[:laenge]
    if ohne_kopf:
        return koerper + "\n\nquellen: " + quelle + "\n"
    felder = {"title": titel, "typ": "tech-wissen", "erfasst_von": "kurator-pruefung"}
    felder.pop(ohne_feld, None)
    kopf = "\n".join("%s: %s" % (name, wert) for name, wert in felder.items())
    return ("---\n%s\n---\n\n%s\n\n## quellen\n- %s\n" % (kopf, koerper, quelle))


@contextmanager
def wegwerf_bestand(notizen: list, atome: list):
    """Ein Bestand aus Wegwerf-Dateien statt der echten Saeulen."""
    ordner = Path(tempfile.mkdtemp(prefix="kurator_"))
    wissen = ordner / "wissen"
    atomordner = ordner / "atome"
    wissen.mkdir(parents=True)
    atomordner.mkdir(parents=True)
    for nummer, text in enumerate(notizen):
        (wissen / ("n%d.md" % nummer)).write_text(text, encoding="utf-8", newline="")
    if atome:
        import json
        (atomordner / "thema.jsonl").write_text(
            "\n".join(json.dumps(a, ensure_ascii=False) for a in atome) + "\n",
            encoding="utf-8", newline="")
    try:
        yield pruefung.Bestand(wissen, atomordner)
    finally:
        shutil.rmtree(ordner, ignore_errors=True)


# ================================================================== Notizen

@anmelden("wissen.kurator.notiz-ohne-kopf-und-quelle-faellt-durch", MODUL,
          "Eine Notiz ohne Kopf, ohne Pflichtfeld oder ohne Quelle geht zurueck",
          TROCKEN,
          "dass nichts Unbelegtes in die Wissenssaeule kommt")
def notiz_ohne_kopf_und_quelle_faellt_durch():
    ohne_kopf = pruefung.notiz_pruefen(_notiz(ohne_kopf=True), REGELN)
    _gleich(ohne_kopf.ok, False, "Notiz ohne Kopf")
    if not any("Kopf" in g for g in ohne_kopf.gruende):
        raise AssertionError("der fehlende Kopf wird nicht benannt")

    for feld in REGELN["pflichtfelder"]:
        befund = pruefung.notiz_pruefen(_notiz(ohne_feld=feld), REGELN)
        _gleich(befund.ok, False, "Notiz ohne Feld " + feld)
        if not any(feld in g for g in befund.gruende):
            raise AssertionError("das fehlende Feld %s wird nicht benannt" % feld)

    duenn = pruefung.notiz_pruefen(_notiz(zeichen=50), REGELN)
    _gleich(duenn.ok, False, "zu duenne Notiz")
    # Der Grund nennt die gemessene Zeichenzahl, nicht nur ein Urteil.
    if not any(g.endswith("Zeichen)") for g in duenn.gruende):
        raise AssertionError("die gemessene Laenge fehlt im Grund: "
                             + ", ".join(duenn.gruende))
    return ("Kopf, %d Pflichtfelder und %d Zeichen Mindestlaenge werden einzeln "
            "eingefordert" % (len(REGELN["pflichtfelder"]),
                              REGELN["mindestzeichen_notiz"]))


@anmelden("wissen.kurator.gute-notiz-kommt-durch", MODUL,
          "Eine vollstaendige Notiz wird angenommen", TROCKEN,
          "dass die Pruefung nicht auch das Brauchbare erschlaegt")
def gute_notiz_kommt_durch():
    befund = pruefung.notiz_pruefen(_notiz(), REGELN)
    if not befund.ok:
        raise AssertionError("eine vollstaendige Notiz wurde abgewiesen: "
                             + ", ".join(befund.gruende))
    # Genau an der Grenze muss sie noch durchgehen.
    knapp = pruefung.notiz_pruefen(_notiz(zeichen=REGELN["mindestzeichen_notiz"]), REGELN)
    if not knapp.ok:
        raise AssertionError("die Notiz genau an der Mindestlaenge fiel durch: "
                             + ", ".join(knapp.gruende))
    return ("vollstaendige Notiz angenommen, auch genau bei %d Zeichen"
            % REGELN["mindestzeichen_notiz"])


# ================================================================== Atome

@anmelden("wissen.kurator.atom-braucht-quelle-und-beleg", MODUL,
          "Eine Aussage ohne Quelle, ohne Beleg oder zu kurz kommt nicht hinein",
          TROCKEN,
          "dass die Atomsaeule nur Behauptungen mit Herkunft enthaelt")
def atom_braucht_quelle_und_beleg():
    gut = {"aussage": "Ein Lehrsatz entsteht erst ab drei gleichartigen Neins.",
           "quelle": "https://beispiel.invalid/a", "beleg": "Absatz 3",
           "thema": "lernen"}
    _gleich(pruefung.atom_pruefen(gut, REGELN).ok, True, "vollstaendiges Atom")

    for feld, was in (("quelle", "keine Quelle"), ("beleg", "kein Beleg")):
        kaputt = dict(gut, **{feld: ""})
        befund = pruefung.atom_pruefen(kaputt, REGELN)
        _gleich(befund.ok, False, "Atom ohne " + feld)
        if was not in befund.gruende:
            raise AssertionError("erwarteter Grund fehlt: " + was)

    kurz = dict(gut, aussage="zu kurz")
    _gleich(pruefung.atom_pruefen(kurz, REGELN).ok, False,
            "Aussage unter %d Zeichen" % REGELN["atom_mindestzeichen"])
    return ("Quelle, Beleg und %d Zeichen Mindestlaenge werden einzeln eingefordert"
            % REGELN["atom_mindestzeichen"])


# ================================================================== Doppelung

@anmelden("wissen.kurator.doppelung-wird-erkannt", MODUL,
          "Was schon im Bestand liegt, wird nicht ein zweites Mal eingepflegt",
          TROCKEN,
          "dass das 2nd Brain nicht mit denselben Notizen zuwaechst",
          blind_fuer="zwei Notizen, die dasselbe sagen, aber anders heissen "
                     "und aus verschiedenen Quellen stammen")
def doppelung_wird_erkannt():
    vorhanden = _notiz(titel="Wie ein Schwarm sich selbst prueft",
                       quelle="https://beispiel.invalid/alt")
    with wegwerf_bestand([vorhanden], [{"aussage": "Ein Lehrsatz entsteht erst "
                                                   "ab drei gleichartigen Neins.",
                                        "thema": "lernen"}]) as bestand:
        gleicher_titel = _notiz(titel="Wie ein Schwarm sich SELBST prueft!",
                                quelle="https://beispiel.invalid/neu")
        _gleich(bestand.kennt_notiz(gleicher_titel), "Titel schon im Bestand",
                "gleicher Titel, andere Schreibweise")

        gleiche_quelle = _notiz(titel="Ganz anderer Titel ueber Schwaerme",
                                quelle="https://beispiel.invalid/alt")
        _gleich(bestand.kennt_notiz(gleiche_quelle), "Quelle schon im Bestand",
                "gleiche Quelle")

        neue = _notiz(titel="Etwas voellig Neues", quelle="https://beispiel.invalid/neu")
        _gleich(bestand.kennt_notiz(neue), "", "wirklich neue Notiz")

        _gleich(bestand.kennt_atom({"aussage": "Ein Lehrsatz entsteht erst ab drei "
                                               "gleichartigen Neins."}),
                "Aussage schon im Bestand", "bekanntes Atom")
        _gleich(bestand.kennt_atom({"aussage": "Etwas anderes ganz und gar."}), "",
                "neues Atom")

        # Nach dem Einpflegen ist die neue Notiz selbst bekannt - sonst
        # kaeme dieselbe Notiz im selben Lauf zweimal durch.
        bestand.merken_notiz(neue)
        _gleich(bestand.kennt_notiz(neue), "Titel schon im Bestand",
                "eben eingepflegte Notiz")
    return ("Titel und Quelle werden wiedererkannt, auch mit anderer "
            "Schreibweise; Eingepflegtes gilt sofort als bekannt")

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


# ---------------------------------------------- Die Rueckseite: Herausgeben

def _versorger():
    """Die Herausgabe laden - ohne das kleine gehirn.py daneben zu erwischen."""
    import importlib.util
    datei = Path(__file__).resolve().parent / "versorgen.py"
    beschreibung = importlib.util.spec_from_file_location("kurator_versorgen_probe", datei)
    modul = importlib.util.module_from_spec(beschreibung)
    # Vor dem Ausfuehren eintragen: eine Datenklasse darin sucht ihr eigenes
    # Modul in sys.modules. Fehlt es, bricht der Import mit einer Meldung ab,
    # die nach allem aussieht - nur nicht nach der Ursache.
    sys.modules["kurator_versorgen_probe"] = modul
    beschreibung.loader.exec_module(modul)
    return modul


@anmelden("wissen.kurator.gibt-heraus", MODUL,
          "Der Kurator gibt Stoff heraus, nicht nur ein", TROCKEN,
          "dass eine kreative Straße Material bekommt statt zu erfinden")
def gibt_heraus():
    v = _versorger()
    stoff = v.versorge({"text": "RepoCity Agenten und Produktionsstraßen"},
                       modul="prod.praesentation", braucht=("text",))
    if not stoff.frage:
        raise AssertionError("der Auftrag wurde nicht in eine Frage übersetzt")
    if stoff.deckung.stufe not in ("gut", "duenn", "leer"):
        raise AssertionError("die Deckung trägt keine der drei Stufen")
    if not stoff.deckung.satz:
        raise AssertionError("die Deckung wird nicht im Klartext gesagt")
    return "Deckung %s: %s" % (stoff.deckung.stufe, stoff.deckung.satz[:60])


@anmelden("wissen.kurator.leeres-thema-wird-gesagt", MODUL,
          "Ein Thema ohne Fund wird als leer gemeldet, nicht stillschweigend gefüllt", TROCKEN,
          "dass ein Agent auf nichts baut, ohne dass es jemand merkt")
def leeres_thema_wird_gesagt():
    v = _versorger()
    stoff = v.versorge({"text": "Xqzwvyk Blorbfnu Zzzhamster 99812"},
                       modul="prod.praesentation", braucht=("text",))
    if stoff.deckung.stufe == "gut":
        raise AssertionError(
            "zu einem erfundenen Thema meldet der Kurator gute Deckung")
    if stoff.empfehlung == "bauen":
        raise AssertionError(
            "bei dünner Deckung empfiehlt er trotzdem einfach zu bauen")
    return "erfundenes Thema: Deckung %s, Empfehlung %s" % (
        stoff.deckung.stufe, stoff.empfehlung)


@anmelden("wissen.kurator.lebensverwaltung-bleibt-aussen", MODUL,
          "Nur die kreativen Straßen holen hier Stoff", TROCKEN,
          "dass Post, Wohnung und Bewerbung ihre eigenen Quellen behalten")
def lebensverwaltung_bleibt_aussen():
    sys.path.append(str(Path(__file__).resolve().parent.parent / "kern"))
    import stoff as fassade
    for modul in ("prod.praesentation", "prod.video.clip", "prod.musik"):
        if not fassade.ist_kreativ(modul):
            raise AssertionError("%s wird nicht als kreativ erkannt" % modul)
    for modul in ("wohnung", "post", "bewerbung", "kalender", "trading"):
        if fassade.ist_kreativ(modul):
            raise AssertionError(
                "%s würde Stoff aus dem 2nd Brain ziehen, obwohl es nicht dazugehört" % modul)
    return "kreative Straßen holen Stoff, die Lebensverwaltung nicht"


# --------------------------------------------- Der Stoff kommt bei den Straßen an
#
# Ein Stoffbeschaffer, den niemand liest, ist ein Regal ohne Tür. Diese beiden
# Prüfungen halten fest, dass aus dem Stoff wirklich eine Anweisung wird und
# dass jede kreative Straße sie auch mitschickt.

@anmelden("wissen.kurator.stoff-wird-zur-anweisung", MODUL,
          "Aus dem Stoff wird ein Block für die Frage ans Modell", TROCKEN,
          "dass das Modell den eigenen Stoff wirklich zu sehen bekommt")
def stoff_wird_zur_anweisung():
    sys.path.append(str(Path(__file__).resolve().parent.parent / "kern"))
    import stoff as fassade

    leer = fassade.als_anweisung({})
    if leer:
        raise AssertionError("ohne Stoff entsteht trotzdem ein Block: %r" % leer[:80])

    feld = {"kontext": "RepoCity baut Straßen, keine Werkzeugkästen.",
            "quellen": ["2nd Brain: strassen.md"],
            "deckung": "duenn", "deckung_satz": "Nur 2 brauchbare Funde.",
            "verbotsliste": ["revolutionär", "nahtlos"]}
    block = fassade.als_anweisung(feld)
    for erwartet in ("RepoCity baut Straßen", "strassen.md",
                     "Nur 2 brauchbare Funde", "revolutionär"):
        if erwartet not in block:
            raise AssertionError("im Block fehlt: %s" % erwartet)
    if "vorsichtig" not in block:
        raise AssertionError(
            "bei dünner Deckung wird das Modell nicht zur Vorsicht angehalten")

    # Und das Feld aus einem Auftrag herausholen - Dict wie Objekt.
    if fassade.aus_auftrag({"stoff": feld}) is not feld:
        raise AssertionError("das Stofffeld wird aus dem Auftrag nicht gefunden")
    if fassade.aus_auftrag({"thema": "ohne Stoff"}) != {}:
        raise AssertionError("ein Auftrag ohne Stoff liefert kein leeres Feld")
    return "Block trägt Kontext, Herkunft, Deckung und Verbotsliste"


@anmelden("wissen.kurator.jede-kreative-strasse-liest-den-stoff", MODUL,
          "Jede kreative Straße gibt den Stoff an ihr Modell weiter", TROCKEN,
          "dass keine Straße am eigenen Wissen vorbei erfindet")
def jede_kreative_strasse_liest_den_stoff():
    universe = Path(__file__).resolve().parent.parent
    # Je Straße: die Datei, in der aus dem Thema Text wird, und der AUFRUF,
    # an dem man sieht, dass der Stoff mitgeht. Gesucht wird der Aufruf, nicht
    # der Name - sonst genügte die Funktion, die niemand benutzt.
    stellen = {
        "video": ("video_agent/drehbuch.py", r"(?<!def )_stoffblock\("),
        "musik": ("musik_agent/stil.py", r"(?<!def )_stoffblock\("),
        "lernprogramm": ("lern_agent/curriculum.py", r"(?<!def )_stoffblock\("),
        "marketing": ("marketing/kampagne.py", r"(?<!def )_stoffblock\("),
        "software": ("architekt/entwurf.py", r"(?<!def )_stoffblock\("),
        "social": ("social_media_manager/beitrag.py", r"(?<!def )stoff_zum\("),
        "praesentation": ("gestalter/folien.py", r"(?<!def )_stoff_zum_auftrag\("),
    }
    fehlt = []
    for strasse, (datei, aufruf) in stellen.items():
        pfad = universe / datei
        if not pfad.exists():
            fehlt.append("%s: %s gibt es nicht" % (strasse, datei))
            continue
        text = pfad.read_text(encoding="utf-8")
        if not re.search(aufruf, text):
            fehlt.append("%s: %s reicht den Stoff nicht weiter" % (strasse, datei))
    if fehlt:
        raise AssertionError("; ".join(fehlt))

    # Und der Auftrag muss den Stoff überhaupt tragen können.
    for datei in ("video_agent/modelle.py", "musik_agent/modelle.py",
                  "lern_agent/modelle.py"):
        text = (universe / datei).read_text(encoding="utf-8")
        if "stoff: dict" not in text:
            raise AssertionError(
                "%s: der Auftrag hat kein Feld für den Stoff - "
                "er ginge auf dem Weg verloren" % datei)
    return "%d Straßen lesen den Stoff, 3 Aufträge tragen ihn" % len(stellen)
