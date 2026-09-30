# -*- coding: utf-8 -*-
"""Die Kopfkur: dem Altbestand nachtragen, was der Kurator heute verlangt.

Der Grossteil von `wissen/` kam in einem Rutsch aus den Transkripten ins Regal -
vor dem Kurator, also ohne seine Pruefung. Drei Maengel, alle bei allen:

  1 Der Titel ist der Dateiname ("07_im_Abitur_-_geht_das_wirklich_transcript").
    Er sagt nicht, worum es geht, und die Bedeutungssuche findet darueber nichts.
  2 Keine Quelle, kein `erfasst_von`. Kein Agent kann sich darauf berufen.
  3 (geprueft und in Ordnung: die Umlaute. Am 13.09. sah es in einer
    PowerShell-Ausgabe nach Verstuemmelung aus - das war der Anzeigefehler des
    Werkzeugs, nicht die Datei. Die Heilung unten bleibt trotzdem drin, als
    Wache fuer den Fall, dass einmal wirklich so etwas hereinkommt; sie fasst
    nichts an, wenn nichts kaputt ist.)

Was die Kur macht, und was sie ausdruecklich nicht macht:

  macht    verstuemmelte Umlaute reparieren, falls welche auftauchen - rein
           mechanisch, mit Gegenprobe: der Weg zurueck muss denselben Text
           ergeben, sonst wird nichts angefasst
  macht    Titel aus dem Dateinamen lesbar machen: Unterstriche zu Leerzeichen,
           "_transcript" weg, erster Buchstabe gross
  macht    Quelle und `erfasst_von` nachtragen, wahrheitsgemaess: "Transkript,
           Altbestand vor dem Kurator" - keine erfundene Adresse
  macht    das Schlagwort "altbestand" setzen, damit man sie wiederfindet
  macht NICHT einen inhaltlichen Titel erfinden. Der braeuchte ein Modell je
           Notiz; bei mehreren tausend Notizen ist das eine eigene Entscheidung
           mit eigenen Kosten, keine Nebenwirkung einer Kur.

    python kopfkur.py --trocken      nur zaehlen, nichts anfassen
    python kopfkur.py --nur 20       an zwanzig Dateien vorfuehren
    python kopfkur.py                die Kur durchfuehren
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

KERN = Path(__file__).resolve().parent
GEHIRN = KERN.parent.parent / "mein_ki_gehirn"
WISSEN = GEHIRN / "wissen"

KOPF = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)

# Woran man die verstuemmelten Umlaute erkennt: das typische Vorzeichen des
# Doppelfehlers (UTF-8-Bytes als Windows-Zeichensatz gelesen), gefolgt von einem
# Zeichen aus dem oberen Bereich. Es wird nicht Zeichen fuer Zeichen ersetzt,
# sondern der ganze Vorgang rueckgaengig gemacht - das trifft auch Zeichen, an
# die hier niemand gedacht hat.
VORZEICHEN = re.compile("[ÃÂÄÅ]["
                        "-¿–—‚-„ƒ†…]")


def umlaute_heilen(text: str) -> tuple[str, int]:
    """Den Doppelfehler rueckgaengig machen - aber nur, wenn er aufgeht.

    Geht er nicht auf, bleibt der Text unveraendert. Ein halb geheilter Text
    waere schlimmer als ein durchgehend verstuemmelter: man merkt ihn nicht mehr.
    """
    treffer = len(VORZEICHEN.findall(text))
    if not treffer:
        return text, 0
    try:
        geheilt = text.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text, 0
    # Die Gegenprobe: der Weg zurueck muss genau den Ausgangstext ergeben. Sonst
    # war es kein Doppelfehler, sondern echter Inhalt - und wir haetten ihn
    # zerstoert.
    try:
        if geheilt.encode("utf-8").decode("cp1252", errors="strict") != text:
            return text, 0
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text, 0
    return geheilt, treffer


def titel_lesbar(roh: str) -> str:
    """Aus einem Dateinamen einen lesbaren Titel machen. Nichts erfinden."""
    t = re.sub(r"_transcript$", "", roh.strip())
    t = t.replace("_", " ")
    t = re.sub(r"\s+", " ", t).strip(" -")
    return (t[:1].upper() + t[1:]) if t else roh


def _felder(kopftext: str) -> dict:
    felder = {}
    for zeile in kopftext.splitlines():
        if ":" in zeile and not zeile.startswith((" ", "-", "\t")):
            name, _, wert = zeile.partition(":")
            felder[name.strip()] = wert.strip()
    return felder


def _tags_mit_altbestand(roh: str) -> str:
    """Das Schlagwort anhaengen, ohne die vorhandenen zu verlieren."""
    roh = (roh or "").strip()
    if "altbestand" in roh:
        return roh
    if roh.startswith("[") and roh.endswith("]"):
        inhalt = roh[1:-1].strip()
        return "[%s]" % (inhalt + ", altbestand" if inhalt else "altbestand")
    return "[%s, altbestand]" % roh if roh else "[altbestand]"


def _kopf_aus_dem_text(text: str, datei: Path):
    """Aus Ueberschrift und Quellenzeile einen Kopf bauen. Nichts erfinden.

    Gibt (neuer Text, Titel, Quelle-nachgetragen) zurueck, oder None, wenn nicht
    einmal eine Ueberschrift dasteht.
    """
    ueberschrift = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    if not ueberschrift:
        return None
    titel = ueberschrift.group(1).strip()

    # Die Quellenzeile, wie sie in diesen Dokumenten steht: **Quelle:** ... oder
    # **Quellen:** gefolgt von einer Aufzaehlung.
    quellen = []
    q = re.search(r"\*\*Quellen?:\*\*\s*(.*?)(?:\n\n|\n#)", text, re.S)
    if q:
        roh = q.group(1).strip()
        for zeile in roh.splitlines():
            zeile = zeile.strip().lstrip("-").strip()
            if zeile:
                quellen.append(zeile)
    quelle_nachgetragen = not quellen
    if not quellen:
        quellen = ["Handgeschriebenes Projektdokument, Herkunft im Text"]

    # Die Art aus dem Dateinamen ablesen - die Benennung im Projekt ist eindeutig.
    stamm = datei.stem.lower()
    typ = ("bauplan" if stamm.startswith("bauplan") else
           "norm" if stamm.startswith(("norm", "mass", "fristen")) else
           "recht" if ("datenschutz" in stamm or "verordnung" in stamm
                       or "gesetz" in stamm) else
           "tech-wissen")

    zeilen = ['title: "%s"' % titel.replace('"', "'"),
              "tags: [%s, projektdokument]" % typ,
              "typ: %s" % typ,
              "quellen:"]
    zeilen += ["- %s" % q_.replace('"', "'") for q_ in quellen[:6]]
    zeilen += ["erfasst_am: %s" % date.today().isoformat(),
               "erfasst_von: kopfkur-projektdokument",
               'hinweis: "Von Hand geschriebenes Projektdokument. Titel und '
               'Quelle stehen im Text; der Kopf wurde daraus gebaut, nichts '
               'ergaenzt."']
    return "---\n" + "\n".join(zeilen) + "\n---\n\n" + text.lstrip(), titel, quelle_nachgetragen


def eine_datei(datei: Path, trocken: bool) -> dict:
    befund = {"datei": datei.name, "umlaute": 0, "titel_neu": "", "quelle_neu": False,
              "geaendert": False, "grund": ""}
    try:
        text = datei.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as fehler:
        befund["grund"] = "nicht lesbar: %s" % fehler
        return befund

    neu, treffer = umlaute_heilen(text)
    befund["umlaute"] = treffer

    kopf = KOPF.match(neu)
    if not kopf:
        # Kein Kopf heisst nicht schlechte Notiz: die handgeschriebenen
        # Projektdokumente (Bauplaene, Normen, Rechtstexte) tragen ihren Titel
        # als Ueberschrift und ihre Quelle als **Quelle:**-Zeile im Text. Daraus
        # laesst sich ein Kopf bauen, ohne etwas zu erfinden.
        gebaut = _kopf_aus_dem_text(neu, datei)
        if gebaut is None:
            befund["grund"] = ("kein Kopf und keine Ueberschrift - der Kurator "
                               "wuerde sie abweisen")
            if treffer and not trocken:
                datei.write_text(neu, encoding="utf-8", newline="")
            befund["geaendert"] = bool(treffer)
            return befund
        befund["titel_neu"] = gebaut[1]
        befund["quelle_neu"] = gebaut[2]
        befund["geaendert"] = True
        if not trocken:
            datei.write_text(gebaut[0], encoding="utf-8", newline="")
        return befund

    felder = _felder(kopf.group(1))
    rumpf = neu[kopf.end():]

    alter_titel = felder.get("title", "").strip('"').strip("'")
    titel = alter_titel
    # Nur anfassen, wenn der Titel wirklich der Dateiname ist. Wer schon einen
    # richtigen Titel hat, behaelt ihn.
    if alter_titel == datei.stem or alter_titel.replace(" ", "_") == datei.stem:
        titel = titel_lesbar(datei.stem)
        befund["titel_neu"] = titel

    zeilen = ['title: "%s"' % titel.replace('"', "'")]
    zeilen.append("tags: %s" % _tags_mit_altbestand(felder.get("tags", "")))
    zeilen.append("typ: %s" % (felder.get("typ") or "tech-wissen"))
    if felder.get("thema"):
        zeilen.append("thema: %s" % felder["thema"])

    hat_quelle = bool(felder.get("quelle") or felder.get("quellen"))
    if hat_quelle:
        for name in ("quelle", "quellen"):
            if felder.get(name):
                zeilen.append("%s: %s" % (name, felder[name]))
    else:
        zeilen += ["quellen:",
                   "- Transkript, Altbestand vor dem Kurator "
                   "(Herkunft nicht mehr feststellbar)"]
        befund["quelle_neu"] = True

    zeilen.append("erfasst_am: %s" % (felder.get("erfasst_am") or date.today().isoformat()))
    zeilen.append("erfasst_von: %s" % (felder.get("erfasst_von") or "kopfkur-altbestand"))
    if felder.get("hinweis"):
        zeilen.append("hinweis: %s" % felder["hinweis"])
    else:
        zeilen.append('hinweis: "Altbestand aus dem Transkriptpaket, vor dem '
                      'Kurator ins Regal gekommen. Der Titel ist der Name der '
                      'Quelle, kein inhaltlicher Titel - worum es geht, steht in '
                      'der Zusammenfassung darunter."')

    ergebnis = "---\n" + "\n".join(zeilen) + "\n---\n" + rumpf
    befund["geaendert"] = ergebnis != text
    if befund["geaendert"] and not trocken:
        datei.write_text(ergebnis, encoding="utf-8", newline="")
    return befund


def _main(argumente: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    z = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    z.add_argument("--trocken", action="store_true", help="nur zaehlen, nichts anfassen")
    z.add_argument("--nur", type=int, default=0, help="nur so viele Dateien")
    w = z.parse_args(argumente)

    dateien = sorted(WISSEN.rglob("*.md"))
    if w.nur:
        dateien = dateien[:w.nur]
    if not dateien:
        print("Nichts in %s" % WISSEN)
        return 0

    umlaute = titel = quellen = geaendert = ohne_kopf = unlesbar = 0
    beispiele = []
    for datei in dateien:
        b = eine_datei(datei, w.trocken)
        umlaute += 1 if b["umlaute"] else 0
        titel += 1 if b["titel_neu"] else 0
        quellen += 1 if b["quelle_neu"] else 0
        geaendert += 1 if b["geaendert"] else 0
        if "kein Kopf" in b["grund"]:
            ohne_kopf += 1
        if "nicht lesbar" in b["grund"]:
            unlesbar += 1
        if b["titel_neu"] and len(beispiele) < 5:
            beispiele.append("%s\n          -> %s" % (datei.stem[:62], b["titel_neu"][:62]))

    print("%s %d Dateien" % ("TROCKEN, nichts angefasst:" if w.trocken else "Kur an", len(dateien)))
    print("  Umlaute zu reparieren   %d" % umlaute)
    print("  Titel lesbar zu machen  %d" % titel)
    print("  Quelle nachzutragen     %d" % quellen)
    print("  ohne Kopf               %d" % ohne_kopf)
    print("  nicht lesbar            %d" % unlesbar)
    print("  insgesamt betroffen     %d" % geaendert)
    if beispiele:
        print("\nSo wuerden die Titel aussehen:")
        for b in beispiele:
            print("  " + b)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
