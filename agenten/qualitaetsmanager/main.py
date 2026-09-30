"""Qualitaetsmanager - er nimmt ab, bevor du es siehst.

Er sitzt in jeder Produktionsstrasse. Was er tut, in einem Satz: er misst,
was sich messen laesst, haelt es gegen die bestaetigten Lehrsaetze und
entscheidet, ob das Stueck dir vorgelegt oder zurueckgeschickt wird.

Der Weg eines Stuecks durch ihn:

    Agent meldet fertig
        -> harte Messung        Datei, Laenge, Aufloesung, Ton, Stille
        -> Beipackzettel        alle Pflichtfelder da, Bildquellen belegt
        -> Lehrsaetze           was aus frueheren Neins gelernt wurde
        -> bestanden?
             ja   -> in den Warenausgang, du wirst gefragt
             nein -> zurueck in die Strasse, hoechstens zweimal
             dreimal durchgefallen -> FEHLER, mit Grund auf die Halde

Was er ausdruecklich NICHT tut: ueber Geschmack urteilen. Ob ein Schnitt gut
sitzt, entscheidet kein Grenzwert. Dafuer gibt es den Kontaktbogen - ein
Blatt mit gleichmaessig verteilten Einzelbildern - und, wenn du es
einschaltest, ein Modell. Beides kostet und ist deshalb abschaltbar.

Aufruf:
    python main.py pruefen video <datei> --auftrag a1 --modul prod.video.clip
    python main.py abnehmen  <dieselben Angaben>   pruefen und einstellen
    python main.py liste                            was er gerade geprueft hat
    python main.py grenzen                          welche Werte gelten
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(KERN))

import pruefliste  # noqa: E402
import rueckweg  # noqa: E402
import warenausgang  # noqa: E402

try:
    import melden as meldung
except ImportError:
    meldung = None

AGENT = "qualitaetsmanager"
#: Unter dieser Kennung meldet er - eine Modul-Kennung aus Modul.kt.
MODUL = "system.qm"

#: So oft darf er zurueckschicken, bevor ein Stueck liegen bleibt.
#: So entschieden: hoechstens zweimal je Einstellung.
HOECHSTENS_ZURUECK = 2


class Urteil:
    VORLEGEN = "vorlegen"          # bestanden, geht in den Warenausgang
    ZURUECK = "zurueck"            # Maengel, aber noch ein Versuch erlaubt
    LIEGEN_LASSEN = "liegen_lassen"  # zu oft durchgefallen


def pruefen(was: str, datei: str | Path | None, modul: str,
            zettel: dict | None = None, soll: dict | None = None,
            konfiguration: dict | None = None) -> pruefliste.Befund:
    """Messen, Zettel prüfen, gegen die Lehrsaetze halten. Kostet nichts."""
    befund = pruefliste.hart_pruefen(was, datei, soll)
    if zettel:
        befund.maengel.extend(pruefliste.zettel_pruefen(zettel))
    saetze = rueckweg.lehrsaetze(modul, "aktiv", konfiguration)
    pruefliste.aus_lehrsaetzen(saetze, befund)
    return befund


def abnehmen(was: str, datei: str | Path | None, auftrag: str, modul: str,
             titel: str, durchlaeufe: int = 1, zettel: dict | None = None,
             soll: dict | None = None, kosten: float = 0.0,
             art: str = "echt",
             konfiguration: dict | None = None) -> dict:
    """Pruefen und entscheiden, was mit dem Stueck geschieht.

    Bestanden heisst nicht 'gut', sondern 'ohne messbaren Mangel und im
    Rahmen dessen, was bisher gelernt wurde'. Ueber gut entscheidest du.
    """
    voll = dict(zettel or {})
    voll.setdefault("was", was)
    voll.setdefault("auftrag", auftrag)
    voll.setdefault("modul", modul)
    voll.setdefault("titel", titel)
    voll.setdefault("abgenommen_von", AGENT)

    befund = pruefen(was, datei, modul, voll, soll, konfiguration)

    # Worauf das Stueck stand. Der Stoffbeschaffer hat es gemessen und in den
    # Auftrag geschrieben; von dort kommt es ueber den Beipackzettel hierher.
    # Es wird nicht bewertet - es wird sichtbar gemacht: ein Stueck, das auf
    # nichts stand, sieht sonst genauso aus wie eines, das auf zwanzig Funden
    # steht, und beim Lernen laesst sich beides nicht mehr auseinanderhalten.
    deckung = str(voll.get("deckung", "")).strip()
    deckung_satz = str(voll.get("deckung_satz", "")).strip()
    vermerk = _deckungsvermerk(deckung, deckung_satz)

    if befund.bestanden:
        eintrag = warenausgang.einstellen(
            was=was, auftrag=auftrag, modul=modul, titel=titel,
            datei=str(datei or ""), gueteklasse=voll.get("gueteklasse", ""),
            laenge=_laenge(befund), format_=_format(befund),
            stimme=voll.get("stimme", ""), bildquellen=voll.get("bildquellen", ""),
            kosten=kosten, abgenommen_von=AGENT,
            taugt_fuer=voll.get("taugt_fuer", ""),
            notiz=befund.als_text() + vermerk, konfiguration=konfiguration)
        _melde("info", "%s abgenommen: %s" % (was, titel),
               befund.als_text(), auftrag, {"warenausgang": eintrag["kennung"]})
        _nachpruefen(modul, auftrag)
        return {"urteil": Urteil.VORLEGEN, "befund": befund,
                "warenausgang": eintrag["kennung"], "durchlaeufe": durchlaeufe}

    if durchlaeufe <= HOECHSTENS_ZURUECK:
        _melde("fortschritt",
               "%s zurueckgegeben (%d. Durchlauf)" % (was, durchlaeufe),
               befund.als_text(), auftrag)
        return {"urteil": Urteil.ZURUECK, "befund": befund,
                "durchlaeufe": durchlaeufe}

    grund = "; ".join(befund.maengel)
    rueckweg.verwerfen("auftrag", auftrag,
                       "Dreimal durchgefallen: " + grund,
                       herkunft=modul,
                       wiederaufnahme="Wenn die Maengel oben behoben sind",
                       konfiguration=konfiguration)
    rueckweg.erfahrung_ablegen(
        auftrag=auftrag, modul=modul,
        was_versucht=titel, befund=befund.als_text(),
        urteil="nein", grund=grund,
        gueteklasse=voll.get("gueteklasse", ""),
        durchlaeufe=durchlaeufe, kosten=kosten, art=art,
        deckung=deckung, deckung_satz=deckung_satz,
        konfiguration=konfiguration)
    _melde("fehler", "%s bleibt liegen: %s" % (was, titel),
           "Dreimal durchgefallen. Auf der Halde vermerkt.\n\n" + befund.als_text(),
           auftrag)
    return {"urteil": Urteil.LIEGEN_LASSEN, "befund": befund,
            "durchlaeufe": durchlaeufe}


def _nachpruefen(modul: str, auftrag: str) -> None:
    """Nach der Abnahme die Pruefstrasse ueber dieses Modul laufen lassen.

    Die Abnahme sagt, ob das Stueck taugt. Die Nachpruefung sagt, ob die
    Strasse noch haelt, was ihre Kette verspricht - zwei verschiedene Fragen.
    Bricht sie ab, ist das kein Grund, die Abnahme zu verwerfen: das Stueck
    ist geprueft, die Strasse ist es dann eben nicht.
    """
    try:
        import pruefstrasse
        if pruefstrasse.laeuft_gerade():
            return            # wir stecken selbst in einem Pruefstandlauf
        pruefstrasse.nach_dem_lauf(modul, auftrag)
    except Exception:
        pass


def _deckungsvermerk(deckung: str, satz: str) -> str:
    """Ein Satz fuer den Beipackzettel - kein Urteil, ein Vermerk.

    Ein duenn oder gar nicht gedecktes Stueck wird nicht angehalten: es kann
    genau richtig sein. Aber es steht dann dabei, damit niemand es fuer
    belegt haelt, was nirgends belegt ist.
    """
    if not deckung:
        return ""
    zeile = satz or {"gut": "Das Thema war im 2nd Brain gut gedeckt.",
                     "duenn": "Zum Thema lag wenig im 2nd Brain.",
                     "leer": "Zum Thema lag nichts im 2nd Brain."}.get(
                         deckung, "Deckung: " + deckung)
    if deckung in ("duenn", "leer"):
        zeile += (" Was hier steht, ist nicht durch eigenes Wissen belegt - "
                  "vor der Veroeffentlichung nachsehen.")
    return "\n\nWorauf das Stueck stand: " + zeile


def _laenge(befund) -> str:
    s = befund.gemessen.get("sekunden")
    return ("%.0f s" % s) if s else "-"


def _format(befund) -> str:
    b, h = befund.gemessen.get("breite"), befund.gemessen.get("hoehe")
    return ("%dx%d" % (b, h)) if b and h else "-"


def _melde(art: str, kurz: str, text: str, vorgang: str = "",
           daten: dict | None = None) -> None:
    if meldung is not None:
        meldung.melde(absender=MODUL, art=art, zusammenfassung=kurz,
                      text=text, vorgang=vorgang or None, daten=daten or {})


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    if not argumente:
        print(__doc__)
        return 2

    if argumente[0] == "grenzen":
        for was, werte in pruefliste.GRENZEN.items():
            print("%s:" % was)
            for k, v in werte.items():
                print("    %-22s %s" % (k, v))
        print("\nPflichtfelder im Beipackzettel: %s"
              % ", ".join(pruefliste.PFLICHTFELDER))
        print("Hoechstens %d Rueckgaben, danach bleibt ein Stueck liegen."
              % HOECHSTENS_ZURUECK)
        return 0

    if argumente[0] == "liste":
        for z in warenausgang.bestand():
            if z.get("abgenommen_von") == AGENT:
                print("%s  %-10s %-18s %s" % (z["kennung"], z.get("was"),
                                              z.get("stand"), z.get("titel")))
        return 0

    p = argparse.ArgumentParser(prog="qualitaetsmanager")
    p.add_argument("befehl", choices=["pruefen", "abnehmen"])
    p.add_argument("was", choices=list(pruefliste.GRENZEN))
    p.add_argument("datei")
    p.add_argument("--auftrag", required=True)
    p.add_argument("--modul", required=True)
    p.add_argument("--titel", default="")
    p.add_argument("--durchlauf", type=int, default=1)
    p.add_argument("--kosten", type=float, default=0.0)
    p.add_argument("--gueteklasse", default="")
    p.add_argument("--bildquellen", default="")
    p.add_argument("--stimme", default="")
    p.add_argument("--taugt-fuer", dest="taugt_fuer", default="")
    a = p.parse_args(argumente)

    zettel = {"gueteklasse": a.gueteklasse, "bildquellen": a.bildquellen,
              "stimme": a.stimme, "taugt_fuer": a.taugt_fuer}
    titel = a.titel or Path(a.datei).stem

    if a.befehl == "pruefen":
        befund = pruefen(a.was, a.datei, a.modul,
                         dict(zettel, was=a.was, auftrag=a.auftrag,
                              modul=a.modul, titel=titel,
                              abgenommen_von=AGENT))
        print(befund.als_text())
        return 0 if befund.bestanden else 1

    ergebnis = abnehmen(a.was, a.datei, a.auftrag, a.modul, titel,
                        a.durchlauf, zettel, kosten=a.kosten)
    print(ergebnis["befund"].als_text())
    print()
    if ergebnis["urteil"] == Urteil.VORLEGEN:
        print("Abgenommen. Liegt als %s im Warenausgang und wartet auf deine "
              "Freigabe." % ergebnis["warenausgang"])
        return 0
    if ergebnis["urteil"] == Urteil.ZURUECK:
        print("Zurueck in die Strasse (%d. von %d Durchlaeufen)."
              % (ergebnis["durchlaeufe"], HOECHSTENS_ZURUECK))
        return 1
    print("Bleibt liegen - dreimal durchgefallen. Steht auf der Halde.")
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
