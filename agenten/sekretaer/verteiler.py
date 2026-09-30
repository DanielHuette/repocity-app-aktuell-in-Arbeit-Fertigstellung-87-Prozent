"""Der Sekretaer als Verteiler - hier wird aus einem Auftrag Arbeit.

Bisher hat der Sekretaer nur zusammengetragen, was die Agenten hinterlassen
haben. Das hier ist die andere Richtung: Er holt beim Hub ab, was Daniel
aufgegeben hat, sieht nach, wer dafuer zustaendig ist, und startet ihn.

    Hub  --- Auftrag -->  Sekretaer  --- startet -->  Agent
    Hub  <-- Zustand ---  Sekretaer  <-- meldet ----  Agent

Drei Dinge sind Absicht:

**Jeder Agent bekommt seinen eigenen Prozess.** Ueber kern/starter.py.
main.py gibt es zwoelfmal im Universe, einstellungen.py zehnmal - im
selben Prozess wuerde der zweite Agent mit den Einstellungen des ersten
arbeiten, ohne dass es jemand merkt.

**Ein Auftrag ohne Agenten wird zurueckgewiesen, nicht liegengelassen.**
Fuer Praesentation, Apps, Marketing, Webseite und Trading gibt es noch
keinen Agenten. Ein Auftrag dorthin bekommt sofort eine ehrliche Absage -
das ist besser, als wenn Daniel wochenlang auf ein Ergebnis wartet.

**Der Kostentopf wird vorher gefragt.** Ein Auftrag, dessen Topf leer ist,
faengt gar nicht erst an.

**Ein unklarer Auftrag wird gefragt, nicht geraten.** Seit dem 11.09.2026
steht vor der Strasse die Klaerung (kern/klaerung.py). Was sie nicht
versteht, geht als Meldung "rueckfrage" ins Fach des Auftraggebers; der
Auftrag wartet beim Hub im Zustand "rueckfrage". Die Antwort kommt als
Entscheidung zurueck (ja + Text = Antwort, nein = zurueckziehen) und wird
an den Auftragstext gehaengt - dann laeuft er wie jeder andere.

  python verteiler.py stand       was beim Hub liegt und wer dafuer da waere
  python verteiler.py einmal      alle offenen Auftraege verteilen
  python verteiler.py takt        immer wieder nachsehen (Dauerlauf)
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

import hub as hub_modul  # noqa: E402
import kennung as kennung_modul  # noqa: E402
import starter  # noqa: E402
import verbrauch

try:
    import laenge as laenge_modul
except ImportError:                                  # pragma: no cover
    laenge_modul = None

try:
    import stoff as stoff_modul
except ImportError:
    stoff_modul = None  # noqa: E402

try:
    import klaerung as klaerung_modul
except ImportError:                                  # pragma: no cover
    klaerung_modul = None

ARTENDATEI = UNIVERSE / "auftragsarten.json"
ZUSTAND = UNIVERSE / "zustand"

#: Zustand eines Auftrags, der auf eine Antwort des Auftraggebers wartet.
RUECKFRAGE = "rueckfrage"

#: Wie oft im Dauerlauf beim Hub nachgesehen wird.
TAKT_SEK = 60


def tabellen() -> tuple[dict, dict]:
    """(Auftragsarten, wer arbeitet). Leer, wenn die Datei fehlt."""
    try:
        d = json.loads(ARTENDATEI.read_text(encoding="utf-8"))
        return d.get("arten", {}), d.get("wer_arbeitet", {})
    except (OSError, json.JSONDecodeError):
        return {}, {}


def modul_von(art: str) -> str | None:
    """Die Auftragsart kann als Kennung oder als Beschriftung kommen."""
    arten, _ = tabellen()
    if art in arten:
        return arten[art]["modul"]
    for kennung, angabe in arten.items():
        if angabe.get("label", "").lower() == art.lower():
            return angabe["modul"]
    return None


def zustaendig(modul: str) -> dict | None:
    _, wer = tabellen()
    return wer.get(modul)


# ------------------------------------------------------------------ verteilen

def einen_verteilen(auftrag: dict) -> dict:
    """Einen Auftrag zustellen. Gibt zurueck, was daraus geworden ist."""
    kennung = auftrag.get("id", "?")
    art = auftrag.get("art", "")
    modul = auftrag.get("modul") or modul_von(art)

    if not modul:
        return _absage(kennung, "Die Auftragsart '%s' kenne ich nicht. "
                                "Bekannt sind: %s"
                       % (art, ", ".join(sorted(tabellen()[0]))))

    stelle = zustaendig(modul)
    if not stelle:
        return _absage(kennung,
                       "Fuer '%s' gibt es noch keinen Agenten. Der Auftrag "
                       "wird nicht angenommen - besser eine Absage jetzt als "
                       "Warten auf etwas, das nicht kommt." % modul)

    # Kostentopf fragen, bevor irgendetwas anlaeuft.
    darf, grund = verbrauch.darf(modul, 0.0)
    if not darf:
        return _absage(kennung, "Kostenbremse: " + grund)

    # Die bestellte Laenge. Die Grenzen sind hart: was ausserhalb liegt, wird
    # nicht zurechtgebogen, sondern abgesagt - mit dem Bereich im Klartext.
    # Steht nichts im Auftrag, gilt die Voreinstellung der Strasse.
    laenge_sek = _laenge_bestimmen(auftrag, modul)
    if isinstance(laenge_sek, str):
        return _absage(kennung, laenge_sek)

    agent = stelle["agent"]

    # Ist der Auftrag klar genug? Ein Auftrag, der schon einmal gefragt
    # wurde, traegt seine Antwort im Text und wird nicht noch einmal gefragt.
    if klaerung_modul is not None and not auftrag.get("_geklaert"):
        klaerung = klaerung_modul.pruefen(auftrag, modul)
        if not klaerung.klar:
            return _rueckfrage(auftrag, modul, klaerung)

    # Stoff besorgen, bevor die Strasse anlaeuft: der Kurator gibt heraus, was
    # das Haus zum Thema hat, und sagt, wie gut es gedeckt ist. Nur fuer die
    # kreativen Strassen - die Lebensverwaltung hat eigene Quellen.
    stoff = None
    if stoff_modul is not None and stoff_modul.ist_kreativ(modul):
        stoff = stoff_modul.holen(
            {"id": kennung, "titel": auftrag.get("titel", ""),
             "text": auftrag.get("text", ""), "modul": modul},
            modul=modul, braucht=("text", "bilder", "stuecke"))
        if stoff is not None:
            hub_modul.zustand_melden(
                kennung, "angenommen",
                "Stoff: %s" % stoff.deckung.satz, fortschritt=0.0)

    if stelle.get("eingang"):
        _in_den_eingang(stelle["eingang"], auftrag, modul, stoff, laenge_sek)

    hub_modul.zustand_melden(
        kennung, "angenommen",
        "%s laeuft an" % agent, fortschritt=0.0)

    # Anstossen und weitergehen. Der Sekretaer wartet nicht mehr auf die
    # Werkstatt und urteilt nicht ueber sie: was aus dem Auftrag wird,
    # meldet sie selbst. Seine Sache ist nur noch, ob sie ueberhaupt
    # anlaeuft.
    anstoss = starter.anstossen(agent, stelle.get("befehl", "einmal"))

    if anstoss.gestartet or anstoss.schon_da:
        hub_modul.zustand_melden(
            kennung, "laeuft",
            "An %s uebergeben - %s. Was dabei herauskommt, meldet er selbst."
            % (agent, "arbeitet schon" if anstoss.schon_da else "angelaufen"),
            fortschritt=0.5)
        return {"kennung": kennung, "agent": agent, "modul": modul,
                "ergebnis": "uebergeben", "pid": anstoss.pid}

    hub_modul.zustand_melden(
        kennung, "fehler", "%s: %s" % (agent, anstoss.grund))
    return {"kennung": kennung, "agent": agent, "modul": modul,
            "ergebnis": "nicht angestossen", "grund": anstoss.grund}


def _absage(kennung: str, grund: str) -> dict:
    hub_modul.zustand_melden(kennung, "abgebrochen", grund)
    return {"kennung": kennung, "ergebnis": "abgelehnt", "grund": grund}


# ------------------------------------------------------------------ Rueckfrage

def _rueckfrage(auftrag: dict, modul: str, klaerung) -> dict:
    """Die Fragen ins Fach des Auftraggebers legen, den Auftrag warten lassen.

    Kommt die Meldung nicht an, bleibt der Auftrag beim Hub auf "gesendet"
    und wird beim naechsten Takt wieder angefasst - eine Frage, die niemand
    lesen kann, ist keine.
    """
    kennung = auftrag.get("id", "?")
    text = klaerung.als_text()
    if klaerung.annahmen:
        text += "\n\nWas ich sonst annehme, wenn du nichts anderes sagst:\n" + "\n".join(
            "- " + a for a in klaerung.annahmen)
    angekommen = hub_modul.melden(
        "sekretaer", text, art=RUECKFRAGE,
        zusammenfassung="Rueckfrage zu deinem Auftrag: %s" % (
            (auftrag.get("titel") or auftrag.get("text") or auftrag.get("art") or "")[:60]),
        vorgang=kennung,
        daten={"fragen": klaerung.fragen, "annahmen": klaerung.annahmen,
               "modul": modul, "weg": klaerung.weg},
        nutzer=auftrag.get("nutzer", ""))
    if not angekommen:
        return {"kennung": kennung, "modul": modul, "ergebnis": "rueckfrage nicht zustellbar",
                "grund": "Meldung kam nicht beim Hub an"}
    _merkzettel(kennung).write_text(json.dumps({
        "id": kennung, "modul": modul, "fragen": klaerung.fragen,
        "annahmen": klaerung.annahmen, "gefragt": datetime.now().isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    hub_modul.zustand_melden(
        kennung, RUECKFRAGE,
        "Rueckfrage an dich: %s" % (klaerung.fragen[0] if klaerung.fragen else "?"),
        fortschritt=0.0)
    return {"kennung": kennung, "modul": modul, "ergebnis": "rueckfrage",
            "fragen": list(klaerung.fragen)}


def _merkzettel(kennung: str) -> Path:
    ordner = ZUSTAND / "rueckfragen"
    ordner.mkdir(parents=True, exist_ok=True)
    return ordner / ("%s.json" % _dateiname(kennung))


def _mit_antwort(auftrag: dict, entscheidung: dict) -> str:
    """Der Auftragstext, ergaenzt um Fragen und Antwort - so sieht die
    Strasse beides, und die Erfahrung dazu spaeter auch."""
    fragen, annahmen = [], []
    try:
        zettel = json.loads(_merkzettel(auftrag.get("id", "?")).read_text(encoding="utf-8"))
        fragen, annahmen = zettel.get("fragen", []), zettel.get("annahmen", [])
    except (OSError, json.JSONDecodeError):
        fragen = list((entscheidung.get("daten") or {}).get("fragen", []))
        annahmen = list((entscheidung.get("daten") or {}).get("annahmen", []))
    zeilen = [(auftrag.get("text") or "").strip(), "", "Rueckfrage des Sekretaers:"]
    zeilen += ["- " + f for f in fragen]
    zeilen += ["Antwort des Auftraggebers: " + (entscheidung.get("grund") or "").strip()]
    if annahmen:
        zeilen += ["Dabei angenommen: " + "; ".join(annahmen)]
    return "\n".join(zeilen).strip()


def rueckfragen_abholen() -> list[dict]:
    """Beantwortete Rueckfragen einsammeln und die Auftraege laufen lassen.

    Ein Auftrag, der beim Hub auf "rueckfrage" steht, wartet auf eine
    Entscheidung zu der Meldung, deren vorgang seine Kennung ist. Ja heisst:
    die Antwort (der Text der Entscheidung) kommt an den Auftrag, dann
    laeuft er. Nein heisst: zurueckgezogen. Sobald der Auftrag laeuft oder
    abgesagt ist, steht er nicht mehr auf "rueckfrage" - dieselbe Antwort
    wird darum kein zweites Mal verarbeitet.
    """
    if not hasattr(hub_modul, "auftraege"):
        return []
    wartend = {a.get("id"): a for a in hub_modul.auftraege(RUECKFRAGE)}
    if not wartend:
        return []
    ergebnisse = []
    for entscheidung in hub_modul.entscheidungen():
        if entscheidung.get("art") != RUECKFRAGE:
            continue
        auftrag = wartend.pop(entscheidung.get("vorgang"), None)
        if auftrag is None:
            continue
        kennung = auftrag.get("id", "?")
        if entscheidung.get("entscheidung") == "nein":
            ergebnisse.append(_absage(
                kennung, "Auf die Rueckfrage hin zurueckgezogen: %s"
                % (entscheidung.get("grund") or "").strip()))
        else:
            auftrag["text"] = _mit_antwort(auftrag, entscheidung)
            auftrag["_geklaert"] = True
            ergebnisse.append(einen_verteilen(auftrag))
        try:
            _merkzettel(kennung).unlink()
        except OSError:
            pass
    return ergebnisse


def _dateiname(kennung: str) -> str:
    """Aus einer Hub-Kennung einen Dateinamen machen.

    Die Regel dazu steht in kern/kennung.py und nur dort - sie gilt
    genauso fuer die Arbeitsordner der Werkstaetten, und solange sie
    hier ein zweites Mal stand, galt sie dort eben nicht.
    """
    return kennung_modul.sauber(kennung)


def _laenge_bestimmen(auftrag: dict, modul: str):
    """Die bestellte Laenge in Sekunden - oder ein Absagegrund als Text.

    Ohne den Regler-Baustein wird nichts geprueft und nichts erfunden: dann
    geht der Auftrag durch wie bisher.
    """
    if laenge_modul is None or laenge_modul.regler(modul) is None:
        return None
    gewuenscht = auftrag.get("laenge_sek", auftrag.get("sekunden"))
    if gewuenscht in (None, ""):
        return laenge_modul.voreinstellung(modul)
    passt, grund = laenge_modul.pruefen(modul, gewuenscht)
    if not passt:
        return "Die bestellte Laenge geht nicht: %s." % grund
    return float(gewuenscht)


def _in_den_eingang(ordner: str, auftrag: dict, modul: str,
                    stoff=None, laenge_sek=None) -> Path:
    """Den Auftrag als JSON in den Eingang des Agenten legen.

    So bekommt ein Agent seinen Auftrag, ohne dass wir seine Kommandozeile
    umbauen muessen - der Video-Agent liest diesen Ordner ohnehin schon.
    """
    ziel = ZUSTAND / ordner
    ziel.mkdir(parents=True, exist_ok=True)
    datei = ziel / ("%s.json" % _dateiname(auftrag.get("id", "auftrag")))
    inhalt = {
        "id": auftrag.get("id"),
        "thema": auftrag.get("text", ""),
        "text": auftrag.get("text", ""),
        "titel": auftrag.get("titel", ""),
        "modul": modul,
        "trocken": auftrag.get("trocken", True),
        "vom_hub": True,
        "angelegt": auftrag.get("angelegt", datetime.now().isoformat()),
    }
    if laenge_sek is not None:
        inhalt["laenge_sek"] = laenge_sek
        inhalt["sekunden"] = laenge_sek        # so heisst es in den Strassen
        if laenge_modul is not None:
            inhalt["laenge_soll"] = laenge_modul.als_soll(modul, laenge_sek)
    if stoff is not None and stoff_modul is not None:
        inhalt["stoff"] = stoff_modul.als_auftragsfeld(stoff)
    datei.write_text(json.dumps(inhalt, ensure_ascii=False, indent=2),
                     encoding="utf-8", newline="")
    return datei


def alle_verteilen() -> list[dict]:
    offen = hub_modul.offene_auftraege()
    ergebnisse = [einen_verteilen(a) for a in offen]
    ergebnisse += rueckfragen_abholen()
    return ergebnisse


# ------------------------------------------------------------------ Aufruf

def _stand() -> int:
    arten, wer = tabellen()
    print("AUFTRAGSARTEN UND WER SIE BEDIENT")
    print("=" * 68)
    for kennung, angabe in sorted(arten.items()):
        modul = angabe["modul"]
        stelle = wer.get(modul)
        print("%-16s %-22s %s" % (
            angabe["label"][:16], modul,
            stelle["agent"] if stelle else "-- noch kein Agent --"))
    print()

    if not hub_modul.eingerichtet():
        print("Der Hub ist nicht eingerichtet - es kann nichts hereinkommen.")
        print("  python universe/kern/einrichten.py hub")
        return 2
    try:
        zahlen = hub_modul.stand()
        print("Hub: %s Auftraege, davon %s offen"
              % (zahlen.get("auftraege"), zahlen.get("offen")))
    except hub_modul.NichtErreichbar as fehler:
        print("Hub nicht erreichbar: %s" % fehler)
        return 1
    for a in hub_modul.offene_auftraege():
        print("  %-26s %-18s %s" % (a.get("id"), a.get("art"),
                                    (a.get("text") or "")[:34]))
    return 0


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()

    if befehl == "stand":
        return _stand()

    if befehl == "einmal":
        ergebnisse = alle_verteilen()
        if not ergebnisse:
            print("Nichts zu verteilen.")
            return 0
        for e in ergebnisse:
            print("%-26s %-14s %s" % (e["kennung"], e["ergebnis"],
                                      e.get("agent") or e.get("grund", "")[:40]
                                      or "; ".join(e.get("fragen", []))[:40]))
        return 0

    if befehl == "takt":
        takt = int(argumente[1]) if len(argumente) > 1 else TAKT_SEK
        print("Sekretaer im Dauerlauf, alle %d Sekunden. Strg-C beendet." % takt)
        while True:
            try:
                for e in alle_verteilen():
                    print("%s  %-26s %-14s %s" % (
                        datetime.now().strftime("%H:%M:%S"), e["kennung"],
                        e["ergebnis"], e.get("agent") or ""))
            except KeyboardInterrupt:
                print("\nangehalten.")
                return 0
            except Exception as fehler:
                # Ein Fehler haelt den Dauerlauf nicht an - beim naechsten
                # Takt wird es wieder versucht.
                print("Takt uebersprungen: %s" % fehler)
            try:
                time.sleep(takt)
            except KeyboardInterrupt:
                print("\nangehalten.")
                return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
