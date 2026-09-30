"""Ausbilder - Kommandozeile.

Der Ausbilder schult keine Agenten. Er liest, was die Auftraege gelehrt
haben, und schlaegt daraus Regeln vor. Bestaetigen tut Daniel.

  python main.py sichten [modul]     Erfahrungen lesen, Lehrsaetze vorschlagen
  python main.py sichten --ohne-modell   dasselbe, aber ohne jede Einbettung
  python main.py vorschlaege         was auf deine Bestaetigung wartet
  python main.py bestaetigen L0001
  python main.py ablehnen L0001 "warum nicht"
  python main.py nachpruefen         welcher Lehrsatz nichts bewirkt hat
  python main.py zurueckziehen L0001 "keine Bewegung"
  python main.py zeugnis [modul] [seit-datum]
  python main.py anweisung <modul>   was ein Agent als Vorwissen bekommt
  python main.py technik [modul]     wo die Maschinerie hakt - Prozessfehler je Klasse
  python main.py stand

Nichts davon kostet Geld. Nur 'sichten --formulieren' fragt ein Modell, ob
es den Rohsatz glatter schreibt - das sind Bruchteile eines Cent je Satz und
ist ausdruecklich abschaltbar. Ohne die Fahne wird der Satz aus den Gruenden
selbst gebaut; er steht dann etwas holprig da, sagt aber dasselbe.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

KERN = Path(__file__).resolve().parent.parent / "kern"
sys.path.insert(0, str(KERN))

import modellwahl  # noqa: E402
import rueckweg  # noqa: E402

try:
    import melden as meldung
except ImportError:
    meldung = None

AGENT = "ausbilder"
#: Unter dieser Kennung meldet er - eine Modul-Kennung aus Modul.kt.
MODUL = "ausbildung"

#: Bewegt sich der Anteil der Neins um weniger als das, gilt ein Lehrsatz
#: als wirkungslos.
MINDESTBEWEGUNG = 0.05

#: So lange bekommt ein Lehrsatz Zeit, bevor nachgeprueft wird.
SCHONFRIST_TAGE = 30


def _module() -> list[str]:
    """Die Modul-Kennungen aus gehirn.json - dieselben wie in Modul.kt."""
    import json
    datei = KERN.parent / "gehirn.json"
    try:
        briefe = json.loads(datei.read_text(encoding="utf-8")).get("steckbriefe", {})
    except (OSError, json.JSONDecodeError):
        return []
    return [k for k in briefe if k != "standard"]


def _melde(art: str, kurz: str, text: str, daten: dict | None = None) -> None:
    if meldung is not None:
        meldung.melde(absender=MODUL, art=art, zusammenfassung=kurz,
                      text=text, daten=daten or {})


# ------------------------------------------------------------------ sichten

def befehl_sichten(module: list[str], formulieren: bool, genau: bool = True) -> int:
    """Sucht Wiederholungen und legt daraus Lehrsatz-Vorschlaege an.

    Eine einzelne Erfahrung wird nie zur Regel. Erst ab der Schwelle - sonst
    bekommt man einen Agenten voller Aberglauben.
    """
    neu = 0
    for modul in module:
        reif = rueckweg.reif_fuer_lehrsatz(modul, genau=genau)
        if not reif:
            continue
        vorhanden = {s.get("kennung"): s for s in rueckweg.lehrsaetze(modul, None)}
        belegt = set()
        for s in vorhanden.values():
            belegt.update(s.get("belege") or [])

        for haufen in reif:
            # Schon einmal behandelt? Dann nicht noch einmal vorschlagen.
            if set(haufen["belege"]) <= belegt:
                print("  %-22s %dx %-28s -> schon behandelt"
                      % (modul, haufen["anzahl"], haufen["kern"]))
                continue
            satz = _satz_bauen(haufen, formulieren)
            datei = rueckweg.lehrsatz_vorschlagen(
                satz, modul, haufen["belege"],
                begruendung="%d Auftraege sind aus demselben Grund zurueckgekommen:\n%s"
                            % (haufen["anzahl"],
                               "\n".join("- " + g for g in haufen["gruende"])))
            neu += 1
            print("  %-22s %dx %-28s -> %s" % (modul, haufen["anzahl"],
                                               haufen["kern"], datei.name))
            _melde("freigabe",
                   "Lehrsatz-Vorschlag fuer %s" % modul,
                   "%s\n\nGrundlage: %d gleichartige Neins."
                   % (satz, haufen["anzahl"]),
                   {"lehrsatz": datei.name.split("_")[0], "modul": modul})
    if neu == 0:
        print("Nichts Neues - keine Wiederholung hat die Schwelle erreicht.")
    else:
        print("\n%d Vorschlag/Vorschlaege angelegt. Bestaetigen mit:"
              "  python main.py bestaetigen <Kennung>" % neu)
    return 0


def _satz_bauen(haufen: dict, formulieren: bool) -> str:
    """Aus den wiederholten Gruenden einen Satz machen.

    Ohne Modell wird der haeufigste Grund woertlich genommen und als
    Anweisung gewendet. Das ist holprig, aber richtig - und kostenlos.
    """
    roh = "Wiederholt bemaengelt: %s. Darauf beim naechsten Mal vor der " \
          "Abnahme selbst achten." % _haeufigster(haufen["gruende"])
    if not formulieren:
        return roh
    glatt = _durch_modell(haufen)
    return glatt or roh


def _haeufigster(gruende: list[str]) -> str:
    """Der kuerzeste der Gruende - er enthaelt meist genau die Sache."""
    return min(gruende, key=len).rstrip(".")


def _durch_modell(haufen: dict) -> str | None:
    """Optional: ein Modell formuliert den Satz. Kostet Bruchteile eines Cent."""
    try:
        sys.path.insert(0, str(KERN))
        import umgebung
        umgebung.laden()
    except Exception:
        pass
    import os
    schluessel = os.environ.get("ANTHROPIC_API_KEY")
    if not schluessel:
        print("    (kein ANTHROPIC_API_KEY - Rohsatz wird verwendet)")
        return None
    try:
        import anthropic
    except ImportError:
        print("    (Paket 'anthropic' fehlt - Rohsatz wird verwendet)")
        return None
    try:
        antwort = anthropic.Anthropic(api_key=schluessel).messages.create(
            model=modellwahl.MODELL, max_tokens=160,
            messages=[{"role": "user", "content":
                       "Diese Rueckmeldungen kamen mehrfach zum selben Punkt:\n"
                       + "\n".join("- " + g for g in haufen["gruende"])
                       + "\n\nSchreibe daraus EINEN Satz als Anweisung an den Agenten. "
                         "Deutsch, konkret, ohne Fachbegriffe, ohne Einleitung. "
                         "Nur den Satz."}])
        _buchen(antwort, modellwahl.MODELL, "Lehrsatz formulieren")
        return antwort.content[0].text.strip()
    except Exception as fehler:
        print("    (Modell nicht erreichbar: %s - Rohsatz wird verwendet)" % fehler)
        return None


# ------------------------------------------------------------------ Vorschlaege

def befehl_vorschlaege() -> int:
    liste = rueckweg.lehrsaetze(None, "vorschlag")
    if not liste:
        print("Kein Vorschlag offen.")
        return 0
    for s in liste:
        print("%s  gilt fuer %s   (%d Belege)"
              % (s["kennung"], s.get("gilt_fuer"), len(s.get("belege") or [])))
        print("    %s" % s.get("satz", ""))
    print("\nBestaetigen:  python main.py bestaetigen <Kennung>")
    print("Ablehnen:     python main.py ablehnen <Kennung> \"warum nicht\"")
    return 0


def befehl_bestaetigen(kennung: str) -> int:
    datei = rueckweg.lehrsatz_entscheiden(kennung, True)
    if datei is None:
        print("nicht gefunden: " + kennung)
        return 1
    print("%s ist aktiv. Er geht ab sofort in die Anweisung des Agenten." % kennung)
    return 0


def befehl_ablehnen(kennung: str, grund: str) -> int:
    if not grund.strip():
        print("Ein Nein ohne Grund lehrt nichts - bitte einen Satz mitgeben.")
        return 2
    datei = rueckweg.lehrsatz_entscheiden(kennung, False, grund=grund)
    if datei is None:
        print("nicht gefunden: " + kennung)
        return 1
    print("%s abgelehnt und auf der Halde vermerkt." % kennung)
    return 0


# ------------------------------------------------------------------ nachpruefen

def befehl_nachpruefen() -> int:
    """Welcher Lehrsatz hat nichts bewirkt.

    Zurueckgezogen wird nicht von selbst - das legt der Ausbilder dir vor,
    so entschieden.
    """
    aktive = rueckweg.lehrsaetze(None, "aktiv")
    if not aktive:
        print("Kein aktiver Lehrsatz.")
        return 0
    frisch = (date.today() - timedelta(days=SCHONFRIST_TAGE)).isoformat()
    ohne_wirkung = []
    for s in aktive:
        ab = s.get("bestaetigt_am") or ""
        if ab > frisch:
            print("%s  noch in der Schonfrist (seit %s)" % (s["kennung"], ab))
            continue
        w = rueckweg.wirkung_pruefen(s["kennung"])
        vorher, nachher = w.get("anteil_neins_vorher"), w.get("anteil_neins_nachher")
        if nachher is None or w.get("stuecke_nachher", 0) < 3:
            print("%s  zu wenig Stuecke seither (%d) - noch nicht messbar"
                  % (s["kennung"], w.get("stuecke_nachher", 0)))
            continue
        pfeil = "unveraendert"
        if vorher is not None:
            pfeil = "%.0f %% -> %.0f %%" % (vorher * 100, nachher * 100)
        if w.get("anweisung_geaendert"):
            pfeil += " (Anweisung seither geaendert: %d Fassungen - Bewegung nicht allein dem Lehrsatz zuzuschreiben)" % len(
                w.get("fassungen_nachher") or [])
        if not w.get("bewegt"):
            ohne_wirkung.append((s, pfeil))
            print("%s  OHNE WIRKUNG   Anteil deiner Neins %s" % (s["kennung"], pfeil))
        else:
            print("%s  wirkt          Anteil deiner Neins %s" % (s["kennung"], pfeil))

    for s, pfeil in ohne_wirkung:
        _melde("freigabe",
               "Lehrsatz %s bewirkt nichts" % s["kennung"],
               "Seit der Bestaetigung hat sich der Anteil deiner Neins nicht "
               "bewegt (%s). Zuruecknehmen?\n\n%s" % (pfeil, s.get("satz", "")),
               {"lehrsatz": s["kennung"]})
    if ohne_wirkung:
        print("\nZurueckziehen:  python main.py zurueckziehen <Kennung> \"Grund\"")
    return 0


def befehl_zurueckziehen(kennung: str, grund: str) -> int:
    datei = rueckweg.lehrsatz_zurueckziehen(kennung, grund or "keine Wirkung messbar")
    if datei is None:
        print("nicht gefunden: " + kennung)
        return 1
    print("%s zurueckgezogen. Er bleibt lesbar und liegt auf der Halde," % kennung)
    print("damit ihn niemand in einem halben Jahr noch einmal vorschlaegt.")
    return 0


# ------------------------------------------------------------------ Zeugnis

def befehl_technik(modul: str | None) -> int:
    """Prozessfehler, getrennt von den Urteilen: welche Strasse haengt woran.

    Ab drei gleichen Faellen geht eine Meldung an Daniel - ein einzelner
    Ausfall ist Wetter, drei sind ein Muster.
    """
    haufen = rueckweg.technik_haufen(modul)
    if not haufen:
        print("Keine Prozessfehler vermerkt.")
        return 0
    for h in haufen:
        print("%3d x  %-22s %s" % (h["anzahl"], h["modul"], h["klasse"]))
    for h in haufen:
        if h["anzahl"] >= rueckweg.SCHWELLE:
            _melde("info", "%s: %d x %s" % (h["modul"], h["anzahl"], h["klasse"]),
                   "Die Strasse %s ist %d-mal an '%s' gescheitert. Das ist kein Urteil "
                   "ueber ein Stueck, sondern ein Fehler der Maschinerie - "
                   "nachsehen, bevor es der naechste Auftrag ausbadet."
                   % (h["modul"], h["anzahl"], h["klasse"]), h)
    return 0


def befehl_zeugnis(module: list[str], seit: str | None) -> int:
    kopf = "%-24s %6s %8s %8s %9s %8s" % (
        "Strasse", "Stuecke", "Durchl.", "Neins", "EUR/St.", "Min/St.")
    print(kopf)
    print("-" * len(kopf))
    leer = True
    for modul in module:
        z = rueckweg.zeugnis(modul, seit)
        if not z["stuecke"]:
            continue
        leer = False
        print("%-24s %6d %8.2f %7.0f%% %9.2f %8.1f"
              % (modul, z["stuecke"], z["durchlaeufe_schnitt"],
                 z["anteil_neins"] * 100, z["kosten_je_stueck"],
                 z["minuten_je_stueck"]))
    if leer:
        print("(noch keine Erfahrungen abgelegt)")
    else:
        print("\nDie wichtigste Spalte ist 'Neins'. Sie soll ueber Monate fallen,")
        print("waehrend die Zahl der Stuecke steigt.")
    return 0


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    if not argumente:
        print(__doc__)
        return 2
    befehl = argumente[0].lower()
    rest = argumente[1:]

    if befehl == "sichten":
        formulieren = "--formulieren" in rest
        genau = "--ohne-modell" not in rest
        genannt = [a for a in rest if not a.startswith("--")]
        return befehl_sichten(genannt or _module(), formulieren, genau)
    if befehl == "vorschlaege":
        return befehl_vorschlaege()
    if befehl == "bestaetigen" and rest:
        return befehl_bestaetigen(rest[0])
    if befehl == "ablehnen" and len(rest) > 1:
        return befehl_ablehnen(rest[0], " ".join(rest[1:]))
    if befehl == "nachpruefen":
        return befehl_nachpruefen()
    if befehl == "zurueckziehen" and rest:
        return befehl_zurueckziehen(rest[0], " ".join(rest[1:]))
    if befehl == "zeugnis":
        genannt = [a for a in rest if not a.startswith("2")]
        datum = next((a for a in rest if a.startswith("2")), None)
        return befehl_zeugnis(genannt or _module(), datum)
    if befehl == "technik":
        return befehl_technik(rest[0] if rest else None)
    if befehl == "anweisung" and rest:
        print(rueckweg.vorwissen(rest[0]) or "(noch nichts gelernt)")
        return 0
    if befehl == "stand":
        for name, zahl in rueckweg.stand().items():
            print("%-26s %d" % (name, zahl))
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))


def _buchen(antwort, modell, wofuer):
    """Modellaufruf verbuchen. Nie eine Ausnahme nach aussen - eine
    verlorene Buchung ist besser als ein abgebrochener Lauf."""
    try:
        import sys as _sys
        from pathlib import Path as _Path

        kern = str(_Path(__file__).resolve().parent.parent / "kern")
        if kern not in _sys.path:
            _sys.path.append(kern)
        import modellkosten

        modellkosten.buchen(antwort, "ausbildung", modell, wofuer)
    except Exception:
        pass
