"""Der Email-Manager. Ein Durchlauf alle 30 Minuten.

Je Postfach: ungelesene Post holen, beurteilen, antworten, melden, Spam leeren.
Jede Mail wird einzeln an die RepoCity App gemeldet, mit Kurzfassung - das ist
Daniels Kontrolle.

Faellt ein Postfach aus, laeuft das andere weiter. Der Durchlauf bricht nie ganz ab.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
import traceback

from pathlib import Path as _Pfad

HIER_ORDNER = _Pfad(__file__).resolve().parent


# ─────────────────────────────────────────────────────────────────────────
#  EIGENE DATEIEN EINDEUTIG LADEN
#
#  Es gibt im Universe zwei Dateien namens `hub.py`: eine im Kern, eine
#  hier. Sobald ein Kern-Baustein geladen wird, legt er den Kern-Ordner
#  ganz vorne in den Suchpfad - und ab da fuehrt ein schlichtes
#  `import hub` in die falsche Datei. Am 09.09. nachgemessen:
#  `main.hub.__file__` zeigte auf `universe/kern/hub.py`, und damit fehlte
#  `hub.melde` - der Manager waere bei der ersten Meldung abgebrochen.
#
#  Darum wird die eigene Datei hier ueber ihren Pfad geladen, nicht ueber
#  ihren Namen. Das ist eindeutig, egal wer sonst am Suchpfad dreht.
# ─────────────────────────────────────────────────────────────────────────

def _eigenes(name: str):
    import importlib.util
    ziel = HIER_ORDNER / (name + ".py")
    kennung = "email_manager_" + name
    if kennung in sys.modules:
        return sys.modules[kennung]
    spec = importlib.util.spec_from_file_location(kennung, ziel)
    modul = importlib.util.module_from_spec(spec)
    sys.modules[kennung] = modul
    spec.loader.exec_module(modul)
    return modul


import agent
import einstellungen as e
hub = _eigenes("hub")
import postfach
from postfach import Konto, Postfach

_laeuft = True


def _anhalten(*_):
    global _laeuft
    _laeuft = False
    print("Halte nach diesem Durchlauf an.", flush=True)


signal.signal(signal.SIGTERM, _anhalten)
signal.signal(signal.SIGINT, _anhalten)


# --- Was schon bearbeitet wurde -------------------------------------------


def _erledigt_laden() -> set[str]:
    datei = e.ZUSTAND / "erledigt.json"
    if datei.exists():
        try:
            return set(json.loads(datei.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return set()
    return set()


def _erledigt_sichern(erledigt: set[str]) -> None:
    try:
        e.ZUSTAND.mkdir(parents=True, exist_ok=True)
        # Nur die juengsten behalten, sonst waechst die Datei ohne Ende.
        auszug = list(erledigt)[-5000:]
        (e.ZUSTAND / "erledigt.json").write_text(
            json.dumps(auszug, ensure_ascii=False), encoding="utf-8", newline="")
    except OSError:
        pass


# --- Konten ----------------------------------------------------------------


def _konten_bauen(zugangsdaten: dict) -> list[Konto]:
    konten = []
    for satz in zugangsdaten.get("postfaecher", []):
        konten.append(Konto(
            name=satz.get("name", satz["adresse"]),
            adresse=satz["adresse"],
            benutzer=satz.get("benutzer", satz["adresse"]),
            passwort=satz["passwort"],
            imap_server=satz["imap_server"],
            imap_port=int(satz.get("imap_port", 993)),
            smtp_server=satz.get("smtp_server", ""),
            smtp_port=int(satz.get("smtp_port", 465)),
            smtp_ssl=bool(satz.get("smtp_ssl", True)),
            spam_ordner=satz.get("spam_ordner", "Spam"),
            entwuerfe_ordner=satz.get("entwuerfe_ordner", "Drafts"),
            anzeigename=satz.get("anzeigename", ""),
            signatur_foermlich=satz.get("signatur_foermlich", ""),
            signatur_normal=satz.get("signatur_normal", ""),
            signatur_casual=satz.get("signatur_casual", ""),
        ))
    return konten


def _konten_der_nutzer() -> list[Konto]:
    """Die Postfaecher der Nutzer - je Konto am Hub eines, wenn es eines gibt.

    Was ein Nutzer bei der Einrichtung eingetragen hat, liegt in seinem Fach
    im Tresor. Hier wird es geholt und zu einem benutzbaren Konto gemacht;
    die Serverangaben kommen aus `postfachanbieter.json`, wenn der Nutzer
    sie nicht selbst eingetragen hat.

    Was fehlt oder nicht traegt, wird gemeldet - dem Nutzer in sein Fach,
    nicht in Daniels. Und es wird uebersprungen, nicht geraten.
    """
    konten: list[Konto] = []
    for k in hub.nutzer():
        kennung = str(k.get("email", "")).strip()
        if not kennung:
            continue
        zugang = hub.zugang_von(kennung, "postfach")
        if not zugang:
            continue          # nichts hinterlegt - das ist kein Fehler
        try:
            konto = postfach.konto_aus_zugang(zugang)
        except ValueError as fehler:
            hub.melde("Das Postfach laesst sich nicht einrichten",
                      art="stoerung", zusammenfassung=str(fehler),
                      nutzer=kennung)
            hub.befund_melden(kennung, "postfach", False, str(fehler))
            continue
        konto.eigentuemer = kennung
        konten.append(konto)
    return konten


# --- Darf RepoCity heute noch selbst abschicken? ---------------------------
#
# Zwei Fragen, und beide muessen ja sein: Hat der Nutzer es eingeschaltet,
# und ist seine Obergrenze fuer heute noch nicht erreicht? Ohne beides wird
# vorgelegt statt gesendet - genau wie frueher.
#
# Der Zaehler steht in einer Datei neben dem Zustand, mit dem Datum darin.
# Ein neuer Tag setzt ihn zurueck, ohne dass jemand aufraeumen muss.

ZAEHLERDATEI = e.ZUSTAND / "abschick_zaehler.json"


def _zaehler_lesen() -> dict:
    heute = time.strftime("%Y-%m-%d")
    try:
        d = json.loads(ZAEHLERDATEI.read_text(encoding="utf-8"))
        if d.get("tag") == heute:
            return d
    except (OSError, ValueError):
        pass
    return {"tag": heute, "stand": {}}


def _zaehler_hoch(kennung: str, bereich: str) -> None:
    d = _zaehler_lesen()
    fach = d["stand"].setdefault(kennung or "-", {})
    fach[bereich] = int(fach.get(bereich, 0)) + 1
    try:
        e.ZUSTAND.mkdir(parents=True, exist_ok=True)
        ZAEHLERDATEI.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="")
    except OSError:
        pass


def _abnahme(text: str, vorgang: str, betreff: str, an: str, nutzer: str) -> dict:
    """Die Antwort abnehmen lassen, bevor sie hinausgeht.

    Klemmt der Qualitaetsmanager, darf sie hinaus wie vorher - eine Antwort
    soll nicht daran scheitern, dass eine Messung nicht lief.
    """
    try:
        import importlib.util as _iu
        name = "lebensabnahme"
        modul = sys.modules.get(name)
        if modul is None:
            stelle = _iu.spec_from_file_location(
                name, Path(__file__).resolve().parent.parent / "kern" / "lebensabnahme.py")
            modul = _iu.module_from_spec(stelle)
            sys.modules[name] = modul
            stelle.loader.exec_module(modul)
    except Exception:                                      # noqa: BLE001
        return {"darf_hinaus": True, "maengel": [], "warenausgang": "",
                "grund": "Qualitaetsmanager nicht erreichbar"}
    return modul.abnehmen("post", text, auftrag=vorgang, titel=betreff,
                          zettel={"an": an, "nutzer": nutzer})


def darf_selbst_abschicken(konto: Konto, bereich: str = "post") -> tuple[bool, str]:
    """Darf fuer dieses Postfach jetzt selbst gesendet werden?

    Gibt zurueck: (ja/nein, Grund fuers Nein in Alltagssprache).
    """
    if e.TROCKEN:
        return False, "Trockenlauf - es geht nichts hinaus"
    if not konto.eigentuemer:
        # Daniels eigene Postfaecher waehrend der Entwicklung: hier gilt
        # weiter, was bisher galt.
        return True, ""
    einst = hub.einstellungen_von(konto.eigentuemer)
    an = bool((einst.get("selbstAbschicken") or {}).get(bereich))
    if not an:
        return False, "du hast eingestellt, dass ich dir das vorlege"
    grenze = int((einst.get("hoechstensAmTag") or {}).get(bereich, 0))
    if grenze <= 0:
        return False, "es ist keine Obergrenze gesetzt"
    schon = int((_zaehler_lesen()["stand"].get(konto.eigentuemer, {})).get(bereich, 0))
    if schon >= grenze:
        return False, ("deine Obergrenze fuer heute ist erreicht (%d von %d)"
                       % (schon, grenze))
    return True, ""


# --- Ein Postfach, ein Durchlauf ------------------------------------------


def _postfach_durchgehen(konto: Konto, liste: list[str],
                         erledigt: set[str]) -> dict:
    zaehler = {"gelesen": 0, "gesendet": 0, "entwurf": 0,
               "uebergangen": 0, "spam": 0}

    with Postfach(konto) as fach:
        for mail in fach.ungelesene(hoechstens=e.MAX_MAILS_JE_LAUF):
            kennung = mail.message_id or f"{konto.adresse}:{mail.uid}"
            if kennung in erledigt:
                continue
            zaehler["gelesen"] += 1

            # Andere Agenten brauchen den Inhalt, nicht die Zugangsdaten.
            try:
                import posteingang
                posteingang.merken(
                    von=mail.von, von_name=mail.von_name, betreff=mail.betreff,
                    text=mail.text, datum=str(mail.datum),
                    postfach=konto.adresse, kennung=kennung)
            except Exception:
                pass

            try:
                urteil = agent.beurteilen(mail, fach.verlauf(mail), konto.adresse)
            except Exception as fehler:
                hub.melde(
                    f"{konto.name}: Mail von {mail.von} konnte nicht beurteilt werden",
                    art="stoerung", zusammenfassung=str(fehler))
                continue

            kopf = (f"{konto.name}: Mail von {mail.von_name or mail.von} "
                    f"- {mail.betreff}")

            # Grussformel und Signatur kommen vom Code, nicht vom Modell.
            # So stehen sie immer da, immer vollstaendig, immer gleich.
            signatur = konto.signatur(urteil.get("tonlage", "foermlich"))
            volltext = urteil["text"].rstrip()
            if signatur:
                volltext = volltext + "\n\n" + signatur.strip()

            # Erst die Abnahme, dann alles Weitere. Sie misst den fertigen
            # Text samt Signatur - Laenge und stehengebliebene Luecken - und
            # haelt ihn gegen die Lehrsaetze. Faellt er durch, wird nicht
            # gesendet; der Entwurf liegt mit den Maengeln im Fach, damit
            # sichtbar ist, was fehlt.
            abnahme = None
            if urteil["antworten"]:
                abnahme = _abnahme(volltext, kennung, urteil["betreff"],
                                   mail.von, konto.eigentuemer)
                if not abnahme["darf_hinaus"]:
                    fach.entwurf_ablegen(mail.von, urteil["betreff"], volltext)
                    zaehler["entwurf"] += 1
                    hub.melde(
                        f"{kopf} - NICHT GESENDET, die Abnahme fand Maengel",
                        art="freigabe",
                        zusammenfassung="; ".join(abnahme["maengel"])
                        + "\n\nEntwurf: " + volltext[:800],
                        vorgang=kennung, nutzer=konto.eigentuemer)
                    continue

            if not urteil["antworten"]:
                zaehler["uebergangen"] += 1
                hub.melde(f"{kopf} - nicht beantwortet: {urteil['grund']}",
                          art="dringend" if urteil.get("dringend") else "empfangen",
                          zusammenfassung=urteil["zusammenfassung"],
                          vorgang=kennung)

            elif mail.von not in liste:
                abgelegt = fach.entwurf_ablegen(mail.von, urteil["betreff"], volltext)
                zaehler["entwurf"] += 1
                hub.melde(
                    f"{kopf} - NICHT GESENDET, Empfaenger steht nicht auf der Liste"
                    + (" (als Entwurf abgelegt)" if abgelegt else ""),
                    art="freigabe",
                    zusammenfassung=urteil["zusammenfassung"] + "\n\nAntwort: " + volltext[:800],
                    vorgang=kennung)

            elif not darf_selbst_abschicken(konto, "post")[0]:
                grund = darf_selbst_abschicken(konto, "post")[1]
                abgelegt = fach.entwurf_ablegen(mail.von, urteil["betreff"], volltext)
                zaehler["entwurf"] += 1
                hub.melde(f"{kopf} - nicht gesendet, weil {grund}"
                          + (" (als Entwurf abgelegt)" if abgelegt else ""),
                          art="freigabe",
                          zusammenfassung=urteil["zusammenfassung"]
                          + "\n\nAntwort waere gewesen: " + volltext[:800],
                          vorgang=kennung, nutzer=konto.eigentuemer)

            else:
                try:
                    fach.senden(mail.von, urteil["betreff"], volltext, mail)
                    zaehler["gesendet"] += 1
                    _zaehler_hoch(konto.eigentuemer, "post")
                    hub.melde(f"{kopf} - beantwortet an {mail.von}",
                              art="gesendet", nutzer=konto.eigentuemer,
                              zusammenfassung=urteil["zusammenfassung"]
                              + "\n\nGesendet: " + volltext[:800],
                              vorgang=kennung)
                except Exception as fehler:
                    hub.melde(f"{kopf} - Versand fehlgeschlagen",
                              art="stoerung", zusammenfassung=str(fehler),
                              vorgang=kennung)
                    continue

            fach.als_gelesen(mail)
            erledigt.add(kennung)

        # Spam: erst melden, was drin lag, dann leeren. Sonst ist es weg,
        # bevor jemand es gesehen hat.
        if e.SPAM_LEEREN:
            inhalt = fach.spam_inhalt()
            if inhalt:
                zeilen = "\n".join(f"{absender} - {betreff}" for absender, betreff in inhalt)
                zahl = 0 if e.TROCKEN else fach.spam_leeren()
                zaehler["spam"] = zahl if not e.TROCKEN else len(inhalt)
                hub.melde(
                    f"{konto.name}: Spam-Ordner geleert, {zaehler['spam']} Nachrichten",
                    art="aufraeumen", zusammenfassung=zeilen[:2000])

    return zaehler


# --- Schleife --------------------------------------------------------------


def durchlauf(konten: list[Konto], erledigt: set[str]) -> None:
    try:
        liste = hub.empfaengerliste_holen()
    except hub.HubFehler as fehler:
        liste = []
        hub.melde("Empfaengerliste nicht erreichbar, es wird nichts gesendet",
                  art="stoerung", zusammenfassung=str(fehler))

    gesamt = {"gelesen": 0, "gesendet": 0, "entwurf": 0, "uebergangen": 0, "spam": 0}
    for konto in konten:
        try:
            teil = _postfach_durchgehen(konto, liste, erledigt)
            for schluessel, wert in teil.items():
                gesamt[schluessel] += wert
        except Exception as fehler:
            hub.melde(f"{konto.name}: Postfach nicht erreichbar",
                      art="stoerung", zusammenfassung=str(fehler),
                      nutzer=konto.eigentuemer)
            if konto.eigentuemer:
                hub.befund_melden(konto.eigentuemer, "postfach", False,
                                  str(fehler))
            traceback.print_exc()

    _erledigt_sichern(erledigt)
    hub.melde(
        "Durchlauf beendet: {gelesen} gelesen, {gesendet} beantwortet, "
        "{entwurf} zurueckgehalten, {uebergangen} uebergangen, "
        "{spam} Spam entfernt".format(**gesamt),
        art="lauf")


def main() -> int:
    print("Email-Manager startet.", flush=True)
    try:
        zugangsdaten = hub.zugangsdaten_holen()
    except hub.HubFehler as fehler:
        hub.melde("Kein Postzugang: " + str(fehler), art="stoerung")
        print("Kein Postzugang:", fehler, file=sys.stderr, flush=True)
        return 1

    # Der Modellschluessel kommt denselben Weg wie die Postfachdaten: aus dem Hub,
    # nach Freigabe in der App. Er landet nur in der Umgebung dieses Prozesses.
    if zugangsdaten.get("anthropic_api_key"):
        os.environ["ANTHROPIC_API_KEY"] = zugangsdaten["anthropic_api_key"]
    if not os.environ.get("ANTHROPIC_API_KEY"):
        hub.melde("Kein Modellschluessel hinterlegt", art="stoerung")
        return 1

    # Zwei Quellen, und die Reihenfolge sagt, welche wichtiger ist: erst
    # die Postfaecher dieses Rechners (Regel A - Daniels eigene, solange
    # gebaut wird), dann die der Nutzer aus dem Tresor.
    konten = _konten_bauen(zugangsdaten) + _konten_der_nutzer()
    if not konten:
        hub.melde("Keine Postfaecher hinterlegt", art="stoerung")
        return 1

    eigene = sum(1 for k in konten if not k.eigentuemer)
    hub.melde(f"Email-Manager laeuft, {len(konten)} Postfaecher "
              f"({eigene} auf diesem Rechner, {len(konten) - eigene} von Nutzern), "
              f"alle {e.TAKT_SEKUNDEN // 60} Minuten"
              + (" - TROCKENLAUF" if e.TROCKEN else ""), art="lauf")

    erledigt = _erledigt_laden()
    while _laeuft:
        durchlauf(konten, erledigt)
        for _ in range(e.TAKT_SEKUNDEN):
            if not _laeuft:
                break
            time.sleep(1)

    hub.melde("Email-Manager angehalten", art="lauf")
    return 0


if __name__ == "__main__":
    sys.exit(main())