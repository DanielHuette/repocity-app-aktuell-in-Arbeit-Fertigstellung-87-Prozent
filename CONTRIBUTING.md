# Mitarbeiten

RepoCity ist ein Einzelprojekt in Entwicklung. Beiträge von außen sind
willkommen, laufen aber über ein Gespräch vorher — bitte zuerst ein Issue
öffnen, statt ungefragt einen Pull Request zu schicken.

## Bevor du etwas baust

1. Lies [docs/ARCHITEKTUR.md](docs/ARCHITEKTUR.md) und
   [docs/ORGANIGRAMM.md](docs/ORGANIGRAMM.md).
2. Öffne ein Issue und beschreibe, was du vorhast.
3. Warte auf eine Antwort. Erst dann lohnt sich die Arbeit.

## Entwicklungsumgebung

**Webseite**

```bash
cd webseite
npm install
npm run dev          # Entwicklungsserver
npm run build        # bauen
```

**Kern und Agenten**

```bash
python -m venv .venv
.venv/Scripts/activate      # Windows
pip install -r requirements.txt
```

**Android-App**

Das Projekt unter `app/` in Android Studio öffnen und mit Gradle bauen. Eine
`local.properties` mit dem Pfad zum SDK gehört dazu und liegt nicht im
Repository.

## Wie hier geschrieben wird

- **Deutsch.** Ordner, Dateien, Funktionen und Kommentare tragen deutsche Namen.
  Fachbegriffe, für die es kein gutes deutsches Wort gibt, bleiben stehen.
- **Kommentare sagen warum, nicht was.** Was der Code tut, steht im Code.
- **Keine erfundenen Zahlen.** Was nicht gemessen ist, wird nicht behauptet.
- **Ein Zweck je Datei.** Wer eine Datei nicht in einem Satz beschreiben kann,
  hat zwei Dinge hineingelegt.

## Bevor du einen Pull Request schickst

- Der Bau läuft durch: `python kern/bau.py webseite` beziehungsweise `app`.
- Keine Schlüssel, keine Zugangsdaten, keine personenbezogenen Daten im Diff.
- Eine Zeile je Änderung im [CHANGELOG.md](CHANGELOG.md).
