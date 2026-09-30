# -*- coding: utf-8 -*-
"""Der Dokumentwandler: was du hinlegst, liegt danach in der Wissensdatenbank.

Ablauf in einem Satz: Datei in den Ablegeordner -> Markdown -> entkernt ->
Eingang fuer den Kurator -> der pflegt ein. Niemand schreibt an ihm vorbei.

    mein_ki_gehirn/eingang/dokumente/_neu/       hier legst du ab
    mein_ki_gehirn/eingang/dokumente/<datum>_<name>/   das baut er daraus
    mein_ki_gehirn/eingang/dokumente/_verarbeitet/     dorthin wandert das Original

Warum ein eigener Schritt und nicht direkt in `wissen/`: der Kurator ist die
einzige Stelle, die in die vier Saeulen schreibt. Wer an ihm vorbei schreibt,
umgeht die Pruefung auf Kopf, Quelle, Mindestlaenge und Doppelung - und vor
allem landet nichts in der Vektorsaeule. Die Notiz waere eine Datei, die kein
Agent ueber eine Bedeutungssuche findet.

Der Obsidian Clipper legt hier ebenfalls ab: `mein_ki_gehirn` ist ein Vault,
und der Ablegeordner liegt darin. Eine geclippte Seite kommt mit einem eigenen
Kopf (`source`, `author`, `published`); der wird gelesen, damit die Adresse der
Seite als Quelle stehen bleibt und nicht der Dateiname. Danach geht sie
denselben Weg wie jedes andere Dokument - am Ende hat sie dieselbe Form wie die
Notizen aus den Transkripten.

Was gewandelt wird: PDF, Word, PowerPoint, Excel, HTML, EPUB, CSV, JSON, XML,
Text und Markdown - alles, was `markitdown` kann. Bilder und Ton laesst er
liegen: dafuer gibt es andere Wege, und ein leerer Text waere schlimmer als
gar keiner.

Was "entkernt" heisst: markitdown gibt den Rohtext, samt Menuezeilen, Fussnoten
und Geschwaetz. Der Destillierer (kern/destillat.py) macht daraus die
Wissensnotiz und die belegten Einzelaussagen. Ohne Modellschluessel nimmt er
den Ausschnitt-Weg und markiert die Aussagen als "roh" - dann steht es dem
Kurator ins Gesicht geschrieben, dass noch jemand draufsehen muss.

    python dokumentwandler.py                  alles im Ablegeordner wandeln
    python dokumentwandler.py --datei X.pdf    nur diese eine
    python dokumentwandler.py --trocken        nur sagen, was er taete
    python dokumentwandler.py --leitfrage "?"  Leitfrage fuer die Entkernung
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

KERN = Path(__file__).resolve().parent
UNIVERSE = KERN.parent
WURZEL = UNIVERSE.parent
GEHIRN = WURZEL / "mein_ki_gehirn"
EINGANG = GEHIRN / "eingang" / "dokumente"
ABLAGE = EINGANG / "_neu"
ERLEDIGT = EINGANG / "_verarbeitet"

# Was markitdown zuverlaessig kann und wovon ein Sachtext zu erwarten ist.
# Bilder und Ton stehen bewusst nicht drin: markitdown gaebe dort nur die
# Beschriftung heraus, und eine Notiz aus drei Woertern ist keine Notiz.
KANN = {".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".xls", ".html", ".htm",
        ".epub", ".csv", ".json", ".xml", ".txt", ".md", ".rtf", ".msg", ".zip"}

# Unter so vielen Zeichen lohnt die Entkernung nicht - der Kurator wuerde die
# Notiz ohnehin als "zu duenn" zurueckgeben (mindestzeichen_notiz = 400).
MINDESTENS = 400


def _laden(name: str, datei: Path):
    """Ein Nachbarmodul ueber den Pfad laden, nicht ueber den Namen.

    Im Universe tragen mehrere Ordner gleichnamige Module (gehirn.py,
    umgebung.py, pruefungen.py). Ein normaler Import erwischt das falsche.
    """
    fertig = sys.modules.get(name)
    if fertig is not None:
        return fertig
    beschreibung = importlib.util.spec_from_file_location(name, datei)
    modul = importlib.util.module_from_spec(beschreibung)
    sys.modules[name] = modul
    beschreibung.loader.exec_module(modul)
    return modul


destillat = _laden("kern_destillat", KERN / "destillat.py")
modellwahl = _laden("kern_modellwahl", KERN / "modellwahl.py")
try:
    umgebung = _laden("kern_umgebung", KERN / "umgebung.py")
    umgebung.laden()
except Exception:                                   # ohne .env laeuft er trotzdem
    pass


# ---------------------------------------------------------------- wandeln

def wandelbar(datei: Path) -> bool:
    return datei.is_file() and datei.suffix.lower() in KANN and not datei.name.startswith(".")


def nach_markdown(datei: Path) -> str:
    """Die Datei durch markitdown schicken. Gibt den Rohtext zurueck."""
    from markitdown import MarkItDown
    ergebnis = MarkItDown(enable_plugins=False).convert(str(datei))
    return (ergebnis.text_content or "").strip()


# Der Kopf, den der Obsidian Clipper schreibt. Unter diesen Namen steht die
# Adresse der Seite - je nach Vorlage anders benannt, deshalb mehrere.
QUELLFELDER = ("source", "url", "quelle", "link", "permalink")


def _clipperkopf(text: str) -> dict:
    """Aus einer geclippten Seite Adresse, Titel und Verfasser holen.

    Nur die flachen Felder; verschachteltes YAML kommt in einem Clipper-Kopf
    nicht vor, und ein YAML-Paket dafuer zu laden waere eine Abhaengigkeit
    fuer nichts.
    """
    treffer = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not treffer:
        return {}
    felder = {}
    for zeile in treffer.group(1).splitlines():
        if ":" in zeile and not zeile.startswith((" ", "-", "\t")):
            name, _, wert = zeile.partition(":")
            felder[name.strip().lower()] = wert.strip().strip('"').strip("'")
    return felder


def _quelle_bestimmen(datei: Path, roh: str) -> tuple[str, str]:
    """Was als Quelle in der Notiz steht - und welcher Titel gilt.

    Eine geclippte Seite nennt ihre Adresse selbst. Die gehoert in die Notiz:
    daran erkennt der Kurator eine Doppelung, und ein Agent kann nachsehen.
    Bei allem anderen bleibt es beim Dateinamen.
    """
    kopf = _clipperkopf(roh)
    for feld in QUELLFELDER:
        wert = kopf.get(feld, "")
        if wert.startswith(("http://", "https://")):
            return wert, (kopf.get("title") or datei.stem)
    return "Datei: " + datei.name, datei.stem


def _thema(datei: Path) -> str:
    """Aus dem Dateinamen einen Ordnernamen machen, der keine Ueberraschung ist."""
    stamm = re.sub(r"[^A-Za-z0-9\-]+", "-", datei.stem.lower()).strip("-")
    return (stamm or "dokument")[:48]


def _leitfrage(datei: Path, gesetzt: str) -> str:
    """Die Frage, an der die Entkernung sich ausrichtet.

    Vorrang hat, was auf der Kommandozeile steht. Danach eine Beidatei
    `<name>.frage.txt` neben dem Dokument - so kann man beim Ablegen sagen,
    worauf es ankommt, ohne einen Befehl zu tippen. Sonst der Dateiname.
    """
    if gesetzt:
        return gesetzt
    bei = datei.with_suffix(datei.suffix + ".frage.txt")
    if bei.exists():
        text = bei.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            return text
    lesbar = re.sub(r"[_\-]+", " ", datei.stem).strip()
    return "Was steht in '%s' an Sachgehalt, den ein Agent spaeter anwenden kann?" % lesbar


def _modellkonfiguration() -> dict:
    return {"modell": {"name": modellwahl.MODELL,
                       "schluessel_umgebung": "ANTHROPIC_API_KEY"}}


def eine_datei(datei: Path, leitfrage: str = "", trocken: bool = False) -> dict:
    """Eine Datei wandeln, entkernen und als Eingang hinlegen.

    Gibt einen Befund zurueck: was daraus wurde und wohin es ging.
    """
    befund = {"datei": datei.name, "ok": False, "grund": "", "ordner": "",
              "zeichen": 0, "atome": 0, "weg": "", "quelle": ""}

    if not wandelbar(datei):
        befund["grund"] = "Art wird nicht gewandelt (%s)" % (datei.suffix or "ohne Endung")
        return befund

    try:
        roh = nach_markdown(datei)
    except ImportError:
        befund["grund"] = ("markitdown fehlt - `pip install markitdown[all]` "
                           "im selben Python, mit dem dieser Aufruf laeuft")
        return befund
    except Exception as fehler:
        befund["grund"] = "markitdown kam nicht durch: %s" % fehler
        return befund

    befund["zeichen"] = len(roh)
    if len(roh) < MINDESTENS:
        befund["grund"] = ("nur %d Zeichen herausgekommen - der Kurator naehme sie "
                           "als 'zu duenn' ohnehin nicht an" % len(roh))
        return befund

    quelle, quelltitel = _quelle_bestimmen(datei, roh)
    befund["quelle"] = quelle
    frage = _leitfrage(datei, leitfrage)
    thema = _thema(datei)
    ziel = EINGANG / ("%s_%s" % (date.today().isoformat(), thema))

    if trocken:
        befund.update(ok=True, ordner=str(ziel), grund="trocken - nichts geschrieben",
                      weg="wuerde entkernen")
        return befund

    inhalt = destillat.destillieren(frage, quelltitel, quelle, roh,
                                    _modellkonfiguration())
    befund["weg"] = inhalt.get("weg", "?")
    if not inhalt.get("brauchbar", True):
        befund["grund"] = "Entkernung sagt unbrauchbar: %s" % inhalt.get("grund", "")
        return befund

    # Bei einer geclippten Seite steht hier ihre Adresse, sonst der Dateiname.
    # Der Kurator verlangt eine Quelle - eine Adresse ist die bessere.
    notiz = destillat.notiz_bauen(inhalt, quelle, thema, agent="dokumentwandler")
    atome = destillat.atome_bauen(inhalt, quelle, quelltitel, thema,
                                  agent="dokumentwandler")

    (ziel / "wissen").mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9\-_]+", "-", datei.stem)[:60] or "notiz"
    (ziel / "wissen" / (name + ".md")).write_text(notiz, encoding="utf-8", newline="")

    with (ziel / "atome.jsonl").open("a", encoding="utf-8") as offen:
        for atom in atome:
            offen.write(json.dumps(atom, ensure_ascii=False) + "\n")
    befund["atome"] = len(atome)

    _quellen_ergaenzen(ziel, datei, roh, inhalt.get("weg", "?"), quelle)
    _uebergabe_schreiben(ziel)

    ERLEDIGT.mkdir(parents=True, exist_ok=True)
    shutil.move(str(datei), str(_frei(ERLEDIGT / datei.name)))
    bei = datei.with_suffix(datei.suffix + ".frage.txt")
    if bei.exists():
        shutil.move(str(bei), str(_frei(ERLEDIGT / bei.name)))

    befund.update(ok=True, ordner=str(ziel))
    return befund


def _frei(ziel: Path) -> Path:
    """Einen freien Namen finden, statt ein Original zu ueberschreiben."""
    if not ziel.exists():
        return ziel
    stempel = datetime.now().strftime("%H%M%S")
    return ziel.with_name("%s_%s%s" % (ziel.stem, stempel, ziel.suffix))


def _quellen_ergaenzen(ziel: Path, datei: Path, roh: str, weg: str,
                       quelle: str = "") -> None:
    pfad = ziel / "quellen.json"
    daten = {"herkunft": "Vom Dokumentwandler gewandelt", "dateien": []}
    if pfad.exists():
        try:
            daten = json.loads(pfad.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    daten.setdefault("dateien", []).append({
        "name": datei.name,
        "art": datei.suffix.lower(),
        "zeichen_roh": len(roh),
        "gewandelt_am": datetime.now().isoformat(timespec="seconds"),
        "entkernt": weg,
        "quelle": quelle,
    })
    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=1),
                    encoding="utf-8", newline="")


def _uebergabe_schreiben(ziel: Path) -> None:
    notizen = len(list((ziel / "wissen").glob("*.md"))) if (ziel / "wissen").exists() else 0
    zeilen = 0
    atomdatei = ziel / "atome.jsonl"
    if atomdatei.exists():
        zeilen = sum(1 for z in atomdatei.read_text(encoding="utf-8").splitlines() if z.strip())
    (ziel / "UEBERGABE.md").write_text(
        "---\ntyp: uebergabe\nvon: dokumentwandler\nan: kurator\ndatum: %s\n"
        'frage: "Abgelegte Dokumente - Sachgehalt fuer die Wissensdatenbank"\n'
        "notizen: %d\natome: %d\nstatus: offen\n---\n\n"
        "# Abgelegte Dokumente\n\n"
        "## Was hier liegt\n"
        "- `wissen/` - %d Notizen, aus abgelegten Dateien gewandelt und entkernt.\n"
        "- `atome.jsonl` - %d belegte Einzelaussagen.\n"
        "- `quellen.json` - welche Datei welche Notiz ergeben hat.\n\n"
        "## Wie es hierher kam\n"
        "Die Datei lag in `eingang/dokumente/_neu/`. Der Dokumentwandler hat sie mit\n"
        "markitdown nach Markdown gebracht, den Sachgehalt herausgeloest und das\n"
        "Original nach `_verarbeitet/` gelegt. Eingepflegt wird hier nichts - das\n"
        "macht der Kurator.\n"
        % (date.today().isoformat(), notizen, zeilen, notizen, zeilen),
        encoding="utf-8", newline="")


# ---------------------------------------------------------------- Lauf

def einmal(leitfrage: str = "", trocken: bool = False) -> list[dict]:
    """Alles wandeln, was im Ablegeordner liegt."""
    ABLAGE.mkdir(parents=True, exist_ok=True)
    befunde = []
    for datei in sorted(ABLAGE.iterdir()):
        if datei.name.endswith(".frage.txt"):
            continue                                # Beidatei, kein Dokument
        if not wandelbar(datei):
            continue
        befunde.append(eine_datei(datei, leitfrage, trocken))
    return befunde


def _melden(befunde: list[dict]) -> None:
    """Dem Sekretaer sagen, was geworden ist. Nie eine Ausnahme nach aussen -
    eine verlorene Meldung ist besser als ein abgebrochener Lauf."""
    if not befunde:
        return
    try:
        melden = _laden("kern_melden", KERN / "melden.py")
        gut = [b for b in befunde if b["ok"]]
        schlecht = [b for b in befunde if not b["ok"]]
        text = "Dokumentwandler: %d gewandelt, %d liegengeblieben." % (len(gut), len(schlecht))
        for b in schlecht:
            text += "\n  %s - %s" % (b["datei"], b["grund"])
        if gut:
            text += "\nEingang steht bereit; der Kurator pflegt beim naechsten Lauf ein."
        melden.melde("dokumentwandler", text,
                     art="warnung" if schlecht else "info")
    except Exception:
        pass


def _main(argumente: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    zerleger = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    zerleger.add_argument("--datei", default="", help="nur diese eine Datei")
    zerleger.add_argument("--leitfrage", default="", help="Frage fuer die Entkernung")
    zerleger.add_argument("--trocken", action="store_true", help="nur sagen, was er taete")
    wahl = zerleger.parse_args(argumente)

    if wahl.datei:
        datei = Path(wahl.datei)
        if not datei.is_absolute():
            datei = ABLAGE / datei
        befunde = [eine_datei(datei, wahl.leitfrage, wahl.trocken)]
    else:
        befunde = einmal(wahl.leitfrage, wahl.trocken)

    if not befunde:
        print("Ablegeordner leer: %s" % ABLAGE)
        return 0
    for b in befunde:
        zeichen = "ok " if b["ok"] else "-- "
        print("%s%s" % (zeichen, b["datei"]))
        if b["ok"]:
            print("     %d Zeichen roh, %d Atome, entkernt: %s"
                  % (b["zeichen"], b["atome"], b["weg"]))
            print("     -> %s" % b["ordner"])
        else:
            print("     %s" % b["grund"])
    if not wahl.trocken:
        _melden(befunde)
    return 0 if all(b["ok"] for b in befunde) else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
