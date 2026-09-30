"""Marketing - was gesagt wird, wem, wo und wann.

Eine eigene Stelle, kein Mitlaeufer bei Social Media: Social Media
stellt einen Beitrag her, Marketing entscheidet vorher, was ueberhaupt
gesagt werden soll. Der Plan geht in den Warenausgang und wartet auf
deine Freigabe - veroeffentlicht wird nichts.

Aufruf:
    python main.py planen              alle Auftraege im Eingang
    python main.py planen --ohne-modell    Notplan, kostet nichts
    python main.py plaene              was geplant wurde
    python main.py zeigen <auftrag>
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

import kampagne  # noqa: E402

try:
    import warenausgang
    ANGESCHLOSSEN = True
except ImportError:
    warenausgang = None
    ANGESCHLOSSEN = False

try:
    import melden
except ImportError:
    melden = None

AGENT = "marketing"
MODUL = kampagne.MODUL
EINGANG = UNIVERSE / "zustand" / "marketing_eingang"


def offene_auftraege() -> list[dict]:
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
    datei = Path(auftrag.get("_datei", ""))
    if not datei.exists():
        return
    fertig = EINGANG / "_geplant"
    fertig.mkdir(parents=True, exist_ok=True)
    try:
        datei.replace(fertig / datei.name)
    except OSError:
        pass


def einen_planen(auftrag: dict, mit_modell: bool = True) -> dict:
    plan = kampagne.planen(auftrag, mit_modell=mit_modell)
    pfad = kampagne.speichern(plan)
    kennung = _vorlegen(plan, pfad) if ANGESCHLOSSEN else ""

    _melde("fortschritt" if plan.vollstaendig else "frage",
           "Kampagne: %s" % plan.titel,
           plan.botschaft + ("\n\nOhne Modell entstanden - nennt keine "
                             "Kanaele." if not plan.mit_modell else ""),
           plan.auftrag, {"kampagne": str(pfad), "warenausgang": kennung})
    _weglegen(auftrag)
    return {"plan": plan, "datei": pfad, "warenausgang": kennung}


def _vorlegen(plan, pfad: Path) -> str:
    """Vom Qualitaetsmanager als Text abnehmen lassen und einstellen."""
    try:
        qm = _qualitaetsmanager()
        if qm is not None:
            ergebnis = qm.abnehmen(
                was="text", datei=kampagne.als_markdown(plan),
                auftrag=plan.auftrag, modul=MODUL, titel=plan.titel,
                zettel={"gueteklasse": "kampagne", "bildquellen": "-",
                        "stimme": "-",
                        "taugt_fuer": "Vorlage fuer Social Media"},
                kosten=plan.kosten)
            return ergebnis.get("warenausgang", "")
    except Exception:
        pass
    try:
        eintrag = warenausgang.einstellen(
            was="text", auftrag=plan.auftrag, modul=MODUL, titel=plan.titel,
            datei=str(pfad), gueteklasse="kampagne",
            laenge="%d Kanaele" % len(plan.kanaele), format_="markdown",
            kosten=plan.kosten, abgenommen_von=AGENT,
            taugt_fuer="Vorlage fuer Social Media",
            notiz="Ohne Qualitaetsmanager eingestellt - ungeprueft.")
        return eintrag["kennung"]
    except Exception:
        return ""


def _qualitaetsmanager():
    """Nur die eine Datei laden - diese hier heisst selbst main.py."""
    import importlib.util

    fertig = sys.modules.get("qm_abnahme")
    if fertig is not None:
        return fertig
    datei = QM / "main.py"
    if not datei.exists():
        return None
    kennung = importlib.util.spec_from_file_location("qm_abnahme", datei)
    modul = importlib.util.module_from_spec(kennung)
    sys.modules["qm_abnahme"] = modul
    kennung.loader.exec_module(modul)
    return modul


def alle_planen(mit_modell: bool = True) -> list[dict]:
    auftraege = offene_auftraege()
    if not auftraege:
        print("Nichts im Eingang.")
        return []
    aus = []
    for auftrag in auftraege:
        ergebnis = einen_planen(auftrag, mit_modell)
        plan = ergebnis["plan"]
        print("%s  %-46s %s" % ("+" if plan.vollstaendig else "?",
                                plan.titel[:46],
                                ergebnis["warenausgang"] or "(nicht eingestellt)"))
        aus.append(ergebnis)
    return aus


def plaene() -> list[Path]:
    wurzel = UNIVERSE / "zustand" / "kampagnen"
    return sorted(wurzel.glob("*/KAMPAGNE.md")) if wurzel.exists() else []


def _marke() -> str:
    """Welche Marke der NUTZER fuer dieses Modul gesetzt hat.

    RepoCity setzt keine. Steht hier "keine", ist das kein Fehler, sondern
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


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    rest = argumente[1:]

    if befehl == "planen":
        alle_planen(mit_modell="--ohne-modell" not in rest)
        return 0

    if befehl == "plaene":
        gefunden = plaene()
        if not gefunden:
            print("Noch keine Kampagne.")
            return 0
        for p in gefunden:
            print("%-24s %s" % (p.parent.name, p))
        return 0

    if befehl == "zeigen":
        if not rest:
            print("Welcher Auftrag?")
            return 2
        datei = kampagne.ordner(rest[0]) / "KAMPAGNE.md"
        if not datei.exists():
            print("Keine Kampagne zu %s." % rest[0])
            return 1
        print(datei.read_text(encoding="utf-8"))
        return 0

    if befehl == "stand":
        print("Marketing")
        print("  Eingang        %d Auftraege" % len(offene_auftraege()))
        print("  Kampagnen      %d" % len(plaene()))
        print("  Kern           %s" % ("angeschlossen" if ANGESCHLOSSEN
                                       else "-- fehlt --"))
        print("  Plan kostet    %.3f EUR (geschaetzt aus der Preistabelle)"
              % kampagne.KOSTEN_JE_PLAN_EUR)
        print("  deine Marke    %s" % _marke())
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
