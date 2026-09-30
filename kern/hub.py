"""Die Verbindung des Rechners zum Hub.

Der Hub liegt auf speedofthespirit.dev und ist eine Poststelle, kein
Arbeiter. Die Agenten laufen hier, die App liegt auf dem Handy; beide
erreichen einander nicht direkt. Also legt jeder dort ab, was der andere
holen soll.

**Der Rechner fragt nach, er wird nicht angerufen.** Das ist Absicht: so
braucht dieser Rechner keine offene Tuer ins Internet und es funktioniert
hinter jedem Router.

    App  --- Auftrag -->  HUB  <-- holt ab --- Sekretaer (hier)
    App  <-- Meldung ---  HUB  <-- meldet ---- Agenten (hier)

Alles hier ist gutmuetig: Steht der Hub nicht, faellt nichts aus. Meldungen
landen weiter im Tagebuch, Auftraege kommen dann eben aus dem Eingangsordner.
Ein Hub, dessen Ausfall die Produktion anhaelt, waere schlimmer als keiner.

Aufruf von Hand:
    python hub.py stand
    python hub.py auftraege
    python hub.py probe
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
sys.path.insert(0, str(HIER))

import umgebung  # noqa: E402

#: So lange wird auf den Hub gewartet, dann gilt er als nicht da.
GEDULD_SEK = 20

# Cloudflare weist Anfragen ohne Absender ab - mit einem nackten 403 und
# ohne Begruendung. Das hat uns bei Pexels schon einmal einen Nachmittag
# gekostet. Wer klopft, sagt wer er ist.
KENNUNG = "RepoCity/1.0 (+https://speedofthespirit.dev)"


class NichtErreichbar(RuntimeError):
    """Der Hub antwortet nicht. Kein Grund, die Arbeit anzuhalten."""


def _zugang() -> tuple[str, str]:
    """Adresse und Schluessel. Beide leer heisst: kein Hub eingerichtet."""
    umgebung.laden()
    import os

    adresse = (os.environ.get("UNIVERSE_HUB_URL", "") or "").strip().rstrip("/")
    if adresse and "://" not in adresse:
        adresse = "https://" + adresse
    return adresse, (os.environ.get("UNIVERSE_CONTAINER_SCHLUESSEL", "") or "").strip()


def eingerichtet() -> bool:
    adresse, schluessel = _zugang()
    return bool(adresse and schluessel)


def _rufen(weg: str, daten: dict | None = None, verfahren: str = "GET") -> dict:
    adresse, schluessel = _zugang()
    if not adresse:
        raise NichtErreichbar("UNIVERSE_HUB_URL ist nicht gesetzt")
    if not schluessel:
        raise NichtErreichbar(
            "UNIVERSE_CONTAINER_SCHLUESSEL fehlt - ohne Ausweis laesst der "
            "Hub niemanden herein. Siehe universe/HUB-EINRICHTEN.md")

    anfrage = urllib.request.Request(
        adresse + "/api/hub" + weg,
        data=json.dumps(daten).encode("utf-8") if daten is not None else None,
        method=verfahren,
        headers={"Content-Type": "application/json",
                 "User-Agent": KENNUNG,
                 "Authorization": "Bearer " + schluessel})
    try:
        with urllib.request.urlopen(anfrage, timeout=GEDULD_SEK) as antwort:
            return json.loads(antwort.read().decode("utf-8"))
    except urllib.error.HTTPError as fehler:
        try:
            inhalt = json.loads(fehler.read().decode("utf-8"))
        except Exception:
            inhalt = {}
        raise NichtErreichbar("%s: %s" % (
            fehler.code, inhalt.get("fehler", fehler.reason))) from fehler
    except Exception as fehler:
        raise NichtErreichbar(str(fehler)) from fehler


# ------------------------------------------------------------------ senden

def melden(absender: str, text: str, art: str = "info",
           zusammenfassung: str = "", vorgang: str | None = None,
           daten: dict | None = None, nutzer: str = "") -> bool:
    """Eine Meldung einliefern. True, wenn sie angekommen ist.

    ``nutzer`` ist das Fach, in das sie gehoert - die Kennung dessen, fuer
    den gerade gearbeitet wird. Ohne Angabe legt der Hub sie ins Fach des
    Admins. Sie in jedes Fach zu legen waere eine Datenpanne mit Ansage,
    darum gibt es diesen Fall nicht.
    """
    try:
        return melden_streng(absender, text, art=art,
                             zusammenfassung=zusammenfassung, vorgang=vorgang,
                             daten=daten, nutzer=nutzer)
    except NichtErreichbar:
        return False


def melden_streng(absender: str, text: str, art: str = "info",
                  zusammenfassung: str = "", vorgang: str | None = None,
                  daten: dict | None = None, nutzer: str = "") -> bool:
    """Wie melden(), aber sie schweigt einen Fehler nicht weg.

    Das braucht kern/melden.py: es schreibt in das Tagebuch, WARUM eine
    Meldung nicht angekommen ist. Ein blosses False dort haette denselben
    Wert wie gar nichts - und genau daran ist der alte Meldeweg monatelang
    unbemerkt tot gewesen.
    """
    satz = {
        "absender": absender, "text": text, "art": art,
        "zusammenfassung": zusammenfassung, "vorgang": vorgang,
        "daten": daten or {}}
    if nutzer:
        satz["nutzer"] = nutzer
    return bool(_rufen("/push", satz, "POST").get("angenommen"))


def puls(seit: str, takte: int, takt_sekunden: float,
         kosten: dict | None = None) -> bool:
    """Der Leitung ihren Puls an den Hub geben - seit wann, wie oft.

    Das Dashboard zeigt daraus, ob und seit wann der Rechner laeuft. Ein
    Schluessel am Hub, der ueberschrieben wird; keine Meldung.

    Seit dem 10.09. faehrt die Kostenzusammenfassung des Monats mit
    (verbrauch.zusammenfassung): so zeigt die Kostenseite der Webseite echte
    Zahlen statt 0,00. Das Buch selbst bleibt auf dem Rechner.
    """
    satz = {"seit": seit, "takte": takte, "takt_sekunden": takt_sekunden}
    if kosten:
        satz["kosten"] = kosten
    try:
        return bool(_rufen("/puls", satz, "POST").get("angenommen"))
    except NichtErreichbar:
        return False


def zustand_melden(auftrag_id: str, zustand: str, rueckmeldung: str = "",
                   fortschritt: float | None = None,
                   warenausgang: str = "") -> bool:
    """Dem Hub sagen, wie es um einen Auftrag steht."""
    satz = {"zustand": zustand, "rueckmeldung": rueckmeldung}
    if fortschritt is not None:
        satz["fortschritt"] = fortschritt
    if warenausgang:
        satz["warenausgang"] = warenausgang
    try:
        return bool(_rufen("/auftrag/" + auftrag_id, satz, "POST").get("angenommen"))
    except NichtErreichbar:
        return False


# ------------------------------------------------------------------ holen

def auftraege(zustand: str | None = None) -> list[dict]:
    """Was beim Hub liegt. Leere Liste, wenn er nicht erreichbar ist."""
    weg = "/auftraege" + ("?zustand=" + zustand if zustand else "")
    try:
        return _rufen(weg).get("auftraege", [])
    except NichtErreichbar:
        return []


def offene_auftraege() -> list[dict]:
    """Was noch niemand angefasst hat - aelteste zuerst, wie an der Theke."""
    return list(reversed(auftraege("gesendet")))


def geraete(nutzer: str = "") -> list[dict]:
    """Wohin fuer diesen Nutzer geweckt werden darf.

    Das Handy hat seine Adresse selbst hinterlegt (worker/hub.js, Weg
    /api/hub/geraet). Hier wird sie geholt - und nur hier: der Weg zum Hub
    steht an einer Stelle, sonst entsteht daneben eine zweite, die niemand
    pflegt. Genau das ist am 09.09. schon einmal passiert.

    Leere Liste heisst: kein Geraet angemeldet. Das ist kein Fehler, sondern
    ein Zustand - und der Anrufer muss ihn unterscheiden koennen von "der Hub
    antwortet nicht", weshalb dieser Fall eine Ausnahme wirft.
    """
    import urllib.parse  # noqa: PLC0415

    weg = "/geraete"
    if nutzer:
        weg += "?nutzer=" + urllib.parse.quote(nutzer)
    return _rufen(weg).get("geraete", [])


def meldungen(anzahl: int = 60) -> list[dict]:
    try:
        return _rufen("/meldungen?anzahl=%d" % anzahl).get("meldungen", [])
    except NichtErreichbar:
        return []


def entscheidungen() -> list[dict]:
    """Meldungen, die Daniel inzwischen beantwortet hat."""
    return [m for m in meldungen(200) if m.get("entscheidung") in ("ja", "nein")]


def stand() -> dict:
    """Lebenszeichen. Wirft NichtErreichbar, wenn der Hub schweigt."""
    return _rufen("/stand")


# ------------------------------------------------------------------ Aufruf

def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "stand").lower()

    if befehl == "stand":
        adresse, schluessel = _zugang()
        print("Adresse   : %s" % (adresse or "-- nicht gesetzt --"))
        print("Schluessel: %s" % ("gesetzt (%d Zeichen)" % len(schluessel)
                                  if schluessel else "-- fehlt --"))
        if not eingerichtet():
            print("\nDer Hub ist nicht eingerichtet.")
            print("Siehe universe/HUB-EINRICHTEN.md - oder:")
            print("  python universe/kern/einrichten.py hub")
            return 2
        try:
            for name, wert in stand().items():
                print("%-12s %s" % (name, wert))
            return 0
        except NichtErreichbar as fehler:
            print("\nNicht erreichbar: %s" % fehler)
            return 1

    if befehl == "auftraege":
        liste = auftraege(argumente[1] if len(argumente) > 1 else None)
        if not liste:
            print("Nichts beim Hub.")
        for a in liste:
            print("%-28s %-16s %-12s %s" % (a.get("id"), a.get("art"),
                                            a.get("zustand"),
                                            (a.get("text") or "")[:40]))
        return 0

    if befehl == "meldungen":
        for m in meldungen(int(argumente[1]) if len(argumente) > 1 else 20):
            print("%s %-18s %-10s %s" % (m.get("zeit", "")[:16],
                                         m.get("absender"), m.get("art"),
                                         (m.get("zusammenfassung") or "")[:44]))
        return 0

    if befehl == "probe":
        print("Probe-Meldung an den Hub ...")
        if melden("system", "Probe vom Rechner", art="info",
                  zusammenfassung="Der Hub ist erreichbar"):
            print("angekommen.")
            return 0
        print("nicht angekommen - siehe 'python hub.py stand'")
        return 1

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
