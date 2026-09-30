"""Was ansteht — aus allen Quellen zusammengetragen.

Der Sekretär arbeitet nicht selbst. Er sieht nach, was die Agenten
hinterlassen haben, und macht daraus eine Vorlage: was Daniel entscheiden
muss, was fällig ist, was gefunden wurde.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import einstellungen as e
import meldung

DRINGEND = {"stoerung", "freigabe", "zustellfehler"}


def _tage_her(roh: str) -> int | None:
    if not roh:
        return None
    try:
        return (date.today() - date.fromisoformat(roh[:10])).days
    except ValueError:
        return None


def _laden(pfad: str):
    datei = Path(pfad)
    if not datei.exists():
        return None
    try:
        return json.loads(datei.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def freigaben(konfig: dict) -> list[dict]:
    """Post, die auf ein Ja wartet."""
    offen: list[dict] = []
    pfad = e.ZUSTAND / "postausgang.jsonl"
    if not pfad.exists():
        return offen
    with pfad.open(encoding="utf-8") as datei:
        for zeile in datei:
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                satz = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if satz.get("zustand") in ("offen", "trocken"):
                offen.append({
                    "art": "freigabe",
                    "von": satz.get("absender_agent", ""),
                    "was": satz.get("betreff", ""),
                    "an": satz.get("an", ""),
                    "zustand": satz.get("zustand"),
                    "vorgang": satz.get("vorgang", ""),
                    "angelegt_am": satz.get("angelegt_am", ""),
                })
    return offen


def fristen(konfig: dict) -> list[dict]:
    """Was liegen bleibt, wenn niemand nachfasst."""
    grenzen = konfig["fristen"]
    faellig: list[dict] = []

    bewerbungen = _laden(konfig["quellen"]["bewerbungen"]) or []
    for eintrag in bewerbungen:
        if eintrag.get("stand") != "beworben":
            continue
        verlauf = eintrag.get("verlauf") or [{}]
        tage = _tage_her(verlauf[-1].get("am", ""))
        if tage is not None and tage >= grenzen["bewerbung_nachfassen_tage"]:
            faellig.append({"art": "nachfassen", "bereich": "bewerbung", "tage": tage,
                            "was": f"{eintrag.get('firma','')} · {eintrag.get('titel','')}",
                            "vorgang": eintrag.get("kennung", "")})

    wohnungen = _laden(konfig["quellen"]["wohnungen"]) or []
    for eintrag in wohnungen:
        if eintrag.get("status") != "angefragt" or not eintrag.get("angefragt_am"):
            continue
        tage = _tage_her(eintrag["angefragt_am"])
        if tage is not None and tage >= grenzen["wohnung_nachfassen_tage"]:
            faellig.append({"art": "nachfassen", "bereich": "wohnung", "tage": tage,
                            "was": eintrag.get("titel", "")[:70],
                            "vorgang": eintrag.get("kennung", "")})

    for wurzel in konfig["quellen"]["eingaenge"]:
        pfad = Path(wurzel)
        if not pfad.exists():
            continue
        for ordner in pfad.iterdir():
            if not ordner.is_dir() or ordner.name == "_erledigt":
                continue
            tage = _tage_her(ordner.name[:10])
            if tage is not None and tage >= grenzen["eingang_liegen_tage"]:
                faellig.append({"art": "liegt", "bereich": "wissen", "tage": tage,
                                "was": f"{pfad.name}/{ordner.name} wartet auf den Kurator",
                                "vorgang": ordner.name})
    return faellig


def meldungen(seit_tagen: int = 2) -> list[dict]:
    grenze = (datetime.now() - timedelta(days=seit_tagen)).strftime("%Y-%m-%dT%H:%M:%S")
    saetze = [s for s in meldung.offene_meldungen() if s.get("gesendet_am", "") >= grenze]
    return saetze


def stoerungen(saetze: list[dict]) -> list[dict]:
    return [s for s in saetze if s.get("art") in DRINGEND]


def abgelehnte_abrufe(seit_tagen: int = 2) -> list[dict]:
    pfad = e.ZUSTAND / "abgelehnt.jsonl"
    if not pfad.exists():
        return []
    grenze = (datetime.now() - timedelta(days=seit_tagen)).strftime("%Y-%m-%dT%H:%M:%S")
    gefunden = []
    with pfad.open(encoding="utf-8") as datei:
        for zeile in datei:
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                satz = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if satz.get("am", "") >= grenze:
                gefunden.append(satz)
    return gefunden