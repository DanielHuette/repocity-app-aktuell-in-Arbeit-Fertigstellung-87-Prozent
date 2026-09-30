# Deep Researcher

Sucht im Netz, schält den Haupttext heraus, destilliert daraus Wissensnotizen und
Atome und legt beides für den Kurator in den Eingang des 2nd brain.

## Befehle

    python main.py recherche "<frage>"                 sucht, liest, destilliert, legt ab
    python main.py recherche "<frage>" --quellen 12    mehr Quellen
    python main.py recherche "<frage>" --art vorlagen  sucht zusätzlich nach Quelltext-Vorlagen
    python main.py recherche "<frage>" --art lernprogramm
    python main.py frage "<frage>"                     nur die Trefferliste, nichts wird abgelegt
    python main.py eingang                             was für den Kurator bereitliegt

## Was dabei herauskommt

    <eingang>/<datum>_<frage>/
      UEBERGABE.md    was drin ist und was der Kurator noch tun muss
      wissen/*.md     je Quelle eine Notiz, Format wie die vorhandenen Wissensdateien
      atome.jsonl     je Zeile ein Atom: Aussage, wörtlicher Beleg, Quelle, Thema, Sicherheit
      quellen.json    jede Adresse mit Zeichenzahl und Ausgang

Zusätzlich landet ein Fallbeispiel in der Verbesserungs-Säule: welche Frage, welche
Quellen taugten, welche nicht und warum.

## Suche

Bing über einen stillen Browser, weil Suchmaschinen die reine Abfrage mit 202
abweisen. Bings Verweise werden ausgepackt, sonst zeigen alle Treffer auf dieselbe
Adresse. Wikipedia kommt über die offene Schnittstelle dazu. Liegt ein Schlüssel in
`TAVILY_API_KEY`, wird der bevorzugt — schneller und schonender.

## Mit und ohne Modellschlüssel

Mit `ANTHROPIC_API_KEY` destilliert das Modell: eine Wissensnotiz mit Mechanismus,
Konzepten, Werkzeugen und Code, dazu Atome mit wörtlichem Beleg und
Sicherheitsgrad "hoch" oder "mittel".

Ohne Schlüssel greift der Ausschnitt-Weg: Sätze, die die Frage berühren, werden als
Atome mit Sicherheit "roh" abgelegt. Brauchbar als Rohstoff, nicht als Wissen — der
Kurator sieht am Feld, was noch durchmuss.

## Einrichten

    pip install -r requirements.txt
    playwright install chromium

## Was bewusst nicht passiert

Der Researcher schreibt nicht in die Wissens-, Vektor- oder Atom-Säule des 2nd brain.
Er legt in den Eingang; das Einpflegen ist Sache des Kurators. Nur die
Verbesserungs-Säule beschreibt er direkt.