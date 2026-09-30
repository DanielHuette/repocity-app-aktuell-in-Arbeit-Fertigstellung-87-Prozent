# -*- coding: utf-8 -*-
"""Der Setzer - die PDF-Strasse (Daniels 105).

    python main.py einmal    was im Eingang liegt, abarbeiten, dann Schluss
    python main.py stand     was gerade anliegt
    python main.py probe     ein Probedokument setzen, trocken, ohne Auftrag

Woher die Auftraege kommen: aus universe/zustand/setzer_eingang. Dort legt
sie der Sekretaer als JSON ab (sekretaer/verteiler.py) und startet danach
diese Werkstatt mit "einmal". Das ist der einzige Weg herein.

Der Weg eines Auftrags:

    Auftrag ─► Gliedern (Modell oder trocken) ─► Setzen (reportlab)
            ─► Abnahme ─► Warenausgang ─► Rueckmeldung an den Hub

Gebaut nach dem Muster der Musik-Werkstatt, damit es einen Weg gibt und
nicht zwei.
"""
from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
sys.path.insert(0, str(HIER))


def _kern_baustein(name: str):
    """Einen Kern-Baustein ueber seinen Pfad laden, nicht ueber den Suchpfad
    (main.py gibt es dreizehnmal im Universe)."""
    import importlib.util
    stelle = importlib.util.spec_from_file_location(
        "kern_%s_fuer_setzer" % name, KERN / (name + ".py"))
    modul = importlib.util.module_from_spec(stelle)
    stelle.loader.exec_module(modul)
    return modul


_kern_baustein("umgebung").laden()



def _eigen(name: str):
    """Einen eigenen Baustein ueber seinen Pfad laden (einstellungen.py gibt es zwoelfmal)."""
    import importlib.util
    stelle = importlib.util.spec_from_file_location("setzer_" + name, HIER / (name + ".py"))
    modul = importlib.util.module_from_spec(stelle)
    sys.modules[stelle.name] = modul   # dataclasses brauchen das Modul dort
    stelle.loader.exec_module(modul)
    return modul


e = _eigen("einstellungen")
inhalt = _eigen("inhalt")
meldung = _eigen("meldung")
pruefung = _eigen("pruefung")
satz = _eigen("satz")
warenausgang_setzer = _eigen("warenausgang_setzer")

hub = _kern_baustein("hub")
kennung_modul = _kern_baustein("kennung")

_laeuft = True


def _halt(*_):
    global _laeuft
    _laeuft = False


def _liegt_an() -> list[Path]:
    e.EINGANG.mkdir(parents=True, exist_ok=True)
    return sorted(e.EINGANG.glob("*.json"))


def _sauber(text: str) -> str:
    erlaubt = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    klein = (text.lower().replace(" ", "-").replace("ä", "ae").replace("ö", "oe")
             .replace("ü", "ue").replace("ß", "ss"))
    return "".join(z for z in klein if z in erlaubt)[:40] or "dokument"


def setzen(auftrag_id: str, titel: str, text: str, kit: str = "", stoff: dict | None = None,
           trocken: bool = True) -> dict:
    """Ein Dokument durch die Strasse schicken. Gibt den Befund als dict zurueck.

    Wirft nie - der Aufrufer sieht am Feld 'fehler', was war."""
    ordner = e.WERKSTATT / kennung_modul.sauber(auftrag_id)
    ordner.mkdir(parents=True, exist_ok=True)
    aus = {"auftrag": auftrag_id, "weg": "", "pdf": "", "seiten": 0, "woerter": 0,
           "bestanden": False, "gruende": [], "fehler": ""}
    try:
        doku, weg = inhalt.gliedern(titel, text, stoff, trocken=trocken, auftrag_id=auftrag_id)
        aus["weg"] = weg
        pdf = satz.setzen(doku, ordner / "dokument.pdf", kit=kit, auftrag_id=auftrag_id)
        befund = pruefung.pruefe(doku, pdf)
        aus.update(seiten=befund.seiten, woerter=befund.woerter,
                   bestanden=befund.bestanden, gruende=befund.gruende)
        if befund.bestanden:
            e.AUSGABE.mkdir(parents=True, exist_ok=True)
            endgueltig = e.AUSGABE / ("%s_%s.pdf" % (kennung_modul.sauber(auftrag_id), _sauber(titel)))
            endgueltig.write_bytes(pdf.read_bytes())
            aus["pdf"] = str(endgueltig)
    except Exception as fehler:                            # noqa: BLE001
        aus["fehler"] = str(fehler)
    return aus


def naechster_auftrag() -> tuple[dict, str] | None:
    for datei in _liegt_an():
        try:
            satz_ = json.loads(datei.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            datei.replace(datei.with_suffix(".json.kaputt"))
            meldung.melde("fehler", "Auftrag %s war nicht lesbar und liegt jetzt als .kaputt daneben." % datei.name)
            continue
        datei.replace(datei.with_suffix(".json.genommen"))
        text = (satz_.get("text") or satz_.get("thema") or "").strip()
        if not text:
            meldung.melde("fehler", "Auftrag %s hat keinen Text - ohne den gibt es kein Dokument." % datei.name)
            continue
        return satz_, str(satz_.get("id") or "")
    return None


def einen_abarbeiten() -> bool:
    genommen = naechster_auftrag()
    if genommen is None:
        return False
    satz_, kennung = genommen
    text = (satz_.get("text") or satz_.get("thema") or "").strip()
    titel = (satz_.get("titel") or text.splitlines()[0]).strip()[:120]
    trocken = bool(satz_.get("trocken", e.TROCKEN))
    kit = str(satz_.get("kit") or "")
    stoff = satz_.get("stoff") if isinstance(satz_.get("stoff"), dict) else {}
    auftrag_id = kennung or kennung_modul.sauber(titel)

    meldung.melde("angenommen", "Auftrag %s: %s" % (auftrag_id, titel), {"auftrag": auftrag_id})
    if kennung:
        hub.zustand_melden(kennung, "laeuft", "Der Setzer arbeitet.", fortschritt=0.5)

    aus = setzen(auftrag_id, titel, text, kit=kit, stoff=stoff, trocken=trocken)
    gut = aus["bestanden"] and aus["pdf"] and not aus["fehler"]

    ausgang = ""
    if gut:
        ausgang = warenausgang_setzer.einstellen(
            auftrag_id=auftrag_id, titel=titel, pdf=Path(aus["pdf"]),
            seiten=aus["seiten"], woerter=aus["woerter"], trocken=trocken)
        if ausgang:
            meldung.melde("warenausgang",
                          "Auftrag %s liegt als %s im Warenausgang und wartet auf deine Freigabe." % (auftrag_id, ausgang),
                          {"auftrag": auftrag_id, "warenausgang": ausgang})
    else:
        meldung.melde("fehler", "Auftrag %s: %s" % (auftrag_id, aus["fehler"] or "; ".join(aus["gruende"])),
                      {"auftrag": auftrag_id})

    if kennung:
        hub.zustand_melden(
            kennung, "fertig" if gut else "fehler",
            (aus["fehler"] or "; ".join(aus["gruende"])) if not gut
            else "Das Dokument liegt bereit: %s (%d Seiten)" % (aus["pdf"], aus["seiten"]),
            fortschritt=1.0, warenausgang=ausgang)
    return True


def _stand() -> int:
    print("Der Setzer (PDF-Strasse)")
    print("  Trocken:   %s" % ("ja" if e.TROCKEN else "nein"))
    print("  Eingang:   %s" % e.EINGANG)
    print("  Ausgabe:   %s" % e.AUSGABE)
    liegt = _liegt_an()
    print("  Es liegen an: %d Auftraege" % len(liegt))
    for datei in liegt:
        print("     %s" % datei.name)
    return 0


def _einmal() -> int:
    getan = 0
    while _laeuft and einen_abarbeiten():
        getan += 1
    print("%d Auftrag/Auftraege abgearbeitet." % getan)
    return 0


def _probe() -> int:
    aus = setzen("probe", "Probedokument des Setzers",
                 "# Worum es geht\n\nDer Setzer macht aus einem Auftrag ein Dokument. "
                 "Dieser Absatz ist der Beweis, dass die Strasse trocken laeuft.\n\n"
                 "# Was er prueft\n\nSeitenzahl, Titel, Groesse - vor der Vorlage, nicht danach.",
                 trocken=True)
    print(json.dumps(aus, ensure_ascii=False, indent=1))
    return 0 if aus["bestanden"] else 1


def main(argumente: list[str] | None = None) -> int:
    signal.signal(signal.SIGTERM, _halt)
    signal.signal(signal.SIGINT, _halt)
    argumente = sys.argv[1:] if argumente is None else argumente
    befehl = (argumente[0] if argumente else "einmal").lower()
    if befehl == "stand":
        return _stand()
    if befehl == "einmal":
        return _einmal()
    if befehl == "probe":
        return _probe()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
