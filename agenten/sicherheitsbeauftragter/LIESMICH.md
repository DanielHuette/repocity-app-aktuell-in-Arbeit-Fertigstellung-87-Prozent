# Sicherheitsbeauftragter

Er macht einen Rundgang und sagt, was er gefunden hat. **Er ändert nichts
und gibt nie einen Schlüssel aus** — ein Sicherheitsbericht, der Schlüssel
enthält, ist selbst das Leck.

```
python main.py rundgang                 alles prüfen, dauert rund 17 Sekunden
python main.py rundgang --gruendlich    zusätzlich die 20.000 Wissensdokumente
python main.py schluessel               nur Schlüssel und Ablage
python main.py verlauf                  nur den Git-Verlauf
python main.py rechte                   nur Tür, Steckbriefe und Ausgang
python main.py zugaenge                 was fehlt und was das lahmlegt
python main.py stand                    eine Zeile je Schwere
```

## Sein Grundsatz beim Suchen

Er sucht **nicht** nach Mustern, die wie ein Schlüssel aussehen. Er nimmt
deine Schlüssel aus der `.env` und sucht nach **genau diesen Zeichenfolgen**
— im Arbeitsverzeichnis, im Git-Verlauf, im Tagebuch, im Verbrauchsbuch, im
Vault, in den fertigen Beiträgen.

Das findet auch einen Schlüssel, der keinem bekannten Muster folgt, und
schlägt keinen Fehlalarm auf eine zufällig lange Zeichenkette.

**Grenze:** Alles unter 16 Zeichen gilt als Wort, nicht als Geheimnis —
sonst löst jedes `ja` in der `.env` Alarm aus. Deine Passwörter haben 12
Zeichen und werden deshalb **nicht** gesucht. Wenn eines davon irgendwo
landen würde, fiele es ihm nicht auf.

## Wofür er verantwortlich ist

### Schlüssel und Zugänge
- Liegt ein Schlüssel im Klartext außerhalb der `.env`?
- Steht einer im Git-Verlauf? **Das ist das Risiko mit echtem Schaden** —
  ein Schlüssel, der einmal committet wurde, bleibt im Repo, auch wenn die
  Datei später gelöscht wird. Das Repo liegt auf GitHub.
- Ist die `.env` vor Git geschützt — und war sie es immer?
- Ist einer in einer Betriebsdatei gelandet? Das passiert, wenn eine
  Fehlermeldung die ganze Anfrage mitprotokolliert.

### Vollzähligkeit
Welcher Zugang fehlt — und **was das lahmlegt**. Ein fehlender Schlüssel
ist keine Sicherheitslücke, aber dieselbe Sorte stiller Ausfall: der Agent
läuft, findet nichts, meldet nichts. Fehlt `PEXELS_API_KEY`, nimmt die
Videostraße Platzhalter und sagt es nur im Protokoll.

### Ablauf
Ein abgelaufener Schlüssel sieht aus wie ein kaputter Agent — man sucht
tagelang am falschen Ende. Er warnt 21 Tage vorher. Die Termine stehen in
`universe\sicherheit.json`.

### Die Tür
Der Kern hat eine Regel: kein Agent redet selbst mit ChromaDB, alles geht
durch `gehirn.py`. Wer sie umgeht, umgeht auch die Steckbriefe und liest
Regale, die er nicht sehen darf.

### Rechte
Welches Modul darf ins 2nd Brain **schreiben** — und steht es auf der Liste
in `sicherheit.json`? Welches darf das Regal `persoenlich` sehen?

### Der Ausgang
Ist ein Stück abgeholt worden, das nie freigegeben war? Deine Freigabe ist
die einzige Stelle, an der du entscheidest — sie muss halten.

## Die drei Schweregrade

| | Bedeutung |
|---|---|
| **SOFORT** | Ein Schlüssel liegt offen oder im Verlauf. Neu ausstellen, nicht nur löschen. |
| **BALD** | Etwas läuft ab, fehlt oder umgeht eine Regel. Kein Notfall, aber es bleibt nicht folgenlos. |
| **ZUR KENNTNIS** | Der Stand, nicht ein Fehler. Damit niemand etwas für geschützt hält, was es nicht ist. |

## Was er beim ersten Rundgang gefunden hat

- **Nichts Schweres.** Die `.env` ist vor Git sicher, war nie im Verlauf,
  und keiner der sechs Schlüssel liegt irgendwo sonst.
- **Eins BALD:** `kurator\vektor.py` spricht ChromaDB direkt an. Ein älterer
  eigener Weg aus der Zeit vor der Tür. Er schreibt heute nicht in die
  gemeinsame Datenbank — dort liegen nur die sieben bekannten Regale — aber
  der Weg daran vorbei existiert.
- **Sechs Passwörter im Klartext** in der `.env`. Das ist kein Fehler,
  sondern der Stand: eine Datei auf deinem Rechner, nicht im Repo. Es soll
  nur niemand glauben, sie wären geschützt.

## Was noch fehlt

- **Kein Zeitplan.** Er läuft von Hand; sinnvoll wäre einmal wöchentlich,
  und `--gruendlich` einmal im Monat.
- **Passwörter unter 16 Zeichen werden nicht gesucht.** Die Grenze
  herunterzusetzen würde Fehlalarme erzeugen; der ehrlichere Weg wäre, wo
  möglich einen eigenen Zugangsschlüssel statt Benutzer und Passwort zu
  verwenden.
- **Er kann nichts abschalten.** Findet er einen offenen Schlüssel, meldet
  er ihn — sperren müsstest du beim Anbieter.
