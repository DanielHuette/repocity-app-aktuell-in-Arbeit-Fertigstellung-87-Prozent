"""Eingegangene Post, für andere Agenten lesbar.

Der Email-Agent hat die Postfachdaten. Andere Agenten brauchen sie nicht —
sie brauchen den Inhalt. Deshalb schreibt der Email-Agent jede gelesene Mail
hier hinein, und wer sie braucht, holt sie sich.

Der Wohnungsagent nutzt das für die Benachrichtigungen der Portale: bei
ImmobilienScout24 und Immowelt richtet man einen Suchauftrag ein, die Portale
schicken neue Angebote von selbst — und was einem geschickt wird, muss man
nicht holen.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

UNIVERSE = Path(__file__).resolve().parent.parent
DATEI = UNIVERSE / "zustand" / "posteingang.jsonl"
HOECHSTENS = 4000


def merken(von: str, von_name: str, betreff: str, text: str, datum: str = "",
           postfach: str = "", kennung: str = "") -> None:
    satz = {
        "kennung": kennung,
        "postfach": postfach,
        "von": (von or "").lower(),
        "von_name": von_name or "",
        "betreff": betreff or "",
        "text": (text or "")[:20000],
        "datum": datum or datetime.now().isoformat(timespec="seconds"),
        "erfasst_am": date.today().isoformat(),
    }
    try:
        DATEI.parent.mkdir(parents=True, exist_ok=True)
        with DATEI.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps(satz, ensure_ascii=False) + "\n")
    except OSError:
        pass


def lesen(seit_tagen: int = 14, von_enthaelt: list[str] | None = None) -> list[dict]:
    if not DATEI.exists():
        return []
    grenze = (date.today() - timedelta(days=seit_tagen)).isoformat()
    gefunden: list[dict] = []
    with DATEI.open(encoding="utf-8") as datei:
        for zeile in datei:
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                satz = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if satz.get("erfasst_am", "") < grenze:
                continue
            if von_enthaelt:
                absender = satz.get("von", "") + " " + satz.get("von_name", "").lower()
                if not any(teil.lower() in absender for teil in von_enthaelt):
                    continue
            gefunden.append(satz)
    return gefunden[-HOECHSTENS:]