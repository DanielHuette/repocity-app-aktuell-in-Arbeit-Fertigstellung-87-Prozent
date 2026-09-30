"""RSS und Atom lesen — ohne zusätzliches Paket.

Ein Feed ist der höflichste Weg an neue Beiträge: der Betreiber stellt ihn
bereit, damit er gelesen wird. Ein Rundgang über Feeds erzeugt einen Abruf je
Quelle statt eines Streifzugs über die ganze Seite.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from xml.etree import ElementTree

NAMENSRAEUME = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


@dataclass
class Beitrag:
    titel: str
    url: str
    datum: str
    anriss: str
    quelle: str = ""


def lesen(xml: str, quellenname: str = "") -> list[Beitrag]:
    try:
        wurzel = ElementTree.fromstring(xml.strip())
    except ElementTree.ParseError:
        return []

    beitraege: list[Beitrag] = []
    for eintrag in wurzel.iter():
        marke = eintrag.tag.split("}")[-1]
        if marke not in ("item", "entry"):
            continue
        titel = _text(eintrag, ("title",))
        url = _verweis(eintrag)
        datum = _datum(eintrag)
        anriss = _text(eintrag, ("description", "summary", "content", "encoded"))
        if titel and url:
            beitraege.append(Beitrag(titel=titel, url=url, datum=datum,
                                     anriss=_entkleiden(anriss)[:600],
                                     quelle=quellenname))
    return beitraege


def neuer_als(beitraege: list[Beitrag], tage: int) -> list[Beitrag]:
    grenze = (date.today() - timedelta(days=tage)).isoformat()
    frisch = [b for b in beitraege if not b.datum or b.datum >= grenze]
    return frisch


def _text(knoten, marken: tuple[str, ...]) -> str:
    for kind in knoten.iter():
        if kind.tag.split("}")[-1] in marken and (kind.text or "").strip():
            return (kind.text or "").strip()
    return ""


def _verweis(knoten) -> str:
    for kind in knoten.iter():
        marke = kind.tag.split("}")[-1]
        if marke == "link":
            if kind.get("href"):
                art = kind.get("rel") or "alternate"
                if art == "alternate":
                    return kind.get("href", "")
            if (kind.text or "").strip().startswith("http"):
                return kind.text.strip()
        if marke == "id" and (kind.text or "").strip().startswith("http"):
            return kind.text.strip()
    return ""


def _datum(knoten) -> str:
    roh = _text(knoten, ("pubDate", "published", "updated", "date"))
    if not roh:
        return ""
    for muster in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                   "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(roh.strip(), muster).date().isoformat()
        except ValueError:
            continue
    treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", roh)
    return treffer.group(0) if treffer else ""


def _entkleiden(html: str) -> str:
    ohne = re.sub(r"<[^>]+>", " ", html or "")
    ohne = (ohne.replace("&nbsp;", " ").replace("&amp;", "&")
            .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"'))
    return re.sub(r"\s+", " ", ohne).strip()