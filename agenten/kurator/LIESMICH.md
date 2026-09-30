# Kurator

Die einzige Stelle, die in die Säulen des 2nd brain schreibt. Alles andere
liefert an; er prüft und pflegt ein.

## Befehle

    python main.py eingaenge              was bereitliegt
    python main.py stand                  was in den vier Säulen liegt
    python main.py pruefen --alle         prüfen, ohne einzupflegen
    python main.py einpflegen --alle      übernehmen
    python main.py einpflegen <ordner>    einen bestimmten Eingang

## Was er prüft, bevor etwas hineingeht

- Kopf vorhanden, Pflichtfelder gesetzt (`title`, `typ`, `erfasst_von`)
- Quelle angegeben — ohne Herkunft kein Wissen
- Notiz nicht zu dünn (unter 400 Zeichen Rumpf fliegt sie raus)
- Atome: Aussage lang genug, Beleg da, Quelle da
- Doppelungen gegen den Bestand: gleicher Titel oder gleiche Quelle

Was abgelehnt wird, wird gezählt und mit Grund genannt. Ein stilles Verwerfen
wäre schlimmer als gar keine Prüfung.

## Wohin er schreibt

    Säule 1  wissen/       die Notiz als Markdown, Dateiname behalten
    Säule 2  chroma/       Häppchen à 1800 Zeichen, Sammlung "universe_wissen"
    Säule 3  atome/<thema>.jsonl   je Zeile ein Atom
    Säule 4  bleibt den Agenten überlassen

**Eigene Sammlung in der Vektorsäule.** Gemini baut parallel an `wissen`.
Zwei Sammlungen in derselben Datenbank stören einander nicht, eine gemeinsame
Sammlung mit zwei Schreibern schon.

Die Einbettung läuft über `text-embedding-3-small` — dasselbe Modell wie im
AI-Wiki, damit die Abstände vergleichbar bleiben. Ohne `OPENAI_API_KEY` wird
nicht eingebettet und der Grund genannt; Notizen und Atome gehen trotzdem rein.

## Danach

Der Eingangsordner wandert nach `_erledigt`, die `UEBERGABE.md` bekommt
`status: eingepflegt` und die Zahlen angehängt. Der Sekretär bekommt eine
Meldung.