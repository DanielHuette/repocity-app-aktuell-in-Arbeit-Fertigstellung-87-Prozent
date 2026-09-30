# -*- coding: utf-8 -*-
"""Die offene Leitung - das Universe laeuft, statt geweckt zu werden.

    python universe\\kern\\leitung.py            laeuft, bis man sie anhaelt
    python universe\\kern\\leitung.py stand      laeuft sie? seit wann?
    python universe\\kern\\leitung.py einmal     ein einziger Takt, dann Schluss

WAS SICH DAMIT AENDERT

Bis zum 10.09.2026 rief die Windows-Aufgabenplanung alle fuenf Minuten
`zeitplan.py lauf` auf. Das hiess: ein Auftrag vom Handy lag im
schlechtesten Fall fuenf Minuten herum, bevor ihn ueberhaupt jemand sah -
und Windows entschied, ob und wann etwas passiert.

Jetzt laeuft ein einziges Programm dauerhaft und taktet selbst. Der Takt
steht in `zeitplan.json` unter `_takt_sekunden` und liegt bei Sekunden,
nicht Minuten. Auf einem gemieteten Server wird daraus ein Dienst; hier
ist es ein Fenster, das offen bleibt.

WAS SICH NICHT AENDERT

Was faellig ist, entscheidet weiter `zeitplan.py` aus `zeitplan.json`.
Diese Datei ist nur die Uhr, nicht der Plan - sonst gaebe es zwei
Stellen, die wissen, was wann laeuft, und die liefen auseinander.

Der Rechner fragt weiter beim Hub nach; er wird nicht angerufen. Das
bleibt Absicht: so braucht dieser Rechner keine offene Tuer ins Internet.
"Offene Leitung" heisst, dass hier dauerhaft jemand wach ist - nicht,
dass von aussen jemand hereinkommt.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
sys.path.insert(0, str(HIER))

# Muss als erstes stehen: einstellungen.py liest ihre Werte beim Import,
# und steht die .env dann noch nicht in der Umgebung, sind alle Werte leer
# und nichts sagt es. Fallstrick vom 09.09.
import umgebung  # noqa: E402,F401

import zeitplan  # noqa: E402
import hub as _hub  # noqa: E402

#: Alle so viele Sekunden geht der Puls an den Hub. Zehn Minuten: 144
#: Schreibvorgaenge am Tag, und wer nach einer Stunde nichts hoert, weiss
#: Bescheid.
PULS_SEK = 600


def _kosten_fuer_den_puls() -> dict | None:
    """Die Monatszusammenfassung aus dem Verbrauchsbuch - klein gehalten:
    Kategorien, Toepfe, Kostenstellen, Betriebsposten. Faellt sie aus, geht
    der Puls ohne sie; ein Puls ohne Zahlen ist besser als keiner."""
    try:
        import verbrauch
        z = verbrauch.zusammenfassung()
        return {k: z[k] for k in ("seit", "laufend_eur", "betrieb_eur", "gesamt_eur",
                                  "je_kategorie", "je_kostenstelle", "je_topf",
                                  "kontingent_zuege", "betriebsposten", "ohne_preis")}
    except Exception:
        return None

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

ZUSTAND = UNIVERSE / "zustand"
HERZ = ZUSTAND / "leitung.json"
PROTOKOLL = ZUSTAND / "leitung.log"

#: Fallen zwei Takte zusammen, weil einer laenger dauerte, wird der
#: verpasste nicht nachgeholt - zeitplan.faellig() sieht ohnehin nach.
TAKT_VOREINSTELLUNG = 5.0

#: Groesser als das wird das Protokoll nicht. Es ist ein Laufband, kein
#: Archiv - was wirklich passiert ist, steht im Tagebuch.
PROTOKOLL_GRENZE = 1_000_000


def _takt() -> float:
    """Wie oft nachgesehen wird. Steht in zeitplan.json, nicht hier."""
    try:
        daten = json.loads((UNIVERSE / "zeitplan.json").read_text(encoding="utf-8"))
        wert = float(daten.get("_takt_sekunden") or 0)
        return wert if wert > 0 else TAKT_VOREINSTELLUNG
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return TAKT_VOREINSTELLUNG


def _notieren(text: str) -> None:
    try:
        ZUSTAND.mkdir(parents=True, exist_ok=True)
        if PROTOKOLL.exists() and PROTOKOLL.stat().st_size > PROTOKOLL_GRENZE:
            # Die zweite Haelfte behalten - das Neueste ist das Wichtige.
            roh = PROTOKOLL.read_bytes()
            PROTOKOLL.write_bytes(roh[len(roh) // 2:])
        with PROTOKOLL.open("a", encoding="utf-8", newline="") as datei:
            datei.write("%s  %s\n" % (datetime.now().isoformat(timespec="seconds"), text))
    except OSError:
        pass


def _herzschlag(seit: str, takte: int, letzter: str, gelaufen: int) -> None:
    """Woran man von aussen sieht, dass sie noch lebt."""
    try:
        ZUSTAND.mkdir(parents=True, exist_ok=True)
        HERZ.write_text(json.dumps({
            "laeuft": True,
            "pid": os.getpid(),
            "seit": seit,
            "letzter_takt": letzter,
            "takte": takte,
            "gestartet_gesamt": gelaufen,
            "takt_sekunden": _takt(),
        }, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    except OSError:
        pass


def _herz_aus(grund: str) -> None:
    try:
        daten = json.loads(HERZ.read_text(encoding="utf-8")) if HERZ.exists() else {}
    except (OSError, json.JSONDecodeError):
        daten = {}
    daten["laeuft"] = False
    daten["beendet"] = datetime.now().isoformat(timespec="seconds")
    daten["grund"] = grund
    try:
        HERZ.write_text(json.dumps(daten, ensure_ascii=False, indent=2),
                        encoding="utf-8", newline="")
    except OSError:
        pass


def _laeuft_schon() -> int:
    """Die Kennung einer schon laufenden Leitung, sonst 0.

    Zwei Leitungen waeren schlimmer als keine: beide holen denselben
    Auftrag ab und schicken ihn zweimal durch die Werkstatt.
    """
    try:
        daten = json.loads(HERZ.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    if not daten.get("laeuft"):
        return 0
    pid = int(daten.get("pid") or 0)
    if not pid or pid == os.getpid():
        return 0
    # Lebt der Prozess wirklich noch? Ein abgewuergter hinterlaesst
    # sonst eine Datei, die die naechste Leitung nicht starten laesst.
    try:
        if os.name == "nt":
            import subprocess
            aus = subprocess.run(
                ["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=10)
            return pid if str(pid) in (aus.stdout or "") else 0
        os.kill(pid, 0)
        return pid
    except Exception:
        return 0


def takt_einmal() -> int:
    """Ein Durchgang. Gibt zurueck, wie viele Eintraege gestartet wurden."""
    ergebnisse = zeitplan.lauf(laut=False)
    for e in ergebnisse:
        if not e["gelaufen"]:
            _notieren("! %s (%s): %s" % (e["eintrag"], e["agent"], e["grund"]))
    return len(ergebnisse)


def dauerlauf() -> int:
    fremd = _laeuft_schon()
    if fremd:
        print("Es laeuft schon eine Leitung (Kennung %d). Zwei waeren "
              "schlimmer als keine - diese hier hoert wieder auf." % fremd)
        return 1

    seit = datetime.now().isoformat(timespec="seconds")
    takte = 0
    gestartet = 0
    grund = "von Hand angehalten"
    _notieren("Leitung offen, Takt %.1f s" % _takt())
    print("Leitung offen. Takt %.1f Sekunden. Anhalten mit Strg+C." % _takt())

    letzter_puls = 0.0
    try:
        while True:
            beginn = time.time()
            takte += 1
            if beginn - letzter_puls >= PULS_SEK:
                letzter_puls = beginn
                try:
                    _hub.puls(seit, takte, _takt(), _kosten_fuer_den_puls())
                except Exception as fehler:
                    _notieren("! Puls nicht angekommen: %r" % (fehler,))
            try:
                gestartet += takt_einmal()
            except Exception as fehler:
                # Ein Fehler in einem Takt darf die Leitung nicht schliessen.
                # Sonst steht nach der ersten Stolperstelle alles - und
                # niemand merkt es, weil kein Fenster offen ist.
                _notieren("! Takt gestolpert: %r" % (fehler,))
            _herzschlag(seit, takte, datetime.now().isoformat(timespec="seconds"),
                        gestartet)
            rest = _takt() - (time.time() - beginn)
            if rest > 0:
                time.sleep(rest)
    except KeyboardInterrupt:
        pass
    except Exception as fehler:
        grund = "abgebrochen: %r" % (fehler,)
        _notieren("!! " + grund)
        _herz_aus(grund)
        raise
    _herz_aus(grund)
    _notieren("Leitung geschlossen (%d Takte)" % takte)
    print("\nLeitung geschlossen. %d Takte, %d Starts." % (takte, gestartet))
    return 0


def _stand() -> int:
    if not HERZ.exists():
        print("Die Leitung lief hier noch nie.")
        return 1
    try:
        daten = json.loads(HERZ.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print("Die Standdatei ist unlesbar.")
        return 1

    lebt = _laeuft_schon()
    if daten.get("laeuft") and lebt:
        letzter = daten.get("letzter_takt", "")
        alt = ""
        try:
            alt = " (vor %.0f s)" % (datetime.now()
                                     - datetime.fromisoformat(letzter)).total_seconds()
        except (ValueError, TypeError):
            pass
        print("Die Leitung ist offen.")
        print("  Kennung      %s" % daten.get("pid"))
        print("  seit         %s" % daten.get("seit"))
        print("  letzter Takt %s%s" % (letzter, alt))
        print("  Takte        %s" % daten.get("takte"))
        print("  Takt alle    %s s" % daten.get("takt_sekunden"))
        return 0

    if daten.get("laeuft"):
        print("Die Standdatei sagt 'offen', aber der Prozess %s lebt nicht mehr."
              % daten.get("pid"))
        print("Wahrscheinlich abgewuergt. Einfach neu starten.")
        return 1

    print("Die Leitung ist zu.")
    print("  zuletzt offen bis %s (%s)"
          % (daten.get("beendet", "?"), daten.get("grund", "?")))
    return 1


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "").lower()
    if befehl in ("", "offen", "lauf"):
        return dauerlauf()
    if befehl == "stand":
        return _stand()
    if befehl == "einmal":
        n = takt_einmal()
        print("Ein Takt: %d Eintrag/Eintraege gestartet." % n)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
