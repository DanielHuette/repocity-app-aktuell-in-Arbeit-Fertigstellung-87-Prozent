---
typ: liste
status: unfertig
zuletzt: 2026-09-02
---

# Repositories, die der Scout beobachtet

## Grundstock — steht

**331 Repositories mit dem Urteil "ja"** aus `Neustart\repo_pruefung.json`.
Das ist Daniels Handarbeit an 1.570 Funden vom 2026-08-31. Sie wird nicht
wiederholt, sondern übernommen:

    cd universe\github_scout
    python main.py saeen

Danach stehen sie in `daten\beobachtung.json` und werden bei jedem Lauf auf
Bewegung geprüft.

## Suchthemen — vorläufig, zu erweitern

In `github_scout\konfiguration.json` unter `suche.themen`. Aktuell zehn:
Claude-Code-Skills, Multi-Agent-Rahmenwerke, MCP-Server, RAG-Wissensbasen,
Obsidian-Automation, selbstverbessernde Auswertung, LangGraph-Orchestrierung,
Prompt- und Kontext-Engineering, n8n-Automatisierung, Langzeitgedächtnis.

**Noch offen — hier gehört Daniels Urteil hinein:**

- Welche Themen fehlen? Video- und Musikerzeugung, Android-Bau, Trading,
  Lernprogramme mit Hyper Frames sind im Organigramm vorgesehen, aber
  nicht in den Suchthemen.
- Ab wie vielen Sternen lohnt ein Repository? Steht auf 30. Bei kleinen,
  guten Projekten ist das zu hoch — Daniel wollte ausdrücklich auch Repos
  mit wenigen Sternen mitnehmen.
- Sollen einzelne Personen dauerhaft beobachtet werden (affaan-m, ruvnet,
  anthropics, langchain-ai)? Dafür gäbe es die Beobachtungsliste, aber noch
  keinen Befehl "beobachte alles von diesem Konto".

## Was der Scout selbst dazulegt

Jeder Lauf trägt neue Funde ein. Was einmal drin ist, bleibt drin und wird auf
Bewegung geprüft — die Liste wächst also von allein, aber nur mit dem, was die
Suchthemen hergeben.