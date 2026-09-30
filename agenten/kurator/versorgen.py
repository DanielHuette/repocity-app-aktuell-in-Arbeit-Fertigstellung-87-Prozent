"""Der Kurator gibt heraus - die Rueckseite des Einpflegens.

Er ist die einzige Stelle, die in die Regale schreibt. Damit ist er auch die
einzige, die weiss, was drinsteht - und deshalb gibt er den Stoff heraus,
statt dass jede Strasse sich ihren eigenen Weg in die Datenbank baut.

Vier eigene Quellen, kostenlos und sofort da:

    2nd Brain      was zum Thema eingelagert ist - Text, Atome, Bilder
    Warenausgang   fertige Stuecke anderer Strassen als Material
    Brand Kit      Farben, Schrift, Bildsprache, Verbotsliste
    der Auftrag    was du getippt und angehaengt hast

Und das Wichtigste: **er misst die Deckung**. Findet er wenig, sagt er das -
statt dass ein Agent den Rest erfindet und es erst am fertigen Stueck auffaellt.
Aus der Messung folgt der Vorschlag: bauen, Netz dazunehmen, oder nachfragen.

    python versorgen.py probe "Thema"           was zu diesem Thema da ist
    python versorgen.py probe "Thema" --modul prod.video
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
WURZEL = UNIVERSE.parent
KERN = UNIVERSE / "kern"
for _p in (str(KERN), str(HIER)):
    if _p not in sys.path:
        sys.path.append(_p)

def _kern_gehirn():
    """Die Tuer aus dem Kern laden, nicht die kleine Hilfsdatei nebenan.

    Im Kuratorordner liegt eine eigene gehirn.py fuer seinen Einpflegeweg.
    Ein normaler Import wuerde die erwischen - und die kennt die Bildersuche
    nicht. Genau daran sind die Bilder beim ersten Versuch verschwunden.
    """
    import importlib.util
    fertig = sys.modules.get("kern_gehirn")
    if fertig is not None:
        return fertig
    beschreibung = importlib.util.spec_from_file_location(
        "kern_gehirn", KERN / "gehirn.py")
    modul = importlib.util.module_from_spec(beschreibung)
    sys.modules["kern_gehirn"] = modul
    beschreibung.loader.exec_module(modul)
    return modul


gehirn = _kern_gehirn()  # noqa: E402

try:
    import warenausgang
except ImportError:  # der Warenausgang darf fehlen, dann faellt diese Quelle weg
    warenausgang = None

KITS = UNIVERSE / "marke" / "kits.json"
MARKE = UNIVERSE / "marke" / "STAND-MARKE.md"

# Ab wann eine Nähe brauchbar ist. Aus der Wissensdatenbank-Beschreibung in
# START.md: ueber 0,60 sehr gut, 0,45-0,60 brauchbar, unter 0,25 Zufall.
NAEHE_BRAUCHBAR = 0.45
NAEHE_GUT = 0.60

# Wie viele brauchbare Funde eine Produktion traegt. Unter drei ist es ein
# Anfang, unter einem ist es nichts.
GENUG = 5
DUENN = 3


@dataclass
class Deckung:
    """Wie gut die eigenen Quellen dieses Thema abdecken."""
    stufe: str                      # "gut", "duenn", "leer"
    funde: int = 0
    brauchbare: int = 0
    beste_naehe: float = 0.0
    bilder: int = 0
    stuecke: int = 0
    satz: str = ""                  # ein Satz im Klartext, fuer Meldung und Zettel

    @property
    def traegt(self) -> bool:
        return self.stufe == "gut"


@dataclass
class Stoff:
    """Was eine Strasse fuer einen Auftrag bekommt."""
    frage: str
    modul: str
    kontext: str = ""               # fertiger Text fuer den Agenten
    funde: list = field(default_factory=list)
    bilder: list = field(default_factory=list)
    stuecke: list = field(default_factory=list)
    kit: dict = field(default_factory=dict)
    verbotsliste: list = field(default_factory=list)
    deckung: Deckung = field(default_factory=lambda: Deckung("leer"))
    quellen: list = field(default_factory=list)
    empfehlung: str = "bauen"       # "bauen" | "netz" | "nachfragen"

    def als_zettel(self) -> dict:
        """Was davon in den Beipackzettel und die Erfahrung gehoert."""
        return {
            "frage": self.frage,
            "deckung": self.deckung.stufe,
            "funde": self.deckung.funde,
            "brauchbare": self.deckung.brauchbare,
            "bilder": self.deckung.bilder,
            "stuecke": self.deckung.stuecke,
            "quellen": self.quellen,
            "empfehlung": self.empfehlung,
        }


# ------------------------------------------------------------------- Quellen

def _frage_aus(auftrag: dict) -> str:
    teile = [str(auftrag.get(feld) or "").strip()
             for feld in ("titel", "thema", "text", "beschreibung")]
    return " ".join(t for t in teile if t)[:600].strip()


def _aus_dem_gehirn(frage: str, modul: str, je_regal: int):
    try:
        return gehirn.lesen(frage, je_saeule=je_regal, agent=modul)
    except TypeError:
        # Aeltere Fassung ohne Agentenkennung - dann eben der Standard-Steckbrief.
        return gehirn.lesen(frage, je_saeule=je_regal)
    except Exception:
        return []


BILDENDUNGEN = (".png", ".jpg", ".jpeg", ".webp", ".svg")


def _bildpfad(eintrag) -> str:
    """Aus dem Eintrag im Regal den Weg zum wirklichen Bild.

    Im Regal steht die Notiz zum Bild - eine Markdown-Datei mit Bildauftrag,
    Startwert und Urteil. Das Bild selbst liegt daneben und heisst gleich.
    """
    roh = ""
    if isinstance(eintrag, dict):
        roh = str(eintrag.get("datei") or eintrag.get("quelle") or "")
    else:
        roh = str(getattr(eintrag, "quelle", "") or "")
    if not roh:
        return ""
    pfad = Path(roh)
    if not pfad.is_absolute():
        # Ein Eintrag darf relativ zur Wurzel stehen - sonst haengt es davon
        # ab, aus welchem Ordner der Aufruf kam. Genau daran sind die Bilder
        # beim zweiten Versuch verschwunden.
        pfad = WURZEL / roh
    if pfad.suffix.lower() in BILDENDUNGEN and pfad.exists():
        return str(pfad)
    for endung in BILDENDUNGEN:
        neben = pfad.with_suffix(endung)
        if neben.exists():
            return str(neben)
    return ""


def _bilder(frage: str, anzahl: int) -> list[dict]:
    """Bilder aus dem Regal - nur solche, die es wirklich auf der Platte gibt."""
    try:
        roh = gehirn.bilder_suchen(frage, anzahl=anzahl * 2)
    except Exception:
        return []
    aus = []
    gesehen = set()
    for eintrag in roh or []:
        pfad = _bildpfad(eintrag)
        if not pfad or pfad in gesehen:
            continue
        gesehen.add(pfad)
        beschreibung = ""
        if isinstance(eintrag, dict):
            beschreibung = str(eintrag.get("auftrag") or eintrag.get("text") or "")
        else:
            beschreibung = str(getattr(eintrag, "text", "") or "")
        aus.append({"quelle": pfad, "text": beschreibung[:300]})
        if len(aus) >= anzahl:
            break
    return aus


def _stuecke_aus_dem_warenausgang(frage: str, hoechstens: int = 5) -> list[dict]:
    """Fertige Stuecke anderer Strassen sind Material, kein Abfall.

    Genommen wird nur, was freigegeben ist - was noch auf ein Urteil wartet,
    ist kein Material.
    """
    if warenausgang is None:
        return []
    try:
        alle = warenausgang.bestand(stand="freigegeben")
    except Exception:
        return []
    worte = {w.lower() for w in frage.split() if len(w) > 3}
    bewertet = []
    for stueck in alle or []:
        text = " ".join(str(stueck.get(f, "")) for f in ("titel", "taugt_fuer", "modul"))
        treffer = sum(1 for w in worte if w in text.lower())
        if treffer:
            bewertet.append((treffer, stueck))
    bewertet.sort(key=lambda p: -p[0])
    return [s for _, s in bewertet[:hoechstens]]


def _kit(name: str) -> dict:
    if not KITS.exists():
        return {}
    try:
        alle = json.loads(KITS.read_text(encoding="utf-8")).get("kits", [])
    except Exception:
        return {}
    for k in alle:
        if k.get("id") == (name or "").lower():
            return k
    return alle[0] if alle else {}


def _verbotsliste() -> list[str]:
    """Woerter, die in nichts vorkommen sollen, was RepoCity herausgibt.

    Die Liste steht in marke/sprache.py - dort, wo auch die Maschen und der
    Regelblock fuer die Agenten stehen. Zwei Listen an zwei Stellen laufen
    auseinander; deshalb wird hier nur nachgesehen, nicht noch einmal getippt.
    Was zusaetzlich in STAND-MARKE.md steht, kommt dazu.
    """
    voreinstellung = ["revolutionär", "nahtlos", "KI-gestützt", "Game-Changer",
                      "ganzheitlich", "Synergie"]
    try:
        import importlib.util as _iu
        _s = _iu.spec_from_file_location("marke_sprache", UNIVERSE / "marke" / "sprache.py")
        _m = _iu.module_from_spec(_s)
        _s.loader.exec_module(_m)
        voreinstellung = list(_m.WORTE)
    except Exception:
        pass
    if not MARKE.exists():
        return voreinstellung
    text = MARKE.read_text(encoding="utf-8", errors="ignore")
    for zeile in text.splitlines():
        if "Verbotsliste" in zeile and ":" in zeile:
            roh = zeile.split(":", 1)[1]
            worte = [w.strip(" .*_`") for w in roh.split(",")]
            worte = [w for w in worte if w and len(w) < 30]
            if worte:
                # Beides, nicht das eine statt des anderen: die Marke darf
                # ergaenzen, aber nicht die Grundliste stillschweigend ersetzen.
                zusammen = list(voreinstellung)
                for w in worte:
                    if w.lower() not in {v.lower() for v in zusammen}:
                        zusammen.append(w)
                return zusammen
    return voreinstellung


# -------------------------------------------------------------------- Messen

def _messen(funde: list, bilder: list, stuecke: list) -> Deckung:
    naehen = [f.naehe for f in funde if getattr(f, "naehe", None) is not None]
    brauchbare = [n for n in naehen if n >= NAEHE_BRAUCHBAR]
    beste = max(naehen) if naehen else 0.0
    # Ohne Vektorsuche gibt es keine Naehe - dann zaehlt die reine Zahl.
    zahl_brauchbar = len(brauchbare) if naehen else len(funde)

    if zahl_brauchbar >= GENUG:
        stufe = "gut"
    elif zahl_brauchbar >= 1 or bilder or stuecke:
        stufe = "duenn"
    else:
        stufe = "leer"

    if stufe == "gut":
        satz = ("%d Funde, davon %d brauchbar (beste Nähe %.2f) - das trägt."
                % (len(funde), zahl_brauchbar, beste))
    elif stufe == "duenn":
        satz = ("Nur %d brauchbare Funde%s. Das reicht für einen Anfang, "
                "nicht für eine belegte Aussage." % (
                    zahl_brauchbar,
                    ", dafür %d Bilder und %d fertige Stücke" % (len(bilder), len(stuecke))
                    if (bilder or stuecke) else ""))
    else:
        satz = ("Zu diesem Thema liegt nichts im 2nd Brain. Was jetzt gebaut wird, "
                "steht auf nichts als dem Auftragstext.")
    return Deckung(stufe=stufe, funde=len(funde), brauchbare=zahl_brauchbar,
                   beste_naehe=round(beste, 3), bilder=len(bilder),
                   stuecke=len(stuecke), satz=satz)


def _empfehlung(deckung: Deckung) -> str:
    if deckung.stufe == "gut":
        return "bauen"
    if deckung.stufe == "duenn":
        return "netz"
    return "nachfragen"


# ------------------------------------------------------------------ Herausgabe

def versorge(auftrag: dict, modul: str = "", braucht: tuple = ("text",),
             je_regal: int = 4, kit: str = "") -> Stoff:
    """Alles, was die eigenen Quellen zu diesem Auftrag hergeben.

    Kostet nichts: kein Modellaufruf, kein Netz. Was fehlt, wird gesagt,
    nicht erfunden.
    """
    frage = _frage_aus(auftrag)
    stoff = Stoff(frage=frage, modul=modul or str(auftrag.get("modul") or ""))
    if not frage:
        stoff.deckung = Deckung("leer", satz="Der Auftrag nennt kein Thema.")
        stoff.empfehlung = "nachfragen"
        return stoff

    funde = _aus_dem_gehirn(frage, stoff.modul, je_regal) if "text" in braucht else []
    bilder = _bilder(frage, anzahl=6) if "bilder" in braucht else []
    stuecke = _stuecke_aus_dem_warenausgang(frage) if "stuecke" in braucht else []

    stoff.funde = list(funde)
    stoff.bilder = list(bilder)
    stoff.stuecke = list(stuecke)
    stoff.kit = _kit(kit or str(auftrag.get("kit") or ""))
    stoff.verbotsliste = _verbotsliste()

    if funde:
        try:
            stoff.kontext = gehirn.als_kontext(funde)
        except Exception:
            stoff.kontext = "\n\n".join(getattr(f, "text", "") for f in funde)[:12000]

    stoff.quellen = sorted({getattr(f, "saeule", "?") for f in funde})
    if bilder:
        stoff.quellen.append("bilder")
    if stuecke:
        stoff.quellen.append("warenausgang")
    if stoff.kit:
        stoff.quellen.append("brand kit")

    stoff.deckung = _messen(list(funde), list(bilder), list(stuecke))
    stoff.empfehlung = _empfehlung(stoff.deckung)
    return stoff


def netz_vorschlagen(stoff: Stoff) -> dict:
    """Was der Deep Researcher holen wuerde - ohne es zu tun.

    Das Netz kostet Zeit und Modellaufrufe. Deshalb entsteht hier nur der
    Vorschlag; ausgeloest wird er ueber die Kostenfreigabe der Strasse.
    """
    return {
        "auftrag": "recherche",
        "frage": stoff.frage,
        "warum": stoff.deckung.satz,
        "modul": "wissen.research",
        "danach": "Der Kurator pflegt die Funde ein, dann trägt die Straße.",
    }


def _probe(argumente: list[str]) -> int:
    if argumente and argumente[0] == "probe":
        argumente = argumente[1:]
    if not argumente:
        print(__doc__)
        return 2
    modul = ""
    if "--modul" in argumente:
        i = argumente.index("--modul")
        modul = argumente[i + 1] if len(argumente) > i + 1 else ""
        argumente = argumente[:i] + argumente[i + 2:]
    stoff = versorge({"text": " ".join(argumente)}, modul=modul,
                     braucht=("text", "bilder", "stuecke"))
    print("Frage:      %s" % stoff.frage[:80])
    print("Modul:      %s" % (stoff.modul or "(ohne)"))
    print("Deckung:    %s - %s" % (stoff.deckung.stufe, stoff.deckung.satz))
    print("Quellen:    %s" % (", ".join(stoff.quellen) or "keine"))
    print("Empfehlung: %s" % stoff.empfehlung)
    if stoff.empfehlung == "netz":
        print("Vorschlag:  %s" % netz_vorschlagen(stoff)["frage"][:70])
    return 0


if __name__ == "__main__":
    raise SystemExit(_probe(sys.argv[1:]))
