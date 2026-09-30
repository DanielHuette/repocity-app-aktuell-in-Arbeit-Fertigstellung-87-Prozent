"""Das eine Modell fuer das ganze Universe.

Am 11.09.2026 standen im Universe sieben Stellen mit Haiku 3.5 fest im Code
und neun weitere mit Sonnet 4.5 als Voreinstellung - jede fuer sich, keine
wusste von der anderen. Daniel: "minimum model muss opus 5 sein, ueberall".
Seitdem kennt genau eine Stelle den Modellnamen: diese.

    import modellwahl
    MODELL = modellwahl.MODELL

Woher der Name kommt: UNIVERSE_MODELL aus der .env (kern/umgebung.py setzt
sie beim Start in die Umgebung), sonst die Voreinstellung. Ein Modell unter
Opus - Haiku oder Sonnet, gleich welcher Fassung - wird nicht angenommen:
der Start bricht mit einem klaren Satz ab, statt still mit dem falschen
Modell zu arbeiten. Die Pruefung `kosten.kein-modell-unter-opus` sucht dazu
den Code ab, damit auch kein fester Name mehr hineinkommt.

Preise stehen nicht hier, sondern in universe/kosten.json.

    python modellwahl.py            welches Modell gilt
    python modellwahl.py suchen     wo im Universe ein Modell unter Opus steht
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

KERN = Path(__file__).resolve().parent
UNIVERSE = KERN.parent

#: Gilt, wenn die .env nichts anderes sagt.
VOREINSTELLUNG = "claude-opus-5"

#: Modellnamen, die im Universe nichts zu suchen haben. Gesucht wird nach
#: Namen, nicht nach Woertern: "Opus" ist auch ein Tonformat, "Sonnet" ein
#: Gedicht. Ein Name faengt mit "claude-" an, dann kommt die Stufe.
UNTER_OPUS = re.compile(r"claude-(?:3|sonnet|haiku)[\w.-]*")

#: Was die Suche liest - Code, Einstellungen, Beschreibungen.
DATEIARTEN = {".py", ".js", ".mjs", ".ts", ".json", ".jsonc", ".kt", ".md",
              ".astro", ".yaml", ".yml", ".toml"}

#: Was die Suche auslaesst: Fremdpakete, Bauergebnisse, Rohdaten.
AUSSEN = {"node_modules", ".git", "__pycache__", ".wrangler", "build", "dist",
          ".astro", "filme", "daten", "github_cache"}


def pruefen(name: str) -> str:
    """Gibt den Namen zurueck - oder bricht ab, wenn er unter Opus liegt."""
    name = (name or "").strip()
    if not name:
        raise ValueError("Kein Modellname - UNIVERSE_MODELL ist leer.")
    if UNTER_OPUS.search(name):
        raise ValueError(
            "Modell %r liegt unter Opus und ist im Universe nicht zugelassen "
            "(Daniel, 11.09.2026: mindestens Opus 5, ueberall)." % name)
    return name


def _env_laden() -> None:
    """Die .env einlesen, falls das noch niemand getan hat. Ueber den Pfad
    geladen, weil im Universe mehrere Ordner eine eigene umgebung.py tragen."""
    try:
        import importlib.util as iu
        spec = iu.spec_from_file_location("kern_umgebung", KERN / "umgebung.py")
        modul = iu.module_from_spec(spec)
        spec.loader.exec_module(modul)
        modul.laden()
    except Exception:
        pass


def modell() -> str:
    _env_laden()
    return pruefen(os.getenv("UNIVERSE_MODELL") or VOREINSTELLUNG)


def unter_opus_im_code(wurzel: Path | str | None = None) -> list[str]:
    """Jede Zeile im Universe, die ein Modell unter Opus nennt - 'datei:zeile'."""
    wurzel = Path(wurzel or UNIVERSE)
    treffer: list[str] = []
    for datei in sorted(wurzel.rglob("*")):
        if not datei.is_file():
            continue
        if datei.suffix not in DATEIARTEN and datei.name != ".env":
            continue
        teile = datei.relative_to(wurzel).parts
        if any(t in AUSSEN for t in teile[:-1]):
            continue
        try:
            text = datei.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for nummer, zeile in enumerate(text.splitlines(), 1):
            if UNTER_OPUS.search(zeile):
                treffer.append("%s:%d" % ("/".join(teile), nummer))
    return treffer


MODELL = modell()


def _main(argumente: list[str]) -> int:
    if argumente and argumente[0] == "suchen":
        treffer = unter_opus_im_code()
        for t in treffer:
            print(t)
        print("%d Stellen mit einem Modell unter Opus" % len(treffer))
        return 1 if treffer else 0
    print(MODELL)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
