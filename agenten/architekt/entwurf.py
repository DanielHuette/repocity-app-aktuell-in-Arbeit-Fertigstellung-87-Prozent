"""Der Bauplan - was gebaut werden soll, bevor gebaut wird.

Warum ueberhaupt ein Plan, wenn ein Modell den Code auch in einem Zug
schreiben koennte: weil ein abgelehnter Plan ein paar Cent kostet und ein
abgelehnter Bau eine halbe Stunde. Derselbe Grund, aus dem die
Lern-Werkstatt erst das Curriculum vorlegt und dann erzeugt.

Ein Bauplan nennt vier Dinge und sonst nichts:

    ZIEL        was danach geht, was vorher nicht ging - in einem Satz
    DATEIEN     welche Datei entsteht oder sich aendert, und wofuer
    PRUEFUNGEN  woran man sieht, dass es stimmt
    RISIKEN     was dabei kaputtgehen kann

Ohne Modell entsteht trotzdem ein Plan: Ziel und Risiken kommen dann aus
dem Auftragstext und dem Vorwissen. Er ist duerftig, aber ehrlich - und
er sagt selbst, dass er duerftig ist.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"

for _p in (str(KERN),):
    if _p not in sys.path:
        sys.path.append(_p)

#: Unter dieser Kennung meldet und bucht der Architekt.
MODUL = "prod.app"

#: Ein Plan ist kurz. Wird er laenger, ist der Auftrag zu gross.
DATEIEN_HOECHSTENS = 12

#: Was ein Entwurf voraussichtlich kostet - gerechnet, nicht geraten:
#: rund 900 Token hinein, 900 hinaus, mit Opus 5 (5,00 / 25,00 USD je
#: Million, Listenpreis 11.09.2026, Kurs 0,92): (900 x 5 + 900 x 25) / 1e6
#: = 0,027 USD x 0,92 = 0,0248 EUR. Aufgerundet auf 0,03 EUR.
#: Die Obergrenze steht nicht hier, sondern im Topf 'denken' in
#: kosten.json - dort gehoert sie hin, und dort steht auch, warum.
KOSTEN_JE_ENTWURF_EUR = 0.03

import modellwahl  # noqa: E402  - das eine Modell des Universe
MODELL = modellwahl.MODELL


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
            "kern_kennung_fuer_architekt", pfad)
        modul = importlib.util.module_from_spec(stelle)
        stelle.loader.exec_module(modul)
        _kennung_modul = modul
    return _kennung_modul


@dataclass
class Bauplan:
    auftrag: str
    titel: str
    ziel: str = ""
    dateien: list = field(default_factory=list)   # [{"pfad", "wofuer"}]
    pruefungen: list = field(default_factory=list)
    risiken: list = field(default_factory=list)
    vorwissen: str = ""
    mit_modell: bool = False
    kosten: float = 0.0

    @property
    def vollstaendig(self) -> bool:
        return bool(self.ziel and self.dateien and self.pruefungen)


# ------------------------------------------------------------------ Vorwissen

def _vorwissen() -> str:
    """Was beim Bauen schon einmal schiefgegangen ist."""
    try:
        import rueckweg
        return rueckweg.vorwissen(MODUL)
    except Exception:
        return ""


# ------------------------------------------------------------------ Entwurf

def entwerfen(auftrag: dict, mit_modell: bool = True) -> Bauplan:
    """Aus einem Auftragssatz einen Bauplan machen."""
    text = str(auftrag.get("text") or auftrag.get("beschreibung") or "").strip()
    titel = str(auftrag.get("titel") or "").strip() or _titel_aus(text)
    plan = Bauplan(auftrag=str(auftrag.get("id", "ohne-nummer")), titel=titel,
                   vorwissen=_vorwissen())

    if mit_modell:
        gefuellt = _durch_modell(text, plan, _stoffblock(auftrag))
        if gefuellt:
            plan.mit_modell = True
            return plan

    _ohne_modell(text, plan)
    return plan


def _titel_aus(text: str) -> str:
    erster = re.split(r"[.\n]", text.strip())[0].strip()
    return (erster[:70] or "Bauauftrag ohne Titel")


def _ohne_modell(text: str, plan: Bauplan) -> None:
    """Der ehrliche Notplan: er sagt, was er nicht weiss."""
    plan.ziel = text or "Im Auftrag steht kein Satz, was entstehen soll."
    plan.dateien = [{
        "pfad": "(offen)",
        "wofuer": "Ohne Modell kann der Architekt nicht sagen, welche "
                  "Dateien noetig sind. Das muss von Hand ergaenzt werden.",
    }]
    plan.pruefungen = [
        "Der Pruefstand laeuft danach ohne neue rote Zeile: "
        "python universe/kern/pruefstand.py trocken",
    ]
    plan.risiken = [
        "Dieser Plan ist ohne Modell entstanden und nennt keine Dateien. "
        "Er taugt zum Lesen, nicht zum Bauen.",
    ]


# ------------------------------------------------------------------ Modell

_FRAGE = """Du planst eine Aenderung an einem Python-Programm. Antworte
ausschliesslich mit JSON, ohne Text davor oder danach, nach diesem Muster:

{"ziel": "ein Satz: was danach geht, was vorher nicht ging",
 "dateien": [{"pfad": "ordner/datei.py", "wofuer": "ein Halbsatz"}],
 "pruefungen": ["woran man sieht, dass es stimmt"],
 "risiken": ["was dabei kaputtgehen kann"]}

Regeln:
- hoechstens %d Dateien; passt es nicht, nenne im Ziel, was fehlt
- Pfade relativ zum Ordner universe/
- deutsche Bezeichner, deutsche Kommentare
- jede Pruefung muss ohne Geld auskommen und ohne Netz laufen
- keine Erklaerungen ausserhalb des JSON

Der Auftrag:
%s
%s"""


def _stoffblock(auftrag: dict) -> str:
    """Was der Kurator zum Thema herausgegeben hat - als Block fuer die Frage.

    Der Stoff steht im Auftrag; hineingelegt hat ihn der Verteiler, bevor die
    Strasse losgelaufen ist. Ohne Kern gibt es keinen Stoff - dann bleibt der
    Block leer und es wird geplant wie bisher.
    """
    try:
        import stoff as _stoff
        return _stoff.als_anweisung(_stoff.aus_auftrag(auftrag))
    except Exception:
        return ""


def _durch_modell(text: str, plan: Bauplan, stoff: str = "") -> bool:
    """Ein Modell fuellt den Plan. False, wenn es nicht geklappt hat."""
    if not text:
        return False
    if not _darf_kosten():
        return False
    try:
        import umgebung
        umgebung.laden()
    except Exception:
        pass
    schluessel = os.environ.get("ANTHROPIC_API_KEY")
    if not schluessel:
        return False
    try:
        import anthropic
    except ImportError:
        return False

    vorwissen = ("\nWas beim letzten Mal schiefging:\n" + plan.vorwissen
                 if plan.vorwissen else "")
    if stoff:
        # Erst der eigene Stoff, dann das Vorwissen - so steht am Ende der
        # Frage das, was zuletzt gelernt wurde.
        vorwissen = "\n" + stoff + vorwissen
    try:
        antwort = anthropic.Anthropic(api_key=schluessel).messages.create(
            model=MODELL, max_tokens=1400,
            messages=[{"role": "user",
                       "content": _FRAGE % (DATEIEN_HOECHSTENS, text, vorwissen)}])
    except Exception as fehler:
        _technik(plan.auftrag, "dienst-nicht-erreichbar", str(fehler))
        return False

    plan.kosten = _buchen(antwort, "Bauplan: " + plan.titel)
    roh = "".join(getattr(t, "text", "") for t in antwort.content).strip()
    satz = _json_heraus(roh)
    if not satz:
        _technik(plan.auftrag, "antwort-nicht-lesbar", "kein JSON im Bauplan")
        return False

    plan.ziel = str(satz.get("ziel", "")).strip()
    plan.dateien = [
        {"pfad": str(d.get("pfad", "")).strip(),
         "wofuer": str(d.get("wofuer", "")).strip()}
        for d in satz.get("dateien", []) if str(d.get("pfad", "")).strip()
    ][:DATEIEN_HOECHSTENS]
    plan.pruefungen = [str(p).strip() for p in satz.get("pruefungen", []) if str(p).strip()]
    plan.risiken = [str(r).strip() for r in satz.get("risiken", []) if str(r).strip()]
    return plan.vollstaendig




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


def _json_heraus(roh: str) -> dict | None:
    """Das JSON aus der Antwort holen, auch wenn ein Zaun drumherum steht."""
    if roh.startswith("```"):
        roh = re.sub(r"^```[a-z]*\n|\n```$", "", roh.strip())
    try:
        return json.loads(roh)
    except Exception:
        pass
    auf, zu = roh.find("{"), roh.rfind("}")
    if auf < 0 or zu <= auf:
        return None
    try:
        return json.loads(roh[auf:zu + 1])
    except Exception:
        return None


def _darf_kosten() -> bool:
    """Die Reissleine des Controllers - vor dem Aufruf, nicht danach."""
    try:
        import verbrauch
        erlaubt, _ = verbrauch.darf(MODUL, KOSTEN_JE_ENTWURF_EUR)
        return bool(erlaubt)
    except Exception:
        return True


def _buchen(antwort, wofuer: str) -> float:
    try:
        import modellkosten
        satz = modellkosten.buchen(antwort, MODUL, MODELL, wofuer)
        return float((satz or {}).get("betrag_eur", 0.0))
    except Exception:
        return 0.0


# ------------------------------------------------------------------ Ablage

def ordner(auftrag: str) -> Path:
    """Wo dieser Bau liegt. Nie im laufenden Universe - immer daneben."""
    return UNIVERSE / "zustand" / "bau" / _sauber(auftrag)


def _sauber(kennung: str) -> str:
    """Aus einer Hub-Kennung einen Ordnernamen machen.

    Die Kennungen des Hubs enthalten einen Doppelpunkt, und Windows deutet
    den als Trenner zu einem versteckten Datenstrom. Derselbe Fund wie beim
    Verteiler - hier gleich mit eingebaut.
    """
    return _kennung().sauber(kennung, "bau")


def als_markdown(plan: Bauplan) -> str:
    zeilen = [
        "---",
        "auftrag: %s" % plan.auftrag,
        "modul: %s" % MODUL,
        "erstellt: %s" % datetime.now().isoformat(timespec="seconds"),
        "mit_modell: %s" % ("ja" if plan.mit_modell else "nein"),
        "kosten_eur: %.4f" % plan.kosten,
        "---",
        "",
        "# %s" % plan.titel,
        "",
        "## Ziel",
        "",
        plan.ziel or "(offen)",
        "",
        "## Dateien",
        "",
    ]
    for d in plan.dateien:
        zeilen.append("- `%s` - %s" % (d["pfad"], d["wofuer"]))
    zeilen += ["", "## Pruefungen", ""]
    zeilen += ["- %s" % p for p in plan.pruefungen] or ["- (keine genannt)"]
    zeilen += ["", "## Risiken", ""]
    zeilen += ["- %s" % r for r in plan.risiken] or ["- (keine genannt)"]
    if plan.vorwissen:
        zeilen += ["", "## Vorwissen", "", plan.vorwissen]
    zeilen += ["", "", "Dieser Plan baut nichts. Erst nach deiner Freigabe "
               "nimmt ihn der Implementierer auf.", ""]
    return "\n".join(zeilen)


def speichern(plan: Bauplan) -> Path:
    """Bauplan ablegen - lesbar als Markdown, maschinenlesbar als JSON."""
    ziel = ordner(plan.auftrag)
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "BAUPLAN.md").write_text(als_markdown(plan), encoding="utf-8", newline="")
    (ziel / "bauplan.json").write_text(
        json.dumps({
            "auftrag": plan.auftrag, "titel": plan.titel, "ziel": plan.ziel,
            "dateien": plan.dateien, "pruefungen": plan.pruefungen,
            "risiken": plan.risiken, "mit_modell": plan.mit_modell,
            "kosten": plan.kosten,
        }, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    return ziel / "BAUPLAN.md"


def laden(auftrag: str) -> Bauplan | None:
    datei = ordner(auftrag) / "bauplan.json"
    if not datei.exists():
        return None
    try:
        satz = json.loads(datei.read_text(encoding="utf-8"))
    except Exception:
        return None
    return Bauplan(
        auftrag=satz.get("auftrag", auftrag), titel=satz.get("titel", ""),
        ziel=satz.get("ziel", ""), dateien=satz.get("dateien", []),
        pruefungen=satz.get("pruefungen", []), risiken=satz.get("risiken", []),
        mit_modell=bool(satz.get("mit_modell")),
        kosten=float(satz.get("kosten", 0.0)))
