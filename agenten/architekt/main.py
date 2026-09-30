"""Der Architekt - er plant, er baut nicht.

Ein Bauauftrag kommt vom Sekretaer in den Eingang. Der Architekt macht
daraus einen Bauplan, laesst ihn vom Qualitaetsmanager ansehen und legt
ihn in den Warenausgang. Erst wenn du dort freigibst, nimmt ihn der
Implementierer auf.

Warum diese Reihenfolge und nicht gleich bauen: ein abgelehnter Plan
kostet ein paar Cent, ein abgelehnter Bau eine halbe Stunde. Und ein
Plan laesst sich in zwei Minuten lesen - Code nicht.

Aufruf:
    python main.py entwerfen              alle Auftraege im Eingang planen
    python main.py entwerfen --ohne-modell    Notplan, kostet nichts
    python main.py plaene                 was geplant wurde
    python main.py zeigen <auftrag>       einen Bauplan lesen
    python main.py stand
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
QM = UNIVERSE / "qualitaetsmanager"

sys.path.insert(0, str(HIER))
for _p in (str(KERN), str(QM)):
    if _p not in sys.path:
        sys.path.append(_p)

import entwurf  # noqa: E402

try:
    import warenausgang
    import rueckweg
    ANGESCHLOSSEN = True
except ImportError:
    warenausgang = rueckweg = None
    ANGESCHLOSSEN = False

try:
    import melden
except ImportError:
    melden = None

AGENT = "architekt"
MODUL = entwurf.MODUL

#: Hier legt der Sekretaer Bauauftraege ab.
EINGANG = UNIVERSE / "zustand" / "bau_eingang"


# ------------------------------------------------------------------ Eingang

def offene_auftraege() -> list[dict]:
    """Was im Eingang liegt, aelteste zuerst."""
    if not EINGANG.exists():
        return []
    aus = []
    for datei in sorted(EINGANG.glob("*.json")):
        try:
            satz = json.loads(datei.read_text(encoding="utf-8"))
        except Exception:
            continue
        satz["_datei"] = str(datei)
        satz.setdefault("id", datei.stem)
        aus.append(satz)
    return aus


def _weglegen(auftrag: dict) -> None:
    """Einen erledigten Auftrag aus dem Eingang nehmen."""
    datei = Path(auftrag.get("_datei", ""))
    if not datei.exists():
        return
    fertig = EINGANG / "_geplant"
    fertig.mkdir(parents=True, exist_ok=True)
    try:
        datei.replace(fertig / datei.name)
    except OSError:
        pass


# ------------------------------------------------------------------ Planen

def einen_planen(auftrag: dict, mit_modell: bool = True) -> dict:
    """Einen Auftrag zu einem Bauplan machen und vorlegen."""
    plan = entwurf.entwerfen(auftrag, mit_modell=mit_modell)
    pfad = entwurf.speichern(plan)

    kennung = ""
    if ANGESCHLOSSEN:
        kennung = _vorlegen(plan, pfad)

    _melde("fortschritt" if plan.vollstaendig else "frage",
           "Bauplan: %s" % plan.titel,
           plan.ziel + ("\n\nOhne Modell entstanden - er nennt keine Dateien."
                        if not plan.mit_modell else ""),
           plan.auftrag, {"bauplan": str(pfad), "warenausgang": kennung})
    _weglegen(auftrag)
    return {"plan": plan, "datei": pfad, "warenausgang": kennung}


def _vorlegen(plan, pfad: Path) -> str:
    """Den Plan vom Qualitaetsmanager ansehen lassen und einstellen.

    Geprueft wird er als Text: ein Plan unter der Mindestlaenge sagt
    nichts. Ueber den Inhalt urteilst du.
    """
    try:
        eintrag = warenausgang.einstellen(
            was="bauplan", auftrag=plan.auftrag, modul=MODUL,
            titel=plan.titel, datei=str(pfad),
            gueteklasse="plan",
            laenge="%d Dateien" % len(plan.dateien),
            format_="markdown", stimme="", bildquellen="",
            kosten=plan.kosten, abgenommen_von=AGENT,
            taugt_fuer="Vorlage fuer den Implementierer",
            notiz=("Mit Modell entworfen." if plan.mit_modell
                   else "Ohne Modell entstanden - nennt keine Dateien."))
        return eintrag["kennung"]
    except Exception:
        return ""


def alle_planen(mit_modell: bool = True) -> list[dict]:
    auftraege = offene_auftraege()
    if not auftraege:
        print("Nichts im Eingang.")
        return []
    aus = []
    for auftrag in auftraege:
        ergebnis = einen_planen(auftrag, mit_modell)
        plan = ergebnis["plan"]
        print("%s  %-46s %s" % (
            "+" if plan.vollstaendig else "?", plan.titel[:46],
            ergebnis["warenausgang"] or "(nicht eingestellt)"))
        aus.append(ergebnis)
    return aus


# ------------------------------------------------------------------ Ansehen

def plaene() -> list[Path]:
    wurzel = UNIVERSE / "zustand" / "bau"
    return sorted(wurzel.glob("*/BAUPLAN.md")) if wurzel.exists() else []


def _marke() -> str:
    """Welche Marke der NUTZER fuer dieses Modul gesetzt hat.

    RepoCity setzt keine. Steht hier 'keine', ist das kein Fehler, sondern
    die Voreinstellung: was ausgegeben wird, entscheidet der Nutzer.
    """
    try:
        import verbrauch
        lauf = verbrauch.marke(MODUL, "lauf")
        monat = verbrauch.marke(MODUL, "monat")
        if not lauf and not monat:
            return "keine - der Nutzer hat keine gesetzt"
        return "%.2f EUR je Lauf, %.2f im Monat" % (lauf, monat)
    except Exception:
        return "-- nicht ermittelbar --"


def _melde(art: str, kurz: str, text: str, vorgang: str = "",
           daten: dict | None = None) -> None:
    if melden is not None:
        try:
            melden.melde(MODUL, text, art=art, zusammenfassung=kurz,
                         vorgang=vorgang or None, daten=daten or {})
        except Exception:
            pass


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    rest = argumente[1:]

    if befehl == "entwerfen":
        alle_planen(mit_modell="--ohne-modell" not in rest)
        return 0

    if befehl == "plaene":
        gefunden = plaene()
        if not gefunden:
            print("Noch kein Bauplan.")
            return 0
        for p in gefunden:
            print("%-24s %s" % (p.parent.name, p))
        return 0

    if befehl == "zeigen":
        if not rest:
            print("Welcher Auftrag?")
            return 2
        datei = entwurf.ordner(rest[0]) / "BAUPLAN.md"
        if not datei.exists():
            print("Kein Bauplan zu %s." % rest[0])
            return 1
        print(datei.read_text(encoding="utf-8"))
        return 0

    if befehl == "stand":
        print("Architekt")
        print("  Eingang        %d Auftraege" % len(offene_auftraege()))
        print("  Bauplaene      %d" % len(plaene()))
        print("  Kern           %s" % ("angeschlossen" if ANGESCHLOSSEN
                                       else "-- fehlt --"))
        print("  Entwurf kostet %.3f EUR (geschaetzt aus der Preistabelle)"
              % entwurf.KOSTEN_JE_ENTWURF_EUR)
        print("  deine Marke    %s" % _marke())
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
