"""Pruefungen der Coding-Agenten: Architekt und Implementierer.

Alles trocken. Kein Modell wird gefragt, nichts wird ins laufende
Universe geschrieben - jede Pruefung, die etwas ablegt, tut das in einem
Ordner, den sie danach wieder wegraeumt.

Der Punkt, auf den es hier ankommt: der Implementierer darf unter keinen
Umstaenden ins laufende Universe schreiben, bevor Daniel freigegeben hat.
Drei der Pruefungen bewachen genau das.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
QM = UNIVERSE / "qualitaetsmanager"
sys.path.insert(0, str(HIER))
for _p in (str(KERN), str(QM)):
    if _p not in sys.path:
        sys.path.append(_p)

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

werkbank = laden(HIER / "werkbank.py", "bau_werkbank")
entwurf = laden(UNIVERSE / "architekt" / "entwurf.py", "bau_entwurf")
pruefliste = laden(QM / "pruefliste.py", "qm_pruefliste")

MODUL = "prod.app"


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


@contextmanager
def _eigenes_universe():
    """Ein leeres Universe auf Zeit - damit keine Pruefung das echte anfasst."""
    ablage = Path(tempfile.mkdtemp(prefix="bau_"))
    echt_w, echt_e = werkbank.UNIVERSE, entwurf.UNIVERSE
    werkbank.UNIVERSE = ablage
    entwurf.UNIVERSE = ablage
    try:
        yield ablage
    finally:
        werkbank.UNIVERSE, entwurf.UNIVERSE = echt_w, echt_e
        shutil.rmtree(ablage, ignore_errors=True)


# ------------------------------------------------------------------ Architekt

@anmelden("bau.plan-ohne-modell-sagt-es-selbst", MODUL,
          "Ein Plan ohne Modell gibt sich als solcher zu erkennen", TROCKEN,
          "dass niemand einen leeren Plan fuer einen fertigen haelt")
def plan_ohne_modell_sagt_es_selbst():
    """Ohne Modell kann der Architekt keine Dateien nennen. Er darf das
    nicht verschweigen - sonst faengt der Implementierer an zu bauen und
    findet nichts."""
    with _eigenes_universe():
        plan = entwurf.entwerfen(
            {"id": "probe1", "text": "Baue einen Zaehler."}, mit_modell=False)
    _gleich(plan.mit_modell, False, "ohne Modell")
    _gleich(plan.vollstaendig, True, "hat Ziel, Dateien und Pruefungen")
    text = " ".join(plan.risiken).lower()
    if "ohne modell" not in text:
        raise AssertionError("Der Plan sagt nicht, dass er ohne Modell entstand")
    return "Notplan entsteht und nennt sich selbst duerftig"


@anmelden("bau.plan-wird-abgelegt-und-wiedergefunden", MODUL,
          "Ein Bauplan laesst sich speichern und wieder laden", TROCKEN,
          "dass zwischen Plan und Bau nichts verlorengeht")
def plan_wird_abgelegt():
    with _eigenes_universe():
        plan = entwurf.entwerfen({"id": "probe2", "text": "Zwei Zahlen addieren."},
                                 mit_modell=False)
        plan.dateien = [{"pfad": "rechner/summe.py", "wofuer": "addiert"}]
        pfad = entwurf.speichern(plan)
        if not pfad.exists():
            raise AssertionError("BAUPLAN.md fehlt")
        zurueck = entwurf.laden("probe2")
        _gleich(zurueck.titel, plan.titel, "Titel")
        _gleich(len(zurueck.dateien), 1, "Dateien")
    return "BAUPLAN.md und bauplan.json werden geschrieben und gelesen"


@anmelden("bau.doppelpunkt-wird-entschaerft", MODUL,
          "Eine Hub-Kennung mit Doppelpunkt wird zu einem Ordnernamen",
          TROCKEN,
          "dass ein Bauordner auf Windows nicht als versteckter Datenstrom "
          "endet")
def doppelpunkt_wird_entschaerft():
    """Derselbe Fund wie beim Verteiler: NTFS deutet den Doppelpunkt als
    Trenner zu einem alternativen Datenstrom."""
    name = entwurf.ordner("auftrag:m3k9x2-a7b1c4").name
    if ":" in name:
        raise AssertionError("Der Doppelpunkt steht noch im Namen: %r" % name)
    return "aus 'auftrag:m3k9x2-a7b1c4' wird '%s'" % name


@anmelden("bau.json-auch-mit-zaun", MODUL,
          "Ein JSON im Backtick-Zaun wird trotzdem gelesen", TROCKEN,
          "dass ein Bauplan nicht an drei Zeichen scheitert")
def json_auch_mit_zaun():
    satz = entwurf._json_heraus('```json\n{"ziel": "x"}\n```')
    if not satz or satz.get("ziel") != "x":
        raise AssertionError("Zaun nicht abgenommen: %r" % satz)
    return "Backticks und Vorspann werden abgenommen"


# ------------------------------------------------------------- Implementierer

@anmelden("bau.pfad-bricht-nicht-aus", MODUL,
          "Ein Pfad, der aus dem Bauordner zeigt, wird abgewiesen", TROCKEN,
          "dass ein Modell nicht mitten ins laufende Universe schreibt")
def pfad_bricht_nicht_aus():
    """Ein Modell, das '../../kern/gehirn.py' vorschlaegt, wuerde ohne
    diese Sperre den Kern ueberschreiben."""
    with tempfile.TemporaryDirectory() as ablage:
        wurzel = Path(ablage)
        if werkbank._im_ordner(wurzel, "../draussen.py") is not None:
            raise AssertionError("'..' kam durch")
        if werkbank._im_ordner(wurzel, "../../kern/gehirn.py") is not None:
            raise AssertionError("Der Kern waere erreichbar gewesen")
        if werkbank._im_ordner(wurzel, "unten/drin.py") is None:
            raise AssertionError("Ein gueltiger Pfad wurde abgewiesen")
    return "'..' wird abgewiesen, normale Pfade kommen durch"


@anmelden("bau.uebersetzungsfehler-faellt-auf", MODUL,
          "Code, der nicht uebersetzt, wird als solcher erkannt", TROCKEN,
          "dass kaputter Code nicht als fertig gemeldet wird")
def uebersetzungsfehler_faellt_auf():
    with _eigenes_universe():
        ordner = werkbank.neubau("probe3")
        ordner.mkdir(parents=True)
        (ordner / "heil.py").write_text(
            "def zwei():\n    return 2\n", encoding="utf-8", newline="")
        (ordner / "kaputt.py").write_text(
            "def offen(\n", encoding="utf-8", newline="")
        bericht = werkbank.messen("probe3")
    _gleich(bericht["uebersetzt"], False, "uebersetzt")
    _gleich(bericht["dateien"], 2, "Dateien gezaehlt")
    if not any("kaputt.py" in f for f in bericht["uebersetzungsfehler"]):
        raise AssertionError("Die kaputte Datei wurde nicht benannt")
    return "kaputt.py wird benannt, heil.py nicht"


@anmelden("bau.pruefungen-werden-gezaehlt", MODUL,
          "Die Pruefungen eines Baus werden gelesen, nicht geglaubt", TROCKEN,
          "dass der Qualitaetsmanager echte Zahlen bekommt")
def pruefungen_werden_gezaehlt():
    with _eigenes_universe():
        ordner = werkbank.neubau("probe4")
        ordner.mkdir(parents=True)
        (ordner / "pruefungen.py").write_text(
            'print("3 bestanden, 1 durchgefallen, 0 uebersprungen")\n',
            encoding="utf-8", newline="")
        bericht = werkbank.messen("probe4")
    _gleich(bericht["pruefungen_gelaufen"], True, "gelaufen")
    _gleich(bericht["bestanden"], 3, "bestanden")
    _gleich(bericht["durchgefallen"], 1, "durchgefallen")
    return "3 bestanden, 1 durchgefallen werden aus der Ausgabe gelesen"


@anmelden("bau.abnahme-laesst-kaputtes-nicht-durch", MODUL,
          "Der Qualitaetsmanager weist einen Bau ohne Pruefbericht ab",
          TROCKEN,
          "dass nur belegter Code vorgelegt wird")
def abnahme_laesst_kaputtes_nicht_durch():
    with tempfile.TemporaryDirectory() as ablage:
        bau = Path(ablage) / "neu"
        bau.mkdir()
        (bau / "x.py").write_text("x = 1\n", encoding="utf-8", newline="")

        ohne = pruefliste.hart_pruefen("code", bau)
        if ohne.bestanden:
            raise AssertionError("Ein Bau ohne Pruefbericht kam durch")

        (Path(ablage) / "pruefbericht.json").write_text(json.dumps({
            "dateien": 2, "zeilen": 40, "uebersetzt": False,
            "uebersetzungsfehler": ["x.py: unerwartetes Ende"],
            "pruefungen_gelaufen": True, "bestanden": 0, "durchgefallen": 2,
        }), encoding="utf-8", newline="")
        kaputt = pruefliste.hart_pruefen("code", bau)
        if kaputt.bestanden:
            raise AssertionError("Ein Bau, der nicht uebersetzt, kam durch")
        if len(kaputt.maengel) < 2:
            raise AssertionError("Nur ein Mangel genannt: %r" % kaputt.maengel)

        (Path(ablage) / "pruefbericht.json").write_text(json.dumps({
            "dateien": 2, "zeilen": 40, "uebersetzt": True,
            "uebersetzungsfehler": [],
            "pruefungen_gelaufen": True, "bestanden": 3, "durchgefallen": 0,
        }), encoding="utf-8", newline="")
        heil = pruefliste.hart_pruefen("code", bau)
        if not heil.bestanden:
            raise AssertionError("Ein heiler Bau wurde abgewiesen: %r"
                                 % heil.maengel)
    return "ohne Bericht und mit Uebersetzungsfehler abgewiesen, heil durch"


@anmelden("bau.uebernahme-sichert-vorher", MODUL,
          "Vor dem Ueberschreiben liegt die alte Datei als Kopie", TROCKEN,
          "dass der Rueckweg eine Kopie ist und kein Rateschritt")
def uebernahme_sichert_vorher():
    with _eigenes_universe() as ablage:
        alt = ablage / "kern" / "beispiel.py"
        alt.parent.mkdir(parents=True)
        alt.write_text("alt = 1\n", encoding="utf-8", newline="")

        neu = werkbank.neubau("probe5") / "kern"
        neu.mkdir(parents=True)
        (neu / "beispiel.py").write_text("neu = 2\n", encoding="utf-8", newline="")

        ergebnis = werkbank.uebernehmen("probe5")
        _gleich(alt.read_text(encoding="utf-8"), "neu = 2\n", "uebernommen")
        sicherung = (werkbank.neubau("probe5").parent / "vorher"
                     / "kern" / "beispiel.py")
        if not sicherung.exists():
            raise AssertionError("Keine Sicherung angelegt")
        _gleich(sicherung.read_text(encoding="utf-8"), "alt = 1\n", "Sicherung")
        _gleich(len(ergebnis["kopiert"]), 1, "kopiert")
    return "die alte Datei liegt unter <bau>/vorher/"


@anmelden("bau.nichts-ins-universe-ohne-freigabe", MODUL,
          "Ohne Freigabe wird weder gebaut noch uebernommen", TROCKEN,
          "dass sich das System nicht selbst umbaut",
          blind_fuer="einen Warenausgang, der falsche Staende meldet")
def nichts_ins_universe_ohne_freigabe():
    """Die wichtigste Pruefung hier. Ein Agent, der sich selbst aendern
    darf, waehrend er laeuft, kann sich in einen Zustand bringen, aus dem
    heraus er den Fehler nicht mehr melden kann."""
    quelle = (HIER / "main.py").read_text(encoding="utf-8")

    def rumpf(name: str) -> str:
        auf = quelle.index("\ndef %s(" % name)
        zu = quelle.find("\ndef ", auf + 1)
        return quelle[auf:zu if zu > 0 else len(quelle)]

    for name in ("bauen", "uebernehmen"):
        if "FREIGEGEBEN" not in rumpf(name):
            raise AssertionError(
                "%s() fragt nicht nach der Freigabe" % name)
    if "werkbank.uebernehmen" not in rumpf("uebernehmen"):
        raise AssertionError("Die Uebernahme laeuft nicht ueber die Werkbank")
    return "bauen() und uebernehmen() fragen beide nach der Freigabe"


# ------------------------------------------------------------------ Schleife und Fingerabdruck

schleife = laden(HIER / "schleife.py", "bau_schleife")


def _bericht(*, uebersetzt=True, durchgefallen=0, dateien=2):
    return {"dateien": dateien, "zeilen": 10, "uebersetzt": uebersetzt,
            "uebersetzungsfehler": [] if uebersetzt else ["x.py: invalid syntax"],
            "pruefungen_gelaufen": durchgefallen > 0, "bestanden": 0,
            "durchgefallen": durchgefallen, "ausgabe": ""}


def _werkzeug_das_zaehlt(aufrufe: list):
    def werkzeug(text, ordner):
        aufrufe.append((text, ordner))
        return {"usage": None, "usd": 0.0, "text": "", "art": "success", "schritte": 3}
    return werkzeug


@anmelden("bau.schleife-haelt-nach-fuenf-runden", MODUL,
          "Die Nachbesserung hoert nach hoechstens fuenf Runden auf und sagt es", TROCKEN,
          "dass eine Schleife, die nie gruen wird, nicht ewig laeuft und nicht stumm endet",
          blind_fuer="ob das Werkzeug in einer Runde wirklich etwas Sinnvolles aendert")
def schleife_haelt_nach_fuenf_runden():
    aufrufe = []
    with _eigenes_universe():
        stand = schleife.nachbessern(
            "probe6", {"ziel": "x", "dateien": []}, _bericht(uebersetzt=False),
            werkzeug=_werkzeug_das_zaehlt(aufrufe),
            messen=lambda auftrag, plan: _bericht(uebersetzt=False))
    _gleich(stand["halt"], schleife.RUNDEN_ERSCHOEPFT, "Halt")
    _gleich(stand["runden"], 5, "genau fuenf Runden")
    _gleich(len(aufrufe), 5, "das Werkzeug lief genau fuenf Mal")
    if "Runde 5 von 5" not in aufrufe[-1][0]:
        raise AssertionError("die letzte Runde weiss nicht, dass sie die letzte ist")
    if not stand["grund"]:
        raise AssertionError("der Halt nennt keinen Grund")
    return "fuenf Runden, dann Halt 'runden-erschoepft' mit Grund"


@anmelden("bau.schleife-hoert-auf-wenn-gruen", MODUL,
          "Die Nachbesserung hoert auf, sobald der Bau gruen ist - und faengt bei gruen gar nicht an",
          TROCKEN, "dass keine Runde gekauft wird, die nichts mehr zu tun hat")
def schleife_hoert_auf_wenn_gruen():
    aufrufe = []
    with _eigenes_universe():
        stand = schleife.nachbessern(
            "probe7", {"ziel": "x", "dateien": []}, _bericht(),
            werkzeug=_werkzeug_das_zaehlt(aufrufe), messen=lambda a, p: _bericht())
        _gleich((stand["halt"], stand["runden"], len(aufrufe)),
                (schleife.GRUEN, 0, 0), "gruen: keine Runde")

        zaehler = {"n": 0}

        def messen(auftrag, plan):
            zaehler["n"] += 1
            return _bericht(durchgefallen=0 if zaehler["n"] >= 2 else 1)

        stand = schleife.nachbessern(
            "probe7", {"ziel": "x", "dateien": []}, _bericht(durchgefallen=1),
            werkzeug=_werkzeug_das_zaehlt(aufrufe), messen=messen)
        _gleich((stand["halt"], stand["runden"], len(aufrufe)),
                (schleife.NACHGEBESSERT, 2, 2), "nach der zweiten Runde gruen")

        stand = schleife.nachbessern(
            "probe7", {"ziel": "x", "dateien": []}, _bericht(uebersetzt=False, dateien=0),
            werkzeug=_werkzeug_das_zaehlt(aufrufe), messen=messen)
        _gleich((stand["halt"], len(aufrufe)), (schleife.NICHTS_GEBAUT, 2), "ohne Dateien keine Runde")
    return "gruen -> 0 Runden; gruen nach Runde 2 -> Halt; ohne Dateien -> keine Runde"


@anmelden("bau.werkzeug-bleibt-im-bauordner", MODUL,
          "Das Werkzeug der Nachbesserung darf nur im Bauordner lesen und schreiben", TROCKEN,
          "dass die Schleife nicht ins laufende Universe schreibt und keine Befehle ausfuehrt")
def werkzeug_bleibt_im_bauordner():
    with _eigenes_universe() as ablage:
        ordner = werkbank.neubau("probe8")
        ordner.mkdir(parents=True)
        ja, _ = schleife.darf_werkzeug(ordner, "Write", {"file_path": str(ordner / "a.py")})
        _gleich(ja, True, "Schreiben im Bauordner")
        ja, _ = schleife.darf_werkzeug(ordner, "Edit", {"file_path": "unter/b.py"})
        _gleich(ja, True, "relativ im Bauordner")
        nein, grund = schleife.darf_werkzeug(ordner, "Write", {"file_path": "../../kern/gehirn.py"})
        _gleich(nein, False, "heraus aus dem Bauordner")
        nein, _ = schleife.darf_werkzeug(ordner, "Read", {"file_path": str(ablage / "kern" / "x.py")})
        _gleich(nein, False, "auch Lesen nicht ausserhalb")
        nein, grund = schleife.darf_werkzeug(ordner, "Bash", {"command": "python pruefungen.py"})
        _gleich(nein, False, "keine Befehle")
        if "Bash" not in grund:
            raise AssertionError("der Grund nennt das Werkzeug nicht")
        nein, _ = schleife.darf_werkzeug(ordner, "WebFetch", {"url": "https://x"})
        _gleich(nein, False, "kein Netz")
    return "innen ja, aussen nein, Bash nein, Netz nein"


@anmelden("bau.uebernahme-nur-unveraendert", MODUL,
          "Uebernommen wird nur der Stand, der vorgelegt wurde", TROCKEN,
          "dass eine Freigabe nicht fuer etwas gilt, das nach der Vorlage geaendert wurde")
def uebernahme_nur_unveraendert():
    with _eigenes_universe():
        neu = werkbank.neubau("probe9")
        neu.mkdir(parents=True)
        (neu / "a.py").write_text("a = 1\n", encoding="utf-8", newline="")
        nein, grund = werkbank.uebernahme_erlaubt("probe9")
        _gleich(nein, False, "ohne Vorlage keine Uebernahme")
        satz = werkbank.vorgelegt_merken("probe9", "wa1")
        _gleich(len(satz["fingerabdruck"]), 12, "Abdruck zwoelf Zeichen")
        ja, _ = werkbank.uebernahme_erlaubt("probe9")
        _gleich(ja, True, "unveraendert: erlaubt")
        (neu / "a.py").write_text("a = 2\n", encoding="utf-8", newline="")
        nein, grund = werkbank.uebernahme_erlaubt("probe9")
        _gleich(nein, False, "geaendert: verweigert")
        if "geaendert" not in grund:
            raise AssertionError("der Grund sagt nicht, dass sich etwas geaendert hat")
        (neu / "b.py").write_text("b = 1\n", encoding="utf-8", newline="")
        (neu / "a.py").write_text("a = 1\n", encoding="utf-8", newline="")
        nein, _ = werkbank.uebernahme_erlaubt("probe9")
        _gleich(nein, False, "eine Datei dazu: verweigert")
    quelle = (HIER / "main.py").read_text(encoding="utf-8")
    auf = quelle.index("\ndef uebernehmen(")
    if "uebernahme_erlaubt" not in quelle[auf:quelle.find("\ndef ", auf + 1)]:
        raise AssertionError("main.uebernehmen() fragt den Fingerabdruck nicht ab")
    return "ohne Vorlage nein, unveraendert ja, geaendert nein, Datei dazu nein"


@anmelden("bau.marke-haelt-den-bau-an", MODUL,
          "Eine Marke des Nutzers haelt den Bau an, bevor sie ueberschritten wird",
          TROCKEN,
          "dass die Marke wirkt, ohne einen Bau schon am Anfang abzulehnen",
          blind_fuer="ob die Schaetzung selbst stimmt - das zeigt erst ein "
                     "echter Lauf")
def marke_haelt_den_bau_an():
    """Frueher stand hier ein fester Deckel, und genau daran ist es einmal
    gescheitert: der Implementierer fragte nach 0,60 EUR, der Topf 'denken'
    erlaubte 0,50 EUR je Lauf, Antwort nein. Er haette nie eine Datei
    geschrieben, und aufgefallen waere es erst beim ersten echten Bau.

    Feste Deckel gibt es nicht mehr - die Grenze setzt der Nutzer. Was
    bleibt, ist die Frage dahinter: Ein einzelner SCHRITT muss durchgehen,
    solange die Marke des Nutzers nicht erreicht ist, und ein voller
    Bauplan darf sie ausschoepfen, ohne sie zu sprengen. Sonst bricht ein
    Bau mittendrin ab und laesst halbe Dateien liegen.
    """
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "kern"))
    import verbrauch
    import bremse
    import shutil as _shutil
    import tempfile as _tempfile

    ohne_marke, _ = verbrauch.darf(MODUL, entwurf.KOSTEN_JE_ENTWURF_EUR)
    if not ohne_marke:
        raise AssertionError("ohne gesetzte Marke darf nichts abgelehnt werden")

    ordner = _Path(_tempfile.mkdtemp(prefix="bremse_bau_"))
    echt_bremse, echt_buch = bremse.DATEI, verbrauch.BUCH
    bremse.DATEI = ordner / "kostenbremse.json"
    verbrauch.BUCH = ordner / "verbrauch.jsonl"
    try:
        voll = werkbank.KOSTEN_JE_DATEI_EUR * entwurf.DATEIEN_HOECHSTENS
        # Die Marke liegt genau auf einem vollen Bauplan: er muss
        # hineinpassen, jeder einzelne Schritt erst recht.
        bremse.setzen(MODUL, lauf_eur=round(voll, 4))

        for name, betrag in (("Entwurf", entwurf.KOSTEN_JE_ENTWURF_EUR),
                             ("eine Datei", werkbank.KOSTEN_JE_DATEI_EUR),
                             ("ein voller Bauplan", voll)):
            erlaubt, grund = verbrauch.darf(MODUL, betrag)
            if not erlaubt:
                raise AssertionError("%s wird abgelehnt: %s" % (name, grund))

        # Ein ANGEFANGENER Lauf laeuft ueber die Marke hinaus zu Ende -
        # so entschieden, damit nichts Halbes liegen bleibt.
        erlaubt, grund = verbrauch.darf(MODUL, werkbank.KOSTEN_JE_DATEI_EUR,
                                        schon_im_lauf=voll)
        if not erlaubt:
            raise AssertionError("ein angefangener Bau muss fertig werden duerfen")

        # Ein NEUER Lauf faengt ueber der Marke nicht an. Marke so klein,
        # dass schon der Entwurf sie sprengt.
        bremse.setzen(MODUL, lauf_eur=round(entwurf.KOSTEN_JE_ENTWURF_EUR / 2, 6))
        erlaubt, _ = verbrauch.darf(MODUL, entwurf.KOSTEN_JE_ENTWURF_EUR)
        if erlaubt:
            raise AssertionError("ueber der Marke faengt kein neuer Lauf an")
    finally:
        bremse.DATEI, verbrauch.BUCH = echt_bremse, echt_buch
        _shutil.rmtree(ordner, ignore_errors=True)

    return ("Entwurf %.3f, Datei %.3f, voller Bauplan %.3f EUR - ohne Marke "
            "laeuft alles; mit Marke passt der volle Bauplan hinein, ein "
            "angefangener Bau wird fertig, ein neuer faengt darueber nicht an"
            % (entwurf.KOSTEN_JE_ENTWURF_EUR, werkbank.KOSTEN_JE_DATEI_EUR, voll))


if __name__ == "__main__":
    import pruefstand as selbst

    raise SystemExit(selbst._main(["trocken", MODUL]))
