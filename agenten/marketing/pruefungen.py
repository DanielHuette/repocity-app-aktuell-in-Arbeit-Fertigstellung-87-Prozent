"""Pruefungen des Marketings. Alles trocken, kein Modell wird gefragt."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

kampagne = laden(HIER / "kampagne.py", "marketing_kampagne")

MODUL = "prod.marketing"


@anmelden("marketing.notplan-sagt-was-fehlt", MODUL,
          "Ohne Modell nennt der Plan keine erfundenen Kanaele", TROCKEN,
          "dass niemand einen leeren Plan fuer einen fertigen haelt")
def notplan_sagt_was_fehlt():
    """Drei erfundene Kanaele waeren schlechter als keiner: man wuerde
    danach arbeiten."""
    plan = kampagne.planen({"id": "p1", "text": "Der Rueckweg soll bekannt "
                                                "werden."}, mit_modell=False)
    if plan.mit_modell:
        raise AssertionError("Es wurde doch ein Modell gefragt")
    text = " ".join(k["warum"] for k in plan.kanaele).lower()
    if "ohne modell" not in text:
        raise AssertionError("Der Plan verschweigt, dass er leer ist")
    if plan.vollstaendig:
        raise AssertionError("Ein Notplan darf nicht als vollstaendig gelten")
    return "der Notplan nennt sich selbst unvollstaendig"


@anmelden("marketing.plan-steht-lesbar-da", MODUL,
          "Der Plan wird als Markdown und als JSON abgelegt", TROCKEN,
          "dass zwischen Plan und Beitrag nichts verlorengeht")
def plan_steht_lesbar_da():
    echt = kampagne.UNIVERSE
    with tempfile.TemporaryDirectory() as ablage:
        kampagne.UNIVERSE = Path(ablage)
        try:
            plan = kampagne.planen({"id": "auftrag:p2", "titel": "Probe",
                                    "text": "x"}, mit_modell=False)
            plan.botschaft = "Ein Satz, der steht."
            pfad = kampagne.speichern(plan)
            text = pfad.read_text(encoding="utf-8")
            if "Ein Satz, der steht." not in text:
                raise AssertionError("Die Botschaft fehlt im Markdown")
            if not (pfad.parent / "kampagne.json").exists():
                raise AssertionError("Das JSON fehlt")
            if ":" in pfad.parent.name:
                raise AssertionError("Doppelpunkt im Ordnernamen: %s"
                                     % pfad.parent.name)
        finally:
            kampagne.UNIVERSE = echt
    return "Markdown und JSON liegen da, der Ordnername ist entschaerft"


@anmelden("marketing.marke-haelt-den-plan-an", MODUL,
          "Ohne Marke laeuft ein Plan, mit erreichter Marke nicht mehr", TROCKEN,
          "dass die Marke des Nutzers wirkt, ohne jeden Plan abzulehnen, "
          "bevor er anfaengt")
def marke_haelt_den_plan_an():
    import shutil as _shutil
    import tempfile as _tempfile
    from pathlib import Path as _Path

    import bremse
    import verbrauch

    erlaubt, grund = verbrauch.darf(MODUL, kampagne.KOSTEN_JE_PLAN_EUR)
    if not erlaubt:
        raise AssertionError("ohne gesetzte Marke darf nichts abgelehnt werden: "
                             + grund)

    ordner = _Path(_tempfile.mkdtemp(prefix="bremse_mkt_"))
    echt_bremse, echt_buch = bremse.DATEI, verbrauch.BUCH
    bremse.DATEI = ordner / "kostenbremse.json"
    verbrauch.BUCH = ordner / "verbrauch.jsonl"
    try:
        # Marke genau auf einen Plan: der geht durch, der zweite nicht mehr.
        bremse.setzen(MODUL, monat_eur=round(kampagne.KOSTEN_JE_PLAN_EUR, 5))
        erlaubt, _ = verbrauch.darf(MODUL, kampagne.KOSTEN_JE_PLAN_EUR)
        if not erlaubt:
            raise AssertionError("der erste Plan muss noch durchgehen")
        verbrauch.buchen(MODUL, kampagne.KOSTEN_JE_PLAN_EUR, "erster Plan")
        erlaubt, grund = verbrauch.darf(MODUL, kampagne.KOSTEN_JE_PLAN_EUR)
        if erlaubt:
            raise AssertionError("an der Marke muesste angehalten werden")
    finally:
        bremse.DATEI, verbrauch.BUCH = echt_bremse, echt_buch
        _shutil.rmtree(ordner, ignore_errors=True)

    return ("Plan %.5f EUR: ohne Marke laeuft er, mit Marke genau einer"
            % kampagne.KOSTEN_JE_PLAN_EUR)


if __name__ == "__main__":
    import pruefstand as selbst

    raise SystemExit(selbst._main(["trocken", MODUL]))
