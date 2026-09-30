"""Bauen und veroeffentlichen - immer durch das Tor.

Wer die App baut oder die Webseite veroeffentlicht, geht hier durch. Erst
laeuft die Pruefstrasse; nur wenn sie gruen ist, passiert etwas. Rot heisst:
es passiert nichts, und der Grund steht da.

Das ist die Stelle, an der nichts Kaputtes nach draussen kommt. Deshalb gibt
es genau einen Weg daran vorbei, und der kostet einen Satz:

    python universe/kern/bau.py app
    python universe/kern/bau.py webseite
    python universe/kern/bau.py app --trotzdem "Grund, warum es diesmal muss"

Ein --trotzdem ohne Grund wird abgewiesen - wie ein Nein ohne Satz auf dem
Rueckweg. Und jedes --trotzdem wird gemeldet, damit es nicht zur Gewohnheit
wird.
"""
from __future__ import annotations

import re
import shutil
import subprocess

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
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
APP = UNIVERSE / "app"
GRADLE = APP / "repocity"
WEBSEITE = UNIVERSE / "webseite"

if str(HIER) not in sys.path:
    sys.path.insert(0, str(HIER))

import pruefstrasse  # noqa: E402

try:
    import melden
except ImportError:                                  # pragma: no cover
    melden = None

MODUL = "system.bau"
WINDOWS = sys.platform.startswith("win")


def _bauzeit_stempeln() -> None:
    """BAUZEIT in wrangler.jsonc auf jetzt setzen - die Laufzeit der Webseite
    im Dashboard ist die Zeit seit diesem Stempel."""
    import re
    from datetime import datetime, timezone
    datei = WEBSEITE / "wrangler.jsonc"
    roh = datei.read_bytes()
    jetzt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ").encode()
    neu = re.sub(rb'"BAUZEIT": "[^"]*"', b'"BAUZEIT": "' + jetzt + b'"', roh, count=1)
    if neu != roh:
        datei.write_bytes(neu)


def _laufen(befehl: list[str], wo: Path) -> int:
    """Einen Befehl ausfuehren und seine Ausgabe durchreichen."""
    print("  > %s" % " ".join(befehl), flush=True)
    return subprocess.call(befehl, cwd=str(wo), shell=WINDOWS)


#: Der Pruefstand ist ausgesetzt - von Daniel am 14.09.2026 angeordnet:
#: "er ist ab sofort ausgesetzt und nur wenn ich sage pruefe wird irgendwas
#: geprueft [...] das endet hier und jetzt!"
#:
#: Das Tor bleibt im Code stehen und ist in einer Zeile wieder scharf zu
#: stellen. Geloescht wird es nicht: die 374 Pruefungen und ihre Gegenproben
#: sind Arbeit von zwei Wochen, und wozu sie da sind, hat er im selben Satz
#: gesagt - nach dem Bau die Funktion nachsehen, vor dem Livegang, ob alles
#: laeuft. Nur eben dann, und nicht bei jedem Handgriff.
TOR_AUSGESETZT = True


def _durchs_tor(was: str, trotzdem: str) -> bool:
    if TOR_AUSGESETZT:
        print("Tor ausgesetzt (Daniel, 14.09.2026) - es wird sofort gebaut. "
              "Pruefen nur auf Zuruf: python universe/kern/pruefstand.py trocken",
              flush=True)
        return True
    befund = pruefstrasse.tor(was)
    print(befund.satz(), flush=True)

    # Die Gegenproben laufen hier NICHT mit.
    #
    # Am 09.09.2026 einmal so gebaut und gemessen: der ganze Satz braucht
    # ueber zehn Minuten, weil einzelne Gegenproben selbst bauen oder
    # einbetten. Vor jedem Bau ist das kein Netz, sondern eine Bremse -
    # und wer bremst, baut am Ende daran vorbei.
    #
    # Sie laufen stattdessen im Tageslauf
    # (`python universe/kern/pruefstrasse.py taeglich`) und auf Zuruf
    # (`... pruefstrasse.py gegenproben`). Beides startet jede einzelne
    # wirklich - gezaehlt wird nirgends mehr.
    if befund.gruen:
        return True
    for kennung, grund in befund.rote:
        print("  rot: %s - %s" % (kennung, grund[:160]), flush=True)
    if not trotzdem:
        print("\nEs wird nichts gebaut. Erst gruen, dann bauen - oder mit "
              "--trotzdem \"Grund\" vorbei, wenn es sein muss.", flush=True)
        return False
    print("\nVorbei am Tor, auf ausdruecklichen Wunsch: %s" % trotzdem, flush=True)
    if melden is not None:
        try:
            melden.melde(MODUL,
                         "Am Tor vorbei gebaut (%s). Grund: %s\n\nRot waren: %s"
                         % (was, trotzdem,
                            ", ".join(k for k, _ in befund.rote)),
                         art="warnung",
                         zusammenfassung="Am Tor vorbei: " + was,
                         daten={"anlass": was, "grund": trotzdem,
                                "rote": [k for k, _ in befund.rote]})
        except Exception:
            pass
    return True


# --------------------------------------------------------------------- App

def _fassung() -> str:
    """Die Fassung steht in build.gradle.kts - nicht raten, nachlesen."""
    text = (GRADLE / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    treffer = re.search(r'versionName\s*=\s*"([^"]+)"', text)
    return treffer.group(1) if treffer else "ohne-nummer"


def app(trotzdem: str = "") -> int:
    if not _durchs_tor("bau", trotzdem):
        return 1
    gradlew = "gradlew.bat" if WINDOWS else "./gradlew"
    # Nur bauen. Die Pruefungen der App liefen hier mit, bis Daniel am
    # 15.09.2026 darauf gestossen ist - der Pruefstand ist seit dem 14.09.
    # ausgesetzt, und dieser Aufruf war das letzte Schlupfloch. Sie bleiben
    # stehen und laufen auf Zuruf: gradlew testDebugUnitTest
    schluss = _laufen([gradlew, "assembleDebug", "--console=plain"], GRADLE)
    if schluss != 0:
        print("Der Bau der App ist gescheitert.", flush=True)
        return schluss
    fertig = GRADLE / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    if not fertig.exists():
        print("Gebaut, aber die APK liegt nicht, wo sie liegen sollte.", flush=True)
        return 1
    ziel = APP / ("RepoCity-%s-debug.apk" % _fassung())
    shutil.copy2(fertig, ziel)
    print("fertig: %s (%.1f MB)" % (ziel, ziel.stat().st_size / 1024 / 1024), flush=True)
    return 0


# ----------------------------------------------------------------- Webseite

def webseite(trotzdem: str = "") -> int:
    # "webseite", nicht "veroeffentlichen": so heisst das Tor in
    # pruefstrasse.py, und nur unter diesem Namen greift die Ausnahmeliste
    # TOR_OHNE. Mit dem anderen Namen lief alles durch - auch die Pruefungen
    # des Handelskerns, die mit der Webseite nichts zu tun haben. Es kracht
    # dabei nicht, es wird nur stillschweigend mehr geprueft als vereinbart.
    if not _durchs_tor("webseite", trotzdem):
        return 1
    _bauzeit_stempeln()
    schluss = _laufen(["npm", "run", "build"], WEBSEITE)
    if schluss != 0:
        print("Der Bau der Webseite ist gescheitert.", flush=True)
        return schluss
    schluss = _laufen(["npx", "wrangler", "deploy"], WEBSEITE)
    if schluss != 0:
        print("Das Veroeffentlichen ist gescheitert.", flush=True)
        return schluss
    print("veroeffentlicht: https://speedofthespirit.dev", flush=True)
    return 0


# ------------------------------------------------------------------- Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "").lower()
    rest = argumente[1:]

    trotzdem = ""
    if "--trotzdem" in rest:
        i = rest.index("--trotzdem")
        trotzdem = " ".join(rest[i + 1:]).strip()
        if not trotzdem:
            print("Ein --trotzdem ohne Grund wird abgewiesen. Schreib dazu, "
                  "warum es diesmal sein muss.")
            return 2

    if befehl == "app":
        return app(trotzdem)
    if befehl in ("webseite", "web"):
        return webseite(trotzdem)

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
