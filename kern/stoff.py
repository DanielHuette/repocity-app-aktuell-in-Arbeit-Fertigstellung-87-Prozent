"""Stoff fuer die kreativen Strassen - die eine Tuer zum Kurator.

Keine Strasse baut sich ihren eigenen Weg in die Datenbank. Sie ruft hier an,
und hier wird der Kurator gefragt: er hat eingepflegt, er weiss, was drinsteht,
er gibt heraus.

    import stoff
    s = stoff.holen(auftrag, modul="prod.praesentation", braucht=("text", "bilder"))
    s.kontext        was der Agent seinem Modell mitgibt
    s.bilder         Bilder aus dem Regal
    s.deckung.satz   ein Satz im Klartext, wie gut das Thema gedeckt ist
    s.empfehlung     "bauen" | "netz" | "nachfragen"

Nur die kreativen Strassen holen hier Stoff - was zur Lebensverwaltung gehoert
(Post, Wohnung, Bewerbung, Kalender) hat eigene Quellen und bleibt unberuehrt.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

KERN = Path(__file__).resolve().parent
UNIVERSE = KERN.parent
VERSORGEN = UNIVERSE / "kurator" / "versorgen.py"
SPRACHE = UNIVERSE / "marke" / "sprache.py"
DIAGRAMME = UNIVERSE / "marke" / "diagramme.py"

# Wer immer Schaubilder baut, bekommt die Bauregeln ungefragt mit. Genannt hat
# sie Daniel am 13.09.2026: Lernprogramme, Praesentationen, Videos, die
# Kennzahlentafeln auf Webseite und in der App, und die Handelsschaubilder.
SCHAUBILD_MODULE = (
    "prod.lernprogramm", "prod.praesentation", "prod.video", "prod.dashboard",
    "prod.webseite", "prod.app", "handel",
)


def _modul_laden(name: str, datei: Path):
    fertig = sys.modules.get(name)
    if fertig is not None:
        return fertig
    if not datei.exists():
        return None
    try:
        beschreibung = importlib.util.spec_from_file_location(name, datei)
        modul = importlib.util.module_from_spec(beschreibung)
        sys.modules[name] = modul
        beschreibung.loader.exec_module(modul)
        return modul
    except Exception:
        return None


def braucht_schaubild(modul: str, auftragstext: str = "") -> bool:
    """Ob dieser Auftrag die Schaubildregeln braucht.

    Zwei Wege: das Modul gehoert zu den Bereichen, die immer Schaubilder bauen,
    oder im Auftragstext steht, dass eins gewuenscht ist. Der zweite Weg deckt
    den Einzelfall ab, ohne dass jede Strasse in die Liste muss.
    """
    if str(modul or "").startswith(SCHAUBILD_MODULE):
        return True
    text = str(auftragstext or "").lower()
    return any(w in text for w in ("diagramm", "schaubild", "grafik", "chart",
                                   "ablaufplan", "schema", "kennzahlentafel"))


def _sprache():
    """Die Sprachregeln laden - ueber den Pfad, wie alles hier.

    Warum sie an dieser Stelle stehen: `als_anweisung` ist die eine Tuer, durch
    die jede kreative Strasse ihre Frage ans Modell baut. Wer die Regeln hier
    anhaengt, erreicht alle - ohne dass eine Strasse ihre eigene Fassung erfindet.
    """
    return _modul_laden("marke_sprache", SPRACHE)


def _diagramme():
    """Die Bauregeln fuer Schaubilder - dieselbe Tuer, dieselbe Begruendung."""
    return _modul_laden("marke_diagramme", DIAGRAMME)

# Wer hier Stoff holt: alles, was produziert. Die Lebensverwaltung nicht.
KREATIVE_STAEMME = ("prod.",)


def ist_kreativ(modul: str) -> bool:
    return str(modul or "").startswith(KREATIVE_STAEMME)


def _kurator():
    """Den Kurator laden, ohne ihn zu importieren wie ein Paket.

    Sein Ordner heisst wie sein Modul, und darin liegt eine eigene gehirn.py -
    ein normaler Import wuerde die falsche erwischen.
    """
    fertig = sys.modules.get("kurator_versorgen")
    if fertig is not None:
        return fertig
    if not VERSORGEN.exists():
        return None
    beschreibung = importlib.util.spec_from_file_location(
        "kurator_versorgen", VERSORGEN)
    modul = importlib.util.module_from_spec(beschreibung)
    sys.modules["kurator_versorgen"] = modul
    beschreibung.loader.exec_module(modul)
    return modul


def holen(auftrag: dict, modul: str = "", braucht: tuple = ("text",),
          kit: str = ""):
    """Stoff zu diesem Auftrag - oder None, wenn der Kurator nicht da ist."""
    k = _kurator()
    if k is None:
        return None
    try:
        return k.versorge(auftrag, modul=modul, braucht=braucht, kit=kit)
    except Exception:
        return None


def als_auftragsfeld(stoff) -> dict:
    """Was in den Auftrag geschrieben wird, damit die Strasse es vorfindet.

    Absichtlich klein: Text und Zahlen, keine Objekte. Der Auftrag wandert
    als JSON durch den Eingang einer Strasse.
    """
    if stoff is None:
        return {}
    return {
        "kontext": stoff.kontext,
        "bilder": [
            b if isinstance(b, dict)
            else {"quelle": getattr(b, "quelle", "") or "",
                  "text": (getattr(b, "text", "") or "")[:300]}
            for b in (stoff.bilder or [])
        ],
        "stuecke": [
            {"kennung": s.get("kennung", ""), "titel": s.get("titel", ""),
             "datei": s.get("datei", "")}
            for s in (stoff.stuecke or [])
        ],
        "verbotsliste": stoff.verbotsliste,
        # Nur ein Schalter, nicht der ganze Text: der Auftrag wandert als JSON
        # durch den Eingang, und fuenf Kilobyte Regeln in jedem Auftrag waeren
        # Ballast. Den Text baut `als_anweisung` beim Fragen.
        "sprachregeln": True,
        "schaubildregeln": braucht_schaubild(stoff.modul, stoff.frage),
        "deckung": stoff.deckung.stufe,
        "deckung_satz": stoff.deckung.satz,
        "funde": stoff.deckung.funde,
        "brauchbare": stoff.deckung.brauchbare,
        "quellen": stoff.quellen,
        "empfehlung": stoff.empfehlung,
    }


def als_anweisung(feld) -> str:
    """Der Stoff als Block fuer die Frage an ein Sprachmodell.

    Jede kreative Strasse fragt irgendwann ein Modell. Damit alle dasselbe
    mitgeben - und niemand seine eigene Fassung erfindet - steht der Block
    hier, an einer Stelle.

    Nimmt den Stoff selbst oder das Feld, das im Auftrag steht. Ist nichts
    da, kommt ein leerer Text zurueck; dann fragt die Strasse wie bisher.
    """
    if feld is None:
        return ""
    if not isinstance(feld, dict):
        feld = als_auftragsfeld(feld)
    if not feld:
        return ""

    zeilen = []
    kontext = str(feld.get("kontext") or "").strip()
    if kontext:
        zeilen += ["Das steht bei uns schon zu diesem Thema. Nimm es als "
                   "Grundlage und erfinde nichts dazu:", "", kontext]

    quellen = [str(q) for q in (feld.get("quellen") or []) if q]
    if quellen:
        zeilen += ["", "Herkunft: " + ", ".join(quellen[:8])]

    # Die Deckung sagt der Strasse, wie fest der Boden ist, auf dem sie baut.
    stufe = str(feld.get("deckung") or "")
    satz = str(feld.get("deckung_satz") or "").strip()
    if satz:
        zeilen += ["", "Deckung: " + satz]
    if stufe == "duenn":
        zeilen += ["Schreibe entsprechend vorsichtig: keine Zahlen und keine "
                   "Behauptungen, die nicht oben stehen."]
    elif stufe == "leer":
        zeilen += ["Wir haben dazu nichts. Bleib allgemein, nenne keine Zahlen "
                   "und keine Namen, die nicht im Auftrag stehen."]

    verboten = [str(w) for w in (feld.get("verbotsliste") or []) if w]
    if verboten:
        zeilen += ["", "Diese Woerter kommen nicht vor: " + ", ".join(verboten)]

    if feld.get("sprachregeln", True):
        s = _sprache()
        if s is not None:
            zeilen += ["", s.als_regeln(kurz=bool(feld.get("sprachregeln_kurz")))]

    if feld.get("schaubildregeln"):
        d = _diagramme()
        if d is not None:
            zeilen += ["", d.regeln(str(feld.get("schaubildart") or ""),
                                    str(feld.get("kit") or ""))]

    return "\n".join(zeilen).strip()


def aus_auftrag(satz) -> dict:
    """Das Stofffeld aus einem Auftrag holen - Dict wie Objekt.

    Der Verteiler schreibt es unter "stoff" in den Auftrag. Wer den Auftrag
    als Objekt bekommt, findet es unter demselben Namen.
    """
    if satz is None:
        return {}
    if isinstance(satz, dict):
        feld = satz.get("stoff")
    else:
        feld = getattr(satz, "stoff", None)
    return feld if isinstance(feld, dict) else {}


def netz_vorschlag(stoff) -> dict:
    k = _kurator()
    if k is None or stoff is None:
        return {}
    try:
        return k.netz_vorschlagen(stoff)
    except Exception:
        return {}
