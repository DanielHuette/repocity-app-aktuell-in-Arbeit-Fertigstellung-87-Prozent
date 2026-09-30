# Kostenstellenverantwortlicher / Controller

Er überwacht nicht Kosten, er überwacht **Betrieb**. Geld ist eine von vier
Größen.

## Warum das der Unterschied ist

Ein Controller, der nur Geld zählt, meldet dir am Monatsende „0,00 € verbraucht".
Das kann heißen, dass alles sparsam lief — oder dass seit drei Wochen nichts
mehr läuft und es niemand gemerkt hat.

**Das Teuerste in einem unbeaufsichtigten System ist nicht der teure Lauf,
sondern der Prozess, der still stehengeblieben ist.**

## Die vier Größen

| Größe | Was sie beantwortet |
|---|---|
| **Geld** | Was hat welche Kostenstelle verbraucht, gegen welchen Topf |
| **Takt** | Läuft dieser Teil noch — oder schweigt er länger als gewohnt |
| **Kontingente** | Was ist von den freien Abrufen übrig (Pexels, GitHub, Pixabay) |
| **Deine Eingriffe** | Wie oft du eingreifen musstest — die knappste Ressource |

```
python main.py bericht          alles zusammen, zum Lesen
python main.py kassensturz      Geld je Topf und Kostenstelle
python main.py puls             wer meldet sich, wer schweigt
python main.py kontingente      was von den freien Abrufen übrig ist
python main.py verschwendung    was bezahlt und dann verworfen wurde
python main.py warnen           nur das, was gemeldet gehört
python main.py darf prod.video.stueck 0.30
```

## Das Verbrauchsbuch

Er gibt kein Geld aus und hält nichts an. Er liest das **Verbrauchsbuch** —
`universe\zustand\verbrauch.jsonl` — in das jede bezahlte Handlung bucht.
Angehalten wird an der Stelle, die ausgeben will, über `verbrauch.darf()`.

Gebucht wird auf eine **Kostenstelle**: eine Modul-Kennung aus `Modul.kt`
(`prod.video.clip`, `wissen.scout`, `system.qm`). Jede Kostenstelle gehört zu
einem Topf, jeder Topf hat einen Monats- und einen Lauf-Deckel.

Wer heute bucht:

| Stelle | Was |
|---|---|
| `kern/vektor.py` | jede Einbettung |
| `marke/kit_bilder.py` | jedes erzeugte Bild |
| `video_agent/bildquelle.py` | jeder Pexels- und Pixabay-Abruf (Kontingent) |
| `kern/pruefstand.py` | Prüfläufe — als `herkunft: pruefung`, zählt nicht |

**Alles, was mit Geld zu tun hat, steht in `universe\kosten.json`** — Töpfe,
Deckel, Preise, Umrechnungskurs, Kontingente. Eine Stelle, nicht drei.

## Die harte Bremse

So entschieden: **ein angefangener Lauf darf über den Deckel hinaus fertig
werden.** Ein halbes Video ist niemandem gedient.

Ohne Grenze wäre das ein Blankoscheck. Deshalb gibt es die **Reißleine**: beim
Doppelten des Lauf-Deckels bricht auch ein laufender Auftrag ab. Der Faktor
steht als `reissleine_faktor` in `kosten.json`.

| Fall | Was passiert |
|---|---|
| Neuer Lauf, Monatsdeckel erreicht | fängt nicht an |
| Neuer Lauf, einzelner Schritt über dem Lauf-Deckel | fängt nicht an |
| Laufender Auftrag, Deckel überschritten | läuft zu Ende, wird gemeldet |
| Laufender Auftrag, Reißleine erreicht | bricht ab |

## Der Takt

Er lernt selbst, in welchem Abstand sich eine Kostenstelle normalerweise
meldet — aus dem Tagebuch, in das jeder Agent schreibt. Erst ab **einer Woche
Beobachtung und drei Meldungen** legt er einen Takt fest; vorher steht dort
„noch unbekannt", und das ist ehrlicher als eine Zahl aus zwei Datenpunkten.

Gerechnet wird mit dem **Median**, nicht dem Durchschnitt: ein einzelner
langer Abstand über Weihnachten soll den Takt nicht verbiegen. Ab dem
**2,5-fachen** des gewohnten Abstands gilt eine Stelle als still.

**Ungebaut ist kein Stillstand.** Ein Modul, von dem noch nie eine Meldung
kam, gibt es nur auf dem Papier — das ist etwas anderes als ein Teil, das
kaputt ist. Der Bericht nennt beides getrennt.

### Ein Befund, der das nötig macht

Die Absender im Tagebuch heißen `video_agent`, `prod.video.clip`,
`wohnungs-agent`, `github-scout` — mal der Agent, mal das Modul, mal mit
Bindestrich, mal mit Unterstrich. Wer danach gruppiert, zählt dieselbe Stelle
mehrfach. `takt.ALIAS` räumt das auf. Sauberer wäre, dass jeder Agent gleich
seine Modul-Kennung meldet — das steht noch aus.

## Was noch fehlt

- **Die Agenten sollen ihre Modul-Kennung melden**, dann ist die Alias-Liste
  überflüssig.
- **Anthropic- und OpenAI-Modellaufrufe buchen noch nicht.** Nur Einbettungen.
  Solange der Drehbuch-Schritt über einen Schlüssel läuft, fehlt diese Zahl.
- **Kein Zeitplan.** Er läuft von Hand; `warnen` gehört einmal täglich
  aufgerufen.
- **Platte und Datenbank** hast du bewusst ausgeklammert — `repos` und
  `github_cache` liegen bei 24 GB, die Vektordatenbank bei 1,15 GB. Wenn das
  später doch überwacht werden soll, ist die Stelle dafür `stand()`.
