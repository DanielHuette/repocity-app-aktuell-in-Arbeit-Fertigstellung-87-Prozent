# Produktionsstraße Lernprogramme und Präsentationen — Bauplan

Stand 2026-09-04. Erarbeitet, nicht abgenommen.

## Der tragende Gedanke

**Ein neutrales Zwischenformat, mehrere dumme Renderer.**

Der Schwarm schreibt nie direkt Folien oder Lerneinheiten. Er schreibt je Wissensblatt
ein **Lernobjekt als JSON**:

```
lernziel, kernaussagen[], karten[{frage, antwort, art}], quiz[],
quelle: { vault_datei, chroma_chunk_ids[] }
```

Genau dort sitzt die Qualitätsprüfung: Ist jede Aussage an eine Quelle gebunden?
Gibt es Dubletten (Abgleich über ChromaDB)? Erst danach wird gerendert.

Der Vorteil: Ein neues Ausgabeformat kostet einen Renderer, nicht eine neue Straße.

## Die vier Renderer

| Ausgabe | Werkzeug | Lizenz | Warum dieses |
|---|---|---|---|
| Karteikarten | `genanki` → `.apkg` | MIT | Reines Python, Anki ist der Standard |
| Wiederholung | `py-fsrs` 6.3.1 + SQLite | MIT | FSRS-6 ist Stand der Technik, keine Cloud |
| Interaktive Einheit | reveal.js + `reveal-quiz`, statisches HTML | MIT | Kein Server nötig |
| Folien | Marp CLI im Container | MIT | Markdown rein, PDF/PPTX raus |

**Zur Wiederholung nach Vergessenskurve:** FSRS-6 gegen SM-2 ist gemessen, nicht behauptet —
Vergleich über 349,9 Mio. Wiederholungen aus 9.999 Sammlungen: FSRS-6 LogLoss 0,3460
gegen FSRS-v4 0,3726. `py-fsrs` hat keine Kernabhängigkeiten und einen Optimierer,
der die Parameter monatlich auf die eigene Historie nachzieht.

**Abgeraten:**

- **Open edX** — mehrere GB Container, Betriebsaufwand ohne Gegenwert für uns.
- **SCORM / xAPI** — erst bauen, wenn ein fremdes Lernsystem es verlangt.
- **Slidev** — schönste Ergebnisse, aber Vue-Kenntnisse und hoher Pflegeaufwand.
- **python-pptx** — nur wenn ein festes Corporate-Template zwingend ist; es hat
  keinen Umbruch, Textüberlauf muss selbst geprüft werden.

**Optional dazu:** `Presenton` (Apache-2.0, FastAPI + Docker, ein Befehl, läuft mit
lokalem Ollama) — wenn "vorzeigbar ohne Handarbeit" schwerer wiegt als volle Kontrolle.

## HyperFrames — der Befund

Der Begriff ist doppelt belegt, und die Erwartung stimmt nicht:

- **`heygen-com/hyperframes`** (Apache-2.0, TypeScript, Node 22 + ffmpeg, Docker vorhanden):
  "Write HTML. Render video. Built for agents." Also **HTML/CSS/JS → MP4, deterministisch**.
  Das ist eine **Video-Ausgabestufe**, kein Lernwerkzeug. Kein Python-Binding.
- `hyperframe` im Python-Umfeld ist etwas völlig anderes (HTTP/2-Frames).

**Es gibt kein HyperFrames für interaktive Lernprogramme.** Der Anschluss ergibt trotzdem
Sinn — aber an anderer Stelle: als Renderer, der aus einer Lerneinheit ein **Erklärvideo**
macht. Weil es Node-only ist, gehört es in einen **eigenen Container hinter einer
Schnittstelle**, nicht in den Kern.

## Container

Zwei Bilder, ein gemeinsames Ablagefach:

1. `python:3.12-slim` — die Agenten, genanki, py-fsrs, Chroma-Client.
2. Node + Chromium — Marp (und später HyperFrames).

## Kosten

Nur Modell-Kosten für das Erzeugen der Lernobjekte. Mit einem lokalen Modell: **0 €**.

## Nächste Schritte

1. Das JSON-Schema des Lernobjekts festlegen — das ist die eigentliche Entscheidung.
2. Prüfstufe bauen: Quellenbindung und Dublettenabgleich gegen ChromaDB.
3. Renderer 1 (genanki) und 4 (Marp) zuerst — sie liefern sofort etwas Vorzeigbares.
4. Wiederholungsdienst mit py-fsrs, Reviews in SQLite, monatliche Optimierung.
5. HyperFrames erst danach, als Videostufe.
