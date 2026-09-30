"""Der Ablauf der Lern-Werkstatt.

    Auftrag ─► Briefing ─► Curriculum ─► ABNAHME durch Daniel
                                              │
                                    Go ───────┴─────── Änderungswunsch
                                     │                      │
                                     ▼                      ▼
                          Erzeugung: Erzähler,        zurück ins Curriculum
                          Animationen, Zusammenbau
                                     │
                                     ▼
                            eine HTML-Datei ─► Vorlage ─► fertig

Die Abnahme in der Mitte ist keine Förmlichkeit. Sie steht dort, weil erst
danach anfängt, was Zeit und Geld kostet — genau wie im Vorbild.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import animation
import curriculum as curr
import einstellungen as e
import erzaehler
import kurs as kursbau
from modelle import Auftrag, Ergebnis, Zustand


def entwerfen(auftrag: Auftrag) -> Ergebnis:
    """Erster Halbschritt: nur das Curriculum. Nichts wird erzeugt."""
    ergebnis = Ergebnis(auftrag=auftrag)
    ordner = e.WERKSTATT / auftrag.id
    ordner.mkdir(parents=True, exist_ok=True)
    try:
        ergebnis.zustand = Zustand.CURRICULUM
        c = curr.entwirf(auftrag)
        ergebnis.curriculum = c
        (ordner / "curriculum.md").write_text(curr.als_text(c), encoding="utf-8", newline="")
        ergebnis.merke(f"Curriculum entworfen: {len(c.level)} Level")
        ergebnis.zustand = (Zustand.WARTET_AUF_ABNAHME if e.CURRICULUM_ABNAHME
                            else Zustand.ERZEUGUNG)
        return ergebnis
    except Exception as fehler:
        ergebnis.zustand = Zustand.FEHLER
        ergebnis.fehler = str(fehler)
        ergebnis.merke("abgebrochen: " + str(fehler))
        return ergebnis


def erzeugen(ergebnis: Ergebnis) -> Ergebnis:
    """Zweiter Halbschritt: nach dem Go. Hier entstehen Medien und Datei."""
    auftrag, c = ergebnis.auftrag, ergebnis.curriculum
    if c is None:
        ergebnis.zustand = Zustand.FEHLER
        ergebnis.fehler = "kein Curriculum"
        return ergebnis

    ordner = e.WERKSTATT / auftrag.id
    medien: dict[int, dict] = {}

    try:
        ergebnis.zustand = Zustand.ERZEUGUNG

        for l in c.level:
            eintrag: dict = {}

            ton = erzaehler.sprich(l.sprechertext, ordner / f"level{l.nr}_stimme.mp3")
            if ton:
                eintrag["ton"] = ton
                ergebnis.merke(f"Level {l.nr}: Erzähler aufgenommen")

            if e.HYPERFRAMES_AN:
                punkte = [z.strip() for z in l.lehrtext.split("\n") if z.strip()][:4]
                szene = animation.szene(l.titel, punkte, l.bild_hinweis)
                film = animation.baue(szene, ordner / f"level{l.nr}.mp4")
                if film:
                    eintrag["video"] = film
                    ergebnis.merke(f"Level {l.nr}: Animation gebaut")

            if eintrag:
                medien[l.nr] = eintrag

        ergebnis.zustand = Zustand.ZUSAMMENBAU
        ziel = ordner / "kurs.html"
        kursbau.baue(c, auftrag.id, ziel, medien)

        e.AUSGABE.mkdir(parents=True, exist_ok=True)
        endgueltig = e.AUSGABE / f"{auftrag.id}_{_sauber(c.titel)}.html"
        shutil.copy2(ziel, endgueltig)
        if (ziel.parent / "medien").exists():
            shutil.copytree(ziel.parent / "medien", e.AUSGABE / "medien", dirs_exist_ok=True)

        ergebnis.kurs = endgueltig
        ergebnis.zustand = Zustand.VORLAGE
        groesse = endgueltig.stat().st_size / 1024
        ergebnis.merke(f"Kurs gebaut: eine Datei, {groesse:.0f} KB")
        return ergebnis

    except Exception as fehler:
        ergebnis.zustand = Zustand.FEHLER
        ergebnis.fehler = str(fehler)
        ergebnis.merke("abgebrochen: " + str(fehler))
        return ergebnis


def produzieren(auftrag: Auftrag) -> Ergebnis:
    """Beide Halbschritte am Stueck — fuer den Trockenlauf und den Fall,
    dass die Abnahme abgeschaltet ist."""
    ergebnis = entwerfen(auftrag)
    if ergebnis.zustand in (Zustand.FEHLER,):
        return ergebnis
    if ergebnis.zustand == Zustand.WARTET_AUF_ABNAHME and e.CURRICULUM_ABNAHME and not auftrag.trocken:
        return ergebnis
    return erzeugen(ergebnis)


def _sauber(text: str) -> str:
    erlaubt = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    klein = (text.lower().replace(" ", "-").replace("ä", "ae").replace("ö", "oe")
                 .replace("ü", "ue").replace("ß", "ss"))
    return "".join(z for z in klein if z in erlaubt)[:40] or "kurs"
