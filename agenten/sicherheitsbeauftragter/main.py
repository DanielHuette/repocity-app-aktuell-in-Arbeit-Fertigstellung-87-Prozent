"""Sicherheitsbeauftragter - Kommandozeile.

Er macht einen Rundgang und sagt, was er gefunden hat. Er aendert nichts
und gibt nie einen Schluessel aus - ein Sicherheitsbericht, der Schluessel
enthaelt, ist selbst das Leck.

  python main.py rundgang       alles pruefen, dauert Sekunden
  python main.py rundgang --gruendlich   zusaetzlich die 20.000 Dokumente
                                         im Wissensspeicher, dauert Minuten
  python main.py schluessel     nur die Schluessel und Zugaenge
  python main.py verlauf        nur den Git-Verlauf (dauert am laengsten)
  python main.py rechte         nur Tuer und Steckbriefe
  python main.py zugaenge       welcher Zugang fehlt und was das lahmlegt
  python main.py stand          eine Zeile je Bereich

Was er im Blick hat:

  SCHLUESSEL   Er sucht nicht nach Mustern, die wie ein Schluessel aussehen.
               Er nimmt deine Schluessel aus der .env und sucht nach genau
               diesen Zeichenfolgen - im Arbeitsverzeichnis, im Git-Verlauf,
               im Tagebuch, im Vault, in den fertigen Beitraegen.
  ZUGAENGE     Welcher fehlt, welcher laeuft bald ab - und welches Modul
               deshalb stillsteht, ohne es zu melden.
  TUER         Redet ein Agent an gehirn.py vorbei mit der Datenbank? Dann
               umgeht er auch die Steckbriefe.
  AUSGANG      Ist etwas abgeholt worden, das nie freigegeben war?
"""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

import pruefer  # noqa: E402

try:
    import meldung
except ImportError:
    meldung = None

MODUL = "system.sicherheit"


def _ausgeben(bericht: pruefer.Bericht, kopf: str = "") -> int:
    if kopf:
        print(kopf)
        print("=" * len(kopf))
    schwer = bericht.nach_schwere(pruefer.SCHWER)
    mittel = bericht.nach_schwere(pruefer.MITTEL)
    hinweise = bericht.nach_schwere(pruefer.HINWEIS)

    for gruppe, titel in ((schwer, "SOFORT"), (mittel, "BALD"),
                          (hinweise, "ZUR KENNTNIS")):
        if not gruppe:
            continue
        print("\n%s" % titel)
        for b in gruppe:
            print(b.zeile())

    print("\nGeprueft: " + ", ".join(bericht.geprueft))
    if not bericht.befunde:
        print("Nichts gefunden.")
    else:
        print("%d schwer, %d bald, %d zur Kenntnis."
              % (len(schwer), len(mittel), len(hinweise)))

    if (schwer or mittel) and meldung is not None:
        meldung.melde(
            "\n".join(b.zeile() for b in schwer + mittel),
            art="fehler" if schwer else "info",
            zusammenfassung="Sicherheitsrundgang: %d schwer, %d bald"
                            % (len(schwer), len(mittel)))
    return 1 if schwer else 0


def _teilbericht(*pruefungen) -> pruefer.Bericht:
    bericht = pruefer.Bericht()
    for p in pruefungen:
        p(bericht)
    return bericht


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "rundgang").lower()

    if befehl == "rundgang":
        gruendlich = "--gruendlich" in argumente
        return _ausgeben(pruefer.rundgang(gruendlich=gruendlich),
                         "SICHERHEITSRUNDGANG"
                         + (" (gruendlich)" if gruendlich else ""))

    if befehl == "schluessel":
        return _ausgeben(_teilbericht(
            pruefer.ablage_pruefen, pruefer.schluessel_suchen,
            pruefer.betriebsdaten_pruefen, pruefer.klartext_pruefen),
            "SCHLUESSEL")

    if befehl == "verlauf":
        return _ausgeben(_teilbericht(pruefer.verlauf_pruefen), "GIT-VERLAUF")

    if befehl == "rechte":
        return _ausgeben(_teilbericht(
            pruefer.tuer_pruefen, pruefer.steckbriefe_pruefen,
            pruefer.ausgang_pruefen), "RECHTE UND AUSGANG")

    if befehl == "zugaenge":
        return _ausgeben(_teilbericht(
            pruefer.vollzaehligkeit_pruefen, pruefer.ablauf_pruefen),
            "ZUGAENGE")

    if befehl == "stand":
        b = pruefer.rundgang()
        print("%-16s %d" % ("schwer", len(b.nach_schwere(pruefer.SCHWER))))
        print("%-16s %d" % ("bald", len(b.nach_schwere(pruefer.MITTEL))))
        print("%-16s %d" % ("zur Kenntnis", len(b.nach_schwere(pruefer.HINWEIS))))
        print("%-16s %s" % ("Schluessel", len(pruefer.geheimnisse())))
        return 0 if b.sauber else 1

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
