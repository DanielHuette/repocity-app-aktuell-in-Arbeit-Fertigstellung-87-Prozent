"""Webseitenbetreuer - er sieht nach, er baut nicht um.

Er geht die gebaute Seite ab: zeigt jeder interne Verweis auf etwas, das
es gibt, ist eine Seite unverhaeltnismaessig schwer geworden, antwortet
die veroeffentlichte Fassung. Findet er etwas, meldet er es.

Was zu aendern ist, geht als Bauauftrag an den Architekten und braucht
deine Freigabe - wie jede andere Aenderung auch. Ein Agent, der die
oeffentliche Seite selbst umschreibt, waehrend niemand hinsieht, waere
genau das, was man nicht will.

Aufruf:
    python main.py rundgang        Wege und Gewichte im gebauten Stand
    python main.py lebend          antwortet die veroeffentlichte Seite
    python main.py stand
"""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"

sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

import rundgang  # noqa: E402

try:
    import melden
except ImportError:
    melden = None

AGENT = "webseitenbetreuer"
MODUL = rundgang.MODUL


def gehen(auch_lebend: bool = False) -> rundgang.Befund:
    befund = rundgang.wege_pruefen()
    if auch_lebend:
        befund.lebend = rundgang.lebend_pruefen()
    return befund


def _melde(befund: rundgang.Befund) -> None:
    if melden is None:
        return
    art = "info" if befund.sauber else "fehler"
    kurz = ("Webseite in Ordnung" if befund.sauber
            else "Webseite: %d tote Verweise, %d schwere Seiten"
                 % (len(befund.tote_verweise), len(befund.schwere_seiten)))
    try:
        melden.melde(MODUL, befund.als_text(), art=art, zusammenfassung=kurz)
    except Exception:
        pass


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()

    if befehl in ("rundgang", "lebend"):
        befund = gehen(auch_lebend=(befehl == "lebend"))
        print(befund.als_text())
        _melde(befund)
        return 0 if befund.sauber else 1

    if befehl == "stand":
        wurzel = rundgang.dist()
        print("Webseitenbetreuer")
        print("  Gebauter Stand  %s" % (wurzel if wurzel.exists()
                                        else "-- fehlt, 'npm run build' laeuft nicht --"))
        print("  Grenze je Seite %d KB" % rundgang.SEITE_HOECHSTENS_KB)
        print("  Wichtige Wege   %d" % len(rundgang.WICHTIGE_WEGE))
        print()
        print("  Er aendert nichts. Aenderungen laufen ueber den Architekten")
        print("  und deine Freigabe.")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
