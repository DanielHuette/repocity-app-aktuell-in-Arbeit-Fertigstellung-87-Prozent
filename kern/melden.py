"""Meldungen an den Sekretär und die RepoCity App - der Weg des Kerns.

Warum die Datei nicht mehr meldung.py heißt: Elf Agenten haben eine eigene
meldung.py mit einer anderen Signatur. Python kann nur ein Modul je Namen
halten - wer zuerst geladen wird, gewinnt für alle, und dann ruft eine
Produktionsstraße plötzlich die falsche Funktion auf. Das ist genau einmal
passiert und hat den ersten Durchlauf der Video-Straße gekostet.

Jeder Agent meldet hierüber. Der Weg ist immer derselbe: erst ins Tagebuch,
dann an den Hub. Der Sekretär liest das Tagebuch und legt in der App vor.
Schlägt der Hub fehl, bricht darum nichts ab — eine verlorene Meldung ist
besser als angehaltene Arbeit.

**Der Weg nach draußen steht in kern/hub.py und nirgends sonst.**
Bis zum 09.09.2026 stand er hier ein zweites Mal: diese Datei las Adresse
und Ausweis aus `universe/hub.json` - einer Datei, die es nie gab und die
auch nichts anlegt. Ergebnis: jede Agentenmeldung landete nur im Tagebuch,
keine einzige erreichte Hub oder App, und niemand hat es gemerkt, weil
`melde()` gutmütig False zurückgibt. Zwei Quellen für dieselbe Sache, eine
davon leer - dasselbe Muster wie beim E-Mail-Manager am selben Tag.
Zusammengelegt: hier wird nichts mehr selbst gerufen.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
ZUSTAND = UNIVERSE / "zustand"
TAGEBUCH = ZUSTAND / "tagebuch.jsonl"

#: Einmal geladen, dann nur noch benutzt.
_hub_modul = None


def _hub():
    """kern/hub.py - über seinen Pfad geladen, nicht über den Suchpfad.

    `import hub` wäre hier mehrdeutig: der E-Mail-Manager hat ein eigenes
    hub.py, und wessen Ordner gerade vorne im Suchpfad steht, entscheidet
    sonst darüber, welches geladen wird. Genau daran ist der E-Mail-Manager
    am 09.09. gescheitert. Über den Pfad geladen, gibt es diese Frage nicht.
    """
    global _hub_modul
    if _hub_modul is None:
        import importlib.util
        stelle = importlib.util.spec_from_file_location(
            "kern_hub_fuer_melden", HIER / "hub.py")
        modul = importlib.util.module_from_spec(stelle)
        stelle.loader.exec_module(modul)
        _hub_modul = modul
    return _hub_modul


def melde(absender: str, text: str, art: str = "info",
          zusammenfassung: str = "", vorgang: str | None = None,
          daten: dict | None = None, nutzer: str = "") -> bool:
    """Gibt True zurück, wenn der Hub die Meldung angenommen hat.

    ``nutzer`` ist das Fach, in das sie gehört - die Kennung dessen, für
    den gerade gearbeitet wird. Ohne Angabe legt der Hub sie ins Fach des
    Admins.
    """
    satz = {
        "absender": absender,
        "art": art,
        "text": text,
        "zusammenfassung": zusammenfassung,
        "vorgang": vorgang,
        "daten": daten or {},
        "gesendet_am": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if nutzer:
        satz["nutzer"] = nutzer
    ins_tagebuch(satz)

    try:
        hub = _hub()
        if not hub.eingerichtet():
            # Kein Hub eingerichtet ist kein Fehler - dann liest der
            # Sekretär eben das Tagebuch. Aber es wird vermerkt, sonst
            # sucht später jemand einen Zustellfehler, den es nicht gibt.
            ins_tagebuch({"absender": absender, "art": "nicht_zugestellt",
                          "text": "Kein Hub eingerichtet - die Meldung steht "
                                  "nur im Tagebuch. Siehe HUB-EINRICHTEN.md",
                          "gesendet_am": satz["gesendet_am"]})
            return False
        return hub.melden_streng(absender, text, art=art,
                                 zusammenfassung=zusammenfassung,
                                 vorgang=vorgang, daten=daten, nutzer=nutzer)
    except Exception as fehler:
        # Bewusst jeder Fehler, nicht nur Netzfehler - siehe oben.
        ins_tagebuch({"absender": absender, "art": "zustellfehler",
                      "text": str(fehler), "gesendet_am": satz["gesendet_am"]})
        return False


def ins_tagebuch(satz: dict) -> None:
    try:
        ZUSTAND.mkdir(parents=True, exist_ok=True)
        with TAGEBUCH.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps(satz, ensure_ascii=False) + "\n")
    except OSError:
        pass


def offene_meldungen(absender: str = "", seit: str = "") -> list[dict]:
    """Was im Tagebuch steht — das liest der Sekretär."""
    if not TAGEBUCH.exists():
        return []
    gefunden = []
    with TAGEBUCH.open(encoding="utf-8") as datei:
        for zeile in datei:
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                satz = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if absender and satz.get("absender") != absender:
                continue
            if seit and satz.get("gesendet_am", "") < seit:
                continue
            gefunden.append(satz)
    return gefunden
