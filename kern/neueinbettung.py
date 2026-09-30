# -*- coding: utf-8 -*-
"""Die Vektorsaeule auf den neuen Stand des Regals bringen.

Warum das noetig ist: die Bedeutungssuche antwortet aus der Vektorsaeule, nicht
aus den Dateien. Aendert sich der Kopf einer Notiz - Titel, Quelle, `erfasst_von` -,
merkt die Saeule davon nichts. Sie liefert dann weiter den alten Titel in der
Trefferliste, und der neue Text im ersten Haeppchen ist nicht eingebettet.

Was hier passiert, Notiz fuer Notiz:

    1 die Haeppchen dieser Notiz aus dem Regal 'wissen' entfernen
      (gefunden ueber das Kennzeichen `quelle` - das ist der Dateiname. Nicht
       ueber `datei`: dort steht ein abgeschnittener Pfad, der nie trifft, und
       nicht ueber die Kennung: die haengt am Text und aendert sich mit ihm)
    2 die Notiz neu zerlegen und einbetten, mit dem Kopf von heute

Danach werden die Waisen entfernt: Haeppchen, deren Notiz es nicht mehr gibt.
Am 13.09. sind 287 Notizen ohne KI-Bezug geloescht worden; ihre Haeppchen lagen
danach noch im Regal und waeren weiter als Treffer gekommen.

Andere Regale (atome, bilder, recht, erfahrungen ...) werden nicht angefasst.

Kosten: die Einbettung laeuft ueber text-embedding-3-small. Gerechnet am Bestand
vom 13.09.: 6.381 Notizen, rund 20 Millionen Zeichen, das sind bei 3,5 Zeichen je
Zeichenkette rund 5,7 Millionen Zeichenketten - bei 0,02 US-Dollar je Million
also etwa 0,11 US-Dollar. Der genaue Betrag wird gebucht.

    python neueinbettung.py --trocken     nur zaehlen
    python neueinbettung.py --nur 20      an zwanzig vorfuehren
    python neueinbettung.py               alles
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

KERN = Path(__file__).resolve().parent
UNIVERSE = KERN.parent
GEHIRN = UNIVERSE.parent / "mein_ki_gehirn"
WISSEN = GEHIRN / "wissen"
CHROMA = GEHIRN / "chroma"

sys.path.insert(0, str(KERN))
import vektor  # noqa: E402

KOPF = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _laden(name: str, datei: Path):
    fertig = sys.modules.get(name)
    if fertig is not None:
        return fertig
    b = importlib.util.spec_from_file_location(name, datei)
    m = importlib.util.module_from_spec(b)
    sys.modules[name] = m
    b.loader.exec_module(m)
    return m


def _felder(text: str) -> dict:
    treffer = KOPF.match(text)
    if not treffer:
        return {}
    felder = {}
    for zeile in treffer.group(1).splitlines():
        if ":" in zeile and not zeile.startswith((" ", "-", "\t")):
            name, _, wert = zeile.partition(":")
            felder[name.strip()] = wert.strip().strip('"').strip("'")
    return felder


def _kennzeichen(datei: Path, felder: dict) -> dict:
    return {"titel": felder.get("title", datei.stem),
            # Der Dateiname, nicht der Pfad: `datei` trug bis zum 13.09. einen
            # abgeschnittenen Pfad und war damit als Schluessel unbrauchbar.
            "datei": datei.name,
            "typ": felder.get("typ", "tech-wissen"),
            "thema": felder.get("thema", ""),
            "erfasst_von": felder.get("erfasst_von", ""),
            "quelle": datei.name,
            "art": "wissen"}


def ein_bund(fach, dateien: list, trocken: bool) -> tuple[int, int]:
    """Ein Bund Notizen in einem Zug: erst alle alten Haeppchen weg, dann alle
    neuen in einer gebuendelten Einbettung.

    Warum gebuendelt: eine Anfrage je Notiz waere eine Netzrunde je Notiz.
    Gemessen am 13.09.: so kamen 250 Notizen in 35 Minuten durch - fuer 6.381
    waeren das fuenfzehn Stunden. `aufnehmen_viele` bettet die Stuecke aus
    hundert Dateien gemeinsam ein.
    """
    posten = []
    alt = 0
    for datei in dateien:
        try:
            text = datei.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        try:
            vorhanden = fach.get(where={"quelle": datei.name}, include=[])
            alt += len(vorhanden.get("ids") or [])
        except Exception:
            pass
        posten.append((text, _kennzeichen(datei, _felder(text)), datei.name))

    if trocken:
        return alt, sum(len(vektor.haeppchen(text)) for text, _k, _q in posten)

    for datei in dateien:
        try:
            fach.delete(where={"quelle": datei.name})
        except Exception:
            pass
    neu = vektor.aufnehmen_viele("wissen", CHROMA, posten)
    return alt, neu


def _melden(notizen: int, entfernt: int, neu: int, vorher: int, nachher: int) -> None:
    try:
        m = _laden("kern_melden", KERN / "melden.py")
        verloren = vorher - nachher
        m.melde("neueinbettung",
                "Vektorsaeule neu eingebettet: %d Notizen, %d Haeppchen entfernt, "
                "%d neu. Vorher %d, nachher %d.%s"
                % (notizen, entfernt, neu, vorher, nachher,
                   "" if verloren <= 0 else
                   "\nACHTUNG: %d Haeppchen weniger als vorher - nachsehen." % verloren),
                art="warnung" if (vorher - nachher) > 0 else "info")
    except Exception:
        pass


def _main(argumente: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    z = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    z.add_argument("--trocken", action="store_true")
    z.add_argument("--nur", type=int, default=0)
    w = z.parse_args(argumente)

    fach = vektor.regal("wissen", CHROMA)
    vorher = fach.count()
    dateien = sorted(WISSEN.rglob("*.md"))
    if w.nur:
        dateien = dateien[:w.nur]
    print("%s %d Notizen, Regal 'wissen' hat %d Haeppchen"
          % ("TROCKEN:" if w.trocken else "Neu einbetten:", len(dateien), vorher))

    # Hundert Notizen je Bund: das sind rund 300 Haeppchen, die die Einbettung
    # in zwei bis drei Anfragen erledigt. Groessere Buendel bringen kaum noch
    # etwas und machen einen Abbruch teurer.
    BUND = 100
    entfernt = neu = 0
    for anfang in range(0, len(dateien), BUND):
        teil = dateien[anfang:anfang + BUND]
        try:
            a, n = ein_bund(fach, teil, w.trocken)
        except Exception as fehler:
            print("  Bund ab %d: %s" % (anfang, fehler), flush=True)
            continue
        entfernt += a
        neu += n
        print("  %d von %d ... (%d entfernt, %d neu)"
              % (min(anfang + BUND, len(dateien)), len(dateien), entfernt, neu), flush=True)

    # Waisen: Haeppchen, deren Notiz es nicht mehr gibt.
    waisen = 0
    if not w.trocken and not w.nur:
        namen = {d.name for d in WISSEN.rglob("*.md")}
        stapel = 5000
        weg = []
        holen = fach.get(include=["metadatas"], limit=stapel)
        kennungen, metas = holen.get("ids") or [], holen.get("metadatas") or []
        # Chroma gibt ohne Blaettern nur einen Ausschnitt; deshalb in Runden.
        gesehen = 0
        while kennungen:
            for k, m in zip(kennungen, metas):
                if str(m.get("quelle", "")) not in namen:
                    weg.append(k)
            gesehen += len(kennungen)
            if gesehen >= fach.count():
                break
            holen = fach.get(include=["metadatas"], limit=stapel, offset=gesehen)
            kennungen, metas = holen.get("ids") or [], holen.get("metadatas") or []
        if weg:
            for i in range(0, len(weg), 1000):
                fach.delete(ids=weg[i:i + 1000])
            waisen = len(weg)
            print("Waisen entfernt: %d (Notiz gibt es nicht mehr)" % waisen)

    nachher = fach.count()
    print("\nentfernt %d, neu %d" % (entfernt, neu))
    print("Regal 'wissen': vorher %d, nachher %d" % (vorher, nachher))
    if not w.trocken and not w.nur:
        # Die Gegenprobe: jede verbliebene Notiz muss mindestens ein Haeppchen
        # haben. Weniger Haeppchen als vorher ist hier richtig - die Waisen der
        # geloeschten Notizen sind weg -, aber eine Notiz ohne Haeppchen waere
        # aus der Suche verschwunden.
        ohne = [d.name for d in WISSEN.rglob("*.md")
                if not (fach.get(where={"quelle": d.name}, include=[], limit=1)
                        .get("ids"))]
        if ohne:
            print("ACHTUNG: %d Notizen ohne Haeppchen, z.B. %s"
                  % (len(ohne), ", ".join(ohne[:3])))
        else:
            print("Gegenprobe: jede der %d Notizen hat Haeppchen."
                  % len(list(WISSEN.rglob("*.md"))))
        _melden(len(dateien), entfernt, neu, vorher, nachher)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
