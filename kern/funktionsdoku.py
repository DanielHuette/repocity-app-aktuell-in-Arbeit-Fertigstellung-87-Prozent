# -*- coding: utf-8 -*-
"""Erzeugt die Funktionsdokumentation aus universe/funktionen.json.

    python universe\\kern\\funktionsdoku.py            FUNKTIONSDOKUMENTATION.md neu schreiben
    python universe\\kern\\funktionsdoku.py pruefen    steht die Datei auf dem letzten Stand?
    python universe\\kern\\funktionsdoku.py soll <id>  die Sollwerte einer Funktion, als JSON

Warum erzeugt und nicht von Hand geschrieben: die Zeiten und Kosten sind
gleichzeitig Dokumentation, Sollwert für die Messung und Grenze im Prüfstand.
Stünden sie an zwei Stellen, liefen sie auseinander – genau das ist am 06.09.
bei den Bildpreisen passiert. Sie stehen deshalb nur in funktionen.json.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

UNIVERSE = Path(__file__).resolve().parent.parent
WURZEL = UNIVERSE.parent
QUELLE = UNIVERSE / "funktionen.json"
ZIEL = WURZEL / "FUNKTIONSDOKUMENTATION.md"

#: Wo die Ablaufbilder liegen und in welchem Design das feste Bild gebaut
#: wird. Erzeugt werden sie von mein_ki_gehirn/bilder/diagramme/
#: funktionsdiagramm.py - aus derselben funktionen.json, damit Bild und Text
#: nicht auseinanderlaufen koennen.
BILDER = "mein_ki_gehirn/bilder/diagramme"
#: Und derselbe Ablauf als Film - gebaut von universe/gestalter/filmweg.mjs.
FILME = "mein_ki_gehirn/filme"
BILD_KIT = "rechenwerk"

#: Was in dieser Datei nichts zu suchen hat - von Daniel am 15.09.2026
#: benannt. Die Sperre laeuft ueber den fertigen Text, bevor er geschrieben
#: wird, und bricht ab, sobald eines davon wieder auftaucht. Sie steht hier,
#: weil sich so ein Satz beim Schreiben jedes Mal richtig anfuehlt: er
#: erklaert, wie sorgfaeltig gearbeitet wurde. Nur liest das niemand, der
#: wissen will, was passiert, wenn er einen Schalter umlegt.
SPERRE = (
    ("Diese Datei wird erzeugt", "Hinweis auf den eigenen Erzeuger"),
    ("Neu bauen:", "Bauanleitung"),
    ("Erzeugt aus derselben Quelle", "Hinweis auf die eigene Quelle"),
    ("Aus derselben Quelle wie Text und Bild", "Hinweis auf die eigene Quelle"),
    ("Die Bahnen sind die Orte", "Erklaerung des eigenen Bildes"),
    ("Wozu diese Datei da ist", "Vorwort ueber sich selbst"),
    ("Drei Leser, ein Text", "Vorwort ueber sich selbst"),
    ("Das Signal läuft die Schiene entlang", "Beschreibung des eigenen Films"),
    ("Was noch fehlt", "Baustellenliste"),
    ("Geraten statt gemessen", "Baustellenliste"),
    ("nicht scharf geschaltet", "Baustellenliste"),
    ("nicht verhandelbar", "Vermerk an einer Grenze"),
    ("Von Daniel am", "Herkunftsvermerk"),
    ("Was sie auslöst", "Abschnitt, den Daniel entfernt hat"),
    ("Was ausdrücklich nicht passiert", "Abschnitt, den Daniel entfernt hat"),
    ("Drei Wege hinein", "Abschnitt, den Daniel entfernt hat"),
    ("| Kostentopf |", "Kennungstabelle"),
    ("Stand: 20", "Datumszeile im Kopf"),
)


def zeit(ms: float) -> str:
    """Millisekunden lesbar – so genau wie nötig, nicht genauer."""
    if ms < 1:
        return f"{ms:.3f}".rstrip("0").rstrip(".").replace(".", ",") + " ms"
    if ms < 1000:
        return f"{ms:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " ms"
    sekunden = ms / 1000
    if sekunden < 10:
        return f"{sekunden:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " Sek"
    return f"{sekunden:.0f} Sek"


def spanne(von: float, bis: float) -> str:
    return zeit(von) if von == bis else f"{zeit(von)} – {zeit(bis)}"


def euro(betrag: float) -> str:
    if betrag == 0:
        return "0,00 €"
    if betrag < 0.01:
        return f"{betrag:.5f}".replace(".", ",") + " €"
    return f"{betrag:.2f}".replace(".", ",") + " €"


def laden() -> dict:
    return json.loads(QUELLE.read_text(encoding="utf-8"))


def sollwerte(kennung: str) -> dict:
    """Was eine Messung erreichen muss. Nur unsere Schritte – Netz zählt nicht mit."""
    funktion = laden()["funktionen"][kennung]
    unser = [s for s in funktion["schritte"] if s["unser_teil"]]
    neben = funktion.get("nebenlaeufig", [])
    return {
        "funktion": kennung,
        "schritte": {s["name"]: {"von_ms": s["soll_ms"]["von"],
                                 "bis_ms": s["soll_ms"]["bis"],
                                 "schlimmstenfalls_ms": s["schlimmstenfalls_ms"],
                                 "herkunft": s["herkunft"]} for s in unser},
        "gesamt_von_ms": round(sum(s["soll_ms"]["von"] for s in unser), 3),
        "gesamt_bis_ms": round(sum(s["soll_ms"]["bis"] for s in unser), 3),
        "gesamt_schlimmstenfalls_ms": round(sum(s["schlimmstenfalls_ms"] for s in unser), 3),
        "kosten_je_lauf_eur": round(sum(s["kosten_eur"] for s in unser), 5),
        "kosten_mit_nebenlaeufigem_eur": round(
            sum(s["kosten_eur"] for s in unser) + sum(n["kosten_eur"] for n in neben), 5),
    }


def geschaetzte_schritte(funktion: dict) -> list[str]:
    """Unsere Schritte, deren Zeit noch geraten ist. Sperrt die Scharfschaltung."""
    return [s["name"] for s in funktion["schritte"]
            if s["unser_teil"] and s["herkunft"] == "geschätzt"]


def _funktion_schreiben(kennung: str, f: dict) -> list[str]:
    z: list[str] = []
    a = z.append
    a(f"## {f['name']}")
    a("")
    # Zuerst das Bild, dann der Text: wer die Seite aufschlaegt, soll die
    # Struktur sehen, bevor er liest (Daniel, 10.09.). Jede Kette waehlt ihr
    # eigenes Design - gesucht wird, was da ist.
    bild = f"{BILDER}/ablauf-{kennung}-{BILD_KIT}.svg"
    if not (WURZEL / bild).exists():
        gefunden = sorted((WURZEL / BILDER).glob(f"ablauf-{kennung}-*.svg"))
        gefunden = [g for g in gefunden if not g.name.endswith("-rohling.svg")]
        if gefunden:
            bild = f"{BILDER}/{gefunden[0].name}"
    if (WURZEL / bild).exists():
        a(f"![Ablauf: {f['name']}]({bild})")
        a("")
    a(f"**Wozu.** {f['zweck']}")
    a("")
    if f.get("warum_tempo"):
        a(f"**Warum das Tempo zählt.** {f['warum_tempo']}")
        a("")

    if f.get("bauweise"):
        b = f["bauweise"]
        a("### Wie sie gebaut ist")
        a("")
        a("| Rolle | wo | tut was | schläft? |")
        a("|---|---|---|---|")
        for r in b["rollen"]:
            a(f"| **{r['rolle']}** | {r['wo']} | {r['tut']} | "
              f"{'ja, bis der Weckruf kommt' if r['schlaeft'] else 'nein, nie'} |")
        a("")
        a(f"**Warum geteilt:** {b['warum_geteilt']}")
        a("")

    if False:  # Der Zubringer-Teil steht nicht mehr in der Doku (Daniel, 15.09.2026).
        zub = f["zubringer"]
        a("### Drei Wege hinein, ein Mittelteil")
        a("")
        a(zub["_hinweis"])
        a("")
        a("| | Weg | wie lange | Herkunft | für welche Quellen |")
        a("|---|---|---|---|---|")
        for k in sorted(x for x in zub if not x.startswith("_")):
            e = zub[k]
            fuer = ", ".join(e.get("fuer") or []) or "*noch keine*"
            a(f"| **{k}** | **{e['name']}** | "
              f"{spanne(e['soll_ms']['von'], e['soll_ms']['bis'])} | "
              f"{e['herkunft']} | {fuer} |")
        a("")
        for k in sorted(x for x in zub if not x.startswith("_")):
            e = zub[k]
            a(f"**{k} — {e['name']}.** {e['was']}")
            a("")
            if e.get("nie_fuer"):
                a(f"> Nicht für: {', '.join(e['nie_fuer'])}")
                a("")
            if e.get("nur_android"):
                a("> Nur auf Android.")
                a("")
            if e.get("hinweis_nutzer"):
                a(f"> **Für den Nutzer:** {e['hinweis_nutzer']}")
                a("")

            if e.get("rueckweg"):
                r = e["rueckweg"]
                a(f"> **Der R\u00fcckweg.** {r['was']}")
                a(">")
                a(f"> {r['nur_bestaetigte_kanaele']}")
                a(">")
                a(f"> Zeit: {spanne(r['soll_ms']['von'], r['soll_ms']['bis'])}. "
                  f"Herkunft: **{r['herkunft']}** \u2014 {r['quelle']}")
                a(">")
                a("> Code: " + ", ".join(f"`{c}`" for c in r["code"]))
                a(">")
                a(f"> Gepr\u00fcft mit: {r['pruefung']}")
                a("")

    if f.get("tore"):
        tor = f["tore"]
        a("### Die drei Tore vor dem Absenden")
        a("")
        a(tor["_hinweis"])
        a("")
        a("| Tor | Frage | fällt es durch | womit geprüft wird |")
        a("|---|---|---|---|")
        for k in sorted(x for x in tor if not x.startswith("_")):
            e = tor[k]
            a(f"| **{k}. {e['name']}** | {e['frage']} | {e['faellt_durch']} | "
              f"{e['womit']} |")
        a("")

    if f.get("gutes_gesuch"):
        g = f["gutes_gesuch"]
        a("### Was in eine Anfrage gehört")
        a("")
        for zeile in g["aufbau"]:
            a(f"- {zeile}")
        a("")
        a(f"**Länge:** {g['laenge']}")
        a("")
        a(f"**Worauf es ankommt.** {g['worauf_es_ankommt']}")
        a("")
        a(f"*Quelle: {g['beleg']}*")
        a("")

    if f.get("nachweise"):
        n = f["nachweise"]
        a("### Wo RepoCity aufhört")
        a("")
        a(f"**RepoCity:** {n['was_repocity_tut']}")
        a("")
        a(f"**Der Nutzer:** {n['was_der_nutzer_tut']}")
        a("")
        a(f"> In der App steht dazu: „{n['hinweis_in_der_app']}“")
        a("")

    if f.get("wachhund"):
        w = f["wachhund"]
        a("### Der Wachhund")
        a("")
        a(f"**Was passiert:** {w['was']}")
        a("")

    if f.get("einrichtungsassistent"):
        ea = f["einrichtungsassistent"]
        a("### Der Einrichtungsassistent")
        a("")
        a(ea["_hinweis"])
        a("")
        a("| # | Punkt | was der Test feststellt |")
        a("|---|---|---|")
        for punkt in ea["punkte"]:
            a(f"| {punkt['nr']} | **{punkt['titel']}** | {punkt['test']} |")
        a("")
        a(f"*Code: `{ea['code']}`*")
        a("")

    if f.get("eigene_quellen"):
        eq = f["eigene_quellen"]
        a("### Eigene Quellen hinzufügen")
        a("")
        a(eq["_hinweis"])
        a("")
        for i, schritt in enumerate(eq["weg"], 1):
            a(f"{i}. {schritt}")
        a("")
        a(f"**Was eine Erkundung kostet:** {euro(eq['kosten_je_erkundung_eur'])} — "
          f"{eq['kosten_rechnung']}")
        a("")
        a(f"*Code: `{eq['code']}`*")
        a("")

    if f.get("einrichtung"):
        a("### Was der Nutzer einmal einrichtet")
        a("")
        a("| # | Was | Warum |")
        a("|---|---|---|")
        for e in f["einrichtung"]:
            a(f"| {e['nr']} | {e['was']} | {e['warum']} |")
        a("")

    a("### Der Ablauf mit Uhr")
    a("")
    a("| # | Schritt | wo | Zeit | Herkunft | Kosten |")
    a("|---|---|---|---|---|---|")
    for s in f["schritte"]:
        name = s["name"] if s["unser_teil"] else s["name"] + " *(außerhalb)*"
        a(f"| {s['nr']} | **{name}** | {s['wo']} | "
          f"{spanne(s['soll_ms']['von'], s['soll_ms']['bis'])} | {s['herkunft']} | "
          f"{euro(s['kosten_eur'])} |")
    soll = sollwerte(kennung)
    a(f"| | **gesamt, unser Teil** | | "
      f"**{spanne(soll['gesamt_von_ms'], soll['gesamt_bis_ms'])}** | | "
      f"**{euro(soll['kosten_je_lauf_eur'])}** |")
    a(f"| | schlimmstenfalls | | {zeit(soll['gesamt_schlimmstenfalls_ms'])} | | |")
    a("")

    # Derselbe Ablauf, aber laufend: die Seite spielt ihn ab, der Film hält ihn fest.
    seite = f"universe/gestalter/filmbrett/compositions/ablauf-{kennung}.html"
    film = f"{FILME}/ablauf-{kennung}.mp4"
    if (WURZEL / seite).exists():
        a("### Derselbe Ablauf als Film")
        a("")
        if (WURZEL / film).exists():
            groesse = (WURZEL / film).stat().st_size / 1024 / 1024
            a(f"[Film ansehen]({film}) — {groesse:.1f} MB")
        else:
            a("Die Seite steht, der Film ist noch nicht gerechnet.")
        a("")

    a("Was in jedem Schritt passiert:")
    a("")
    for s in f["schritte"]:
        a(f"**{s['nr']}. {s['name']}** — {s['was']}")
        a("")
        a(f"> Zeit: {spanne(s['soll_ms']['von'], s['soll_ms']['bis'])}, "
          f"schlimmstenfalls {zeit(s['schlimmstenfalls_ms'])}. "
          f"Herkunft: **{s['herkunft']}** — {s['quelle']}")
        if s["kosten_eur"]:
            a(">")
            a(f"> Kosten: {euro(s['kosten_eur'])}. {s['kosten_rechnung']}")
        if s.get("code"):
            a(">")
            a(f"> Code: `{s['code']}`")
        a("")
        if s.get("empfang"):
            emp = s["empfang"]
            a(f"> **Wo der Ruf ankommt.** {emp['was']}")
            a(">")
            a(f"> {emp['not_aus']}")
            a(">")
            a(f"> **Zugang:** {emp['zugang']}")
            a(">")
            a(f"> **Gemessen statt gesch\u00e4tzt:** {emp['messung']}")
            a(">")
            a("> Code: " + ", ".join(f"`{c}`" for c in emp["code"]))
            a(">")
            a(f"> Gepr\u00fcft mit: {emp['pruefung']}")
            a("")

    if f.get("nebenlaeufig"):
        a("### Was nebenher läuft")
        a("")
        for n in f["nebenlaeufig"]:
            a(f"**{n['name']}** ({n['wo']}) — {n['was']}")
            a("")
            a(f"> Zeit: {spanne(n['soll_ms']['von'], n['soll_ms']['bis'])}. "
              f"Herkunft: **{n['herkunft']}** — {n['quelle']}")
            a(">")
            a(f"> Kosten: {euro(n['kosten_eur'])}. {n['kosten_rechnung']}")
            a(">")
            a(f"> Verlängert die Kette: {'ja' if n['verlaengert_die_kette'] else 'nein'}. "
              f"Abschaltbar: {'ja' if n['abschaltbar'] else 'nein'}.")
            a("")

    if f.get("kosten"):
        k = f["kosten"]
        a("### Was sie kosten darf")
        a("")
        a("**Das entscheidet der Nutzer.** RepoCity setzt hier keine Grenze; die "
          "Zahlen oben sind gemessene Preise zum Anzeigen, keine Deckel.")
        a("")
        a("| | |")
        a("|---|---|")
        a(f"| Schlüssel für die eigene Marke | `{k['bremse_schluessel']}` |")
        a(f"| In der App einstellbar | {'ja' if k['einstellbar_in_der_app'] else 'nein'} |")
        a(f"| Voreinstellung | {k['voreinstellung']} |")
        a("")
        a("Was die App zeigt:")
        a("")
        for zeile in k.get("was_die_app_zeigt", []):
            a(f"- {zeile}")
        a("")
        a("Hat der Nutzer eine Marke gesetzt, gilt: **Warnung bei 80 %, Stopp am "
          "Wert, ein angefangener Lauf wird fertig, beim Doppelten der Lauf-Marke "
          "bricht auch der ab.**")
        a("")

    if f.get("grenzen"):
        a("### Grenzen")
        a("")
        for g in f["grenzen"]:
            a(f"**{g['nr']}. {g['regel']}**")
            a("")
            a(g["was"])
            a("")

    if f.get("belege"):
        a("### Belege")
        a("")
        a("| Was | Quelle |")
        a("|---|---|")
        for b in f["belege"]:
            a(f"| {b['was']} | {b['quelle']} |")
        a("")

    a("---")
    a("")
    return z


def sperre_pruefen(text: str) -> None:
    """Haelt draussen, was Daniel am 15.09.2026 hier entfernt hat.

    Sie bricht ab, statt zu melden: eine Warnung, die nur im Protokoll steht,
    liest beim naechsten Lauf niemand - und dann steht es wieder drin.
    """
    getroffen = [(w, warum) for w, warum in SPERRE if w in text]
    if getroffen:
        raise SystemExit(
            "Die Funktionsdokumentation traegt wieder, was nicht hineingehoert:\n"
            + "\n".join("  %-42s %s" % ("\"%s\"" % w, warum) for w, warum in getroffen)
            + "\n\nEntweder steht es im Erzeuger (kern/funktionsdoku.py) oder in\n"
              "universe/funktionen.json. Dort gehoert es weg, nicht die Sperre.")


def markdown() -> str:
    daten = laden()
    z: list[str] = []
    a = z.append
    a("# RepoCity — Funktionsdokumentation")
    a("")
    a("## Wie eine Zeit hier zustande kommt")
    a("")
    a("| Herkunft | heißt |")
    a("|---|---|")
    for k, v in daten["_herkunft_der_zeiten"].items():
        a(f"| **{k}** | {v} |")
    a("")
    a("## Was eine Funktion kosten darf")
    a("")
    a(daten["_kostenbremse"])
    a("")
    a("### Die Nutzerbremse")
    a("")
    a("**80 %:** „Du hast 8 von 10 € verbraucht.“ Es läuft weiter, nichts wird "
      "angehalten.")
    a("")
    a("**Die Marke erreicht:** Die nächste Produktion startet nicht und sagt "
      "warum: „Angehalten, weil deine Marke von 10 € erreicht ist.“ Was schon "
      "läuft, wird fertig.")
    a("")
    a("**Der Nutzer entscheidet:** Marke hochsetzen, Marke lösen — dann läuft es "
      "sofort weiter.")
    a("")
    a("Das ist der einzige Ort, an dem RepoCity wegen Geld etwas anhält. Es gibt "
      "keine Grenze, die jemand anderes gesetzt hat, und keine Freigabe, auf die "
      "gewartet werden muss.")
    a("")
    a("## Was erfasst ist")
    a("")
    a("| Funktion | Art | Modul | Stand | Zeit, unser Teil | Kosten je Lauf |")
    a("|---|---|---|---|---|---|")
    for kennung, f in daten["funktionen"].items():
        soll = sollwerte(kennung)
        kosten = euro(soll["kosten_je_lauf_eur"])
        if soll["kosten_mit_nebenlaeufigem_eur"] != soll["kosten_je_lauf_eur"]:
            kosten += f" (mit Zusatz {euro(soll['kosten_mit_nebenlaeufigem_eur'])})"
        anker = f["name"].lower().replace(" ", "-")
        a(f"| [{f['name']}](#{anker}) | {f['art']} | `{f['modul']}` | {f['stand']} | "
          f"{spanne(soll['gesamt_von_ms'], soll['gesamt_bis_ms'])} | {kosten} |")
    a("")
    a("---")
    a("")
    for kennung, f in daten["funktionen"].items():
        z.extend(_funktion_schreiben(kennung, f))
    fertig = "\n".join(z)
    sperre_pruefen(fertig)
    return fertig



# ---------------------------------------------------------------------------
#  DIE WEBSEITE BEKOMMT DIESELBE ERKLAERUNG
#
#  Der Nutzer soll nachlesen koennen, wie RepoCity arbeitet - im Streitfall
#  wie aus Neugier. Damit App, Dokument und Webseite nicht auseinanderlaufen,
#  wird die HTML-Fassung HIER erzeugt, aus demselben Text. Zwei Renderer
#  waeren zwei Wahrheiten.
# ---------------------------------------------------------------------------

HTML_ZIEL = WURZEL / "universe" / "webseite" / "src" / "daten" / "funktionsdokumentation.html"


def _zeichen(s: str) -> str:
    """Erst entschaerfen, dann die eigenen Auszeichnungen einsetzen."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    # Bilder zuerst - sonst wird aus einem Bild ein Link mit Ausrufezeichen.
    # Auf der Webseite steht statt des festen Bildes die anfassbare Fassung
    # (ablauf-<kennung>.html): dunkel, die Pfeile laufen, dauerhaft - so wie
    # Daniel sie am 10.09. verlangt hat. Der Rahmen bekommt das
    # Seitenverhaeltnis des Bildes, damit die Seite beim Laden nicht springt;
    # die genaue Hoehe meldet die Fassung danach selbst (postMessage).
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: _ablauf_rahmen(
        m.group(2).rsplit("/", 1)[-1], m.group(1)), s)
    # Der Film wird auf der Seite nicht verlinkt, sondern gezeigt. Ohne Ton,
    # in Endlosschleife, ohne Vorabladen - siebzehn Filme auf einer Seite
    # duerfen nicht siebzehnmal Datenvolumen kosten, bevor jemand hinsieht.
    s = re.sub(r"\[Film ansehen\]\(([^)]+)\)",
               lambda m: ('<video src="/filme/%s" controls loop muted '
                          'playsinline preload="none" '
                          'style="width:100%%;border-radius:10px"></video>'
                          % m.group(1).rsplit("/", 1)[-1]), s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def _ablauf_rahmen(bildname: str, alt: str) -> str:
    """Der Rahmen, in dem die anfassbare Fassung auf der Webseite laeuft."""
    kennung = bildname.rsplit("-", 1)[0]            # ablauf-video-rechenwerk.svg -> ablauf-video
    seite = WURZEL / BILDER / f"{kennung}.html"
    if not seite.exists():
        return '<img src="/diagramme/%s" alt="%s" loading="lazy" />' % (bildname, alt)
    breite, hoehe = _seitenverhaeltnis(seite)
    return ('<div class="ablauf-rahmen" style="aspect-ratio: %d / %d">'
            '<iframe src="/diagramme/%s.html?theme=dark" title="%s" '
            'loading="lazy" scrolling="no"></iframe></div>'
            % (breite, hoehe, kennung, alt))


def _seitenverhaeltnis(seite: Path) -> tuple[int, int]:
    """Breite und Hoehe des Bildes in der Fassung - aus dem viewBox gelesen."""
    kopf = seite.read_text(encoding="utf-8")
    m = re.search(r'<svg[^>]*viewBox="0 0 (\d+)(?:\.\d+)? (\d+)(?:\.\d+)?"', kopf)
    if not m:
        return (16, 10)
    # Der Rahmen um das Bild (Innenabstand 0,6rem oben und unten, gerechnet
    # mit 16px) kommt dazu, sonst wird die Hoehe zu knapp und es blitzt.
    return (int(m.group(1)), int(m.group(2)) + 20)


#: Was in jede Kopie der anfassbaren Fassung fuer die Webseite gesetzt wird:
#: Werkzeugleiste und Nebenfenster weg, nur das Bild; die Pfeile laufen
#: dauerhaft, auch wenn jemand hineinklickt (kein Klick erreicht das Bild);
#: und die Fassung meldet ihre Hoehe an die Seite, die sie einbettet.
EINBETTUNG = """<style id="repocity-einbettung">
  .toolbar, .header, .cards, .diagram-nav, .overview-map, .focus-chip, .route-probe,
  .semantic-lens, .diagram-guide, .node-finder, .guided-views, .share-chapter-cue,
  .intent-trace-status, .overview-map-feedback { display: none !important; }
  html, body { height: auto !important; min-height: 0 !important; padding: 0 !important;
    margin: 0 !important; overflow: hidden !important; background-image: none !important; }
  .container { max-width: none !important; height: auto !important; gap: 0 !important; }
  .diagram-container { padding: 0.6rem !important; border-radius: 0.75rem !important;
    --archify-nav-reserve: 0px !important; }
  .diagram-container > svg { width: 100% !important; height: auto !important; pointer-events: none; }
  /* Die Pfeile laufen dauerhaft - unabhaengig davon, was das Werkzeug sonst
     anhaelt (Ruhig-Schalter, Fokus, Einbettung, Blatt im Hintergrund). */
  #repocity svg[data-animation="trace"] [data-animate="edge"] {
    stroke-dasharray: 10 8 !important;
    animation: repocity-fluss 1.4s linear infinite !important;
    animation-delay: calc(var(--step, 0) * -160ms) !important;
    opacity: 1 !important;
  }
  @keyframes repocity-fluss { from { stroke-dashoffset: 36; } to { stroke-dashoffset: 0; } }
</style>
<script id="repocity-einbettung-skript">
  (function () {
    document.documentElement.id = "repocity";
    function melde() {
      try {
        var h = document.documentElement.scrollHeight;
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ repocity: "ablauf", hoehe: h }, "*");
        }
      } catch (e) {}
    }
    window.addEventListener("load", function () { melde(); setTimeout(melde, 400); });
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(melde).observe(document.documentElement);
    }
  })();
</script>
"""


def _fassung_einbetten(quelle: Path, ziel: Path) -> None:
    """Die anfassbare Fassung mit dem Einbettungsblock neben die Seite legen."""
    text = quelle.read_text(encoding="utf-8")
    if "</head>" in text:
        text = text.replace("</head>", EINBETTUNG + "</head>", 1)
    ziel.write_text(text, encoding="utf-8", newline="\n")


def _felder(zeile: str) -> list:
    return [x.strip() for x in zeile.strip().strip("|").split("|")]


#: Zeichen, die in einer Sprungmarke stehen duerfen. Alles andere wird zum
#: Bindestrich. Absichtlich streng: eine Marke landet in einer Adresse, und
#: was dort umgeschrieben werden muss, ist keine Marke mehr.
_UMLAUTE = {"\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue", "\u00df": "ss",
            "\u00c4": "ae", "\u00d6": "oe", "\u00dc": "ue"}


def marke(text: str) -> str:
    """Aus einer Ueberschrift eine Sprungmarke machen.

    Sie muss zweierlei koennen: in einer Adresse stehen, ohne umgeschrieben zu
    werden, und beim naechsten Lauf wieder genau dieselbe sein. Darum wird sie
    aus dem Text gerechnet und nirgends von Hand gepflegt - eine von Hand
    gepflegte Liste laeuft irgendwann neben den Ueberschriften her.
    """
    s = text.strip()
    s = re.sub(r"<[^>]+>", "", s)          # Auszeichnungen zaehlen nicht mit
    s = re.sub(r"[`*_]", "", s)
    for a, b in _UMLAUTE.items():
        s = s.replace(a, b)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "abschnitt"


def html() -> str:
    zeilen = markdown().splitlines()
    aus = []
    vergeben: dict[str, int] = {}
    i = 0
    while i < len(zeilen):
        z = zeilen[i]
        nackt = z.strip()

        if not nackt:
            i += 1
            continue

        if nackt == "---":
            aus.append("<hr />")
            i += 1
            continue

        if nackt.startswith("#"):
            stufe = len(nackt) - len(nackt.lstrip("#"))
            roh_titel = nackt[stufe:].strip()
            # Sprungmarke: ohne sie kann der Wegweiser nur auf die Seite
            # zeigen, nicht auf den Absatz - und "hier steht es irgendwo auf
            # 98.000 Zeichen" ist keine Antwort. Zwei gleiche Ueberschriften
            # ("Was sie ausloest" steht bei jeder Strasse) bekommen eine
            # laufende Nummer, damit keine Marke zweimal vorkommt.
            m = marke(roh_titel)
            vergeben[m] = vergeben.get(m, 0) + 1
            if vergeben[m] > 1:
                m = "%s-%d" % (m, vergeben[m])
            aus.append('<h%d id="%s">%s</h%d>'
                       % (stufe, m, _zeichen(roh_titel), stufe))
            i += 1
            continue

        trenner = (
            i + 1 < len(zeilen)
            and zeilen[i + 1].strip().startswith("|")
            and set(zeilen[i + 1].strip().replace("|", "").replace(" ", "")) <= {"-", ":"}
        )
        if nackt.startswith("|") and trenner:
            aus.append('<div class="tabelle-rahmen"><table>')
            aus.append("<thead><tr>" + "".join(
                "<th>%s</th>" % _zeichen(x) for x in _felder(z)) + "</tr></thead><tbody>")
            i += 2
            while i < len(zeilen) and zeilen[i].strip().startswith("|"):
                aus.append("<tr>" + "".join(
                    "<td>%s</td>" % _zeichen(x) for x in _felder(zeilen[i])) + "</tr>")
                i += 1
            aus.append("</tbody></table></div>")
            continue

        if nackt.startswith(">"):
            teile = []
            while i < len(zeilen) and zeilen[i].strip().startswith(">"):
                inhalt = zeilen[i].strip()[1:].strip()
                teile.append(_zeichen(inhalt) if inhalt else "<br /><br />")
                i += 1
            aus.append("<blockquote>" + " ".join(teile) + "</blockquote>")
            continue

        if nackt.startswith("- ") or nackt.startswith("* "):
            aus.append("<ul>")
            while i < len(zeilen) and (
                zeilen[i].strip().startswith("- ") or zeilen[i].strip().startswith("* ")
            ):
                aus.append("<li>%s</li>" % _zeichen(zeilen[i].strip()[2:]))
                i += 1
            aus.append("</ul>")
            continue

        # Nummerierte Aufzaehlung
        if re.match(r"^\d+\. ", nackt):
            aus.append("<ol>")
            while i < len(zeilen) and re.match(r"^\d+\. ", zeilen[i].strip()):
                aus.append("<li>%s</li>" % _zeichen(
                    re.sub(r"^\d+\. ", "", zeilen[i].strip())))
                i += 1
            aus.append("</ol>")
            continue

        # Ein Absatz ist im Quelltext hart umbrochen. Wer jede Zeile einzeln
        # setzt, bekommt eine Seite aus Einzeilern - also zusammenfassen, bis
        # eine Leerzeile oder etwas Besonderes kommt.
        absatz = []
        while i < len(zeilen):
            w = zeilen[i].strip()
            if not w or w == "---" or w.startswith(("#", "|", ">", "- ", "* ")):
                break
            if re.match(r"^\d+\. ", w) and absatz:
                break
            absatz.append(w)
            i += 1
        # Ein Bild allein ist kein Absatz: der Rahmen darum ist ein Block,
        # und ein Block in einem <p> laesst den Browser das <p> zerreissen.
        if len(absatz) == 1 and absatz[0].startswith("!["):
            aus.append(_zeichen(absatz[0]))
        else:
            aus.append("<p>%s</p>" % _zeichen(" ".join(absatz)))

    return "\n".join(aus) + "\n"


def bilder_fuer_webseite() -> int:
    """Die Ablaufbilder gehoeren neben die Seite, sonst zeigt sie leere Rahmen."""
    ziel = WURZEL / "universe" / "webseite" / "public" / "diagramme"
    ziel.mkdir(parents=True, exist_ok=True)
    anzahl = 0
    for quelle in (WURZEL / BILDER).glob("ablauf-*.svg"):
        (ziel / quelle.name).write_bytes(quelle.read_bytes())
        anzahl += 1
    # Und die anfassbaren Fassungen - sie sind es, die die Seite zeigt.
    for quelle in (WURZEL / BILDER).glob("ablauf-*.html"):
        _fassung_einbetten(quelle, ziel / quelle.name)
        anzahl += 1
    return anzahl


def filme_fuer_webseite() -> int:
    """Die Filme gehoeren neben die Seite, sonst zeigt sie leere Abspieler."""
    ziel = WURZEL / "universe" / "webseite" / "public" / "filme"
    ziel.mkdir(parents=True, exist_ok=True)
    quelle_ordner = WURZEL / FILME
    if not quelle_ordner.exists():
        return 0
    anzahl = 0
    for quelle in quelle_ordner.glob("ablauf-*.mp4"):
        (ziel / quelle.name).write_bytes(quelle.read_bytes())
        anzahl += 1
    return anzahl


def html_schreiben() -> str:
    inhalt = html()
    HTML_ZIEL.parent.mkdir(parents=True, exist_ok=True)
    with HTML_ZIEL.open("w", encoding="utf-8", newline="\n") as datei:
        datei.write(inhalt)
    return inhalt

def schreiben() -> int:
    text = markdown()
    with ZIEL.open("w", encoding="utf-8", newline="\n") as datei:
        datei.write(text)
    print(f"geschrieben: {ZIEL} ({len(text)} Zeichen)")
    fassung = html_schreiben()
    print(f"geschrieben: {HTML_ZIEL} ({len(fassung)} Zeichen)")
    anzahl = bilder_fuer_webseite()
    print(f"gespiegelt: {anzahl} Ablaufbilder in die Webseite")
    filme = filme_fuer_webseite()
    print(f"gespiegelt: {filme} Filme in die Webseite")
    return 0


def pruefen() -> int:
    if not ZIEL.exists():
        print("FEHLT: FUNKTIONSDOKUMENTATION.md wurde nie erzeugt.")
        return 1
    def ohne_datum(t: str) -> str:
        return "\n".join(z for z in t.splitlines() if not z.startswith("Stand: "))
    if ohne_datum(ZIEL.read_text(encoding="utf-8")) != ohne_datum(markdown()):
        print("VERALTET: FUNKTIONSDOKUMENTATION.md passt nicht zu funktionen.json.")
        print("  python universe\\kern\\funktionsdoku.py")
        return 1
    if not HTML_ZIEL.exists():
        print("FEHLT: die Fassung für die Webseite wurde nie erzeugt.")
        return 1
    if HTML_ZIEL.read_text(encoding="utf-8") != html():
        print("VERALTET: die Webseite zeigt eine andere Erklärung als das Dokument.")
        print("  python universe\\kern\\funktionsdoku.py")
        return 1
    print("aktuell: Dokument und Webseite stimmen mit funktionen.json überein.")
    return 0


def main(argumente: list[str]) -> int:
    if not argumente:
        return schreiben()
    if argumente[0] == "pruefen":
        return pruefen()
    if argumente[0] == "soll" and len(argumente) > 1:
        print(json.dumps(sollwerte(argumente[1]), ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
