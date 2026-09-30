---
id: deep-researcher
name: deep researcher
organigramm_id: k3
rolle: agent
bereich: wissenszufluss
status: gebaut
quelle: deep_researcher/, geprüft am 2026-09-02
verbindungen: [kurator, implementierer-coding-agent, github-scout]
werkzeuge: [bing, wikipedia, tavily, playwright, trafilatura, anthropic]
---

# deep researcher

## Aufgabe

Holt neue Informationen aus dem Netz ins 2nd brain: Sachwissen, Vorlagen für
Webseiten-Grafik, Bauart interaktiver Lernprogramme. Er sucht, lädt die Seite,
schält den Haupttext heraus und destilliert daraus Wissensnotizen und Atome.

## Wann er tätig wird

`main.py recherche "<frage>"` auf Zuruf, vom Kurator oder per Zeitplan.
Vor der Suche prüft er, was das 2nd brain zur Frage schon hergibt, und sagt es an.

## Woran er fertig erkennt

Im Eingang liegt ein Ordner mit `UEBERGABE.md`, `wissen/`, `atome.jsonl` und
`quellen.json`. In der Verbesserungs-Säule liegt das Fallbeispiel.

## Übergaben

- **kurator** — bekommt den Eingangsordner; er pflegt ein und speist die Vektorsäule.
- **implementierer-coding-agent** — bekommt vom Kurator die Notizen zur Aufbereitung.
- **github-scout** — dieselbe Ablageform, damit der Kurator nur ein Format kennt.

## Grenze

Er schreibt nicht in die Wissens-, Vektor- oder Atom-Säule. Das macht der Kurator.

## Code

`universe/deep_researcher/` — Befehle in `LIESMICH.md`, Selbsttests in
`tests/test_researcher.py`.