"""Pruefungen fuer Mia. Alles trocken, alles kostenlos, kein Netz.

Geprueft wird die Datei, die im Worker wirklich laeuft - nicht eine
Nachbildung in Python. Das waere die Doppelung, die nach zwei Wochen
auseinanderlaeuft: die Python-Fassung waere gruen und der Worker offen.

Der Lauf selbst steckt in pruefung.mjs und wird einmal gestartet; jede
Pruefung hier liest ihr Ergebnis aus demselben Lauf. Faellt eine Grenze im
Worker weg, faellt hier eine Pruefung durch - genau dafuer sind sie da.
"""
from __future__ import annotations

import json
import subprocess

# Kein Konsolenfenster fuer Hilfsprogramme (ffmpeg, node, npm, ...).
# Eine Quelle: universe/kern/ohne_fenster.py - ueber den Pfad geladen,
# weil im Universe zwoelf Ordner gleichnamige Module haben.
import importlib.util as _iu
from pathlib import Path as _P
for _o in _P(__file__).resolve().parents:
    _k = _o / "kern" / "ohne_fenster.py"
    if _k.exists():
        _s = _iu.spec_from_file_location("ohne_fenster", _k)
        _m = _iu.module_from_spec(_s)
        _s.loader.exec_module(_m)
        break
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

fuehrung = laden(KERN / "fuehrung.py", "kern_fuehrung")
verzeichnis = laden(KERN / "verzeichnis.py", "kern_verzeichnis")

MODUL = "fragefenster"
REGELN = json.loads((HIER / "regeln.json").read_text(encoding="utf-8"))

_lauf: dict | None = None


def ergebnisse() -> dict:
    """Den Node-Lauf einmal starten, danach nur noch nachschlagen."""
    global _lauf
    if _lauf is None:
        fertig = subprocess.run(
            ["node", str(HIER / "pruefung.mjs")],
            capture_output=True, text=True, encoding="utf-8", timeout=120,
        )
        zeile = (fertig.stdout or "").strip().splitlines()
        if not zeile:
            raise AssertionError("pruefung.mjs hat nichts ausgegeben: "
                                 + (fertig.stderr or "")[:400])
        _lauf = json.loads(zeile[-1])
    return _lauf


def _muss(*namen: str) -> str:
    """Diese Einzelpruefungen muessen gruen sein."""
    alle = ergebnisse()["ergebnisse"]
    fehlt = [n for n in namen if n not in alle]
    if fehlt:
        raise AssertionError("Pruefung nicht gelaufen: " + ", ".join(fehlt))
    rot = [n for n in namen if not alle[n]]
    if rot:
        raise AssertionError("durchgefallen: " + ", ".join(rot))
    return "%d Einzelpruefungen gruen" % len(namen)


# ================================================== Die Verbote stehen wirklich

@anmelden("mia.verbote-in-der-anweisung", MODUL,
          "Jedes Verbot steht in der Anweisung, mit seinem Standardsatz", TROCKEN,
          "dass kein Verbot aus der Anweisung faellt, ohne dass es auffaellt")
def verbote_in_der_anweisung():
    namen = ["verbot-in-anweisung:%s" % v["kennung"] for v in REGELN["verbote"]]
    _muss(*namen)
    return "%d Verbote stehen in der Anweisung: %s" % (
        len(namen), ", ".join(v["kennung"] for v in REGELN["verbote"]))


@anmelden("mia.offenlegung", MODUL,
          "Mias erster Satz steht in der Anweisung; die Kennzeichnung als KI steht neben ihrem Namen", TROCKEN,
          "die Pflicht aus Artikel 50 der KI-Verordnung, seit 02.08.2026")
def offenlegung():
    return _muss("offenlegung")


@anmelden("mia.ton", MODUL,
          "Beide Tonlagen stehen in der Anweisung, die Anrede bleibt gleich", TROCKEN,
          "locker bei Produkt und Bedienung, foermlich bei Recht, Kosten und Moral")
def ton():
    return _muss("ton-locker", "ton-foermlich", "ton-anrede")


# ================================================== Stufen und Einschleusen

@anmelden("mia.gast-sieht-nichts-persoenliches", MODUL,
          "Ohne Anmeldung gibt es keine persoenlichen Themen", TROCKEN,
          "dass niemand ohne Kennung an Daten kommt, auch nicht an eigene")
def gast_sieht_nichts_persoenliches():
    return _muss("gast-ohne-eigenes", "nutzer-mit-eigenes")


@anmelden("mia.gast-erreicht-kein-modell", MODUL,
          "Ohne Konto nur Antworten, die nichts kosten", TROCKEN,
          "dass kein Fremder auf Kosten des Betreibers das Modell fragt - "
          "Daniel, 11.09.2026: 'nicht angemeldete duerfen nur fragen stellen die kein geld kosten'")
def gast_erreicht_kein_modell():
    _muss("gast-erreicht-kein-modell", "gast-kostet-nichts")
    return "Gast: Wegweiser ja, Modell nie - kein Schreibvorgang, keine Buchung"


@anmelden("mia.frage-ist-kein-befehl", MODUL,
          "Die Frage geht eingefasst als Text hinein", TROCKEN,
          "dass 'vergiss deine Regeln' im Eingabefeld eine Frage bleibt",
          blind_fuer="ob das Modell sich trotzdem ueberreden laesst - "
                     "dagegen haelt die Ausgangspruefung")
def frage_ist_kein_befehl():
    return _muss("frage-eingefasst", "anweisung-warnt-vor-einschleusen")


@anmelden("mia.eingang", MODUL,
          "Leere und zu lange Fragen werden abgewiesen", TROCKEN,
          "dass die Laenge begrenzt ist, bevor sie Geld kostet")
def eingang():
    return _muss("eingang-leer", "eingang-zu-lang", "eingang-normal")


# ================================================== Die letzte Grenze

@anmelden("mia.ausgang-faengt", MODUL,
          "Die Ausgangspruefung faengt Schluessel, Pfade, fremde Adressen, Quelltext",
          TROCKEN,
          "die einzige Grenze, die auch dann haelt, wenn die Ueberredung glueckt")
def ausgang_faengt():
    namen = ["ausgang-faengt:schluessel-anthropic", "ausgang-faengt:schluessel-github",
             "ausgang-faengt:umgebungsname", "ausgang-faengt:fremde-email",
             "ausgang-faengt:dateipfad", "ausgang-faengt:quelltext"]
    _muss(*namen)
    return "6 Fluchtwege dicht: Anthropic-Schluessel, GitHub-Schluessel, " \
           "Name aus der .env, fremde E-Mail, Dateipfad, Quelltextblock"


@anmelden("mia.ausgang-laesst-durch", MODUL,
          "Eine normale Antwort kommt durch", TROCKEN,
          "dass die Sperrliste nicht auch das Erlaubte erschlaegt")
def ausgang_laesst_durch():
    return _muss("ausgang-laesst-eigene-adresse-durch",
                 "ausgang-laesst-normale-antwort-durch")


# ================================================== Geld

@anmelden("mia.tagesdeckel-haelt", MODUL,
          "Der Tagesdeckel ist gesetzt und sperrt, bevor Geld fliesst", TROCKEN,
          "dass ein fehlender Deckel als 'noch nicht entschieden' gilt und "
          "ein aufgebrauchter die Absage kostenlos macht")
def tagesdeckel_haelt():
    _muss("deckel-sind-gesetzt", "aufgebrauchter-deckel-sperrt",
          "fehlender-deckel-sperrt-im-code", "absage-kostet-nichts",
          "vergessener-deckel-sperrt-trotzdem")
    k = REGELN["kosten"]
    if k.get("deckel") == "aus":
        return ("Deckel ausgeschaltet (Daniel, 09.09.2026) - ein VERGESSENER "
                "Deckel sperrt weiterhin, das ist eigens geprueft")
    return ("je Kennung %.4f EUR, alle Gaeste %.4f EUR, gesamt %.4f EUR am Tag"
            % (k["obergrenze_je_kennung_und_tag_eur"],
               k["obergrenze_gast_je_tag_eur"],
               k["obergrenze_gesamt_je_tag_eur"]))


@anmelden("mia.preis-stimmt", MODUL,
          "Der gerechnete Preis trifft die Messung", TROCKEN,
          "dass die Kosten aus echten Tokenzahlen kommen, nicht aus einer Schaetzung")
def preis_stimmt():
    _muss("preis-stimmt-mit-messung", "unbekanntes-modell-kostet-trotzdem")
    return "4035 Token ein, 700 aus (gemessen 2026-09-06), claude-opus-5: " \
           "0,03466 EUR nach Liste vom 11.09.2026"


# ================================================== Sie redet, sie handelt nicht

@anmelden("mia.keine-werkzeuge", MODUL,
          "Mia hat keine Werkzeuge", TROCKEN,
          "dass das Fragefenster nichts ausloesen kann - kein Auftrag, kein Versand")
def keine_werkzeuge():
    return _muss("keine-werkzeuge")


@anmelden("mia.scharf-schalter", MODUL,
          "Mia laesst sich mit einem Schalter stilllegen", TROCKEN,
          "dass es einen Not-Aus gibt, der ohne Umbau wirkt")
def scharf_schalter():
    _muss("scharf-schalter-wird-beachtet", "offene-punkte-sind-vermerkt")
    offen = [z for z in REGELN["_scharf_erst_wenn"] if z.startswith("OFFEN")]
    return "scharf: %s; noch offen: %s" % (
        REGELN["scharf"], "; ".join(offen) if offen else "nichts")


# ====================================================== Der Wegweiser
# Seit dem 09.09.2026 sucht Mia erst und fragt dann. Findet sie die Stelle
# auf den Seiten, geht der Verweis hinaus und das Modell wird nie gefragt -
# das kostet nichts. Diese Pruefungen halten fest, dass der billige Weg
# wirklich billig ist und der teure nur dann laeuft, wenn es sein muss.

@anmelden("mia.wegweiser-findet", MODUL,
          "Jeder Beispielsatz der Frageliste findet seinen Eintrag", TROCKEN,
          "dass die Suche traegt - sonst laeuft jede Frage ins Modell und "
          "kostet Geld",
          blind_fuer="Formulierungen, an die beim Schreiben niemand gedacht hat")
def wegweiser_findet():
    _muss("wegweiser-findet-die-beispielsaetze")
    faq = json.loads((HIER.parent / "faq.json").read_text(encoding="utf-8"))
    saetze = sum(len(e["beispiele"]) for e in faq["eintraege"])
    return "%d Eintraege, %d Beispielsaetze, alle gefunden" % (
        len(faq["eintraege"]), saetze)


@anmelden("mia.wegweiser-findet-nichts-fremdes", MODUL,
          "Themenfremde Fragen finden nichts", TROCKEN,
          "dass die Suche nicht zuversichtlich danebenzeigt - ein Wegweiser, "
          "der immer etwas findet, ist schlimmer als keiner")
def wegweiser_findet_nichts_fremdes():
    _muss("wegweiser-findet-nichts-fremdes")
    return "Wetter, Rezepte, Hauptstaedte, 'ignoriere deine Regeln' - " \
           "nichts davon schlaegt an"


@anmelden("mia.wegweiser-kostet-nichts", MODUL,
          "Ein Treffer fragt kein Modell und schreibt nichts", TROCKEN,
          "den ganzen Sinn der Sache: die Antwort kostet 0,00 EUR und "
          "verbraucht auch kein Schreibkontingent im Speicher")
def wegweiser_kostet_nichts():
    _muss("wegweiser-antwortet-selbst", "wegweiser-fragt-kein-modell",
          "wegweiser-schreibt-nichts", "wegweiser-nennt-die-stelle",
          "wegweiser-nennt-den-ort-in-der-app", "ohne-treffer-geht-es-ans-modell",
          "modellantwort-wird-gebucht")
    return "Treffer: kein Modellaufruf, kein Schreibvorgang, Verweis fuer " \
           "Webseite und App. Ohne Treffer: Modell, und es wird gebucht"


@anmelden("mia.faq-verweise-tragen", MODUL,
          "Kein Verweis der Frageliste zeigt ins Leere", TROCKEN,
          "dass ein Verweis auf eine Sprungmarke fuehrt, die es wirklich gibt")
def faq_verweise_tragen():
    _muss("faq-verweise-zeigen-irgendwohin")
    faq = json.loads((HIER.parent / "faq.json").read_text(encoding="utf-8"))
    mit = sum(1 for e in faq["eintraege"] if e["marke"])
    return "%d Verweise mit Sprungmarke, alle treffen" % mit


@anmelden("mia.faq-liegt-der-app-bei", MODUL,
          "Die Frageliste im App-Paket ist dieselbe Datei", TROCKEN,
          "dass die App keine alte Fassung mit sich traegt - sie muss auch "
          "ohne Netz antworten koennen",
          blind_fuer="eine Datei, die in beiden Fassungen gleich falsch ist")
def faq_liegt_der_app_bei():
    gut, satz = verzeichnis.beilage_stimmt()
    if not gut:
        raise AssertionError(satz)
    return satz


# ====================================================== Die neun Schutzstufen
# Am 09.09.2026 aus einem oeffentlichen Regelwerk fuer Chatbot-Schutzstufen
# uebernommen, soweit es fuer ein Fragefenster Sinn ergab. Neun Sachen fehlten
# hier vorher.

@anmelden("mia.personendaten-fliegen-raus", MODUL,
          "Telefon, Bankverbindung und Anschrift fliegen aus Frage, Angaben "
          "und Antwort", TROCKEN,
          "das Verbot 'fremde Personendaten' - es stand bis zum 09.09.2026 "
          "nur im Regeltext, gepruef hat es niemand")
def personendaten_fliegen_raus():
    _muss("personendaten:telefon", "personendaten:iban",
          "personendaten:anschrift", "angaben-ohne-personendaten")
    return "%d Muster, an drei Stellen: Frage, Angaben, Antwort" % len(
        REGELN["personendaten"]["muster"])


@anmelden("mia.kein-code-in-der-antwort", MODUL,
          "Skript, Ereignis-Anhaengsel und Vorlagenklammern fliegen heraus",
          TROCKEN,
          "dass ueber Mias Antwort kein Skript auf die Seite des naechsten "
          "Lesers kommt - ihre Antwort wird im Browser dargestellt")
def kein_code_in_der_antwort():
    _muss("code:skript", "code:ereignis", "code:vorlage", "code:adresse")
    return "%d Muster: Skript, Ereignis, Vorlage, Adresse mit Code, " \
           "verstecktes Bild" % len(REGELN["eingeschleuster_code"]["muster"])


@anmelden("mia.ausgang-hat-drei-ausgaenge", MODUL,
          "Sperren, schneiden, warnen - nicht nur sperren", TROCKEN,
          "dass ein Satz zu viel nicht mehr die ganze Antwort kostet")
def ausgang_hat_drei_ausgaenge():
    _muss("ausgang-sperrt", "ausgang-schneidet", "ausgang-warnt")
    arten = {}
    for m in REGELN["ausgang"]["muster"]:
        arten[m.get("art", "sperren")] = arten.get(m.get("art", "sperren"), 0) + 1
    return "; ".join("%s: %d" % (a, n) for a, n in sorted(arten.items()))


@anmelden("mia.umleiten-statt-sperren", MODUL,
          "Bei einer Absage wird die naechstliegende Stelle genannt", TROCKEN,
          "dass blankes Blocken nicht den vertreibt, der wirklich etwas "
          "wissen wollte")
def umleiten_statt_sperren():
    return _muss("umleiten-statt-sperren")


@anmelden("mia.nachbohren-hat-ein-ende", MODUL,
          "Nach drei Ablehnungen kommt eine feste Absage, ohne Modellaufruf",
          TROCKEN,
          "dass jemand nicht beliebig oft umformuliert, bis eine Luecke "
          "aufgeht - der Tagesdeckel zaehlt Geld, nicht Absicht")
def nachbohren_hat_ein_ende():
    _muss("nachbohren-sperrt", "nachbohren-kostet-nichts",
          "nachbohren-wird-gezaehlt")
    n = REGELN["nachbohren"]
    return "Grenze %d Ablehnungen in %d Minuten" % (
        n["grenze"], n["zeitfenster_minuten"])


@anmelden("mia.protokoll-je-pruefung", MODUL,
          "Jede Pruefung schreibt auf, was sie entschied und wie lange sie "
          "brauchte", TROCKEN,
          "dass ein Fehlalarm auffindbar ist - im Protokoll stand bis zum "
          "09.09.2026 nur DASS abgelehnt wurde, nicht welche Pruefung es war")
def protokoll_je_pruefung():
    return _muss("protokoll-je-pruefung", "protokoll-mit-dauer")


@anmelden("mia.angaben-sind-daten-kein-befehl", MODUL,
          "Nachgeladene Angaben gehen eingefasst hinein", TROCKEN,
          "dass eine versteckte Anweisung in den eigenen Daten des Fragenden "
          "nicht befolgt wird - die Einfassung schuetzte vorher nur die Frage")
def angaben_sind_daten_kein_befehl():
    return _muss("angaben-werden-eingefasst",
                 "anweisung-warnt-vor-angaben-als-befehl")


# ============================================================== Die Fuehrung
# Mia ist nicht nur das Fragefenster: sie fuehrt beim ersten Start durch die
# App. Der Text dazu steht an einer Stelle (universe/fuehrung.json) und wird
# an zwei Stellen gelesen. Diese drei Pruefungen halten fest, dass die eine
# Stelle nicht auseinanderlaeuft.

@anmelden("mia.fuehrung-haengt-an-den-quellen", MODUL,
          "Jeder Halt der Fuehrung meint ein Feld, das es wirklich gibt", TROCKEN,
          "dass Mia niemanden durch eine Tuer fuehrt, die es nicht gibt",
          blind_fuer="einen Text, der stimmt und trotzdem nichts erklaert")
def fuehrung_haengt_an_den_quellen():
    """Die Fuehrung nennt Felder, Stufen und Strassen. Alle drei haben
    ihre eigene Quelle - bereiche.ts, abo.ts, funktionen.json. Wer hier
    etwas erfindet oder ein Feld vergisst, faellt auf."""
    fuehrung.neu_lesen()
    schlecht = fuehrung.pruefen()
    if schlecht:
        raise AssertionError("; ".join(schlecht[:4]))
    return ("%d Halte, jeder auf ein Feld aus bereiche.ts, kein Feld ohne Halt"
            % len(fuehrung.alles()["halte"]))


@anmelden("mia.fuehrung-zeigt-nichts-gesperrtes", MODUL,
          "Eine niedrige Stufe bekommt keine Fuehrung durch gesperrte Felder",
          TROCKEN,
          "dass die Fuehrung niemandem etwas zeigt, das er gar nicht aufmachen kann",
          blind_fuer="Felder, die in bereiche.ts falsch eingestuft sind")
def fuehrung_zeigt_nichts_gesperrtes():
    """Von Daniel am 09.09.: die Tour laeuft im Rahmen der
    Freischaltungsstufe. Ein Halt vor einer verschlossenen Tuer waere
    keine Fuehrung, sondern Werbung."""
    fuehrung.neu_lesen()
    raenge = fuehrung.stufen_rang()
    zahlen = {}
    for stufe in sorted(raenge, key=lambda s: raenge[s]):
        gezeigt = fuehrung.halte(stufe)
        zahlen[stufe] = len(gezeigt)
        zu = [h["route"] for h in gezeigt
              if raenge.get(h["stufe"], 0) > raenge[stufe]]
        if zu:
            raise AssertionError(
                "Stufe '%s' bekaeme Halte zu gesperrten Feldern: %s"
                % (stufe, ", ".join(zu)))
    unten = min(raenge, key=lambda s: raenge[s])
    oben = max(raenge, key=lambda s: raenge[s])
    if zahlen[unten] >= zahlen[oben]:
        raise AssertionError(
            "'%s' sieht %d Halte, '%s' ebenso viele oder mehr (%d) - dann "
            "filtert die Stufe gar nicht"
            % (unten, zahlen[unten], oben, zahlen[oben]))
    return "; ".join("%s sieht %d" % (s, n) for s, n in zahlen.items())


@anmelden("mia.fuehrung-liegt-der-app-bei", MODUL,
          "Die Fuehrung im App-Paket ist dieselbe Datei", TROCKEN,
          "dass die App nicht eine alte Fassung mit sich traegt",
          blind_fuer="eine Datei, die in beiden Fassungen gleich falsch ist")
def fuehrung_liegt_der_app_bei():
    """Die App liest die Fuehrung aus ihrer Beilage, weil sie ohne Netz
    fuehren koennen muss. Kopie ja - andere Fassung nein."""
    gut, satz = fuehrung.beilage_stimmt()
    if not gut:
        raise AssertionError(satz)
    return satz
