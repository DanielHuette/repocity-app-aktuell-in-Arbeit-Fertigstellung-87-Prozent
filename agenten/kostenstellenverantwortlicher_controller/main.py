"""Kostenstellenverantwortlicher / Controller - Kommandozeile.

Er ueberwacht nicht Kosten, er ueberwacht Betrieb. Geld ist eine von vier
Groessen:

  GELD          je Kostenstelle, gegen den Topf, mit harter Bremse
  TAKT          laeuft dieser Teil noch? Ein Modul, das seit zehn Tagen
                schweigt, ist ein Alarm - kein Sparerfolg
  KONTINGENT    freie Abrufe bei Pexels, GitHub, Pixabay. Kosten nichts
                und halten die Strasse trotzdem an, wenn sie leer sind
  EINGRIFFE     wie oft du eingreifen musstest. Die knappste Ressource

  python main.py kassensturz      Geld je Topf und Kostenstelle
  python main.py puls             wer meldet sich, wer schweigt
  python main.py kontingente      was von den freien Abrufen uebrig ist
  python main.py verschwendung    was bezahlt und dann verworfen wurde
  python main.py bericht          alles zusammen, zum Lesen
  python main.py darf prod.video.stueck 0.30    darf das laufen?
  python main.py takte            was er gelernt hat

Er gibt kein Geld aus und haelt nichts an - er sagt, was ist. Angehalten
wird an der Stelle, die ausgeben will, ueber verbrauch.darf().
Die Grenze setzt der Nutzer selbst - siehe kern/bremse.py.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

import takt as takt_lernen  # noqa: E402
import rueckweg  # noqa: E402
import verbrauch  # noqa: E402

try:
    import melden as meldung
except ImportError:
    meldung = None

AGENT = "kostenstellenverantwortlicher"
MODUL = "system.kosten"

#: Ab diesem Anteil der Marke, die der Nutzer gesetzt hat, wird gewarnt.
#: Von Daniel am 07.09. festgelegt. Ohne gesetzte Marke gibt es keine
#: Warnung, weil es keine Grenze gibt.
WARNSCHWELLE = 0.8


def _module() -> list[str]:
    try:
        briefe = json.loads((HIER.parent / "gehirn.json").read_text(
            encoding="utf-8")).get("steckbriefe", {})
    except (OSError, json.JSONDecodeError):
        return []
    return sorted(k for k in briefe if k != "standard")


# ------------------------------------------------------------------ Geld

def kassensturz(seit: str | None = None) -> dict:
    seit = seit or verbrauch.monatsanfang()
    toepfe = {}
    for name, topf in verbrauch.stammdaten().get("toepfe", {}).items():
        # Die Marke gehoert dem Nutzer und haengt an der Kostenstelle, nicht
        # am Topf. Fuer die Uebersicht gilt die groesste im Topf.
        module = topf.get("module") or []
        monat = max([verbrauch.marke(m, "monat") for m in module] or [0.0])
        ist = verbrauch.verbraucht(topf=name, seit=seit)
        toepfe[name] = {
            "verbraucht": round(ist, 4),
            "marke": monat,
            "rest": round(monat - ist, 4) if monat else None,
            "anteil": round(ist / monat, 3) if monat else None,
            "warnung": bool(monat) and ist >= monat * WARNSCHWELLE,
        }
    stellen: dict[str, float] = {}
    for s in verbrauch.buchungen(seit, art=verbrauch.GELD):
        stellen[s["kostenstelle"]] = round(
            stellen.get(s["kostenstelle"], 0.0) + s.get("betrag_eur", 0.0), 6)
    return {"seit": seit, "toepfe": toepfe,
            "kostenstellen": dict(sorted(stellen.items(),
                                         key=lambda p: -p[1]))}


# ------------------------------------------------------------------ Verschwendung

def verschwendung(seit: str | None = None) -> dict:
    """Was bezahlt und dann verworfen wurde.

    Die Halde sagt, was liegen blieb. Die Erfahrungen sagen, was es
    gekostet hat. Zusammen ergibt das die Zahl, die am meisten weh tut -
    und die einzige, die sich durch besseres Lernen wirklich senken laesst.
    """
    seit = seit or verbrauch.monatsanfang()
    verworfen = {h.get("kennung"): h for h in rueckweg.halde()
                 if h.get("datum", "") >= seit}
    summe = 0.0
    posten = []
    for e in rueckweg.erfahrungen(None, 5000, art=None):
        if e.get("datum", "") < seit:
            continue
        kosten = _zahl(e.get("kosten"))
        if e.get("urteil") == "nein" and kosten:
            summe += kosten
            posten.append({"auftrag": e.get("auftrag"), "modul": e.get("modul"),
                           "kosten": kosten, "grund": e.get("grund", "")})
    return {"seit": seit, "summe": round(summe, 4),
            "posten": sorted(posten, key=lambda p: -p["kosten"]),
            "auf_der_halde": len(verworfen)}


def _zahl(wert, ersatz=0.0) -> float:
    try:
        return float(str(wert).replace(",", "."))
    except (TypeError, ValueError):
        return ersatz


# ------------------------------------------------------------------ Eingriffe

def eingriffe(seit: str | None = None) -> dict:
    """Wie oft du eingreifen musstest - die knappste Ressource im Haus."""
    seit = seit or verbrauch.monatsanfang()
    alle = [e for e in rueckweg.erfahrungen(None, 5000, art=rueckweg.ECHT)
            if e.get("datum", "") >= seit]
    neins = [e for e in alle if e.get("urteil") == "nein"]
    return {
        "seit": seit,
        "vorgelegt": len(alle),
        "deine_neins": len(neins),
        "anteil": round(len(neins) / len(alle), 3) if alle else None,
        "gruende": [e.get("grund", "") for e in neins][:8],
    }


# ------------------------------------------------------------------ Bericht

def bericht(seit: str | None = None) -> str:
    seit = seit or verbrauch.monatsanfang()
    k = kassensturz(seit)
    v = verschwendung(seit)
    ein = eingriffe(seit)
    takte = takt_lernen.lernen()
    still = [e for e in takte.values() if e["still"]]
    ungebaut = takt_lernen.nie_gemeldet(_module())

    z = ["BERICHT DES KOSTENSTELLENVERANTWORTLICHEN",
         "Zeitraum: seit %s" % seit, "", "GELD", ""]
    z.append("%-22s %11s %11s %8s" % ("Topf", "verbraucht", "deine Marke", "Anteil"))
    for name, t in k["toepfe"].items():
        anteil = "%.1f %%" % (t["anteil"] * 100) if t["anteil"] is not None else "-"
        zeichen = "  !" if t["warnung"] else "   "
        z.append("%-22s %10.4f€ %10.2f€ %7s%s"
                 % (name, t["verbraucht"], t["marke"], anteil, zeichen))
    if k["kostenstellen"]:
        z += ["", "Die teuersten Kostenstellen:"]
        for stelle, betrag in list(k["kostenstellen"].items())[:5]:
            z.append("   %-24s %10.4f€" % (stelle, betrag))
    else:
        z += ["", "   Keine Ausgabe verbucht."]

    z += ["", "TAKT", ""]
    if still:
        z.append("Diese Stellen schweigen laenger als gewohnt:")
        for e in still:
            z.append("   ! %-22s %s" % (e["kostenstelle"], e["warum"]))
    else:
        z.append("   Keine Stelle schweigt laenger als gewohnt.")
    unbekannt = [e for e in takte.values() if e["takt"] == "noch unbekannt"]
    if unbekannt:
        z.append("   %d Stellen sind noch zu kurz beobachtet fuer einen Takt."
                 % len(unbekannt))
    if ungebaut:
        z += ["", "   Von diesen Modulen kam noch nie eine Meldung -",
              "   das ist kein Stillstand, sondern ungebaut:"]
        z.append("   " + ", ".join(ungebaut))

    z += ["", "KONTINGENTE", ""]
    for dienst in verbrauch.stammdaten().get("kontingente", {}):
        if dienst.startswith("_"):
            continue
        s = verbrauch.kontingent_stand(dienst)
        z.append("   %-10s %s von %s je Stunde, %s von %s im Monat"
                 % (dienst, s["in_dieser_stunde"], s["je_stunde"],
                    s["in_diesem_monat"], s["je_monat"]))

    z += ["", "VERSCHWENDUNG", "",
          "   %.4f€ bezahlt und dann verworfen, %d Stueck auf der Halde."
          % (v["summe"], v["auf_der_halde"])]
    for p in v["posten"][:3]:
        z.append("   %-14s %8.4f€  %s" % (p["auftrag"], p["kosten"],
                                          (p["grund"] or "")[:44]))

    z += ["", "DEINE EINGRIFFE", ""]
    if ein["vorgelegt"]:
        z.append("   %d Stueck vorgelegt, %d davon von dir abgelehnt (%.0f %%)."
                 % (ein["vorgelegt"], ein["deine_neins"], (ein["anteil"] or 0) * 100))
        for g in ein["gruende"][:3]:
            z.append("      - " + g[:60])
    else:
        z.append("   Nichts vorgelegt in diesem Zeitraum.")

    z += ["", "Diese Zahl soll ueber Monate fallen, waehrend die Menge steigt.",
          "Das ist die eine Zahl, an der 'laeuft unbeaufsichtigt' zu erkennen ist."]
    return "\n".join(z)


def warnen(seit: str | None = None) -> list[str]:
    """Was gemeldet gehoert. Leer heisst: alles im Rahmen."""
    hinweise = []
    for name, t in kassensturz(seit)["toepfe"].items():
        if t["warnung"]:
            hinweise.append("Topf '%s' bei %.0f %% deiner Marke (%.2f von "
                            "%.2f EUR)." % (name, (t["anteil"] or 0) * 100,
                                            t["verbraucht"], t["marke"]))
    for e in takt_lernen.stillstand():
        hinweise.append("%s: %s" % (e["kostenstelle"], e["warum"]))
    for dienst in verbrauch.stammdaten().get("kontingente", {}):
        if dienst.startswith("_"):
            continue
        s = verbrauch.kontingent_stand(dienst)
        if s["stunde_frei"] is not None and s["je_stunde"] and \
                s["in_dieser_stunde"] >= s["je_stunde"] * WARNSCHWELLE:
            hinweise.append("Kontingent %s fast aufgebraucht: %s von %s in "
                            "dieser Stunde." % (dienst, s["in_dieser_stunde"],
                                                s["je_stunde"]))
    if hinweise and meldung is not None:
        meldung.melde(absender=MODUL, art="fehler",
                      zusammenfassung="%d Hinweise vom Controller" % len(hinweise),
                      text="\n".join("- " + h for h in hinweise))
    return hinweise


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "bericht").lower()
    rest = argumente[1:]
    seit = next((a for a in rest if a.startswith("2")), None)

    if befehl == "bericht":
        print(bericht(seit))
        return 0

    if befehl == "kassensturz":
        k = kassensturz(seit)
        print("seit %s" % k["seit"])
        for name, t in k["toepfe"].items():
            print("%-22s %10.4f€ von %8.2f€%s"
                  % (name, t["verbraucht"], t["marke"],
                     "   ACHTUNG" if t["warnung"] else ""))
        for stelle, betrag in k["kostenstellen"].items():
            print("   %-24s %10.4f€" % (stelle, betrag))
        return 0

    if befehl == "puls":
        takte = takt_lernen.lernen()
        if not takte:
            print("Das Tagebuch ist leer - noch kein Puls messbar.")
            return 0
        print("%-24s %-13s %10s  %s" % ("Kostenstelle", "Takt", "still seit", ""))
        for e in sorted(takte.values(), key=lambda x: (not x["still"],
                                                       x["kostenstelle"])):
            print("%s%-24s %-13s %8.1f h  %s"
                  % ("! " if e["still"] else "  ", e["kostenstelle"],
                     e["takt"], e["stunden_still"], e["warum"][:52]))
        ungebaut = takt_lernen.nie_gemeldet(_module())
        if ungebaut:
            print("\nNoch nie gemeldet (ungebaut, nicht kaputt):")
            print("  " + ", ".join(ungebaut))
        return 0

    if befehl == "takte":
        for e in sorted(takt_lernen.lernen().values(),
                        key=lambda x: x["kostenstelle"]):
            print("%-24s %-13s aus %d Meldungen ueber %.1f Tage"
                  % (e["kostenstelle"], e["takt"], e["meldungen"],
                     e["beobachtet_tage"]))
        return 0

    if befehl == "kontingente":
        for dienst in verbrauch.stammdaten().get("kontingente", {}):
            if dienst.startswith("_"):
                continue
            s = verbrauch.kontingent_stand(dienst)
            print("%-10s %5s von %6s je Stunde   %6s von %7s im Monat"
                  % (dienst, s["in_dieser_stunde"], s["je_stunde"],
                     s["in_diesem_monat"], s["je_monat"]))
        return 0

    if befehl == "verschwendung":
        v = verschwendung(seit)
        print("%.4f€ bezahlt und verworfen, %d Stueck auf der Halde (seit %s)"
              % (v["summe"], v["auf_der_halde"], v["seit"]))
        for p in v["posten"]:
            print("  %-14s %8.4f€ %-22s %s" % (p["auftrag"], p["kosten"],
                                               p["modul"], p["grund"][:40]))
        return 0

    if befehl == "darf" and len(rest) > 1:
        ja, grund = verbrauch.darf(rest[0], float(rest[1]),
                                   float(rest[2]) if len(rest) > 2 else 0.0)
        print(("JA  - " if ja else "NEIN - ") + grund)
        return 0 if ja else 1

    if befehl == "warnen":
        hinweise = warnen(seit)
        for h in hinweise:
            print("! " + h)
        if not hinweise:
            print("Alles im Rahmen.")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
