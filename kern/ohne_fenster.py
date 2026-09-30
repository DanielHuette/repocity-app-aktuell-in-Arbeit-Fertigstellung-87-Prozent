# -*- coding: utf-8 -*-
"""Kein Konsolenfenster fuer Hilfsprogramme - an genau einer Stelle.

Unter Windows reisst jeder Start eines Konsolenprogramms ein Fenster auf:
ffmpeg, node, npm, wrangler, edge-tts, jeder Agentenlauf. Solange alle
paar Minuten eines aufblitzte, fiel es nicht auf. Seit die Leitung im
Sekundentakt arbeitet und eine Videostrasse dutzende ffmpeg-Aufrufe
macht, flackert der Bildschirm dauernd - Daniel am 10.09.2026: "das nervt
so unendlich".

Es an vierzig Aufrufstellen einzeln einzutragen waere vierzig Stellen,
die man vergessen kann. Darum hier: wer dieses Modul laedt, startet ab
dann kein sichtbares Fenster mehr - subprocess.run, .call und
.check_output gehen alle durch Popen.

Wer selbst ein Fenster will, gibt creationflags ausdruecklich an; dann
wird nichts angefasst.

    import ohne_fenster   # mehr ist nicht noetig

CREATE_NO_WINDOW ist 0x08000000. NICHT zusammen mit DETACHED_PROCESS
benutzen - die beiden schliessen einander aus, und Windows macht dann
doch ein Fenster auf. Genau daran ist am 10.09. der erste Anlauf
gescheitert.
"""
from __future__ import annotations

import subprocess
import sys

#: Windows-Wert von CREATE_NO_WINDOW. getattr, weil es die Konstante auf
#: anderen Systemen gar nicht gibt.
FLAG = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def anwenden() -> bool:
    """Gibt zurueck, ob ab jetzt kein Fenster mehr aufgeht."""
    if sys.platform != "win32":
        return False
    if getattr(subprocess.Popen, "_ohne_fenster", False):
        return True  # schon geschehen, nicht zweimal einpacken

    alt = subprocess.Popen.__init__

    def neu(self, *args, **kwargs):
        if not kwargs.get("creationflags"):
            kwargs["creationflags"] = FLAG
        return alt(self, *args, **kwargs)

    subprocess.Popen.__init__ = neu
    subprocess.Popen._ohne_fenster = True
    return True


#: Beim Laden gleich wirksam - das ist der ganze Zweck.
anwenden()
