---
id: github-scout
name: github scout
organigramm_id: k2
rolle: agent
bereich: wissenszufluss
status: gebaut
quelle: github_scout/, geprüft am 2026-09-02
verbindungen: [kurator, deep-researcher, sekretaer]
werkzeuge: [github-api, anthropic]
---

# github scout

## Aufgabe

Durchsucht GitHub nach neuen Skills, Verbesserungen und nachahmenswerten
Projekten für das 2nd brain und für den Bau des Universe. Bewertet, was taugt,
erntet die Besten ab und legt Notizen und Atome für den Kurator bereit.

## Wann er tätig wird

Einmal die Woche. `main.py suchen`.

## Woran er fertig erkennt

Im Eingang liegt ein Ordner mit `UEBERGABE.md`, `wissen/`, `atome.jsonl` und
`quellen.json`. Die Beobachtungsliste ist fortgeschrieben, der Sekretär hat die
Meldung.

## Übergaben

- **kurator** — bekommt den Eingangsordner, pflegt ein, speist die Vektorsäule.
- **deep-researcher** — dieselbe Ablageform, damit der Kurator nur ein Format kennt.
- **sekretaer** — Meldung über das Tagebuch an die RepoCity App.

## Grenze

Er schreibt nicht in die Wissens-, Vektor- oder Atom-Säule. Das macht der Kurator.

## Code

`universe/github_scout/` — Befehle in `LIESMICH.md`, Selbsttests in
`tests/test_scout.py`.