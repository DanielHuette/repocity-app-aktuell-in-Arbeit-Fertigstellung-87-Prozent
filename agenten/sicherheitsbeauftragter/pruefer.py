"""Was der Sicherheitsbeauftragte prueft.

Sein Grundsatz: Er sucht nicht nach Mustern, die wie ein Schluessel
aussehen. Er nimmt DEINE Schluessel aus der .env und sucht nach genau
diesen Zeichenfolgen - im Arbeitsverzeichnis, im Git-Verlauf, im Tagebuch,
im Vault, in den fertigen Beitraegen. Das findet auch einen Schluessel, der
keinem bekannten Muster folgt, und meldet keinen Fehlalarm auf eine
zufaellig lange Zeichenkette.

Er gibt dabei nie einen Wert aus. Ein Befund nennt den NAMEN des
Schluessels und die STELLE, an der er liegt - nie den Schluessel selbst.
Ein Sicherheitsbericht, der Schluessel enthaelt, ist selbst das Leck.

Vier Bereiche:

  SCHLUESSEL   Liegt einer, wo er nicht hingehoert? Fehlt einer, sodass ein
               Modul stillschweigend nicht arbeitet? Laeuft einer bald ab?
  TUER         Redet ein Agent an der einen Tuer vorbei mit der Datenbank?
               Liest einer ein Regal, das sein Steckbrief nicht erlaubt?
  AUSGANG      Geht etwas aus dem Haus, das nicht freigegeben ist - oder
               das einen Schluessel enthaelt?
  ABLAGE       Ist die .env vor Git sicher? War sie es immer?
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
from datetime import date, datetime
import pathlib
from pathlib import Path

UNIVERSE = Path(__file__).resolve().parent.parent
NEUSTART = UNIVERSE.parent
ENV = NEUSTART / ".env"
SICHERHEITSDATEI = UNIVERSE / "sicherheit.json"

SCHWER, MITTEL, HINWEIS = "schwer", "mittel", "hinweis"

#: Ein Wert, dessen NAME ihn als Geheimnis ausweist, gilt als Geheimnis -
#: unabhaengig von der Laenge. Ein Passwort mit zwoelf Zeichen ist ein
#: Passwort, auch wenn es kurz ist.
GEHEIMNISWORTE = ("PASSWORT", "PASSWORD", "SCHLUESSEL", "SCHLUESSEL",
                  "KEY", "TOKEN", "SECRET", "GEHEIM", "AUSWEIS")

#: Unter dieser Laenge wird auch ein so benannter Wert nicht gesucht:
#: ein einzelnes Zeichen als Platzhalter kommt in jeder Datei vor und
#: erzeugt nur Fehlalarm.
MINDESTLAENGE_BENANNT = 8

#: Alles andere muss so lang sein, um als Geheimnis zu gelten. Sonst
#: loest jedes "ja" in der .env Alarm aus.
MINDESTLAENGE = 16

#: Diese Eintraege der .env sind keine Geheimnisse, auch wenn sie lang sind.
KEINE_GEHEIMNISSE = {
    "UNIVERSE_MODELL", "UNIVERSE_ZUSTAND", "UNIVERSE_TROCKEN",
    "UNIVERSE_HUB_URL", "MASTERMIND_HUB_ENDPOINT",
}

#: Wo gesucht wird. Alles andere ist zu gross oder gehoert nicht uns.
NICHT_DURCHSUCHEN = {"repos", "github_cache", "node_modules", "_archiv",
                     ".git", "chroma", "build", "__pycache__", ".gradle"}

#: Dateien mit diesen Endungen werden gelesen. Bilder und Videos nicht.
LESBAR = {".py", ".md", ".json", ".jsonl", ".txt", ".kt", ".js", ".ts",
          ".astro", ".html", ".yml", ".yaml", ".toml", ".cfg", ".ini",
          ".ps1", ".sh", ".bat", ".srt", ".ass", ".properties"}


@dataclass
class Befund:
    schwere: str
    bereich: str
    was: str
    wo: str = ""
    rat: str = ""

    def zeile(self) -> str:
        zeichen = {SCHWER: "!!", MITTEL: " !", HINWEIS: "  "}[self.schwere]
        text = "%s %-10s %s" % (zeichen, self.bereich, self.was)
        if self.wo:
            text += "\n           bei: %s" % self.wo
        if self.rat:
            text += "\n           Rat: %s" % self.rat
        return text


@dataclass
class Bericht:
    befunde: list[Befund] = field(default_factory=list)
    geprueft: list[str] = field(default_factory=list)

    def dazu(self, *befunde: Befund) -> None:
        self.befunde.extend(befunde)

    @property
    def sauber(self) -> bool:
        return not any(b.schwere in (SCHWER, MITTEL) for b in self.befunde)

    def nach_schwere(self, schwere: str) -> list[Befund]:
        return [b for b in self.befunde if b.schwere == schwere]


# ------------------------------------------------------------------ Stammdaten

def einstellungen() -> dict:
    try:
        return json.loads(SICHERHEITSDATEI.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def geheimnisse() -> dict[str, str]:
    """Name -> Wert. Wird nie ausgegeben, nur zum Suchen benutzt."""
    aus: dict[str, str] = {}
    if not ENV.exists():
        return aus
    for zeile in ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        name, wert = zeile.split("=", 1)
        name, wert = name.strip(), wert.strip().strip('"').strip("'")
        if name in KEINE_GEHEIMNISSE or not wert:
            continue
        if _heisst_wie_ein_geheimnis(name):
            if len(wert) >= MINDESTLAENGE_BENANNT:
                aus[name] = wert
        elif len(wert) >= MINDESTLAENGE:
            aus[name] = wert
    return aus


def _heisst_wie_ein_geheimnis(name: str) -> bool:
    """Sagt der Name schon, dass es ein Geheimnis ist?

    Frueher entschied nur die Laenge - und Passwoerter mit zwoelf Zeichen
    fielen unter die Grenze von sechzehn. Waere eines irgendwo gelandet,
    haette es niemand gefunden. Der Name weiss es besser als die Laenge.
    """
    gross = name.upper()
    return any(wort in gross for wort in GEHEIMNISWORTE)


def alle_eintraege() -> dict[str, str]:
    """Alle .env-Zeilen, auch die kurzen und leeren - fuer die Vollzaehligkeit."""
    aus: dict[str, str] = {}
    if not ENV.exists():
        return aus
    for zeile in ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
        zeile = zeile.strip()
        if zeile and not zeile.startswith("#") and "=" in zeile:
            name, wert = zeile.split("=", 1)
            aus[name.strip()] = wert.strip().strip('"').strip("'")
    return aus


# ------------------------------------------------------------------ Ablage

def ablage_pruefen(bericht: Bericht) -> None:
    bericht.geprueft.append("Ablage der .env")
    if not ENV.exists():
        bericht.dazu(Befund(SCHWER, "Ablage", "Es gibt keine .env.",
                            rat="Ohne sie arbeitet kein Agent mit Zugang."))
        return

    if not _git("check-ignore", "-q", ".env", erfolg_ist=0):
        bericht.dazu(Befund(
            SCHWER, "Ablage", "Die .env ist nicht vor Git geschuetzt.",
            wo=str(ENV),
            rat="'.env' in die .gitignore aufnehmen, SOFORT - ein Commit "
                "genuegt und die Schluessel liegen fuer immer im Verlauf."))

    verlauf = _git("log", "--all", "--oneline", "--", ".env")
    if verlauf:
        bericht.dazu(Befund(
            SCHWER, "Ablage",
            "Die .env war schon einmal im Repo (%d Commits)."
            % len(verlauf.splitlines()),
            rat="Alle betroffenen Schluessel beim Anbieter neu ausstellen. "
                "Aus dem Verlauf loeschen reicht nicht - Kopien koennen "
                "laengst woanders liegen."))


def _git(*teile: str, erfolg_ist: int | None = None) -> str | bool:
    try:
        lauf = subprocess.run(["git"] + list(teile), cwd=str(NEUSTART),
                              capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return False if erfolg_ist is not None else ""
    if erfolg_ist is not None:
        return lauf.returncode == erfolg_ist
    return lauf.stdout


# ------------------------------------------------------------------ Schluessel

def schluessel_suchen(bericht: Bericht, gruendlich: bool = False) -> None:
    """Sucht die echten Werte aus der .env im Arbeitsverzeichnis.

    Nicht nach Mustern - nach genau diesen Zeichenfolgen. Das findet auch
    einen Schluessel ohne erkennbares Muster.

    gruendlich=False durchsucht Code, Einstellungen, Vault und Betriebsdaten -
    also die Stellen, an denen ein Schluessel realistisch landet. Das dauert
    Sekunden.
    gruendlich=True nimmt zusaetzlich mein_ki_gehirn dazu: 20.000 Dokumente
    aus Transkripten und fremden Repos. Das dauert Minuten und lohnt sich,
    wenn ein Agent einmal eine Fehlermeldung mit voller Anfrage abgelegt
    haben koennte.
    """
    werte = geheimnisse()
    bericht.geprueft.append("%d Schluessel im %s"
                            % (len(werte), "ganzen Bestand" if gruendlich
                               else "Arbeitsverzeichnis"))
    if not werte:
        return
    umgekehrt = {wert: name for name, wert in werte.items()}

    for datei in _dateien(gruendlich):
        try:
            inhalt = datei.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for wert, name in umgekehrt.items():
            if wert in inhalt:
                bericht.dazu(Befund(
                    SCHWER, "Schluessel",
                    "%s steht im Klartext ausserhalb der .env." % name,
                    wo=str(datei.relative_to(NEUSTART)),
                    rat="Aus der Datei entfernen und ueber os.environ lesen. "
                        "Steht die Datei unter Git, den Schluessel neu "
                        "ausstellen lassen."))


#: Der Wissensspeicher wird nur beim gruendlichen Rundgang mitgelesen -
#: 20.000 Dokumente kosten Minuten, und ein eigener Schluessel landet dort
#: nur, wenn ein Agent eine Fehlermeldung mit voller Anfrage abgelegt hat.
NUR_GRUENDLICH = {"mein_ki_gehirn"}


def _dateien(gruendlich: bool = False):
    """Alles Lesbare unter Neustart, ohne die grossen Fremdordner.

    Mit os.walk und nicht mit rglob: rglob laeuft erst durch jeden Ordner
    und ueberspringt ihn dann - bei 24 GB geklonter Fremd-Repos dauert
    allein das Durchlaufen Minuten. Hier werden die Ordner abgeschnitten,
    bevor hineingegangen wird.
    """
    import os

    ueberspringen = set(NICHT_DURCHSUCHEN)
    if not gruendlich:
        ueberspringen |= NUR_GRUENDLICH

    for wurzel, ordner, dateien in os.walk(NEUSTART):
        # In-place kuerzen: os.walk geht danach nur noch in das, was bleibt.
        ordner[:] = [o for o in ordner if o not in ueberspringen]
        for name in dateien:
            if name == ".env":
                continue
            pfad = pathlib.Path(wurzel) / name
            if pfad.suffix.lower() not in LESBAR:
                continue
            try:
                if pfad.stat().st_size > 4_000_000:
                    continue
            except OSError:
                continue
            yield pfad


#: Wo im Verlauf gesucht wird. Ohne diese Einschraenkung vergleicht die
#: Suche die APKs im Repo mit - hundert Megabyte je Schluessel.
TEXTPFADE = ("*.py", "*.md", "*.json", "*.jsonl", "*.txt", "*.kt", "*.js",
             "*.ts", "*.astro", "*.html", "*.yml", "*.yaml", "*.toml",
             "*.cfg", "*.ini", "*.ps1", "*.sh", "*.bat", "*.properties",
             "*.env*", ".env", ".gitignore", "Dockerfile*")


def verlauf_pruefen(bericht: Bericht) -> None:
    """Ein Schluessel im Git-Verlauf bleibt dort, auch wenn die Datei
    geloescht wird. Das Repo liegt auf GitHub - das ist das eine Risiko
    mit echtem Schaden."""
    werte = geheimnisse()
    bericht.geprueft.append("Git-Verlauf auf %d Schluessel" % len(werte))
    for name, wert in werte.items():
        # Nur Textdateien: das Repo enthaelt fuenf APKs zu je 20 MB, und
        # die Suche vergleicht sonst hundert Megabyte Binaerdaten je
        # Schluessel. Ein Schluessel steht ohnehin nie in einer APK.
        treffer = _git("log", "--all", "-S", wert, "--oneline",
                       "--", *TEXTPFADE)
        if treffer:
            bericht.dazu(Befund(
                SCHWER, "Verlauf",
                "%s taucht im Git-Verlauf auf (%d Commits)."
                % (name, len(treffer.splitlines())),
                rat="Beim Anbieter neu ausstellen. Das Repo liegt auf GitHub; "
                    "wer es je geklont hat, hat den Schluessel."))


def betriebsdaten_pruefen(bericht: Bericht) -> None:
    """Tagebuch, Verbrauchsbuch, Vault und die fertigen Beitraege.

    Das sind die Stellen, an denen ein Schluessel unbemerkt landet: eine
    Fehlermeldung mit der vollen Anfrage, ein Beitrag mit einem Link.
    """
    werte = geheimnisse()
    orte = [UNIVERSE / "zustand", NEUSTART / "vault"]
    bericht.geprueft.append("Tagebuch, Verbrauchsbuch, Vault")
    for ort in orte:
        if not ort.exists():
            continue
        for datei in ort.rglob("*"):
            if not datei.is_file() or datei.suffix.lower() not in LESBAR:
                continue
            try:
                inhalt = datei.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for name, wert in werte.items():
                if wert in inhalt:
                    bericht.dazu(Befund(
                        SCHWER, "Betrieb",
                        "%s steht in einer Betriebsdatei." % name,
                        wo=str(datei.relative_to(NEUSTART)),
                        rat="Die Zeile entfernen und die Stelle suchen, die "
                            "sie geschrieben hat - meist eine Fehlermeldung, "
                            "die die ganze Anfrage mitprotokolliert."))


def vollzaehligkeit_pruefen(bericht: Bericht) -> None:
    """Welche Zugaenge fehlen - und welches Modul deshalb stillsteht.

    Ein fehlender Schluessel ist keine Sicherheitsluecke, aber dieselbe
    Sorte stiller Ausfall: der Agent laeuft, findet nichts, meldet nichts.
    """
    eintraege = alle_eintraege()
    erwartet = einstellungen().get("zugaenge", {})
    bericht.geprueft.append("%d erwartete Zugaenge" % len(erwartet))
    for name, angabe in erwartet.items():
        wert = eintraege.get(name, "")
        if not wert:
            bericht.dazu(Befund(
                angabe.get("schwere", MITTEL), "Zugang",
                "%s ist leer oder fehlt." % name,
                wo=angabe.get("modul", ""),
                rat=angabe.get("folge", "") or
                    "Ohne ihn arbeitet dieses Modul nicht, ohne es zu melden."))


def ablauf_pruefen(bericht: Bericht, heute: date | None = None) -> None:
    """Ein Schluessel, der abgelaufen ist, sieht aus wie ein kaputter Agent."""
    heute = heute or date.today()
    vorlauf = int(einstellungen().get("ablauf_vorlauf_tage", 21))
    daten = einstellungen().get("ablaeuft", {})
    bericht.geprueft.append("%d Ablaufdaten" % len(daten))
    for name, tag in daten.items():
        try:
            wann = datetime.strptime(str(tag), "%Y-%m-%d").date()
        except ValueError:
            continue
        rest = (wann - heute).days
        if rest < 0:
            bericht.dazu(Befund(
                SCHWER, "Ablauf", "%s ist seit %d Tagen abgelaufen."
                % (name, -rest),
                rat="Neu ausstellen. Bis dahin schlaegt jeder Aufruf fehl - "
                    "und sieht aus wie ein kaputter Agent."))
        elif rest <= vorlauf:
            bericht.dazu(Befund(
                MITTEL, "Ablauf", "%s laeuft in %d Tagen ab (%s)."
                % (name, rest, wann.isoformat()),
                rat="Jetzt neu ausstellen, nicht am letzten Tag."))


def klartext_pruefen(bericht: Bericht) -> None:
    """Passwoerter liegen im Klartext in der .env.

    Das ist kein Fehler, sondern der Stand: eine Datei auf deinem Rechner,
    nicht im Repo. Es soll nur niemand glauben, sie waeren geschuetzt.
    """
    passwoerter = [n for n, w in alle_eintraege().items()
                   if "PASSWORT" in n.upper() and w]
    if passwoerter:
        bericht.dazu(Befund(
            HINWEIS, "Klartext",
            "%d Passwoerter liegen im Klartext in der .env." % len(passwoerter),
            wo=", ".join(sorted(passwoerter)),
            rat="Fuer den Handel gibt es den Android-Keystore. Fuer die .env "
                "gibt es nichts Vergleichbares - wer hier Zugriff auf den "
                "Rechner hat, hat die Zugaenge. Wo der Anbieter es anbietet, "
                "ist ein eigener Schluessel besser als Benutzer und Passwort."))


# ------------------------------------------------------------------ Tuer

def tuer_pruefen(bericht: Bericht) -> None:
    """Redet jemand an der einen Tuer vorbei mit der Datenbank?

    Der Kern hat eine Regel: kein Agent redet selbst mit ChromaDB, alles
    geht durch gehirn.py. Wer sie umgeht, umgeht damit auch die
    Steckbriefe - und liest Regale, die er nicht sehen darf.
    """
    bericht.geprueft.append("Zugriffe an der Tuer vorbei")
    erlaubt = {"kern", "kostenstellenverantwortlicher_controller"}
    muster = re.compile(r"^\s*import\s+chromadb|^\s*from\s+chromadb", re.M)
    for datei in UNIVERSE.rglob("*.py"):
        if any(teil in NICHT_DURCHSUCHEN for teil in datei.parts):
            continue
        try:
            rel = datei.relative_to(UNIVERSE)
        except ValueError:
            continue
        if rel.parts and rel.parts[0] in erlaubt:
            continue
        try:
            if muster.search(datei.read_text(encoding="utf-8", errors="ignore")):
                bericht.dazu(Befund(
                    MITTEL, "Tuer",
                    "Hier wird ChromaDB direkt angesprochen.",
                    wo=str(rel),
                    rat="Ueber gehirn.lesen() gehen. Wer direkt zugreift, "
                        "umgeht die Steckbriefe und sieht Regale, die ihm "
                        "nicht zustehen."))
        except OSError:
            continue


def steckbriefe_pruefen(bericht: Bericht) -> None:
    """Darf jedes Modul nur, was vorgesehen ist?"""
    try:
        briefe = json.loads((UNIVERSE / "gehirn.json").read_text(
            encoding="utf-8")).get("steckbriefe", {})
    except (OSError, json.JSONDecodeError):
        return
    bericht.geprueft.append("%d Steckbriefe" % len(briefe))
    darf_schreiben = set(einstellungen().get("darf_schreiben", []))
    for name, brief in briefe.items():
        if name.startswith("_"):
            continue
        if brief.get("schreiben") and name not in darf_schreiben:
            bericht.dazu(Befund(
                MITTEL, "Rechte",
                "%s darf schreiben, steht aber nicht auf der Liste." % name,
                rat="Entweder in sicherheit.json unter 'darf_schreiben' "
                    "aufnehmen oder das Recht in gehirn.json entziehen."))
        if "persoenlich" in (brief.get("regale") or []):
            bericht.dazu(Befund(
                HINWEIS, "Rechte",
                "%s darf das Regal 'persoenlich' sehen." % name,
                rat="Das geht nur mit Besitzer-Angabe - gepruefte Regel in "
                    "gehirn.lesen(). Hier steht es nur, damit du es weisst."))


# ------------------------------------------------------------------ Ausgang

def ausgang_pruefen(bericht: Bericht) -> None:
    """Geht etwas aus dem Haus, das nicht freigegeben ist?"""
    ausgang = NEUSTART / "vault" / "warenausgang"
    if not ausgang.exists():
        return
    bericht.geprueft.append("Warenausgang")
    for datei in ausgang.glob("W*.md"):
        text = datei.read_text(encoding="utf-8", errors="ignore")
        kopf = dict(_kopfzeilen(text))
        if kopf.get("abgeholt_von") and not kopf.get("freigegeben_von"):
            bericht.dazu(Befund(
                SCHWER, "Ausgang",
                "%s wurde abgeholt, ohne freigegeben zu sein."
                % kopf.get("kennung", datei.name),
                wo=str(datei.relative_to(NEUSTART)),
                rat="Nachsehen, wer es geholt hat - die Freigabe ist die "
                    "einzige Stelle, an der du entscheidest."))


def _kopfzeilen(text: str):
    treffer = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not treffer:
        return
    for zeile in treffer.group(1).splitlines():
        if ":" in zeile:
            name, wert = zeile.split(":", 1)
            yield name.strip(), wert.strip().strip('"')


# ------------------------------------------------------------------ Rundgang

def rundgang(heute: date | None = None, gruendlich: bool = False) -> Bericht:
    """Alles auf einmal. Kostet nichts und aendert nichts.

    gruendlich=True nimmt den Wissensspeicher dazu - dann dauert es Minuten
    statt Sekunden.
    """
    bericht = Bericht()
    ablage_pruefen(bericht)
    schluessel_suchen(bericht, gruendlich)
    verlauf_pruefen(bericht)
    betriebsdaten_pruefen(bericht)
    vollzaehligkeit_pruefen(bericht)
    ablauf_pruefen(bericht, heute)
    klartext_pruefen(bericht)
    tuer_pruefen(bericht)
    steckbriefe_pruefen(bericht)
    ausgang_pruefen(bericht)
    return bericht
