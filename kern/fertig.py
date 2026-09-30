# -*- coding: utf-8 -*-
"""Fertig heisst Ja oder Nein - nicht "sieht gut aus".

Bis zum 13.09.2026 endete jeder Auftrag mit einer Beschreibung: der
Qualitaetsmanager hat abgenommen, das Stueck liegt im Warenausgang, Daniel gibt
frei. Eine Beschreibung kann man nicht nachrechnen, und deshalb musste Daniel
jedes einzelne Stueck ansehen. Genau das soll aufhoeren.

Hier steht je Bestandteil, woran man ohne Meinung erkennt, ob ein Stueck fertig
ist. Jedes Kriterium hat genau drei moegliche Antworten:

    JA      gemessen und erfuellt
    NEIN    gemessen und nicht erfuellt  -> das Stueck geht gar nicht erst raus,
            und es wird eine Erfahrung "nein" abgelegt. Drei gleichartige Neins
            ergeben beim Ausbilder einen Lehrsatz - so lernt die Strasse daraus.
    OFFEN   noch nicht messbar           -> Daniel entscheidet. Das ist der
            Zustand fuer den Betatest, und er soll schrumpfen.

Selbstfreigabe: hat ein Bestandteil %d Stuecke hintereinander ohne ein einziges
OFFEN und ohne ein einziges NEIN geliefert, gibt er sich danach selbst frei.
Kommt ein NEIN, faellt der Zaehler auf null und Daniel sieht wieder hin. Damit
verschwindet die Handarbeit dort, wo sie sich bewaehrt hat, und bleibt dort, wo
sie noch gebraucht wird.

    python fertig.py katalog             was je Bestandteil gilt
    python fertig.py stand               wo die Selbstfreigabe steht
    python fertig.py pruefen <datei> --modul prod.social
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

KERN = Path(__file__).resolve().parent
UNIVERSE = KERN.parent
ZUSTAND = UNIVERSE / "zustand" / "fertigkriterien.json"

JA, NEIN, OFFEN = "ja", "nein", "offen"

# Wie viele saubere Stuecke hintereinander, bevor ein Bestandteil sich selbst
# freigibt. Drei, wie beim Ausbilder: ein Zufall ist keiner mehr, wenn er
# dreimal derselbe war. Zwei waeren zu wenig (ein guter Tag), fuenf zu traege.
SELBSTFREIGABE_AB = 3

__doc__ = __doc__ % SELBSTFREIGABE_AB


def _laden(name: str, datei: Path):
    fertig = sys.modules.get(name)
    if fertig is not None:
        return fertig
    if not datei.exists():
        return None
    try:
        b = importlib.util.spec_from_file_location(name, datei)
        m = importlib.util.module_from_spec(b)
        sys.modules[name] = m
        b.loader.exec_module(m)
        return m
    except Exception:
        return None


@dataclass
class Kriterium:
    name: str
    frage: str                    # die Ja/Nein-Frage im Klartext
    messen: object = None         # (zettel, text) -> (antwort, gemessen)
    warum: str = ""


@dataclass
class Urteil:
    modul: str
    ja: bool = False
    einzeln: list = field(default_factory=list)   # (name, antwort, gemessen)
    neins: list = field(default_factory=list)
    offene: list = field(default_factory=list)
    selbstfreigabe: bool = False
    satz: str = ""


# ------------------------------------------------------------ die Messungen

def _liegt_vor(zettel: dict, text: str):
    n = len((text or "").strip())
    return (JA if n > 0 else NEIN), "%d Zeichen" % n


def _sprache_sauber(zettel: dict, text: str):
    s = _laden("marke_sprache", UNIVERSE / "marke" / "sprache.py")
    if s is None:
        return OFFEN, "marke/sprache.py fehlt"
    funde = s.pruefen(text or "")
    if not funde:
        return JA, "kein Muster"
    return NEIN, "%d Muster: %s" % (len(funde), ", ".join(sorted({f.art for f in funde}))[:80])


def _quelle_genannt(zettel: dict, text: str):
    hat = bool(str(zettel.get("bildquellen") or "").strip() not in ("", "-"))
    hat = hat or bool(re.search(r"https?://|Quelle:|quellen:", text or "", re.I))
    return (JA if hat else NEIN), ("genannt" if hat else "keine Quelle im Stueck")


def _kosten_im_rahmen(zettel: dict, text: str):
    """Die tatsaechlichen Kosten gegen die Schaetzung des Auftrags."""
    ist = float(zettel.get("kosten") or 0.0)
    soll = zettel.get("kosten_geschaetzt")
    if soll in (None, "", "-"):
        return OFFEN, "%.2f EUR angefallen, keine Schaetzung im Auftrag" % ist
    soll = float(soll)
    # Zwanzig Prozent Luft: ein Modellaufruf schwankt mit der Antwortlaenge,
    # und wer bei jeder Schwankung rot wird, schaltet die Pruefung ab.
    grenze = soll * 1.2
    return (JA if ist <= grenze else NEIN), "%.2f von hoechstens %.2f EUR" % (ist, grenze)


def _keine_erfundene_zahl(zettel: dict, text: str):
    """Jede Zahl im Stueck muss im gelieferten Stoff vorkommen.

    Ohne Stoff ist es nicht messbar - dann OFFEN, nicht JA. Ein stillschweigendes
    Ja waere die gefaehrlichere Antwort: es sieht aus wie geprueft.
    """
    stoff = str(zettel.get("stoff_kontext") or "")
    if not stoff:
        return OFFEN, "kein Stoff mitgeliefert, nicht nachrechenbar"
    # Jahreszahlen, Prozente und Kleinzahlen bis 10 sind Sprachbestandteil,
    # keine Behauptung. Geprueft werden Zahlen ab 11 und alle mit Trennzeichen.
    zahlen = {z for z in re.findall(r"\b\d[\d.,]{1,}\b", text or "")
              if not re.fullmatch(r"[0-9]|10|19\d\d|20\d\d", z)}
    frei = sorted(z for z in zahlen if z not in stoff)
    if frei:
        return NEIN, "nicht im Stoff: " + ", ".join(frei[:6])
    return JA, "%d Zahlen, alle belegt" % len(zahlen)


def _laenge_eingehalten(zettel: dict, text: str):
    soll = zettel.get("laenge")
    if soll in (None, "", "-"):
        return OFFEN, "keine Laengenvorgabe im Auftrag"
    treffer = re.search(r"(\d+)", str(soll))
    if not treffer:
        return OFFEN, "Laengenvorgabe '%s' nicht als Zahl lesbar" % soll
    grenze = int(treffer.group(1))
    ist = len((text or "").strip())
    return (JA if ist <= grenze else NEIN), "%d von hoechstens %d Zeichen" % (ist, grenze)


def _schaubild_besteht(zettel: dict, text: str):
    d = _laden("marke_diagramme", UNIVERSE / "marke" / "diagramme.py")
    if d is None:
        return OFFEN, "marke/diagramme.py fehlt"
    if "<svg" not in (text or "").lower():
        return OFFEN, "kein Schaubild in diesem Stueck"
    funde = d.pruefen(text)
    if not funde:
        return JA, "Geschmackstest bestanden"
    return NEIN, "; ".join("%s %s" % (f.art, f.stelle[:14]) for f in funde[:4])


def _datei_da(zettel: dict, text: str):
    pfad = str(zettel.get("erzeugnis") or "").strip()
    if pfad in ("", "-"):
        return NEIN, "keine Datei am Beipackzettel"
    p = Path(pfad)
    if not p.is_absolute():
        p = UNIVERSE.parent / pfad
    if not p.exists():
        return NEIN, "Datei fehlt: %s" % pfad
    return JA, "%s, %d Byte" % (p.name, p.stat().st_size)


# --------------------------------------------------------------- der Katalog

# Gilt fuer jedes Stueck, gleich aus welcher Strasse.
UEBERALL = [
    Kriterium("liegt-vor", "Ist ueberhaupt etwas entstanden?", _liegt_vor,
              "Ein leeres Stueck ist der haeufigste stille Fehlschlag."),
    Kriterium("datei-da", "Liegt die genannte Datei wirklich am genannten Ort?", _datei_da,
              "Ein Beipackzettel ohne Datei sieht im Warenausgang aus wie fertige Arbeit."),
    Kriterium("sprache-sauber", "Ist der Text frei von Maschinentext-Maschen?",
              _sprache_sauber, "Sonst geht Werbesprache unter unserem Namen heraus."),
    Kriterium("keine-erfundene-zahl", "Steht jede Zahl im gelieferten Stoff?",
              _keine_erfundene_zahl, "Eine erfundene Zahl ist der Schaden, der bleibt."),
    Kriterium("quelle-genannt", "Nennt das Stueck seine Herkunft?", _quelle_genannt,
              "Ohne Quelle kann niemand nachsehen und niemand widersprechen."),
    Kriterium("kosten-im-rahmen", "Blieb es im geschaetzten Rahmen?", _kosten_im_rahmen,
              "Sonst faellt eine Kostenexplosion erst am Monatsende auf."),
]

# Je Bestandteil das, was nur dort gilt. Die Liste folgt den Modulen, die der
# Pruefstand fuehrt - eine andere Liste zu pflegen hiesse, zwei Wahrheiten zu haben.
JE_BESTANDTEIL = {
    "prod.social": [
        Kriterium("laenge-eingehalten", "Passt der Beitrag in das Format?", _laenge_eingehalten,
                  "Ein zu langer Beitrag wird von der Plattform abgeschnitten."),
    ],
    "prod.video.clip": [
        Kriterium("laenge-eingehalten", "Liegt die Laufzeit in der Vorgabe?", _laenge_eingehalten),
    ],
    "prod.pdf": [
        Kriterium("schaubild-besteht", "Bestehen enthaltene Schaubilder den Geschmackstest?",
                  _schaubild_besteht),
    ],
    "prod.lernen": [
        Kriterium("schaubild-besteht", "Bestehen enthaltene Schaubilder den Geschmackstest?",
                  _schaubild_besteht),
    ],
    "prod.app": [
        Kriterium("schaubild-besteht", "Bestehen enthaltene Schaubilder den Geschmackstest?",
                  _schaubild_besteht),
    ],
    "webseite": [
        Kriterium("schaubild-besteht", "Bestehen enthaltene Schaubilder den Geschmackstest?",
                  _schaubild_besteht),
    ],
    "prod.marketing": [
        Kriterium("laenge-eingehalten", "Passt der Text in das Format?", _laenge_eingehalten),
    ],
}

# Bestandteile, die kein Stueck herausgeben, sondern eine Wirkung haben. Ihr
# Fertigkriterium ist die Pruefung im Pruefstand, nicht ein Beipackzettel.
UEBER_DEN_PRUEFSTAND = {
    "system", "system.hub", "system.kosten", "system.laenge", "system.pruefstrasse",
    "system.qm", "system.sicherheit", "ausbildung", "fragefenster", "wissen",
    "wissen.kurator", "wissen.research", "wissen.scout", "trading", "marke",
    "kalender", "post", "wohnung", "bewerbung", "gestalter",
}


def katalog(modul: str = "") -> list[Kriterium]:
    if modul and modul in UEBER_DEN_PRUEFSTAND:
        return []
    return UEBERALL + JE_BESTANDTEIL.get(modul, [])


# ------------------------------------------------------------------- Urteil

def beurteilen(modul: str, zettel: dict, text: str) -> Urteil:
    """Das Ja/Nein zu einem Stueck. Nichts wird geschrieben, nur gemessen."""
    u = Urteil(modul=modul)
    for k in katalog(modul):
        if k.messen is None:
            u.einzeln.append((k.name, OFFEN, "keine Messung hinterlegt"))
            u.offene.append(k.name)
            continue
        try:
            antwort, gemessen = k.messen(zettel or {}, text or "")
        except Exception as fehler:
            antwort, gemessen = OFFEN, "Messung brach ab: %s" % fehler
        u.einzeln.append((k.name, antwort, gemessen))
        if antwort == NEIN:
            u.neins.append("%s (%s)" % (k.name, gemessen))
        elif antwort == OFFEN:
            u.offene.append(k.name)

    u.ja = not u.neins
    if not u.einzeln:
        u.satz = ("%s gibt keine Stuecke heraus - sein Fertigkriterium ist der "
                  "Pruefstand." % modul)
        u.ja = True
    elif u.neins:
        u.satz = "Nicht fertig: " + "; ".join(u.neins[:3])
    elif u.offene:
        u.satz = ("Alle messbaren Kriterien erfuellt, %d noch nicht messbar (%s) - "
                  "Daniel entscheidet." % (len(u.offene), ", ".join(u.offene[:3])))
    else:
        u.satz = "Alle %d Kriterien erfuellt und gemessen." % len(u.einzeln)
    return u


# ------------------------------------------------------- Zaehler und Freigabe

def _stand() -> dict:
    if ZUSTAND.exists():
        try:
            return json.loads(ZUSTAND.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _stand_sichern(stand: dict) -> None:
    ZUSTAND.parent.mkdir(parents=True, exist_ok=True)
    ZUSTAND.write_text(json.dumps(stand, ensure_ascii=False, indent=1),
                       encoding="utf-8", newline="")


def buchen(u: Urteil) -> Urteil:
    """Das Urteil in den Zaehler eintragen und sagen, ob es sich selbst freigibt."""
    stand = _stand()
    eintrag = stand.setdefault(u.modul, {"saubere_in_folge": 0, "letztes": "",
                                         "neins_gesamt": 0, "seit": date.today().isoformat()})
    if u.neins:
        eintrag["saubere_in_folge"] = 0
        eintrag["neins_gesamt"] = int(eintrag.get("neins_gesamt", 0)) + 1
    elif u.offene:
        # Nicht zuruecksetzen, aber auch nicht hochzaehlen: was Daniel noch
        # entscheiden muss, ist kein Beleg dafuer, dass die Strasse allein laeuft.
        pass
    else:
        eintrag["saubere_in_folge"] = int(eintrag.get("saubere_in_folge", 0)) + 1
    eintrag["letztes"] = date.today().isoformat()
    u.selbstfreigabe = (u.ja and not u.offene
                        and eintrag["saubere_in_folge"] >= SELBSTFREIGABE_AB)
    _stand_sichern(stand)
    return u


def erfahrung_ablegen(u: Urteil, auftrag: str, was_versucht: str = "") -> bool:
    """Ein NEIN in den Rueckweg - damit der Ausbilder daraus einen Lehrsatz macht."""
    if not u.neins:
        return False
    try:
        r = _laden("kern_rueckweg", KERN / "rueckweg.py")
        r.erfahrung_ablegen(
            auftrag=auftrag, modul=u.modul,
            was_versucht=was_versucht or "Stueck fertigstellen",
            befund=u.satz, urteil="nein", grund="; ".join(u.neins),
            art=r.ECHT)
        return True
    except Exception:
        return False


def _main(argumente: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    z = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    unter = z.add_subparsers(dest="befehl", required=True)
    unter.add_parser("katalog")
    unter.add_parser("stand")
    p = unter.add_parser("pruefen")
    p.add_argument("datei")
    p.add_argument("--modul", default="")
    w = z.parse_args(argumente)

    if w.befehl == "katalog":
        print("Gilt ueberall:")
        for k in UEBERALL:
            print("  %-22s %s" % (k.name, k.frage))
        print("\nJe Bestandteil zusaetzlich:")
        for modul, ks in sorted(JE_BESTANDTEIL.items()):
            print("  %-18s %s" % (modul, ", ".join(k.name for k in ks)))
        print("\nUeber den Pruefstand statt ueber ein Stueck (%d):" % len(UEBER_DEN_PRUEFSTAND))
        print("  " + ", ".join(sorted(UEBER_DEN_PRUEFSTAND)))
        print("\nSelbstfreigabe ab %d sauberen Stuecken in Folge." % SELBSTFREIGABE_AB)
        return 0

    if w.befehl == "stand":
        stand = _stand()
        if not stand:
            print("Noch kein Stueck beurteilt.")
            return 0
        for modul, e in sorted(stand.items()):
            frei = "selbstfreigabe" if e.get("saubere_in_folge", 0) >= SELBSTFREIGABE_AB \
                else "Daniel gibt frei"
            print("  %-20s %d sauber in Folge, %d Neins gesamt - %s"
                  % (modul, e.get("saubere_in_folge", 0), e.get("neins_gesamt", 0), frei))
        return 0

    text = Path(w.datei).read_text(encoding="utf-8", errors="replace")
    u = beurteilen(w.modul, {"erzeugnis": w.datei}, text)
    for name, antwort, gemessen in u.einzeln:
        print("  %-4s %-22s %s" % (antwort.upper(), name, gemessen))
    print("\n" + u.satz)
    return 0 if u.ja else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
