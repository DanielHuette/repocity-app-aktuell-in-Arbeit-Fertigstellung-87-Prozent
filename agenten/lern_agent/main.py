"""Die Lern-Werkstatt.

    python main.py einmal    was im Eingang liegt, abarbeiten, dann Schluss
    python main.py takt      immer wieder nachsehen (Dauerlauf)
    python main.py stand     was gerade anliegt

**Woher die Auftraege kommen: aus universe/zustand/lern_eingang.**
Dort legt sie der Sekretaer als JSON ab (sekretaer/verteiler.py) und startet
danach diese Werkstatt mit "einmal". Das ist der einzige Weg herein. Die
Werkstatt fragt den Hub nicht selbst - wer beim Hub abholt, ist der
Sekretaer, und zwar allein.

**Der Halt vor der Abnahme.** Zuerst entsteht nur das Curriculum. Es wird
vorgelegt, und erst nach dem Ja faengt an, was Zeit und Geld kostet. Der
Auftrag wartet dabei nicht im laufenden Prozess, sondern auf der Platte:
er wird in `zustand/lern_abnahme` geparkt und beim naechsten Lauf wieder
aufgenommen, sobald am Hub eine Entscheidung dazu steht. Ein Prozess, der
eine Viertelstunde auf ein Ja wartet, blockiert seinen eigenen Starter -
und der raeumt ihn nach einer halben Stunde ab.

Bis zum 09.09.2026 stimmte hier dreierlei nicht:

* Sie fragte `HUB_URL + /api/auftrag/lern` und `/api/abnahme/lern/<id>`.
  Beide Adressen hat es beim Hub nie gegeben. Die Aufrufe fielen in den
  Fehlerzweig, die Antwort war immer "nichts da": die Werkstatt drehte im
  Leerlauf und konnte gar keinen Auftrag bekommen.
* Der Sekretaer startete sie mit "einmal" - das Wort wurde nicht
  ausgewertet. Sie ging in die Endlosschleife und wurde nach der halben
  Stunde vom Starter abgeraeumt, mit Rueckgabe ungleich null.
* Die Abnahme wurde im laufenden Prozess abgewartet, bis zu 15 Minuten.
"""
from __future__ import annotations

import json
import signal
import sys
import time
from dataclasses import asdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
sys.path.insert(0, str(HIER))


def _kern_baustein(name: str):
    """Einen Kern-Baustein ueber seinen Pfad laden, nicht ueber den Suchpfad.

    main.py gibt es zwoelfmal im Universe, einstellungen.py zehnmal,
    umgebung.py achtmal. Wer sich auf den Suchpfad verlaesst, bekommt
    irgendwann das Modul eines anderen Agenten.
    """
    import importlib.util
    stelle = importlib.util.spec_from_file_location(
        "kern_%s_fuer_lernen" % name, KERN / (name + ".py"))
    modul = importlib.util.module_from_spec(stelle)
    stelle.loader.exec_module(modul)
    return modul


# Die .env MUSS vor einstellungen geladen werden: einstellungen.py liest
# beim Import aus der Umgebung.
_kern_baustein("umgebung").laden()

import einstellungen as e                                    # noqa: E402
import meldung                                               # noqa: E402
import strasse                                               # noqa: E402
import warenausgang_lern                                     # noqa: E402
from modelle import (                                        # noqa: E402
    Aufgabe, Auftrag, Curriculum, Ergebnis, Level, Zustand)

hub = _kern_baustein("hub")
kennung_modul = _kern_baustein("kennung")

EINGANG = e.ZUSTAND / "lern_eingang"
#: Wo ein Auftrag liegt, der auf die Abnahme des Curriculums wartet.
WARTEBANK = e.ZUSTAND / "lern_abnahme"

_laeuft = True


def _halt(*_):
    global _laeuft
    _laeuft = False


# ------------------------------------------------------------- Auftraege

def _liegt_an() -> list[Path]:
    EINGANG.mkdir(parents=True, exist_ok=True)
    return sorted(EINGANG.glob("*.json"))


def _auftrag_aus(satz: dict) -> Auftrag:
    auftrag = Auftrag(
        thema=satz.get("thema") or satz.get("text") or satz.get("titel") or "",
        zielgruppe=satz.get("zielgruppe", "Mitarbeiter ohne Vorkenntnisse"),
        vorwissen=satz.get("vorwissen", "keines"),
        minuten=int(satz.get("minuten", e.MINUTEN_STANDARD)),
        level_anzahl=min(int(satz.get("level", e.LEVEL_STANDARD)), e.LEVEL_MAX),
        stil=satz.get("stil", "3D-Render, ruhig, sachlich"),
        trocken=bool(satz.get("trocken", e.TROCKEN)),
        stoff=satz.get("stoff") if isinstance(satz.get("stoff"), dict) else {},
    )
    if satz.get("id"):
        # Der Arbeitsordner heisst wie die Hub-Kennung - aber entschaerft:
        # die Kennungen des Hubs enthalten einen Doppelpunkt, und aus dem
        # laesst Windows keinen Ordner machen. Gemeldet wird weiter unter
        # der echten Kennung, sonst findet die App den Auftrag nicht wieder.
        auftrag.id = kennung_modul.sauber(str(satz["id"]))
    return auftrag


def naechster_auftrag() -> tuple[Auftrag, str] | None:
    """Der naechste Auftrag und die Hub-Kennung dazu - zwei verschiedene
    Dinge, siehe _auftrag_aus()."""
    for datei in _liegt_an():
        try:
            satz = json.loads(datei.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            datei.replace(datei.with_suffix(".json.kaputt"))
            meldung.melde("fehler", "Auftrag %s war nicht lesbar und liegt "
                                    "jetzt als .kaputt daneben." % datei.name)
            continue
        datei.replace(datei.with_suffix(".json.genommen"))
        auftrag = _auftrag_aus(satz)
        if not auftrag.thema.strip():
            meldung.melde("fehler", "Auftrag %s hat kein Thema - ohne das "
                                    "laesst sich nichts entwerfen." % datei.name)
            continue
        return auftrag, str(satz.get("id") or "")
    return None


# --------------------------------------------------- der Halt vor der Abnahme
#
# Geparkt wird der Auftrag mitsamt dem Curriculum, das Daniel vorgelegt
# bekommt. Das Curriculum liegt daneben auch als curriculum.md - die
# Textfassung ist zum Lesen, diese hier zum Weiterarbeiten. Wuerde nur die
# Textfassung liegen, muesste die Werkstatt nach dem Ja neu entwerfen, und
# dann baute sie etwas anderes, als abgenommen wurde.

def _parken(ergebnis: Ergebnis, kennung: str) -> Path:
    WARTEBANK.mkdir(parents=True, exist_ok=True)
    datei = WARTEBANK / ("%s.json" % ergebnis.auftrag.id)
    datei.write_text(json.dumps(
        {"kennung": kennung,
         "auftrag": asdict(ergebnis.auftrag),
         "curriculum": asdict(ergebnis.curriculum) if ergebnis.curriculum else None,
         "protokoll": ergebnis.protokoll},
        ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    return datei


def _aufnehmen(datei: Path) -> tuple[Ergebnis, str] | None:
    try:
        satz = json.loads(datei.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        datei.replace(datei.with_suffix(".json.kaputt"))
        return None
    auftrag = Auftrag(**satz["auftrag"])
    roh = satz.get("curriculum")
    curriculum = None
    if roh:
        level = []
        for l in roh.get("level", []):
            aufgabe = l.get("aufgabe")
            level.append(Level(**{**l, "aufgabe":
                                  Aufgabe(**aufgabe) if aufgabe else None}))
        curriculum = Curriculum(**{**roh, "level": level})
    ergebnis = Ergebnis(auftrag=auftrag, curriculum=curriculum,
                        zustand=Zustand.WARTET_AUF_ABNAHME)
    ergebnis.protokoll = list(satz.get("protokoll", []))
    return ergebnis, str(satz.get("kennung") or auftrag.id)


def _entscheidung(auftrag_id: str) -> tuple[str, str]:
    """Was Daniel zu diesem Auftrag gesagt hat: ("ja"|"nein"|"", Grund).

    Gefragt wird der Hub - dort steht die Entscheidung an der Meldung, die
    das Curriculum vorgelegt hat. Es gibt keine zweite Stelle dafuer.
    """
    for m in hub.entscheidungen():
        if str(m.get("vorgang") or "") == auftrag_id:
            return str(m.get("entscheidung") or ""), str(m.get("grund") or "")
    return "", ""


def wartende_pruefen() -> int:
    """Geparkte Auftraege, zu denen inzwischen ein Ja vorliegt, weiterbauen."""
    WARTEBANK.mkdir(parents=True, exist_ok=True)
    getan = 0
    for datei in sorted(WARTEBANK.glob("*.json")):
        if not _laeuft:
            break
        aufgenommen = _aufnehmen(datei)
        if aufgenommen is None:
            continue
        ergebnis, kennung = aufgenommen
        wahl, grund = _entscheidung(kennung)
        if not wahl:
            continue
        if wahl == "nein":
            datei.unlink()
            meldung.melde("abgelehnt", "Curriculum %s abgelehnt: %s"
                          % (kennung, grund),
                          {"auftrag": kennung, "grund": grund})
            hub.zustand_melden(kennung, "abgebrochen", grund[:400])
            continue
        datei.unlink()
        _nach_abnahme(ergebnis, kennung)
        getan += 1
    return getan


# ------------------------------------------------------------- ein Kurs

def _nach_abnahme(ergebnis: Ergebnis, kennung: str) -> None:
    """Der zweite Halbschritt, nach dem Ja: jetzt entstehen Ton und Bild."""
    hub.zustand_melden(kennung, "laeuft",
                       "Abgenommen - der Kurs wird gebaut.", fortschritt=0.6)
    try:
        ergebnis = strasse.erzeugen(ergebnis)
    except Exception as fehler:                        # noqa: BLE001
        import traceback
        meldung.melde("fehler", "Auftrag %s abgebrochen: %s" % (kennung, fehler),
                      {"auftrag": kennung,
                       "spur": traceback.format_exc()[-2000:]})
        hub.zustand_melden(kennung, "fehler", str(fehler)[:400])
        return
    _melden_fertig(ergebnis, kennung)


def _melden_fertig(ergebnis: Ergebnis, kennung: str) -> None:
    meldung.melde(ergebnis.zustand.value,
                  "Auftrag %s: %s" % (kennung, ergebnis.zustand.value),
                  {"auftrag": kennung,
                   "kurs": str(ergebnis.kurs) if ergebnis.kurs else None})
    gut = ergebnis.kurs is not None and not ergebnis.fehler

    # Der fertige Kurs in den Warenausgang - dort gibt Daniel frei. Ohne
    # diesen Schritt war die Lern-Strasse eine Sackgasse: der Kurs lag in
    # der Ablage und niemand erfuhr davon.
    ausgang = ""
    if gut:
        c = ergebnis.curriculum
        ausgang = warenausgang_lern.einstellen(
            auftrag_id=kennung, titel=(c.titel if c else ergebnis.auftrag.thema),
            stueck=ergebnis.kurs,
            sekunden=float(ergebnis.auftrag.minuten) * 60.0,
            zweck="lernprogramm", kosten=0.0,
            befund_text="%d Level, %d Minuten"
                        % (len(c.level) if c else 0, ergebnis.auftrag.minuten),
            trocken=ergebnis.auftrag.trocken)
        if ausgang:
            meldung.melde("warenausgang",
                          "Auftrag %s liegt als %s im Warenausgang und wartet "
                          "auf deine Freigabe." % (kennung, ausgang),
                          {"auftrag": kennung, "warenausgang": ausgang})

    hub.zustand_melden(
        kennung, "fertig" if gut else "fehler",
        ergebnis.fehler or ("Der Kurs liegt bereit: %s" % ergebnis.kurs),
        fortschritt=1.0, warenausgang=ausgang)


def einen_abarbeiten() -> bool:
    """Einen Auftrag entwerfen. False heisst: keiner da."""
    genommen = naechster_auftrag()
    if genommen is None:
        return False
    auftrag, kennung = genommen
    kennung = kennung or auftrag.id

    meldung.melde("angenommen", "Auftrag %s: %s" % (kennung, auftrag.thema),
                  {"auftrag": kennung})
    hub.zustand_melden(kennung, "laeuft",
                       "Die Lern-Werkstatt entwirft das Curriculum.",
                       fortschritt=0.3)
    try:
        # produzieren() entscheidet selbst, ob die Abnahme dazwischen muss:
        # im Trockenlauf und mit abgeschalteter Abnahme laeuft es durch,
        # sonst haelt es beim Curriculum an. Diese Regel steht in
        # strasse.py und wird hier nicht ein zweites Mal geschrieben -
        # zwei Stellen, die dasselbe wissen, laufen auseinander.
        ergebnis = strasse.produzieren(auftrag)
    except Exception as fehler:                        # noqa: BLE001
        import traceback
        meldung.melde("fehler", "Auftrag %s abgebrochen: %s"
                      % (kennung, fehler),
                      {"auftrag": kennung,
                       "spur": traceback.format_exc()[-2000:]})
        hub.zustand_melden(kennung, "fehler", str(fehler)[:400])
        return True

    if ergebnis.zustand == Zustand.FEHLER:
        meldung.melde("fehler", "Auftrag %s: %s" % (kennung, ergebnis.fehler),
                      {"auftrag": kennung})
        hub.zustand_melden(kennung, "fehler", ergebnis.fehler[:400])
        return True

    if ergebnis.zustand == Zustand.WARTET_AUF_ABNAHME:
        _parken(ergebnis, kennung)
        meldung.melde(
            "abnahme_noetig", "Curriculum liegt vor: %s" % auftrag.thema,
            {"auftrag": kennung,
             "datei": str(e.WERKSTATT / auftrag.id / "curriculum.md"),
             "level": len(ergebnis.curriculum.level) if ergebnis.curriculum else 0})
        hub.zustand_melden(
            kennung, "wartet_auf_abnahme",
            "Das Curriculum liegt vor und wartet auf deine Abnahme. Erst "
            "danach wird gebaut - vorher kostet nichts.", fortschritt=0.5)
        return True

    _melden_fertig(ergebnis, kennung)
    return True


# ------------------------------------------------------------------ Aufruf

def _stand() -> int:
    WARTEBANK.mkdir(parents=True, exist_ok=True)
    print("Lern-Werkstatt%s" % (" (Trockenlauf)" if e.TROCKEN else ""))
    print("  Eingang:   %s" % EINGANG)
    print("  Wartebank: %s" % WARTEBANK)
    print("  Ausgabe:   %s" % e.AUSGABE)
    fehlt = e.fehlende_schluessel()
    if fehlt:
        print("  Es fehlt:  %s" % ", ".join(fehlt))
    liegt = _liegt_an()
    print("  Es liegen an:        %d Auftraege" % len(liegt))
    for datei in liegt:
        print("     %s" % datei.name)
    wartet = sorted(WARTEBANK.glob("*.json"))
    print("  Wartet auf Abnahme:  %d" % len(wartet))
    for datei in wartet:
        aufgenommen = _aufnehmen(datei)
        kennung = aufgenommen[1] if aufgenommen else datei.stem
        wahl, _ = _entscheidung(kennung)
        print("     %-24s %s" % (kennung, wahl or "noch keine Antwort"))
    return 0


def _einmal() -> int:
    """Alles abarbeiten, was jetzt anliegt - dann Schluss.

    Erst die Wartebank: was abgenommen ist, wird zu Ende gebaut. Danach das
    Neue. Andersherum bliebe ein abgenommenes Curriculum liegen, obwohl
    Daniel darauf wartet.
    """
    getan = wartende_pruefen()
    while _laeuft and einen_abarbeiten():
        getan += 1
    print("%d Auftrag/Auftraege bearbeitet." % getan)
    return 0


def _takt() -> int:
    fehlt = e.fehlende_schluessel()
    meldung.melde("start", "Lern-Werkstatt bereit"
                  + (", Trockenlauf" if e.TROCKEN else "")
                  + ((", es fehlt: " + ", ".join(fehlt)) if fehlt else ""))
    while _laeuft:
        getan = wartende_pruefen()
        while _laeuft and einen_abarbeiten():
            getan += 1
        if not getan:
            time.sleep(e.TAKT_SEKUNDEN)
    meldung.melde("halt", "Lern-Werkstatt angehalten")
    return 0


def main(argumente: list[str] | None = None) -> int:
    signal.signal(signal.SIGTERM, _halt)
    signal.signal(signal.SIGINT, _halt)

    argumente = sys.argv[1:] if argumente is None else argumente
    befehl = (argumente[0] if argumente else "einmal").lower()

    if befehl == "stand":
        return _stand()
    if befehl == "einmal":
        return _einmal()
    if befehl == "takt":
        return _takt()

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
