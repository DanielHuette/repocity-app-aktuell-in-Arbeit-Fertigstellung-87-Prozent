"""Der Rueckweg - wie die Agenten aus ihren Auftraegen lernen.

Der Warenausgang regelt nur die Uebergabe. Damit lernt kein Agent etwas.
Lernen heisst hier: die Anweisung, mit der ein Agent beim naechsten Mal
antritt, ist eine andere als beim letzten Mal - und zwar nachweislich zum
Besseren.

Drei Stufen, sie lassen sich nicht abkuerzen:

  Stufe 1  ERFAHRUNG   jeder abgeschlossene Auftrag hinterlaesst eine Spur
  Stufe 2  LEHRSATZ    ab drei gleichartigen Urteilen darf eine Regel
                       vorgeschlagen werden - Daniel bestaetigt sie
  Stufe 3  ZEUGNIS     vier Zahlen je Strasse; eine Regel ohne Wirkung
                       wird zurueckgezogen

Dazu eine vierte Ablage, die nichts lehrt, aber nichts vergessen laesst:

  HALDE                alles, was nach zu vielen Anlaeufen verworfen wurde
                       oder brachliegt - mit Grund und Datum

Und seit dem 11.09.2026 die Prozessfehler, getrennt von den Urteilen:

  TECHNIK              das Modell lieferte nichts, die Antwort war nicht
                       lesbar, der Dienst nicht erreichbar, die Zeit um -
                       liegt unter erfahrungen/_technik, zaehlt nicht ins
                       Zeugnis und wird keinem Agenten als Vorwissen
                       vorgelesen; der Ausbilder haeuft es getrennt

Alles liegt doppelt: als Markdown im Vault (damit Daniel es in Obsidian
lesen und korrigieren kann) und in der Vektordatenbank (damit ein Agent es
findet). Das Markdown ist die Wahrheit; die Datenbank ist nur der Index.
Faellt die Datenbank aus, wird still ohne sie weitergearbeitet.

Aufruf von Hand:
    python rueckweg.py stand
    python rueckweg.py zeugnis prod.video.stueck
    python rueckweg.py lehrsaetze
    python rueckweg.py halde
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import vektor as _vektor
except ImportError:
    _vektor = None

PFADDATEI = Path(__file__).resolve().parent.parent / "gehirn.json"

#: Ab so vielen gleichartigen Urteilen darf ein Lehrsatz vorgeschlagen werden.
SCHWELLE = 3

#: Woher eine Erfahrung stammt. Nur ECHT zaehlt ins Zeugnis.
ECHT = "echt"          # Echtbetrieb - ein Stueck, das wirklich entstanden ist
TROCKEN = "trocken"    # Trockenlauf mit Platzhaltern
PRUEFUNG = "pruefung"  # eine durchgefallene Pruefung des Pruefstands
TECHNIK = "technik"    # ein Prozessfehler der Maschinerie, kein Urteil ueber ein Stueck

#: Die Klassen der Prozessfehler - aus der AIEOS-Fehlertaxonomie die vier,
#: die im Universe vorkommen. Klassifiziert, nicht beschrieben: eine Klasse
#: laesst sich zaehlen und haeufen, eine Beschreibung nur lesen.
TECHNIK_KLASSEN = ("dienst-nicht-erreichbar", "antwort-nicht-lesbar",
                   "modell-nichts-geliefert", "zeitgrenze")

#: So viele Erfahrungen bekommt ein Agent vor dem naechsten Auftrag mitgegeben.
VORWISSEN_ANZAHL = 5

#: Wo die Anweisung eines Moduls steht. Der Inhaltsabdruck dieser Datei kommt
#: als "anweisung" in jede Erfahrung - damit spaeter feststeht, mit welcher
#: Fassung der Anweisung ein Stueck entstanden ist. Bis zum 11.09.2026 wusste
#: das keine Erfahrung, und wirkung_pruefen konnte eine Aenderung der
#: Anweisung nicht von der Wirkung eines Lehrsatzes unterscheiden.
UNIVERSE = Path(__file__).resolve().parent.parent
ANWEISUNGSDATEIEN = {
    "prod.praesentation": "gestalter/folien.py",
    "prod.app": "implementierer/werkbank.py",
    "prod.marketing": "marketing/kampagne.py",
    "prod.video": "video_agent/drehbuch.py",
    "prod.musik": "musik_agent/stil.py",
    "prod.lernen": "lern_agent/curriculum.py",
    "prod.pdf": "setzer/inhalt.py",
    "bewerbung": "bewerbungs_agent/modell.py",
    "post": "email_manager/agent.py",
    "wohnung": "wohnungs_agent/auskunft.py",
}


def anweisung_fassung(modul: str) -> str:
    """Die Fassung der Anweisung eines Moduls: zwoelf Zeichen aus dem
    Inhaltsabdruck der Datei, in der sie steht. Leer, wenn das Modul keine
    Anweisung hat (Strassen ohne Modell) oder die Datei fehlt."""
    rel = ANWEISUNGSDATEIEN.get(modul) or next(
        (v for k, v in ANWEISUNGSDATEIEN.items() if modul.startswith(k + ".")), "")
    if not rel:
        return ""
    try:
        return hashlib.md5((UNIVERSE / rel).read_bytes()).hexdigest()[:12]
    except OSError:
        return ""


# ------------------------------------------------------------------ Pfade

def _pfade(konfiguration: dict | None = None) -> dict:
    pfade = {}
    if PFADDATEI.exists():
        try:
            pfade.update(json.loads(PFADDATEI.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            pass
    pfade.update((konfiguration or {}).get("gehirn", {}))
    pfade.setdefault("vault", r"C:\AI_Projekte\Neustart\vault")
    pfade.setdefault("vektor", r"C:\AI_Projekte\Neustart\mein_ki_gehirn\chroma")
    return pfade


def _ordner(was: str, konfiguration: dict | None = None) -> Path:
    ziel = Path(_pfade(konfiguration)["vault"]) / was
    ziel.mkdir(parents=True, exist_ok=True)
    return ziel


def _regal_fuellen(regal: str, text: str, marken: dict,
                   quelle: str, konfiguration: dict | None) -> None:
    """Legt denselben Inhalt in die Vektordatenbank. Faellt sie aus, ist das
    kein Fehler - das Markdown steht bereits."""
    if _vektor is None:
        return
    try:
        _vektor.aufnehmen(regal, _pfade(konfiguration)["vektor"], text, marken, quelle)
    except Exception:
        pass


# ------------------------------------------------------------------ Markdown

def _kopf_schreiben(felder: dict) -> str:
    zeilen = ["---"]
    for schluessel, wert in felder.items():
        if isinstance(wert, (list, tuple)):
            zeilen.append("%s: [%s]" % (schluessel, ", ".join(str(w) for w in wert)))
        elif isinstance(wert, str) and (":" in wert or wert == ""):
            zeilen.append('%s: "%s"' % (schluessel, wert.replace('"', "'")))
        else:
            zeilen.append("%s: %s" % (schluessel, wert))
    zeilen.append("---")
    return "\n".join(zeilen)


def _kopf_lesen(inhalt: str) -> dict:
    """Liest die Kopfdaten. Bewusst einfach - eine Ebene, keine Verschachtelung."""
    treffer = re.match(r"^---\n(.*?)\n---\n", inhalt, re.S)
    if not treffer:
        return {}
    felder: dict = {}
    for zeile in treffer.group(1).splitlines():
        if ":" not in zeile:
            continue
        schluessel, wert = zeile.split(":", 1)
        wert = wert.strip()
        if wert.startswith("[") and wert.endswith("]"):
            felder[schluessel.strip()] = [
                t.strip() for t in wert[1:-1].split(",") if t.strip()]
        else:
            felder[schluessel.strip()] = wert.strip('"').strip("'")
    return felder


def _zahl(wert, ersatz=0.0) -> float:
    try:
        return float(str(wert).replace(",", "."))
    except (TypeError, ValueError):
        return ersatz


def _saeubern(text: str) -> str:
    for alt, neu in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        text = text.lower().replace(alt, neu)
    return re.sub(r"[^a-z0-9.]+", "-", text).strip("-")[:60] or "ohne-namen"


# ================================================================== Stufe 1

def erfahrung_ablegen(auftrag: str, modul: str, was_versucht: str,
                      befund: str = "", urteil: str = "offen", grund: str = "",
                      gueteklasse: str = "", durchlaeufe: int = 0,
                      kosten: float = 0.0, dauer_minuten: float = 0.0,
                      art: str = ECHT, deckung: str = "", deckung_satz: str = "",
                      anweisung: str = "",
                      konfiguration: dict | None = None) -> Path:
    """Eine Erfahrung je abgeschlossenem Auftrag.

    Nicht das Ergebnis wird abgelegt, sondern was daran gut oder schlecht war.

    Jede Erfahrung traegt ausserdem, womit das Stueck entstanden ist: die
    Fassung der Anweisung (anweisung, sonst aus ANWEISUNGSDATEIEN gerechnet)
    und die Lehrsaetze, die dabei aktiv waren. Erst damit kann wirkung_pruefen
    sagen, ob sich eine Zahl wegen eines Lehrsatzes bewegt hat - oder weil
    jemand zwischendurch die Anweisung umgeschrieben hat.

    urteil   'ja' oder 'nein' - bei 'nein' ist grund Pflicht, sonst lernt
             niemand etwas: ein reines Nein sagt nur, dass etwas falsch war.
    deckung  worauf das Stueck stand: 'gut', 'duenn' oder 'leer'. Ohne das
             laesst sich spaeter nicht unterscheiden, ob ein Nein an der
             Strasse lag oder daran, dass zum Thema nichts da war.
    """
    if urteil == "nein" and not grund.strip():
        raise ValueError("Ein Nein ohne Grund lehrt nichts - grund fehlt.")

    kopf = {
        "typ": "erfahrung",
        "art": art,
        "auftrag": auftrag,
        "modul": modul,
        "gueteklasse": gueteklasse or "-",
        "datum": date.today().isoformat(),
        "urteil": urteil,
        "grund": grund,
        "durchlaeufe": durchlaeufe,
        "kosten": round(kosten, 2),
        "dauer_minuten": round(dauer_minuten, 1),
        "deckung": deckung or "-",
        "anweisung": anweisung or anweisung_fassung(modul) or "-",
        "lehrsaetze": [s["kennung"] for s in lehrsaetze(modul, "aktiv", konfiguration)],
        "aussenwirkung": "",
    }
    koerper = "\n".join([
        "",
        "## Was versucht wurde",
        was_versucht.strip() or "-",
        "",
        "## Befund des Qualitaetsmanagers",
        befund.strip() or "-",
        "",
        "## Urteil",
        ("%s%s" % (urteil, " - " + grund if grund else "")),
        "",
        "## Worauf das Stueck stand",
        (deckung_satz.strip() or
         ("Deckung: " + deckung if deckung else
          "Nicht gemessen - dieser Auftrag lief ohne Stoffbeschaffer.")),
        "",
        "## Aussenwirkung",
        "noch offen",
        "",
    ])
    unterordner = "erfahrungen" if art == ECHT else "erfahrungen/_" + art
    ziel = _ordner(unterordner, konfiguration) / (
        "%s_%s_%s.md" % (date.today().isoformat(), _saeubern(modul), _saeubern(auftrag)))
    ziel.write_text(_kopf_schreiben(kopf) + "\n" + koerper, encoding="utf-8", newline="")

    _regal_fuellen("erfahrungen",
                   "%s\n%s" % (was_versucht, grund),
                   {"quelle": ziel.name, "auftrag": auftrag, "modul": modul,
                    "urteil": urteil, "gueteklasse": gueteklasse or "-",
                    "art": art, "datum": kopf["datum"],
                    "deckung": deckung or "-"},
                   ziel.name, konfiguration)
    return ziel


def technik_vermerken(auftrag: str, modul: str, klasse: str, einzelheit: str = "",
                      konfiguration: dict | None = None) -> Path | None:
    """Ein Prozessfehler als Erfahrung, art=TECHNIK.

    Bis zum 11.09.2026 stand "Das Modell hat nichts Brauchbares geliefert"
    als Satz in einem Bericht und lehrte niemanden etwas. Jetzt ist es eine
    Erfahrung mit Klasse: der Ausbilder sieht, welche Strasse wie oft woran
    haengt. Nie eine Ausnahme nach aussen - der Vermerk ist Beiwerk.
    """
    if klasse not in TECHNIK_KLASSEN:
        klasse = "sonstiges"
    grund = klasse + (": " + einzelheit.strip()[:300] if einzelheit.strip() else "")
    try:
        return erfahrung_ablegen(auftrag, modul, "Modellaufruf", urteil="nein",
                                 grund=grund, art=TECHNIK, konfiguration=konfiguration)
    except Exception:
        return None


def technik_haufen(modul: str | None = None, anzahl: int = 500,
                   konfiguration: dict | None = None) -> list[dict]:
    """Prozessfehler je Modul und Klasse, haeufigste zuerst - fuer den Ausbilder."""
    zaehler: dict[tuple[str, str], int] = {}
    for e in erfahrungen(modul, anzahl, konfiguration, art=TECHNIK):
        klasse = str(e.get("grund", "")).split(":", 1)[0].strip() or "sonstiges"
        schluessel = (str(e.get("modul", "")), klasse)
        zaehler[schluessel] = zaehler.get(schluessel, 0) + 1
    return [{"modul": m, "klasse": k, "anzahl": n}
            for (m, k), n in sorted(zaehler.items(), key=lambda p: -p[1])]


def aussenwirkung_nachtragen(auftrag: str, text: str,
                             konfiguration: dict | None = None) -> Path | None:
    """Was der Social-Media-Agent nach ein paar Tagen zurueckmeldet."""
    for datei in sorted(_ordner("erfahrungen", konfiguration).glob("*_%s.md" % _saeubern(auftrag))):
        inhalt = datei.read_text(encoding="utf-8")
        inhalt = re.sub(r"^aussenwirkung: .*$", 'aussenwirkung: "%s"' % text.replace('"', "'"),
                        inhalt, count=1, flags=re.MULTILINE)
        inhalt = inhalt.replace("## Aussenwirkung\nnoch offen",
                                "## Aussenwirkung\n%s (%s)" % (text, date.today().isoformat()))
        datei.write_text(inhalt, encoding="utf-8", newline="")
        return datei
    return None


def erfahrungen(modul: str | None = None, anzahl: int = 50,
                konfiguration: dict | None = None,
                art: str | None = ECHT) -> list[dict]:
    """Die juengsten Erfahrungen, neueste zuerst.

    art=ECHT (Vorgabe) liefert nur, was im Echtbetrieb entstanden ist.
    Trockenlaeufe und Pruefungen liegen in Unterordnern daneben und zaehlen
    nicht ins Zeugnis - sonst behauptet eine Zahl etwas ueber die
    Produktion, was in Wahrheit aus einer Probe stammt.
    art=None liefert alles, gleich woher.
    """
    ordner = _ordner("erfahrungen", konfiguration)
    kandidaten: list[tuple] = [(d, ECHT) for d in ordner.glob("*.md")]
    for unter in ordner.glob("_*"):
        if unter.is_dir():
            # Der Ordnername sagt, woher es stammt: _trocken, _pruefung.
            kandidaten += [(d, unter.name.lstrip("_")) for d in unter.glob("*.md")]
    kandidaten.sort(key=lambda paar: paar[0].name, reverse=True)

    aus: list[dict] = []
    for datei, aus_ordner in kandidaten:
        kopf = _kopf_lesen(datei.read_text(encoding="utf-8"))
        if not kopf:
            continue
        kopf["art"] = kopf.get("art") or aus_ordner
        if modul and kopf.get("modul") != modul:
            continue
        if art is not None and kopf["art"] != art:
            continue
        kopf["datei"] = datei.name
        aus.append(kopf)
        if len(aus) >= anzahl:
            break
    return aus


# ================================================================== Stufe 2

def _naechste_kennung(ordner: Path) -> str:
    hoechste = 0
    for datei in ordner.glob("L*.md"):
        treffer = re.match(r"L(\d{4})", datei.name)
        if treffer:
            hoechste = max(hoechste, int(treffer.group(1)))
    return "L%04d" % (hoechste + 1)


def lehrsatz_vorschlagen(satz: str, gilt_fuer: str, belege: list[str],
                         begruendung: str = "", schwelle: int = SCHWELLE,
                         konfiguration: dict | None = None) -> Path:
    """Der Ausbilder schlaegt vor - erst ab genug Belegen.

    Eine einzelne Erfahrung darf nie zur Dauerregel werden. Sonst bekommt
    man einen Agenten voller Aberglauben: einmal ein Nein fuer eine
    Kleinigkeit kassiert und die Sache fortan grundsaetzlich gemieden.

    gilt_fuer  eine Modul-Kennung ('prod.video.stueck') oder eine Gruppe
               ('produktion') - ein Lehrsatz ueber Aufhaenger gilt fuer
               beide Gueteklassen, einer ueber Bildprompts nur fuer eine.
    """
    if len(belege) < schwelle:
        raise ValueError(
            "%d Belege sind zu wenig - erst ab %d darf ein Lehrsatz vorgeschlagen werden."
            % (len(belege), schwelle))

    ordner = _ordner("lehrsaetze", konfiguration)
    kennung = _naechste_kennung(ordner)
    kopf = {
        "typ": "lehrsatz",
        "kennung": kennung,
        "gilt_fuer": gilt_fuer,
        "stand": "vorschlag",
        "belege": belege,
        "vorgeschlagen": date.today().isoformat(),
        "bestaetigt_von": "",
        "bestaetigt_am": "",
        "zurueckgezogen_am": "",
        "wirkung": "",
    }
    koerper = "\n".join([
        "", "## Satz", satz.strip(), "",
        "## Warum", begruendung.strip() or "-", "",
        "## Belege", "\n".join("- %s" % b for b in belege), "",
    ])
    ziel = ordner / ("%s_%s.md" % (kennung, _saeubern(gilt_fuer)))
    ziel.write_text(_kopf_schreiben(kopf) + "\n" + koerper, encoding="utf-8", newline="")
    return ziel


def lehrsatz_entscheiden(kennung: str, ja: bool, von: str = "daniel",
                         grund: str = "", konfiguration: dict | None = None) -> Path | None:
    """Daniels Ja oder Nein zu einem Vorschlag. Ein Nein wandert auf die Halde."""
    for datei in _ordner("lehrsaetze", konfiguration).glob("%s_*.md" % kennung):
        inhalt = datei.read_text(encoding="utf-8")
        neuer_stand = "aktiv" if ja else "abgelehnt"
        inhalt = re.sub(r"^stand: .*$", "stand: %s" % neuer_stand,
                        inhalt, count=1, flags=re.MULTILINE)
        inhalt = re.sub(r"^bestaetigt_von: .*$", "bestaetigt_von: %s" % (von if ja else ""),
                        inhalt, count=1, flags=re.MULTILINE)
        inhalt = re.sub(r"^bestaetigt_am: .*$", "bestaetigt_am: %s" % (date.today().isoformat() if ja else ""),
                        inhalt, count=1, flags=re.MULTILINE)
        datei.write_text(inhalt, encoding="utf-8", newline="")
        kopf = _kopf_lesen(inhalt)
        if ja:
            _regal_fuellen("lehrsaetze", _abschnitt(inhalt, "Satz"),
                           {"quelle": datei.name, "kennung": kennung,
                            "gilt_fuer": kopf.get("gilt_fuer", ""), "stand": "aktiv"},
                           datei.name, konfiguration)
        else:
            verwerfen("lehrsatz", kennung,
                      grund or "von Daniel abgelehnt",
                      herkunft=datei.name, konfiguration=konfiguration)
        return datei
    return None


def lehrsatz_zurueckziehen(kennung: str, grund: str,
                           konfiguration: dict | None = None) -> Path | None:
    """Ein Lehrsatz, nach dem sich keine Zahl bewegt, wird zurueckgezogen.

    Nicht geloescht: er bleibt lesbar und landet zusaetzlich auf der Halde,
    damit spaeter niemand dieselbe Regel noch einmal vorschlaegt.
    """
    for datei in _ordner("lehrsaetze", konfiguration).glob("%s_*.md" % kennung):
        inhalt = datei.read_text(encoding="utf-8")
        inhalt = re.sub(r"^stand: .*$", "stand: zurueckgezogen",
                        inhalt, count=1, flags=re.MULTILINE)
        inhalt = re.sub(r"^zurueckgezogen_am: .*$",
                        "zurueckgezogen_am: %s" % date.today().isoformat(),
                        inhalt, count=1, flags=re.MULTILINE)
        inhalt = re.sub(r"^wirkung: .*$", 'wirkung: "%s"' % grund.replace('"', "'"),
                        inhalt, count=1, flags=re.MULTILINE)
        datei.write_text(inhalt, encoding="utf-8", newline="")
        verwerfen("lehrsatz", kennung, grund, herkunft=datei.name,
                  konfiguration=konfiguration)
        return datei
    return None


def lehrsaetze(gilt_fuer: str | None = None, stand: str | None = "aktiv",
               konfiguration: dict | None = None) -> list[dict]:
    """Lehrsaetze, gefiltert nach Geltung und Stand.

    gilt_fuer 'prod.video.stueck' liefert auch die Saetze, die an der Gruppe
    'produktion' haengen - eine Regel ueber Aufhaenger gilt fuer beide
    Gueteklassen.
    """
    aus: list[dict] = []
    for datei in sorted(_ordner("lehrsaetze", konfiguration).glob("L*.md")):
        inhalt = datei.read_text(encoding="utf-8")
        kopf = _kopf_lesen(inhalt)
        if not kopf:
            continue
        if stand and kopf.get("stand") != stand:
            continue
        if gilt_fuer and not _greift(kopf.get("gilt_fuer", ""), gilt_fuer):
            continue
        kopf["satz"] = _abschnitt(inhalt, "Satz")
        kopf["datei"] = datei.name
        aus.append(kopf)
    return aus


def _greift(geltung: str, modul: str) -> bool:
    """'produktion' greift auch bei 'prod.video.stueck'."""
    if not geltung or geltung == modul:
        return True
    if geltung == "produktion" and modul.startswith("prod."):
        return True
    return modul.startswith(geltung + ".")


def _abschnitt(inhalt: str, ueberschrift: str) -> str:
    treffer = re.search(r"^## %s\n(.*?)(?=\n## |\Z)" % re.escape(ueberschrift),
                        inhalt, re.S | re.M)
    return treffer.group(1).strip() if treffer else ""


def reif_fuer_lehrsatz(modul: str, schwelle: int = SCHWELLE,
                       genau: bool = True,
                       konfiguration: dict | None = None,
                       art: str = ECHT) -> list[dict]:
    """Welche Gruende sich oft genug wiederholt haben.

    Der Ausbilder schaut hier nach, bevor er etwas vorschlaegt.

    Zwei Gruende gehoeren in denselben Haufen, wenn sie dieselbe Sache
    meinen - nicht, wenn sie dieselben Woerter benutzen. "Ton zu leise
    gegenueber der Musik" und "Die Musik uebertoent die Stimme" ist
    derselbe Mangel, teilt aber nur ein einziges Wort.

    genau=True  vergleicht die Bedeutung ueber die Vektorschicht. Das
                kostet eine Einbettung je Grund - bei 500 Gruenden rund
                0,0002 EUR, also praktisch nichts.
    genau=False vergleicht nur die Woerter. Kostet nichts, uebersieht aber
                Umschreibungen. Wird auch dann genommen, wenn kein
                Schluessel da ist oder die Vektorschicht schweigt.
    """
    neins = [e for e in erfahrungen(modul, anzahl=500, konfiguration=konfiguration, art=art)
             if e.get("urteil") == "nein" and e.get("grund")]
    if not neins:
        return []

    naehe = _naehe_matrix([e["grund"] for e in neins]) if genau else None
    haufen = _haufen_bilden(neins, naehe)

    reif = []
    for gruppe in haufen:
        if len(gruppe) < schwelle:
            continue
        gemeinsam: set[str] | None = None
        for e in gruppe:
            w = _inhaltsworte(e["grund"])
            gemeinsam = w if gemeinsam is None else (gemeinsam & w)
        if not gemeinsam:
            gemeinsam = _inhaltsworte(min((e["grund"] for e in gruppe), key=len))
        reif.append({
            "kern": " ".join(sorted(gemeinsam)[:5]),
            "anzahl": len(gruppe),
            "gruende": [e["grund"] for e in gruppe],
            "belege": [e["auftrag"] for e in gruppe],
            "modul": modul,
        })
    reif.sort(key=lambda h: -h["anzahl"])
    return reif


def _haufen_bilden(neins: list[dict], naehe) -> list[list[dict]]:
    """Einfachbindung: wer zu irgendeinem im Haufen passt, gehoert dazu."""
    haufen: list[list[int]] = []
    worte = [_inhaltsworte(e["grund"]) for e in neins]
    for i in range(len(neins)):
        ziel = None
        for h in haufen:
            if any(_gehoert_zusammen(i, j, worte, naehe) for j in h):
                ziel = h
                break
        if ziel is None:
            haufen.append([i])
        else:
            ziel.append(i)
    return [[neins[i] for i in h] for h in haufen]


def _gehoert_zusammen(i: int, j: int, worte: list[set[str]], naehe) -> bool:
    if naehe is not None:
        return naehe[i][j] >= NAEHE_AB
    return _aehnlich(worte[i], worte[j])


def _naehe_matrix(texte: list[str]):
    """Kosinus-Naehe aller Gruende untereinander. None, wenn nicht moeglich."""
    if _vektor is None or len(texte) < 2:
        return None
    try:
        vektoren = _vektor.einbetten(texte)
    except Exception:
        return None
    if not vektoren or len(vektoren) != len(texte):
        return None

    def punkt(a, b):
        return sum(x * y for x, y in zip(a, b))

    laengen = [max(punkt(v, v) ** 0.5, 1e-9) for v in vektoren]
    return [[punkt(vektoren[i], vektoren[j]) / (laengen[i] * laengen[j])
             for j in range(len(texte))] for i in range(len(texte))]


#: Ab dieser Kosinus-Naehe gelten zwei Gruende als dieselbe Sache.
#: Ueber 0,60 ist sehr aehnlich, 0,45-0,60 brauchbar, darunter Zufall.
NAEHE_AB = 0.55

#: Ab so viel Ueberschneidung gelten zwei Gruende als dieselbe Sache.
AEHNLICH_AB = 0.34

_FUELLWORTE = {
    "der", "die", "das", "und", "ist", "war", "zu", "ein", "eine", "einen",
    "den", "dem", "des", "nicht", "sich", "mit", "auf", "fuer", "fur",
    "hat", "sind", "aber", "noch", "sehr", "wie", "als", "auch", "schon",
    "wieder", "viel", "mehr", "ganz", "immer", "beim", "vom", "zum", "zur",
    "man", "kein", "keine", "wurde", "wurden", "worden", "haben", "hatte",
    "etwas", "alles", "nochmal", "diesmal", "leider", "einfach",
}


def _inhaltsworte(text: str) -> set[str]:
    """Was von einem Grund uebrig bleibt, wenn man die Fuellworte streicht."""
    worte = set()
    for wort in re.findall(r"[A-Za-z\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df]{4,}", text.lower()):
        wort = _entumlauten(wort)
        if wort in _FUELLWORTE:
            continue
        worte.add(_stamm(wort))
    return worte


def _entumlauten(wort: str) -> str:
    for alt, neu in (("\u00e4", "ae"), ("\u00f6", "oe"), ("\u00fc", "ue"), ("\u00df", "ss")):
        wort = wort.replace(alt, neu)
    return wort


def _stamm(wort: str) -> str:
    """Grob genug, dass 'hektisch' und 'hektischer' zusammenfallen."""
    for endung in ("ischer", "ische", "isch", "ungen", "ung", "eren", "ern",
                   "est", "end", "ere", "er", "en", "es", "em", "e", "s"):
        if len(wort) - len(endung) >= 4 and wort.endswith(endung):
            return wort[: -len(endung)]
    return wort


def _aehnlich(a: set[str], b: set[str]) -> bool:
    """Ueberschneidung, gemessen am kleineren der beiden Gruende."""
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= AEHNLICH_AB


# ================================================================== Vorwissen

def vorwissen(modul: str, anzahl: int = VORWISSEN_ANZAHL,
              konfiguration: dict | None = None) -> str:
    """Was einem Agenten vor dem naechsten Auftrag in die Anweisung gelegt wird.

    Das ist die Stelle, an der das 2nd Brain zum ersten Mal etwas *tut*,
    statt nur zu lagern. Kein Training, kein Modell - nur Gedaechtnis.
    """
    saetze = lehrsaetze(modul, "aktiv", konfiguration)
    letzte = erfahrungen(modul, anzahl, konfiguration)
    if not saetze and not letzte:
        return ""

    teile = ["===== was du beim letzten Mal gelernt hast ====="]
    if saetze:
        teile.append("\nGeltende Lehrsaetze - daran haeltst du dich:")
        for s in saetze:
            teile.append("- %s  [%s, gilt fuer %s]" % (s["satz"], s["kennung"], s["gilt_fuer"]))
    if letzte:
        teile.append("\nDie letzten Durchlaeufe:")
        for e in letzte:
            zeile = "- %s  Auftrag %s: %s" % (e.get("datum", ""), e.get("auftrag", ""),
                                              e.get("urteil", ""))
            if e.get("grund"):
                zeile += " - " + e["grund"]
            if _zahl(e.get("durchlaeufe")) > 1:
                zeile += " (%s Durchlaeufe)" % e["durchlaeufe"]
            if e.get("aussenwirkung"):
                zeile += " | draussen: " + e["aussenwirkung"]
            teile.append(zeile)
    return "\n".join(teile)


# ================================================================== Stufe 3

def zeugnis(modul: str, seit: str | None = None,
            konfiguration: dict | None = None) -> dict:
    """Die vier Zahlen je Produktionsstrasse.

    seit  ISO-Datum; ohne Angabe zaehlt alles.

    'Anteil deiner Neins' ist die wichtigste Zahl: Das Ziel ist erreicht,
    wenn sie ueber Monate faellt, waehrend die Menge steigt.
    """
    liste = [e for e in erfahrungen(modul, anzahl=5000, konfiguration=konfiguration)
             if not seit or e.get("datum", "") >= seit]
    if not liste:
        return {"modul": modul, "stuecke": 0, "durchlaeufe_schnitt": 0.0,
                "anteil_neins": 0.0, "kosten_je_stueck": 0.0,
                "minuten_je_stueck": 0.0, "seit": seit or "Anfang"}
    neins = sum(1 for e in liste if e.get("urteil") == "nein")
    return {
        "modul": modul,
        "stuecke": len(liste),
        "durchlaeufe_schnitt": round(
            sum(_zahl(e.get("durchlaeufe"), 1) for e in liste) / len(liste), 2),
        "anteil_neins": round(neins / len(liste), 3),
        "kosten_je_stueck": round(
            sum(_zahl(e.get("kosten")) for e in liste) / len(liste), 2),
        "minuten_je_stueck": round(
            sum(_zahl(e.get("dauer_minuten")) for e in liste) / len(liste), 1),
        "seit": seit or "Anfang",
    }


def wirkung_pruefen(kennung: str, konfiguration: dict | None = None) -> dict:
    """Hat sich seit diesem Lehrsatz eine Zahl bewegt?

    Vergleicht das Zeugnis vor und nach dem Tag der Bestaetigung. Bewegt
    sich nichts, gehoert der Satz zurueckgezogen - nicht diskutiert.
    """
    for datei in _ordner("lehrsaetze", konfiguration).glob("%s_*.md" % kennung):
        kopf = _kopf_lesen(datei.read_text(encoding="utf-8"))
        ab = kopf.get("bestaetigt_am") or ""
        modul = kopf.get("gilt_fuer", "")
        alle = erfahrungen(None, 5000, konfiguration)
        vorher = [e for e in alle if _greift(modul, e.get("modul", "")) and e.get("datum", "") < ab]
        nachher = [e for e in alle if _greift(modul, e.get("modul", "")) and e.get("datum", "") >= ab]

        def anteil(liste):
            return round(sum(1 for e in liste if e.get("urteil") == "nein") / len(liste), 3) \
                if liste else None

        v, n = anteil(vorher), anteil(nachher)

        def fassungen(liste):
            return sorted({str(e.get("anweisung") or "") for e in liste} - {"", "-"})

        fv, fn = fassungen(vorher), fassungen(nachher)
        return {
            "kennung": kennung, "gilt_fuer": modul, "ab": ab,
            "anteil_neins_vorher": v, "anteil_neins_nachher": n,
            "stuecke_vorher": len(vorher), "stuecke_nachher": len(nachher),
            "bewegt": (v is not None and n is not None and abs(v - n) >= 0.05),
            # Mehr als eine Fassung seit der Bestaetigung: dann hat sich nicht
            # nur der Lehrsatz geaendert, sondern auch die Anweisung selbst -
            # die Bewegung laesst sich dem Lehrsatz nicht allein zuschreiben.
            "fassungen_vorher": fv, "fassungen_nachher": fn,
            "anweisung_geaendert": len(fn) > 1 or bool(fv and fn and fv != fn),
        }
    return {}


# ================================================================== Halde

def verwerfen(was: str, kennung: str, grund: str, herkunft: str = "",
              wiederaufnahme: str = "", konfiguration: dict | None = None) -> Path:
    """Alles, was verworfen wird oder brachliegt, kommt hierher.

    Damit nichts vergessen wird: ein Auftrag, der nach drei Anlaeufen
    liegen bleibt; ein Lehrsatz ohne Wirkung; ein Vorhaben, das nicht
    weiterverfolgt wird. Mit Grund, Datum und - falls bekannt - der
    Bedingung, unter der man es wieder anfassen wuerde.
    """
    ordner = _ordner("halde", konfiguration)
    kopf = {
        "typ": "verworfen",
        "was": was,
        "kennung": kennung,
        "datum": date.today().isoformat(),
        "herkunft": herkunft,
        "wiederaufnahme": wiederaufnahme,
    }
    koerper = "\n\n## Grund\n%s\n" % (grund.strip() or "-")
    if wiederaufnahme:
        koerper += "\n## Wieder anfassen, wenn\n%s\n" % wiederaufnahme.strip()
    ziel = ordner / ("%s_%s_%s.md" % (date.today().isoformat(), _saeubern(was), _saeubern(kennung)))
    ziel.write_text(_kopf_schreiben(kopf) + koerper, encoding="utf-8", newline="")
    return ziel


def halde(was: str | None = None, konfiguration: dict | None = None) -> list[dict]:
    """Was liegt auf der Halde - neueste zuerst."""
    aus = []
    for datei in sorted(_ordner("halde", konfiguration).glob("*.md"), reverse=True):
        inhalt = datei.read_text(encoding="utf-8")
        kopf = _kopf_lesen(inhalt)
        if not kopf or (was and kopf.get("was") != was):
            continue
        kopf["grund"] = _abschnitt(inhalt, "Grund")
        kopf["datei"] = datei.name
        aus.append(kopf)
    return aus


# ================================================================== Aufruf

def stand(konfiguration: dict | None = None) -> dict:
    return {
        "erfahrungen": len(list(_ordner("erfahrungen", konfiguration).glob("*.md"))),
        "technik": len(list(_ordner("erfahrungen/_technik", konfiguration).glob("*.md"))),
        "lehrsaetze_aktiv": len(lehrsaetze(None, "aktiv", konfiguration)),
        "lehrsaetze_vorschlag": len(lehrsaetze(None, "vorschlag", konfiguration)),
        "lehrsaetze_zurueckgezogen": len(lehrsaetze(None, "zurueckgezogen", konfiguration)),
        "halde": len(list(_ordner("halde", konfiguration).glob("*.md"))),
    }


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    if befehl == "stand":
        for name, zahl in stand().items():
            print("%-26s %d" % (name, zahl))
    elif befehl == "zeugnis":
        if len(argumente) < 2:
            print("Aufruf: rueckweg.py zeugnis <modul> [seit-datum]")
            return 2
        z = zeugnis(argumente[1], argumente[2] if len(argumente) > 2 else None)
        print("Zeugnis %s (seit %s)" % (z["modul"], z["seit"]))
        print("  Stuecke insgesamt        %d" % z["stuecke"])
        print("  Durchlaeufe bis Abnahme  %.2f" % z["durchlaeufe_schnitt"])
        print("  Anteil deiner Neins      %.1f %%" % (z["anteil_neins"] * 100))
        print("  Kosten je Stueck         %.2f EUR" % z["kosten_je_stueck"])
        print("  Minuten je Stueck        %.1f" % z["minuten_je_stueck"])
    elif befehl == "lehrsaetze":
        for s in lehrsaetze(None, argumente[1] if len(argumente) > 1 else None):
            print("%s  [%s]  %s  -> %s" % (s["kennung"], s.get("stand"),
                                           s.get("gilt_fuer"), s.get("satz", "")[:80]))
    elif befehl == "halde":
        for h in halde():
            print("%s  %s %s  %s" % (h.get("datum"), h.get("was"),
                                     h.get("kennung"), h.get("grund", "")[:70]))
    elif befehl == "vorwissen":
        if len(argumente) < 2:
            print("Aufruf: rueckweg.py vorwissen <modul>")
            return 2
        print(vorwissen(argumente[1]) or "(noch nichts gelernt)")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
