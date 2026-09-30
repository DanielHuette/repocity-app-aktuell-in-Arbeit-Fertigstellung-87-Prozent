"""Das Verbrauchsbuch - eine Stelle, durch die jede bezahlte Handlung geht.

Vorher buchte nur die Bilderzeugung, und zwar in ihr eigenes Heft.
Einbettungen, Modellaufrufe, Sprachausgabe: nichts davon wurde
verzeichnet. Ein Controller kann nur zaehlen, was gebucht wird - darum
diese Stelle.

Gebucht wird auf eine KOSTENSTELLE. Eine Kostenstelle ist eine
Modul-Kennung aus Modul.kt: prod.video.clip, wissen.scout, system.qm. Jede
Kostenstelle gehoert zu einem Topf; der Topf sammelt, er begrenzt nicht.

Zwei Sorten Buchung:

  GELD          was wirklich Geld kostet, in Euro
  KONTINGENT    was ein freies Kontingent verbraucht - Pexels-Abrufe,
                GitHub-Anfragen. Kostet nichts und kann trotzdem die
                Strasse anhalten, wenn es aufgebraucht ist.

RepoCity setzt dem Nutzer KEINE Grenze. Was er ausgibt, entscheidet er.
Die Grenze setzt er sich selbst, je Produktionsstrasse und je Kette - sie
steht in universe/kostenbremse.json und wird von kern/bremse.py gelesen.
Hat er keine gesetzt, laeuft alles. Hat er eine gesetzt: Warnung bei 80 %,
Stopp am Wert, ein angefangener Lauf wird fertig, beim Doppelten der
Lauf-Marke bricht auch der ab. Von Daniel am 07.09. so entschieden.

Nicht zu verwechseln mit der PRUEFSTANDGRENZE in kosten.json: die ist
keine Nutzersache, sondern der Schutz des Werkzeugs vor sich selbst -
damit ein Testlauf nicht durchdreht.

Aufruf von Hand:
    python verbrauch.py stand
    python verbrauch.py buch 30        die letzten 30 Tage
    python verbrauch.py zusammen       dieser Monat nach Kategorie, mit Betriebskosten
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KOSTENDATEI = UNIVERSE / "kosten.json"
BUCH = UNIVERSE / "zustand" / "verbrauch.jsonl"

sys.path.insert(0, str(HIER))
import bremse  # noqa: E402

GELD = "geld"
KONTINGENT = "kontingent"

#: Woher eine Buchung stammt. Nur ECHT zaehlt in den Bericht.
#: Ein Pruefstandlauf hat schon einmal 4,00 EUR gebucht, die nie geflossen
#: sind - dieselbe Trennung wie bei den Erfahrungen, aus demselben Grund.
ECHT = "echt"
PRUEFUNG = "pruefung"


class Gesperrt(RuntimeError):
    """Die Marke des Nutzers haelt hier an."""


# ------------------------------------------------------------------ Stammdaten

_zwischenspeicher: dict = {}


def stammdaten(neu_lesen: bool = False) -> dict:
    if neu_lesen or not _zwischenspeicher:
        _zwischenspeicher.clear()
        try:
            _zwischenspeicher.update(json.loads(
                KOSTENDATEI.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            _zwischenspeicher.update({"toepfe": {}, "preise": {},
                                      "kontingente": {}, "usd_zu_eur": 0.92})
    return _zwischenspeicher


def eur(usd: float) -> float:
    return round(usd * float(stammdaten().get("usd_zu_eur", 0.92)), 6)


def preis_usd(modell: str, stueck: int = 1) -> float:
    """Was ein Stueck dieses Modells kostet, in USD - die Zahl aus kosten.json.

    Es gibt sie, damit niemand daneben eine eigene Preisformel schreibt.
    Genau das war der Fall: kit_bilder.py und kit_hoch.py rechneten
    Megapixel mal 0,025 USD und schrieben das in die Bildnotizen, waehrend
    hier der gemessene Stueckpreis gebucht wurde. Zwei Zahlen fuer dieselbe
    Ausgabe. Preise stehen an EINER Stelle: kosten.json.
    """
    return round(float(stammdaten().get("preise", {}).get(modell, 0.0)) * stueck, 6)


def preis(modell: str, stueck: int = 1) -> float:
    """Was ein Stueck dieses Modells kostet, in EUR. Gemessen, nicht geraten."""
    return eur(float(stammdaten().get("preise", {}).get(modell, 0.0)) * stueck)


def topf_von(kostenstelle: str) -> str:
    for name, topf in stammdaten().get("toepfe", {}).items():
        if kostenstelle in (topf.get("module") or []):
            return name
    # Unbekannte Kennung faellt auf ihren Stamm zurueck: prod.video.neu -> prod.video
    if "." in kostenstelle:
        return topf_von(kostenstelle.rsplit(".", 1)[0])
    return "denken"


def marke(kostenstelle: str, je: str = "lauf") -> float:
    """Die Marke, die der NUTZER gesetzt hat. 0.0 heisst: keine Grenze.

    Es gibt keinen festen Deckel mehr. Wer hier eine Zahl sucht, die
    RepoCity vorgibt, sucht vergeblich - das ist Absicht.
    """
    return bremse.marke(kostenstelle, je)


def pruefstand_grenze(topf: str) -> float:
    """Was ein PRUEFSTANDLAUF in diesem Topf hoechstens ausgeben darf.

    Keine Nutzergrenze und in keiner Oberflaeche sichtbar: der Schutz des
    Werkzeugs vor sich selbst. Ein Testlauf soll nie mehr kosten als ein
    einzelner echter Lauf. Die Zahl steht in kosten.json.
    """
    eintrag = stammdaten().get("toepfe", {}).get(topf, {})
    return float(eintrag.get("pruefstand_grenze_je_lauf", 0.0))


# ------------------------------------------------------------------ Buchen

def buchen(kostenstelle: str, betrag_eur: float = 0.0, wofuer: str = "",
           art: str = GELD, menge: float = 1, dienst: str = "",
           auftrag: str = "", modell: str = "", herkunft: str = ECHT) -> dict:
    """Eine Handlung verbuchen. Nie eine Ausnahme nach aussen.

    Ein Buchungsfehler darf keinen Produktionslauf mitreissen - eine
    verlorene Buchung ist aergerlich, ein angehaltener Lauf ist teurer.
    """
    satz = {
        "zeit": datetime.now().isoformat(timespec="seconds"),
        "kostenstelle": kostenstelle,
        "topf": topf_von(kostenstelle),
        "art": art,
        "betrag_eur": round(float(betrag_eur), 6),
        "menge": menge,
        "dienst": dienst,
        "modell": modell,
        "auftrag": auftrag,
        "wofuer": wofuer,
        "herkunft": herkunft,
    }
    try:
        BUCH.parent.mkdir(parents=True, exist_ok=True)
        with BUCH.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps(satz, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return satz


def fuer_modell(kostenstelle: str, modell: str, stueck: int = 1,
                wofuer: str = "", auftrag: str = "") -> dict:
    """Kurzform: Preis aus der Tabelle nehmen und buchen."""
    return buchen(kostenstelle, preis(modell, stueck), wofuer,
                  art=GELD, menge=stueck, modell=modell, auftrag=auftrag)


def kontingent(dienst: str, kostenstelle: str, anzahl: int = 1,
               wofuer: str = "", herkunft: str = ECHT) -> dict:
    """Einen Zug aus einem freien Kontingent verbuchen."""
    return buchen(kostenstelle, 0.0, wofuer, art=KONTINGENT,
                  menge=anzahl, dienst=dienst, herkunft=herkunft)


# ------------------------------------------------------------------ Lesen

def buchungen(seit: str | None = None, kostenstelle: str | None = None,
              topf: str | None = None, art: str | None = None,
              herkunft: str | None = ECHT) -> list[dict]:
    """Was im Buch steht. seit ist ein ISO-Datum.

    herkunft=ECHT (Vorgabe) laesst Pruefstandbuchungen weg - sonst
    behauptet eine Zahl eine Ausgabe, die nie stattgefunden hat.
    herkunft=None liefert alles."""
    if not BUCH.exists():
        return []
    aus = []
    try:
        with BUCH.open(encoding="utf-8") as datei:
            for zeile in datei:
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    satz = json.loads(zeile)
                except json.JSONDecodeError:
                    continue
                if seit and satz.get("zeit", "")[:10] < seit:
                    continue
                if kostenstelle and satz.get("kostenstelle") != kostenstelle:
                    continue
                if topf and satz.get("topf") != topf:
                    continue
                if art and satz.get("art") != art:
                    continue
                if herkunft and satz.get("herkunft", ECHT) != herkunft:
                    continue
                aus.append(satz)
    except OSError:
        return []
    return aus


def verbraucht(topf: str | None = None, kostenstelle: str | None = None,
               seit: str | None = None) -> float:
    """Wieviel Geld geflossen ist, in EUR."""
    return round(sum(s.get("betrag_eur", 0.0) for s in
                     buchungen(seit, kostenstelle, topf, GELD)), 6)


def monatsanfang() -> str:
    heute = date.today()
    return heute.replace(day=1).isoformat()


def kontingent_stand(dienst: str) -> dict:
    """Was von einem freien Kontingent schon verbraucht ist."""
    grenzen = stammdaten().get("kontingente", {}).get(dienst, {})
    jetzt = datetime.now()
    stunde = (jetzt - timedelta(hours=1)).isoformat(timespec="seconds")
    in_stunde = sum(s.get("menge", 1) for s in buchungen(art=KONTINGENT, herkunft=None)
                    if s.get("dienst") == dienst and s.get("zeit", "") >= stunde)
    im_monat = sum(s.get("menge", 1) for s in
                   buchungen(monatsanfang(), art=KONTINGENT, herkunft=None)
                   if s.get("dienst") == dienst)
    return {
        "dienst": dienst,
        "je_stunde": grenzen.get("je_stunde"),
        "in_dieser_stunde": in_stunde,
        "je_monat": grenzen.get("je_monat"),
        "in_diesem_monat": im_monat,
        "stunde_frei": (grenzen.get("je_stunde") or 0) - in_stunde
        if grenzen.get("je_stunde") else None,
        "monat_frei": (grenzen.get("je_monat") or 0) - im_monat
        if grenzen.get("je_monat") else None,
    }


# ------------------------------------------------------------------ Kategorien

MODELL, PRODUKTION, BETRIEB = "modell", "produktion", "betrieb"


def kategorie_von(satz: dict) -> str:
    """In welche Spalte des Berichts eine Buchung gehoert.

    modell      Token bei einem Sprachmodell (dienst anthropic/openai)
    produktion  alles mit Stueckpreis: Bilder, Stimme, Einbettungen
    kontingent  ein Zug aus einem freien Kontingent
    betrieb     ein fester Posten aus kosten.json/betriebskosten
    """
    if satz.get("art") == KONTINGENT:
        return KONTINGENT
    if satz.get("art") == BETRIEB:
        return BETRIEB
    modelle = stammdaten().get("kategorien", {}).get("modell", ["anthropic", "openai"])
    if satz.get("dienst") in modelle:
        return MODELL
    return PRODUKTION


def betriebskosten_monat() -> tuple[float, list[dict]]:
    """Die festen Posten dieses Monats, in EUR - aus kosten.json, mit Quelle.

    Ein Posten ohne Quelle zaehlt nicht mit: was nicht belegt ist, steht nicht
    im Bericht. Gerechnet, nicht gebucht - sie fallen an, ob etwas laeuft
    oder nicht."""
    posten = []
    summe = 0.0
    for name, eintrag in stammdaten().get("betriebskosten", {}).items():
        if name.startswith("_") or not isinstance(eintrag, dict):
            continue
        if not eintrag.get("quelle"):
            continue
        betrag = (eur(float(eintrag["usd_je_monat"])) if "usd_je_monat" in eintrag
                  else round(float(eintrag.get("eur_je_monat", 0.0)), 6))
        posten.append({"posten": name, "betrag_eur": betrag,
                       "kostenstelle": eintrag.get("kostenstelle", "system.kosten"),
                       "quelle": eintrag["quelle"]})
        summe += betrag
    return round(summe, 6), posten


def zusammenfassung(seit: str | None = None) -> dict:
    """Alles auf einen Blick: Geld je Kategorie, je Kostenstelle, je Topf,
    dazu die festen Posten und was ohne Preis gebucht wurde.

    'ohne_preis' ist die Liste der Modelle, fuer die Geld-Buchungen mit 0 EUR
    stehen - ein Aufruf, der etwas kostet, dessen Preis aber nicht in
    kosten.json steht. Genau die Luecke, die Daniel mit 32/56 meint: erfasst
    ist er, bepreist noch nicht."""
    seit = seit or monatsanfang()
    saetze = buchungen(seit)
    je_kategorie: dict[str, float] = {}
    je_kostenstelle: dict[str, float] = {}
    je_topf: dict[str, float] = {}
    zuege: dict[str, float] = {}
    ohne_preis: dict[str, int] = {}
    bekannte_preise = stammdaten().get("preise", {})
    for s in saetze:
        kat = kategorie_von(s)
        if s.get("art") == KONTINGENT:
            zuege[s.get("dienst") or "?"] = zuege.get(s.get("dienst") or "?", 0) + float(s.get("menge") or 1)
            continue
        betrag = float(s.get("betrag_eur") or 0.0)
        je_kategorie[kat] = round(je_kategorie.get(kat, 0.0) + betrag, 6)
        je_kostenstelle[s["kostenstelle"]] = round(je_kostenstelle.get(s["kostenstelle"], 0.0) + betrag, 6)
        je_topf[s.get("topf", "?")] = round(je_topf.get(s.get("topf", "?"), 0.0) + betrag, 6)
        if kat == PRODUKTION and betrag == 0.0 and s.get("modell") and s["modell"] not in bekannte_preise:
            ohne_preis[s["modell"]] = ohne_preis.get(s["modell"], 0) + 1
    betrieb, posten = betriebskosten_monat()
    je_kategorie[BETRIEB] = betrieb
    laufend = round(sum(v for k_, v in je_kategorie.items() if k_ != BETRIEB), 6)
    return {
        "seit": seit,
        "laufend_eur": laufend,
        "betrieb_eur": betrieb,
        "gesamt_eur": round(laufend + betrieb, 6),
        "je_kategorie": je_kategorie,
        "je_kostenstelle": je_kostenstelle,
        "je_topf": je_topf,
        "kontingent_zuege": zuege,
        "betriebsposten": posten,
        "ohne_preis": ohne_preis,
        "buchungen": len(saetze),
    }


# ------------------------------------------------------------------ Bremse

def stufe(kostenstelle: str, betrag_eur: float,
          schon_im_lauf: float = 0.0) -> tuple[str, str]:
    """Welche Stufe der Nutzermarke gilt hier? (Stufe, Klartext).

    Stufen: frei | warnung | stopp | abbruch. 'warnung' laeuft weiter -
    der Nutzer soll es nur sehen. Fuer die Anzeige in der App gedacht;
    wer nur ja/nein braucht, nimmt darf().
    """
    verbraucht_monat = verbraucht(topf=topf_von(kostenstelle), seit=monatsanfang())
    return bremse.stufe(kostenstelle, betrag_eur, schon_im_lauf, verbraucht_monat)


def darf(kostenstelle: str, betrag_eur: float,
         schon_im_lauf: float = 0.0) -> tuple[bool, str]:
    """Darf diese Handlung stattfinden?

    schon_im_lauf  was dieser Auftrag bereits verbraucht hat. Ist er einmal
                   angefangen, laeuft er ueber die Marke hinaus zu Ende -
                   bis zum Doppelten der Lauf-Marke.

    Ohne gesetzte Marke ist die Antwort immer ja. Das ist keine Luecke,
    sondern die Entscheidung: der Nutzer bestimmt, was er ausgibt.
    """
    name, text = stufe(kostenstelle, betrag_eur, schon_im_lauf)
    return bremse.darf(name), text


def darf_oder_krach(kostenstelle: str, betrag_eur: float,
                    schon_im_lauf: float = 0.0) -> str:
    """Wie darf(), aber wirft Gesperrt statt False zurueckzugeben."""
    ja, grund = darf(kostenstelle, betrag_eur, schon_im_lauf)
    if not ja:
        raise Gesperrt(grund)
    return grund


# ------------------------------------------------------------------ Aufruf

def stand() -> dict:
    """Was jeder Topf in diesem Monat gekostet hat - und welche Marke gilt.

    Der Topf ist eine Sammelstelle zum Zeigen, keine Grenze. Die Marke
    kommt aus den Einstellungen des Nutzers und ist meistens 0: keine.
    """
    aus = {}
    for name, topf in stammdaten().get("toepfe", {}).items():
        module = topf.get("module") or []
        aus[name] = {
            "monat": round(verbraucht(topf=name, seit=monatsanfang()), 4),
            "marke_monat": max([bremse.marke(m, "monat") for m in module] or [0.0]),
            "marke_lauf": max([bremse.marke(m, "lauf") for m in module] or [0.0]),
        }
    return aus


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    if befehl == "stand":
        print("%-22s %10s %12s %8s" % ("Topf", "Monat", "deine Marke", "Anteil"))
        print("-" * 56)
        for name, z in stand().items():
            if z["marke_monat"]:
                print("%-22s %9.4f€ %11.2f€ %6.1f %%"
                      % (name, z["monat"], z["marke_monat"],
                         z["monat"] / z["marke_monat"] * 100))
            else:
                print("%-22s %9.4f€ %11s %8s"
                      % (name, z["monat"], "keine", "-"))
        print()
        for dienst in stammdaten().get("kontingente", {}):
            if dienst.startswith("_"):
                continue
            k = kontingent_stand(dienst)
            print("%-12s %s von %s je Stunde, %s von %s im Monat"
                  % (dienst, k["in_dieser_stunde"], k["je_stunde"],
                     k["in_diesem_monat"], k["je_monat"]))
        return 0
    if befehl == "buch":
        tage = int(argumente[1]) if len(argumente) > 1 else 7
        seit = (date.today() - timedelta(days=tage)).isoformat()
        for s in buchungen(seit):
            print("%s %-20s %-10s %9.5f€ %s"
                  % (s["zeit"][:16], s["kostenstelle"], s["art"],
                     s["betrag_eur"], s.get("wofuer", "")[:40]))
        return 0
    if befehl == "zusammen":
        z = zusammenfassung()
        print("seit %s: %d Buchungen" % (z["seit"], z["buchungen"]))
        for kat, betrag in sorted(z["je_kategorie"].items()):
            print("  %-12s %9.4f EUR" % (kat, betrag))
        print("  %-12s %9.4f EUR  (laufend %.4f + Betrieb %.4f)"
              % ("gesamt", z["gesamt_eur"], z["laufend_eur"], z["betrieb_eur"]))
        for posten in z["betriebsposten"]:
            print("  Betrieb: %-28s %7.4f EUR  %s" % (posten["posten"], posten["betrag_eur"], posten["quelle"][:60]))
        for dienst, menge in z["kontingent_zuege"].items():
            print("  Kontingent %-10s %6.0f Zuege" % (dienst, menge))
        for modell, anzahl in z["ohne_preis"].items():
            print("  OHNE PREIS: %s (%d mal) - Preis fehlt in kosten.json" % (modell, anzahl))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
