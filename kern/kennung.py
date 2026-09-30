"""Aus einer Hub-Kennung einen Namen machen, den das Dateisystem hergibt.

Die Kennungen des Hubs heissen ``auftrag:m3k9x2-a7b1c4``. Der Doppelpunkt
ist auf Windows kein Zeichen wie jedes andere: NTFS deutet ihn als Trenner
zu einem alternativen Datenstrom.

  · Als **Datei**name wird aus ``auftrag:p.json`` eine Datei ``auftrag`` mit
    einem versteckten Anhang ``p.json``. Der Agent findet nichts, und
    niemand sieht warum.
  · Als **Ordner**name geht es gar nicht: ``os.mkdir`` bricht mit
    "Der Verzeichnisname ist ungueltig" ab (WinError 267).

Auf Linux waere beides nie aufgefallen.

Der erste Fall war seit dem 06.09. im Sekretaer entschaerft, der zweite
nicht - die Werkstaetten bauten ihren Arbeitsordner weiter aus der rohen
Kennung. Am 09.09. beim Durchspielen aufgeflogen: jeder echte Auftrag vom
Hub waere in der Video-Werkstatt sofort abgebrochen. Deshalb steht die
Regel jetzt hier und nur hier.

    sauber("auftrag:m3k9-a7b1")   ->  "auftrag-m3k9-a7b1"
"""
from __future__ import annotations

#: Was ein Name behalten darf. Alles andere wird zum Bindestrich.
ERLAUBT = "-_."


def sauber(kennung: str, ersatz: str = "auftrag") -> str:
    """Ein Name, der als Datei UND als Ordner funktioniert.

    ``ersatz`` ist der Name fuer den Fall, dass nichts uebrig bleibt -
    ein leerer Name waere schlimmer als ein unscharfer.
    """
    gefiltert = "".join(z if (z.isalnum() or z in ERLAUBT) else "-"
                        for z in str(kennung))
    return gefiltert.strip("-.") or ersatz
