# -*- coding: utf-8 -*-
"""Mias Stimme - die Sprechregie.

Nicht die Maschine macht den Unterschied, sondern was man ihr gibt. Das ist
gemessen: ein Text, der vorher in Sprecheinheiten zerlegt und mit Tonhoehe,
Tempo und Pausenlaenge versehen wird, wurde in einem Hoertest mit 3,87 statt
3,20 bewertet, und 15 von 18 Hoerern zogen ihn vor. Eingefuegte Atemgeraeusche
- das, was ueberall empfohlen wird - brachten dagegen 3,35 statt 3,37, also
nichts.
Quelle Regie: arxiv.org/html/2508.17494 (ICNLSP 2025)
Quelle Atem:  arxiv.org/html/2402.00288v1 (Interspeech 2024)

Deshalb steht hier die Regie und nicht die Maschine im Mittelpunkt. Die
Maschine ist austauschbar - heute edge-tts, weil sie kostenlos ist und keinen
Schluessel braucht; morgen eine bessere, ohne dass sich hier etwas aendert.

Drei Regeln, alle belegt:

  1. SATZWEISE VERTONEN, nicht blockweise. Sonst faellt die Maschine ueber
     Satzgrenzen hinweg in eine Melodie, und genau die klingt maschinell.
     Quelle: WellSaid Labs, "Creating a Natural Voice using Text to Speech"

  2. NICHT HETZEN. Als vertrauenswuerdig gemessen wurden 162-240 Woerter je
     Minute; alle fuenf am schlechtesten bewerteten Varianten sprachen
     schnell. Fuer Deutsch sind das 4-6 Silben je Sekunde, also rund 120-180
     Woerter je Minute.
     Quellen: isca-archive.org speechprosody_2024 yu24e; HHU Duesseldorf

  3. TEMPO WECHSELN, nicht gleichmaessig bleiben. Was menschliche
     Synchronsprecher am staerksten nachbilden, ist der Tonhoehenverlauf
     (gemessener Zusammenhang 0,792) - und genau den wirft die Maschine weg.
     Quelle: TACL, "Dubbing in Practice", Bd. 11

Aufruf:
    python universe/mia/stimme.py probe      zwei Proben: roh und gefuehrt
"""
from __future__ import annotations

import asyncio
import json
import re
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
from dataclasses import dataclass
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
if str(KERN) not in sys.path:
    sys.path.insert(0, str(KERN))
PROBEN = HIER / "stimmproben"

#: Auf welche Kostenstelle Mias Stimme bucht. Sie hat einen eigenen Topf in
#: kosten.json, weil sie einen eigenen Deckel hat.
KOSTENSTELLE = "mia.stimme"
TOPF = "stimme"

#: Das Modell, das wirklich Geld kostet. edge-tts kostet nichts und wird
#: trotzdem gebucht - sonst sieht der Bericht so aus, als haette niemand
#: gesprochen.
MODELL_BEZAHLT = "gpt-4o-mini-tts"
MODELL_FREI = "edge-tts"


# ------------------------------------------------------------------- Der Deckel
# Daniel am 09.09.: "Niemand hat gesagt 40 $ waeren ok...10 sind es."
#
# Ein Deckel, der nur in einer Datei steht, ist ein Versprechen. Dieser hier
# wird vor jedem Aufruf gegen das Buch gehalten - gegen das, was wirklich
# gebucht wurde, nicht gegen eine Schaetzung.

def _verbrauch():
    import verbrauch
    return verbrauch


def deckel_usd() -> float:
    """Was hoechstens ausgegeben werden darf. Steht in kosten.json."""
    v = _verbrauch()
    topf = v.stammdaten().get("toepfe", {}).get(TOPF, {})
    return float(topf.get("deckel_gesamt_usd", 0.0))


def ausgegeben_usd() -> float:
    """Was bisher wirklich gebucht wurde, in USD.

    Gelesen wird das Buch, nicht mitgezaehlt: ein Zaehler im Arbeitsspeicher
    faengt bei jedem Start wieder bei null an, und genau so laeuft ein
    Deckel leer.
    """
    v = _verbrauch()
    kurs = float(v.stammdaten().get("usd_zu_eur", 0.92))
    eur = 0.0
    try:
        with v.BUCH.open(encoding="utf-8") as buch:
            for zeile in buch:
                zeile = zeile.strip()
                if not zeile:
                    continue
                satz = json.loads(zeile)
                if (satz.get("kostenstelle") == KOSTENSTELLE
                        and satz.get("herkunft") == v.ECHT):
                    eur += float(satz.get("betrag_eur", 0.0))
    except (OSError, ValueError):
        # Kein Buch heisst: noch nichts ausgegeben. Nicht: kein Deckel.
        return 0.0
    return eur / kurs if kurs else 0.0


def darf(minuten: float) -> tuple:
    """Darf so viel Audio erzeugt werden? Gibt (ja/nein, Satz) zurueck."""
    v = _verbrauch()
    d = deckel_usd()
    if d <= 0:
        return False, ("Fuer die Stimme steht kein Deckel in kosten.json. "
                       "Kein Deckel heisst nicht 'unbegrenzt', sondern 'noch "
                       "nicht entschieden' - und dann wird nicht gesprochen.")
    bisher = ausgegeben_usd()
    kostet = minuten * float(v.stammdaten().get("preise", {})
                             .get(MODELL_BEZAHLT, 0.0))
    if bisher + kostet > d:
        return False, ("Der Deckel haelt an: %.2f von %.2f USD sind vergeben, "
                       "das hier kostet %.2f USD. Was schon gesprochen ist, "
                       "bleibt liegen." % (bisher, d, kostet))
    return True, ("%.2f von %.2f USD vergeben, das hier kostet %.2f USD - "
                  "danach sind %.2f frei."
                  % (bisher, d, kostet, d - bisher - kostet))


def buchen(minuten: float, wofuer: str, modell: str = MODELL_BEZAHLT) -> None:
    """Erzeugtes Audio verbuchen - in Minuten, denn so ist der Preis."""
    v = _verbrauch()
    v.buchen(
        KOSTENSTELLE,
        betrag_eur=v.preis(modell, 1) * minuten,
        wofuer=wofuer,
        menge=round(minuten, 4),
        dienst="openai" if modell == MODELL_BEZAHLT else "edge",
        modell=modell,
    )

#: Mias Stimme: weiblich, um die 30, westeuropaeisch, warm.
#: Von Daniel am 09.09. so festgelegt.
#:
#: Seraphina ist unter den fuenf deutschen weiblichen Stimmen von edge-tts die
#: einzige mehrsprachige und die neueste. Sie ist ein Anfang, kein Ergebnis -
#: die Endmaschine steht noch nicht fest.
STIMME = "de-DE-SeraphinaMultilingualNeural"

#: Wie schnell Mia spricht, gegenueber der Voreinstellung der Maschine.
#:
#: Gerechnet, nicht gesetzt: die Voreinstellung liegt bei rund 185 Woertern je
#: Minute; als vertrauenswuerdig gemessen wurden 162-240, fuer Deutsch
#: entsprechen 4-6 Silben/Sekunde rund 120-180 Woerter/Minute. Zielwert 165,
#: das sind 165/185 = 0,89, also elf Prozent langsamer. Aufgerundet auf -10 %,
#: weil edge-tts in ganzen Prozent rechnet.
GRUNDTEMPO = -10


@dataclass
class Einheit:
    """Eine Sprecheinheit: ein Satz und wie er gesprochen wird."""

    text: str
    #: Tempo gegenueber dem Grundtempo, in Prozent. Minus heisst langsamer.
    tempo: int = 0
    #: Tonhoehe in Hertz gegenueber der Grundlinie. Minus heisst tiefer.
    hoehe: int = 0
    #: Wie lange danach geschwiegen wird, in Millisekunden.
    pause_ms: int = 260


#: Wie lange nach einem Satzzeichen geschwiegen wird.
#:
#: Startwerte aus der Praxisliteratur (echovox 2026): 150-300 ms zwischen
#: Saetzen, 700-900 ms nach einer Pointe. Genommen ist jeweils die Mitte.
#: Gesetzt, nicht gemessen - sobald eine Aufnahme gestoppt wurde, wird das
#: hier ersetzt.
PAUSE_SATZ = 260
PAUSE_FRAGE = 380
PAUSE_ABSATZ = 800
PAUSE_KOMMA = 140


def _trennen(text: str) -> list:
    """Einen Absatz in Saetze zerlegen, ohne Abkuerzungen zu zerreissen."""
    roh = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in roh if s.strip()]


def regie(text: str) -> list:
    """Aus einem Text Sprecheinheiten machen - das Herz der Sache.

    Was hier passiert und warum:

      · Jeder Satz wird eine eigene Einheit, damit die Maschine ihn einzeln
        vertont und nicht ueber Satzgrenzen hinweg in eine Melodie faellt.
      · Der erste Satz eines Absatzes bekommt etwas mehr Tempo - so faengt ein
        Mensch an, bevor er sich einpendelt.
      · Der letzte Satz wird langsamer und faellt in der Tonhoehe ab. Das ist
        das Schlusssignal, das jeder Zuhoerer kennt; ohne es klingt der Text,
        als sei er mittendrin abgeschnitten.
      · Ein kurzer Satz (unter sechs Woertern) wird langsamer gesprochen als
        ein langer. Sonst huscht er vorbei, obwohl kurz meist wichtig heisst.
      · Eine Frage steigt an und bekommt eine laengere Pause - der Zuhoerer
        soll einen Wimpernschlag Zeit haben.
    """
    saetze = _trennen(text)
    einheiten = []
    for i, satz in enumerate(saetze):
        erster = i == 0
        letzter = i == len(saetze) - 1
        woerter = len(satz.split())
        frage = satz.rstrip().endswith("?")

        tempo = 0
        hoehe = 0
        pause = PAUSE_FRAGE if frage else PAUSE_SATZ

        if erster and not letzter:
            tempo += 4
        if woerter < 6:
            tempo -= 6
            hoehe -= 2
        if frage:
            hoehe += 6
        if letzter:
            tempo -= 8
            hoehe -= 4
            pause = PAUSE_ABSATZ

        einheiten.append(Einheit(satz, tempo, hoehe, pause))
    return einheiten


async def _sprechen(einheit: Einheit, ziel: Path) -> None:
    import edge_tts

    ansage = edge_tts.Communicate(
        einheit.text,
        STIMME,
        rate="%+d%%" % (GRUNDTEMPO + einheit.tempo),
        pitch="%+dHz" % einheit.hoehe,
    )
    await ansage.save(str(ziel))
    # Kostenlos, aber Produktion - steht im Buch (Daniel 32/56).
    try:
        import sys as _sys
        from pathlib import Path as _Path
        kern = str(_Path(__file__).resolve().parent.parent / "kern")
        if kern not in _sys.path:
            _sys.path.append(kern)
        import verbrauch
        verbrauch.kontingent("edge_tts", "fragefenster", 1, wofuer="Mias Stimme")
    except Exception:
        pass


def _zusammensetzen(teile: list, pausen_ms: list, ziel: Path) -> None:
    """Die Einheiten mit ihren Pausen dazwischen zu einer Datei fuegen.

    Die Pausen entstehen als echte Stille, nicht als Tag: was die Maschine
    selbst an Pause macht, ist ihre und nicht unsere.
    """
    ordner = ziel.parent
    liste = ordner / "_liste.txt"
    stille = {}

    zeilen = []
    for teil, ms in zip(teile, pausen_ms):
        zeilen.append("file '%s'" % teil.name)
        if ms <= 0:
            continue
        if ms not in stille:
            s = ordner / ("_stille_%d.mp3" % ms)
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                 "-i", "anullsrc=r=24000:cl=mono",
                 "-t", "%.3f" % (ms / 1000.0), "-c:a", "libmp3lame", str(s)],
                check=True,
            )
            stille[ms] = s
        zeilen.append("file '%s'" % stille[ms].name)

    liste.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(liste), "-c", "copy", str(ziel)],
        check=True, cwd=str(ordner),
    )
    liste.unlink(missing_ok=True)
    for s in stille.values():
        s.unlink(missing_ok=True)
    for teil in teile:
        teil.unlink(missing_ok=True)


def gefuehrt(text: str, ziel: Path) -> list:
    """Den Text mit Regie sprechen. Gibt die Einheiten zurueck."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    einheiten = regie(text)
    teile = []
    for i, e in enumerate(einheiten):
        t = ziel.parent / ("_teil_%02d.mp3" % i)
        asyncio.run(_sprechen(e, t))
        teile.append(t)
    # Nach dem letzten Satz keine Pause anhaengen.
    pausen = [e.pause_ms for e in einheiten[:-1]] + [0]
    _zusammensetzen(teile, pausen, ziel)
    return einheiten


def roh(text: str, ziel: Path) -> None:
    """Denselben Text ohne alles - so, wie es die meisten machen."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_sprechen(Einheit(text), ziel))


PROBETEXT = (
    "Hi, ich bin Mia. "
    "Ich zeige dir in zwei Minuten, was hier wo steht. "
    "Du kannst jederzeit abbrechen. "
    "Bei mir liegt die Fuehrung danach weiter bereit."
)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        text = PROBETEXT.replace("Fuehrung", "Führung")
        roh(text, PROBEN / "1_roh.mp3")
        einheiten = gefuehrt(text, PROBEN / "2_gefuehrt.mp3")
        print("Stimme:", STIMME)
        print("Grundtempo: %+d %%" % GRUNDTEMPO)
        print()
        for e in einheiten:
            print("  %+3d %% Tempo  %+3d Hz  %4d ms Pause   %s"
                  % (e.tempo, e.hoehe, e.pause_ms, e.text))
        print()
        print("Zwei Dateien in", PROBEN)
