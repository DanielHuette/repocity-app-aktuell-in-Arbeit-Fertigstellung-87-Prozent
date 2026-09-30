# Änderungen

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unveröffentlicht] — Weg zu 100 %

Offen bis zur Fertigstellung:

- Handelsteil aus dem Trockenmodus in den Echtbetrieb überführen
- Abrechnung über Stripe in allen Abostufen abschließen
- Android-App im Play Store veröffentlichen
- Mehrsprachigkeit der Oberfläche
- Lasttest des Workers unter gleichzeitigen Zugriffen

## [0.87] — 2026-09-30

### Neu
- Hinweis auf der Landing Page: Seite in Arbeit, Handel im Trockenmodus
- Organigramm als vier Tafeln in Oberfläche und App
- Mia, die Assistentin, führt durch die Oberfläche und beantwortet Fragen
- Selbstverbesserung: Erfahrung aus abgearbeiteten Aufträgen fließt als Regel
  und als Kontext in die Agenten zurück

### Geändert
- Kern auf die Auftragskette umgebaut
- Abo-Sperre läuft zuerst durch den Worker, nicht über ausgelieferte Dateien

### Entfernt
- Alter Backtest des Handelsteils: er rechnete je Kerze auf einem Kerzensatz
  statt über die Leiter

## [0.1] — 2026-09-08

- Erster Stand: Kern, Verzeichnis der Agenten, Webseite, Android-App
