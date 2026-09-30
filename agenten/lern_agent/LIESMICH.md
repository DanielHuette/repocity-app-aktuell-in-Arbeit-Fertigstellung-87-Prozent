# Lern-Werkstatt

Die dritte Produktionsstrasse. Ein Thema geht herein, **eine einzige
HTML-Datei** kommt heraus: ein interaktiver Kurs, den man oeffnet, mit
Namen startet und Level fuer Level durchlaeuft.

Nachgebaut nach dem Verfahren aus dem Transkript *"So erstellst du
interaktive Schulungen mit Claude Code auf Knopfdruck"* (Julian Ivanov) —
mit einem Unterschied: die teuren Teile sind abschaltbar und aus.

---

## Der Ablauf

```
Auftrag ─► Briefing ─► Curriculum ─► ABNAHME durch Daniel
                                          │
                                Go ───────┴─────── Änderungswunsch
                                 │                      │
                                 ▼                      ▼
                      Erzeugung: Erzähler,        zurück ins Curriculum
                      Animationen, Zusammenbau
                                 │
                                 ▼
                        eine HTML-Datei
```

**Die Abnahme in der Mitte ist keine Foermlichkeit.** Sie steht dort, weil
erst danach anfaengt, was Zeit und Geld kostet. Im Vorbild ist es dieselbe
Stelle: Curriculum lesen, dann "Go" sagen.

---

## Was der fertige Kurs kann

- **Namen eingeben, dann losgehen.** Der Fortschritt bleibt im Browser
  gespeichert — wer abbricht, macht spaeter weiter.
- **Level fuer Level**, mit Fortschrittsbalken und XP.
- **Vier Aufgabenarten:** zuordnen (Begriffe in Faecher), regler (Zahl
  schaetzen), wahl (eine aus mehreren), reihenfolge (Schritte sortieren).
- **Ohne geloeste Aufgabe kein Weiterkommen.** Genau wie im Vorbild — das
  ist der Grund, warum etwas haengenbleibt.
- **Rueckmeldung bei falscher Antwort**, mit Hinweis, ohne die Loesung zu
  verraten.
- Erzaehlerstimme und Animation je Level, wenn eingeschaltet.

Alles in **einer Datei**. Medien werden eingebettet, solange sie klein sind;
grosse liegen daneben in `medien/`. Eine 300-MB-Datei hilft niemandem.

---

## Was es kostet

| Teil | Womit | Kosten |
|---|---|---|
| Curriculum und Texte | Sprachmodell | Token, mit Ollama nichts |
| Erzaehlerstimme | edge-tts | **nichts**, kein Konto |
| Animationen | HyperFrames (HTML → MP4) | **nichts** ausser Rechenzeit |
| KI-Videos | Higgsfield o. ae. | **5 bis 6 Euro je Clip** — bleibt aus |

Im Vorbild heisst es: *"der Grossteil sind eben die HTML-generierten
Inhalte"*. Genau so ist es hier gebaut. KI-Videos sind ein Schalter, der
standardmaessig auf aus steht.

---

## Ausprobieren

```
python probe.py "Sicherer Umgang mit KI im Arbeitsalltag"
```

Baut eine vollstaendige Schulung ohne Netz, ohne Schluessel, ohne Modell.
Die HTML-Datei landet unter `_probe/lern_fertig/` — im Browser oeffnen und
wirklich durchklicken. Nur die Inhalte sind Platzhalter, die Mechanik ist
echt.

**Geprueft:** falsche Antwort sperrt das Weiterkommen, richtige gibt XP und
gibt frei, Zuordnen und Reihenfolge funktionieren, der Fortschritt
ueberlebt das Neuladen.

---

## Einstellungen

Vorlage in `EINSTELLUNGEN-BEISPIEL.txt`, nach `.env` kopieren.
Die wichtigsten:

- `UNIVERSE_LERN_ABNAHME=ja` — nichts wird erzeugt ohne Go.
- `UNIVERSE_LERN_STIMME_AN=ja` — Erzaehler ueber edge-tts.
- `UNIVERSE_LERN_HYPERFRAMES=nein` — Animationen, braucht Node und ffmpeg.
- `UNIVERSE_LERN_KI_VIDEO=nein` — das Teure. Nur bewusst einschalten.

---

## Was noch fehlt

- HyperFrames wirklich anbinden: der Aufruf steht, geprueft ist er noch
  nicht (Node im Container ist vorbereitet).
- Das Aussehen an die drei Kits koppeln, damit ein Kurs in Rossi,
  Glashaus oder Blende erscheinen kann — heute ist Blende fest eingebaut.
- Anbindung an das 2nd Brain: Curricula aus vorhandenem Wissen statt aus
  dem Modellgedaechtnis. Das ist der eigentliche Hebel — dann lernt der
  Kurs aus dem, was der Schwarm gesammelt hat.
