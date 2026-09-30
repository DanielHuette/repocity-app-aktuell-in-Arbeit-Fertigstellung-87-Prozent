"""Der Rundgang ueber die Webseite - sehen, nicht anfassen.

Dieser Agent aendert die Webseite nicht. Das ist Absicht: eine Seite,
die sich selbst umbaut, waehrend niemand hinsieht, ist genau das, was
man nicht will. Was zu aendern ist, geht als Bauauftrag an den
Architekten und braucht Daniels Freigabe wie jede andere Aenderung.

Er prueft drei Dinge, alle kostenlos und ohne Netz:

    GEBAUT      liegt ueberhaupt ein fertiger Stand in dist/
    WEGE        zeigt jeder interne Verweis auf eine Seite, die es gibt
    GEWICHT     ist eine Seite unverhaeltnismaessig gross geworden

Und eines mit Netz, wenn man es ausdruecklich verlangt:

    LEBEND      antwortet die veroeffentlichte Seite, und mit was
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
WEBSEITE = UNIVERSE / "webseite"

for _p in (str(KERN),):
    if _p not in sys.path:
        sys.path.append(_p)

MODUL = "webseite"

#: Ab hier wird eine einzelne Seite ungemuetlich. Gemessen: die
#: schwerste Seite lag bisher bei rund 90 KB.
SEITE_HOECHSTENS_KB = 400

#: Was der Rundgang nicht prueft, weil es von aussen kommt.
FREMD = re.compile(r"^(https?:|mailto:|tel:|data:|#|//)")

KENNUNG = "RepoCity/1.0 (+https://speedofthespirit.dev)"


@dataclass
class Befund:
    gebaut: bool = False
    seiten: int = 0
    verweise: int = 0
    tote_verweise: list = field(default_factory=list)
    schwere_seiten: list = field(default_factory=list)
    lebend: list = field(default_factory=list)

    @property
    def sauber(self) -> bool:
        return (self.gebaut and not self.tote_verweise
                and not self.schwere_seiten
                and not [z for z in self.lebend if not z["gut"]])

    def als_text(self) -> str:
        zeilen = []
        if not self.gebaut:
            zeilen.append("Es liegt kein gebauter Stand in dist/ - "
                          "'npm run build' ist noch nicht gelaufen.")
            return "\n".join(zeilen)
        zeilen.append("%d Seiten, %d interne Verweise geprueft."
                      % (self.seiten, self.verweise))
        for t in self.tote_verweise:
            zeilen.append("Toter Verweis: %s zeigt auf %s" % (t["von"], t["auf"]))
        for s in self.schwere_seiten:
            zeilen.append("Schwer: %s mit %.0f KB" % (s["seite"], s["kb"]))
        for z in self.lebend:
            zeilen.append("%s %s%s" % (z["weg"], z["stand"],
                                       "" if z["gut"] else "  <- antwortet nicht"))
        if self.sauber:
            zeilen.append("Nichts zu beanstanden.")
        return "\n".join(zeilen)


def dist() -> Path:
    return WEBSEITE / "dist"


# ------------------------------------------------------------------ Wege

def _seiten(wurzel: Path) -> list[Path]:
    return sorted(wurzel.rglob("*.html"))


def _weg_zu_datei(wurzel: Path, weg: str) -> Path:
    """Aus einem Verweis den Ort im gebauten Stand machen."""
    rein = weg.split("#", 1)[0].split("?", 1)[0].strip()
    if rein in ("", "/"):
        return wurzel / "index.html"
    rein = rein.lstrip("/")
    ziel = wurzel / rein
    if ziel.suffix:
        return ziel
    return ziel / "index.html"


def wege_pruefen(wurzel: Path | None = None) -> Befund:
    """Jeder interne Verweis muss auf etwas zeigen, das es gibt."""
    wurzel = wurzel or dist()
    befund = Befund()
    if not wurzel.exists():
        return befund
    befund.gebaut = True

    muster = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']')
    for seite in _seiten(wurzel):
        befund.seiten += 1
        kb = seite.stat().st_size / 1024
        if kb > SEITE_HOECHSTENS_KB:
            befund.schwere_seiten.append(
                {"seite": str(seite.relative_to(wurzel)), "kb": kb})
        text = seite.read_text(encoding="utf-8", errors="ignore")
        for weg in muster.findall(text):
            if FREMD.match(weg) or not weg.startswith("/"):
                continue
            befund.verweise += 1
            if not _weg_zu_datei(wurzel, weg).exists():
                befund.tote_verweise.append(
                    {"von": str(seite.relative_to(wurzel)), "auf": weg})
    return befund


# ------------------------------------------------------------------ Lebend

WICHTIGE_WEGE = ["/", "/app/", "/app/einstellungen/", "/app/trading/",
                 "/intro/", "/credits/", "/impressum/", "/datenschutz/"]


def lebend_pruefen(adresse: str = "https://speedofthespirit.dev",
                   wege: list[str] | None = None) -> list[dict]:
    """Antwortet die veroeffentlichte Seite? Braucht Netz, kostet nichts."""
    import urllib.error
    import urllib.request

    aus = []
    for weg in (wege or WICHTIGE_WEGE):
        anfrage = urllib.request.Request(adresse.rstrip("/") + weg,
                                         headers={"User-Agent": KENNUNG})
        try:
            with urllib.request.urlopen(anfrage, timeout=20) as antwort:
                aus.append({"weg": weg, "stand": str(antwort.status),
                            "gut": 200 <= antwort.status < 300})
        except urllib.error.HTTPError as fehler:
            aus.append({"weg": weg, "stand": str(fehler.code), "gut": False})
        except Exception as fehler:
            aus.append({"weg": weg, "stand": str(fehler)[:60], "gut": False})
    return aus
