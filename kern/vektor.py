"""Die Vektorschicht des Universe - eine Datenbank, mehrere Regale.

Ein Regal ist eine Chroma-Sammlung. Alle Regale liegen in derselben Datenbank
und benutzen dasselbe Einbettungsmodell (text-embedding-3-small, 1536 Werte).
Wer hier ein anderes Modell eintraegt, macht den vorhandenen Bestand
unbrauchbar - die Abstaende waeren nicht mehr vergleichbar.

Regale:
  wissen        Transkripte, Repo-Steckbriefe, alles Lange
  atome         belegte Einzelaussagen
  bilder        jedes erzeugte Bild mit Auftrag, Startwert, Modell, Preis
  verbesserung  was aus Durchlaeufen gelernt wurde
  persoenlich   Daten eines einzelnen Nutzers, immer mit Feld 'besitzer'
  erfahrungen   was ein Auftrag gelehrt hat - Urteil, Grund, Kennzahlen
  lehrsaetze    bestaetigte Dauerregeln, aus wiederholten Urteilen gewonnen
  recht         geltendes Recht je Rechtsquelle, mit gilt_ab und ersetzt

Die Frage wird einmal eingebettet und gemerkt: dieselbe Frage kostet nur
einmal, egal wie viele Regale sie durchsucht.
"""
from __future__ import annotations

import hashlib
import os
import re
import time
from pathlib import Path

MODELL = "text-embedding-3-small"
DIMENSIONEN = 1536
REGALE = ("wissen", "atome", "bilder", "verbesserung", "persoenlich",
          "erfahrungen", "lehrsaetze", "recht")

_kunde = None
_regale: dict[str, object] = {}
_fragen: dict[str, list[float]] = {}


class NichtBereit(RuntimeError):
    """Etwas fehlt - Schluessel, Paket oder Ordner."""


# ------------------------------------------------------------------ Zerlegen

def haeppchen(text: str, zeichen: int = 1800, ueberlappung: int = 250) -> list[str]:
    """Zerlegt entlang der Absaetze, nicht mitten im Satz."""
    text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    if len(text) <= zeichen:
        return [text] if text else []
    stuecke: list[str] = []
    anfang = 0
    while anfang < len(text):
        ende = min(anfang + zeichen, len(text))
        if ende < len(text):
            schnitt = text.rfind("\n\n", anfang + zeichen // 2, ende)
            if schnitt == -1:
                schnitt = text.rfind(". ", anfang + zeichen // 2, ende)
            if schnitt != -1:
                ende = schnitt + 1
        stueck = text[anfang:ende].strip()
        if stueck:
            stuecke.append(stueck)
        if ende >= len(text):
            break
        anfang = max(ende - ueberlappung, anfang + 1)
    return stuecke


# ------------------------------------------------------------------ Datenbank

def oeffnen(pfad: str | Path):
    global _kunde
    if _kunde is None:
        try:
            import chromadb
        except ImportError as fehler:
            raise NichtBereit("Paket fehlt: %s" % fehler.name) from fehler
        ordner = Path(pfad)
        ordner.mkdir(parents=True, exist_ok=True)
        _kunde = chromadb.PersistentClient(path=str(ordner))
    return _kunde


def regal(name: str, pfad: str | Path):
    """Liefert das Regal und legt es an, wenn es noch nicht da ist."""
    if name not in REGALE:
        raise ValueError("unbekanntes Regal: %s" % name)
    if name not in _regale:
        _regale[name] = oeffnen(pfad).get_or_create_collection(
            name, metadata={"hnsw:space": "cosine",
                            "modell": MODELL, "dim": str(DIMENSIONEN)})
    return _regale[name]


# ------------------------------------------------------------------ Einbetten

def _schluessel_holen() -> str | None:
    """Der Schluessel steht in der .env - die wird hier geladen, damit ein
    Aufruf von Hand denselben Weg nimmt wie ein Lauf aus dem Universe."""
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    try:
        import umgebung
        umgebung.laden()
    except Exception:
        for zeile in _env_zeilen():
            if zeile.startswith("OPENAI_API_KEY"):
                os.environ["OPENAI_API_KEY"] = zeile.split("=", 1)[1].strip().strip('"').strip("'")
                break
    return os.environ.get("OPENAI_API_KEY")


def _env_zeilen() -> list[str]:
    datei = Path(r"C:\AI_Projekte\Neustart\.env")
    if not datei.exists():
        return []
    try:
        return datei.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def _openai():
    schluessel = _schluessel_holen()
    if not schluessel:
        raise NichtBereit("OPENAI_API_KEY fehlt")
    try:
        import openai
    except ImportError as fehler:
        raise NichtBereit("Paket fehlt: %s" % fehler.name) from fehler
    return openai.OpenAI(api_key=schluessel)


#: Auf welche Kostenstelle Einbettungen laufen, wenn niemand etwas sagt.
#: Wer es genauer will, setzt vektor.KOSTENSTELLE vor dem Aufruf.
KOSTENSTELLE = "wissen"


def einbetten(texte: list[str], stapel: int = 128) -> list[list[float]]:
    """Bettet in Stapeln ein und wiederholt bei Netzfehlern.

    Jeder Stapel wird verbucht. Ohne Buchung kann der Controller nicht
    zaehlen, was hier ausgegeben wird - und Einbettungen sind die einzige
    Stelle, an der der Kern von selbst Geld ausgibt."""
    if not texte:
        return []
    kunde = _openai()
    ergebnis: list[list[float]] = []
    for anfang in range(0, len(texte), stapel):
        teil = [t[:8000] for t in texte[anfang:anfang + stapel]]
        for versuch in range(4):
            try:
                antwort = kunde.embeddings.create(model=MODELL, input=teil)
                ergebnis.extend(eintrag.embedding for eintrag in antwort.data)
                _buchen(len(teil))
                break
            except Exception:
                if versuch == 3:
                    raise
                time.sleep(2 * (versuch + 1))
    return ergebnis


def _buchen(stueck: int) -> None:
    """Nie eine Ausnahme nach aussen - eine verlorene Buchung ist besser
    als eine abgebrochene Einlagerung."""
    try:
        import verbrauch

        verbrauch.fuer_modell(KOSTENSTELLE, MODELL, stueck,
                              wofuer="Einbettung")
    except Exception:
        pass


def frage_einbetten(frage: str) -> list[float]:
    """Bettet eine Frage ein - und merkt sie sich fuer den Rest des Laufs."""
    schluessel = hashlib.sha1(frage.strip().lower().encode()).hexdigest()
    if schluessel not in _fragen:
        _fragen[schluessel] = einbetten([frage])[0]
    return _fragen[schluessel]


# ------------------------------------------------------------------ Schreiben

def aufnehmen(name: str, pfad: str | Path, text: str, kennzeichen: dict,
              quelle: str = "", zeichen: int = 1800) -> int:
    """Legt einen Text zerlegt ins Regal. Schon Vorhandenes wird uebergangen."""
    stuecke = haeppchen(text, zeichen)
    if not stuecke:
        return 0
    grund = quelle or kennzeichen.get("quelle") or kennzeichen.get("titel") or ""
    kennungen = [hashlib.sha1(("%s|%d|%s" % (grund, nr, s[:80])).encode()).hexdigest()
                 for nr, s in enumerate(stuecke)]
    fach = regal(name, pfad)
    vorhanden: set[str] = set()
    try:
        vorhanden = set(fach.get(ids=kennungen).get("ids", []))
    except Exception:
        pass
    neu = [(k, s) for k, s in zip(kennungen, stuecke) if k not in vorhanden]
    if not neu:
        return 0
    marken = {k: ("" if v is None else str(v)[:500]) for k, v in kennzeichen.items()}
    fach.add(ids=[k for k, _ in neu],
             documents=[s for _, s in neu],
             embeddings=einbetten([s for _, s in neu]),
             metadatas=[dict(marken) for _ in neu])
    return len(neu)


# ------------------------------------------------------------------ Suchen

def aufnehmen_viele(name: str, pfad: str | Path,
                    posten: list[tuple[str, dict, str]],
                    zeichen: int = 1800) -> int:
    """Nimmt viele Texte in einem Zug auf.

    posten: (text, kennzeichen, quelle) je Eintrag.

    Der Unterschied zu aufnehmen(): hier wird ueber alle Texte hinweg
    gebuendelt. Eine Anfrage bettet die Stuecke aus hundert Dateien
    gemeinsam ein statt hundert Anfragen zu stellen - das ist der
    Unterschied zwischen Minuten und Stunden."""
    fach = regal(name, pfad)
    kennungen: list[str] = []
    stuecke: list[str] = []
    marken: list[dict] = []
    for text, kennzeichen, quelle in posten:
        teile = haeppchen(text, zeichen)
        marke = {k: ("" if v is None else str(v)[:500]) for k, v in kennzeichen.items()}
        for nr, stueck in enumerate(teile):
            kennungen.append(hashlib.sha1(
                ("%s|%d|%s" % (quelle, nr, stueck[:80])).encode()).hexdigest())
            stuecke.append(stueck)
            marken.append(dict(marke))
    if not stuecke:
        return 0

    vorhanden: set[str] = set()
    for anfang in range(0, len(kennungen), 500):
        try:
            treffer = fach.get(ids=kennungen[anfang:anfang + 500])
            vorhanden.update(treffer.get("ids", []))
        except Exception:
            pass

    gesehen: set[str] = set()
    frisch = []
    for kennung, stueck, marke in zip(kennungen, stuecke, marken):
        if kennung in vorhanden or kennung in gesehen:
            continue
        gesehen.add(kennung)
        frisch.append((kennung, stueck, marke))
    if not frisch:
        return 0

    for anfang in range(0, len(frisch), 256):
        block = frisch[anfang:anfang + 256]
        fach.add(ids=[k for k, _, _ in block],
                 documents=[s for _, s, _ in block],
                 embeddings=einbetten([s for _, s, _ in block]),
                 metadatas=[m for _, _, m in block])
    return len(frisch)


def suchen(name: str, pfad: str | Path, frage: str, anzahl: int = 4,
           wo: dict | None = None) -> list[dict]:
    """Sucht in einem Regal. 'wo' filtert vorab ueber die Merkmale - das ist
    billig und schneidet die teure Aehnlichkeitssuche klein."""
    try:
        fach = regal(name, pfad)
        if fach.count() == 0:
            return []
        antwort = fach.query(query_embeddings=[frage_einbetten(frage)],
                             n_results=anzahl, where=wo or None)
    except NichtBereit:
        raise
    except Exception:
        return []
    treffer = []
    belege = (antwort.get("documents") or [[]])[0]
    marken = (antwort.get("metadatas") or [[]])[0]
    abstaende = (antwort.get("distances") or [[]])[0]
    for stelle, beleg in enumerate(belege):
        marke = marken[stelle] if stelle < len(marken) and isinstance(marken[stelle], dict) else {}
        treffer.append({
            "regal": name,
            "text": beleg,
            "quelle": marke.get("quelle") or marke.get("datei") or marke.get("titel") or "",
            "merkmale": marke,
            "naehe": round(1 - abstaende[stelle], 4) if stelle < len(abstaende) else None,
        })
    return treffer


def stand(pfad: str | Path) -> dict[str, int]:
    """Wie viele Stuecke liegen in welchem Regal."""
    zahlen = {}
    for name in REGALE:
        try:
            zahlen[name] = regal(name, pfad).count()
        except Exception:
            zahlen[name] = 0
    return zahlen
