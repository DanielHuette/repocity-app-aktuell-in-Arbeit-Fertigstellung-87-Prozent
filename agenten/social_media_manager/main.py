"""Social-Media-Manager - Kommandozeile.

Er holt aus dem Warenausgang, was du freigegeben hast, baut daraus fertige
Beitraege und legt sie ab. Spaeter meldet er zurueck, wie sie draussen
gelaufen sind - das ist der Teil, der die Agenten lernen laesst.

  python main.py offen                was abholbar ist
  python main.py holen                alles Freigegebene abholen und bauen
  python main.py holen W0003          nur dieses Stueck
  python main.py plan                 was gebaut ist und noch nicht draussen
  python main.py raus W0003 tiktok    als veroeffentlicht vermerken
  python main.py rueckmeldung W0003 "1400 Aufrufe, 22 Kommentare"
  python main.py stand

Was er NICHT tut: hochladen. Solange keine Zugaenge stehen, laedst du
selbst hoch - er legt dir Datei, Text und Abspann fertig nebeneinander.
Das ist Absicht: ein Agent, der ohne Zugang so tut, als haette er
veroeffentlicht, ist schlimmer als einer, der es ehrlich liegen laesst.

Ohne deine Freigabe holt er nichts. Das ist die Stelle, an der aus deinem
Ja eine Wirkung wird.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
for pfad in (str(HIER), str(KERN)):
    if pfad not in sys.path:
        sys.path.append(pfad)
sys.path.insert(0, str(HIER))

import beitrag as beitrag_bauen  # noqa: E402
import rueckweg  # noqa: E402
import warenausgang  # noqa: E402

try:
    import melden as meldung
except ImportError:
    meldung = None

AGENT = "social_media_manager"
MODUL = "prod.social"


def _ausgang(konfiguration: dict | None = None) -> Path:
    """Wo die fertigen Beitraege liegen - im Vault, damit du sie siehst."""
    return rueckweg._ordner("social", konfiguration)


def _plandatei(konfiguration: dict | None = None) -> Path:
    return _ausgang(konfiguration) / "_plan.json"


def _plan(konfiguration: dict | None = None) -> dict:
    datei = _plandatei(konfiguration)
    if datei.exists():
        try:
            return json.loads(datei.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def _plan_sichern(plan: dict, konfiguration: dict | None = None) -> None:
    _plandatei(konfiguration).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8", newline="")


# ------------------------------------------------------------------ holen

def holen(kennung: str | None = None,
          konfiguration: dict | None = None) -> list[dict]:
    """Freigegebene Stuecke abholen und Beitraege daraus bauen.

    Nichts davon veroeffentlicht etwas. Was hier entsteht, liegt danach
    fertig im Vault und wartet darauf, dass du es hochlaedst.
    """
    offen = warenausgang.abholbar(AGENT, was="video", konfiguration=konfiguration)
    if kennung:
        offen = [z for z in offen if z.get("kennung") == kennung]
    gebaut = []
    plan = _plan(konfiguration)

    for zettel in offen:
        plattformen = beitrag_bauen.plattformen_fuer(zettel)
        if not plattformen:
            print("  %s: 'taugt_fuer' nennt keine Plattform, die ich kenne (%s)"
                  % (zettel["kennung"], zettel.get("taugt_fuer")))
            continue

        ordner = _ausgang(konfiguration) / zettel["kennung"]
        ordner.mkdir(parents=True, exist_ok=True)
        eintraege = []
        for plattform in plattformen:
            b = beitrag_bauen.bauen(zettel, plattform)
            (ordner / ("%s.txt" % plattform)).write_text(
                _als_blatt(b), encoding="utf-8", newline="")
            eintraege.append({"plattform": plattform,
                              "veroeffentlichbar": b.veroeffentlichbar,
                              "warnungen": b.warnungen,
                              "draussen_seit": "",
                              "rueckmeldung": ""})
            zeichen = "+" if b.veroeffentlichbar else "!"
            print("  %s %s / %-9s %s" % (zeichen, zettel["kennung"], plattform,
                                         "; ".join(b.warnungen) or "fertig"))

        # Die Datei danebenlegen, damit alles an einem Ort ist.
        quelle = Path(zettel.get("erzeugnis", ""))
        if quelle.exists():
            try:
                shutil.copy2(quelle, ordner / quelle.name)
            except OSError:
                pass

        warenausgang.abholen(zettel["kennung"], AGENT, konfiguration=konfiguration)
        plan[zettel["kennung"]] = {
            "titel": zettel.get("titel", ""),
            "auftrag": zettel.get("auftrag", ""),
            "geholt_am": date.today().isoformat(),
            "ordner": str(ordner),
            "beitraege": eintraege,
        }
        gebaut.append(zettel)

    if gebaut:
        _plan_sichern(plan, konfiguration)
        _melde("info", "%d Beitraege gebaut" % len(gebaut),
               "Sie liegen fertig im Vault unter social/ und warten darauf, "
               "dass du sie hochlaedst.")
    return gebaut


def _als_blatt(b) -> str:
    """Ein Blatt je Plattform: alles, was zum Hochladen noetig ist."""
    zeilen = ["# %s" % b.plattform.upper(), "",
              "## Datei", b.datei or "-", "",
              "## Text", b.als_text(), ""]
    if b.erster_kommentar:
        zeilen += ["## Erster Kommentar", b.erster_kommentar, ""]
    if b.warnungen:
        zeilen += ["## Das steht noch im Weg"]
        zeilen += ["- " + w for w in b.warnungen]
        zeilen += [""]
    return "\n".join(zeilen)


# ------------------------------------------------------------------ raus

def veroeffentlicht(kennung: str, plattform: str,
                    konfiguration: dict | None = None) -> bool:
    """Vermerken, dass ein Beitrag draussen ist. Von dir, nicht von ihm."""
    plan = _plan(konfiguration)
    eintrag = plan.get(kennung)
    if not eintrag:
        return False
    for b in eintrag["beitraege"]:
        if b["plattform"] == plattform:
            b["draussen_seit"] = date.today().isoformat()
            _plan_sichern(plan, konfiguration)
            return True
    return False


# ------------------------------------------------------------------ zurueck

def rueckmeldung(kennung: str, text: str,
                 konfiguration: dict | None = None) -> bool:
    """Wie das Stueck draussen gelaufen ist - zurueck an den Auftrag.

    Das ist die dritte Rueckmeldung im Kreis: der Qualitaetsmanager sagt,
    ob es sauber war, du sagst, ob es taugt, und hier steht, was die Welt
    davon gehalten hat. Ohne sie lernt der Agent nur, was dir gefaellt,
    nicht was ankommt.
    """
    plan = _plan(konfiguration)
    eintrag = plan.get(kennung)
    if not eintrag:
        print("unbekannt: " + kennung)
        return False
    for b in eintrag["beitraege"]:
        if b.get("draussen_seit"):
            b["rueckmeldung"] = text
    _plan_sichern(plan, konfiguration)

    datei = rueckweg.aussenwirkung_nachtragen(eintrag["auftrag"], text,
                                              konfiguration=konfiguration)
    if datei is None:
        print("Zu diesem Auftrag gibt es keine Erfahrung - nichts nachgetragen.")
        return False
    print("Nachgetragen in %s" % datei.name)
    _melde("info", "Aussenwirkung zu %s" % kennung, text)
    return True


def _melde(art: str, kurz: str, text: str) -> None:
    if meldung is not None:
        meldung.melde(absender=MODUL, art=art, zusammenfassung=kurz, text=text)


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    rest = argumente[1:]

    if befehl == "offen":
        liste = warenausgang.abholbar(AGENT, was="video")
        if not liste:
            print("Nichts abholbar. Entweder ist nichts fertig, oder es ist")
            print("noch nicht von dir freigegeben.")
        for z in liste:
            print("%s  %-46s %s" % (z["kennung"], (z.get("titel") or "")[:46],
                                    z.get("taugt_fuer")))
        return 0

    if befehl == "holen":
        gebaut = holen(rest[0] if rest else None)
        print("\n%d Stueck geholt." % len(gebaut))
        return 0

    if befehl == "plan":
        plan = _plan()
        if not plan:
            print("Noch nichts geholt.")
        for kennung, e in plan.items():
            print("%s  %s" % (kennung, e.get("titel", "")))
            for b in e["beitraege"]:
                stand = b.get("draussen_seit") or (
                    "bereit" if b["veroeffentlichbar"] else "blockiert")
                print("      %-9s %-12s %s" % (b["plattform"], stand,
                                               b.get("rueckmeldung") or
                                               "; ".join(b.get("warnungen") or [])))
            print("      Ordner: %s" % e.get("ordner"))
        return 0

    if befehl == "raus" and len(rest) > 1:
        print("vermerkt" if veroeffentlicht(rest[0], rest[1]) else "nicht gefunden")
        return 0

    if befehl == "rueckmeldung" and len(rest) > 1:
        return 0 if rueckmeldung(rest[0], " ".join(rest[1:])) else 1

    if befehl == "stand":
        plan = _plan()
        blaetter = sum(len(e["beitraege"]) for e in plan.values())
        draussen = sum(1 for e in plan.values() for b in e["beitraege"]
                       if b.get("draussen_seit"))
        mit_echo = sum(1 for e in plan.values() for b in e["beitraege"]
                       if b.get("rueckmeldung"))
        print("%-26s %d" % ("abholbar", len(warenausgang.abholbar(AGENT, was="video"))))
        print("%-26s %d" % ("geholte Stuecke", len(plan)))
        print("%-26s %d" % ("gebaute Beitraege", blaetter))
        print("%-26s %d" % ("davon draussen", draussen))
        print("%-26s %d" % ("davon mit Rueckmeldung", mit_echo))
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
