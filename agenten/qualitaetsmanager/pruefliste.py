"""Was der Qualitaetsmanager misst, bevor er urteilt.

Getrennt in zwei Sorten, und die Trennung ist der ganze Punkt:

  HART    Zahlen, fuer die niemand hinsehen muss: Datei da, Laenge, Aufloesung,
          Tonspur, Pegel, Dateigroesse, vollstaendiger Beipackzettel, Kosten
          im Rahmen. Kostet nichts, entscheidet die Haelfte der Faelle allein.

  GELERNT alles, was aus einem bestaetigten Lehrsatz kommt. Ein Lehrsatz, der
          sich messen laesst, wird hier zu einer harten Pruefung - das ist die
          Stelle, an der aus "gelernt" tatsaechlich "geprueft" wird. Alles
          andere haengt als Merkposten am Befund, damit der Pruefer es sieht.

Was hier NICHT steht: Geschmack. Ob ein Schnitt gut sitzt, entscheidet kein
Grenzwert. Dafuer gibt es den Kontaktbogen und, wenn du es willst, ein
Modell - beides in main.py und beides abschaltbar.
"""
from __future__ import annotations

import json
import re
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
from dataclasses import dataclass, field
from pathlib import Path

#: Grenzwerte. Sie stehen hier, damit sie an einer Stelle stehen.
GRENZEN = {
    "video": {
        "sekunden_min": 3.0,
        "sekunden_max": 180.0,
        "breite_min": 640,
        "hoehe_min": 640,
        "groesse_mb_min": 0.05,
        "braucht_ton": True,
        "stille_am_stueck_max": 4.0,
    },
    "bild": {
        "breite_min": 512,
        "hoehe_min": 512,
        "groesse_mb_min": 0.01,
    },
    "ton": {
        "sekunden_min": 3.0,
        "groesse_mb_min": 0.02,
    },
    "text": {
        "zeichen_min": 200,
    },
    # ---- Life Automation --------------------------------------------
    # Ein Anschreiben nach DIN 5008: Fliesstext rund 55 Zeichen je Zeile.
    # Vier Absaetze zu je vier Zeilen sind 16 Zeilen -> 16 x 55 = 880.
    # Darunter fehlt ein Absatz. Nach oben: eine Seite bei 11 pt fasst
    # rund 3.000 Zeichen, und mehr als eine Seite liest kein Personaler.
    "anschreiben": {
        "zeichen_min": 880,
        "zeichen_max": 3000,
        "ohne_platzhalter": True,
    },
    # Eine Anfrage auf ein Inserat: Anrede, Selbstvorstellung, Bezug auf die
    # Wohnung, Gruss mit Telefon. Gemessen an der eingebauten Vorlage in
    # wohnungs_agent/antwort.py: sie ergibt gefuellt rund 420 Zeichen, leer
    # 300. Unter 300 fehlt eins der vier Stuecke. Nach oben 1.800: das sind
    # rund sechs Absaetze - laenger liest ein Vermieter nicht.
    "wohnungsanfrage": {
        "zeichen_min": 300,
        "zeichen_max": 1800,
        "ohne_platzhalter": True,
    },
    # Eine Mailantwort darf kurz sein ("Dienstag 14 Uhr passt.") - mit
    # Grussformel und Signatur kommt sie auf rund 60 Zeichen. Weniger ist
    # keine Antwort, sondern ein Fragment. Nach oben 4.000: darueber ist es
    # kein Antwortschreiben mehr, sondern ein Dokument.
    "mailantwort": {
        "zeichen_min": 60,
        "zeichen_max": 4000,
        "ohne_platzhalter": True,
    },
    # Ein Weckruf ist keine Datei, sondern ein Termin. Gemessen werden
    # seine Pflichtfelder: ohne Titel weiss der Geweckte nicht, worum es
    # geht, ohne Beginn nicht, wann.
    "termin": {
        "pflichtfelder": ("titel", "beginn"),
    },
    # Ein Bau des Implementierers. Gemessen wird nicht die Datei, sondern
    # der Ordner daneben - und der Pruefbericht, den die Werkbank beim
    # Uebersetzen geschrieben hat.
    "code": {
        "dateien_min": 1,
        "zeilen_min": 20,
        "muss_uebersetzen": True,
        "durchgefallen_max": 0,
    },
}


#: Was wie Text gemessen wird - Zeichen zaehlen, Woerter zaehlen, Luecken
#: suchen. Alles andere braucht eine Datei.
TEXTARTEN = ("text", "anschreiben", "wohnungsanfrage", "mailantwort")


@dataclass
class Befund:
    """Was die Maschine sagen kann, ohne zu urteilen."""
    was: str = ""
    gemessen: dict = field(default_factory=dict)
    maengel: list[str] = field(default_factory=list)
    merkposten: list[str] = field(default_factory=list)
    geprueft_gegen: list[str] = field(default_factory=list)

    @property
    def bestanden(self) -> bool:
        return not self.maengel

    def als_text(self) -> str:
        teile = []
        if self.gemessen:
            teile.append("Gemessen: " + ", ".join(
                "%s %s" % (k, v) for k, v in self.gemessen.items()))
        if self.maengel:
            teile.append("Maengel:\n" + "\n".join("- " + m for m in self.maengel))
        else:
            teile.append("Keine Maengel.")
        if self.geprueft_gegen:
            teile.append("Geprueft gegen: " + ", ".join(self.geprueft_gegen))
        if self.merkposten:
            teile.append("Merkposten aus Lehrsaetzen:\n"
                         + "\n".join("- " + m for m in self.merkposten))
        return "\n\n".join(teile)

    def als_dict(self) -> dict:
        return {"was": self.was, "gemessen": self.gemessen,
                "maengel": self.maengel, "merkposten": self.merkposten,
                "geprueft_gegen": self.geprueft_gegen,
                "bestanden": self.bestanden}


# ------------------------------------------------------------------ Messen

def _ffprobe(datei: Path) -> dict | None:
    try:
        lauf = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", str(datei)],
            capture_output=True, text=True, timeout=60)
        if lauf.returncode != 0:
            return None
        return json.loads(lauf.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _laengste_stille(datei: Path, schwelle_db: int = -45) -> float:
    """Wie lange am Stueck nichts zu hoeren ist. 0.0, wenn nicht messbar."""
    try:
        lauf = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(datei),
             "-af", "silencedetect=noise=%ddB:d=1.0" % schwelle_db,
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return 0.0
    dauern = [float(t) for t in
              re.findall(r"silence_duration:\s*([\d.]+)", lauf.stderr)]
    return max(dauern) if dauern else 0.0


def _bruch(text: str) -> float:
    try:
        if "/" in text:
            oben, unten = text.split("/", 1)
            return float(oben) / float(unten or 1)
        return float(text)
    except (ValueError, ZeroDivisionError):
        return 0.0


# ------------------------------------------------------------------ Hart

def hart_pruefen(was: str, datei: str | Path | None,
                 soll: dict | None = None) -> Befund:
    """Die Zahlen, fuer die niemand hinsehen muss."""
    befund = Befund(was=was)
    grenzen = dict(GRENZEN.get(was, {}))
    grenzen.update(soll or {})

    if was == "termin":
        # Ein Termin traegt keine Datei. Was er tragen muss, steht in den
        # Grenzen - fehlt eins, geht der Ruf nicht hinaus.
        felder = datei if isinstance(datei, dict) else {}
        befund.gemessen["felder"] = len([w for w in felder.values() if str(w).strip()])
        for pflicht in grenzen.get("pflichtfelder", ()):
            if not str(felder.get(pflicht, "")).strip():
                befund.maengel.append(
                    "Dem Weckruf fehlt %s - so weiss der Geweckte nicht, %s."
                    % ({"titel": "der Titel", "beginn": "die Zeit"}.get(pflicht, pflicht),
                       {"titel": "worum es geht", "beginn": "wann"}.get(pflicht, "was gemeint ist")))
        return befund

    if was in TEXTARTEN:
        text = str(datei or "")
        befund.gemessen["zeichen"] = len(text)
        # Woerter, nicht nur Zeichen: eine Praesentation wird nicht nach ihrer
        # Dateilaenge bestellt, sondern nach der Zeit, die jemand zum Vortragen
        # braucht - und die haengt an der Zahl der Woerter.
        woerter = len([w for w in re.split(r"\s+", _ohne_auszeichnung(text)) if w])
        befund.gemessen["woerter"] = woerter
        if len(text) < grenzen.get("zeichen_min", 0):
            befund.maengel.append(
                "Nur %d Zeichen - unter der Grenze von %d."
                % (len(text), grenzen["zeichen_min"]))
        if grenzen.get("woerter_min") and woerter < grenzen["woerter_min"]:
            befund.maengel.append(
                "Nur %d Woerter - fuer die bestellte Vortragsdauer sind "
                "mindestens %d noetig." % (woerter, grenzen["woerter_min"]))
        if grenzen.get("woerter_max") and woerter > grenzen["woerter_max"]:
            befund.maengel.append(
                "%d Woerter - das sind mehr als die %d, die in die bestellte "
                "Vortragsdauer passen." % (woerter, grenzen["woerter_max"]))
        if grenzen.get("zeichen_max") and len(text) > grenzen["zeichen_max"]:
            befund.maengel.append(
                "%d Zeichen - mehr als die %d, die hier hineinpassen."
                % (len(text), grenzen["zeichen_max"]))
        # Ein stehengebliebener Platzhalter ist der Fehler, den niemand
        # bemerkt, bis der Empfaenger ihn liest: "Sehr geehrte {firma}".
        if grenzen.get("ohne_platzhalter"):
            offen = sorted(set(re.findall(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", text)))
            if offen:
                befund.maengel.append(
                    "Es steht noch eine Luecke im Text: %s - die haette "
                    "gefuellt werden muessen." % ", ".join(offen[:4]))
        return befund

    if was == "code":
        return _code_pruefen(datei, grenzen)

    if not datei:
        befund.maengel.append("Es ist gar keine Datei angegeben.")
        return befund
    pfad = Path(datei)
    if not pfad.exists():
        befund.maengel.append("Die Datei fehlt: %s" % pfad)
        return befund

    mb = pfad.stat().st_size / 1_048_576
    befund.gemessen["groesse_mb"] = round(mb, 3)
    if mb < grenzen.get("groesse_mb_min", 0):
        befund.maengel.append("Die Datei ist fast leer (%.3f MB)." % mb)
        return befund

    if was in ("video", "ton"):
        roh = _ffprobe(pfad)
        if roh is None:
            befund.maengel.append("ffprobe kann die Datei nicht lesen.")
            return befund
        sekunden = float(roh.get("format", {}).get("duration", 0) or 0)
        befund.gemessen["sekunden"] = round(sekunden, 2)
        spuren = roh.get("streams", [])
        bild = next((s for s in spuren if s.get("codec_type") == "video"), None)
        ton = next((s for s in spuren if s.get("codec_type") == "audio"), None)
        befund.gemessen["hat_ton"] = ton is not None

        if sekunden < grenzen.get("sekunden_min", 0):
            befund.maengel.append(
                "Nur %.1f Sekunden - da ist etwas schiefgegangen." % sekunden)
        if grenzen.get("sekunden_max") and sekunden > grenzen["sekunden_max"]:
            befund.maengel.append(
                "%.0f Sekunden - laenger als die Grenze von %.0f."
                % (sekunden, grenzen["sekunden_max"]))

        if was == "video":
            if bild is None:
                befund.maengel.append("Keine Bildspur.")
            else:
                b, h = int(bild.get("width", 0)), int(bild.get("height", 0))
                befund.gemessen["breite"] = b
                befund.gemessen["hoehe"] = h
                befund.gemessen["bildrate"] = round(
                    _bruch(bild.get("avg_frame_rate", "0")), 2)
                if b < grenzen.get("breite_min", 0) or h < grenzen.get("hoehe_min", 0):
                    befund.maengel.append("Zu klein: %dx%d." % (b, h))
            if grenzen.get("braucht_ton") and ton is None:
                befund.maengel.append("Keine Tonspur.")
            elif ton is not None:
                stille = _laengste_stille(pfad)
                befund.gemessen["stille_am_stueck"] = round(stille, 1)
                grenze = grenzen.get("stille_am_stueck_max", 0)
                if grenze and stille > grenze:
                    befund.maengel.append(
                        "%.1f Sekunden am Stueck ohne Ton - Grenze ist %.1f."
                        % (stille, grenze))
        return befund

    if was == "bild":
        roh = _ffprobe(pfad)
        if roh is None:
            befund.maengel.append("Die Datei laesst sich nicht als Bild lesen.")
            return befund
        bild = next((s for s in roh.get("streams", [])
                     if s.get("codec_type") == "video"), None)
        if bild is None:
            befund.maengel.append("Keine Bilddaten.")
            return befund
        b, h = int(bild.get("width", 0)), int(bild.get("height", 0))
        befund.gemessen["breite"], befund.gemessen["hoehe"] = b, h
        if b < grenzen.get("breite_min", 0) or h < grenzen.get("hoehe_min", 0):
            befund.maengel.append("Zu klein: %dx%d." % (b, h))
        return befund

    befund.merkposten.append("Fuer '%s' gibt es noch keine harte Pruefung." % was)
    return befund


# ------------------------------------------------------------------ Beipackzettel

#: Ohne diese Felder darf nichts in den Warenausgang.
def _code_pruefen(ordner, grenzen: dict) -> "Befund":
    """Einen Bau pruefen - an dem, was die Werkbank gemessen hat.

    Der Qualitaetsmanager laesst hier nichts selbst laufen. Frisch
    geschriebener Code, den die Abnahme ausfuehrt, koennte die Abnahme
    mitreissen. Er liest den Pruefbericht, den die Werkbank beim
    Uebersetzen geschrieben hat - und wenn keiner da ist, ist das der
    Mangel.
    """
    import json as _json

    befund = Befund(was="code")
    if not ordner:
        befund.maengel.append("Es ist gar kein Bau angegeben.")
        return befund
    pfad = Path(ordner)
    if not pfad.exists():
        befund.maengel.append("Der Bauordner fehlt: %s" % pfad)
        return befund

    bericht_datei = pfad.parent / "pruefbericht.json"
    if not bericht_datei.exists():
        befund.maengel.append(
            "Kein Pruefbericht. Ohne ihn ist nicht belegt, dass der Bau "
            "ueberhaupt uebersetzt.")
        return befund
    try:
        bericht = _json.loads(bericht_datei.read_text(encoding="utf-8"))
    except Exception:
        befund.maengel.append("Der Pruefbericht ist nicht lesbar.")
        return befund

    befund.gemessen["dateien"] = int(bericht.get("dateien", 0))
    befund.gemessen["zeilen"] = int(bericht.get("zeilen", 0))
    befund.gemessen["durchgefallen"] = int(bericht.get("durchgefallen", 0))
    befund.gemessen["bestanden"] = int(bericht.get("bestanden", 0))

    if befund.gemessen["dateien"] < grenzen.get("dateien_min", 1):
        befund.maengel.append("Es ist keine einzige Datei entstanden.")
    if befund.gemessen["zeilen"] < grenzen.get("zeilen_min", 0):
        befund.maengel.append(
            "Nur %d Zeilen - dafuer braucht es keinen Bau."
            % befund.gemessen["zeilen"])
    if grenzen.get("muss_uebersetzen", True) and not bericht.get("uebersetzt"):
        for fehler in bericht.get("uebersetzungsfehler", []) or ["ohne Angabe"]:
            befund.maengel.append("Uebersetzt nicht: %s" % fehler)
    if befund.gemessen["durchgefallen"] > grenzen.get("durchgefallen_max", 0):
        befund.maengel.append(
            "%d Pruefung(en) durchgefallen."
            % befund.gemessen["durchgefallen"])
    if not bericht.get("pruefungen_gelaufen"):
        befund.merkposten.append(
            "Der Bau bringt keine eigenen Pruefungen mit - es ist nur "
            "belegt, dass er uebersetzt.")
    return befund


PFLICHTFELDER = ("was", "auftrag", "modul", "titel", "abgenommen_von")


def _ohne_auszeichnung(text: str) -> str:
    """Nur das, was jemand vorlesen wuerde - ohne Markup und Code.

    Ein Foliensatz kommt als HTML herein. Wer dessen Zeichen zaehlt, zaehlt
    Klammern und Stilangaben mit und kommt auf ein Vielfaches dessen, was
    wirklich gesprochen wird.
    """
    ohne = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", text,
                  flags=re.S | re.I)
    ohne = re.sub(r"<[^>]+>", " ", ohne)
    return ohne


def zettel_pruefen(angaben: dict) -> list[str]:
    maengel = []
    for feld in PFLICHTFELDER:
        wert = str(angaben.get(feld, "")).strip()
        if not wert or wert == "-":
            maengel.append("Im Beipackzettel fehlt: %s" % feld)
    if str(angaben.get("was")) in ("video", "bild") and \
            not str(angaben.get("bildquellen", "")).strip("- \n"):
        maengel.append("Die Bildquellen sind nicht belegt - "
                       "ohne sie darf nichts veroeffentlicht werden.")
    return maengel


# ------------------------------------------------------------------ Gelernt

#: Welches Wort in einem Lehrsatz auf welche gemessene Groesse zeigt.
#: Nur was hier steht, kann aus einem Satz eine echte Pruefung werden.
WORT_ZU_GROESSE = {
    "sekunde": "sekunden",
    "sekunden": "sekunden",
    "laenge": "sekunden",
    "stille": "stille_am_stueck",
    "zeichen": "zeichen",
    "breite": "breite",
    "hoehe": "hoehe",
    "pixel": "breite",
    "bildrate": "bildrate",
}

_WOERTER = "|".join(sorted(WORT_ZU_GROESSE, key=len, reverse=True))

#: Beide Reihenfolgen kommen in echten Saetzen vor:
#:   "hoechstens 10 Sekunden"        Zahl zuerst
#:   "die Laenge liegt unter 10"     Wort zuerst
_ZAHL_DANN_WORT = re.compile(
    r"(?P<zahl>\d+(?:[.,]\d+)?)\s*(?P<wort>%s)[a-z]*" % _WOERTER, re.I)
_WORT_DANN_ZAHL = re.compile(
    r"(?P<wort>%s)[a-z]*[^0-9]{0,28}?(?P<zahl>\d+(?:[.,]\d+)?)" % _WOERTER, re.I)

#: Diese Woerter machen aus der Zahl eine Untergrenze statt einer Obergrenze.
_MINDESTENS = ("mindestens", "wenigstens", "nicht unter", "nicht kuerzer",
               "laenger als", "min.")


def aus_lehrsaetzen(saetze: list[dict], befund: Befund) -> None:
    """Traegt bestaetigte Lehrsaetze in den Befund ein.

    Nennt ein Lehrsatz eine Groesse, die gemessen wurde, und eine Zahl dazu,
    wird daraus eine echte Pruefung. Sonst haengt er als Merkposten am
    Befund - das ist ehrlicher, als so zu tun, als koenne eine Maschine
    "Aufhaenger staerker" nachmessen.
    """
    for satz in saetze:
        text = satz.get("satz", "")
        kennung = satz.get("kennung", "?")
        befund.geprueft_gegen.append(kennung)
        if not _als_pruefung(text, kennung, befund):
            befund.merkposten.append("%s: %s" % (kennung, text))


def _als_pruefung(text: str, kennung: str, befund: Befund) -> bool:
    """True, wenn aus dem Satz wirklich eine Messung wurde."""
    treffer = _ZAHL_DANN_WORT.search(text) or _WORT_DANN_ZAHL.search(text)
    if not treffer:
        return False
    groesse = WORT_ZU_GROESSE.get(treffer.group("wort").lower())
    if groesse is None:
        return False
    gemessen = befund.gemessen.get(groesse)
    if gemessen is None:
        return False

    grenze = float(treffer.group("zahl").replace(",", "."))
    klein = text.lower()
    untergrenze = any(w in klein for w in _MINDESTENS)
    if untergrenze and float(gemessen) < grenze:
        befund.maengel.append(
            "%s: %s ist %s, verlangt sind mindestens %s - \"%s\""
            % (kennung, groesse, gemessen, grenze, text))
    elif not untergrenze and float(gemessen) > grenze:
        befund.maengel.append(
            "%s: %s ist %s, hoechstens %s erlaubt - \"%s\""
            % (kennung, groesse, gemessen, grenze, text))
    return True
