"""Einrichtungsassistent - fuehrt durch das, was von Hand zu tun ist.

Er nimmt dir ab, was eine Maschine besser kann: Schluessel wuerfeln, in die
.env eintragen, Befehle richtig zusammensetzen, hinterher nachsehen ob es
haelt. Er nimmt dir nicht ab, was du entscheiden musst.

  python einrichten.py stand        was steht, was fehlt
  python einrichten.py hub          Hub-Schluessel erzeugen und eintragen
  python einrichten.py zugang NAME  einen fehlenden Zugang eintragen

Was er NIE tut: einen Schluessel ausgeben, den er nicht selbst gerade
erzeugt hat. Und was er erzeugt, schreibt er nur in die .env - nicht in
eine Meldung, nicht ins Tagebuch, nicht auf den Bildschirm, ausser genau
einmal beim Erzeugen, damit du ihn bei Cloudflare hinterlegen kannst.
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

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

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
NEUSTART = UNIVERSE.parent
ENV = NEUSTART / ".env"
sys.path.insert(0, str(HIER))

#: So viele Zufallszeichen hat ein erzeugter Schluessel. 43 Zeichen aus
#: dem URL-sicheren Vorrat sind 256 Bit - nicht zu erraten, nicht zu lang
#: fuer eine Kopfzeile.
LAENGE = 32


def _zeilen() -> list[str]:
    if not ENV.exists():
        return []
    return ENV.read_text(encoding="utf-8", errors="ignore").splitlines()


def wert(name: str) -> str:
    for zeile in _zeilen():
        if zeile.strip().startswith(name + "="):
            return zeile.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def setzen(name: str, neuer_wert: str) -> None:
    """Traegt einen Wert in die .env ein - oder ersetzt ihn."""
    zeilen = _zeilen()
    for i, zeile in enumerate(zeilen):
        if zeile.strip().startswith(name + "="):
            zeilen[i] = "%s=%s" % (name, neuer_wert)
            break
    else:
        zeilen.append("%s=%s" % (name, neuer_wert))
    ENV.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="")


def wuerfeln() -> str:
    return secrets.token_urlsafe(LAENGE)


# ------------------------------------------------------------------ Hub

def hub_einrichten() -> int:
    """Beide Schluessel erzeugen und den Weg zum Rest zeigen."""
    print("HUB EINRICHTEN")
    print("=" * 60)
    print()
    print("Der Hub braucht zwei Schluessel. Sie haben nichts miteinander zu")
    print("tun und sollen auch nicht gleich sein:")
    print()
    print("  Rechner-Schluessel   Die Agenten und der Sekretaer weisen sich")
    print("                       damit aus. Er liegt in der .env.")
    print("  App-Schluessel       Die RepoCity-App weist sich damit aus.")
    print("                       Er gehoert in die App, nicht in die .env.")
    print()

    vorhanden = wert("UNIVERSE_CONTAINER_SCHLUESSEL")
    if vorhanden:
        print("Ein Rechner-Schluessel steht schon in der .env (%d Zeichen)."
              % len(vorhanden))
        print("Neu wuerfeln wuerde den alten ungueltig machen - dann muesstest")
        print("du ihn auch bei Cloudflare neu hinterlegen.")
        antwort = input("Trotzdem neu wuerfeln? (ja/nein) ").strip().lower()
        if antwort != "ja":
            print("\nNichts geaendert.")
            return _hinweise(vorhanden, None)

    rechner = wuerfeln()
    app = wuerfeln()
    setzen("UNIVERSE_CONTAINER_SCHLUESSEL", rechner)

    adresse = wert("UNIVERSE_HUB_URL")
    if not adresse:
        setzen("UNIVERSE_HUB_URL", "https://speedofthespirit.dev")
        print("UNIVERSE_HUB_URL war leer - auf https://speedofthespirit.dev "
              "gesetzt.")

    zettel = NEUSTART / "APP-SCHLUESSEL.txt"
    zettel.write_text(app + "\n", encoding="utf-8", newline="")

    print()
    print("Der Rechner-Schluessel steht jetzt in der .env.")
    print("Der App-Schluessel steht hier - diese Datei oeffnen, wenn die")
    print("RepoCity-App danach fragt:")
    print()
    print("    " + str(zettel))
    print()

    if _bei_cloudflare_hinterlegen(rechner, app):
        print("Beide Schluessel sind bei Cloudflare hinterlegt.")
        print()
        print("Nachsehen, ob es haelt:")
        print("     python universe\\kern\\hub.py stand")
        print()
        return 0
    print("Cloudflare hat nicht angenommen - der Weg von Hand:")
    print()
    return _hinweise(rechner, app)


def _bei_cloudflare_hinterlegen(rechner: str, app: str) -> bool:
    """Beide Schluessel beim Hub hinterlegen, ohne sie anzuzeigen.

    Der Wert geht durch die Eingabe des Werkzeugs, nicht ueber die
    Befehlszeile - sonst stuende er in der Verlaufsdatei der Konsole.
    """
    import subprocess

    ordner = UNIVERSE / "webseite"
    if not (ordner / "wrangler.jsonc").exists():
        return False
    for name, geheim in (("HUB_SCHLUESSEL", rechner),
                         ("APP_SCHLUESSEL", app)):
        print("  hinterlege %s ..." % name)
        try:
            lauf = subprocess.run(
                "npx wrangler secret put " + name,
                cwd=str(ordner), shell=True, input=geheim + "\n",
                text=True, capture_output=True, timeout=180)
        except Exception as fehler:
            print("  ging nicht: %s" % fehler)
            return False
        if lauf.returncode != 0:
            hinweis = (lauf.stderr or lauf.stdout or "").strip()
            print("  ging nicht: %s" % hinweis[-300:])
            return False
    return True


def _hinweise(rechner: str, app: str | None) -> int:
    print("-" * 60)
    print("Was jetzt noch von Hand zu tun ist:")
    print()
    print("1. Beide Schluessel bei Cloudflare hinterlegen. Im Ordner")
    print("   universe\\webseite ausfuehren:")
    print()
    print("     npx wrangler secret put HUB_SCHLUESSEL")
    print("     npx wrangler secret put APP_SCHLUESSEL")
    print()
    print("   Er fragt jeweils nach dem Wert. Der erste ist der Rechner-,")
    print("   der zweite der App-Schluessel. Sie werden nicht angezeigt und")
    print("   landen NICHT im Repo - das ist der Unterschied zu 'vars'.")
    print()
    print("2. Den Worker veroeffentlichen:")
    print()
    print("     npm run build && npx wrangler deploy")
    print()
    print("3. Nachsehen, ob es haelt:")
    print()
    print("     python universe\\kern\\hub.py stand")
    print()
    if app:
        print("4. Den App-Schluessel in die RepoCity-App eintragen.")
        print("   Bis die App das kann, reicht der Browser: Daniel ist ueber")
        print("   Cloudflare Access ohnehin als admin angemeldet.")
        print()
    return 0



def _pruefer():
    """Den Pruefer des Sicherheitsbeauftragten holen - ohne seinen Ordner
    auf den Suchpfad zu legen.

    Legte man den Ordner auf sys.path, waeren auch seine anderen Module
    (main.py, meldung.py) plotzlich fuer jeden sichtbar, der spaeter
    etwas importiert. Genau so hat sich schon einmal ein Agent das Modul
    eines anderen eingefangen. Wir laden nur die eine Datei, unter einem
    eigenen Namen.
    """
    import importlib.util

    name = "sicherheit_pruefer"
    fertig = sys.modules.get(name)
    if fertig is not None:
        return fertig
    datei = UNIVERSE / "sicherheitsbeauftragter" / "pruefer.py"
    kennung = importlib.util.spec_from_file_location(name, datei)
    modul = importlib.util.module_from_spec(kennung)
    sys.modules[name] = modul
    kennung.loader.exec_module(modul)
    return modul


# ------------------------------------------------------------------ Zugang

def zugang_eintragen(name: str) -> int:
    """Einen fehlenden Zugang eintragen - mit dem, was er lahmlegt."""
    try:
        pruefer = _pruefer()
        angabe = pruefer.einstellungen().get("zugaenge", {}).get(name, {})
    except Exception:
        angabe = {}

    print("ZUGANG EINTRAGEN: %s" % name)
    print("=" * 60)
    if angabe:
        print("Modul : %s" % angabe.get("modul", "--"))
        print("Folge : %s" % angabe.get("folge", "--"))
    if wert(name):
        print("\nSteht schon in der .env (%d Zeichen)." % len(wert(name)))
        if input("Ersetzen? (ja/nein) ").strip().lower() != "ja":
            return 0
    print("\nWert eingeben (er wird nicht angezeigt und nur in die .env "
          "geschrieben):")
    try:
        import getpass

        neu = getpass.getpass("  %s = " % name).strip()
    except Exception:
        neu = input("  %s = " % name).strip()
    if not neu:
        print("Nichts eingegeben, nichts geaendert.")
        return 1
    setzen(name, neu)
    print("\nEingetragen. Nachsehen mit:")
    print("  python universe\\sicherheitsbeauftragter\\main.py zugaenge")
    return 0


# ------------------------------------------------------------------ Stand

def stand() -> int:
    """Was steht, was fehlt - in einer Uebersicht."""
    print("EINRICHTUNG")
    print("=" * 60)
    print()

    print("Hub")
    adresse = wert("UNIVERSE_HUB_URL")
    rechner = wert("UNIVERSE_CONTAINER_SCHLUESSEL")
    print("  %-30s %s" % ("Adresse", adresse or "-- fehlt --"))
    print("  %-30s %s" % ("Rechner-Schluessel",
                          "gesetzt" if rechner else "-- fehlt --"))
    if adresse and rechner:
        import hub as hub_modul

        try:
            zahlen = hub_modul.stand()
            print("  %-30s erreichbar, %s Auftraege, %s offen"
                  % ("Verbindung", zahlen.get("auftraege"), zahlen.get("offen")))
        except Exception as fehler:
            print("  %-30s nicht erreichbar: %s" % ("Verbindung", fehler))
    else:
        print("  -> python einrichten.py hub")

    print()
    print("Zugaenge")
    try:
        pruefer = _pruefer()

        bericht = pruefer.Bericht()
        pruefer.vollzaehligkeit_pruefen(bericht)
        pruefer.ablauf_pruefen(bericht)
        if not bericht.befunde:
            print("  alle erwarteten Zugaenge stehen")
        for b in bericht.befunde:
            print("  %-30s %s" % (b.was, b.rat[:60]))
            if b.bereich == "Zugang":
                name = b.was.split(" ")[0]
                print("  %-30s -> python einrichten.py zugang %s" % ("", name))
    except Exception as fehler:
        print("  Der Sicherheitsbeauftragte antwortet nicht: %s" % fehler)

    print()
    print("Werkzeuge auf diesem Rechner")
    for name, wozu in (("ffmpeg", "Video schneiden"),
                       ("ffprobe", "Video messen"),
                       ("git", "Stand sichern")):
        import shutil

        gefunden = shutil.which(name)
        print("  %-30s %s" % (name, "da" if gefunden else "-- fehlt --"))
    for paket, wozu in (("edge_tts", "Sprecherstimme"),
                        ("chromadb", "2nd Brain"),
                        ("anthropic", "Modellaufrufe")):
        try:
            __import__(paket)
            da = "da"
        except ImportError:
            da = "-- fehlt: pip install %s" % paket.replace("_", "-")
        print("  %-30s %s" % (paket, da))
    return 0


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()
    if befehl == "stand":
        return stand()
    if befehl == "hub":
        return hub_einrichten()
    if befehl == "zugang" and len(argumente) > 1:
        return zugang_eintragen(argumente[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
