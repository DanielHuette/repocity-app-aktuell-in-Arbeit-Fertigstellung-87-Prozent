# -*- coding: utf-8 -*-
"""Der Bildschirmgestalter - Anmelde- und Sperrbildschirme, Bildschirmschoner
fuer PC und Handy, still und bewegt (Daniels 102).

    python main.py einmal    was im Eingang liegt, abarbeiten, dann Schluss
    python main.py stand     was gerade anliegt
    python main.py probe     das RepoCity-Exemplar bauen, trocken, beide Formate

Woher die Auftraege kommen: aus universe/zustand/bildschirm_eingang, abgelegt
vom Sekretaer. Ein Auftrag nennt Motiv, Kit und Geraet (pc, handy oder beide)
und ob das RepoCity-Logo darauf soll (das "Brand-Exemplar").

Der Weg eines Auftrags:

    Auftrag ─► je Format ein Standbild (fal.ai oder gerechnet)
            ─► einlagern (Regel B) ─► bewegter Schoner (ffmpeg)
            ─► Abnahme (Masse, Datei) ─► Warenausgang ─► Rueckmeldung an den Hub
"""
from __future__ import annotations

import json
import random
import signal
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
sys.path.insert(0, str(HIER))


def _kern_baustein(name: str):
    import importlib.util
    stelle = importlib.util.spec_from_file_location(
        "kern_%s_fuer_bildschirm" % name, KERN / (name + ".py"))
    modul = importlib.util.module_from_spec(stelle)
    stelle.loader.exec_module(modul)
    return modul


_kern_baustein("umgebung").laden()



def _eigen(name: str):
    """Einen eigenen Baustein ueber seinen Pfad laden (einstellungen.py gibt es zwoelfmal)."""
    import importlib.util
    stelle = importlib.util.spec_from_file_location("bildschirm_" + name, HIER / (name + ".py"))
    modul = importlib.util.module_from_spec(stelle)
    sys.modules[stelle.name] = modul   # dataclasses brauchen das Modul dort
    stelle.loader.exec_module(modul)
    return modul


e = _eigen("einstellungen")
bewegung = _eigen("bewegung")
meldung = _eigen("meldung")
motiv = _eigen("motiv")
warenausgang_bildschirm = _eigen("warenausgang_bildschirm")

hub = _kern_baustein("hub")
kennung_modul = _kern_baustein("kennung")

_laeuft = True


def _halt(*_):
    global _laeuft
    _laeuft = False


def _liegt_an() -> list[Path]:
    e.EINGANG.mkdir(parents=True, exist_ok=True)
    return sorted(e.EINGANG.glob("*.json"))


def gestalten(auftrag_id: str, text: str, kit: str = "gipfelsturm", geraete: list[str] | None = None,
              mit_logo: bool = False, trocken: bool = True, startwert: int | None = None) -> dict:
    """Ein Auftrag durch die Strasse. Gibt je Format Standbild, Film und Befund zurueck."""
    geraete = [g for g in (geraete or ["pc", "handy"]) if g in e.FORMATE] or ["pc", "handy"]
    startwert = startwert if startwert is not None else random.randint(1, 2_000_000_000)
    ordner = e.WERKSTATT / kennung_modul.sauber(auftrag_id)
    ordner.mkdir(parents=True, exist_ok=True)
    e.AUSGABE.mkdir(parents=True, exist_ok=True)
    aus = {"auftrag": auftrag_id, "weg": "trocken" if trocken else "fal.ai", "stuecke": [],
           "kosten_usd": 0.0, "bestanden": False, "gruende": [], "fehler": ""}
    try:
        for geraet in geraete:
            breite, hoehe = e.FORMATE[geraet]
            name = "%s-%s-%s" % (kennung_modul.sauber(auftrag_id), geraet, startwert)
            roh = ordner / (name + "-roh.png")
            if trocken:
                bild, preis = motiv.gerechnet(breite, hoehe, kit, startwert), 0.0
            else:
                bild, preis = motiv.echt(breite, hoehe, motiv.prompt(text, kit, geraet), startwert, roh)
            if mit_logo:
                bild = motiv.mit_logo(bild)
            standbild = e.AUSGABE / (name + ".png")
            bild.save(standbild, "PNG")
            motiv.einlagern(standbild, {"kit": kit, "geraet": geraet,
                                        "modell": "gerechnet" if trocken else e.MODELL,
                                        "startwert": startwert, "groesse": "%dx%d" % (breite, hoehe),
                                        "kosten_usd": preis, "weg": aus["weg"], "auftrag": text})
            film = None
            fehler_film = ""
            try:
                film = bewegung.film(standbild, e.AUSGABE / (name + ".mp4"))
            except Exception as f:                         # noqa: BLE001
                fehler_film = str(f)
            gruende = []
            if bild.size != (breite, hoehe):
                gruende.append("%s: Bild hat %dx%d statt %dx%d" % (geraet, *bild.size, breite, hoehe))
            if standbild.stat().st_size < 20_000:
                gruende.append("%s: Standbild ist verdaechtig klein" % geraet)
            if e.ffmpeg() and film is None:
                gruende.append("%s: kein bewegter Schoner - %s" % (geraet, fehler_film or "ffmpeg lief nicht"))
            aus["stuecke"].append({"geraet": geraet, "standbild": str(standbild),
                                   "film": str(film) if film else "", "groesse": "%dx%d" % (breite, hoehe),
                                   "gruende": gruende})
            aus["kosten_usd"] += preis
            aus["gruende"] += gruende
        aus["bestanden"] = not aus["gruende"] and bool(aus["stuecke"])
    except Exception as fehler:                            # noqa: BLE001
        aus["fehler"] = str(fehler)
    return aus


def naechster_auftrag() -> tuple[dict, str] | None:
    for datei in _liegt_an():
        try:
            satz = json.loads(datei.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            datei.replace(datei.with_suffix(".json.kaputt"))
            meldung.melde("fehler", "Auftrag %s war nicht lesbar und liegt jetzt als .kaputt daneben." % datei.name)
            continue
        datei.replace(datei.with_suffix(".json.genommen"))
        if not (satz.get("text") or satz.get("thema") or "").strip():
            meldung.melde("fehler", "Auftrag %s nennt kein Motiv." % datei.name)
            continue
        return satz, str(satz.get("id") or "")
    return None


def einen_abarbeiten() -> bool:
    genommen = naechster_auftrag()
    if genommen is None:
        return False
    satz, kennung = genommen
    text = (satz.get("text") or satz.get("thema") or "").strip()
    auftrag_id = kennung or kennung_modul.sauber(text[:30])
    geraete = satz.get("geraete") or ([satz["geraet"]] if satz.get("geraet") else None)
    trocken = bool(satz.get("trocken", e.TROCKEN))

    meldung.melde("angenommen", "Auftrag %s: %s" % (auftrag_id, text[:80]), {"auftrag": auftrag_id})
    if kennung:
        hub.zustand_melden(kennung, "laeuft", "Der Bildschirmgestalter arbeitet.", fortschritt=0.5)

    aus = gestalten(auftrag_id, text, kit=str(satz.get("kit") or "gipfelsturm"), geraete=geraete,
                    mit_logo=bool(satz.get("mit_logo") or satz.get("brand")), trocken=trocken)
    gut = aus["bestanden"] and not aus["fehler"]
    ausgang = ""
    if gut:
        ausgang = warenausgang_bildschirm.einstellen(auftrag_id, text[:80], aus["stuecke"], aus["kosten_usd"], trocken)
        if ausgang:
            meldung.melde("warenausgang", "Auftrag %s liegt als %s im Warenausgang und wartet auf deine Freigabe."
                          % (auftrag_id, ausgang), {"auftrag": auftrag_id, "warenausgang": ausgang})
    else:
        meldung.melde("fehler", "Auftrag %s: %s" % (auftrag_id, aus["fehler"] or "; ".join(aus["gruende"])),
                      {"auftrag": auftrag_id})
    if kennung:
        hub.zustand_melden(kennung, "fertig" if gut else "fehler",
                           (aus["fehler"] or "; ".join(aus["gruende"])) if not gut
                           else "%d Stuecke liegen bereit" % len(aus["stuecke"]),
                           fortschritt=1.0, warenausgang=ausgang)
    return True


def _stand() -> int:
    print("Der Bildschirmgestalter")
    print("  Trocken:   %s" % ("ja" if e.TROCKEN else "nein"))
    print("  ffmpeg:    %s" % (e.ffmpeg() or "fehlt - kein bewegter Schoner"))
    print("  Eingang:   %s" % e.EINGANG)
    print("  Ausgabe:   %s" % e.AUSGABE)
    liegt = _liegt_an()
    print("  Es liegen an: %d Auftraege" % len(liegt))
    return 0


def _einmal() -> int:
    getan = 0
    while _laeuft and einen_abarbeiten():
        getan += 1
    print("%d Auftrag/Auftraege abgearbeitet." % getan)
    return 0


def _probe() -> int:
    aus = gestalten("probe-repocity", "RepoCity-Exemplar: Sonne ueber den Wolken", kit="gipfelsturm",
                    mit_logo=True, trocken=True, startwert=308574231)
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
