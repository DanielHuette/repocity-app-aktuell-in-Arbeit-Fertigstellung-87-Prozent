# -*- coding: utf-8 -*-
"""Der Koerper - er wartet am Postfach und wird geweckt.

Das Sekretaer-Muster aus Manifest Punkt 3, hier zum ersten Mal gebaut:

    Der Koerper laeuft dauerhaft, haelt die Leitung offen und wartet.
    Er denkt nicht. Warten kostet nichts.
    Der Verstand wird nur gerufen, wenn tatsaechlich etwas ankommt.

Statt alle fuenf Minuten nachzufragen, haelt dieser Laeufer eine offene
Verbindung zum Postfach und laesst sich vom Server melden, sobald eine Mail
eintrifft (IMAP IDLE, RFC 2177). Aus bis zu 300 verlorenen Sekunden wird
weniger als eine.

WAS NOCH FEHLT: das Postfachpasswort. Es steht in ABNAHME.md; ohne
USER_EMAIL_PASSWORT laeuft hier nichts, und das ist Absicht - dieser
Laeufer bittet nicht darum, er sagt es und haelt an.

    python dauerlaeufer.py pruefen   kann er starten?
    python dauerlaeufer.py laufen    warten und wecken
"""
from __future__ import annotations

import imaplib
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent

#: Wie lange eine offene Verbindung hoechstens steht, bevor sie erneuert wird.
#: 29 Minuten - RFC 2177 nennt 29 als Obergrenze, viele Server trennen frueher.
IDLE_MINUTEN = 29

#: Wie lange nach einem Abbruch gewartet wird, bevor neu verbunden wird.
#: Verdoppelt sich bis zu dieser Grenze, damit ein dauerhaft kaputter Zugang
#: nicht in einer Schleife gegen den Server laeuft.
WARTEN_START, WARTEN_MAX = 5, 300


def zugang() -> dict:
    """Die Postfachdaten - aus der Umgebung, nie aus dem Code.

    Fehlt etwas, wird das gesagt und nichts versucht. Ein Laeufer, der ohne
    Zugang startet und still nichts tut, ist schlimmer als einer, der gar
    nicht startet.
    """
    sys.path.insert(0, str(UNIVERSE))
    try:
        from kern import umgebung  # noqa: PLC0415
        umgebung.laden()
    except Exception:
        pass
    return {
        "server": os.environ.get("UNIVERSE_IMAP_SERVER", "imap.gmx.net"),
        "port": int(os.environ.get("UNIVERSE_IMAP_PORT", "993")),
        "postfach": os.environ.get("USER_EMAIL_POSTFACH", ""),
        "passwort": os.environ.get("USER_EMAIL_PASSWORT", ""),
        "ordner": os.environ.get("UNIVERSE_IMAP_ORDNER", "INBOX"),
    }


def kann_starten() -> tuple[bool, str]:
    z = zugang()
    fehlt = [n for n in ("postfach", "passwort") if not z[n]]
    if fehlt:
        return False, ("Es fehlt: %s. Beides gehört in die .env - siehe "
                       "ABNAHME.md. Solange wartet dieser Läufer nicht, "
                       "sondern startet gar nicht erst."
                       % ", ".join("USER_EMAIL_" + n.upper() for n in fehlt))
    if len(z["passwort"]) < 4:
        return False, ("USER_EMAIL_PASSWORT ist ein Platzhalter, kein "
                       "Passwort. Siehe ABNAHME.md.")
    return True, "Zugang vollständig: %s an %s" % (z["postfach"], z["server"])


def verbinden(z: dict) -> imaplib.IMAP4_SSL:
    verbindung = imaplib.IMAP4_SSL(z["server"], z["port"])
    verbindung.login(z["postfach"], z["passwort"])
    verbindung.select(z["ordner"])
    return verbindung


def kann_idle(verbindung: imaplib.IMAP4_SSL) -> bool:
    """Beherrscht dieser Server das Warten - oder muss doch gefragt werden?"""
    try:
        return b"IDLE" in verbindung.capabilities or "IDLE" in verbindung.capabilities
    except Exception:
        return False


def _warten_auf_post(verbindung: imaplib.IMAP4_SSL, minuten: int) -> bool:
    """Offene Leitung halten, bis der Server etwas meldet.

    imaplib kennt IDLE nicht von sich aus - der Befehl wird von Hand
    geschickt und die Antwort gelesen. Das ist wenig Code und braucht keine
    fremde Bibliothek.
    """
    kennung = verbindung._new_tag()
    verbindung.send(b"%s IDLE\r\n" % kennung)
    verbindung.readline()  # die Zeile mit dem "+"
    verbindung.sock.settimeout(minuten * 60)
    etwas_da = False
    try:
        while True:
            zeile = verbindung.readline()
            if not zeile:
                break
            if b"EXISTS" in zeile or b"RECENT" in zeile:
                etwas_da = True
                break
    except socket.timeout:
        pass
    finally:
        try:
            verbindung.send(b"DONE\r\n")
            verbindung.readline()
        except Exception:
            pass
        try:
            verbindung.sock.settimeout(None)
        except Exception:
            pass
    return etwas_da


def neue_nachrichten(verbindung: imaplib.IMAP4_SSL) -> list[bytes]:
    zustand, antwort = verbindung.search(None, "UNSEEN")
    if zustand != "OK":
        return []
    return antwort[0].split()


def laufen(beim_eingang=None, minuten: int = IDLE_MINUTEN) -> int:
    """Warten, wecken, weiterwarten. Laeuft, bis jemand ihn anhaelt.

    [beim_eingang] wird mit der Liste der neuen Nachrichtennummern gerufen -
    das ist der Verstand. Er wird nur gerufen, wenn wirklich etwas da ist.
    """
    darf, grund = kann_starten()
    if not darf:
        print(grund)
        return 1

    z = zugang()
    warten = WARTEN_START
    while True:
        try:
            verbindung = verbinden(z)
            if not kann_idle(verbindung):
                print("Dieser Server kann kein IDLE. Ohne offene Leitung ist der "
                      "Alarm nicht schneller als der Zeitplan - das gehört "
                      "gemeldet, nicht stillschweigend umgangen.")
                verbindung.logout()
                return 2

            print("%s wartet am Postfach %s."
                  % (datetime.now().strftime("%H:%M:%S"), z["postfach"]))
            warten = WARTEN_START
            while True:
                if _warten_auf_post(verbindung, minuten):
                    nummern = neue_nachrichten(verbindung)
                    if nummern and beim_eingang:
                        beim_eingang(verbindung, nummern)
                    elif nummern:
                        print("  %d neue Nachricht(en)" % len(nummern))
        except KeyboardInterrupt:
            print("angehalten")
            return 0
        except Exception as fehler:
            print("Verbindung verloren (%s). Neuer Versuch in %d Sekunden."
                  % (fehler, warten))
            time.sleep(warten)
            warten = min(warten * 2, WARTEN_MAX)


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "pruefen").lower()
    if befehl == "pruefen":
        darf, grund = kann_starten()
        print("%s: %s" % ("bereit" if darf else "nicht bereit", grund))
        return 0 if darf else 1
    if befehl == "laufen":
        return laufen()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
