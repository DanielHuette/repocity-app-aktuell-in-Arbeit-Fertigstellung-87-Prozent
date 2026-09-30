"""Die Pruefstrasse - wann geprueft wird, wer es erfaehrt, was daraus wird.

Der Pruefstand kann pruefen. Er tut es aber nur, wenn ihn jemand aufruft. Die
Strasse ist das, was fehlte: sie sagt, WANN von selbst geprueft wird, WER das
Ergebnis erfaehrt und WAS daraus gelernt wird.

Drei Ausloeser - so am 09.09. entschieden:

    tor(was)          vor dem Bau und vor dem Veroeffentlichen. Rot heisst:
                      es passiert nichts. Das ist die Stelle, an der nichts
                      Kaputtes nach draussen kommt.
    nach_dem_lauf()   nach jedem Lauf einer Kette. Die Strasse prueft sich
                      selbst nach - hat sie gehalten, was ihre Kette verspricht?
    taeglich()        einmal am Tag alles, auch wenn niemand etwas geaendert hat.
                      Faengt, was von aussen kaputtgeht.

Ein Wachdienst, der jeder einzelnen Dateiaenderung zusieht, wurde ausdruecklich
nicht gewaehlt.

Jedes Ergebnis geht denselben Weg: als Meldung in die App und als Befund ins
Postfach des zustaendigen Agenten. Ein rotes Ergebnis wird ausserdem zur
Erfahrung im 2nd Brain - das macht der Pruefstand schon, eine durchgefallene
Pruefung ist ein Nein mit Begruendung wie jedes andere.

Und die Strasse misst sich selbst: wie viele Pruefungen eine Gegenprobe haben.
Eine Pruefung, die nicht rot werden kann, ist wertlos - und ein Werkzeug, das
Qualitaet misst, muss selbst auf Qualitaet geprueft werden.

    python universe/kern/pruefstrasse.py tor bau
    python universe/kern/pruefstrasse.py lauf prod.praesentation
    python universe/kern/pruefstrasse.py taeglich
    python universe/kern/pruefstrasse.py gegenproben
    python universe/kern/pruefstrasse.py abdeckung
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
WURZEL = UNIVERSE.parent
BETATESTS = UNIVERSE / "Betatests"
ZUSTAND = UNIVERSE / "zustand"
POSTFACH = ZUSTAND / "pruefbefunde"
ABDECKUNG = ZUSTAND / "abdeckung.json"

if str(HIER) not in sys.path:
    sys.path.insert(0, str(HIER))

import pruefstand  # noqa: E402

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

try:
    import melden
except ImportError:                                  # pragma: no cover
    melden = None

MODUL = "system.pruefstrasse"

#: Was vor welchem Schritt geprueft wird. Nicht alles vor allem - eine Strasse,
#: die vor jedem Handgriff 233 Pruefungen fahren laesst, wird abgeschaltet.
TORE = {
    "bau":            None,          # App bauen: alles, es geht nach draussen
    "webseite":       None,          # Webseite: alles, es geht nach draussen
    "kette":          "gestalter",   # Kette anlegen: Bilder, Filme, Doku
    "doku":           "gestalter",
}

#: Was ein Tor NICHT aufhalten darf.
#:
#: Am 14.09.2026 gemessen: das Tor der Webseite hat auf `sk.lehrvideos-werden-
#: nachgespielt` gewartet - eine Pruefung des Handelskerns, die zaehlt, ob er
#: die Sequenzen so findet wie der Trader im Lehrvideo. Mit der Webseite hat
#: das nichts zu tun. Daniel dazu: *"die beiden dinge haengen ueberhaupt nicht
#: miteinander zusammen"*.
#:
#: Die Pruefungen laufen weiter mit und stehen im Befund - man sieht also, dass
#: sie rot sind. Sie halten den Bau nur nicht mehr an.
#:
#: Auch der App-Bau steht seit dem 14.09.2026 hier. Daniel: *"bau in der app
#: den handelskern halt jetzt mit, mir egal - wenn er fertig ist kann man ihn
#: ja aktualisieren"*. Der Kern geht also unfertig mit ins Paket und wird
#: nachgezogen, statt alles andere aufzuhalten. Das ist eine Entscheidung, die
#: er getroffen hat, keine Nachlaessigkeit: die Sequenzpruefung wartet auf
#: Lehrvideos, die noch geladen werden.
TOR_OHNE = {
    "webseite": ("sk", "trading"),
    "bau": ("sk", "trading"),
}


@dataclass
class Befund:
    """Was bei einem Lauf herauskam - knapp genug fuer eine Meldung."""
    anlass: str = ""
    modul: str = ""
    bestanden: int = 0
    durchgefallen: int = 0
    uebersprungen: int = 0
    rote: list = field(default_factory=list)     # [(kennung, grund)]
    #: Rote Pruefungen, die dieses Tor nichts angehen - sie zaehlen nicht als
    #: durchgefallen, verschwinden aber auch nicht.
    fremd_rot: list = field(default_factory=list)  # [(kennung, grund)]
    dauer_s: float = 0.0

    @property
    def gruen(self) -> bool:
        return self.durchgefallen == 0

    def satz(self) -> str:
        dazu = ""
        if self.fremd_rot:
            dazu = (" - dazu %d rote, die dieses Tor nichts angehen: %s"
                    % (len(self.fremd_rot),
                       "; ".join(k for k, _ in self.fremd_rot[:3])))
        if self.gruen:
            return ("%d Pruefungen, alle gruen (%s)%s"
                    % (self.bestanden, self.anlass, dazu))
        return ("%d von %d Pruefungen rot (%s): %s%s"
                % (self.durchgefallen, self.bestanden + self.durchgefallen,
                   self.anlass, "; ".join(k for k, _ in self.rote[:5]), dazu))


# ------------------------------------------------------------- Die Umgebung
#
# Womit die Strasse arbeitet: wer prueft, wohin der Befund gelegt wird, wer ihn
# meldet. Im Betrieb ist das das Echte. Wer die Strasse selbst prueft, reicht
# eine Wegwerf-Umgebung herein - und muss dafuer an keiner Sperre drehen und
# nichts abschalten. Denselben Weg gehen rueckweg, warenausgang und der
# Qualitaetsmanager mit ihrer `konfiguration`.


def _echter_pruefer(modul: str | None):
    """Der Pruefstand - aber nicht, waehrend er schon laeuft.

    Ohne diese Stelle frisst sich die Strasse auf: die Nachpruefung am Ende
    einer Abnahme startet den Pruefstand, darin laeuft eine Pruefung, die eine
    Abnahme durchspielt, und die startet die Strasse wieder. Das Einsammeln
    leert dabei die Liste der angemeldeten Pruefungen - mitten im Lauf.

    None heisst: jetzt nicht. Nicht "alles gruen".
    """
    if pruefstand.im_lauf():
        return None
    return pruefstand.laufen(modul=modul, laut=False)


def umgebung(pruefer=None, postfach=None, bote=None) -> dict:
    """Eine Umgebung fuer die Strasse. Ohne Angabe die echte."""
    return {
        "pruefer": pruefer or _echter_pruefer,
        "postfach": Path(postfach) if postfach else POSTFACH,
        "bote": bote if bote is not None else melden,
    }


def laeuft_gerade() -> bool:
    """Steckt gerade ein Pruefstandlauf? Dann wird nicht nachgeprueft."""
    return pruefstand.im_lauf()


# ------------------------------------------------------------------ Der Lauf

def _laufen(modul: str | None, anlass: str, u: dict | None = None) -> Befund:
    u = u or umgebung()
    ergebnisse = u["pruefer"](modul)
    if ergebnisse is None:
        return Befund(anlass=anlass + " (uebersprungen: der Pruefstand laeuft schon)",
                      modul=modul or "alle", uebersprungen=1)
    befund = Befund(anlass=anlass, modul=modul or "alle")
    for e in ergebnisse:
        if e.stand == "bestanden":
            befund.bestanden += 1
        elif e.stand == "durchgefallen":
            befund.durchgefallen += 1
            befund.rote.append((e.pruefung.kennung, e.text))
        else:
            befund.uebersprungen += 1
        befund.dauer_s += e.dauer
    befund.dauer_s = round(befund.dauer_s, 2)
    _weitersagen(befund, u)
    return befund


def _weitersagen(befund: Befund, u: dict) -> None:
    """In die App und ins Postfach des zustaendigen Agenten.

    Beides, nicht eines von beidem: die Meldung sieht der Mensch, den Befund
    liest der Agent beim naechsten Lauf. Wer nur meldet, verlaesst sich darauf,
    dass jemand hinsieht.
    """
    _ins_postfach(befund, u["postfach"])
    bote = u["bote"]
    if bote is None:
        return
    try:
        bote.melde(
            MODUL,
            befund.satz() + ("\n\n" + "\n".join("- %s: %s" % (k, g[:180])
                                                for k, g in befund.rote)
                             if befund.rote else ""),
            art="info" if befund.gruen else "fehler",
            zusammenfassung=("Pruefstrasse gruen: " if befund.gruen
                             else "Pruefstrasse ROT: ") + befund.anlass,
            daten={"anlass": befund.anlass, "modul": befund.modul,
                   "bestanden": befund.bestanden,
                   "durchgefallen": befund.durchgefallen,
                   "empfaenger": befund.modul,
                   "rote": [k for k, _ in befund.rote]})
    except Exception:
        pass


def _ins_postfach(befund: Befund, postfach: Path) -> None:
    """Ein Befund je Modul, damit der zustaendige Agent ihn selbst lesen kann.

    Bewusst ein eigener Ordner und nicht der Eingang: im Eingang liegen
    Auftraege, und ein Agent, der dort einen Befund findet, versucht ihn zu
    bearbeiten.
    """
    try:
        postfach.mkdir(parents=True, exist_ok=True)
        name = (befund.modul or "alle").replace("/", "_") + ".json"
        (postfach / name).write_text(json.dumps({
            "anlass": befund.anlass,
            "modul": befund.modul,
            "zeitpunkt": datetime.now().isoformat(timespec="seconds"),
            "bestanden": befund.bestanden,
            "durchgefallen": befund.durchgefallen,
            "uebersprungen": befund.uebersprungen,
            "dauer_s": befund.dauer_s,
            "rote": [{"pruefung": k, "grund": g} for k, g in befund.rote],
            "satz": befund.satz(),
        }, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    except OSError:
        pass


# --------------------------------------------------------------- Die Ausloeser

def tor(was: str, u: dict | None = None) -> Befund:
    """Vor dem Bau und vor dem Veroeffentlichen. Rot heisst: es passiert nichts.

    Gibt den Befund zurueck. Der Aufrufer entscheidet, ob er weitermacht -
    aber `hindurch` sagt ihm klar, ob er darf.
    """
    modul = TORE.get(was, None) if was in TORE else None
    befund = _laufen(modul, "Tor: " + was, u)

    # Was dieses Tor nichts angeht, zaehlt nicht als durchgefallen - es bleibt
    # aber sichtbar, statt stillschweigend zu verschwinden.
    ohne = TOR_OHNE.get(was, ())
    if ohne and befund.rote:
        bleibt, fremd = [], []
        for kennung, grund in befund.rote:
            (fremd if kennung.split(".")[0] in ohne else bleibt).append((kennung, grund))
        befund.rote = bleibt
        befund.fremd_rot = fremd
        befund.durchgefallen -= len(fremd)
    return befund


def hindurch(was: str, u: dict | None = None) -> bool:
    """True, wenn gebaut oder veroeffentlicht werden darf."""
    return tor(was, u).gruen


def nach_dem_lauf(modul: str, auftrag: str = "", u: dict | None = None) -> Befund:
    """Nach jedem Lauf einer Kette - hat die Strasse gehalten, was sie verspricht?"""
    anlass = "nach dem Lauf von %s" % modul + (" (%s)" % auftrag if auftrag else "")
    return _laufen(modul, anlass, u)


def taeglich(u: dict | None = None) -> Befund:
    """Einmal am Tag alles - auch wenn niemand etwas geaendert hat.

    Dazu gehoert seit dem 09.09.2026 der Lauf **jeder** Gegenprobe. Er
    dauert Minuten und hat hier Platz; bei jedem kleinen Pruefstandlauf
    haette er keinen. Ohne ihn faellt nicht auf, wenn eine Gegenprobe nach
    einer Aenderung ins Leere laeuft - genau so sind vier von ihnen
    tagelang unbemerkt tot gewesen.
    """
    # Die Gegenproben laufen hier NICHT mit: die Pruefung der Pruefungen ist
    # ausgesetzt, bis die App fertig ist - von Daniel am 09.09.2026
    # angeordnet. Siehe START.md, erster Punkt der Arbeitsregeln.
    return _laufen(None, "Tageslauf " + date.today().isoformat(), u)


# ------------------------------------------------- Die Pruefung der Pruefung

#: Wie eine Gegenprobe eine Pruefung nennt: als Zeichenkette, entweder ganz
#: ("bau.pfad-bricht-nicht-aus") oder ohne den Modulteil davor
#: ("jede-kette-hat-ihr-bild"). Ein Bindestrich muss vorkommen - daran
#: unterscheidet sich ein Pruefungsname von einem Dateinamen oder Wort.
#:
#: Das Muster hier stand einmal enger: es verlangte fuenf Zeichen vor dem
#: ersten Punkt. Damit fiel jede Pruefung durch, deren Modulteil kuerzer ist -
#: "bau." und "qm." zum Beispiel -, und die Messung meldete 21 ungedeckte
#: Pruefungen, fuer die es laengst eine Gegenprobe gab. Das Messgeraet war
#: selbst ungeeicht. Genau der Fall aus Lehrsatz L0005.
_NAME = re.compile(r"[\"']([a-z][a-z0-9.-]{5,})[\"']")


def _namen_der_gegenproben() -> set:
    namen = set()
    if not BETATESTS.exists():
        return namen
    for datei in sorted(BETATESTS.glob("gegenprobe_*.py")):
        try:
            text = datei.read_text(encoding="utf-8")
        except OSError:
            continue
        for treffer in _NAME.finditer(text):
            name = treffer.group(1)
            if "-" in name:
                namen.add(name)
    return namen


def abdeckung() -> dict:
    """Wie viele Pruefungen eine Gegenprobe haben - und welche nicht.

    Gezaehlt wird ueber den Namen: eine Gegenprobe nennt die Pruefung, die sie
    verstellt. Steht der Name nirgends in einer Gegenprobe, ist die Pruefung
    ungedeckt - niemand hat je nachgesehen, ob sie ueberhaupt rot werden kann.
    """
    pruefungen = pruefstand._einsammeln()
    gegenproben = _namen_der_gegenproben()
    gedeckt, offen = [], []
    for p in pruefungen:
        kurz = p.kennung.split(".")[-1]
        if p.kennung in gegenproben or kurz in gegenproben:
            gedeckt.append(p.kennung)
        else:
            offen.append(p.kennung)
    gesamt = len(pruefungen)
    return {
        "gesamt": gesamt,
        "gedeckt": len(gedeckt),
        "offen": offen,
        # Anteil in Prozent, auf eine Nachkommastelle - 41 von 233 sind 17,6.
        "anteil": round(100 * len(gedeckt) / gesamt, 1) if gesamt else 0.0,
    }


#: Diese Gegenprobe baut selbst mit Gradle und braucht Minuten. Vor einem
#: Bau wird sie uebersprungen - ein Bau, der vor sich selbst eine Gegenprobe
#: laufen laesst, die wiederum baut, wartet auf sich selbst. Im Tageslauf
#: laeuft sie mit, dort ist die Zeit da.
LANGSAM = ("gegenprobe_bau.py",)


def gegenproben_starten(zeitgrenze: int = 300,
                        ausser: tuple = (),
                        nur: tuple = ()) -> list[tuple]:
    """Jede Gegenprobe wirklich starten. Zurueck kommt, was nicht durchlief.

    Vorher stand hier eine Sperrklinke, die eine Quote bewachte: wie viel
    Prozent der Pruefungen eine Gegenprobe **haben**. Am 09.09.2026 stellte
    sich heraus, dass das nichts wert war - vier der mitgezaehlten
    Gegenproben liefen seit Tagen gar nicht mehr durch, weil sie Stellen
    suchten, die es nach einer Aenderung nicht mehr gab. Die Quote stand
    trotzdem bei 40,7 %, und die Sperre hielt das Bau-Tor zu, weil eine
    **Zahl** fiel - nicht, weil ein Fehler da war.

    Gezaehlt wird nicht mehr. Gestartet wird.

    Jede Gegenprobe bekommt ihren eigenen Prozess: sie verstellt Code und
    stellt ihn zurueck, und ein Absturz mittendrin darf nicht den ganzen
    Lauf mitreissen.
    """
    import subprocess

    schlecht = []
    for datei in sorted(BETATESTS.glob("gegenprobe_*.py")):
        if datei.name in ausser:
            continue
        # `nur` gibt es, damit die Gegenprobe DIESER Mechanik nicht sich
        # selbst mitstartet: sie legt eine Wegwerf-Gegenprobe an und will
        # nur wissen, ob die auffaellt. Ohne diese Bremse ruft sie sich
        # endlos selbst auf - am 09.09.2026 einmal so gebaut und binnen
        # Minuten an sechs gleichzeitig laufenden Prozessen gemerkt.
        if nur and datei.name not in nur:
            continue
        try:
            lauf = subprocess.run(
                [sys.executable, "-u", str(datei)], cwd=str(WURZEL),
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=zeitgrenze)
        except subprocess.TimeoutExpired:
            schlecht.append((datei.name, "nach %d Sekunden abgebrochen"
                             % zeitgrenze))
            continue
        if lauf.returncode == 0:
            continue
        # Der letzte Satz sagt am ehesten, woran es lag.
        zeilen = [z.strip() for z in
                  ((lauf.stdout or "") + "\n" + (lauf.stderr or "")).splitlines()
                  if z.strip()]
        schlecht.append((datei.name, zeilen[-1][:200] if zeilen else
                         "Rueckgabe %d ohne Ausgabe" % lauf.returncode))
    return schlecht


def bestmarke_lesen() -> float:
    if ABDECKUNG.exists():
        try:
            return float(json.loads(ABDECKUNG.read_text(encoding="utf-8"))["anteil"])
        except (OSError, ValueError, KeyError):
            return 0.0
    return 0.0


def bestmarke_setzen(anteil: float, gedeckt: int, gesamt: int) -> None:
    """Die Marke geht nur nach oben. Sie ist eine Sperrklinke, kein Tagebuch."""
    ZUSTAND.mkdir(parents=True, exist_ok=True)
    if anteil <= bestmarke_lesen():
        return
    ABDECKUNG.write_text(json.dumps({
        "anteil": anteil, "gedeckt": gedeckt, "gesamt": gesamt,
        "erreicht_am": date.today().isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8", newline="")


# ---------------------------------------------------------------------- Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "abdeckung").lower()
    rest = argumente[1:]

    if befehl == "tor":
        b = tor(rest[0] if rest else "bau")
        print(b.satz())
        return 0 if b.gruen else 1

    if befehl == "lauf":
        if not rest:
            print("Welches Modul?")
            return 2
        b = nach_dem_lauf(rest[0], rest[1] if len(rest) > 1 else "")
        print(b.satz())
        return 0 if b.gruen else 1

    if befehl == "taeglich":
        b = taeglich()
        print(b.satz())
        return 0 if b.gruen else 1

    if befehl == "gegenproben":
        print("Die Pruefung der Pruefungen ist ausgesetzt, bis die App fertig")
        print("ist - von Daniel am 09.09.2026 angeordnet. Siehe START.md.")
        print("Wer sie trotzdem starten will: --trotzdem dahinter.")
        if "--trotzdem" not in rest:
            return 0
        schlecht = gegenproben_starten()
        anzahl = len(list(BETATESTS.glob("gegenprobe_*.py")))
        if not schlecht:
            print("Alle %d Gegenproben laufen durch." % anzahl)
            return 0
        print("%d von %d Gegenproben laufen NICHT durch:" % (len(schlecht), anzahl))
        for name, grund in schlecht:
            print("  %-34s %s" % (name, grund))
        return 1

    if befehl == "abdeckung":
        a = abdeckung()
        marke = bestmarke_lesen()
        print("%d von %d Pruefungen haben eine Gegenprobe (%.1f %%)"
              % (a["gedeckt"], a["gesamt"], a["anteil"]))
        print("Bestmarke bisher: %.1f %%" % marke)
        if "--setzen" in rest:
            bestmarke_setzen(a["anteil"], a["gedeckt"], a["gesamt"])
            print("Marke steht jetzt bei %.1f %%" % bestmarke_lesen())
        if "--offen" in rest:
            for k in a["offen"]:
                print("  ohne Gegenprobe: " + k)
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
