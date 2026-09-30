# Qualitätsmanager

Er nimmt ab, bevor du es siehst. Er sitzt in jeder Produktionsstraße.

## Was er tut

```
Agent meldet fertig
    → harte Messung      Datei, Länge, Auflösung, Tonspur, Stille
    → Beipackzettel      alle Pflichtfelder da, Bildquellen belegt
    → Lehrsätze          was aus früheren Neins gelernt wurde
    → bestanden?
         ja   → in den Warenausgang, du wirst gefragt
         nein → zurück in die Straße, höchstens zweimal
         dreimal durchgefallen → Halde, mit Grund, plus Erfahrung
```

```
python main.py pruefen  video <datei> --auftrag a1 --modul prod.video.clip
python main.py abnehmen video <datei> --auftrag a1 --modul prod.video.clip --titel "..."
python main.py grenzen        welche Werte gelten
python main.py liste          was er abgenommen hat
```

## Der wichtigste Teil: gelernt wird geprüft

Ein bestätigter Lehrsatz ist keine Notiz — er wird zur Messung, sobald er
eine Zahl und eine messbare Größe nennt.

| Lehrsatz | Was daraus wird |
|---|---|
| „Ein Clip darf höchstens 10 Sekunden lang sein." | echte Messung: 12 s fallen durch |
| „Ein Clip soll mindestens 15 Sekunden laufen." | echte Messung, andere Richtung |
| „Der Aufhänger gehört nach vorn." | Merkposten am Befund |

Das ist die Stelle, an der aus „gelernt" tatsächlich „geprüft" wird. Ein
Satz ohne Zahl bleibt Merkposten — ehrlicher, als so zu tun, als könne eine
Maschine „Aufhänger stärker" nachmessen. Welche Wörter er als messbare Größe
erkennt, steht als `WORT_ZU_GROESSE` in `pruefliste.py`.

Jeder Befund nennt unter „Geprüft gegen" die Kennungen aller Lehrsätze, die
er berücksichtigt hat. Damit lässt sich später nachvollziehen, welche Regel
bei welchem Stück gegriffen hat.

## Was er misst

| Ware | Was gemessen wird |
|---|---|
| video | Länge, Breite, Höhe, Bildrate, Tonspur, längste Stille am Stück, Dateigröße |
| ton | Länge, Dateigröße |
| bild | Breite, Höhe, Dateigröße |
| text | Zeichenzahl |

Die Grenzwerte stehen als `GRENZEN` in `pruefliste.py` — an einer Stelle,
nicht verstreut. `python main.py grenzen` zeigt sie.

## Was er ausdrücklich nicht tut

Über Geschmack urteilen. Ob ein Schnitt gut sitzt, entscheidet kein
Grenzwert. „Bestanden" heißt: ohne messbaren Mangel und im Rahmen dessen,
was bisher gelernt wurde. Über gut entscheidest du.

Für das Ansehen gibt es den Kontaktbogen des Video-Agenten
(`video_agent/abnahme.py`) — ein Blatt mit gleichmäßig verteilten
Einzelbildern und Zeitmarke. Der ist noch nicht angeschlossen; siehe unten.

## Was er kostet

Nichts. Alle Messungen laufen über ffprobe und ffmpeg auf deinem Rechner.
Erst wenn ein Modell das Ergebnis ansehen soll, kostet es etwas — das ist
noch nicht gebaut und wäre abschaltbar.

## Wie er geprüft ist

Zehn Prüfungen im Prüfstand, alle trocken und kostenlos. Sie bauen sich ihr
Prüfmaterial selbst: ein Sekundenvideo aus Farbbalken und Sinuston, erzeugt
mit ffmpeg. Damit läuft die Prüfung gegen echte Dateien und echtes ffprobe,
ohne dass irgendetwas erzeugt oder bezahlt werden muss.

```
cd universe\kern
python pruefstand.py trocken system.qm
```

## Was noch fehlt

- **Kontaktbogen anschließen.** `video_agent/abnahme.py` kann ihn schon
  bauen; er hängt noch nicht am Befund.
- **Urteil durch ein Modell**, für alles, was sich nicht messen lässt.
  Muss abschaltbar sein und gegen den Kostentopf buchen.
- **Der Verwerfen-und-neu-Erzeugen-Weg** bei hochwertigen Videos: höchstens
  zweimal je Einstellung, innerhalb der Obergrenze. Heute schickt er den
  ganzen Auftrag zurück, nicht die einzelne Einstellung.
