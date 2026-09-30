"""Kurator — Kommandozeile.

Er ist die einzige Stelle, die in die Säulen des 2nd brain schreibt.
Alles andere liefert an, er prüft und pflegt ein.

  python main.py eingaenge              was bereitliegt
  python main.py pruefen <ordner>       prüfen, ohne einzupflegen
  python main.py einpflegen <ordner>    einen Eingang übernehmen
  python main.py einpflegen --alle      alles Bereitliegende
  python main.py stand                  was in den Säulen liegt
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import einstellungen
import meldung
import pruefung
from vektor import Vektorsaeule

AGENT = "kurator"


def _konfig() -> dict:
    einstellungen.ordner_anlegen()
    return einstellungen.laden()


def _eingangsordner(konfig: dict) -> list[Path]:
    gefunden: list[Path] = []
    for wurzel in konfig["eingaenge"]:
        pfad = Path(wurzel)
        if not pfad.exists():
            continue
        for ordner in sorted(pfad.iterdir()):
            # Ordner mit Unterstrich sind Verwaltung, keine Lieferung:
            # `_erledigt` (abgearbeitet), `_neu` und `_verarbeitet` (Ablegeordner
            # des Dokumentwandlers). Sie duerfen nie als Eingang gelten.
            if ordner.is_dir() and not ordner.name.startswith("_"):
                gefunden.append(ordner)
    return gefunden


def _zaehlen(eingang: Path) -> tuple[int, int, str]:
    notizen = len(list((eingang / "wissen").glob("*.md"))) if (eingang / "wissen").exists() else 0
    atomdatei = eingang / "atome.jsonl"
    atome = sum(1 for _ in atomdatei.open(encoding="utf-8")) if atomdatei.exists() else 0
    von = ""
    uebergabe = eingang / "UEBERGABE.md"
    if uebergabe.exists():
        von = pruefung.kopf_lesen(uebergabe.read_text(encoding="utf-8")).get("von", "")
    return notizen, atome, von


def befehl_eingaenge(args) -> int:
    konfig = _konfig()
    ordner = _eingangsordner(konfig)
    if not ordner:
        print("Nichts bereitliegend.")
        return 0
    for eingang in ordner:
        notizen, atome, von = _zaehlen(eingang)
        print(f"{eingang.parent.name:16} {eingang.name[:44]:46} {von:16} "
              f"{notizen:3} Notizen {atome:5} Atome")
    print(f"\n{len(ordner)} Eingänge")
    return 0


def _erste_quelle(text: str) -> str:
    treffer = re.search(r"https?://\S+", text[:1500])
    return treffer.group(0).rstrip(").,") if treffer else ""


def _durchgehen(eingang: Path, konfig: dict, bestand: pruefung.Bestand,
                saeule, nur_pruefen: bool) -> dict:
    regeln = konfig["pruefung"]
    ziel_wissen = Path(konfig["saeulen"]["wissen"])
    ziel_atome = Path(konfig["saeulen"]["atome"])
    zahlen = {"notizen": 0, "notizen_abgelehnt": 0, "atome": 0,
              "atome_abgelehnt": 0, "haeppchen": 0}
    vermerke: list[str] = []

    notizen_ordner = eingang / "wissen"
    for datei in sorted(notizen_ordner.glob("*.md")) if notizen_ordner.exists() else []:
        text = datei.read_text(encoding="utf-8", errors="ignore")
        befund = pruefung.notiz_pruefen(text, regeln, datei.name)
        doppelt = bestand.kennt_notiz(text)
        if not befund.ok or doppelt:
            zahlen["notizen_abgelehnt"] += 1
            gruende = befund.gruende + ([doppelt] if doppelt else [])
            vermerke.append(f"{datei.name}: " + ", ".join(gruende))
            continue
        if not nur_pruefen:
            ziel_wissen.mkdir(parents=True, exist_ok=True)
            ziel = ziel_wissen / datei.name
            if ziel.exists():
                ziel = ziel_wissen / f"{datei.stem}_{date.today().isoformat()}.md"
            shutil.copy2(datei, ziel)
            bestand.merken_notiz(text)
            if saeule is not None:
                kopf = pruefung.kopf_lesen(text)
                zahlen["haeppchen"] += saeule.aufnehmen(text, {
                    "titel": kopf.get("title", datei.stem),
                    "quelle": _erste_quelle(text),
                    "typ": kopf.get("typ", "tech-wissen"),
                    "thema": kopf.get("thema", ""),
                    "erfasst_von": kopf.get("erfasst_von", ""),
                    "datei": ziel.name,
                })
        zahlen["notizen"] += 1

    atomdatei = eingang / "atome.jsonl"
    if atomdatei.exists():
        gute: list[dict] = []
        with atomdatei.open(encoding="utf-8") as offen:
            for zeile in offen:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    atom = json.loads(zeile)
                except json.JSONDecodeError:
                    zahlen["atome_abgelehnt"] += 1
                    continue
                befund = pruefung.atom_pruefen(atom, regeln)
                if not befund.ok or bestand.kennt_atom(atom):
                    zahlen["atome_abgelehnt"] += 1
                    continue
                gute.append(atom)
                bestand.merken_atom(atom)
        if gute and not nur_pruefen:
            ziel_atome.mkdir(parents=True, exist_ok=True)
            nach_thema: dict[str, list[dict]] = {}
            for atom in gute:
                nach_thema.setdefault(atom.get("thema") or "ohne-thema", []).append(atom)
            for thema, teile in nach_thema.items():
                with (ziel_atome / f"{thema}.jsonl").open("a", encoding="utf-8") as offen:
                    for atom in teile:
                        offen.write(json.dumps(atom, ensure_ascii=False) + "\n")
        zahlen["atome"] += len(gute)

    return {"zahlen": zahlen, "vermerke": vermerke}


def befehl_pruefen(args) -> int:
    return _arbeiten(args, nur_pruefen=True)


def befehl_einpflegen(args) -> int:
    return _arbeiten(args, nur_pruefen=False)


def _arbeiten(args, nur_pruefen: bool) -> int:
    konfig = _konfig()
    alle = _eingangsordner(konfig)
    if getattr(args, "ordner", None):
        gewaehlt = [o for o in alle if args.ordner in o.name or args.ordner == str(o)]
        if not gewaehlt:
            print(f"Kein Eingang zu '{args.ordner}'.")
            return 1
    elif getattr(args, "alle", False):
        gewaehlt = alle
    else:
        print("Entweder einen Ordner nennen oder --alle.")
        return 1
    if not gewaehlt:
        print("Nichts bereitliegend.")
        return 0

    bestand = pruefung.Bestand(Path(konfig["saeulen"]["wissen"]),
                               Path(konfig["saeulen"]["atome"]))
    saeule = None
    if not nur_pruefen:
        saeule = Vektorsaeule(konfig)
        if not saeule.bereit():
            print(f"Vektorsäule nicht bespielt: {saeule.grund}")
            saeule = None

    gesamt = {"notizen": 0, "notizen_abgelehnt": 0, "atome": 0,
              "atome_abgelehnt": 0, "haeppchen": 0}
    for eingang in gewaehlt:
        ergebnis = _durchgehen(eingang, konfig, bestand, saeule, nur_pruefen)
        zahlen = ergebnis["zahlen"]
        for schluessel, wert in zahlen.items():
            gesamt[schluessel] += wert
        print(f"{eingang.name[:48]:50} {zahlen['notizen']:3} Notizen "
              f"({zahlen['notizen_abgelehnt']} abgelehnt), {zahlen['atome']:4} Atome "
              f"({zahlen['atome_abgelehnt']} abgelehnt)")
        for vermerk in ergebnis["vermerke"][:5]:
            print(f"    {vermerk[:100]}")
        if not nur_pruefen:
            _abschliessen(eingang, zahlen)

    art = "geprüft" if nur_pruefen else "eingepflegt"
    zusatz = (f", {gesamt['haeppchen']} Häppchen in der Vektorsäule"
              if gesamt["haeppchen"] else "")
    print(f"\n{art}: {gesamt['notizen']} Notizen, {gesamt['atome']} Atome{zusatz}")

    if not nur_pruefen and konfig.get("melden") and (gesamt["notizen"] or gesamt["atome"]):
        meldung.melde(
            absender=AGENT, art="wissen",
            zusammenfassung=f"{gesamt['notizen']} Notizen und {gesamt['atome']} Atome "
                            "ins 2nd brain übernommen",
            text="\n".join(f"{o.parent.name}/{o.name}" for o in gewaehlt),
            daten=gesamt)
    return 0


def _abschliessen(eingang: Path, zahlen: dict) -> None:
    uebergabe = eingang / "UEBERGABE.md"
    if uebergabe.exists():
        text = uebergabe.read_text(encoding="utf-8")
        text = text.replace("status: offen", "status: eingepflegt")
        text += (f"\n\n## Eingepflegt am {date.today().isoformat()}\n"
                 f"- Notizen übernommen: {zahlen['notizen']} "
                 f"(abgelehnt: {zahlen['notizen_abgelehnt']})\n"
                 f"- Atome übernommen: {zahlen['atome']} "
                 f"(abgelehnt: {zahlen['atome_abgelehnt']})\n"
                 f"- Häppchen in der Vektorsäule: {zahlen['haeppchen']}\n")
        uebergabe.write_text(text, encoding="utf-8", newline="")
    erledigt = eingang.parent / "_erledigt"
    erledigt.mkdir(parents=True, exist_ok=True)
    ziel = erledigt / eingang.name
    if ziel.exists():
        ziel = erledigt / f"{eingang.name}_{date.today().isoformat()}"
    try:
        shutil.move(str(eingang), str(ziel))
    except OSError:
        pass


def befehl_stand(args) -> int:
    konfig = _konfig()
    saeulen = konfig["saeulen"]
    wissen = Path(saeulen["wissen"])
    atome = Path(saeulen["atome"])
    anzahl_notizen = len(list(wissen.rglob("*.md"))) if wissen.exists() else 0
    anzahl_atome = 0
    if atome.exists():
        for datei in atome.rglob("*.jsonl"):
            anzahl_atome += sum(1 for _ in datei.open(encoding="utf-8"))
    saeule = Vektorsaeule(konfig)
    vektor = saeule.anzahl() if saeule.bereit() else -1

    print(f"Säule 1  Wissen        {anzahl_notizen:6} Notizen   {wissen}")
    if vektor >= 0:
        print(f"Säule 2  Vektor        {vektor:6} Häppchen  {saeulen['vektor']}")
    else:
        print(f"Säule 2  Vektor             — {saeule.grund}")
    print(f"Säule 3  Atome         {anzahl_atome:6} Aussagen  {atome}")
    verbesserung = Path(saeulen["verbesserung"])
    faelle = len(list(verbesserung.rglob("*.md"))) if verbesserung.exists() else 0
    print(f"Säule 4  Verbesserung  {faelle:6} Fälle     {verbesserung}")
    print()
    return befehl_eingaenge(args)


def hauptprogramm(argumente=None) -> int:
    zerleger = argparse.ArgumentParser(prog="kurator", description=__doc__)
    unter = zerleger.add_subparsers(dest="befehl", required=True)

    unter.add_parser("eingaenge").set_defaults(funktion=befehl_eingaenge)
    unter.add_parser("stand").set_defaults(funktion=befehl_stand)

    for name, funktion in (("pruefen", befehl_pruefen), ("einpflegen", befehl_einpflegen)):
        teil = unter.add_parser(name)
        teil.add_argument("ordner", nargs="?")
        teil.add_argument("--alle", action="store_true")
        teil.set_defaults(funktion=funktion)

    args = zerleger.parse_args(argumente)
    return args.funktion(args)


if __name__ == "__main__":
    sys.exit(hauptprogramm())