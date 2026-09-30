---
id: sekretaer
name: Sekretär
organigramm_id: k4
rolle: agent
bereich: leitung
status: gebaut
quelle: sekretaer/, geprüft am 2026-09-02
verbindungen: [mastermind-app, kurator, email-agent, bewerbungs-agent, wohnungs-agent]
werkzeuge: [tagebuch, postausgang, hub]
---

# Sekretär

## Aufgabe

Überwacht Fälligkeiten und legt in der RepoCity App vor: was entschieden
werden muss, was fällig ist, was gefunden wurde, was schiefging.

## Wann er tätig wird

`main.py vorlegen`, sinnvollerweise mehrmals täglich per Zeitplan.

## Woran er fertig erkennt

`zustand/vorlage.json` ist neu geschrieben und die Meldung an den Hub raus —
oder, ohne Hub, im Tagebuch vermerkt.

## Übergaben

- **RepoCity App** bekommt die Vorlage.
- **email-agent** leert den Postausgang, sobald ein Ja da ist.
- **kurator** wird angemahnt, wenn ein Eingang zu lange liegt.

## Grenze

Er entscheidet nichts und verschickt nichts. Er legt vor.

## Code

`universe/sekretaer/` — Befehle in `LIESMICH.md`, Selbsttests in
`tests/test_sekretaer.py`.