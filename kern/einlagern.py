"""Fuellt die Regale - wiederholbar, fortsetzbar, ohne Doppelungen.

Aufruf (auf Daniels Rechner):
    python einlagern.py stand
    python einlagern.py wissen --hoechstens 800
    python einlagern.py atome
    python einlagern.py bilder
    python einlagern.py bilder --neu        # Regal vorher leeren und neu aufbauen
    python einlagern.py verbesserung
    python einlagern.py recht
    python einlagern.py alles --hoechstens 500

Was schon eingelagert ist, steht in _einlagern.json neben der Datenbank -
je Datei ihr Inhalts-Fingerabdruck. Aendert sich eine Datei, kommt sie neu
hinein; unveraenderte werden uebersprungen. Ein abgebrochener Lauf wird
beim naechsten Aufruf einfach fortgesetzt.

Die grossen Repo-Abzuege (bis 86 MB Quellcode) werden NICHT ganz eingebettet.
Von ihnen kommt der Kopf ins Regal - Steckbrief, Zweck, Architektur - und der
Treffer verweist auf die Datei. Wer tiefer will, liest die Datei.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))

import vektor  # noqa: E402

KOPF_ZEICHEN = 20000      # so viel wird von einer riesigen Datei eingebettet
STAPEL_DATEIEN = 120      # so viele Dateien wandern in einem Zug zur Einbettung
GROSS_AB = 60000          # ab dieser Groesse gilt eine Datei als riesig


def konfiguration() -> dict:
    datei = HIER.parent / "gehirn.json"
    return json.loads(datei.read_text(encoding="utf-8"))


def _merkzettel(pfad: Path) -> Path:
    return pfad.parent / "_einlagern.json"


def _laden(pfad: Path) -> dict:
    zettel = _merkzettel(pfad)
    if zettel.exists():
        try:
            return json.loads(zettel.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def _sichern(pfad: Path, stand: dict) -> None:
    _merkzettel(pfad).write_text(json.dumps(stand, ensure_ascii=False), encoding="utf-8", newline="")


def _fingerabdruck(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()[:16]


def _frontmatter(text: str) -> dict:
    """Liest das, was zwischen den drei Strichen steht - ohne YAML-Paket."""
    if not text.startswith("---"):
        return {}
    ende = text.find("\n---", 3)
    if ende == -1:
        return {}
    felder = {}
    for zeile in text[3:ende].splitlines():
        if ":" not in zeile or zeile.strip().startswith("#"):
            continue
        name, _, wert = zeile.partition(":")
        wert = wert.strip().strip('"').strip("'")
        if wert.startswith("[") and wert.endswith("]"):
            wert = wert[1:-1].replace("'", "").replace('"', "")
        felder[name.strip()] = wert[:500]
    return felder


# ------------------------------------------------------------------ Quellen

def _dateien(ordner: Path, muster: str = "*.md") -> list[Path]:
    return sorted(ordner.rglob(muster)) if ordner.exists() else []


def wissen_quellen(k: dict) -> list[tuple[Path, str]]:
    """Alles Lange: Transkripte, Repo-Steckbriefe, Vault."""
    quellen = []
    for ordner, art in ((Path(k["wissen"]), "wissen"),
                        (Path(k["wissen"]).parent / "repos", "repo"),
                        (Path(k.get("vault", "")) if k.get("vault") else None, "vault")):
        if ordner is None:
            continue
        for datei in _dateien(ordner):
            quellen.append((datei, art))
    return quellen


def einlagern_texte(k: dict, regalname: str, quellen: list[tuple[Path, str]],
                    hoechstens: int) -> tuple[int, int]:
    pfad = Path(k["vektor"])
    stand = _laden(pfad)
    getan = neu_stuecke = 0
    stapel: list = []
    offen: list = []
    for datei, art in quellen:
        if hoechstens and getan >= hoechstens:
            break
        schluessel = str(datei)
        try:
            text = datei.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text.strip():
            continue
        gross = len(text) > GROSS_AB
        haltbar = text[:KOPF_ZEICHEN] if gross else text
        abdruck = _fingerabdruck(haltbar)
        if stand.get(schluessel) == abdruck:
            continue
        felder = _frontmatter(text)
        kennzeichen = {
            "quelle": datei.name,
            "datei": str(datei),
            "art": art,
            "titel": felder.get("title") or felder.get("titel") or datei.stem,
            "typ": felder.get("typ") or felder.get("type") or "",
            "stichworte": felder.get("tags") or felder.get("stichworte") or "",
            "gekuerzt": "ja" if gross else "nein",
            "zeichen_gesamt": len(text),
        }
        stapel.append((haltbar, kennzeichen, schluessel))
        offen.append((schluessel, abdruck))
        getan += 1
        if len(stapel) >= STAPEL_DATEIEN:
            neu_stuecke += _stapel_schreiben(regalname, pfad, stapel, offen, stand)
            print("  %d Dateien, %d Stuecke" % (getan, neu_stuecke), flush=True)
    neu_stuecke += _stapel_schreiben(regalname, pfad, stapel, offen, stand)
    return getan, neu_stuecke


def _stapel_schreiben(regalname: str, pfad: Path, stapel: list, offen: list,
                      stand: dict) -> int:
    """Schreibt den gesammelten Stapel und merkt erst danach, was drin ist."""
    if not stapel:
        return 0
    try:
        neu = vektor.aufnehmen_viele(regalname, pfad, stapel)
    except vektor.NichtBereit as fehler:
        print("Abbruch:", fehler)
        _sichern(pfad, stand)
        raise SystemExit(1)
    except Exception as fehler:
        print("Stapel uebersprungen: %s" % fehler)
        stapel.clear()
        offen.clear()
        return 0
    for schluessel, abdruck in offen:
        stand[schluessel] = abdruck
    _sichern(pfad, stand)
    stapel.clear()
    offen.clear()
    return neu


def einlagern_atome(k: dict, regalname: str, dateien: list[Path],
                    hoechstens: int) -> tuple[int, int]:
    """Eine Zeile einer .jsonl ist ein Stueck - Atome werden nicht zerlegt."""
    pfad = Path(k["vektor"])
    stand = _laden(pfad)
    getan = neu = 0
    stapel: list = []
    offen: list = []
    for datei in dateien:
        if hoechstens and getan >= hoechstens:
            break
        try:
            zeilen = datei.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for nummer, zeile in enumerate(zeilen):
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                satz = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if not isinstance(satz, dict):
                continue
            schluessel = "%s#%d" % (datei, nummer)
            text = _atom_text(satz)
            if not text.strip():
                continue
            abdruck = _fingerabdruck(text)
            if stand.get(schluessel) == abdruck:
                continue
            kennzeichen = {"quelle": datei.name, "datei": str(datei), "zeile": nummer}
            for feld in ("thema", "quelltitel", "sicherheit", "erfasst_von", "erfasst_am",
                         "kit", "stufe", "startwert", "modell", "typ", "erzeugt",
                         "kosten_usd", "groesse"):
                if satz.get(feld) is not None:
                    kennzeichen[feld] = satz[feld]
            if satz.get("datei"):
                kennzeichen["bilddatei"] = satz["datei"]
            stapel.append((text, kennzeichen, schluessel))
            offen.append((schluessel, abdruck))
            getan += 1
            if len(stapel) >= STAPEL_DATEIEN:
                neu += _stapel_schreiben(regalname, pfad, stapel, offen, stand)
        neu += _stapel_schreiben(regalname, pfad, stapel, offen, stand)
        print("  %s: %d Saetze, %d Stuecke" % (datei.name, getan, neu), flush=True)
    _sichern(pfad, stand)
    return getan, neu


def _atom_text(satz: dict) -> str:
    """Ein Atom als lesbarer Satz - so wird eingebettet, was Bedeutung traegt."""
    if satz.get("typ") == "bild":
        return ("Bild fuer das Kit %s, Stufe %s, Modell %s, Startwert %s.\n"
                "Bildauftrag: %s" % (satz.get("kit", ""), satz.get("stufe", ""),
                                     satz.get("modell", ""), satz.get("startwert", ""),
                                     satz.get("auftrag", "")))
    teile = []
    if satz.get("aussage"):
        teile.append(str(satz["aussage"]))
    if satz.get("beleg"):
        teile.append("Beleg: %s" % satz["beleg"])
    if satz.get("thema"):
        teile.append("Thema: %s" % satz["thema"])
    if satz.get("quelltitel"):
        teile.append("Quelle: %s" % satz["quelltitel"])
    return "\n".join(teile) or json.dumps(satz, ensure_ascii=False)


# ------------------------------------------------------------------ Ablauf

def quellen_des_regals(k: dict, regalname: str) -> tuple[list[Path], list[tuple[Path, str]]]:
    """(Atom-Dateien, Text-Quellen) eines Regals - eine Quelle fuer `lauf` und
    `neu_aufbauen`, damit beide nie auseinanderlaufen."""
    gehirn = Path(k["wissen"]).parent
    if regalname == "wissen":
        return [], wissen_quellen(k)
    if regalname == "atome":
        return [d for d in _dateien(Path(k["atome"]), "*.jsonl")
                if d.name != "bilder-kits.jsonl"], []
    if regalname == "bilder":
        return ([d for d in _dateien(Path(k["atome"]), "*.jsonl")
                 if d.name == "bilder-kits.jsonl"],
                [(d, "bildnotiz") for d in _dateien(gehirn / "bilder")])
    if regalname == "verbesserung":
        return [], [(d, "verbesserung") for d in _dateien(Path(k["verbesserung"]))]
    if regalname == "recht":
        return [], [(d, "recht") for d in _dateien(Path(k["recht"]))]
    raise SystemExit("unbekanntes Regal: %s" % regalname)


def ordner_des_regals(k: dict, regalname: str) -> list[Path]:
    """Die Ordner, aus denen ein Regal gefuellt wird. Gebraucht, um beim
    Neuaufbau auch die Fingerabdruecke von Dateien zu vergessen, die es nicht
    mehr gibt - die stehen in keiner Quellenliste mehr."""
    gehirn = Path(k["wissen"]).parent
    if regalname == "wissen":
        return [Path(k["wissen"]), Path(k["wissen"]).parent / "repos", Path(k["vault"])] \
            if k.get("vault") else [Path(k["wissen"]), Path(k["wissen"]).parent / "repos"]
    if regalname in ("atome", "bilder"):
        ordner = [Path(k["atome"])]
        if regalname == "bilder":
            ordner.append(gehirn / "bilder")
        return ordner
    if regalname == "verbesserung":
        return [Path(k["verbesserung"])]
    if regalname == "recht":
        return [Path(k["recht"])]
    raise SystemExit("unbekanntes Regal: %s" % regalname)


def neu_aufbauen(regalname: str) -> None:
    """Baut ein Regal von Grund auf neu.

    Noetig, wenn Dateien geloescht oder umbenannt wurden: der Einlagerer traegt
    nur ein, er raeumt nichts weg. Ohne das bleiben Stuecke zu Dateien im Regal
    stehen, die es laengst nicht mehr gibt - und die Suche findet sie weiter.
    """
    k = konfiguration()
    pfad = Path(k["vektor"])
    try:
        vorher = vektor.regal(regalname, pfad).count()
    except Exception:
        vorher = 0
    try:
        vektor.oeffnen(pfad).delete_collection(regalname)
        vektor._regale.pop(regalname, None)
    except Exception as fehler:
        raise SystemExit("Regal liess sich nicht loeschen: %s" % fehler)
    stand = _laden(pfad)
    ordner = [str(o.resolve()) for o in ordner_des_regals(k, regalname)]
    behalten = {s: a for s, a in stand.items()
                if not any(s.startswith(o) for o in ordner)}
    vergessen = len(stand) - len(behalten)
    _sichern(pfad, behalten)
    print("Regal %s geleert: %d Stuecke weg, %d Fingerabdruecke vergessen"
          % (regalname, vorher, vergessen), flush=True)


def lauf(regalname: str, hoechstens: int) -> None:
    k = konfiguration()
    beginn = time.time()
    atome, texte = quellen_des_regals(k, regalname)
    getan = neu = 0
    if atome:
        getan, neu = einlagern_atome(k, regalname, atome, hoechstens)
    if texte:
        g2, n2 = einlagern_texte(k, regalname, texte, hoechstens)
        getan += g2
        neu += n2

    print("%s: %d Dateien verarbeitet, %d Stuecke neu, %.0f s"
          % (regalname, getan, neu, time.time() - beginn))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("was", choices=["stand", "wissen", "atome", "bilder",
                                   "verbesserung", "recht", "alles"])
    p.add_argument("--hoechstens", type=int, default=0,
                   help="hoechstens so viele Dateien in diesem Lauf (0 = alle)")
    p.add_argument("--neu", action="store_true",
                   help="das Regal vorher leeren und von Grund auf neu aufbauen - "
                        "noetig, wenn Dateien geloescht oder umbenannt wurden")
    a = p.parse_args()
    k = konfiguration()
    if a.was == "stand":
        for name, zahl in vektor.stand(Path(k["vektor"])).items():
            print("%-14s %6d" % (name, zahl))
        return
    ziele = (["atome", "bilder", "verbesserung", "recht", "wissen"]
             if a.was == "alles" else [a.was])
    for name in ziele:
        if a.neu:
            neu_aufbauen(name)
        lauf(name, a.hoechstens)
    print("---")
    for name, zahl in vektor.stand(Path(k["vektor"])).items():
        print("%-14s %6d" % (name, zahl))


if __name__ == "__main__":
    main()
