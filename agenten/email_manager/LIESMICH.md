# Email-Manager

## Starten

Container:

    docker build -t universe-email .
    docker run -d --name email -v C:\daten:/daten ^
      -e UNIVERSE_HUB_URL=https://speedofthespirit.dev/hub ^
      -e UNIVERSE_CONTAINER_SCHLUESSEL=... universe-email

Ohne Hub, zum Ausprobieren: `zugangsdaten.beispiel.json` ausfüllen, nach
`/daten/zugangsdaten.json` legen, `empfaengerliste.beispiel.json` nach
`/daten/empfaengerliste.json`, `UNIVERSE_HUB_URL` weglassen.

Erster Lauf immer mit `-e UNIVERSE_TROCKEN=ja` — dann wird alles getan und
gemeldet, aber nichts gesendet und nichts gelöscht.

## Schalter

| Schalter | Vorgabe | Wirkung |
|---|---|---|
| UNIVERSE_HUB_URL | leer | ohne ihn: Prüfbetrieb aus lokaler Datei |
| UNIVERSE_CONTAINER_SCHLUESSEL | leer | der Ausweis, nur zum Fragen |
| UNIVERSE_ZUSTAND | /daten | muss außerhalb des Containers liegen |
| UNIVERSE_TAKT_SEKUNDEN | 1800 | 30 Minuten |
| UNIVERSE_MODELL | claude-opus-5 | Voreinstellung aus `kern/modellwahl.py`; ein Modell unter Opus wird nicht angenommen |
| UNIVERSE_SPAM_LEEREN | ja | erst melden, dann leeren |
| UNIVERSE_TROCKEN | nein | ja = nichts senden, nichts löschen |

## Was der Hub können muss

Alle Wege mit `Authorization: Bearer <Container-Ausweis>`.

| Weg | Hinein | Heraus |
|---|---|---|
| POST /zugangsdaten/anfragen | {zweck} | {vorgang} — Hub legt die Anfrage in der App vor |
| POST /zugangsdaten/abholen | {vorgang} | {zustand: wartet\|freigegeben\|abgelehnt\|verfallen, zugangsdaten} |
| POST /empfaengerliste | {zweck} | {adressen: []} |
| POST /push | die Meldung | — |

Aufbau der Zugangsdaten: siehe `zugangsdaten.beispiel.json`. Genau das wird im Hub
hinterlegt, mehr braucht es nicht.

## Meldearten, die in der App ankommen

`empfangen` · `gesendet` · `freigabe` (wollte senden, Empfänger nicht auf der Liste)
· `stoerung` · `aufraeumen` (Spam) · `lauf` (Durchlauf beendet) · `dringend`

Jede Meldung trägt eine Kurzfassung: worum es in der Mail ging und was getan wurde.

## Tonlage und Signatur

Der Agent wählt je Mail: **förmlich** (Geschäft, Behörden, Unbekannte, alles
Verbindliche — DIN-5008-Aufbau) oder **normal** (privat).

Grußformel und Signatur schreibt nicht das Modell, sondern der Code. So stehen sie
immer da und immer vollständig. Beide Signaturen werden je Postfach im Hub
hinterlegt (`signatur_foermlich`, `signatur_normal`).

Die Kennzeichnung `i. A. digitaler Assistent von …` sitzt in der förmlichen
Signatur. Sie ist zugleich DIN-konform und deckt die Offenlegung nach Artikel 50
der EU-KI-Verordnung ab, sobald die Korrespondenz geschäftlich wird.

Grundlagen liegen als Wissen bei den Transkripten:
`DIN_5008_Schreib_und_Gestaltungsregeln.md` und
`EU_KI_Verordnung_Artikel_50_Transparenzpflichten.md`.