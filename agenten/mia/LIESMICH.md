# Mia - das Fragefenster

Mia ist die einzige Stelle, an der Fremde mit RepoCity sprechen. Deshalb ist
sie ein eigener Agent und keine Nebenaufgabe des Sekretaers: gelingt jemandem
eine Ueberredung, erbt er nur Mias Rechte - und Mia hat fast keine.

| | |
|---|---|
| Laeuft in | Cloudflare Worker (`webseite\worker\mia.js`), Weg A |
| Antwortzeit | 2 bis 5 Sekunden, keine Warteschlange ueber den Hub |
| Modell | `claude-opus-5` (aus `regeln.json`, dieselbe Vorgabe wie `kern/modellwahl.py`), Antwort auf 700 Token gedeckelt |
| Kostenstelle | `fragefenster`, Gaeste auf `fragefenster.gast` |
| Werkzeuge | **keine** - sie redet, sie loest nichts aus |
| Erreicht | Seiteninhalte, eigene Daten des Fragenden aus KV |
| Erreicht **nicht** | 2nd Brain, Dateisystem, andere Agenten, Auftragsvergabe |

## Die Dateien

| Datei | Was |
|---|---|
| `REGELWERK.md` | der verbindliche Wortlaut, 11 Paragraphen, mit Uebersetzung jedes Fachbegriffs |
| `regeln.json` | dieselben Regeln maschinenlesbar - **das**, was erzwungen wird |
| `pruefung.mjs` | prueft die Datei, die im Worker laeuft; kein Nachbau |
| `pruefungen.py` | haengt diese Pruefungen in den Pruefstand |
| `kosten_abholen.py` | holt Mias Buchungen aus dem Hub und bucht sie ueber `verbrauch.py` |

Eine Quelle fuer alle Regeln: `regeln.json`. Der Worker liest sie, der
Pruefstand liest dieselbe Datei. Wer eine Regel aendert, aendert sie einmal.

## Warum sie das 2nd Brain nicht sieht

Weg A war eine Entscheidung fuer Geschwindigkeit - und hat einen zweiten
Gewinn: die ganze Risikoklasse "undichte Wissensregale" faellt weg. Was Mia
nicht erreichen kann, kann sie nicht ausplaudern.

Ihr Steckbrief in `..\gehirn.json` steht trotzdem drin und laesst nur das
oeffentliche Regal `wissen` zu. Er haelt die Grenze fuer den Fall, dass sie
spaeter doch angeschlossen wird.

## Geld

Gezaehlt wird im Worker, gebucht wird im Universe:

```
Frage  ->  Worker zaehlt Token, rechnet EUR, legt eine Zeile in KV
       ->  Rechner holt ab (kosten_abholen.py)
       ->  verbrauch.buchen() auf die Kostenstelle fragefenster
       ->  Bericht des Kostenstellenverantwortlichen
```

Gemessen am 2026-09-06: **0,00555 EUR je Frage** (4035 Token ein im Mittel,
700 aus). Messung in `..\Betatests\messung_fragefenster_kosten.json`, mit
`count_tokens` erhoben - das ist kostenlos, es ist kein Geld geflossen.

Daraus die Rechnung fuer den Tagesdeckel:

| Monatsbudget | Fragen im Monat | Fragen am Tag |
|---|---|---|
| 5 EUR | 901 | 30 |
| 10 EUR | 1802 | 60 |
| 25 EUR | 4505 | 150 |

**Solange die drei Deckel in `regeln.json` auf `null` stehen, antwortet Mia
nicht.** Kein gesetzter Deckel heisst nicht "unbegrenzt", sondern "noch nicht
entschieden" - ein offener Hahn ist teurer als ein geschlossener. Eine Pruefung
im Pruefstand haelt das fest.

## Bedienen

```
node universe\mia\pruefung.mjs              alle Grenzen pruefen, kostenlos
python universe\kern\pruefstand.py trocken  dasselbe im Gesamtbericht
python universe\mia\kosten_abholen.py       Buchungen holen und verbuchen
```

## Was fehlt, bevor sie antwortet

Steht in `regeln.json` unter `_scharf_erst_wenn` und in `REGELWERK.md` § 11.
Solange `"scharf": false` ist, bleibt `/api/frage` beim ehrlichen Platzhalter.
