# Ausbilder

Er schult keine Agenten. Er liest, was die Aufträge gelehrt haben, und
schlägt daraus Regeln vor. Bestätigen tust du.

## Warum es ihn gibt

Der Warenausgang regelt nur die Übergabe. Damit lernt kein Agent etwas.
Gelernt ist erst, wenn die Anweisung, mit der ein Agent beim nächsten Mal
antritt, eine andere ist als beim letzten Mal — und zwar nachweislich zum
Besseren. Alles andere ist Gefühl.

## Was er tut

```
python main.py sichten [modul]        Erfahrungen lesen, Lehrsätze vorschlagen
python main.py vorschlaege            was auf deine Bestätigung wartet
python main.py bestaetigen L0001
python main.py ablehnen L0001 "warum nicht"
python main.py nachpruefen            welcher Lehrsatz nichts bewirkt hat
python main.py zurueckziehen L0001 "keine Bewegung"
python main.py zeugnis [modul] [seit]
python main.py anweisung prod.video.stueck    was der Agent als Vorwissen bekommt
python main.py stand
```

## Die drei Regeln, an die er sich hält

**Er schlägt vor, er entscheidet nicht.** Ein Agent, der seine eigene
Anweisung ohne Gegenlesen umschreibt, ist der schnellste Weg zu einem System,
das niemand mehr versteht.

**Erst ab drei gleichen Urteilen.** Eine einzelne Erfahrung wird nie zur
Dauerregel. Sonst bekommst du einen Agenten voller Aberglauben: er hat einmal
ein Nein für eine Kleinigkeit kassiert und meidet die Sache fortan
grundsätzlich.

**Er zieht nichts von selbst zurück.** Findet er einen Lehrsatz ohne Wirkung,
legt er ihn dir vor. Der Befehl `zurueckziehen` ist deiner, nicht seiner.

## Wie er Wiederholungen erkennt

„Ton zu leise gegenüber der Musik", „Die Musik übertönt die Stimme" und
„Stimme geht in der Musik unter" sind derselbe Mangel — sie teilen aber nur
ein einziges Wort. Ein reiner Wortvergleich sieht drei verschiedene Sachen.
Deshalb vergleicht `sichten` die **Bedeutung** über dieselbe Vektorschicht,
mit der auch das 2nd Brain durchsucht wird.

Zwei Gründe gelten als dieselbe Sache ab einer Nähe von 0,55. Nähe ist die
Kosinus-Ähnlichkeit: über 0,60 sehr ähnlich, 0,45–0,60 brauchbar, darunter
Zufall. Der Wert steht als `NAEHE_AB` in `kern/rueckweg.py`.

## Was das kostet

| Befehl | Kosten |
|---|---|
| `sichten` | eine Einbettung je Ablehnungsgrund — bei 500 Gründen rund **0,0002 €** |
| `sichten --ohne-modell` | **nichts**, vergleicht nur Wörter und übersieht Umschreibungen |
| `sichten --formulieren` | zusätzlich Bruchteile eines Cent je Satz, damit ein Modell den Rohsatz glatt schreibt |
| alles andere | **nichts**, es liest nur Dateien |

Ohne `--formulieren` baut er den Satz selbst aus den Gründen. Er steht dann
holprig da, sagt aber dasselbe — und du kannst ihn in Obsidian überschreiben,
bevor du ihn bestätigst.

## Wo was liegt

| Ordner | Inhalt |
|---|---|
| `vault\erfahrungen\` | eine Datei je abgeschlossenem Auftrag |
| `vault\lehrsaetze\` | `L0001_<modul>.md`, Stand: vorschlag → aktiv → zurückgezogen |
| `vault\halde\` | alles Verworfene, mit Grund und Datum |
| `vault\warenausgang\` | Beipackzettel der fertigen Stücke |

Alles ist Markdown mit Kopfdaten. Du kannst jede Datei in Obsidian lesen und
korrigieren — was dort steht, gilt. Die Vektordatenbank ist nur der Index.

## Wann er läuft

Von Hand, solange kein Zeitplan steht. Sinnvoll ist:
`sichten` nach einem Schwung Aufträge, `nachpruefen` einmal im Monat.
Ein Lehrsatz bekommt 30 Tage Schonfrist, bevor er gemessen wird
(`SCHONFRIST_TAGE` in `main.py`), und braucht mindestens drei Stücke seither,
damit die Zahl überhaupt etwas heißt.

## Was er noch nicht kann

- Code bewerten. Das steht in seiner AGENT.md, ist aber ein zweites Thema:
  dafür braucht es erst die Coding-Agenten, die es noch nicht gibt.
- Von selbst laufen. Es gibt noch keinen Zeitplan und keinen Hub-Aufruf,
  der ihn weckt.
