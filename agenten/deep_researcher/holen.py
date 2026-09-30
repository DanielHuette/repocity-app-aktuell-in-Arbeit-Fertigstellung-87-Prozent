"""Seite laden und den Haupttext herausschälen — durch das Tor.

Jeder Abruf geht durch die Prüfung: robots.txt, Sperrliste, Bot-Schutz,
Widerspruch gegen Text- und Data-Mining. Wird abgelehnt, gibt es keinen Text,
sondern einen Grund.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern.compliance import Tor  # noqa: E402

WEG = ["script", "style", "nav", "header", "footer", "aside", "form",
       "noscript", "iframe", "svg"]

_TOR = Tor(tagebuch=Path(__file__).resolve().parent.parent / "zustand" / "abgelehnt.jsonl")


def tor() -> Tor:
    return _TOR


def text_holen(url: str, mindestzeichen: int = 800) -> tuple[str, str]:
    """Gibt (Text, Grund) zurück. Ist der Grund gesetzt, ist der Text leer."""
    antwort, grund = _TOR.versuchen(url)
    if antwort is None:
        return "", grund
    text = _herausschaelen(antwort.text)
    if len(text) < mindestzeichen:
        roh = _per_browser(url)
        if roh:
            besser = _herausschaelen(roh)
            if len(besser) > len(text):
                text = besser
    return text, ""


def _per_browser(url: str) -> str:
    """Nur für Seiten, die ihren Text erst im Browser aufbauen."""
    entscheidung = _TOR.darf(url)
    if not entscheidung.allowed:
        return ""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ""
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            seite = browser.new_page(locale="de-DE")
            try:
                seite.goto(url, wait_until="domcontentloaded", timeout=40000)
                seite.wait_for_timeout(1500)
                return seite.content()
            finally:
                browser.close()
    except Exception:
        return ""


def _herausschaelen(html: str) -> str:
    try:
        import trafilatura
        gewonnen = trafilatura.extract(html, include_comments=False, favor_precision=True)
        if gewonnen and len(gewonnen) > 400:
            return _glaetten(gewonnen)
    except Exception:
        pass

    suppe = BeautifulSoup(html, "lxml")
    for name in WEG:
        for knoten in suppe.find_all(name):
            knoten.decompose()

    bester = ""
    for wahl in ("article", "main", "[role=main]", "#content", ".content", "body"):
        for knoten in suppe.select(wahl):
            text = _glaetten(knoten.get_text("\n"))
            if len(text) > len(bester):
                bester = text
        if len(bester) > 1500:
            break
    return bester


def _glaetten(text: str) -> str:
    zeilen = [re.sub(r"[ \t\xa0]+", " ", zeile).strip() for zeile in text.splitlines()]
    behalten = [z for z in zeilen if len(z) > 2]
    zusammen = "\n".join(behalten)
    return re.sub(r"\n{3,}", "\n\n", zusammen).strip()


def titel_holen(html_oder_text: str, ersatz: str) -> str:
    treffer = re.search(r"<title[^>]*>(.*?)</title>", html_oder_text, re.S | re.I)
    return treffer.group(1).strip()[:160] if treffer else ersatz