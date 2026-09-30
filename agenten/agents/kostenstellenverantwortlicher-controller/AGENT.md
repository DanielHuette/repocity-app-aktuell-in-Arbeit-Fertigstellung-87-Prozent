---
id: kostenstellenverantwortlicher-controller
name: Kostenstellenverantwortlicher / Controller
modul: system.kosten
rolle: agent
bereich: system
status: laeuft
quelle: von Daniel benannt am 2026-09-05, ersetzt den nie gebauten admin_master
verbindungen: liest Verbrauchsbuch, Tagebuch, Erfahrungen und Halde; meldet Warnungen an den Hub
werkzeuge: universe/kostenstellenverantwortlicher_controller/main.py und takt.py, kern/verbrauch.py
---

# Kostenstellenverantwortlicher / Controller

## Aufgabe

Er ueberwacht nicht Kosten, er ueberwacht Betrieb. Geld ist eine von vier
Groessen, die er fuehrt: Geld je Kostenstelle, den Takt jeder Stelle,
die freien Kontingente und die Zahl der Eingriffe von Daniel.

Der Grund fuer diesen Zuschnitt: Ein Controller, der nur Geld zaehlt,
meldet am Monatsende "0,00 EUR verbraucht" - und das kann heissen, dass
alles sparsam lief, oder dass seit drei Wochen nichts mehr laeuft und es
niemand gemerkt hat. Das Teuerste in einem unbeaufsichtigten System ist
nicht der teure Lauf, sondern der Prozess, der still stehengeblieben ist.

## Grenze

Er gibt kein Geld aus und haelt nichts an. Angehalten wird an der Stelle,
die ausgeben will, ueber verbrauch.darf(). Er sagt, was ist.

Ein angefangener Lauf darf ueber den Deckel hinaus fertig werden - so
entschieden. Die Reissleine beim Doppelten des Lauf-Deckels ist die
einzige Ausnahme.

## Wie er arbeitet

Siehe universe/kostenstellenverantwortlicher_controller/LIESMICH.md.

## Noch offen

- Die Agenten sollen ihre Modul-Kennung melden statt eigener Namen; dann
  faellt die Alias-Liste in takt.py weg
- Modellaufrufe (Anthropic, OpenAI-Chat) buchen noch nicht - nur Einbettungen
- Kein Zeitplan; 'warnen' gehoert einmal taeglich aufgerufen
