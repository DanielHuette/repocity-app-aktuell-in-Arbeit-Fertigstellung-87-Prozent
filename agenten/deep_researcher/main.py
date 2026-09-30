"""Deep Researcher — Kommandozeile.

  python main.py recherche "<frage>" [--quellen 8] [--art wissen|vorlagen|lernprogramm]
  python main.py eingang            was für den Kurator bereitliegt
  python main.py frage "<frage>"    nur suchen und die Trefferliste zeigen
"""
from __future__ import annotations

import argparse
import sys

import ablage
import destillat
import katalog
import meldung
import rundgang
import einstellungen
import gehirn
import holen
import suche

ZUSATZ = {
    "wissen": "",
    "vorlagen": " HTML CSS Vorlage Beispiel Quelltext",
    "lernprogramm": " interaktives Lernprogramm Aufbau Didaktik Beispiel",
}


def befehl_frage(args) -> int:
    konfig = einstellungen.laden()
    try:
        treffer = suche.suchen(args.frage, args.quellen, konfig["suche"]["sperrliste"])
    except suche.SucheGesperrt as grund:
        print("Es wird nicht gesucht: %s" % grund)
        return 1
    for eintrag in treffer:
        print(f"{eintrag.quelle:14} {eintrag.titel[:70]}")
        print(f"{'':14} {eintrag.url}")
    print(f"\n{len(treffer)} Quellen")
    return 0


def befehl_recherche(args) -> int:
    konfig = einstellungen.laden()
    frage = args.frage
    suchtext = frage + ZUSATZ.get(args.art, "")

    vorhanden = gehirn.lesen(frage)
    if vorhanden:
        print(f"Im 2nd brain liegt dazu schon etwas: {len(vorhanden)} Fundstellen "
              + ", ".join(sorted({f.saeule for f in vorhanden})))

    try:
        treffer = suche.suchen(suchtext, args.quellen, konfig["suche"]["sperrliste"])
    except suche.SucheGesperrt as grund:
        print("Es wird nicht gesucht: %s" % grund)
        return 1
    if not treffer:
        print("Keine Quellen gefunden.")
        return 1

    ziel = ablage.ordner_anlegen(konfig, frage)
    quellen: list[dict] = []
    notizen = atome_gesamt = 0

    for nummer, eintrag in enumerate(treffer, 1):
        print(f"[{nummer}/{len(treffer)}] {eintrag.url}")
        text, grund = holen.text_holen(eintrag.url, konfig["suche"]["mindestzeichen"])
        if grund:
            quellen.append({"url": eintrag.url, "titel": eintrag.titel,
                            "zeichen": 0, "ausgang": grund})
            print(f"      {grund}")
            continue
        if len(text) < konfig["suche"]["mindestzeichen"]:
            quellen.append({"url": eintrag.url, "titel": eintrag.titel,
                            "zeichen": len(text), "ausgang": "zu wenig Text"})
            print(f"      zu wenig Text ({len(text)} Zeichen)")
            continue

        inhalt = destillat.destillieren(frage, eintrag.titel, eintrag.url, text, konfig)
        if not inhalt.get("brauchbar", True):
            quellen.append({"url": eintrag.url, "titel": eintrag.titel,
                            "zeichen": len(text),
                            "ausgang": "unbrauchbar: " + inhalt.get("grund", "")})
            print(f"      unbrauchbar: {inhalt.get('grund','')}")
            continue

        ablage.notiz_schreiben(ziel, inhalt.get("titel") or eintrag.titel,
                               destillat.notiz_bauen(inhalt, eintrag.url,
                                                     ablage.schluessel(frage)))
        atome = destillat.atome_bauen(inhalt, eintrag.url, eintrag.titel,
                                      ablage.schluessel(frage))
        if atome:
            ablage.atome_anhaengen(ziel, atome)
        notizen += 1
        atome_gesamt += len(atome)
        quellen.append({"url": eintrag.url, "titel": eintrag.titel,
                        "zeichen": len(text), "ausgang": "verwendet",
                        "atome": len(atome), "weg": inhalt.get("weg", "")})
        print(f"      {len(atome)} Atome ({inhalt.get('weg','')})")

    ablage.quellen_schreiben(ziel, quellen)
    ablage.uebergabe_schreiben(ziel, frage, quellen, notizen, atome_gesamt)
    ablage.fall_ablegen(frage, quellen, notizen, atome_gesamt, ziel)

    print(f"\n{notizen} Notizen, {atome_gesamt} Atome")
    print(ziel)
    return 0


def befehl_eingang(args) -> int:
    from pathlib import Path
    konfig = einstellungen.laden()
    eingang = Path(konfig["ablage"]["eingang"])
    if not eingang.exists():
        print("Nichts im Eingang.")
        return 0
    for ordner in sorted(eingang.iterdir()):
        if not ordner.is_dir():
            continue
        notizen = len(list((ordner / "wissen").glob("*.md"))) if (ordner / "wissen").exists() else 0
        atomdatei = ordner / "atome.jsonl"
        atome = sum(1 for _ in atomdatei.open(encoding="utf-8")) if atomdatei.exists() else 0
        print(f"{ordner.name:60} {notizen:3} Notizen  {atome:4} Atome")
    return 0



def befehl_runde(args) -> int:
    """Den Quellenkatalog abgehen und alles Neue destillieren."""
    konfig = einstellungen.laden()
    quellen = katalog.laden(kategorien=args.kategorie or None)
    if not quellen:
        print("Keine Quellen im Katalog. quellen_katalog.json prüfen.")
        return 1
    print(f"{len(quellen)} Quellen, Kategorien: "
          + ", ".join(sorted({q.kategorie for q in quellen})))

    gesehen = rundgang.gesehen_laden()
    neue, vermerke = rundgang.neues_sammeln(quellen, args.tage, args.je_quelle, gesehen)
    print(f"{len(neue)} neue Beiträge, {len(vermerke)} Quellen ohne Neues oder abgelehnt")
    if not neue:
        for vermerk in vermerke[:10]:
            print(f"  {vermerk['quelle'][:28]:30} {vermerk['ausgang'][:60]}")
        return 0

    neue = neue[:args.hoechstens]
    ziel = ablage.ordner_anlegen(konfig, "rundgang")
    quellenliste: list[dict] = []
    notizen = atome_gesamt = 0

    for nummer, (beitrag, quelle) in enumerate(neue, 1):
        print(f"[{nummer}/{len(neue)}] {quelle.name}: {beitrag.titel[:60]}")
        text, grund = holen.text_holen(beitrag.url, konfig["suche"]["mindestzeichen"])
        gesehen.add(beitrag.url)
        if grund or len(text) < konfig["suche"]["mindestzeichen"]:
            quellenliste.append({"url": beitrag.url, "titel": beitrag.titel,
                                 "ausgang": grund or "zu wenig Text",
                                 "herkunft": quelle.name, "lizenz": quelle.lizenz})
            print(f"      {grund or 'zu wenig Text'}")
            continue

        frage = f"Was ist an '{beitrag.titel}' für ein Multi-Agenten-System mit eigener Wissensbasis brauchbar?"
        inhalt = destillat.destillieren(frage, beitrag.titel, beitrag.url, text, konfig)
        if not inhalt.get("brauchbar", True):
            quellenliste.append({"url": beitrag.url, "titel": beitrag.titel,
                                 "ausgang": "unbrauchbar: " + inhalt.get("grund", ""),
                                 "herkunft": quelle.name, "lizenz": quelle.lizenz})
            print(f"      unbrauchbar: {inhalt.get('grund','')}")
            continue

        thema = ablage.schluessel(quelle.kategorie + " " + (quelle.themen[0] if quelle.themen else ""))
        ablage.notiz_schreiben(ziel, inhalt.get("titel") or beitrag.titel,
                               destillat.notiz_bauen(inhalt, beitrag.url, thema))
        atome = destillat.atome_bauen(inhalt, beitrag.url, beitrag.titel, thema)
        if atome:
            ablage.atome_anhaengen(ziel, atome)
        notizen += 1
        atome_gesamt += len(atome)
        quellenliste.append({"url": beitrag.url, "titel": beitrag.titel,
                             "ausgang": "verwendet", "atome": len(atome),
                             "herkunft": quelle.name, "lizenz": quelle.lizenz,
                             "weg": inhalt.get("weg", "")})
        print(f"      {len(atome)} Atome ({inhalt.get('weg','')})")

    rundgang.gesehen_sichern(gesehen)
    ablage.quellen_schreiben(ziel, quellenliste + vermerke)
    ablage.uebergabe_schreiben(ziel, "Rundgang " + str(__import__("datetime").date.today()),
                               quellenliste, notizen, atome_gesamt)
    ablage.fall_ablegen("Rundgang über den Quellenkatalog", quellenliste,
                        notizen, atome_gesamt, ziel)
    try:
        meldung.melde(art="fund",
                      zusammenfassung=f"Rundgang: {notizen} Notizen, {atome_gesamt} Atome",
                      text="\n".join(f"{q['herkunft']}: {q['titel'][:70]}"
                                     for q in quellenliste if q.get("ausgang") == "verwendet"),
                      daten={"notizen": notizen, "atome": atome_gesamt,
                             "eingang": str(ziel)})
    except Exception:
        pass

    print(f"\n{notizen} Notizen, {atome_gesamt} Atome")
    print(ziel)
    return 0


def befehl_katalog(args) -> int:
    quellen = katalog.laden(nur_aktive=False)
    for quelle in sorted(quellen, key=lambda q: (q.kategorie, q.name)):
        marke = " " if quelle.aktiv else "-"
        print(f"{marke} {quelle.kategorie[:14]:16} {quelle.art:6} {quelle.name[:34]:36} {quelle.url[:56]}")
    print(f"\n{len(quellen)} Quellen, {sum(1 for q in quellen if q.aktiv)} aktiv")
    print("Kategorien: " + ", ".join(katalog.kategorien()))
    return 0

def hauptprogramm(argumente=None) -> int:
    zerleger = argparse.ArgumentParser(prog="deep-researcher", description=__doc__)
    unter = zerleger.add_subparsers(dest="befehl", required=True)

    recherche = unter.add_parser("recherche")
    recherche.add_argument("frage")
    recherche.add_argument("--quellen", type=int, default=8)
    recherche.add_argument("--art", choices=list(ZUSATZ), default="wissen")
    recherche.set_defaults(funktion=befehl_recherche)

    nurfrage = unter.add_parser("frage")
    nurfrage.add_argument("frage")
    nurfrage.add_argument("--quellen", type=int, default=8)
    nurfrage.set_defaults(funktion=befehl_frage)

    unter.add_parser("eingang").set_defaults(funktion=befehl_eingang)

    runde = unter.add_parser("runde")
    runde.add_argument("--kategorie", action="append")
    runde.add_argument("--tage", type=int, default=10)
    runde.add_argument("--je-quelle", type=int, default=2, dest="je_quelle")
    runde.add_argument("--hoechstens", type=int, default=12)
    runde.set_defaults(funktion=befehl_runde)

    unter.add_parser("katalog").set_defaults(funktion=befehl_katalog)

    args = zerleger.parse_args(argumente)
    return args.funktion(args)


if __name__ == "__main__":
    sys.exit(hauptprogramm())