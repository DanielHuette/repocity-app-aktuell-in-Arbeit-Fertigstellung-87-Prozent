"""Der eine Weg, einen Agenten zu starten - als eigener Prozess.

Warum nicht einfach importieren: Im Universe gibt es main.py zwoelfmal,
einstellungen.py zehnmal, umgebung.py achtmal, gehirn.py siebenmal.
Python haelt nur EIN Modul je Namen. Wer zuerst geladen wird, gewinnt fuer
alle anderen.

Solange jeder Agent fuer sich lief, hat das nie gestoert. Sobald der
Sekretaer zwei Agenten im selben Prozess startet, bekommt der zweite die
einstellungen.py des ersten - und arbeitet mit fremden Pfaden, fremden
Grenzwerten, fremden Schluesseln. Das ist kein Fehler, den man sieht: der
Agent laeuft, er laeuft nur falsch.

Das laesst sich nicht durch sauberes Benennen loesen, ohne zwoelf Agenten
umzubauen. Es laesst sich aber umgehen, und zwar vollstaendig: **jeder
Agent bekommt seinen eigenen Prozess.** Zwei Prozesse teilen sich kein
sys.modules.

Was das ausserdem bringt:
  · Ein abstuerzender Agent reisst den Sekretaer nicht mit.
  · Eine Zeitgrenze ist durchsetzbar - ein haengender Agent wird beendet.
  · Der Speicher wird am Ende wirklich frei.
  · Dauer und Ausgang jedes Laufs sind messbar und werden verbucht.

Der Preis: Start und Ende kosten je etwa eine halbe Sekunde. Fuer einen
Auftrag, der Minuten laeuft, ist das nichts.

Aufruf von Hand:
    python starter.py liste
    python starter.py video_agent stand
"""
from __future__ import annotations

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
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
sys.path.insert(0, str(HIER))

import verbrauch  # noqa: E402

try:
    import melden
except ImportError:
    melden = None

#: Unter Windows reisst jeder Prozessstart ein Konsolenfenster auf. Bei
#: einem Takt von Sekunden blinkt dabei staendig der Bildschirm. Das hier
#: unterdrueckt es und aendert sonst nichts.
OHNE_FENSTER = {}
if sys.platform == "win32":
    OHNE_FENSTER = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


#: Laenger als das darf kein Agent laufen, bevor er beendet wird.
#: Ein haengender Agent haelt sonst den ganzen Sekretaer auf.
ZEITGRENZE_SEK = 1800

#: Welcher Ordner zu welcher Kostenstelle gehoert. Dieselbe Zuordnung wie
#: in <agent>/meldung.py - hier, weil der Starter die meldung.py des
#: Agenten nicht laden darf, ohne genau das Problem auszuloesen, das er
#: vermeidet.
KOSTENSTELLE = {
    "bewerbungs_agent": "bewerbung",
    "deep_researcher": "wissen.research",
    "email_manager": "post",
    "github_scout": "wissen.scout",
    "kurator": "wissen.kurator",
    "lern_agent": "prod.lernen",
    "musik_agent": "prod.musik",
    "sekretaer": "kalender",
    "video_agent": "prod.video.clip",
    "wohnungs_agent": "wohnung",
    "architekt": "prod.app",
    "gestalter": "prod.praesentation",
    "handelsbeobachter": "trading",
    "marketing": "prod.marketing",
    "webseitenbetreuer": "webseite",
    "implementierer": "prod.app",
    "ausbilder": "ausbildung",
    "qualitaetsmanager": "system.qm",
    "social_media_manager": "prod.social",
    "setzer": "prod.pdf",
    "bildschirmgestalter": "prod.bildschirmschoner",
    "sicherheitsbeauftragter": "system.sicherheit",
    "kostenstellenverantwortlicher_controller": "system.kosten",
}


@dataclass
class Lauf:
    agent: str
    befehl: list[str]
    rueckgabe: int = -1
    dauer: float = 0.0
    ausgabe: str = ""
    fehlerausgabe: str = ""
    abgebrochen: bool = False
    grund: str = ""

    @property
    def gelaufen(self) -> bool:
        return self.rueckgabe == 0 and not self.abgebrochen

    def zeile(self) -> str:
        zeichen = "+" if self.gelaufen else ("~" if self.abgebrochen else "!")
        return "%s %-30s %6.1f s  %s" % (zeichen, self.agent, self.dauer,
                                         self.grund or "Rueckgabe %d"
                                         % self.rueckgabe)


def agenten() -> list[str]:
    """Alle Agentenordner mit einer main.py."""
    return sorted(p.parent.name for p in UNIVERSE.glob("*/main.py"))


def starten(agent: str, *argumente: str, zeitgrenze: int = ZEITGRENZE_SEK,
            umgebung: dict | None = None) -> Lauf:
    """Einen Agenten in einem eigenen Prozess laufen lassen.

    Er bekommt sein eigenes Arbeitsverzeichnis, damit "import
    einstellungen" bei ihm seine eigene Fassung findet und nicht die
    eines anderen.
    """
    import os

    ordner = UNIVERSE / agent
    if not (ordner / "main.py").exists():
        return Lauf(agent, [], grund="kein Agent mit main.py: %s" % agent)

    befehl = [sys.executable, "-u", "main.py", *argumente]
    umwelt = dict(os.environ)
    umwelt.update(umgebung or {})

    beginn = time.time()
    lauf = Lauf(agent, befehl)
    try:
        ergebnis = subprocess.run(
            befehl, cwd=str(ordner), env=umwelt, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=zeitgrenze, **OHNE_FENSTER)
        lauf.rueckgabe = ergebnis.returncode
        lauf.ausgabe = ergebnis.stdout or ""
        lauf.fehlerausgabe = ergebnis.stderr or ""
        lauf.grund = ("gelaufen" if ergebnis.returncode == 0
                      else "mit Rueckgabe %d beendet" % ergebnis.returncode)
    except subprocess.TimeoutExpired:
        lauf.abgebrochen = True
        lauf.grund = ("nach %d Sekunden beendet - er haette sonst alles "
                      "andere aufgehalten" % zeitgrenze)
    except Exception as fehler:
        lauf.grund = "liess sich nicht starten: %s" % fehler
    lauf.dauer = round(time.time() - beginn, 2)

    _vermerken(lauf)
    return lauf


# --------------------------------------------------------------- anstossen

#: Welche Werkstatt gerade arbeitet. Kein Schloss, sondern ein Zettel an
#: der Tuer mit der Kennung des Prozesses. Lebt der nicht mehr, gilt der
#: Zettel nicht - sonst sperrt ein abgewuergter Lauf die Werkstatt fuer
#: immer zu.
LAEUFT = UNIVERSE / "zustand" / "laeuft"


@dataclass
class Anstoss:
    agent: str
    gestartet: bool = False
    schon_da: bool = False
    pid: int = 0
    grund: str = ""


def _lebt(pid: int) -> bool:
    if not pid:
        return False
    try:
        if sys.platform == "win32":
            # tasklist gibt im alten Windows-Zeichensatz aus; ohne diese Angabe
            # stuerzt der Lesefaden von subprocess ab und der Prozess gilt faelschlich
            # als tot (Fallstrick vom 13.09.). Gebraucht wird nur die Ziffernfolge.
            aus = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", timeout=10)
            return str(pid) in (aus.stdout or "")
        import os
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def arbeitet(agent: str) -> int:
    """Kennung des laufenden Prozesses dieser Werkstatt, sonst 0."""
    zettel = LAEUFT / (agent + ".pid")
    try:
        pid = int(zettel.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0
    if _lebt(pid):
        return pid
    try:
        zettel.unlink()
    except OSError:
        pass
    return 0


def anstossen(agent: str, *argumente: str) -> Anstoss:
    """Eine Werkstatt anstossen und NICHT auf sie warten.

    Der Unterschied zu starten(): niemand haelt die Luft an. Der Sekretaer
    legt den Auftrag in den Eingang, stoesst die Werkstatt an und ist
    fertig. Was aus dem Auftrag wird, meldet sie selbst.

    Bis zum 10.09.2026 wartete er bis zum Ende und las den Rueckgabewert.
    Das ging zweimal schief. Erstens: eine Werkstatt, die drei Auftraege
    abarbeitet und beim dritten stolpert, liess auch die ersten beiden als
    "fehler" dastehen - genau so ist am 10.09. ein fertiges Video rot
    geworden, weil eine Karteileiche von gestern danach kam. Zweitens:
    solange sie rechnete, stand alles andere still.

    Zwei Prozesse derselben Werkstatt waeren schlimmer als einer - beide
    greifen in denselben Eingang. Arbeitet sie schon, wird nichts
    gestartet: der Auftrag liegt im Eingang und wird von ihr mit
    abgeraeumt.
    """
    ordner = UNIVERSE / agent
    if not (ordner / "main.py").exists():
        return Anstoss(agent, grund="%s/main.py gibt es nicht" % agent)

    pid = arbeitet(agent)
    if pid:
        return Anstoss(agent, schon_da=True, pid=pid,
                       grund="arbeitet schon (Kennung %d)" % pid)

    try:
        LAEUFT.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    zusatz = {}
    if sys.platform == "win32":
        # Ohne das haengt die Werkstatt am Fenster dessen, der sie
        # angestossen hat, und stirbt mit ihm.
        # NUR CREATE_NO_WINDOW. Zusammen mit DETACHED_PROCESS ist es
        # eine widerspruechliche Angabe, und Windows macht dann doch
        # ein Fenster auf - bei einem Takt von Sekunden blinkt der
        # Bildschirm dauernd.
        zusatz["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    datei = None
    try:
        try:
            datei = (LAEUFT / (agent + ".log")).open("w", encoding="utf-8",
                                                     newline="")
        except OSError:
            datei = None
        vorgang = subprocess.Popen(
            [sys.executable, "-u", "main.py", *[a for a in argumente if a]],
            cwd=str(ordner),
            stdout=datei or subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, **zusatz)
    except Exception as f:
        return Anstoss(agent, grund="liess sich nicht anstossen: %s" % f)
    finally:
        if datei is not None:
            try:
                datei.close()
            except OSError:
                pass

    try:
        (LAEUFT / (agent + ".pid")).write_text(str(vorgang.pid),
                                               encoding="utf-8", newline="")
    except OSError:
        pass
    return Anstoss(agent, gestartet=True, pid=vorgang.pid, grund="angestossen")


def _vermerken(lauf: Lauf) -> None:
    """Dauer und Ausgang ins Verbrauchsbuch - der Controller fuehrt die
    Rechenzeit je Stueck, und ohne diese Zeile weiss er nichts davon."""
    stelle = KOSTENSTELLE.get(lauf.agent, "system")
    try:
        verbrauch.buchen(stelle, 0.0,
                         "Lauf %s: %s" % (lauf.agent, lauf.grund),
                         art="lauf", menge=lauf.dauer)
    except Exception:
        pass
    if (not lauf.gelaufen) and melden is not None:
        try:
            melden.melde(stelle,
                         (lauf.fehlerausgabe or lauf.ausgabe or "")[-1500:],
                         art="fehler",
                         zusammenfassung="%s: %s" % (lauf.agent, lauf.grund))
        except Exception:
            pass


def alle_starten(befehl: str, agenten_liste: list[str] | None = None,
                 zeitgrenze: int = ZEITGRENZE_SEK) -> list[Lauf]:
    """Denselben Befehl bei mehreren Agenten - nacheinander, jeder fuer sich."""
    laeufe = []
    for agent in (agenten_liste or agenten()):
        laeufe.append(starten(agent, befehl, zeitgrenze=zeitgrenze))
    return laeufe


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    if not argumente or argumente[0] == "liste":
        print("Agenten mit einer main.py:\n")
        for agent in agenten():
            print("  %-34s %s" % (agent, KOSTENSTELLE.get(agent, "system")))
        print("\nAufruf: python starter.py <agent> <befehl> [...]")
        return 0

    lauf = starten(argumente[0], *argumente[1:])
    if lauf.ausgabe:
        print(lauf.ausgabe, end="")
    if lauf.fehlerausgabe:
        print(lauf.fehlerausgabe, end="", file=sys.stderr)
    print("\n" + lauf.zeile())
    return lauf.rueckgabe if lauf.rueckgabe >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
