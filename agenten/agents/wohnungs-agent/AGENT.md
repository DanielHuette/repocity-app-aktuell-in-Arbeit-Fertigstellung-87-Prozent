---
id: wohnungs-agent
name: Wohnungsagent
organigramm_id: k29
rolle: agent
bereich: aussen
status: gebaut
quelle: wohnungs_agent/, geprüft am 2026-09-02
verbindungen: [email-agent, sekretaer]
werkzeuge: [nadann, kleinanzeigen, wg-gesucht, playwright]
---

# Wohnungsagent

## Aufgabe

Sucht Mietwohnungen in Münster und 30 km Umkreis, prüft sie gegen die Grenzen
(höchstens 500 € kalt, unter 700 € warm), führt die Liste und legt die Anfrage
an den Vermieter fertig hin.

## Wann er tätig wird

`main.py suchen` auf Zuruf oder per Zeitplan. Bei Wohnungen zählen Stunden,
deshalb ist ein kurzer Takt sinnvoll.

## Woran er fertig erkennt

`daten/liste.md` ist neu geschrieben, die passenden Angebote liegen als Anfrage
im Postausgang, und im Tagebuch steht die Meldung für den Sekretär.

## Übergaben

- **email-agent** — leert `universe/zustand/postausgang.jsonl` und verschickt.
  Der Wohnungsagent hat selbst keine Postfachdaten.
- **sekretaer** — liest `universe/zustand/tagebuch.jsonl` und legt in der App vor.

## Grenze

Er verschickt nichts selbst. In der Betriebsart `trocken` verlässt keine Mail
den Rechner.

## Code

`universe/wohnungs_agent/` — Befehle in `LIESMICH.md`, Selbsttests in
`tests/test_wohnung.py`.