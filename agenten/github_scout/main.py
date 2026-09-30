"""GitHub Scout — Kommandozeile.

  python main.py suchen              alle Themen absuchen, bewerten, die Besten abernten
  python main.py suchen --nur-liste  nur suchen und bewerten, nichts abernten
  python main.py ernten <benutzer/repo>
  python main.py stand               die Beobachtungsliste
  python main.py eingang             was für den Kurator bereitliegt
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import ablage
import beobachtung
import bewertung
import destillat
import einstellungen
import gehirn
import meldung
import saat
from ernte import ernten as repo_ernten
from github import GitHub, Repo

AGENT = "github-scout"


def _konfig() -> dict:
    einstellungen.ordner_anlegen()
    return einstellungen.laden()


def _ausschluss() -> set:
    """Was Daniel verworfen hat, steht in github_scout/ausschluss.txt.

    Eigene Datei, nicht in der Konfiguration: 1.389 Zeilen machten sie unlesbar,
    und ein Repositoriumsname mit "Claude-3" darin liess die Pruefung
    `kosten.kein-modell-unter-opus` anschlagen - die kann einen Repo-Namen nicht
    von einer Modellwahl unterscheiden.
    """
    datei = Path(__file__).resolve().parent / "ausschluss.txt"
    if not datei.exists():
        return set()
    namen = set()
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if zeile and not zeile.startswith("#"):
            namen.add(zeile.lower())
    return namen


def befehl_suchen(args) -> int:
    konfig = _konfig()
    suche = konfig["suche"]
    zugang = GitHub()
    print("angemeldet" if zugang.angemeldet
          else "ohne Zugangsschlüssel — 10 Suchanfragen je Minute, 60 andere je Stunde")

    seit = (date.today() - timedelta(days=suche["seit_tagen"])).isoformat()
    gefunden: dict[str, Repo] = {}
    for thema in suche["themen"]:
        try:
            treffer = zugang.suchen(thema, seit, suche["mindeststerne"], suche["je_thema"])
        except Exception as fehler:
            print(f"{thema[:40]:42} {fehler}")
            break
        for repo in treffer:
            if repo.voller_name not in gefunden:
                gefunden[repo.voller_name] = repo
        print(f"{thema[:40]:42} {len(treffer):3} Treffer")

    # Die Ausschlussliste: was Daniel verworfen hat, wird nicht wieder geholt.
    # Sie greift hier, vor der Bewertung - ein ausgeschlossenes Repository soll
    # gar nicht erst Punkte bekommen und in der Beobachtungsliste auftauchen.
    ausschluss = _ausschluss()
    verworfen = [n for n in gefunden if n.lower() in ausschluss]
    for n in verworfen:
        del gefunden[n]
    if verworfen:
        print(f"\n{len(verworfen)} von der Ausschlussliste uebergangen: "
              + ", ".join(sorted(verworfen)[:5])
              + (" ..." if len(verworfen) > 5 else ""))

    repos = list(gefunden.values())
    for repo in repos:
        bewertung.bewerten(repo, konfig["bewertung"])
    repos.sort(key=lambda r: -r.punkte)

    liste = beobachtung.laden()
    unbekannt, bewegt = beobachtung.einordnen(repos, liste)
    schwelle = konfig["bewertung"]["mindestpunkte"]
    zu_ernten = [r for r in unbekannt + bewegt if r.punkte >= schwelle]
    if args.nur_liste:
        zu_ernten = []
    zu_ernten = zu_ernten[:suche["hoechstens_ernten"]]

    print(f"\n{len(repos)} Repositories, {len(unbekannt)} neu, {len(bewegt)} bewegt, "
          f"{len(zu_ernten)} werden abgeerntet")

    geerntet: set[str] = set()
    notizen = atome_gesamt = 0
    ziel = None
    quellen: list[dict] = []

    if zu_ernten:
        ziel = ablage.ordner_anlegen(konfig, "github-fund")
        for nummer, repo in enumerate(zu_ernten, 1):
            uebrig = zugang.rest.get("core")
            if uebrig is not None and uebrig < 8 and not zugang.angemeldet:
                print(f"      Abrufgrenze fast erreicht ({uebrig} übrig) — "
                      "Rest beim nächsten Lauf. Ein Zugangsschlüssel in "
                      "GITHUB_TOKEN hebt die Grenze auf 5.000 je Stunde.")
                break
            print(f"[{nummer}/{len(zu_ernten)}] {repo.voller_name} ({repo.punkte} Punkte)")
            try:
                gefunden_text = repo_ernten(zugang, repo, konfig["ernte"])
            except Exception as fehler:
                print(f"      {fehler}")
                quellen.append({"url": repo.url, "titel": repo.voller_name,
                                "ausgang": f"nicht erreichbar: {fehler}"})
                continue
            notizen_neu, atome_neu = _ablegen(konfig, ziel, repo, gefunden_text, quellen)
            notizen += notizen_neu
            atome_gesamt += atome_neu
            geerntet.add(repo.voller_name)

        ablage.quellen_schreiben(ziel, quellen)
        ablage.uebergabe_schreiben(ziel, "GitHub-Fund " + date.today().isoformat(),
                                   quellen, notizen, atome_gesamt, agent=AGENT)
        ablage.fall_ablegen("Wochenlauf GitHub", quellen, notizen, atome_gesamt,
                            ziel, agent=AGENT)

    beobachtung.speichern(beobachtung.fortschreiben(liste, repos, geerntet))

    if konfig.get("melden") and (unbekannt or bewegt):
        meldung.melde(
            absender=AGENT, art="fund",
            zusammenfassung=f"{len(unbekannt)} neue und {len(bewegt)} bewegte "
                            f"Repositories, {notizen} Notizen abgelegt",
            text="\n".join(f"{r.punkte:3} {r.voller_name} ({r.sterne}★) — {r.beschreibung[:70]}"
                           for r in (unbekannt + bewegt)[:20]),
            daten={"neu": len(unbekannt), "bewegt": len(bewegt),
                   "geerntet": len(geerntet), "eingang": str(ziel) if ziel else ""},
        )

    for repo in repos[:20]:
        marke = "*" if repo.voller_name in geerntet else " "
        print(f"{marke}{repo.punkte:4} {repo.sterne:7}★ {repo.voller_name[:44]:44} "
              f"{repo.aktualisiert} {repo.beschreibung[:44]}")
    if ziel:
        print(f"\n{notizen} Notizen, {atome_gesamt} Atome\n{ziel}")
    return 0


def _ablegen(konfig: dict, ziel: Path, repo: Repo, gefunden: dict,
             quellen: list[dict]) -> tuple[int, int]:
    frage = (f"Was ist an {repo.voller_name} nachahmenswert für ein Multi-Agenten-System "
             f"mit eigener Wissensbasis?")
    inhalt = destillat.destillieren(frage, repo.voller_name, repo.url,
                                    gefunden["text"], konfig)
    if not inhalt.get("brauchbar", True):
        quellen.append({"url": repo.url, "titel": repo.voller_name,
                        "ausgang": "unbrauchbar: " + inhalt.get("grund", "")})
        print(f"      unbrauchbar: {inhalt.get('grund','')}")
        return 0, 0

    thema = ablage.schluessel(repo.voller_name)
    ablage.notiz_schreiben(ziel, repo.voller_name.replace("/", "-"),
                           destillat.notiz_bauen(inhalt, repo.url, thema, agent=AGENT))
    atome = destillat.atome_bauen(inhalt, repo.url, repo.voller_name, thema, agent=AGENT)
    if atome:
        ablage.atome_anhaengen(ziel, atome)
    quellen.append({"url": repo.url, "titel": repo.voller_name, "ausgang": "verwendet",
                    "sterne": repo.sterne, "punkte": repo.punkte,
                    "marken": gefunden["marken"], "atome": len(atome),
                    "weg": inhalt.get("weg", "")})
    print(f"      {len(atome)} Atome ({inhalt.get('weg','')}), "
          f"Spuren: {', '.join(gefunden['marken']) or 'keine'}")
    return 1, len(atome)


def befehl_ernten(args) -> int:
    konfig = _konfig()
    zugang = GitHub()
    antwort = zugang._ruf(f"/repos/{args.repo}")
    if antwort is None:
        print(f"{args.repo} nicht gefunden.")
        return 1
    daten = antwort.json()
    repo = Repo(voller_name=daten["full_name"],
                beschreibung=(daten.get("description") or "")[:400],
                sterne=daten.get("stargazers_count", 0),
                sprache=daten.get("language") or "",
                aktualisiert=(daten.get("pushed_at") or "")[:10],
                url=daten.get("html_url", ""))
    bewertung.bewerten(repo, konfig["bewertung"])
    ziel = ablage.ordner_anlegen(konfig, repo.voller_name.replace("/", "-"))
    quellen: list[dict] = []
    gefunden = repo_ernten(zugang, repo, konfig["ernte"])
    notizen, atome = _ablegen(konfig, ziel, repo, gefunden, quellen)
    ablage.quellen_schreiben(ziel, quellen)
    ablage.uebergabe_schreiben(ziel, repo.voller_name, quellen, notizen, atome, agent=AGENT)
    print(ziel)
    return 0


def befehl_stand(args) -> int:
    _konfig()
    liste = beobachtung.laden()
    if not liste:
        print("Beobachtungsliste leer. Erst 'suchen' aufrufen.")
        return 0
    gereiht = sorted(liste.items(), key=lambda paar: -paar[1].get("punkte", 0))
    for name, eintrag in gereiht:
        marke = "*" if eintrag.get("zuletzt_geerntet") else " "
        print(f"{marke}{eintrag.get('punkte', 0):4} {eintrag.get('sterne', 0):7}★ "
              f"{name[:46]:46} bewegt {eintrag.get('aktualisiert', '')} "
              f"gesehen {eintrag.get('zuletzt_gesehen', '')}")
    print(f"\n{len(liste)} beobachtet, "
          f"{sum(1 for e in liste.values() if e.get('zuletzt_geerntet'))} abgeerntet")
    return 0


def befehl_eingang(args) -> int:
    konfig = _konfig()
    eingang = Path(konfig["ablage"]["eingang"])
    if not eingang.exists():
        print("Nichts im Eingang.")
        return 0
    for ordner in sorted(eingang.iterdir()):
        if not ordner.is_dir():
            continue
        notizen = len(list((ordner / "wissen").glob("*.md"))) if (ordner / "wissen").exists() else 0
        atomdatei = ordner / "atome.jsonl"
        atome = sum(1 for _ in atomdatei.open(encoding="utf-8")) if atomdatei.exists() else 0
        print(f"{ordner.name:52} {notizen:3} Notizen  {atome:4} Atome")
    return 0



def befehl_saeen(args) -> int:
    """Die von Hand gewaehlten Repositories in die Beobachtungsliste uebernehmen."""
    _konfig()
    liste = beobachtung.laden()
    vorher = len(liste)
    liste, neu = saat.saeen(liste)
    beobachtung.speichern(liste)
    print(f"{neu} Repositories aus der Repo-Pruefung uebernommen "
          f"({vorher} waren schon da, jetzt {len(liste)}).")
    if not neu and not vorher:
        print(f"Nichts gefunden. Liegt {saat.PRUEFUNG} an ihrem Platz?")
    return 0

def hauptprogramm(argumente=None) -> int:
    zerleger = argparse.ArgumentParser(prog="github-scout", description=__doc__)
    unter = zerleger.add_subparsers(dest="befehl", required=True)

    suchen = unter.add_parser("suchen")
    suchen.add_argument("--nur-liste", action="store_true", dest="nur_liste")
    suchen.set_defaults(funktion=befehl_suchen)

    ernten = unter.add_parser("ernten")
    ernten.add_argument("repo")
    ernten.set_defaults(funktion=befehl_ernten)

    unter.add_parser("stand").set_defaults(funktion=befehl_stand)
    unter.add_parser("saeen").set_defaults(funktion=befehl_saeen)
    unter.add_parser("eingang").set_defaults(funktion=befehl_eingang)

    args = zerleger.parse_args(argumente)
    return args.funktion(args)


if __name__ == "__main__":
    sys.exit(hauptprogramm())