# -*- coding: utf-8 -*-
"""Der Postbote - er traegt aus, was der Hub verschicken lassen will.

Der Hub liegt bei Cloudflare und hat kein Postfach. Wenn sich jemand ein
Konto anlegt oder sein Passwort vergessen hat, legt der Hub den Brief in
den Ausgang. Hier wird er abgeholt und ueber dasselbe Postfach verschickt,
das der E-Mail-Manager ohnehin bedient.

    Hub (Ausgang)  --> Postbote --> SMTP --> der Nutzer

Warum nicht direkt aus dem Hub heraus: ein Maildienst in der Wolke waere
ein weiterer Zugang, ein weiterer Preis und eine weitere Stelle, die
ausfallen kann. Das Postfach steht schon.

Abgehakt wird erst, wenn die Mail wirklich draussen ist. Faellt der
Versand aus, bleibt der Brief liegen und geht beim naechsten Lauf hinaus -
kein Konto bleibt unbestaetigt, weil einmal das Netz weg war.

Aufruf:
    python universe/email_manager/postbote.py           austragen
    python universe/email_manager/postbote.py schauen   nur nachsehen
"""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
if str(HIER) not in sys.path:
    sys.path.insert(0, str(HIER))

# Zuerst die .env - sie muss geladen sein, BEVOR einstellungen.py sie
# liest. Am 09.09. hat genau das gefehlt: der Postbote meldete "nichts im
# Ausgang", waehrend am Hub ein Brief lag. Die Hub-Adresse war leer, weil
# die .env nie gelesen wurde.
import umgebung  # noqa: E402,F401

# Nur der eigene Ordner steht auf dem Pfad. Den eines anderen Agenten
# dazuzulegen waere genau der Fehler, den die Pruefung
# "gehirn.gleiche-namen" abfaengt: dann laedt hier ein "hub" aus einem
# fremden Ordner, und niemand sieht es dem Import an.
HIER_ORDNER = HIER


# ─────────────────────────────────────────────────────────────────────────
#  EIGENE DATEIEN EINDEUTIG LADEN
#
#  Es gibt im Universe zwei Dateien namens `hub.py`: eine im Kern, eine
#  hier. Sobald ein Kern-Baustein geladen wird, legt er den Kern-Ordner
#  ganz vorne in den Suchpfad - und ab da fuehrt ein schlichtes
#  `import hub` in die falsche Datei. Am 09.09. nachgemessen:
#  `main.hub.__file__` zeigte auf `universe/kern/hub.py`, und damit fehlte
#  `hub.melde` - der Manager waere bei der ersten Meldung abgebrochen.
#
#  Darum wird die eigene Datei hier ueber ihren Pfad geladen, nicht ueber
#  ihren Namen. Das ist eindeutig, egal wer sonst am Suchpfad dreht.
# ─────────────────────────────────────────────────────────────────────────

def _eigenes(name: str):
    import importlib.util
    ziel = HIER_ORDNER / (name + ".py")
    kennung = "email_manager_" + name
    if kennung in sys.modules:
        return sys.modules[kennung]
    spec = importlib.util.spec_from_file_location(kennung, ziel)
    modul = importlib.util.module_from_spec(spec)
    sys.modules[kennung] = modul
    spec.loader.exec_module(modul)
    return modul


hub = _eigenes("hub")
import einstellungen as e  # noqa: E402
from postfach import Postfach  # noqa: E402


def _erstes_konto():
    """Das Postfach, ueber das ausgetragen wird - das erste eingerichtete.

    Mehr als eines braucht der Postbote nicht: die Absenderadresse des
    Universe ist eine, und ein Nutzer soll nicht mal von der einen und mal
    von der anderen Adresse Post bekommen.
    """
    import main as em  # erst hier, sonst laeuft beim Import der Agent los
    konten = em._konten_bauen(hub.zugangsdaten_holen())
    return konten[0] if konten else None


def austragen(nur_schauen: bool = False, still: bool = True) -> int:
    """Alles austragen, was liegt. Gibt zurueck, wie viele raus sind.

    ``still`` gilt fuer den Lauf im Takt: eine Stoerung haelt nichts an,
    der naechste Lauf holt es nach. Von Hand aufgerufen ist es umgekehrt -
    dann muss dastehen, was hakt und warum.
    """
    if not e.HUB_URL:
        print("Kein Hub eingerichtet (UNIVERSE_HUB_URL ist leer) - "
              "es gibt nichts abzuholen.")
        return 0
    try:
        briefe = hub.postausgang(still=still)
    except hub.HubFehler as fehler:
        print("Der Ausgang ist nicht erreichbar:", fehler)
        return 0
    if not briefe:
        print("Nichts im Ausgang.")
        return 0

    print("%d Brief(e) im Ausgang." % len(briefe))
    for b in briefe:
        print("  an %-30s %s" % (b.get("an", "?"), b.get("betreff", "")))
    if nur_schauen:
        return 0

    if e.TROCKEN:
        print("Trockenlauf - es geht nichts hinaus, und nichts wird abgehakt.")
        return 0

    konto = _erstes_konto()
    if konto is None:
        print("Kein Postfach eingerichtet - die Briefe bleiben liegen.")
        return 0

    raus = 0
    with Postfach(konto) as fach:
        for b in briefe:
            an = str(b.get("an", "")).strip()
            if not an:
                continue
            try:
                fach.senden(an, b.get("betreff", "RepoCity"), b.get("text", ""))
            except Exception as fehler:  # noqa: BLE001 - jeder Grund ist derselbe
                print("  liegen geblieben (%s): %s" % (an, fehler))
                continue
            # Erst jetzt - abgehakt wird, was wirklich draussen ist.
            if hub.post_abhaken(b.get("id", "")):
                raus += 1
            else:
                print("  raus, aber nicht abgehakt (%s) - er kommt noch einmal" % an)

    print("%d Brief(e) verschickt." % raus)
    return raus


if __name__ == "__main__":
    # Von Hand aufgerufen wird nichts verschwiegen; im Takt schon.
    sys.exit(0 if austragen("schauen" in sys.argv[1:], still=False) >= 0 else 1)
