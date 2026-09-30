"""Der Kampagnenplan - was gesagt wird, wem, wo und wann.

Marketing ist im Universe kein Mitlaeufer bei Social Media, sondern eine
eigene Stelle. Der Unterschied: Social Media stellt einen fertigen
Beitrag her, Marketing entscheidet vorher, was ueberhaupt gesagt werden
soll und an wen.

Ein Plan nennt fuenf Dinge und sonst nichts:

    BOTSCHAFT     ein Satz, der ohne Erklaerung steht
    ZIELGRUPPE    wen er treffen soll und was den interessiert
    KANAELE       wo, und warum dort
    TAKT          wie oft, ueber welchen Zeitraum
    BAUSTEINE     drei Textanfaenge, an denen man sofort sieht, ob es traegt

Ohne Modell entsteht trotzdem ein Plan. Er nimmt Botschaft und
Zielgruppe woertlich aus dem Auftrag und sagt selbst, dass der Rest
fehlt - das ist ehrlicher als drei erfundene Kanaele.
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

MODUL = "prod.marketing"
import modellwahl  # noqa: E402  - das eine Modell des Universe
MODELL = modellwahl.MODELL

#: Gerechnet aus der Preistabelle: rund 700 Token hinein, 1100 hinaus,
#: mit Opus 5 (5,00 / 25,00 USD je Million, Listenpreis 11.09.2026):
#: (700 x 5 + 1100 x 25) / 1e6 = 0,031 USD x 0,92 = 0,0285 EUR.
#: Aufgerundet auf 0,03 EUR. Die Decke steht im Topf
#: 'clips_und_bilder' in kosten.json, nicht hier.
KOSTEN_JE_PLAN_EUR = 0.03

#: Mehr Kanaele heisst nicht mehr Wirkung, sondern duennere Arbeit.
KANAELE_HOECHSTENS = 4


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
            "kern_kennung_fuer_marketing", pfad)
        modul = importlib.util.module_from_spec(stelle)
        stelle.loader.exec_module(modul)
        _kennung_modul = modul
    return _kennung_modul


@dataclass
class Plan:
    auftrag: str
    titel: str
    botschaft: str = ""
    zielgruppe: str = ""
    kanaele: list = field(default_factory=list)   # [{"wo", "warum"}]
    takt: str = ""
    bausteine: list = field(default_factory=list)
    vorwissen: str = ""
    mit_modell: bool = False
    kosten: float = 0.0

    @property
    def vollstaendig(self) -> bool:
        """'(offen)' ist kein Inhalt.

        Ohne diese Pruefung gilt der Notplan als fertig, weil in jedem
        Feld etwas steht - und wird als fertiger Plan weitergereicht.
        """
        def steht(wert) -> bool:
            return bool(str(wert).strip()) and not str(wert).lstrip().startswith("(offen")

        return (steht(self.botschaft) and steht(self.zielgruppe)
                and any(steht(k.get("wo")) for k in self.kanaele)
                and any(steht(b) for b in self.bausteine))


# ------------------------------------------------------------------ Planen

def planen(auftrag: dict, mit_modell: bool = True) -> Plan:
    text = str(auftrag.get("text") or auftrag.get("beschreibung") or "").strip()
    titel = str(auftrag.get("titel") or "").strip() or _titel_aus(text)
    plan = Plan(auftrag=str(auftrag.get("id", "ohne-nummer")), titel=titel,
                vorwissen=_vorwissen())

    if mit_modell and _durch_modell(text, plan, _stoffblock(auftrag)):
        plan.mit_modell = True
        return plan

    _ohne_modell(text, plan)
    return plan


def _titel_aus(text: str) -> str:
    erster = re.split(r"[.\n]", text.strip())[0].strip()
    return erster[:70] or "Kampagne ohne Titel"


def _vorwissen() -> str:
    try:
        import rueckweg
        return rueckweg.vorwissen(MODUL)
    except Exception:
        return ""


def _ohne_modell(text: str, plan: Plan) -> None:
    """Der ehrliche Notplan: er nennt, was fehlt, statt es zu erfinden."""
    plan.botschaft = text or "Im Auftrag steht kein Satz, was gesagt werden soll."
    plan.zielgruppe = "(offen - steht nicht im Auftrag)"
    plan.kanaele = [{"wo": "(offen)",
                     "warum": "Ohne Modell nennt der Plan keine Kanaele. "
                              "Drei erfundene waeren schlechter als keiner."}]
    plan.takt = "(offen)"
    plan.bausteine = ["(offen - ohne Modell entsteht kein Text)"]


# ------------------------------------------------------------------ Modell

_FRAGE = """Du planst eine Kampagne. Antworte ausschliesslich mit JSON,
ohne Text davor oder danach, nach diesem Muster:

{"botschaft": "ein Satz, der ohne Erklaerung steht",
 "zielgruppe": "wen er trifft und was den interessiert",
 "kanaele": [{"wo": "Kanal", "warum": "ein Halbsatz"}],
 "takt": "wie oft, ueber welchen Zeitraum",
 "bausteine": ["drei Textanfaenge, je hoechstens zwei Saetze"]}

Regeln:
- hoechstens %d Kanaele; lieber zwei gut als vier halb
- genau drei Bausteine
- deutsch, keine Werbefloskeln, keine Ausrufezeichen
- nichts versprechen, was das Erzeugnis nicht haelt

Der Auftrag:
%s
%s"""


def _stoffblock(auftrag: dict) -> str:
    """Was der Kurator zum Thema herausgegeben hat - als Block fuer die Frage.

    Der Stoff steht im Auftrag; hineingelegt hat ihn der Verteiler. Ohne Kern
    gibt es keinen Stoff - dann bleibt der Block leer.
    """
    try:
        import stoff as _stoff
        return _stoff.als_anweisung(_stoff.aus_auftrag(auftrag))
    except Exception:
        return ""


def _durch_modell(text: str, plan: Plan, stoff: str = "") -> bool:
    if not text or not _darf():
        return False
    kunde = _kunde()
    if kunde is None:
        return False

    vorwissen = ("\nWas beim letzten Mal nicht getragen hat:\n" + plan.vorwissen
                 if plan.vorwissen else "")
    if stoff:
        # Erst der eigene Stoff, dann das Vorwissen - in dieser Reihenfolge
        # steht am Ende der Frage das, was zuletzt gelernt wurde.
        vorwissen = "\n" + stoff + vorwissen
    try:
        antwort = kunde.messages.create(
            model=MODELL, max_tokens=1200,
            messages=[{"role": "user",
                       "content": _FRAGE % (KANAELE_HOECHSTENS, text, vorwissen)}])
    except Exception as fehler:
        _technik(plan.auftrag, "dienst-nicht-erreichbar", str(fehler))
        return False

    plan.kosten = _buchen(antwort, "Kampagnenplan: " + plan.titel, plan.auftrag)
    satz = _json_heraus("".join(getattr(t, "text", "") for t in antwort.content))
    if not satz:
        _technik(plan.auftrag, "antwort-nicht-lesbar", "kein JSON im Kampagnenplan")
        return False

    plan.botschaft = str(satz.get("botschaft", "")).strip()
    plan.zielgruppe = str(satz.get("zielgruppe", "")).strip()
    plan.kanaele = [
        {"wo": str(k.get("wo", "")).strip(), "warum": str(k.get("warum", "")).strip()}
        for k in satz.get("kanaele", []) if str(k.get("wo", "")).strip()
    ][:KANAELE_HOECHSTENS]
    plan.takt = str(satz.get("takt", "")).strip()
    plan.bausteine = [str(b).strip() for b in satz.get("bausteine", []) if str(b).strip()]
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
        rueckweg.technik_vermerken(str(auftrag), "prod.marketing", klasse, einzelheit)
    except Exception:
        pass


def _json_heraus(roh: str) -> dict | None:
    roh = roh.strip()
    if roh.startswith("```"):
        roh = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", roh)
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


def _kunde():
    try:
        import umgebung
        umgebung.laden()
    except Exception:
        pass
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    except Exception:
        return None


def _darf() -> bool:
    try:
        import verbrauch
        ja, _ = verbrauch.darf(MODUL, KOSTEN_JE_PLAN_EUR)
        return bool(ja)
    except Exception:
        return True


def _buchen(antwort, wofuer: str, auftrag: str) -> float:
    try:
        import modellkosten
        satz = modellkosten.buchen(antwort, MODUL, MODELL, wofuer, auftrag)
        return float((satz or {}).get("betrag_eur", 0.0))
    except Exception:
        return 0.0


# ------------------------------------------------------------------ Ablage

def ordner(auftrag: str) -> Path:
    return UNIVERSE / "zustand" / "kampagnen" / (_kennung().sauber(auftrag, "kampagne"))


def als_markdown(plan: Plan) -> str:
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
        "## Botschaft",
        "",
        plan.botschaft or "(offen)",
        "",
        "## Zielgruppe",
        "",
        plan.zielgruppe or "(offen)",
        "",
        "## Kanaele",
        "",
    ]
    for k in plan.kanaele:
        zeilen.append("- **%s** - %s" % (k["wo"], k["warum"]))
    zeilen += ["", "## Takt", "", plan.takt or "(offen)", "",
               "## Bausteine", ""]
    for nr, b in enumerate(plan.bausteine, 1):
        zeilen += ["%d. %s" % (nr, b), ""]
    if plan.vorwissen:
        zeilen += ["## Vorwissen", "", plan.vorwissen, ""]
    zeilen += ["", "Dieser Plan veroeffentlicht nichts. Was daraus wird, "
               "baut Social Media - und erst nach deiner Freigabe.", ""]
    return "\n".join(zeilen)


def speichern(plan: Plan) -> Path:
    ziel = ordner(plan.auftrag)
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "KAMPAGNE.md").write_text(als_markdown(plan), encoding="utf-8", newline="")
    (ziel / "kampagne.json").write_text(json.dumps({
        "auftrag": plan.auftrag, "titel": plan.titel,
        "botschaft": plan.botschaft, "zielgruppe": plan.zielgruppe,
        "kanaele": plan.kanaele, "takt": plan.takt,
        "bausteine": plan.bausteine, "mit_modell": plan.mit_modell,
        "kosten": plan.kosten,
    }, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    return ziel / "KAMPAGNE.md"
