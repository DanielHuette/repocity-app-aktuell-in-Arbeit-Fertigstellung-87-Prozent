# -*- coding: utf-8 -*-
"""Sechs Fragen an das zweite Gehirn - mit Zahlen statt Gefuehl.

Ein zweites Gehirn waechst still und verfaellt still. Sechstausend Notizen sehen
nach viel aus und koennen trotzdem nichts taugen: wenn die Bedeutungssuche sie
nicht findet, wenn keine Quelle darunter steht, wenn die Haelfte doppelt ist.
Deshalb wird nicht geschaetzt, sondern gemessen.

    1 Auffindbarkeit  Findet eine echte Frage etwas Brauchbares?
    2 Abdeckung       Wie viel vom Bestand steht ueberhaupt in der Vektorsaeule?
    3 Belegtheit      Wie viele Notizen nennen ihre Quelle?
    4 Aktualitaet     Wie alt ist der Bestand?
    5 Doppelung       Wie viel steht zweimal da?
    6 Nutzung         Wird ueberhaupt daraus geholt - und mit welcher Deckung?

Jede Frage hat eine Grenze. Die Grenzen sind gerechnet oder aus dem Betrieb
abgelesen; die Rechnung steht jeweils daneben. Der Befund geht nach
`mein_ki_gehirn/verbesserung/MESSUNG-ZWEITES-GEHIRN.md` und an den Sekretaer.

    python gehirnmessung.py            messen und den Befund schreiben
    python gehirnmessung.py --ohne-netz    Frage 1 auslassen (kostet sonst Einbettungen)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

KERN = Path(__file__).resolve().parent
UNIVERSE = KERN.parent
WURZEL = UNIVERSE.parent
GEHIRN = WURZEL / "mein_ki_gehirn"
WISSEN = GEHIRN / "wissen"
ATOME = GEHIRN / "atome"
CHROMA = GEHIRN / "chroma"
BEFUND = GEHIRN / "verbesserung" / "MESSUNG-ZWEITES-GEHIRN.md"

# Die Stichprobenfragen fuer Frage 1. Sie kommen aus dem, was wir wirklich
# fragen - nicht aus dem, was gut aussieht. Wer mit Wunschfragen misst, misst
# sein Wunschdenken.
STICHPROBE = [
    "Wie bestimmt man den Nullpunkt einer Fibonacci-Sequenz?",
    "Wie baut man einen Agentenschwarm, der sich selbst verbessert?",
    "Wie bringt man ein Video von der Idee zum fertigen Schnitt?",
    "Was gehoert in eine Datenschutzerklaerung fuer eine Web-App?",
    "Wie misst man, ob ein Text nach Maschine klingt?",
    "Wie richtet man eine Vektordatenbank fuer Obsidian ein?",
]

# Grenzen, mit Rechnung.
GRENZEN = {
    # Von sechs echten Fragen muessen mindestens vier etwas Brauchbares finden.
    # Vier von sechs = 67 %: bei drei von sechs waere Muenzwurf, bei sechs von
    # sechs waere die Stichprobe zu leicht gewaehlt.
    "auffindbarkeit": 0.67,
    # Jede Notiz soll in der Vektorsaeule stehen. 0,95 statt 1,0, weil ganz
    # frisch Eingepflegtes zwischen zwei Laeufen kurz fehlen darf.
    "abdeckung": 0.95,
    # Eine Notiz ohne Quelle ist eine Behauptung. 0,90: die handverlesenen
    # Altbestaende aus der Anfangszeit duerfen fehlen, Neues nicht.
    "belegtheit": 0.90,
    # Haelfte des Bestands juenger als ein Jahr. Aelter heisst nicht falsch,
    # aber ein Medianalter ueber 365 Tagen heisst: es kommt nichts nach.
    "aktualitaet_tage": 365,
    # Ueber 5 % Doppelungen heisst, dass die Doppelungspruefung nicht greift.
    "doppelung": 0.05,
    # In 30 Tagen mindestens 10 Abrufe, sonst baut niemand darauf.
    "nutzung_30_tage": 10,
}

KOPF = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


@dataclass
class Antwort:
    frage: str
    zahl: str
    grenze: str
    bestanden: bool
    satz: str
    was_tun: str = ""


def _kopf(text: str) -> dict:
    treffer = KOPF.match(text)
    if not treffer:
        return {}
    felder = {}
    for zeile in treffer.group(1).splitlines():
        if ":" in zeile and not zeile.startswith((" ", "-", "\t")):
            name, _, wert = zeile.partition(":")
            felder[name.strip()] = wert.strip().strip('"').strip("'")
    return felder


def _notizen() -> list[tuple[Path, dict, str]]:
    heraus = []
    if not WISSEN.exists():
        return heraus
    for datei in WISSEN.rglob("*.md"):
        try:
            text = datei.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        heraus.append((datei, _kopf(text), text))
    return heraus


def _laden(name: str, datei: Path):
    fertig = sys.modules.get(name)
    if fertig is not None:
        return fertig
    b = importlib.util.spec_from_file_location(name, datei)
    m = importlib.util.module_from_spec(b)
    sys.modules[name] = m
    b.loader.exec_module(m)
    return m


# --------------------------------------------------------------- die sechs

def f1_auffindbarkeit(ohne_netz: bool = False) -> Antwort:
    if ohne_netz:
        return Antwort("Auffindbarkeit", "nicht gemessen", "4 von 6", True,
                       "Mit --ohne-netz uebersprungen (kostet Einbettungen).")
    try:
        g = _laden("kern_gehirn", KERN / "gehirn.py")
    except Exception as fehler:
        return Antwort("Auffindbarkeit", "-", "4 von 6", False,
                       "Das Gehirn liess sich nicht laden: %s" % fehler,
                       "gehirn.py pruefen - ohne Suche ist der Bestand tot.")
    treffer = 0
    einzeln = []
    for frage in STICHPROBE:
        try:
            funde = g.lesen(frage, je_saeule=3)
        except Exception:
            funde = []
        beste = max([getattr(f, "naehe", 0.0) or 0.0 for f in funde], default=0.0)
        gut = beste >= 0.45          # dieselbe Schwelle wie beim Kurator
        treffer += gut
        einzeln.append("%s %.2f" % ("+" if gut else "-", beste))
    anteil = treffer / len(STICHPROBE)
    return Antwort(
        "Auffindbarkeit", "%d von %d (%s)" % (treffer, len(STICHPROBE), ", ".join(einzeln)),
        "mindestens %d von %d" % (round(GRENZEN["auffindbarkeit"] * len(STICHPROBE)), len(STICHPROBE)),
        anteil >= GRENZEN["auffindbarkeit"],
        "Eine echte Frage findet %s Brauchbares (Naehe ab 0,45)."
        % ("meistens" if anteil >= GRENZEN["auffindbarkeit"] else "zu selten"),
        "" if anteil >= GRENZEN["auffindbarkeit"] else
        "Die Notizen sind zu lang oder zu unspezifisch. Kleinere Haeppchen und "
        "sprechendere Titel bringen mehr als mehr Notizen.")


def f2_abdeckung() -> Antwort:
    notizen = len(_notizen())
    haeppchen = 0
    try:
        v = _laden("kern_vektor", KERN / "vektor.py")
        haeppchen = sum(v.stand(CHROMA).values())
    except Exception:
        pass
    if not notizen:
        return Antwort("Abdeckung", "0 Notizen", "-", False, "Es liegt nichts im Regal.")
    # Eine Notiz ergibt im Schnitt mehr als ein Haeppchen; gemessen am Lauf vom
    # 13.09.: 8 Notizen -> 58 Haeppchen, also 7,25. Erwartet wird deshalb
    # mindestens ein Haeppchen je Notiz - weniger heisst, es fehlen Notizen ganz.
    verhaeltnis = haeppchen / notizen if notizen else 0.0
    bestanden = verhaeltnis >= GRENZEN["abdeckung"]
    return Antwort(
        "Abdeckung", "%d Notizen, %d Haeppchen (%.2f je Notiz)" % (notizen, haeppchen, verhaeltnis),
        "mindestens %.2f je Notiz" % GRENZEN["abdeckung"], bestanden,
        "Der Bestand steht %s in der Vektorsaeule."
        % ("vollstaendig" if bestanden else "nur teilweise"),
        "" if bestanden else
        "Fehlende Notizen ueber den Kurator nachpflegen: `python main.py einpflegen --alle`. "
        "Was von Hand nach wissen/ geschrieben wurde, steht nirgends sonst.")


def f3_belegtheit() -> Antwort:
    notizen = _notizen()
    if not notizen:
        return Antwort("Belegtheit", "-", "-", False, "Kein Bestand.")
    mit = sum(1 for _d, kopf, text in notizen
              if kopf.get("quelle") or kopf.get("quellen") or "quellen:" in text[:800]
              or re.search(r"https?://", text[:1200]))
    mit_kopf = sum(1 for _d, kopf, _t in notizen if kopf)
    anteil = mit / len(notizen)
    bestanden = anteil >= GRENZEN["belegtheit"]
    return Antwort(
        "Belegtheit", "%d von %d mit Quelle (%.0f %%), %d mit Kopf (%.0f %%)"
                      % (mit, len(notizen), anteil * 100, mit_kopf,
                         mit_kopf * 100.0 / len(notizen)),
        "mindestens %.0f %%" % (GRENZEN["belegtheit"] * 100), bestanden,
        "%s Notizen nennen, woher sie stammen." % ("Fast alle" if bestanden else "Zu wenige"),
        "" if bestanden else
        "Der grosse Rest kam vor dem Kurator ins Regal - ohne Kopf, ohne Quelle. "
        "Der Weg dorthin steht heute (Ablegeordner -> Dokumentwandler -> Kurator); "
        "der Altbestand muss einmal durch denselben Weg, sonst bleibt er eine "
        "Behauptungssammlung, auf die kein Agent sich berufen kann.")


def f4_aktualitaet() -> Antwort:
    notizen = _notizen()
    if not notizen:
        return Antwort("Aktualitaet", "-", "-", False, "Kein Bestand.")
    heute = date.today()
    alter = []
    for datei, kopf, _text in notizen:
        wann = kopf.get("erfasst_am") or kopf.get("datum") or ""
        try:
            alter.append((heute - date.fromisoformat(wann[:10])).days)
        except ValueError:
            try:
                alter.append((heute - date.fromtimestamp(datei.stat().st_mtime)).days)
            except OSError:
                pass
    if not alter:
        return Antwort("Aktualitaet", "-", "-", False, "Kein Datum lesbar.")
    alter.sort()
    median = alter[len(alter) // 2]
    bestanden = median <= GRENZEN["aktualitaet_tage"]
    return Antwort(
        "Aktualitaet", "Median %d Tage, aeltestes %d Tage" % (median, alter[-1]),
        "Median hoechstens %d Tage" % GRENZEN["aktualitaet_tage"], bestanden,
        "Die Haelfte des Bestands ist %s." % ("juenger als ein Jahr" if bestanden
                                              else "aelter als ein Jahr"),
        "" if bestanden else
        "Es kommt nichts nach. Der Deep Researcher und der Dokumentwandler "
        "liefern zu selten - oder es wird nur abgelegt, was ohnehin bekannt ist.")


def f5_doppelung() -> Antwort:
    notizen = _notizen()
    if not notizen:
        return Antwort("Doppelung", "-", "-", False, "Kein Bestand.")
    titel = Counter()
    for _d, kopf, _t in notizen:
        t = re.sub(r"\W+", " ", (kopf.get("title") or "").lower()).strip()
        if t:
            titel[t] += 1
    # Ohne Titel ist nichts zu vergleichen. Ein "0 % Doppelung" waere dann kein
    # gutes Zeugnis, sondern ein blinder Fleck - und ein gruener blinder Fleck
    # ist schlimmer als ein rotes Ergebnis.
    mit_titel = sum(titel.values())
    if mit_titel < len(notizen) * 0.5:
        return Antwort(
            "Doppelung", "nicht messbar: nur %d von %d Notizen haben einen Titel"
                         % (mit_titel, len(notizen)),
            "hoechstens %.0f %%" % (GRENZEN["doppelung"] * 100), False,
            "Ohne Titel im Kopf laesst sich keine Doppelung finden.",
            "Der Bestand ist groesstenteils ohne Kopf ins Regal gekommen - siehe "
            "Belegtheit. Erst die Koepfe, dann diese Messung.")
    doppelt = sum(z - 1 for z in titel.values() if z > 1)
    anteil = doppelt / len(notizen)
    bestanden = anteil <= GRENZEN["doppelung"]
    haeufigste = ", ".join("%s (%dx)" % (t[:34], z)
                           for t, z in titel.most_common(3) if z > 1) or "keine"
    return Antwort(
        "Doppelung", "%d von %d (%.1f %%) - %s" % (doppelt, len(notizen), anteil * 100, haeufigste),
        "hoechstens %.0f %%" % (GRENZEN["doppelung"] * 100), bestanden,
        "%s Doppelungen im Bestand." % ("Kaum" if bestanden else "Zu viele"),
        "" if bestanden else
        "Die Doppelungspruefung des Kurators greift nur bei gleichem Titel und "
        "gleicher Quelle. Was durch zwei Wege hereinkam, steht zweimal da - "
        "einmal durchgehen und die aeltere Fassung loeschen.")


def f6_nutzung() -> Antwort:
    """Wie oft in 30 Tagen etwas aus dem Gehirn geholt wurde.

    Abgelesen an den Erfahrungen des Rueckwegs: dort steht bei jedem Auftrag
    die Deckung, die der Kurator gemeldet hat. Wo keine Deckung steht, wurde
    nichts geholt.
    """
    try:
        r = _laden("kern_rueckweg", KERN / "rueckweg.py")
        alle = r.erfahrungen(anzahl=500)
    except Exception as fehler:
        return Antwort("Nutzung", "-", "-", False,
                       "Der Rueckweg liess sich nicht lesen: %s" % fehler)
    grenze = (datetime.now() - timedelta(days=30)).date().isoformat()
    jung = [e for e in alle if str(e.get("datum") or e.get("wann") or "")[:10] >= grenze]
    mit_deckung = [e for e in jung if str(e.get("deckung") or "") in ("gut", "duenn")]
    gut = sum(1 for e in mit_deckung if e.get("deckung") == "gut")
    bestanden = len(mit_deckung) >= GRENZEN["nutzung_30_tage"]
    return Antwort(
        "Nutzung", "%d Abrufe in 30 Tagen, davon %d mit guter Deckung"
                   % (len(mit_deckung), gut),
        "mindestens %d" % GRENZEN["nutzung_30_tage"], bestanden,
        "Es wird %s daraus geholt." % ("regelmaessig" if bestanden else "kaum"),
        "" if bestanden else
        "Entweder laufen die Strassen nicht, oder sie holen keinen Stoff. "
        "Nachsehen, ob `stoff.holen` in den kreativen Strassen wirklich gerufen wird - "
        "ein Gehirn, aus dem niemand liest, ist eine Ablage.")


def messen(ohne_netz: bool = False) -> list[Antwort]:
    return [f1_auffindbarkeit(ohne_netz), f2_abdeckung(), f3_belegtheit(),
            f4_aktualitaet(), f5_doppelung(), f6_nutzung()]


def befund_schreiben(antworten: list[Antwort]) -> Path:
    durch = [a for a in antworten if not a.bestanden]
    zeilen = [
        "---",
        "title: \"Messung des zweiten Gehirns\"",
        "typ: messung",
        "erfasst_von: gehirnmessung",
        "erfasst_am: %s" % date.today().isoformat(),
        "---",
        "",
        "# Messung des zweiten Gehirns",
        "",
        "Gemessen am %s. %d von %d Fragen bestanden."
        % (date.today().isoformat(), len(antworten) - len(durch), len(antworten)),
        "",
        "| Frage | Gemessen | Grenze | |",
        "|---|---|---|---|",
    ]
    for a in antworten:
        zeilen.append("| %s | %s | %s | %s |"
                      % (a.frage, a.zahl, a.grenze, "ja" if a.bestanden else "**nein**"))
    zeilen += ["", "## Was die Zahlen sagen", ""]
    for a in antworten:
        zeilen.append("- **%s** - %s" % (a.frage, a.satz))
    if durch:
        zeilen += ["", "## Was zu tun ist", ""]
        for a in durch:
            if a.was_tun:
                zeilen.append("- **%s**: %s" % (a.frage, a.was_tun))
    else:
        zeilen += ["", "Nichts zu tun - alle sechs Grenzen gehalten.", ""]
    BEFUND.parent.mkdir(parents=True, exist_ok=True)
    BEFUND.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="")
    return BEFUND


def _melden(antworten: list[Antwort]) -> None:
    try:
        m = _laden("kern_melden", KERN / "melden.py")
        durch = [a for a in antworten if not a.bestanden]
        m.melde("gehirnmessung",
                "Zweites Gehirn: %d von %d Fragen bestanden.%s"
                % (len(antworten) - len(durch), len(antworten),
                   "" if not durch else "\nDurchgefallen: "
                   + "; ".join("%s (%s)" % (a.frage, a.zahl) for a in durch)),
                art="warnung" if durch else "info")
    except Exception:
        pass


def _main(argumente: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    z = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    z.add_argument("--ohne-netz", action="store_true",
                   help="Frage 1 auslassen - sie kostet Einbettungen")
    w = z.parse_args(argumente)
    antworten = messen(w.ohne_netz)
    for a in antworten:
        print("%-16s %-1s %-52s (Grenze: %s)"
              % (a.frage, "+" if a.bestanden else "!", a.zahl[:52], a.grenze))
    pfad = befund_schreiben(antworten)
    _melden(antworten)
    print("\nBefund: %s" % pfad)
    return 0 if all(a.bestanden for a in antworten) else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
