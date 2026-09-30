# Social-Media-Manager

Er holt aus dem Warenausgang, was du freigegeben hast, baut daraus fertige
Beiträge und meldet später zurück, wie sie draußen gelaufen sind.

```
python main.py offen                was abholbar ist
python main.py holen                alles Freigegebene abholen und bauen
python main.py holen W0004          nur dieses Stück
python main.py plan                 was gebaut ist und noch nicht draußen
python main.py raus W0004 tiktok    als veröffentlicht vermerken
python main.py rueckmeldung W0004 "1400 Aufrufe, 22 Kommentare"
python main.py stand
```

## Was er nicht tut

**Hochladen.** Solange keine Zugänge stehen, lädst du selbst hoch — er legt
Datei, Text und Abspann fertig nebeneinander in `vault\social\<Kennung>\`.

Das ist Absicht. Ein Agent, der ohne Zugang so tut, als hätte er
veröffentlicht, ist schlimmer als einer, der es ehrlich liegen lässt: du
würdest dich auf eine Zahl verlassen, die es nicht gibt.

## Ohne deine Freigabe holt er nichts

Das ist die Stelle, an der aus deinem Ja eine Wirkung wird. `offen` zeigt
nur, was du freigegeben hast; `holen` nimmt nur das. Ein Stück, das im
Warenausgang auf dich wartet, existiert für ihn nicht.

Zusätzlich prüft er beim Bauen jedes Beitrags noch einmal, ob eine Freigabe
im Beipackzettel steht. Fehlt sie, wird der Beitrag zwar gebaut, aber als
blockiert vermerkt und nicht als bereit.

## Der Abspann

Jeder Beitrag nennt die Fotografen. Die Pexels-Lizenz verlangt das nicht —
gegenüber jemandem, dessen Aufnahme man kostenlos benutzt, ist es
selbstverständlich.

Die Namen stehen Szene für Szene im Beipackzettel. Der Abspann fasst
Doppelnennungen zusammen und behält die Reihenfolge des Auftretens:

```
Aufnahmen: Pexels / Gitti Whittaker, Pexels / Tima Miroshnichenko,
Pexels / Blue Bird, Pexels / cottonbro studio, Pexels / Alena Darmel
```

**Ohne nennbare Quelle gibt es keinen Beitrag.** Steht im Beipackzettel nur
`pexels` ohne Namen, wird das als Mangel vermerkt und der Beitrag gilt nicht
als bereit.

## Was er je Plattform kennt

| Plattform | Zeichen | Schlagworte | Abspann | Format |
|---|---|---|---|---|
| tiktok | 2200 | 5 | im Text | Hochformat |
| reels | 2200 | 5 | im Text | Hochformat |
| shorts | 5000 | 3 | im Text | Hochformat |
| linkedin | 3000 | 3 | im Text | egal |
| x | 280 | 2 | erster Kommentar | egal |

Bei X passt der Abspann nicht in 280 Zeichen — dort wandert er in den ersten
Kommentar, statt weggelassen zu werden. Welche Plattformen ein Stück
bekommt, sagt sein `taugt_fuer` im Beipackzettel.

Die Tabelle steht als `PLATTFORMEN` in `beitrag.py`.

## Die Rückmeldung von draußen

`rueckmeldung` trägt ein, wie ein Stück gelaufen ist — und schreibt es an die
**Erfahrung des Auftrags** im 2nd Brain. Das ist die dritte Rückmeldung im
Kreis:

| Wer | Sagt |
|---|---|
| Qualitätsmanager | ob es sauber war |
| du | ob es taugt |
| **hier** | was die Welt davon gehalten hat |

Ohne die dritte lernt der Agent nur, was dir gefällt, nicht was ankommt.
Sie taucht danach im Vorwissen des nächsten Auftrags auf:

```
- 2026-09-05  Auftrag 7b9d392f8aea: ja | draussen: 1400 Aufrufe in drei
  Tagen, 22 Kommentare, Abbruch meist bei Sekunde 8
```

## Wo was liegt

| Ort | Inhalt |
|---|---|
| `vault\social\<Kennung>\` | je Plattform ein Blatt, dazu die Videodatei |
| `vault\social\_plan.json` | was gebaut, was draußen, was zurückgemeldet ist |

## Was noch fehlt

- **Zugänge.** Ohne sie lädt niemand hoch. TikTok, Instagram und YouTube
  brauchen je ein Entwicklerkonto; das ist ein eigener Schritt.
- **Ein Zeitplan.** Er läuft von Hand.
- **Zahlen von selbst holen.** Die Rückmeldung tippst du heute ein. Sobald
  Zugänge stehen, kann er die Aufrufe selbst abrufen.
