"""Aus einem Stueck im Warenausgang wird ein fertiger Beitrag.

Ein Beitrag ist mehr als die Datei: er braucht einen Text, der ohne Ton
funktioniert, Schlagworte, die zur Plattform passen, und den Abspann - wer
die Aufnahmen gemacht hat.

Der Abspann ist kein Beiwerk. Die Pexels-Lizenz verlangt ihn nicht, aber
gegenueber jemandem, dessen Aufnahme man kostenlos benutzt, ist er
selbstverstaendlich. Er steht im Beipackzettel, Szene fuer Szene.

Was hier NICHT passiert: veroeffentlichen. Der Beitrag wird gebaut und
abgelegt. Wer ihn hochlaedt, entscheidet sich woanders - solange keine
Zugaenge stehen, bist das du, von Hand.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Was jede Plattform vertraegt. Zeichen, Schlagworte, ob ein Abspann
#: in den Text passt oder in den ersten Kommentar gehoert.
PLATTFORMEN = {
    "tiktok": {"zeichen": 2200, "schlagworte": 5, "abspann": "text",
               "hochformat": True},
    "reels": {"zeichen": 2200, "schlagworte": 5, "abspann": "text",
              "hochformat": True},
    "shorts": {"zeichen": 5000, "schlagworte": 3, "abspann": "text",
               "hochformat": True},
    "linkedin": {"zeichen": 3000, "schlagworte": 3, "abspann": "text",
                 "hochformat": False},
    "x": {"zeichen": 280, "schlagworte": 2, "abspann": "kommentar",
          "hochformat": False},
}

#: Schlagworte, die zum Universe gehoeren - sie stehen vor den Themenworten.
STAMM_SCHLAGWORTE = ["KIAgenten", "Automatisierung"]


@dataclass
class Beitrag:
    plattform: str
    titel: str
    text: str
    schlagworte: list[str] = field(default_factory=list)
    abspann: str = ""
    erster_kommentar: str = ""
    datei: str = ""
    warnungen: list[str] = field(default_factory=list)

    @property
    def veroeffentlichbar(self) -> bool:
        return not self.warnungen

    def als_text(self) -> str:
        teile = [self.text]
        if self.abspann and not self.erster_kommentar:
            teile.append(self.abspann)
        if self.schlagworte:
            teile.append(" ".join("#" + s for s in self.schlagworte))
        return "\n\n".join(t for t in teile if t)


def stoff_zum(zettel: dict) -> dict:
    """Was das 2nd Brain zum Titel dieses Stuecks hergibt.

    Social Media bekommt seine Arbeit aus dem Warenausgang, nicht vom
    Verteiler - im Beipackzettel steht also kein Stoff. Also wird er hier
    geholt, an derselben Tuer wie ueberall: beim Kurator.

    Gebraucht wird davon vor allem die Verbotsliste. Ein Beitrag, der
    draussen steht, ist das Letzte, was sich zurueckholen laesst.
    """
    import sys as _sys
    from pathlib import Path as _Path
    kern = str(_Path(__file__).resolve().parent.parent / "kern")
    if kern not in _sys.path:
        _sys.path.append(kern)
    try:
        import stoff as _stoff
        geholt = _stoff.holen({"thema": (zettel.get("titel") or "").strip(),
                               "id": zettel.get("auftrag", "")},
                              modul="prod.social", braucht=("text",))
        return _stoff.als_auftragsfeld(geholt)
    except Exception:
        return {}


def bauen(zettel: dict, plattform: str, stoff: dict | None = None) -> Beitrag:
    """Baut den Beitrag aus dem Beipackzettel. Kostet nichts."""
    regeln = PLATTFORMEN.get(plattform)
    if regeln is None:
        raise ValueError("unbekannte Plattform: %s" % plattform)

    if stoff is None:
        stoff = stoff_zum(zettel)
    verboten = [str(w).lower() for w in (stoff.get("verbotsliste") or []) if w]

    titel = (zettel.get("titel") or "").strip()
    abspann = _abspann(zettel.get("bildquellen", ""))
    schlagworte = _schlagworte(titel, regeln["schlagworte"], verboten)

    beitrag = Beitrag(
        plattform=plattform,
        titel=titel,
        text=_text(titel, regeln, abspann, schlagworte),
        schlagworte=schlagworte,
        abspann=abspann,
        datei=zettel.get("erzeugnis", ""),
    )
    if regeln["abspann"] == "kommentar":
        beitrag.erster_kommentar = abspann

    beitrag.warnungen = _pruefen(zettel, beitrag, regeln)
    beitrag.warnungen += _verbotene_woerter(beitrag, verboten)
    return beitrag


def _verbotene_woerter(beitrag: Beitrag, verboten: list[str]) -> list[str]:
    """Woerter, die im Universe nicht vorkommen - aus der Verbotsliste des
    Kurators. Sie wird nicht stillschweigend wegkorrigiert: der Beitrag wird
    angehalten und gesagt, was drinsteht."""
    if not verboten:
        return []
    text = (beitrag.als_text() or "").lower()
    getroffen = [w for w in verboten if w in text]
    if not getroffen:
        return []
    # Nicht stillschweigend wegkorrigieren: eine Warnung macht den Beitrag
    # von selbst unveroeffentlichbar (veroeffentlichbar ist "keine Warnung").
    return ["verbotenes Wort im Text: " + ", ".join(sorted(set(getroffen)))]


def _text(titel: str, regeln: dict, abspann: str, schlagworte: list[str]) -> str:
    """Der Text muss ohne Ton tragen - viele sehen das Video stumm."""
    rest = regeln["zeichen"]
    rest -= len(abspann) + 2 if regeln["abspann"] == "text" else 0
    rest -= sum(len(s) + 2 for s in schlagworte)
    text = titel
    if len(text) > rest:
        text = text[:max(0, rest - 1)].rstrip() + "…"
    return text


def _abspann(bildquellen: str) -> str:
    """Wer genannt werden muss - ohne Doppelnennungen, in der Reihenfolge
    des Auftretens."""
    namen: list[str] = []
    for zeile in (bildquellen or "").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile == "-":
            continue
        # "Szene 3: Pexels / MART PRODUCTION" -> "Pexels / MART PRODUCTION"
        wer = zeile.split(":", 1)[1].strip() if ":" in zeile else zeile
        if wer and wer not in namen:
            namen.append(wer)
    if not namen:
        return ""
    return "Aufnahmen: " + ", ".join(namen)


def _schlagworte(titel: str, anzahl: int, verboten: list[str] | None = None) -> list[str]:
    """Aus dem Titel, ohne Fuellworte und ohne verbotene Woerter, dazu die
    Stammworte."""
    tabu = set(verboten or [])
    worte = [w for w in re.findall(r"[A-Za-zÄÖÜäöüß]{5,}", titel)
             if w.lower() not in _FUELLWORTE and w.lower() not in tabu]
    aus = list(STAMM_SCHLAGWORTE)
    for wort in worte:
        marke = wort[0].upper() + wort[1:]
        if marke not in aus:
            aus.append(marke)
        if len(aus) >= anzahl:
            break
    return aus[:anzahl]


_FUELLWORTE = {"warum", "wieso", "einen", "eine", "einem", "eines", "deine",
               "dein", "braucht", "haben", "wird", "werden", "seine", "ihre",
               "diese", "dieser", "dieses", "nicht", "sich", "durch", "gegen"}


def _pruefen(zettel: dict, beitrag: Beitrag, regeln: dict) -> list[str]:
    """Was der Veroeffentlichung im Weg steht. Eine leere Liste heisst frei."""
    warnungen = []
    if not zettel.get("freigegeben_von"):
        warnungen.append("Nicht von dir freigegeben - ohne das darf nichts raus.")
    if not beitrag.abspann:
        warnungen.append("Kein Abspann: die Bildquellen im Beipackzettel "
                         "nennen niemanden, den man nennen koennte.")
    if not beitrag.datei or beitrag.datei == "-":
        warnungen.append("Der Beipackzettel verweist auf keine Datei.")
    if not beitrag.titel:
        warnungen.append("Kein Titel.")
    format_ = (zettel.get("format") or "").lower()
    if regeln["hochformat"] and format_ and "hoch" not in format_ \
            and "1080x1920" not in format_:
        warnungen.append("%s will Hochformat, das Stueck ist %s."
                         % (beitrag.plattform, format_))
    if len(beitrag.als_text()) > regeln["zeichen"]:
        warnungen.append("Text ist laenger als %d Zeichen." % regeln["zeichen"])
    return warnungen


def plattformen_fuer(zettel: dict) -> list[str]:
    """Wofuer das Stueck laut Beipackzettel taugt - und was es davon gibt."""
    roh = (zettel.get("taugt_fuer") or "").lower()
    gewuenscht = [t.strip() for t in re.split(r"[,;]", roh) if t.strip()]
    return [p for p in gewuenscht if p in PLATTFORMEN]
