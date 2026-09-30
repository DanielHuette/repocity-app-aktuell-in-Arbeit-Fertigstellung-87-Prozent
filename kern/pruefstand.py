"""Der Pruefstand - was laeuft wirklich, was nur trocken, was ist ungeprueft.

Warum es ihn gibt: Ohne ihn behauptet jeder Teil des Universe, er
funktioniere. Sieben Agenten laufen, drei laufen trocken, neunzehn sind nur
gedacht - das laesst sich von aussen nicht unterscheiden, wenn niemand es
misst.

Drei Arten von Pruefung, streng getrennt:

  TROCKEN   laeuft ohne Netz und ohne Geld. Alles, was Mechanik ist:
            schreibt eine Datei richtig, wird ein Nein ohne Grund
            abgewiesen, greift eine Gruppenregel bei beiden Klassen.
            Das ist der groesste Teil und der, der taeglich laufen soll.

  NAH       laeuft gegen echte Dienste, aber mit dem billigsten Modell und
            der kleinsten Menge - eine Einbettung, eine Anfrage. Kostet
            Bruchteile eines Cent und ist einem echten Lauf sehr nah:
            derselbe Schluessel, dasselbe Netz, dasselbe Format.

  ECHT      erzeugt wirklich etwas und kostet wirklich Geld. Laeuft nur,
            wenn der Topf, zu dem sein Modul gehoert, noch Rest hat.

Die Grenzen stehen in universe/kosten.json, je Topf getrennt. Ein
Echttest, der nicht mehr in den Rest passt, wird nicht ausgefuehrt - er
wird als 'uebersprungen, Grenze' vermerkt. Nichts laeuft an einer Grenze
vorbei.

Was dabei herauskommt:
  PRUEFSTAND.md    die Wahrheit, in Obsidian lesbar, im Git-Log verfolgbar
  pruefstand.html  dieselbe Tabelle zum Aufmachen im Browser

Aufruf:
    python pruefstand.py trocken            alles ohne Kosten
    python pruefstand.py nah                zusaetzlich die billigen Echtwege
    python pruefstand.py echt prod.video.clip
    python pruefstand.py uebersicht         nur den Bericht neu schreiben
    python pruefstand.py grenze             was die Toepfe hergeben
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
NEUSTART = UNIVERSE.parent
sys.path.insert(0, str(HIER))

BERICHT_MD = NEUSTART / "PRUEFSTAND.md"
BERICHT_HTML = NEUSTART / "pruefstand.html"
PROTOKOLL = UNIVERSE / "zustand" / "pruefstand.jsonl"

TROCKEN, NAH, ECHT = "trocken", "nah", "echt"
ARTEN = (TROCKEN, NAH, ECHT)

import verbrauch  # noqa: E402  - Geld steht an genau einer Stelle


# ------------------------------------------------------------------ Anmeldung

@dataclass
class Pruefung:
    kennung: str
    modul: str
    name: str
    art: str
    zeigt: str
    lauf: object
    kosten_schaetzung: float = 0.0
    #: Was diese Pruefung NICHT zeigen kann - ehrlich, damit niemand mehr
    #: hineinliest, als drinsteht.
    blind_fuer: str = ""


_angemeldet: list[Pruefung] = []


def anmelden(kennung: str, modul: str, name: str, art: str, zeigt: str,
             kosten_schaetzung: float = 0.0, blind_fuer: str = ""):
    """Dekorator. Jede Pruefung meldet sich selbst an."""
    def nimm(funktion):
        if art not in ARTEN:
            raise ValueError("unbekannte Art: %s" % art)
        _angemeldet.append(Pruefung(kennung, modul, name, art, zeigt,
                                    funktion, kosten_schaetzung, blind_fuer))
        return funktion
    return nimm


def laden(datei: str | Path, name: str):
    """Ein Modul aus einer Datei laden, unter einem eindeutigen Namen.

    Warum das noetig ist: main.py gibt es zwoelfmal im Universe, meldung.py
    elfmal, einstellungen.py zehnmal. Python haelt nur ein Modul je Namen -
    wer zuerst geladen wird, gewinnt fuer alle. Ein "import main" in der
    Pruefung des Social-Media-Managers hat schon den Ausbilder erwischt.

    Wer hier laedt, bekommt genau die Datei, die er nennt.
    """
    datei = Path(datei)
    ordner = str(datei.parent)
    if ordner not in sys.path:
        sys.path.append(ordner)
    beschreibung = importlib.util.spec_from_file_location(name, datei)
    modul = importlib.util.module_from_spec(beschreibung)
    sys.modules[name] = modul
    beschreibung.loader.exec_module(modul)
    return modul


def _einsammeln() -> list[Pruefung]:
    """Sucht in jedem Agentenordner nach pruefungen.py und laedt sie."""
    _angemeldet.clear()
    for datei in sorted(UNIVERSE.glob("*/pruefungen.py")):
        sys.path.insert(0, str(datei.parent))
        try:
            name = "pruefungen_" + datei.parent.name
            lade = importlib.util.spec_from_file_location(name, datei)
            modul = importlib.util.module_from_spec(lade)
            lade.loader.exec_module(modul)
        except Exception as fehler:
            print("  ! %s liess sich nicht laden: %s" % (datei.parent.name, fehler))
    return list(_angemeldet)


# ------------------------------------------------------------ Pruefstandgrenze
# Toepfe, Preise und Kurs stehen in universe/kosten.json - eine Stelle fuer
# alles, was mit Geld zu tun hat. Hier wird nur durchgereicht.
#
# Die Grenze hier ist KEINE Nutzergrenze. Der Nutzer setzt sich seine Marke
# selbst (universe/kostenbremse.json); die Zahl hier schuetzt das Werkzeug
# vor sich selbst, damit ein Testlauf nicht durchdreht.

def _grenzen() -> dict:
    return verbrauch.stammdaten()


def eur(usd: float) -> float:
    return verbrauch.eur(usd)


def preis(modell: str, stueck: int = 1) -> float:
    return verbrauch.preis(modell, stueck)


def _topf_von(modul: str) -> str:
    return verbrauch.topf_von(modul)


class Kasse:
    """Fuehrt Buch je Topf fuer diesen einen Pruefstandlauf.

    Die Pruefstandgrenze aus kosten.json gilt als Obergrenze fuer den
    gesamten Pruefstandlauf - ein Pruefstand soll nie mehr ausgeben als
    ein einzelner echter Lauf.
    """

    def __init__(self):
        self.toepfe = {name: verbrauch.pruefstand_grenze(name)
                       for name in _grenzen().get("toepfe", {})}
        self.verbraucht = {name: 0.0 for name in self.toepfe}

    def rest(self, topf: str) -> float:
        return round(self.toepfe.get(topf, 0.0) - self.verbraucht.get(topf, 0.0), 4)

    def passt(self, modul: str, betrag: float) -> tuple[bool, str]:
        topf = _topf_von(modul)
        if betrag <= 0:
            return True, topf
        return (betrag <= self.rest(topf)), topf

    def buchen(self, modul: str, betrag: float) -> None:
        topf = _topf_von(modul)
        self.verbraucht[topf] = round(self.verbraucht.get(topf, 0.0) + betrag, 4)
        if betrag > 0:
            # Als Pruefung gebucht, nicht als Ausgabe: was hier laeuft,
            # ist ein Pruefstandlauf und darf den Bericht nicht verfaelschen.
            verbrauch.buchen(modul, betrag, wofuer="Pruefstand",
                             herkunft=verbrauch.PRUEFUNG)


# ------------------------------------------------------------------ Laufen

@dataclass
class Ergebnis:
    pruefung: Pruefung
    stand: str            # bestanden | durchgefallen | uebersprungen
    dauer: float = 0.0
    kosten: float = 0.0
    text: str = ""
    spur: str = ""


#: Laeuft der Pruefstand gerade? Wer waehrend eines Laufs einen zweiten
#: anstoesst, zieht sich den Boden unter den Fuessen weg: das Einsammeln leert
#: die Liste der angemeldeten Pruefungen und liest alle Module neu ein - mitten
#: in der Pruefung, die gerade laeuft. Die Pruefstrasse fragt hier nach, bevor
#: sie nachprueft.
_im_lauf = False


def im_lauf() -> bool:
    return _im_lauf


def laufen(arten: tuple[str, ...] = (TROCKEN,), modul: str | None = None,
           laut: bool = True) -> list[Ergebnis]:
    global _im_lauf
    if _im_lauf:
        return []
    _im_lauf = True
    try:
        return _laufen_wirklich(arten, modul, laut)
    finally:
        _im_lauf = False


def _laufen_wirklich(arten: tuple[str, ...], modul: str | None,
                     laut: bool) -> list[Ergebnis]:
    pruefungen = _einsammeln()
    kasse = Kasse()
    ergebnisse: list[Ergebnis] = []

    for p in pruefungen:
        if p.art not in arten:
            continue
        if modul and p.modul != modul and not p.modul.startswith(modul + "."):
            continue

        passt, topf = kasse.passt(p.modul, p.kosten_schaetzung)
        if not passt:
            ergebnisse.append(Ergebnis(p, "uebersprungen", 0.0, 0.0,
                                       "Pruefstandgrenze: Topf '%s' hat noch "
                                       "%.2f EUR, gebraucht wuerden %.2f EUR"
                                       % (topf, kasse.rest(topf), p.kosten_schaetzung)))
            if laut:
                print("  - %-34s uebersprungen (Grenze)" % p.kennung)
            continue

        anfang = time.time()
        try:
            rueckgabe = p.lauf()
            kosten = 0.0
            text = ""
            if isinstance(rueckgabe, dict):
                kosten = float(rueckgabe.get("kosten", 0.0))
                text = str(rueckgabe.get("text", ""))
            elif isinstance(rueckgabe, str):
                text = rueckgabe
            kasse.buchen(p.modul, kosten)
            e = Ergebnis(p, "bestanden", time.time() - anfang, kosten, text)
        except Exception as fehler:
            e = Ergebnis(p, "durchgefallen", time.time() - anfang, 0.0,
                         str(fehler), traceback.format_exc(limit=4))
        ergebnisse.append(e)
        if laut:
            zeichen = {"bestanden": "+", "durchgefallen": "!"}[e.stand]
            geld = ("  %.4f EUR" % e.kosten) if e.kosten else ""
            print("  %s %-34s %5.2f s%s" % (zeichen, p.kennung, e.dauer, geld))
            if e.stand == "durchgefallen":
                print("      %s" % e.text)

    _protokollieren(ergebnisse, kasse)
    _als_erfahrung(ergebnisse)
    bericht_schreiben(ergebnisse, kasse)
    return ergebnisse


def _protokollieren(ergebnisse: list[Ergebnis], kasse: Kasse) -> None:
    try:
        PROTOKOLL.parent.mkdir(parents=True, exist_ok=True)
        with PROTOKOLL.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps({
                "zeitpunkt": datetime.now().isoformat(timespec="seconds"),
                "bestanden": sum(1 for e in ergebnisse if e.stand == "bestanden"),
                "durchgefallen": sum(1 for e in ergebnisse if e.stand == "durchgefallen"),
                "uebersprungen": sum(1 for e in ergebnisse if e.stand == "uebersprungen"),
                "kosten": round(sum(e.kosten for e in ergebnisse), 4),
                "je_topf": kasse.verbraucht,
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _als_erfahrung(ergebnisse: list[Ergebnis]) -> None:
    """Durchgefallene Pruefungen gehen als Erfahrung ins 2nd Brain.

    Damit lernen die Agenten auch aus fehlgeschlagenen Laeufen - eine
    durchgefallene Pruefung ist ein Nein mit Begruendung wie jedes andere.
    """
    durchgefallen = [e for e in ergebnisse if e.stand == "durchgefallen"]
    if not durchgefallen:
        return
    try:
        import rueckweg
    except ImportError:
        return
    for e in durchgefallen:
        try:
            rueckweg.erfahrung_ablegen(
                auftrag="pruefung-" + e.pruefung.kennung,
                modul=e.pruefung.modul,
                was_versucht="Pruefung %s (%s): %s"
                             % (e.pruefung.kennung, e.pruefung.art, e.pruefung.name),
                befund=e.spur[:1200] or e.text,
                urteil="nein",
                grund=e.text or "Pruefung durchgefallen",
                durchlaeufe=1,
                kosten=e.kosten,
                dauer_minuten=round(e.dauer / 60, 2),
                art=rueckweg.PRUEFUNG)
        except Exception:
            pass


# ------------------------------------------------------------------ Bericht

def _module_ohne_pruefung(pruefungen: list[Pruefung]) -> list[str]:
    """Welche Module gar nicht geprueft werden - das ist die wichtigste Spalte."""
    try:
        briefe = json.loads((UNIVERSE / "gehirn.json").read_text(encoding="utf-8"))
        alle = [k for k in briefe.get("steckbriefe", {}) if k != "standard"]
    except (OSError, json.JSONDecodeError):
        return []
    geprueft = {p.modul for p in pruefungen}
    return sorted(m for m in alle if m not in geprueft)


def bericht_schreiben(ergebnisse: list[Ergebnis] | None = None,
                      kasse: Kasse | None = None) -> Path:
    pruefungen = _einsammeln()
    kasse = kasse or Kasse()
    ergebnisse = ergebnisse or []
    nach_kennung = {e.pruefung.kennung: e for e in ergebnisse}
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M")

    zeilen = [
        "# Pruefstand",
        "",
        "Geschrieben am %s. Diese Datei wird bei jedem Lauf ueberschrieben." % jetzt,
        "",
        "Sie beantwortet drei Fragen: Was laeuft wirklich? Was ist nur trocken",
        "geprueft und damit noch nicht bewiesen? Und was ist ueberhaupt nicht",
        "geprueft?",
        "",
        "## Was die drei Arten heissen",
        "",
        "| Art | Was sie beweist | Was sie nicht beweist | Kosten |",
        "|---|---|---|---|",
        "| **trocken** | Die Mechanik stimmt: Dateien, Zustaende, Sperren, Rechnungen. | Dass ein echter Dienst antwortet oder dass ein Ergebnis gut aussieht. | keine |",
        "| **nah** | Derselbe Schluessel, dasselbe Netz, dasselbe Format wie im Echtbetrieb - nur mit dem billigsten Modell und der kleinsten Menge. | Dass das Ergebnis in voller Groesse auch taugt. | Bruchteile eines Cent |",
        "| **echt** | Es entsteht wirklich etwas, so wie es spaeter entsteht. | Nichts weiter - das ist der Beweis. | siehe Pruefstandgrenze |",
        "",
    ]

    if ergebnisse:
        b = sum(1 for e in ergebnisse if e.stand == "bestanden")
        d = sum(1 for e in ergebnisse if e.stand == "durchgefallen")
        u = sum(1 for e in ergebnisse if e.stand == "uebersprungen")
        ampel = "GRUEN" if d == 0 and b else ("ROT" if d else "GRAU")
        zeilen += ["## Letzter Lauf", "",
                   "**%s** - %d bestanden, %d durchgefallen, %d uebersprungen, "
                   "%.4f EUR verbraucht." % (ampel, b, d, u,
                                             sum(e.kosten for e in ergebnisse)),
                   ""]
        if d:
            zeilen += ["Durchgefallen:", ""]
            for e in ergebnisse:
                if e.stand == "durchgefallen":
                    zeilen.append("- `%s` (%s) - %s" % (e.pruefung.kennung,
                                                        e.pruefung.modul, e.text))
            zeilen.append("")

    zeilen += ["## Die Pruefungen", "",
               "| Kennung | Modul | Art | Was sie zeigt | Blind fuer | Kosten | Letzter Stand |",
               "|---|---|---|---|---|---|---|"]
    for p in sorted(pruefungen, key=lambda x: (x.modul, x.art, x.kennung)):
        e = nach_kennung.get(p.kennung)
        stand = {"bestanden": "bestanden", "durchgefallen": "**durchgefallen**",
                 "uebersprungen": "uebersprungen"}.get(e.stand if e else "", "nicht gelaufen")
        kosten = "-" if not p.kosten_schaetzung else "%.4f EUR" % p.kosten_schaetzung
        zeilen.append("| `%s` | %s | %s | %s | %s | %s | %s |"
                      % (p.kennung, p.modul, p.art, p.zeigt,
                         p.blind_fuer or "-", kosten, stand))
    zeilen.append("")

    ohne = _module_ohne_pruefung(pruefungen)
    zeilen += ["## Ueberhaupt nicht geprueft", "",
               "Diese Teile des Universe haben keine einzige Pruefung. Was sie",
               "koennen, ist damit Behauptung - nicht Befund.", ""]
    if ohne:
        for m in ohne:
            zeilen.append("- `%s`" % m)
    else:
        zeilen.append("Keiner - jedes Modul hat mindestens eine Pruefung.")
    zeilen.append("")

    zeilen += ["## Pruefstandgrenze", "",
               "| Topf | Grenze je Pruefstandlauf | verbraucht | wofuer |",
               "|---|---|---|---|"]
    for name, topf in _grenzen().get("toepfe", {}).items():
        zeilen.append("| %s | %.2f EUR | %.4f EUR | %s |"
                      % (name, float(topf.get("pruefstand_grenze_je_lauf", 0)),
                         kasse.verbraucht.get(name, 0.0), topf.get("warum", "")))
    zeilen += ["",
               "Ein Echttest, der nicht mehr in den Rest seines Topfes passt, wird",
               "nicht ausgefuehrt. Die Grenzen stehen in `universe/kosten.json` als",
                   "`pruefstand_grenze_je_lauf` - das ist keine Nutzergrenze.",
               "",
               "## Wie man Kosten klein haelt",
               "",
               "1. **Trocken zuerst.** Alles, was Mechanik ist, gehoert in eine",
               "   Trockenpruefung. Was dort schon durchfaellt, braucht keinen Echtlauf.",
               "2. **Nah statt echt, wo es geht.** Ein Bild in 512 Pixeln mit dem",
               "   schnellen Modell beweist, dass der Weg steht. Die Aufloesung",
               "   beweist nichts, was der kleine Lauf nicht auch zeigt.",
               "3. **Ein Echtlauf je Aenderung, nicht je Idee.** Erst alle",
               "   Trockenpruefungen gruen, dann einmal echt.",
               "4. **Startwerte festhalten.** Ein gemerkter Startwert liefert",
               "   dasselbe Bild noch einmal, ohne es neu zu bezahlen.",
               "5. **Die Pruefstandgrenze ist keine Warnung, sondern eine Sperre.** Sie darf",
               "   ruhig knapp sein - ein uebersprungener Test kostet nur Zeit.",
               ""]

    BERICHT_MD.write_text("\n".join(zeilen), encoding="utf-8", newline="")
    _html_schreiben(pruefungen, nach_kennung, kasse, ohne, jetzt)
    return BERICHT_MD


def _html_schreiben(pruefungen, nach_kennung, kasse, ohne, jetzt) -> None:
    farbe = {"bestanden": "#2e7d32", "durchgefallen": "#c62828",
             "uebersprungen": "#f9a825", "nicht gelaufen": "#9e9e9e"}
    reihen = []
    for p in sorted(pruefungen, key=lambda x: (x.modul, x.art, x.kennung)):
        e = nach_kennung.get(p.kennung)
        stand = e.stand if e else "nicht gelaufen"
        reihen.append(
            '<tr><td><span class="punkt" style="background:%s"></span>%s</td>'
            '<td>%s</td><td>%s</td><td>%s</td><td class="leise">%s</td>'
            '<td class="zahl">%s</td></tr>'
            % (farbe.get(stand, "#9e9e9e"), p.kennung, p.modul, p.art, p.zeigt,
               p.blind_fuer or "&mdash;",
               "&mdash;" if not p.kosten_schaetzung else "%.4f&nbsp;&euro;" % p.kosten_schaetzung))
    toepfe = "".join(
        "<tr><td>%s</td><td class='zahl'>%.2f&nbsp;&euro;</td>"
        "<td class='zahl'>%.4f&nbsp;&euro;</td><td class='leise'>%s</td></tr>"
        % (name, float(t.get("pruefstand_grenze_je_lauf", 0)),
           kasse.verbraucht.get(name, 0.0), t.get("warum", ""))
        for name, t in _grenzen().get("toepfe", {}).items())
    ungeprueft = "".join("<li><code>%s</code></li>" % m for m in ohne) or \
                 "<li>Keiner &mdash; jedes Modul hat mindestens eine Pruefung.</li>"

    BERICHT_HTML.write_text("""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<title>Pruefstand</title>
<style>
 :root{color-scheme:light dark}
 body{font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:32px;
      background:#fbfaf8;color:#1b1b1b;max-width:1180px}
 h1{font-size:26px;margin:0 0 4px} h2{font-size:17px;margin:34px 0 10px}
 .leise{color:#6b6b6b} .zahl{text-align:right;white-space:nowrap}
 table{border-collapse:collapse;width:100%%;font-size:14px}
 th{text-align:left;font-weight:600;border-bottom:2px solid #ddd;padding:7px 10px}
 td{border-bottom:1px solid #eee;padding:7px 10px;vertical-align:top}
 tr:hover td{background:#f3f1ed}
 .punkt{display:inline-block;width:9px;height:9px;border-radius:50%%;margin-right:8px}
 code{background:#efece7;padding:1px 5px;border-radius:4px;font-size:13px}
 .karte{background:#fff;border:1px solid #e6e2db;border-radius:12px;padding:16px 20px;margin:14px 0}
 @media (prefers-color-scheme:dark){
  body{background:#151413;color:#e9e6e1} tr:hover td{background:#1f1e1c}
  th{border-color:#333} td{border-color:#262523} code{background:#262523}
  .karte{background:#1c1b19;border-color:#302e2b} .leise{color:#9d9890}}
</style></head><body>
<h1>Pruefstand</h1>
<p class="leise">Stand %s &middot; erzeugt aus PRUEFSTAND.md</p>

<div class="karte">
<b>trocken</b> &mdash; die Mechanik stimmt. Kostet nichts, beweist aber nicht,
dass ein echter Dienst antwortet.<br>
<b>nah</b> &mdash; derselbe Schluessel, dasselbe Netz, dasselbe Format wie im
Echtbetrieb, nur kleinste Menge. Bruchteile eines Cent.<br>
<b>echt</b> &mdash; es entsteht wirklich etwas. Laeuft nur innerhalb der Grenze.
</div>

<h2>Die Pruefungen</h2>
<table><tr><th>Kennung</th><th>Modul</th><th>Art</th><th>Was sie zeigt</th>
<th>Blind fuer</th><th>Kosten</th></tr>%s</table>

<h2>Ueberhaupt nicht geprueft</h2>
<p class="leise">Was diese Teile koennen, ist Behauptung &mdash; nicht Befund.</p>
<ul>%s</ul>

<h2>Pruefstandgrenze</h2>
<table><tr><th>Topf</th><th>Grenze je Pruefstandlauf</th><th>verbraucht</th><th>wofuer</th></tr>%s</table>
</body></html>""" % (jetzt, "".join(reihen), ungeprueft, toepfe), encoding="utf-8", newline="")


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "trocken").lower()
    modul = argumente[1] if len(argumente) > 1 else None

    if befehl == "trocken":
        print("Trockenlauf - kostet nichts.")
        ergebnisse = laufen((TROCKEN,), modul)
    elif befehl == "nah":
        print("Trocken und nah - kostet Bruchteile eines Cent.")
        ergebnisse = laufen((TROCKEN, NAH), modul)
    elif befehl == "echt":
        if not modul:
            print("Echttests laufen nur fuer ein genanntes Modul:")
            print("  python pruefstand.py echt prod.video.clip")
            return 2
        print("Echtlauf fuer %s - innerhalb der Pruefstandgrenze." % modul)
        ergebnisse = laufen((TROCKEN, NAH, ECHT), modul)
    elif befehl == "uebersicht":
        bericht_schreiben()
        print("geschrieben: %s\n            %s" % (BERICHT_MD, BERICHT_HTML))
        return 0
    elif befehl in ("grenze", "deckel"):
        kasse = Kasse()
        for name, topf in _grenzen().get("toepfe", {}).items():
            print("%-22s %6.2f EUR   %s" % (name, kasse.toepfe.get(name, 0),
                                            topf.get("warum", "")))
            for m in topf.get("module", []):
                print("    %s" % m)
        return 0
    else:
        print(__doc__)
        return 2

    d = sum(1 for e in ergebnisse if e.stand == "durchgefallen")
    print("\n%d bestanden, %d durchgefallen, %d uebersprungen, %.4f EUR"
          % (sum(1 for e in ergebnisse if e.stand == "bestanden"), d,
             sum(1 for e in ergebnisse if e.stand == "uebersprungen"),
             sum(e.kosten for e in ergebnisse)))
    print("Bericht: %s" % BERICHT_MD)
    return 1 if d else 0


if __name__ == "__main__":
    # Die Pruefungen schreiben sich in *ihre* Sicht auf dieses Modul ein.
    # Als "__main__" waere das eine zweite, leere Liste - darum hier bewusst
    # ueber den Modulnamen gehen, damit beide dieselbe Liste sehen.
    import pruefstand as selbst

    raise SystemExit(selbst._main(sys.argv[1:]))
