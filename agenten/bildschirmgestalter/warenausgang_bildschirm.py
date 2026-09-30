# -*- coding: utf-8 -*-
"""Die fertigen Bildschirme in den Warenausgang legen - ein Eintrag je Auftrag,
das Standbild fuer den PC als Hauptdatei, alles andere im Beipackzettel."""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

try:
    import rueckweg
    import warenausgang
    ANGESCHLOSSEN = True
except ImportError:                                        # pragma: no cover
    ANGESCHLOSSEN = False


def einstellen(auftrag_id: str, titel: str, stuecke: list[dict], kosten_usd: float,
               trocken: bool = False) -> str:
    if not ANGESCHLOSSEN or not stuecke:
        return ""
    haupt = stuecke[0]
    weitere = "; ".join("%s: %s%s" % (s["geraet"], Path(s["standbild"]).name,
                                      (" + " + Path(s["film"]).name) if s.get("film") else "")
                        for s in stuecke)
    try:
        eintrag = warenausgang.einstellen(
            was="bildschirmschoner", auftrag=auftrag_id, modul="prod.bildschirmschoner", titel=titel,
            datei=str(haupt["standbild"]), gueteklasse="einfach",
            laenge=", ".join(s["groesse"] for s in stuecke), format_="png+mp4" if any(s.get("film") for s in stuecke) else "png",
            stimme="", bildquellen="gerechnet" if trocken else "fal.ai", kosten=kosten_usd,
            abgenommen_von="bildschirmgestalter", taugt_fuer="Anmelde- und Sperrbildschirm, Bildschirmschoner",
            notiz="Stuecke: " + weitere,
            art=rueckweg.TROCKEN if trocken else rueckweg.ECHT)
        return eintrag["kennung"]
    except Exception:                                      # noqa: BLE001
        return ""
