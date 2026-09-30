"""Pruefungen fuer den Qualitaetsmanager.

Die Echttests bauen sich ihr Pruefmaterial mit ffmpeg selbst - ein
Sekundenvideo aus Farbbalken und einem Sinuston. Das kostet nichts und
laeuft trotzdem gegen echte Dateien und echtes ffprobe.
"""
from __future__ import annotations

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
from contextlib import contextmanager
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

import pruefliste  # noqa: E402
# Ueber den Dateipfad laden: main.py gibt es zwoelfmal im Universe.
qm = laden(HIER / "main.py", "qualitaetsmanager_main")
import rueckweg  # noqa: E402
import warenausgang  # noqa: E402


@contextmanager
def wegwerf_vault():
    ordner = tempfile.mkdtemp(prefix="qm_pruefung_")
    konfig = {"gehirn": {"vault": ordner, "vektor": ordner + "/chroma"}}
    echt_pfade = rueckweg._pfade
    echt_fuellen = rueckweg._regal_fuellen
    echt_meldung = warenausgang._meldung
    echt_qm_meldung = qm.meldung
    rueckweg._pfade = lambda k=None: echt_pfade(konfig)
    rueckweg._regal_fuellen = lambda *a, **k: None
    warenausgang._meldung = None
    qm.meldung = None
    try:
        yield konfig, Path(ordner)
    finally:
        rueckweg._pfade = echt_pfade
        rueckweg._regal_fuellen = echt_fuellen
        warenausgang._meldung = echt_meldung
        qm.meldung = echt_qm_meldung
        shutil.rmtree(ordner, ignore_errors=True)


def _video_bauen(ziel: Path, sekunden: float = 6.0, breite: int = 1080,
                 hoehe: int = 1920, mit_ton: bool = True) -> Path:
    """Ein Pruefvideo aus Farbbalken und Sinuston. Kostet nichts."""
    befehl = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
              "-f", "lavfi", "-i",
              "testsrc=size=%dx%d:rate=25:duration=%s" % (breite, hoehe, sekunden)]
    if mit_ton:
        befehl += ["-f", "lavfi", "-i", "sine=frequency=440:duration=%s" % sekunden,
                   "-c:a", "aac", "-shortest"]
    befehl += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(sekunden), str(ziel)]
    subprocess.run(befehl, capture_output=True, timeout=180, check=True)
    return ziel


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


# ================================================================== Messen

@anmelden("qm.misst-video", "system.qm",
          "Er misst Laenge, Aufloesung und Tonspur richtig", TROCKEN,
          "dass die harten Zahlen aus der Datei kommen, nicht aus einer Annahme",
          blind_fuer="ob das Video inhaltlich taugt")
def misst_video():
    with tempfile.TemporaryDirectory() as ordner:
        datei = _video_bauen(Path(ordner) / "gut.mp4", 6.0, 1080, 1920, True)
        befund = pruefliste.hart_pruefen("video", datei)
        _gleich(round(befund.gemessen["sekunden"]), 6, "Laenge")
        _gleich(befund.gemessen["breite"], 1080, "Breite")
        _gleich(befund.gemessen["hoehe"], 1920, "Hoehe")
        _gleich(befund.gemessen["hat_ton"], True, "Tonspur")
        _gleich(befund.bestanden, True, "keine Maengel")
        return "6 s, 1080x1920, Ton da - ohne Mangel"


@anmelden("qm.findet-fehlenden-ton", "system.qm",
          "Ein Video ohne Ton faellt durch", TROCKEN,
          "dass eine fehlende Tonspur nicht durchrutscht")
def findet_fehlenden_ton():
    with tempfile.TemporaryDirectory() as ordner:
        datei = _video_bauen(Path(ordner) / "stumm.mp4", 6.0, mit_ton=False)
        befund = pruefliste.hart_pruefen("video", datei)
        _gleich(befund.bestanden, False, "faellt durch")
        if not any("Tonspur" in m for m in befund.maengel):
            raise AssertionError("der Mangel heisst nicht nach der Tonspur: %s"
                                 % befund.maengel)
        return "stummes Video als Mangel erkannt"


@anmelden("qm.findet-zu-kurz", "system.qm",
          "Ein zu kurzes Stueck faellt durch", TROCKEN,
          "dass ein abgebrochener Lauf auffaellt")
def findet_zu_kurz():
    with tempfile.TemporaryDirectory() as ordner:
        # Gross genug, dass die Groessenschwelle (0,05 MB) nicht vorher
        # zuschlaegt: ein kleines Ein-Sekunden-Video faellt als "fast leer"
        # durch, und die Laengenmessung liefe nie. Genau so stand es hier -
        # aufgefallen ist es erst durch die Gegenprobe.
        datei = _video_bauen(Path(ordner) / "kurz.mp4", 1.0, 2160, 3840)
        befund = pruefliste.hart_pruefen("video", datei)
        _gleich(befund.bestanden, False, "faellt durch")
        # Nicht nur DASS es durchfaellt, sondern WORAN. Ein Ein-Sekunden-Video
        # ist auch klein und still - ohne diese Zeile waere die Pruefung gruen
        # geblieben, selbst wenn die Laengenmessung ganz ausgebaut waere.
        if not any("Sekunde" in m for m in befund.maengel):
            raise AssertionError(
                "es faellt durch, aber nicht wegen der Laenge: %s" % befund.maengel)
        _gleich(round(befund.gemessen.get("sekunden", 0)), 1, "gemessene Laenge")
        return "1-Sekunden-Video als zu kurz erkannt, nicht nur als kaputt"


@anmelden("qm.fehlende-datei", "system.qm",
          "Eine fehlende Datei faellt durch statt zu krachen", TROCKEN,
          "dass der Pruefer bei fehlendem Material nicht abstuerzt")
def fehlende_datei():
    befund = pruefliste.hart_pruefen("video", "C:/gibt/es/nicht.mp4")
    _gleich(befund.bestanden, False, "faellt durch")
    return "fehlende Datei sauber als Mangel gemeldet"


# ================================================================== Zettel

@anmelden("qm.zettel-unvollstaendig", "system.qm",
          "Ein lueckenhafter Beipackzettel faellt durch", TROCKEN,
          "dass nichts ohne Herkunft in den Warenausgang kommt")
def zettel_unvollstaendig():
    maengel = pruefliste.zettel_pruefen(
        {"was": "video", "auftrag": "a1", "modul": "prod.video.clip",
         "titel": "", "abgenommen_von": "qualitaetsmanager"})
    if not any("titel" in m for m in maengel):
        raise AssertionError("fehlender Titel wurde nicht bemaengelt: %s" % maengel)
    ohne_quellen = pruefliste.zettel_pruefen(
        {"was": "video", "auftrag": "a1", "modul": "prod.video.clip",
         "titel": "T", "abgenommen_von": "qm", "bildquellen": "-"})
    if not any("Bildquellen" in m for m in ohne_quellen):
        raise AssertionError("fehlende Bildquellen wurden nicht bemaengelt")
    return "fehlender Titel und fehlende Bildquellen erkannt"


# ================================================================== Gelernt

@anmelden("qm.lehrsatz-wird-pruefung", "system.qm",
          "Ein Lehrsatz mit Zahl wird zur echten Messung", TROCKEN,
          "dass aus 'gelernt' tatsaechlich 'geprueft' wird",
          blind_fuer="Lehrsaetze ohne Zahl - die bleiben Merkposten")
def lehrsatz_wird_pruefung():
    befund = pruefliste.Befund(was="video", gemessen={"sekunden": 12.0})
    pruefliste.aus_lehrsaetzen(
        [{"kennung": "L0001", "satz": "Ein Clip darf hoechstens 10 Sekunden lang sein."},
         {"kennung": "L0002", "satz": "Der Aufhaenger gehoert nach vorn."}],
        befund)
    _gleich(len(befund.maengel), 1, "ein Mangel aus dem messbaren Satz")
    if "L0001" not in befund.maengel[0]:
        raise AssertionError("der Mangel nennt den Lehrsatz nicht")
    _gleich(len(befund.merkposten), 1, "der unmessbare Satz bleibt Merkposten")
    _gleich(befund.geprueft_gegen, ["L0001", "L0002"], "beide vermerkt")
    return "Satz mit Zahl wurde Messung, Satz ohne Zahl wurde Merkposten"


@anmelden("qm.mindestens-dreht-die-richtung", "system.qm",
          "'mindestens' macht aus der Zahl eine Untergrenze", TROCKEN,
          "dass eine Regel nicht in die falsche Richtung greift")
def mindestens_dreht_die_richtung():
    zu_kurz = pruefliste.Befund(was="video", gemessen={"sekunden": 8.0})
    pruefliste.aus_lehrsaetzen(
        [{"kennung": "L0003", "satz": "Ein Clip soll mindestens 15 Sekunden laufen."}],
        zu_kurz)
    _gleich(len(zu_kurz.maengel), 1, "8 s verletzt die Untergrenze 15 s")
    lang_genug = pruefliste.Befund(was="video", gemessen={"sekunden": 20.0})
    pruefliste.aus_lehrsaetzen(
        [{"kennung": "L0003", "satz": "Ein Clip soll mindestens 15 Sekunden laufen."}],
        lang_genug)
    _gleich(len(lang_genug.maengel), 0, "20 s ist in Ordnung")
    return "8 s bemaengelt, 20 s durchgelassen"


# ================================================================== Entscheiden

@anmelden("qm.bestanden-geht-in-den-warenausgang", "system.qm",
          "Ein sauberes Stueck landet im Warenausgang", TROCKEN,
          "dass der Weg vom Agenten bis zu deiner Freigabe steht")
def bestanden_geht_weiter():
    with wegwerf_vault() as (K, vault):
        datei = _video_bauen(vault / "gut.mp4", 6.0)
        ergebnis = qm.abnehmen("video", datei, "a1", "prod.video.clip",
                               "Pruefclip", durchlaeufe=1,
                               zettel={"bildquellen": "testsrc"},
                               konfiguration=K)
        _gleich(ergebnis["urteil"], qm.Urteil.VORLEGEN, "Urteil")
        zettel = warenausgang.bestand(konfiguration=K)
        _gleich(len(zettel), 1, "ein Stueck im Warenausgang")
        _gleich(zettel[0]["stand"], warenausgang.WARTET, "wartet auf deine Freigabe")
        _gleich(zettel[0]["abgenommen_von"], "qualitaetsmanager", "abgenommen von")
        return "abgenommen, eingestellt, wartet auf Freigabe"


@anmelden("qm.zurueck-hoechstens-zweimal", "system.qm",
          "Beim dritten Durchfallen bleibt das Stueck liegen", TROCKEN,
          "dass kein Auftrag endlos Geld verbrennt")
def zurueck_hoechstens_zweimal():
    with wegwerf_vault() as (K, vault):
        datei = _video_bauen(vault / "stumm.mp4", 6.0, mit_ton=False)
        for durchlauf in (1, 2):
            e = qm.abnehmen("video", datei, "a2", "prod.video.stueck", "Stumm",
                            durchlaeufe=durchlauf, konfiguration=K)
            _gleich(e["urteil"], qm.Urteil.ZURUECK, "Durchlauf %d" % durchlauf)
        e = qm.abnehmen("video", datei, "a2", "prod.video.stueck", "Stumm",
                        durchlaeufe=3, kosten=0.29, konfiguration=K)
        _gleich(e["urteil"], qm.Urteil.LIEGEN_LASSEN, "dritter Durchlauf")
        _gleich(len(warenausgang.bestand(konfiguration=K)), 0,
                "nichts im Warenausgang")
        h = rueckweg.halde(konfiguration=K)
        _gleich(len(h), 1, "ein Eintrag auf der Halde")
        erfahrungen = rueckweg.erfahrungen("prod.video.stueck", konfiguration=K)
        _gleich(len(erfahrungen), 1, "eine Erfahrung abgelegt")
        _gleich(erfahrungen[0]["urteil"], "nein", "als Nein abgelegt")
        return "zweimal zurueck, beim dritten Mal Halde und Erfahrung"


@anmelden("qm.mangel-blockiert-warenausgang", "system.qm",
          "Ein Stueck mit Mangel kommt nie in den Warenausgang", TROCKEN,
          "dass du nichts vorgelegt bekommst, was messbar kaputt ist")
def mangel_blockiert():
    with wegwerf_vault() as (K, vault):
        # Wieder gross genug, damit die Laenge blockiert und nicht die Groesse.
        datei = _video_bauen(vault / "kurz.mp4", 1.0, 2160, 3840)
        e = qm.abnehmen("video", datei, "a3", "prod.video.clip", "Zu kurz",
                        durchlaeufe=1,
                        # Ein vollstaendiger Zettel - sonst blockiert der
                        # Zettel und nicht die Messung, und die Pruefung
                        # saehe genauso aus, wenn gar nicht gemessen wuerde.
                        zettel={"gueteklasse": "clip", "bildquellen": "testsrc",
                                "stimme": "-", "taugt_fuer": "Probe"},
                        konfiguration=K)
        _gleich(e["urteil"], qm.Urteil.ZURUECK, "Urteil")
        _gleich(warenausgang.bestand(konfiguration=K), [], "Warenausgang leer")
        if not any("Sekunde" in m for m in e["befund"].maengel):
            raise AssertionError(
                "der Zettel war vollstaendig - blockiert hat also nicht die "
                "Messung: %s" % e["befund"].maengel)
        return "die Messung blockiert, nicht der Zettel"


# ---------------------------------------------- Worauf das Stueck stand
#
# Der Stoffbeschaffer misst vor dem Lauf, wie gut ein Thema im 2nd Brain
# gedeckt ist. Diese Messung darf unterwegs nicht verlorengehen: sie gehoert
# auf den Beipackzettel und in die Erfahrung. Ohne sie sieht ein Stueck, das
# auf nichts stand, spaeter genauso aus wie eines auf zwanzig Funden.

@anmelden("qm.deckung-steht-auf-dem-beipackzettel", "system.qm",
          "Ein duenn gedecktes Stueck sagt das auf seinem Zettel", TROCKEN,
          "dass niemand fuer belegt haelt, was nirgends belegt ist")
def deckung_steht_auf_dem_beipackzettel():
    with wegwerf_vault() as (K, vault):
        datei = _video_bauen(vault / "duenn.mp4", 6.0)
        qm.abnehmen("video", datei, "a4", "prod.video.clip", "Duenn gedeckt",
                    durchlaeufe=1,
                    zettel={"bildquellen": "testsrc", "deckung": "duenn",
                            "deckung_satz": "Nur 2 brauchbare Funde."},
                    konfiguration=K)
        zettel = warenausgang.bestand(konfiguration=K)
        _gleich(len(zettel), 1, "ein Stueck im Warenausgang")
        notiz = zettel[0].get("notiz", "")
        if "Nur 2 brauchbare Funde" not in notiz:
            raise AssertionError(
                "auf dem Zettel steht nicht, worauf das Stueck stand: %r" % notiz[-160:])
        if "nicht durch eigenes Wissen belegt" not in notiz:
            raise AssertionError(
                "bei duenner Deckung fehlt der Hinweis, vorher nachzusehen")

        # Und ein gut gedecktes Stueck bekommt keinen Warnsatz angehaengt.
        datei2 = _video_bauen(vault / "gut2.mp4", 6.0)
        qm.abnehmen("video", datei2, "a5", "prod.video.clip", "Gut gedeckt",
                    durchlaeufe=1,
                    zettel={"bildquellen": "testsrc", "deckung": "gut",
                            "deckung_satz": "12 Funde, davon 7 brauchbar."},
                    konfiguration=K)
        zwei = [z for z in warenausgang.bestand(konfiguration=K)
                if z.get("titel") == "Gut gedeckt"]
        _gleich(len(zwei), 1, "auch das zweite Stueck steht drin")
        if "nicht durch eigenes Wissen belegt" in zwei[0].get("notiz", ""):
            raise AssertionError("ein gut gedecktes Stueck wird gewarnt")
        return "duenn wird vermerkt und gewarnt, gut nur vermerkt"


@anmelden("qm.deckung-steht-in-der-erfahrung", "system.qm",
          "Die Erfahrung haelt fest, worauf das Stueck stand", TROCKEN,
          "dass beim Lernen ein Nein von leerem Regal unterscheidbar bleibt")
def deckung_steht_in_der_erfahrung():
    with wegwerf_vault() as (K, vault):
        datei = _video_bauen(vault / "stumm2.mp4", 6.0, mit_ton=False)
        for durchlauf in (1, 2, 3):
            qm.abnehmen("video", datei, "a6", "prod.video.stueck", "Stumm",
                        durchlaeufe=durchlauf,
                        zettel={"deckung": "leer",
                                "deckung_satz": "Zum Thema liegt nichts im 2nd Brain."},
                        konfiguration=K)
        erfahrungen = rueckweg.erfahrungen("prod.video.stueck", konfiguration=K)
        _gleich(len(erfahrungen), 1, "eine Erfahrung abgelegt")
        if erfahrungen[0].get("deckung") != "leer":
            raise AssertionError(
                "die Erfahrung sagt nicht, worauf das Stueck stand: %r"
                % erfahrungen[0].get("deckung"))
        return "die Erfahrung traegt die Deckung im Kopf"
