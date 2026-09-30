---
id: kurator
name: Kurator
organigramm_id: k5
rolle: agent
bereich: wissenszufluss
status: gebaut
quelle: kurator/, geprüft am 2026-09-02
verbindungen: [deep-researcher, github-scout, sekretaer]
werkzeuge: [chromadb, openai-embeddings]
---

# Kurator

## Aufgabe

Pflegt neue Inhalte in das 2nd brain ein. Er ist die einzige Stelle, die in die
Säulen schreibt — deshalb prüft er vorher: Kopf, Quelle, Umfang, Doppelungen.

## Wann er tätig wird

Wenn im Eingang etwas liegt. `main.py einpflegen --alle`, auf Zuruf oder per
Zeitplan.

## Woran er fertig erkennt

Der Eingangsordner liegt in `_erledigt`, die `UEBERGABE.md` trägt
`status: eingepflegt` samt Zahlen, und die Säulen sind gewachsen.

## Übergaben

- **deep-researcher** und **github-scout** liefern in den Eingang, beide im
  selben Format.
- **sekretaer** bekommt die Meldung, was übernommen wurde.

## Grenze

Er löscht nichts und überschreibt nichts. Eine Notiz, deren Name schon
vergeben ist, bekommt das Datum angehängt.

## Code

`universe/kurator/` — Befehle in `LIESMICH.md`, Selbsttests in
`tests/test_kurator.py`.