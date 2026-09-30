"""Der Implementierer - er baut, was du freigegeben hast.

Er faengt nie von selbst an. Er baut nur zu einem Bauplan, der im
Warenausgang liegt und von dir freigegeben ist. Danach legt er das
Ergebnis wieder dort ab und wartet auf deine zweite Freigabe, bevor
irgendetwas ins laufende Universe kommt.

    Bauplan freigegeben
        -> Dateien schreiben        neben dem Universe, nie darin
        -> uebersetzen und pruefen  kostet nichts, ist echt
        -> nachbessern              liest die Maengel, bessert nach, misst
                                    wieder - hoechstens fuenf Runden
                                    (schleife.py)
        -> Qualitaetsmanager        laesst nichts durch, was nicht uebersetzt
        -> Warenausgang             du siehst es in der App
        -> deine Freigabe           gilt genau dem vorgelegten Stand
                                    (Fingerabdruck) - aendert sich danach
                                    eine Datei, wird nicht uebernommen
        -> uebernehmen              mit Sicherung der alten Dateien

Aufruf:
    python main.py offen                 welche Bauplaene freigegeben sind
    python main.py bauen <auftrag>       schreiben, pruefen, vorlegen
    python main.py uebernehmen <auftrag> den freigegebenen Bau einlegen
    python main.py zurueck <auftrag>     die Sicherung zurueckspielen
    python main.py stand
"""
from __future__ import annotations

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

import werkbank  # noqa: E402
import schleife  # noqa: E402

try:
    import warenausgang
    import rueckweg
    ANGESCHLOSSEN = True
except ImportError:
    warenausgang = rueckweg = None
    ANGESCHLOSSEN = False


def _qualitaetsmanager():
    """Den Qualitaetsmanager holen, ohne seinen Ordner auf den Pfad zu legen.

    Diese Datei heisst selbst main.py. Ein schlichtes "import main" holt
    darum sie selbst - und der Ordner des Qualitaetsmanagers auf dem
    Suchpfad wuerde ausserdem seine uebrigen Module fuer alle sichtbar
    machen. Es wird genau eine Datei geladen, unter eigenem Namen.
    """
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


try:
    import melden
except ImportError:
    melden = None

AGENT = "implementierer"
MODUL = werkbank.MODUL


# ------------------------------------------------------------------ Suchen

def freigegebene_plaene() -> list[dict]:
    """Bauplaene, die du freigegeben hast und die noch nicht gebaut sind."""
    if not ANGESCHLOSSEN:
        return []
    aus = []
    for zettel in warenausgang.bestand():
        if zettel.get("was") != "bauplan":
            continue
        if zettel.get("stand") != warenausgang.FREIGEGEBEN:
            continue
        auftrag = zettel.get("auftrag", "")
        if (werkbank.neubau(auftrag)).exists():
            continue          # schon gebaut
        aus.append(zettel)
    return aus


def _zettel_zum_bau(auftrag: str) -> dict | None:
    if not ANGESCHLOSSEN:
        return None
    for zettel in warenausgang.bestand():
        if zettel.get("was") == "code" and zettel.get("auftrag") == auftrag:
            return zettel
    return None


# ------------------------------------------------------------------ Bauen

def bauen(auftrag: str) -> int:
    plan = werkbank.bauplan(auftrag)
    if plan is None:
        print("Zu %s gibt es keinen Bauplan." % auftrag)
        return 1

    if ANGESCHLOSSEN and not any(
            z.get("auftrag") == auftrag
            and z.get("was") == "bauplan"
            and z.get("stand") == warenausgang.FREIGEGEBEN
            for z in warenausgang.bestand()):
        print("Der Bauplan zu %s ist nicht freigegeben. Es wird nicht "
              "gebaut." % auftrag)
        return 1

    print("Baue %s ..." % plan.get("titel", auftrag))
    geschrieben = werkbank.schreiben(auftrag, plan)
    if geschrieben.get("hinweis"):
        print("  " + geschrieben["hinweis"])
    for d in geschrieben["dateien"]:
        print("  %s %-40s %s" % ("+" if d.get("geschrieben") else "!",
                                 d["pfad"], d.get("grund", "")))

    bericht = werkbank.messen(auftrag, plan)
    _messung_zeigen(bericht)

    # Die Schleife: Maengel lesen, nachbessern, wieder messen - hoechstens
    # schleife.RUNDEN_HOECHSTENS Mal. Was sie hinterlaesst, wird vorgelegt.
    nachbesserung = schleife.nachbessern(auftrag, plan, bericht)
    print("  " + schleife.als_text(nachbesserung))
    if nachbesserung["runden"]:
        bericht = nachbesserung["bericht"]
        _messung_zeigen(bericht)
        geschrieben["kosten"] = geschrieben.get("kosten", 0.0) + nachbesserung["kosten"]

    kennung = _vorlegen(auftrag, plan, geschrieben, bericht)
    if kennung:
        vorlage = werkbank.vorgelegt_merken(auftrag, kennung)
        print("\nLiegt als %s im Warenausgang (Abdruck %s). Erst nach deiner "
              "Freigabe kommt es ins Universe - und nur genau dieser Stand."
              % (kennung, vorlage["fingerabdruck"]))
    _melde("fortschritt" if bericht["uebersetzt"] else "fehler",
           "Bau fertig: %s" % plan.get("titel", auftrag),
           _text(bericht, geschrieben, nachbesserung), auftrag,
           {"warenausgang": kennung, "nachbesserung": nachbesserung["halt"],
            "runden": nachbesserung["runden"]})
    return 0 if bericht["uebersetzt"] else 1


def _messung_zeigen(bericht: dict) -> None:
    print("  %d Dateien, %d Zeilen, %s" % (
        bericht["dateien"], bericht["zeilen"],
        "uebersetzt" if bericht["uebersetzt"] else "UEBERSETZT NICHT"))
    if bericht["pruefungen_gelaufen"]:
        print("  Pruefungen: %d bestanden, %d durchgefallen"
              % (bericht["bestanden"], bericht["durchgefallen"]))


def _text(bericht: dict, geschrieben: dict, nachbesserung: dict | None = None) -> str:
    zeilen = ["%d Dateien, %d Zeilen." % (bericht["dateien"], bericht["zeilen"])]
    if nachbesserung is not None:
        zeilen.append(schleife.als_text(nachbesserung))
    if not bericht["uebersetzt"]:
        zeilen.append("Uebersetzt nicht:")
        zeilen += ["  " + f for f in bericht["uebersetzungsfehler"]]
    if bericht["pruefungen_gelaufen"]:
        zeilen.append("Pruefungen: %d bestanden, %d durchgefallen"
                      % (bericht["bestanden"], bericht["durchgefallen"]))
    else:
        zeilen.append("Keine Pruefungen im Bau - es gibt keine pruefungen.py.")
    if geschrieben.get("kosten"):
        zeilen.append("Gekostet: %.4f EUR" % geschrieben["kosten"])
    return "\n".join(zeilen)


def _vorlegen(auftrag: str, plan: dict, geschrieben: dict,
              bericht: dict) -> str:
    """Vom Qualitaetsmanager abnehmen lassen und einstellen."""
    if not ANGESCHLOSSEN:
        return ""
    qm = _qualitaetsmanager()
    try:
        if qm is None:
            raise RuntimeError("Qualitaetsmanager nicht gefunden")
        ergebnis = qm.abnehmen(
            was="code", datei=werkbank.neubau(auftrag), auftrag=auftrag,
            modul=MODUL, titel=plan.get("titel", auftrag),
            zettel={"gueteklasse": "bau",
                    "taugt_fuer": "Uebernahme ins Universe",
                    "bildquellen": "-", "stimme": "-"},
            kosten=geschrieben.get("kosten", 0.0))
        return ergebnis.get("warenausgang", "")
    except Exception:
        # Ohne den Qualitaetsmanager wird trotzdem eingestellt - aber
        # ungeprueft, und das steht dann auch auf dem Zettel.
        try:
            eintrag = warenausgang.einstellen(
                was="code", auftrag=auftrag, modul=MODUL,
                titel=plan.get("titel", auftrag),
                datei=str(werkbank.neubau(auftrag)), gueteklasse="bau",
                laenge="%d Dateien" % bericht["dateien"], format_="python",
                kosten=geschrieben.get("kosten", 0.0), abgenommen_von=AGENT,
                taugt_fuer="Uebernahme ins Universe",
                notiz="Ohne Qualitaetsmanager eingestellt - ungeprueft.")
            return eintrag["kennung"]
        except Exception:
            return ""


# ------------------------------------------------------------------ Uebernahme

def uebernehmen(auftrag: str) -> int:
    zettel = _zettel_zum_bau(auftrag)
    if ANGESCHLOSSEN and (zettel is None
                          or zettel.get("stand") != warenausgang.FREIGEGEBEN):
        print("Der Bau zu %s ist nicht freigegeben. Es wird nichts "
              "uebernommen." % auftrag)
        return 1

    # Die Freigabe gilt genau dem Stand, der vorgelegt wurde. Ist seither
    # eine Datei anders, wird nichts uebernommen - auch nicht "fast dasselbe".
    erlaubt, grund = werkbank.uebernahme_erlaubt(auftrag)
    if not erlaubt:
        print("Es wird nichts uebernommen: " + grund)
        _melde("warnung", "Uebernahme verweigert: %s" % auftrag, grund, auftrag)
        return 1

    ergebnis = werkbank.uebernehmen(auftrag)
    if not ergebnis["kopiert"]:
        print("Es gibt nichts zu uebernehmen.")
        return 1
    for pfad in ergebnis["kopiert"]:
        print("  -> universe/%s" % pfad)
    if ergebnis["gesichert"]:
        print("\n%d Datei(en) vorher gesichert unter <bau>/vorher/."
              % len(ergebnis["gesichert"]))
    if ergebnis["abgelehnt"]:
        print("\nAbgelehnt, weil der Pfad aus dem Universe zeigt:")
        for pfad in ergebnis["abgelehnt"]:
            print("  " + pfad)
    print("\nJetzt den Pruefstand laufen lassen:")
    print("  python universe/kern/pruefstand.py trocken")
    _melde("fortschritt", "Bau uebernommen: %s" % auftrag,
           "\n".join("universe/" + p for p in ergebnis["kopiert"]), auftrag)
    return 0


def zurueck(auftrag: str) -> int:
    """Die Sicherung zurueckspielen - wenn die Uebernahme etwas kaputt macht."""
    import shutil
    sicherung = werkbank.neubau(auftrag).parent / "vorher"
    if not sicherung.exists():
        print("Es gibt keine Sicherung zu %s." % auftrag)
        return 1
    zurueckgelegt = 0
    for datei in sorted(sicherung.rglob("*")):
        if not datei.is_file():
            continue
        rel = datei.relative_to(sicherung)
        ziel = UNIVERSE / rel
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(datei, ziel)
        print("  <- universe/%s" % rel)
        zurueckgelegt += 1
    print("\n%d Datei(en) auf den Stand vor der Uebernahme gebracht."
          % zurueckgelegt)
    return 0


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


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    rest = argumente[1:]

    if befehl == "offen":
        plaene = freigegebene_plaene()
        if not plaene:
            print("Kein freigegebener Bauplan wartet.")
            return 0
        for z in plaene:
            print("%-10s %s" % (z.get("auftrag"), z.get("titel")))
        return 0

    if befehl in ("bauen", "uebernehmen", "zurueck"):
        if not rest:
            print("Welcher Auftrag?")
            return 2
        return {"bauen": bauen, "uebernehmen": uebernehmen,
                "zurueck": zurueck}[befehl](rest[0])

    if befehl == "stand":
        wurzel = UNIVERSE / "zustand" / "bau"
        baue = sorted(p.parent.name for p in wurzel.glob("*/neu")) \
            if wurzel.exists() else []
        print("Implementierer")
        print("  freigegebene Bauplaene  %d" % len(freigegebene_plaene()))
        print("  gebaut                  %d" % len(baue))
        print("  Kern                    %s"
              % ("angeschlossen" if ANGESCHLOSSEN else "-- fehlt --"))
        print("  Datei kostet            %.3f EUR (geschaetzt aus der "
              "Preistabelle)" % werkbank.KOSTEN_JE_DATEI_EUR)
        print("  deine Marke             %s" % _marke())
        print("\n  Gebaut wird immer neben dem Universe. Ins Universe kommt")
        print("  nur, was du freigibst - und dann mit Sicherung.")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
