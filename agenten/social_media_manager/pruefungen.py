"""Pruefungen des Social-Media-Managers. Alles trocken, alles kostenlos."""
from __future__ import annotations

import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

import beitrag as B  # noqa: E402
# main.py gibt es im Universe zwoelfmal - ueber den Dateipfad laden, sonst
# erwischt "import main" den Agenten, der zufaellig zuerst geladen wurde.
smm = laden(HIER / "main.py", "social_media_manager_main")
import rueckweg  # noqa: E402
import warenausgang  # noqa: E402

MODUL = "prod.social"


@contextmanager
def wegwerf_vault():
    ordner = tempfile.mkdtemp(prefix="smm_")
    konfig = {"gehirn": {"vault": ordner, "vektor": ordner + "/chroma"}}
    echt_pfade = rueckweg._pfade
    echt_fuellen = rueckweg._regal_fuellen
    echt_wa = warenausgang._meldung
    echt_smm = smm.meldung
    rueckweg._pfade = lambda k=None: echt_pfade(konfig)
    rueckweg._regal_fuellen = lambda *a, **k: None
    warenausgang._meldung = None
    smm.meldung = None
    try:
        yield konfig, Path(ordner)
    finally:
        rueckweg._pfade = echt_pfade
        rueckweg._regal_fuellen = echt_fuellen
        warenausgang._meldung = echt_wa
        smm.meldung = echt_smm
        shutil.rmtree(ordner, ignore_errors=True)


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


def _stueck(K, ordner: Path, freigeben=True, quellen=None, taugt="tiktok, reels"):
    datei = ordner / "clip.mp4"
    datei.write_bytes(b"nicht wirklich ein Video, reicht als Datei")
    warenausgang.einstellen(
        "video", "a1", "prod.video.clip", "Warum dein Schwarm Kontrolle braucht",
        datei=str(datei), gueteklasse="einfach", laenge="25 s",
        format_="hochformat", stimme="de-DE-ConradNeural",
        bildquellen=quellen if quellen is not None else
        "Szene 1: Pexels / MART PRODUCTION\nSzene 2: Pexels / Ron Lach\n"
        "Szene 3: Pexels / MART PRODUCTION",
        kosten=0.0, taugt_fuer=taugt, konfiguration=K)
    if freigeben:
        warenausgang.freigeben("W0001", konfiguration=K)
    return warenausgang.bestand(konfiguration=K)[0]


# ================================================================== Abspann

@anmelden("social.abspann", "prod.social",
          "Jeder Fotograf wird genannt, keiner doppelt", TROCKEN,
          "dass die Namensnennung aus dem Beipackzettel wirklich ankommt")
def abspann_steht():
    zettel = {"titel": "T", "bildquellen":
              "Szene 1: Pexels / MART PRODUCTION\nSzene 2: Pexels / Ron Lach\n"
              "Szene 3: Pexels / MART PRODUCTION",
              "erzeugnis": "x.mp4", "freigegeben_von": "daniel",
              "format": "hochformat", "taugt_fuer": "tiktok"}
    b = B.bauen(zettel, "tiktok")
    _gleich(b.abspann, "Aufnahmen: Pexels / MART PRODUCTION, Pexels / Ron Lach",
            "Abspann")
    return "zwei Namen genannt, die Doppelnennung zusammengefasst"


@anmelden("social.ohne-abspann-blockiert", "prod.social",
          "Ohne nennbare Quelle geht kein Beitrag raus", TROCKEN,
          "dass niemandes Aufnahme unbenannt verwendet wird")
def ohne_abspann_blockiert():
    zettel = {"titel": "T", "bildquellen": "-", "erzeugnis": "x.mp4",
              "freigegeben_von": "daniel", "format": "hochformat"}
    b = B.bauen(zettel, "tiktok")
    _gleich(b.veroeffentlichbar, False, "blockiert")
    if not any("Abspann" in w for w in b.warnungen):
        raise AssertionError("der fehlende Abspann wird nicht bemaengelt")
    return "kein Abspann, kein Beitrag"


@anmelden("social.freigabe-noetig", "prod.social",
          "Ohne deine Freigabe ist nichts veroeffentlichbar", TROCKEN,
          "dass deine Freigabe auch hier zaehlt, nicht nur beim Abholen")
def freigabe_noetig():
    zettel = {"titel": "T", "bildquellen": "Szene 1: Pexels / A",
              "erzeugnis": "x.mp4", "freigegeben_von": "", "format": "hochformat"}
    b = B.bauen(zettel, "tiktok")
    _gleich(b.veroeffentlichbar, False, "blockiert")
    zettel["freigegeben_von"] = "daniel"
    _gleich(B.bauen(zettel, "tiktok").veroeffentlichbar, True, "nach der Freigabe")
    return "ohne Freigabe blockiert, mit Freigabe frei"


# ================================================================== Plattform

@anmelden("social.laengen", "prod.social",
          "Der Text passt in die Grenze der Plattform", TROCKEN,
          "dass ein Beitrag nicht beim Hochladen abgeschnitten wird")
def laengen_passen():
    lang = "Ein sehr langer Titel " * 30
    zettel = {"titel": lang, "bildquellen": "Szene 1: Pexels / A",
              "erzeugnis": "x.mp4", "freigegeben_von": "daniel", "format": "hochformat"}
    for plattform, regeln in B.PLATTFORMEN.items():
        b = B.bauen(zettel, plattform)
        if len(b.als_text()) > regeln["zeichen"]:
            raise AssertionError("%s: %d Zeichen, erlaubt sind %d"
                                 % (plattform, len(b.als_text()), regeln["zeichen"]))
    return "alle fuenf Plattformen innerhalb ihrer Grenze"


@anmelden("social.hochformat", "prod.social",
          "Ein Querformat wird fuer TikTok bemaengelt", TROCKEN,
          "dass kein falsches Format hochgeladen wird")
def hochformat_gefordert():
    zettel = {"titel": "T", "bildquellen": "Szene 1: Pexels / A",
              "erzeugnis": "x.mp4", "freigegeben_von": "daniel",
              "format": "querformat"}
    b = B.bauen(zettel, "tiktok")
    if not any("Hochformat" in w for w in b.warnungen):
        raise AssertionError("das Querformat wird nicht bemaengelt")
    _gleich(B.bauen(zettel, "linkedin").veroeffentlichbar, True,
            "LinkedIn nimmt Querformat")
    return "TikTok bemaengelt Querformat, LinkedIn nicht"


@anmelden("social.x-abspann-in-den-kommentar", "prod.social",
          "Bei knappem Platz wandert der Abspann in den Kommentar", TROCKEN,
          "dass die Nennung auch dort erhalten bleibt, wo 280 Zeichen gelten")
def abspann_in_den_kommentar():
    zettel = {"titel": "Warum dein Schwarm eine Kontrolle braucht",
              "bildquellen": "Szene 1: Pexels / MART PRODUCTION",
              "erzeugnis": "x.mp4", "freigegeben_von": "daniel", "format": "querformat"}
    b = B.bauen(zettel, "x")
    if not b.erster_kommentar:
        raise AssertionError("kein erster Kommentar gebaut")
    if b.abspann in b.als_text():
        raise AssertionError("der Abspann steht doppelt")
    return "Abspann steht im ersten Kommentar, nicht im Text"


# ================================================================== Ablauf

@anmelden("social.holt-nur-freigegebenes", "prod.social",
          "Er holt nichts, was du nicht freigegeben hast", TROCKEN,
          "dass deine Freigabe die Schranke ist, nicht eine Anzeige")
def holt_nur_freigegebenes():
    with wegwerf_vault() as (K, ordner):
        _stueck(K, ordner, freigeben=False)
        _gleich(smm.holen(konfiguration=K), [], "vor der Freigabe")
        warenausgang.freigeben("W0001", konfiguration=K)
        geholt = smm.holen(konfiguration=K)
        _gleich(len(geholt), 1, "nach der Freigabe")
        _gleich(smm.holen(konfiguration=K), [], "beim zweiten Mal nicht noch einmal")
        return "gesperrt bis zur Freigabe, danach genau einmal geholt"


@anmelden("social.blaetter-liegen-bereit", "prod.social",
          "Je Plattform ein Blatt mit Datei, Text und Abspann", TROCKEN,
          "dass du zum Hochladen nichts zusammensuchen musst")
def blaetter_liegen_bereit():
    with wegwerf_vault() as (K, ordner):
        _stueck(K, ordner)
        smm.holen(konfiguration=K)
        ziel = smm._ausgang(K) / "W0001"
        for plattform in ("tiktok", "reels"):
            blatt = ziel / ("%s.txt" % plattform)
            if not blatt.exists():
                raise AssertionError("kein Blatt fuer " + plattform)
            text = blatt.read_text(encoding="utf-8")
            for muss in ("## Datei", "## Text", "Aufnahmen: Pexels"):
                if muss not in text:
                    raise AssertionError("%s fehlt in %s" % (muss, plattform))
        if not (ziel / "clip.mp4").exists():
            raise AssertionError("die Videodatei liegt nicht daneben")
        return "zwei Blaetter plus Videodatei in einem Ordner"


@anmelden("social.rueckmeldung-kommt-an", "prod.social",
          "Die Aussenwirkung landet an der Erfahrung", TROCKEN,
          "dass der Kreis auch von draussen geschlossen wird",
          blind_fuer="ob die gemeldeten Zahlen stimmen")
def rueckmeldung_kommt_an():
    with wegwerf_vault() as (K, ordner):
        rueckweg.erfahrung_ablegen("a1", "prod.video.clip", "ein Clip",
                                   urteil="ja", art=rueckweg.ECHT,
                                   konfiguration=K)
        _stueck(K, ordner)
        smm.holen(konfiguration=K)
        smm.veroeffentlicht("W0001", "tiktok", konfiguration=K)
        _gleich(smm.rueckmeldung("W0001", "1400 Aufrufe, 22 Kommentare",
                                 konfiguration=K), True, "nachgetragen")
        e = rueckweg.erfahrungen("prod.video.clip", art=rueckweg.ECHT,
                                 konfiguration=K)[0]
        _gleich(e.get("aussenwirkung"), "1400 Aufrufe, 22 Kommentare",
                "Aussenwirkung an der Erfahrung")
        return "1400 Aufrufe stehen an der Erfahrung des Auftrags"
