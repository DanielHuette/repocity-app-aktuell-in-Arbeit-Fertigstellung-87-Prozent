---
id: ausbilder
name: Ausbilder
organigramm_id: k26
rolle: agent
bereich: wissenszufluss
status: laeuft
quelle: organigramm/ORGANIGRAMM_2ND_BRAIN.html, Stand 2026-09-01
verbindungen: liest vault/erfahrungen, schreibt vault/lehrsaetze, meldet an den Hub
werkzeuge: universe/ausbilder/main.py, kern/rueckweg.py, kern/vektor.py
---

# Ausbilder

## Aufgabe

überwacht alle coding agents und bewertet code, bewertet verbesserungen durch neue coding läufe und bewertet mit dem Qualitätsmanager zusammen die Produktqualität

## Noch offen

- Code bewerten - braucht erst die Coding-Agenten, die es noch nicht gibt
- Ein Zeitplan, der ihn weckt; bis dahin laeuft er von Hand

## Wie er arbeitet

Siehe universe/ausbilder/LIESMICH.md. Kurz: er liest die Erfahrungen aus
abgeschlossenen Auftraegen, fasst Ablehnungsgruende nach Bedeutung zusammen
und schlaegt ab drei gleichartigen Urteilen einen Lehrsatz vor. Daniel
bestaetigt. Wirkungslose Lehrsaetze legt er zur Ruecknahme vor - er zieht
nichts von selbst zurueck.