"""Der Zeitplan - was von selbst laeuft.

Eine Aufgabe in der Windows-Aufgabenplanung ruft dieses Skript alle fuenf
Minuten auf. Es sieht in universe/zeitplan.json nach, was faellig ist, und
startet es - jeden Agenten in seinem eigenen Prozess.

Warum nicht fuenfzehn Windows-Aufgaben: Dann muesste man fuenfzehn Stellen
pflegen und wuesste nie, welche noch stimmt. So gibt es eine Aufgabe und
eine Datei, und die Datei liegt im Repo und ist lesbar.

Wann etwas zuletzt lief, steht in universe/zustand/zeitplan_stand.json.
Faellt der Rechner aus, wird beim naechsten Start nachgeholt - aber nur
einmal, nicht fuenfmal fuer fuenf verpasste Takte.

  python zeitplan.py faellig      was jetzt drankaeme, ohne es zu tun
  python zeitplan.py lauf         faellige Eintraege ausfuehren
  python zeitplan.py stand        wann was zuletzt lief
  python zeitplan.py einrichten   den Befehl fuer die Aufgabenplanung zeigen
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
sys.path.insert(0, str(HIER))

import starter  # noqa: E402

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

PLANDATEI = UNIVERSE / "zeitplan.json"
STANDDATEI = UNIVERSE / "zustand" / "zeitplan_stand.json"


def plan() -> dict:
    try:
        return json.loads(PLANDATEI.read_text(encoding="utf-8")).get("eintraege", {})
    except (OSError, json.JSONDecodeError):
        return {}


def _stand() -> dict:
    try:
        return json.loads(STANDDATEI.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _stand_sichern(stand: dict) -> None:
    try:
        STANDDATEI.parent.mkdir(parents=True, exist_ok=True)
        STANDDATEI.write_text(json.dumps(stand, ensure_ascii=False, indent=2),
                              encoding="utf-8", newline="")
    except OSError:
        pass


def faellig(jetzt: datetime | None = None) -> list[tuple[str, dict]]:
    """Was jetzt drankaeme. Ausgeschaltete Eintraege bleiben aus."""
    jetzt = jetzt or datetime.now()
    stand = _stand()
    aus = []
    for name, eintrag in plan().items():
        if eintrag.get("an") is False:
            continue
        # Sekunden schlagen Minuten. Seit der offenen Leitung taktet das
        # Universe in Sekunden, und der Sekretaer soll nicht eine Minute
        # auf einem Auftrag sitzen bleiben. Steht beides in einem Eintrag,
        # gilt die Sekundenangabe - sonst waere es eine Frage der
        # Reihenfolge, welche der beiden Zahlen zaehlt.
        sekunden = float(eintrag.get("alle_sekunden", 0) or 0)
        if sekunden <= 0:
            sekunden = int(eintrag.get("alle_minuten", 0) or 0) * 60
        if sekunden <= 0:
            continue
        zuletzt = stand.get(name, {}).get("zuletzt")
        if not zuletzt:
            aus.append((name, eintrag))
            continue
        try:
            wann = datetime.fromisoformat(zuletzt)
        except ValueError:
            aus.append((name, eintrag))
            continue
        if jetzt - wann >= timedelta(seconds=sekunden):
            aus.append((name, eintrag))
    return aus


def lauf(jetzt: datetime | None = None, laut: bool = True) -> list[dict]:
    """Alles Faellige ausfuehren. Ein Fehler haelt den Rest nicht auf."""
    jetzt = jetzt or datetime.now()
    stand = _stand()
    ergebnisse = []

    for name, eintrag in faellig(jetzt):
        agent = eintrag.get("agent", "")
        argumente = []
        if eintrag.get("datei"):
            # Ein Eintrag kann eine andere Datei als main.py meinen -
            # der Verteiler des Sekretaers zum Beispiel.
            argumente = [eintrag["datei"], eintrag.get("befehl", "")]
        elif eintrag.get("befehl"):
            argumente = [eintrag["befehl"]]

        if eintrag.get("datei"):
            ergebnis = _andere_datei(agent, eintrag["datei"],
                                     eintrag.get("befehl", ""))
        else:
            ergebnis = starter.starten(agent, *[a for a in argumente if a])

        stand[name] = {
            "zuletzt": jetzt.isoformat(timespec="seconds"),
            "gelaufen": ergebnis.gelaufen,
            "dauer": ergebnis.dauer,
            "grund": ergebnis.grund,
        }
        ergebnisse.append({"eintrag": name, "agent": agent,
                           "gelaufen": ergebnis.gelaufen,
                           "dauer": ergebnis.dauer, "grund": ergebnis.grund})
        if laut:
            zeichen = "+" if ergebnis.gelaufen else "!"
            print("%s %-24s %-30s %5.1f s  %s"
                  % (zeichen, name, agent, ergebnis.dauer, ergebnis.grund))

    _stand_sichern(stand)
    return ergebnisse


def _andere_datei(agent: str, datei: str, befehl: str):
    """Wie starter.starten, aber mit einer anderen Datei als main.py."""
    import subprocess
    import time

    ordner = starter.UNIVERSE / agent
    lauf = starter.Lauf(agent, [])
    if not (ordner / datei).exists():
        lauf.grund = "%s/%s gibt es nicht" % (agent, datei)
        return lauf
    beginn = time.time()
    try:
        ergebnis = subprocess.run(
            # An den Leerzeichen trennen, damit auch "einpflegen --alle" geht.
            # Ein einzelnes Wort verhaelt sich unveraendert.
            [sys.executable, "-u", datei] + (befehl.split() if befehl else []),
            cwd=str(ordner), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=starter.ZEITGRENZE_SEK, **starter.OHNE_FENSTER)
        lauf.rueckgabe = ergebnis.returncode
        lauf.ausgabe = ergebnis.stdout or ""
        lauf.fehlerausgabe = ergebnis.stderr or ""
        lauf.grund = ("gelaufen" if ergebnis.returncode == 0
                      else "Rueckgabe %d" % ergebnis.returncode)
    except subprocess.TimeoutExpired:
        lauf.abgebrochen = True
        lauf.grund = "nach %d Sekunden beendet" % starter.ZEITGRENZE_SEK
    except Exception as fehler:
        lauf.grund = "liess sich nicht starten: %s" % fehler
    lauf.dauer = round(time.time() - beginn, 2)
    starter._vermerken(lauf)
    return lauf


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "faellig").lower()

    if befehl == "faellig":
        dran = faellig()
        if not dran:
            print("Nichts faellig.")
        for name, eintrag in dran:
            print("%-24s %-30s alle %d Minuten"
                  % (name, eintrag.get("agent"), eintrag.get("alle_minuten", 0)))
        return 0

    if befehl == "lauf":
        ergebnisse = lauf()
        if not ergebnisse:
            print("Nichts faellig.")
        schlecht = sum(1 for e in ergebnisse if not e["gelaufen"])
        return 1 if schlecht else 0

    if befehl == "stand":
        stand = _stand()
        print("%-24s %-30s %-20s %s"
              % ("Eintrag", "Agent", "zuletzt", "Ausgang"))
        print("-" * 92)
        for name, eintrag in sorted(plan().items()):
            s = stand.get(name, {})
            an = "" if eintrag.get("an") is not False else "  (aus)"
            print("%-24s %-30s %-20s %s%s"
                  % (name, eintrag.get("agent", ""),
                     (s.get("zuletzt") or "noch nie")[:19],
                     s.get("grund", "-"), an))
        return 0

    if befehl == "einrichten":
        print("ZEITPLAN IN DIE AUFGABENPLANUNG EINTRAGEN")
        print("=" * 68)
        print()
        print("Eine einzige Aufgabe genuegt - sie ruft alle fuenf Minuten")
        print("dieses Skript auf, und das sieht in zeitplan.json nach, was")
        print("faellig ist.")
        print()
        print("In einer PowerShell ALS ADMINISTRATOR:")
        print()
        print('  $tat = New-ScheduledTaskAction -Execute "%s" `' % sys.executable)
        print('      -Argument "%s lauf" `' % (HIER / "zeitplan.py"))
        print('      -WorkingDirectory "%s"' % HIER)
        print('  $takt = New-ScheduledTaskTrigger -Once -At (Get-Date) `')
        print('      -RepetitionInterval (New-TimeSpan -Minutes 5)')
        print('  Register-ScheduledTask -TaskName "RepoCity Universe" `')
        print('      -Action $tat -Trigger $takt -Description `')
        print('      "Verteilt Auftraege und laesst faellige Agenten laufen."')
        print()
        print("Danach nachsehen mit:")
        print("  python zeitplan.py stand")
        print()
        print("Wieder entfernen:")
        print('  Unregister-ScheduledTask -TaskName "RepoCity Universe" -Confirm:$false')
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
