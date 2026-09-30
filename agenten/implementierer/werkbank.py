"""Die Werkbank - hier wird gebaut, und zwar neben dem Universe.

Der wichtigste Satz dieser Datei: **es wird nie in das laufende Universe
geschrieben.** Gebaut wird in universe/zustand/bau/<auftrag>/neu/. Erst
ein eigener Befehl uebernimmt das Ergebnis, und der legt vorher eine
Sicherung an.

Das ist keine Vorsicht um der Vorsicht willen. Ein Agent, der sich selbst
aendern darf, waehrend er laeuft, kann sich in einen Zustand bringen, aus
dem heraus er den Fehler nicht mehr melden kann - und dann steht das
Universe still, ohne dass jemand erfaehrt warum.

Was hier gemessen wird, kostet nichts und ist echt:

    uebersetzt      laeuft jede .py durch den Uebersetzer
    zeilen          wieviel wirklich entstanden ist
    pruefungen      die pruefungen.py des Bauplans, falls es eine gibt

Das Ergebnis steht in pruefbericht.json. Der Qualitaetsmanager liest ihn
und laesst nichts durch, was nicht uebersetzt oder was rote Pruefungen
hat.
"""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import re
import shutil
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
import tempfile
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"

for _p in (str(KERN),):
    if _p not in sys.path:
        sys.path.append(_p)

MODUL = "prod.app"
import modellwahl  # noqa: E402  - das eine Modell des Universe
MODELL = modellwahl.MODELL

#: Was eine einzelne Datei voraussichtlich kostet - gerechnet, nicht
#: geraten: rund 600 Token hinein, 1500 hinaus, mit Opus 5 (5,00 / 25,00 USD
#: je Million, Listenpreis 11.09.2026): (600 x 5 + 1500 x 25) / 1e6 =
#: 0,0405 USD x 0,92 = 0,0373 EUR. Aufgerundet auf 0,04 EUR. Ein Bau mit den
#: hoechstens zwoelf Dateien eines Bauplans landet damit bei rund 48 Cent.
#:
#: Die Obergrenze steht bewusst NICHT hier. Sie ist die Marke, die der
#: Nutzer fuer den Topf 'denken' setzt (verbrauch.marke) - ohne Marke sagt
#: die Bremse ja, so ist es entschieden. Der Agent schaetzt nur seinen
#: naechsten Schritt, die Decke gehoert dem Controller. Vorher
#: stand hier 0,60 EUR und wurde als ganzer Betrag angefragt: das liegt
#: ueber dem Lauf-Deckel, und die Reissleine haette jeden Bau abgelehnt,
#: bevor die erste Datei entsteht.
KOSTEN_JE_DATEI_EUR = 0.04

#: Eine einzelne Datei bleibt ueberschaubar - sonst ist der Plan zu grob.
ZEILEN_HOECHSTENS = 600

#: Wie lange eine Pruefung laufen darf, bevor sie abgebrochen wird.
ZEITGRENZE_SEK = 300


# ------------------------------------------------------------------ Ordner

#: Die Regel, wie aus einer Hub-Kennung ein Name wird, steht in
#: kern/kennung.py und nur dort. Sie stand am 09.09.2026 an fuenf Stellen -
#: und galt an den Stellen, wo sie fehlte, eben nicht: die Werkstaetten
#: bauten ihren Arbeitsordner aus der rohen Kennung und brachen bei jedem
#: echten Auftrag mit "Der Verzeichnisname ist ungueltig" ab.
_kennung_modul = None


def _kennung():
    """Immer die echte kern/kennung.py, neben diesem Ordner.

    Nicht ueber ``UNIVERSE``: das verstellen die Pruefungen auf einen
    Wegwerf-Ordner, in dem es keinen Kern gibt. Und erst nach dem Laden
    gemerkt - sonst bliebe ein halb geladenes Modul haengen und jede
    weitere Pruefung scheiterte an etwas anderem als der Ursache. Beides
    am 09.09. im Pruefstand aufgefallen.
    """
    global _kennung_modul
    if _kennung_modul is None:
        import importlib.util
        pfad = Path(__file__).resolve().parent.parent / "kern" / "kennung.py"
        stelle = importlib.util.spec_from_file_location(
            "kern_kennung_fuer_implementierer", pfad)
        modul = importlib.util.module_from_spec(stelle)
        stelle.loader.exec_module(modul)
        _kennung_modul = modul
    return _kennung_modul


def neubau(auftrag: str) -> Path:
    """Der Ordner, in dem die neuen Dateien entstehen."""
    return _bau(auftrag) / "neu"


def _bau(auftrag: str) -> Path:
    return UNIVERSE / "zustand" / "bau" / (_kennung().sauber(auftrag, "bau"))


def bauplan(auftrag: str) -> dict | None:
    datei = _bau(auftrag) / "bauplan.json"
    if not datei.exists():
        return None
    try:
        return json.loads(datei.read_text(encoding="utf-8"))
    except Exception:
        return None


# ------------------------------------------------------------------ Schreiben

_FRAGE = """Schreibe genau eine Python-Datei. Antworte nur mit dem Code,
ohne Erklaerung davor oder danach, ohne Zaun aus Backticks.

Regeln des Hauses:
- deutsche Bezeichner und deutsche Kommentare
- der Docstring oben sagt, WARUM es diese Datei gibt, nicht was sie tut
- keine Abhaengigkeit, die nicht schon im Universe benutzt wird
- hoechstens %d Zeilen
- nichts ausgeben, was ein Geheimnis sein koennte

Das Ganze, damit du weisst, wo die Datei steht:
%s

Diese Datei: %s
Wofuer: %s
%s"""


def schreiben(auftrag: str, plan: dict) -> dict:
    """Die Dateien des Bauplans anlegen. Gibt einen Bericht zurueck."""
    ziel = neubau(auftrag)
    ziel.mkdir(parents=True, exist_ok=True)

    bericht = {"auftrag": auftrag, "dateien": [], "kosten": 0.0,
               "mit_modell": False, "hinweis": ""}

    kunde = _kunde()
    if kunde is None:
        bericht["hinweis"] = (
            "Ohne ANTHROPIC_API_KEY oder ohne das Paket 'anthropic' kann "
            "hier nichts entstehen. Es wurde nichts geschrieben.")
        return bericht

    umriss = _umriss(plan)
    for eintrag in plan.get("dateien", []):
        pfad = str(eintrag.get("pfad", "")).strip()
        if not pfad or pfad.startswith("("):
            continue
        sicher = _im_ordner(ziel, pfad)
        if sicher is None:
            bericht["dateien"].append(
                {"pfad": pfad, "geschrieben": False,
                 "grund": "Pfad zeigt aus dem Bauordner heraus."})
            continue

        erlaubt, grund = _darf(bericht["kosten"])
        if not erlaubt:
            bericht["hinweis"] = grund
            break

        code, kosten = _eine_datei(kunde, umriss, pfad,
                                   str(eintrag.get("wofuer", "")), auftrag)
        bericht["kosten"] += kosten
        if not code:
            bericht["dateien"].append(
                {"pfad": pfad, "geschrieben": False,
                 "grund": "Das Modell hat nichts Brauchbares geliefert."})
            _technik(auftrag, "modell-nichts-geliefert", pfad)
            continue

        sicher.parent.mkdir(parents=True, exist_ok=True)
        sicher.write_text(code, encoding="utf-8", newline="\n")
        bericht["mit_modell"] = True
        bericht["dateien"].append(
            {"pfad": pfad, "geschrieben": True,
             "zeilen": code.count("\n") + 1})
    return bericht


def _umriss(plan: dict) -> str:
    zeilen = ["Ziel: " + str(plan.get("ziel", ""))]
    for d in plan.get("dateien", []):
        zeilen.append("  %s - %s" % (d.get("pfad"), d.get("wofuer")))
    if plan.get("pruefungen"):
        zeilen.append("Geprueft wird: " + "; ".join(plan["pruefungen"]))
    return "\n".join(zeilen)


def _eine_datei(kunde, umriss: str, pfad: str, wofuer: str,
                auftrag: str) -> tuple[str, float]:
    try:
        antwort = kunde.messages.create(
            model=MODELL, max_tokens=4000,
            messages=[{"role": "user", "content": _FRAGE % (
                ZEILEN_HOECHSTENS, umriss, pfad, wofuer, "")}])
    except Exception as fehler:
        _technik(auftrag, "dienst-nicht-erreichbar", "%s: %s" % (pfad, fehler))
        return "", 0.0
    kosten = _buchen(antwort, "Bau %s: %s" % (auftrag, pfad), auftrag)
    roh = "".join(getattr(t, "text", "") for t in antwort.content).strip()
    return _ohne_zaun(roh), kosten




def _technik(auftrag: str, klasse: str, einzelheit: str = "") -> None:
    """Ein Prozessfehler als Erfahrung - getrennt von den Urteilen ueber das
    Stueck, damit der Ausbilder sieht, wo die Maschinerie hakt. Nie eine
    Ausnahme nach aussen: ein fehlender Vermerk ist besser als ein Abbruch."""
    try:
        import sys as _sys
        from pathlib import Path as _Path
        kern = str(_Path(__file__).resolve().parent.parent / "kern")
        if kern not in _sys.path:
            _sys.path.append(kern)
        import rueckweg
        rueckweg.technik_vermerken(str(auftrag), "prod.app", klasse, einzelheit)
    except Exception:
        pass


def _ohne_zaun(roh: str) -> str:
    """Backticks abnehmen, falls das Modell doch welche gesetzt hat."""
    if roh.startswith("```"):
        roh = re.sub(r"^```[a-zA-Z]*\n", "", roh)
        roh = re.sub(r"\n```\s*$", "", roh)
    return roh.strip() + "\n" if roh.strip() else ""


def _im_ordner(wurzel: Path, pfad: str) -> Path | None:
    """Verhindert, dass ein Pfad aus dem Bauordner ausbricht.

    Ein Modell, das '../../kern/gehirn.py' vorschlaegt, wuerde sonst
    mitten ins laufende Universe schreiben.
    """
    ziel = (wurzel / pfad).resolve()
    try:
        ziel.relative_to(wurzel.resolve())
    except ValueError:
        return None
    return ziel


# ------------------------------------------------------------------ Messen

def messen(auftrag: str, plan: dict | None = None) -> dict:
    """Uebersetzen, zaehlen, pruefen. Kostet nichts, sagt die Wahrheit."""
    ordner = neubau(auftrag)
    bericht = {
        "auftrag": auftrag,
        "zeit": datetime.now().isoformat(timespec="seconds"),
        "dateien": 0, "zeilen": 0,
        "uebersetzt": True, "uebersetzungsfehler": [],
        "pruefungen_gelaufen": False, "bestanden": 0, "durchgefallen": 0,
        "ausgabe": "",
    }
    if not ordner.exists():
        bericht["uebersetzt"] = False
        bericht["uebersetzungsfehler"] = ["Es wurde gar nichts gebaut."]
        return bericht

    for datei in sorted(ordner.rglob("*")):
        if not datei.is_file():
            continue
        bericht["dateien"] += 1
        try:
            bericht["zeilen"] += len(
                datei.read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            pass
        if datei.suffix == ".py":
            fehler = _uebersetzt(datei)
            if fehler:
                bericht["uebersetzt"] = False
                bericht["uebersetzungsfehler"].append(fehler)

    pruefdatei = next(iter(sorted(ordner.rglob("pruefungen.py"))), None)
    if pruefdatei is not None and bericht["uebersetzt"]:
        _pruefungen_laufen(pruefdatei, bericht)

    (_bau(auftrag)).mkdir(parents=True, exist_ok=True)
    (_bau(auftrag) / "pruefbericht.json").write_text(
        json.dumps(bericht, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    return bericht


def _uebersetzt(datei: Path) -> str:
    """Leerer Text heisst: sie uebersetzt."""
    with tempfile.TemporaryDirectory() as ablage:
        try:
            py_compile.compile(str(datei), cfile=str(Path(ablage) / "x.pyc"),
                               doraise=True)
            return ""
        except py_compile.PyCompileError as fehler:
            return "%s: %s" % (datei.name, str(fehler).splitlines()[-1][:200])
        except Exception as fehler:
            return "%s: %s" % (datei.name, str(fehler)[:200])


def _pruefungen_laufen(datei: Path, bericht: dict) -> None:
    """Die Pruefungen des Baus laufen lassen - im eigenen Prozess.

    Im eigenen Prozess, weil ein frisch geschriebenes Modul beim Laden
    alles Moegliche tun kann. Was dabei abstuerzt, stuerzt dort ab.
    """
    try:
        lauf = subprocess.run(
            [sys.executable, "-u", datei.name],
            cwd=str(datei.parent), capture_output=True, text=True,
            timeout=ZEITGRENZE_SEK)
    except subprocess.TimeoutExpired:
        bericht["pruefungen_gelaufen"] = True
        bericht["durchgefallen"] = 1
        bericht["ausgabe"] = ("Die Pruefungen liefen laenger als %d Sekunden "
                              "und wurden abgebrochen." % ZEITGRENZE_SEK)
        return
    except Exception as fehler:
        bericht["ausgabe"] = "Pruefungen nicht startbar: %s" % fehler
        return

    bericht["pruefungen_gelaufen"] = True
    bericht["ausgabe"] = ((lauf.stdout or "") + (lauf.stderr or ""))[-4000:]
    treffer = re.search(r"(\d+)\s+bestanden.*?(\d+)\s+durchgefallen",
                        bericht["ausgabe"], re.S)
    if treffer:
        bericht["bestanden"] = int(treffer.group(1))
        bericht["durchgefallen"] = int(treffer.group(2))
    else:
        bericht["bestanden"] = 1 if lauf.returncode == 0 else 0
        bericht["durchgefallen"] = 0 if lauf.returncode == 0 else 1


# ------------------------------------------------------------------ Fingerabdruck

def fingerabdruck(auftrag: str) -> str:
    """Der Inhaltsabdruck des ganzen Baus: jede Datei unter neu/, mit Pfad.

    Zwoelf Zeichen reichen, um zwei Staende auseinanderzuhalten; leer, wenn
    es nichts gibt.
    """
    ordner = neubau(auftrag)
    if not ordner.exists():
        return ""
    h = hashlib.sha256()
    for datei in sorted(p for p in ordner.rglob("*") if p.is_file()):
        h.update(str(datei.relative_to(ordner)).replace("\\", "/").encode("utf-8"))
        h.update(b"\0")
        h.update(datei.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:12]


def vorgelegt_merken(auftrag: str, warenausgang_kennung: str) -> dict:
    """Festhalten, welcher Stand vorgelegt wurde - die Freigabe gilt genau dem.

    Seit dem 11.09.2026: die Uebernahme prueft gegen diesen Abdruck. Wer
    nach der Vorlage noch eine Datei im Bauordner aendert - Mensch, Modell
    oder Schleife -, macht die Freigabe damit ungueltig.
    """
    satz = {"auftrag": auftrag, "warenausgang": warenausgang_kennung,
            "fingerabdruck": fingerabdruck(auftrag),
            "vorgelegt": datetime.now().isoformat(timespec="seconds")}
    _bau(auftrag).mkdir(parents=True, exist_ok=True)
    (_bau(auftrag) / "vorgelegt.json").write_text(
        json.dumps(satz, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    return satz


def uebernahme_erlaubt(auftrag: str) -> tuple[bool, str]:
    """Ist der Bau noch der, der vorgelegt wurde? (ja/nein, Grund)."""
    datei = _bau(auftrag) / "vorgelegt.json"
    if not datei.exists():
        return False, "Der Bau wurde nie vorgelegt - ohne Vorlage keine Freigabe, ohne Freigabe keine Uebernahme."
    try:
        satz = json.loads(datei.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "Die Vorlage (vorgelegt.json) ist nicht lesbar."
    jetzt = fingerabdruck(auftrag)
    if not jetzt:
        return False, "Im Bauordner liegt nichts mehr."
    if jetzt != satz.get("fingerabdruck"):
        return False, ("Der Bau hat sich seit der Vorlage geaendert (Abdruck %s, vorgelegt %s). "
                       "Die Freigabe galt dem alten Stand - neu vorlegen." % (jetzt, satz.get("fingerabdruck")))
    return True, ""


# ------------------------------------------------------------------ Uebernahme

def uebernehmen(auftrag: str) -> dict:
    """Den fertigen Bau ins Universe legen - mit Sicherung.

    Wird nur nach deiner Freigabe aufgerufen. Jede Datei, die dabei
    ueberschrieben wird, liegt vorher unter <bau>/vorher/ - so ist der
    Rueckweg immer noch eine Kopie und kein Rateschritt.
    """
    quelle = neubau(auftrag)
    sicherung = _bau(auftrag) / "vorher"
    ergebnis = {"kopiert": [], "gesichert": [], "abgelehnt": []}
    if not quelle.exists():
        return ergebnis

    for datei in sorted(quelle.rglob("*")):
        if not datei.is_file():
            continue
        rel = datei.relative_to(quelle)
        ziel = _im_ordner(UNIVERSE, str(rel))
        if ziel is None:
            ergebnis["abgelehnt"].append(str(rel))
            continue
        if ziel.exists():
            alt = sicherung / rel
            alt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ziel, alt)
            ergebnis["gesichert"].append(str(rel))
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(datei, ziel)
        ergebnis["kopiert"].append(str(rel))
    return ergebnis


# ------------------------------------------------------------------ Modell

def _kunde():
    try:
        import umgebung
        umgebung.laden()
    except Exception:
        pass
    schluessel = os.environ.get("ANTHROPIC_API_KEY")
    if not schluessel:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        return anthropic.Anthropic(api_key=schluessel)
    except Exception:
        return None


def _darf(schon: float) -> tuple[bool, str]:
    try:
        import verbrauch
        return verbrauch.darf(MODUL, KOSTEN_JE_DATEI_EUR, schon)
    except Exception:
        return True, ""


def _buchen(antwort, wofuer: str, auftrag: str) -> float:
    try:
        import modellkosten
        satz = modellkosten.buchen(antwort, MODUL, MODELL, wofuer, auftrag)
        return float((satz or {}).get("betrag_eur", 0.0))
    except Exception:
        return 0.0
