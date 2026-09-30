"""Der Warenausgang - wo ein fertiges Stueck liegen bleibt, bis es geholt wird.

Ein Agent, der etwas fertig hat, ruft den naechsten Agenten *nicht* an. Er
stellt das Stueck hier ein und meldet das an den Hub. Wer es braucht, holt es
hier ab.

Zwei Gruende, warum das ein Regal ist und kein Foerderband:

  1. Deine Freigabe braucht einen Platz. Ein Aufruf laeuft durch; damit dein
     Ja dazwischen passt, muss das Stueck liegen bleiben koennen.
  2. Direkte Aufrufe zwischen Agenten werden ab dem fuenften Agenten zu einem
     Knoten, den niemand mehr entwirrt.

Jedes Stueck traegt einen Beipackzettel. Fehlt darin 'freigegeben_von', darf
es niemand veroeffentlichen - abholbar() gibt es dann gar nicht erst heraus.

Der Beipackzettel liegt als Markdown im Vault, damit du ihn in Obsidian lesen
kannst. Das Erzeugnis selbst bleibt, wo der Agent es hingelegt hat; der
Zettel verweist darauf.

Aufruf von Hand:
    python warenausgang.py bestand
    python warenausgang.py offen              # wartet auf deine Freigabe
    python warenausgang.py freigeben W0003
    python warenausgang.py ablehnen W0003 "Ton verzerrt"
    python warenausgang.py abholbar social_media_manager
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rueckweg as _rueckweg

try:
    import melden as _meldung
except ImportError:
    _meldung = None

#: Stand eines Stuecks im Warenausgang.
WARTET = "wartet_auf_freigabe"
FREIGEGEBEN = "freigegeben"
ABGELEHNT = "abgelehnt"


def _ordner(konfiguration: dict | None = None) -> Path:
    return _rueckweg._ordner("warenausgang", konfiguration)


def _naechste_kennung(ordner: Path) -> str:
    hoechste = 0
    for datei in ordner.glob("W*.md"):
        treffer = re.match(r"W(\d{4})", datei.name)
        if treffer:
            hoechste = max(hoechste, int(treffer.group(1)))
    return "W%04d" % (hoechste + 1)


def _lesen(datei: Path) -> dict:
    inhalt = datei.read_text(encoding="utf-8")
    zettel = _rueckweg._kopf_lesen(inhalt)
    if not zettel:
        return {}
    zettel["bildquellen"] = _rueckweg._abschnitt(inhalt, "Bildquellen")
    zettel["notiz"] = _rueckweg._abschnitt(inhalt, "Notiz")
    zettel["datei_zettel"] = datei.name
    return zettel


def _feld_setzen(datei: Path, feld: str, wert: str) -> None:
    inhalt = datei.read_text(encoding="utf-8")
    zeile = "%s: %s" % (feld, wert if wert and ":" not in wert else '"%s"' % wert)
    if re.search(r"^%s: .*$" % re.escape(feld), inhalt, re.M):
        inhalt = re.sub(r"^%s: .*$" % re.escape(feld), zeile, inhalt, count=1, flags=re.M)
    else:
        inhalt = inhalt.replace("---\n", "---\n" + zeile + "\n", 1)
    datei.write_text(inhalt, encoding="utf-8", newline="")


def _finden(kennung: str, konfiguration: dict | None = None) -> Path | None:
    treffer = sorted(_ordner(konfiguration).glob("%s_*.md" % kennung))
    return treffer[0] if treffer else None


# ------------------------------------------------------------------ einstellen

def _fertig_modul():
    """kern/fertig.py ueber den Pfad laden - im Universe gibt es Namen mehrfach."""
    import importlib.util as _iu
    fertig = _sys_module_cache.get("kern_fertig")
    if fertig is not None:
        return fertig
    datei = Path(__file__).resolve().parent / "fertig.py"
    if not datei.exists():
        return None
    b = _iu.spec_from_file_location("kern_fertig", datei)
    m = _iu.module_from_spec(b)
    _sys_module_cache["kern_fertig"] = m
    b.loader.exec_module(m)
    return m


_sys_module_cache: dict = {}


def _beurteilen(modul: str, zettel: dict, text: str):
    """Das Ja/Nein holen. Faellt es aus, wird nicht blockiert - eine kaputte
    Messung darf keine fertige Arbeit aufhalten, aber sie darf sie auch nicht
    stillschweigend durchwinken: dann steht 'offen' am Zettel."""
    try:
        f = _fertig_modul()
        if f is None:
            return None
        return f.buchen(f.beurteilen(modul, zettel, text))
    except Exception:
        return None


def einstellen(was: str, auftrag: str, modul: str, titel: str,
               datei: str = "", gueteklasse: str = "", laenge: str = "",
               format_: str = "", stimme: str = "", bildquellen: str = "",
               kosten: float = 0.0, abgenommen_von: str = "qualitaetsmanager",
               taugt_fuer: str = "", notiz: str = "", art: str = "echt",
               kosten_geschaetzt: float | None = None, stoff_kontext: str = "",
               stueck_text: str = "",
               konfiguration: dict | None = None) -> dict:
    """Ein fertiges Stueck in den Warenausgang legen.

    Es ist damit noch nicht veroeffentlichbar - erst deine Freigabe macht es
    abholbar. Der Hub wird benachrichtigt, damit du es in der App siehst.

    Davor steht seit dem 13.09.2026 das Ja/Nein: kern/fertig.py misst die
    Kriterien dieses Bestandteils. Ein NEIN kommt gar nicht erst herein - es
    wird eine Erfahrung "nein" abgelegt, aus der der Ausbilder lernt. Sind alle
    Kriterien gemessen und erfuellt und hat der Bestandteil das dreimal
    hintereinander geschafft, gibt er sich selbst frei; sonst wartet er wie
    bisher auf Daniel.
    """
    ordner = _ordner(konfiguration)
    kennung = _naechste_kennung(ordner)
    zettel = {
        "typ": "beipackzettel",
        "kennung": kennung,
        "art": art,
        "was": was,
        "gueteklasse": gueteklasse or "-",
        "auftrag": auftrag,
        "modul": modul,
        "titel": titel,
        "laenge": laenge or "-",
        "format": format_ or "-",
        "stimme": stimme or "-",
        "kosten": round(kosten, 2),
        "abgenommen_von": abgenommen_von,
        "abgenommen_am": date.today().isoformat(),
        "freigegeben_von": "",
        "freigegeben_am": "",
        "stand": WARTET,
        "taugt_fuer": taugt_fuer or "-",
        "abgeholt_von": "",
        "abgeholt_am": "",
        "erzeugnis": datei or "-",
    }
    urteil = _beurteilen(modul, dict(zettel, bildquellen=bildquellen,
                                     kosten_geschaetzt=kosten_geschaetzt,
                                     stoff_kontext=stoff_kontext),
                         stueck_text or notiz or titel)
    if urteil is not None:
        zettel["fertig"] = "ja" if urteil.ja else "nein"
        zettel["fertig_satz"] = urteil.satz
        zettel["fertig_offen"] = ", ".join(urteil.offene) or "-"
        if not urteil.ja:
            # Nicht fertig heisst: geht nicht in den Warenausgang. Sonst liegt
            # dort Ausschuss, den Daniel aussortieren muss - und genau das
            # soll aufhoeren.
            _fertig_modul().erfahrung_ablegen(urteil, auftrag, "Stueck fertigstellen")
            if _meldung is not None:
                _meldung.melde(
                    absender=modul, art="warnung",
                    zusammenfassung="Nicht fertig, nicht eingestellt: %s" % titel,
                    text=urteil.satz, vorgang=auftrag,
                    daten={"modul": modul, "neins": urteil.neins})
            zettel["stand"] = "nicht_fertig"
            return zettel
        if urteil.selbstfreigabe:
            zettel["stand"] = "freigegeben"
            zettel["freigegeben_von"] = "selbstfreigabe"
            zettel["freigegeben_am"] = date.today().isoformat()

    koerper = "\n".join([
        "", "## Bildquellen", bildquellen.strip() or "-",
        "", "## Fertigkriterien",
        "\n".join("- %-22s %-5s %s" % (n, a.upper(), g)
                   for n, a, g in (urteil.einzeln if urteil else [])) or "-",
        "", "## Notiz", notiz.strip() or "-", "",
    ])
    ziel = ordner / ("%s_%s.md" % (kennung, _rueckweg._saeubern(titel)))
    ziel.write_text(_rueckweg._kopf_schreiben(zettel) + "\n" + koerper, encoding="utf-8", newline="")

    if _meldung is not None:
        _meldung.melde(
            absender=modul, art="freigabe",
            zusammenfassung="%s liegt im Warenausgang: %s" % (was, titel),
            text=("Abgenommen von %s. Kosten %.2f EUR. "
                  "Ohne deine Freigabe holt es niemand ab."
                  % (abgenommen_von, kosten)),
            vorgang=auftrag, daten={"warenausgang": kennung, "modul": modul},
        )
    return zettel


# ------------------------------------------------------------------ freigeben

def freigeben(kennung: str, von: str = "daniel",
              konfiguration: dict | None = None) -> dict | None:
    """Deine Freigabe. Erst danach ist das Stueck abholbar."""
    datei = _finden(kennung, konfiguration)
    if datei is None:
        return None
    _feld_setzen(datei, "freigegeben_von", von)
    _feld_setzen(datei, "freigegeben_am", date.today().isoformat())
    _feld_setzen(datei, "stand", FREIGEGEBEN)
    return _lesen(datei)


def ablehnen(kennung: str, grund: str, konfiguration: dict | None = None) -> dict | None:
    """Deine Ablehnung. Braucht einen Satz und wandert auf die Halde.

    Ein reines Nein sagt nur, dass etwas falsch war, nicht was - und der
    naechste Durchlauf wiederholt es.
    """
    if not grund.strip():
        raise ValueError("Ein Nein ohne Grund lehrt nichts - grund fehlt.")
    datei = _finden(kennung, konfiguration)
    if datei is None:
        return None
    _feld_setzen(datei, "stand", ABGELEHNT)
    zettel = _lesen(datei)
    _rueckweg.verwerfen("warenausgang", kennung, grund,
                        herkunft=datei.name, konfiguration=konfiguration)
    return zettel


# ------------------------------------------------------------------ abholen

def abholbar(fuer: str = "", was: str | None = None,
             konfiguration: dict | None = None,
             art: str | None = "echt") -> list[dict]:
    """Was ein Agent holen darf.

    Nur freigegebene Stuecke, und nur solche, die dieser Agent noch nicht
    geholt hat. Ohne deine Freigabe taucht hier nichts auf - das ist die
    Stelle, an der aus der Freigabe eine Wirkung wird.
    """
    aus = []
    for datei in sorted(_ordner(konfiguration).glob("W*.md")):
        zettel = _lesen(datei)
        if not zettel or zettel.get("stand") != FREIGEGEBEN:
            continue
        if art is not None and zettel.get("art", "echt") != art:
            continue   # ein Trockenlauf ist keine Ware
        if not zettel.get("freigegeben_von"):
            continue
        if was and zettel.get("was") != was:
            continue
        if fuer and fuer in [t.strip() for t in zettel.get("abgeholt_von", "").split(",")]:
            continue
        aus.append(zettel)
    return aus


def abholen(kennung: str, von: str, konfiguration: dict | None = None) -> dict | None:
    """Ein Agent nimmt ein Stueck mit. Mehrere duerfen dasselbe holen."""
    datei = _finden(kennung, konfiguration)
    if datei is None:
        return None
    zettel = _lesen(datei)
    if zettel.get("stand") != FREIGEGEBEN:
        raise PermissionError(
            "%s ist nicht freigegeben (Stand: %s) - es darf niemand abholen."
            % (kennung, zettel.get("stand")))
    bisher = [t.strip() for t in zettel.get("abgeholt_von", "").split(",") if t.strip()]
    if von not in bisher:
        bisher.append(von)
    _feld_setzen(datei, "abgeholt_von", ", ".join(bisher))
    _feld_setzen(datei, "abgeholt_am", date.today().isoformat())
    return _lesen(datei)


# ------------------------------------------------------------------ Uebersicht

def bestand(stand: str | None = None, konfiguration: dict | None = None,
            art: str | None = "echt") -> list[dict]:
    """art="echt" laesst Trockenlaeufe weg - die sollen dir nicht als
    freizugebende Ware begegnen. art=None zeigt alles."""
    aus = []
    for datei in sorted(_ordner(konfiguration).glob("W*.md")):
        zettel = _lesen(datei)
        if not zettel:
            continue
        if stand is not None and zettel.get("stand") != stand:
            continue
        if art is not None and zettel.get("art", "echt") != art:
            continue
        aus.append(zettel)
    return aus


def offen(konfiguration: dict | None = None) -> list[dict]:
    """Was auf deine Freigabe wartet - nur aus dem Echtbetrieb."""
    return bestand(WARTET, konfiguration)


def zahlen(konfiguration: dict | None = None) -> dict:
    alle = bestand(None, konfiguration)
    return {
        "wartet_auf_freigabe": sum(1 for z in alle if z.get("stand") == WARTET),
        "freigegeben": sum(1 for z in alle if z.get("stand") == FREIGEGEBEN),
        "abgelehnt": sum(1 for z in alle if z.get("stand") == ABGELEHNT),
        "noch_nicht_abgeholt": sum(1 for z in alle
                                   if z.get("stand") == FREIGEGEBEN
                                   and not z.get("abgeholt_von")),
    }


# ------------------------------------------------------------------ Aufruf

def _zeile(z: dict) -> str:
    return "%s  %-10s %-16s %-34s %s" % (
        z.get("kennung", ""), z.get("was", ""), z.get("stand", ""),
        (z.get("titel", "") or "")[:34], z.get("abgeholt_von", "") or "-")


def _main(argumente: list[str]) -> int:
    befehl = (argumente[0] if argumente else "bestand").lower()
    if befehl == "bestand":
        for z in bestand():
            print(_zeile(z))
        print()
        for name, zahl in zahlen().items():
            print("%-24s %d" % (name, zahl))
    elif befehl == "offen":
        liste = offen()
        if not liste:
            print("Nichts wartet auf deine Freigabe.")
        for z in liste:
            print(_zeile(z))
            print("      Auftrag %s, %s, %s EUR, abgenommen von %s"
                  % (z.get("auftrag"), z.get("laenge"), z.get("kosten"),
                     z.get("abgenommen_von")))
    elif befehl == "freigeben" and len(argumente) > 1:
        z = freigeben(argumente[1])
        print(_zeile(z) if z else "nicht gefunden: " + argumente[1])
    elif befehl == "ablehnen" and len(argumente) > 2:
        z = ablehnen(argumente[1], " ".join(argumente[2:]))
        print(_zeile(z) if z else "nicht gefunden: " + argumente[1])
    elif befehl == "abholbar" and len(argumente) > 1:
        liste = abholbar(argumente[1])
        if not liste:
            print("Nichts abholbar fuer " + argumente[1])
        for z in liste:
            print(_zeile(z))
    elif befehl == "zettel" and len(argumente) > 1:
        datei = _finden(argumente[1])
        print(datei.read_text(encoding="utf-8") if datei else "nicht gefunden")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
