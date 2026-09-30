# Was nachweislich funktioniert — und was es kostet

Stand 07.09.2026. Für einen Ein-Personen-Betrieb mit Agentenschwarm, Budget nahe null.

**Belegstärke:** `BELEGT` kontrolliertes Experiment/Metaanalyse · `KORRELATIV` ·
`EINZELFALL` mit offengelegten Zahlen · `MEINUNG`

---

## 1 · Der stärkste Hebel: kostenlose Kleinwerkzeuge

**Hier klaffen Aufwand und Wirkung weiter auseinander als bei allem anderen.**

`EINZELFÄLLE` mit Besucherschätzungen, Stand August 2026:

| Anbieter | Werkzeug | Besuche aus der Suche |
|---|---|---|
| HubSpot | E-Mail-Signatur-Generator | ~55.000 im Monat |
| Clockify | Zeitumrechner 24h/12h | ~31.200 im Monat |
| Gusto | Stundenlohn-Rechner | ~17.800 im Monat |
| Kapwing | Meme-Baukasten | ~10.500 im Monat |
| Ahrefs | eigener Werkzeugbereich | in der Spitze ~1 Mio. im Monat |
| FreeConvert | Dateiumwandler | von 380.000 auf über 1,5 Mio. in fünf Jahren |

**Der Satz, der das für RepoCity entscheidet:** Ahrefs beziffert die Herstellung eines
solchen Rechners mit KI heute auf **„ein Durchgang, rund 1 Minute, 1,24 $".**

**Ein Agentenschwarm, der Software baut, ist genau dafür gemacht.** Naheliegend:
ein Anschreiben-Prüfer · ein Auswerter für Wohnungsanzeigen · ein Finder für
Terminkonflikte im Kalender · ein Zusammenfasser für lange Videos. Jeweils ohne
Anmeldung nutzbar, mit einem sichtbaren Hinweis „das Ganze macht der Schwarm
automatisch".

**Einschränkung, die dazugehört:** Die Zahlen stammen von einer interessierten Partei
und sind Schätzungen, keine Messungen. Die Größenordnung ist plausibel, die genauen
Werte nicht belegt.

---

## 2 · Der Wochenablauf

**Was belegt ist:** der Rhythmus, nicht der Stundenplan. Jon Yongfook (Bannerbear,
`EINZELFALL` mit Zahlen): **50 % bauen, 50 % vermarkten — nicht halbtags, sondern im
Wochenwechsel.** Eine Woche bauen, eine Woche darüber reden, was entstanden ist.
Offengelegt: rund 800 € Monatsumsatz zu Beginn, 6.000 nach sechs Monaten, später
48.000.

Daraus abgeleitet für einen Menschen mit Schwarm im Rücken — **Ableitung, nicht
Beleg**:

| Tag | Was | Zeit |
|---|---|---|
| Mo | **Ernte** — Mitschriften aus Nutzergesprächen und Erwähnungsmeldungen durchsehen, drei Themen festlegen | 60–90 Min |
| Di | **Herstellen** — ein Hauptstück (Vorführung oder Anleitung). Der Schwarm baut daraus Text, Kurzclips, Newsletter-Absatz | 2–3 Std |
| Mi | **Freigabe** — Entwürfe durchsehen, Zahlen und Behauptungen prüfen, einreihen | 45 Min |
| Do | **Antworten** — in Foren, Kommentaren, Nachrichten. **Von Hand.** | 60 Min |
| Fr | **Einträge und Beziehungen** — ein Verzeichniseintrag, eine gezielte Kontaktaufnahme, eine Bewertung erbitten | 45 Min |
| So | **Messen** — eine Zahl notieren, eine Sache streichen | 30 Min |

---

## 3 · Wo die deutschsprachige Zielgruppe ist

| Ort | Eintrag | Kosten, Stand 09/2026 |
|---|---|---|
| **alleKI.de** | offene Einreichung, 13 Kategorien, 235+ Werkzeuge gelistet, **prüft ausdrücklich Serverstandort und DSGVO**, Antwort in 5 Werktagen | **kostenlos** |
| **OMR Reviews** | Basisprofil selbst anlegen | **kostenlos**; Paket ab 575 €/Monat im Jahresvertrag; Anzeigen ab 100 €/Monat |
| **Capterra / GetApp** | Profil beanspruchen, Bewertungen sammeln | **kostenlos**; Anzeigen: Mindestgebot 2 $/Klick, **Mindestbudget 500 $/Monat** |
| **trusted.de** | redaktionelles Testportal | Preis nicht veröffentlicht |

**alleKI.de ist der auffälligste Treffer:** kostenlos, deutschsprachig — und der
DSGVO-Prüfstempel ist genau das Verkaufsargument gegenüber amerikanischen Anbietern.

**Eine Warnung aus den Quellen:** Das Forum von „Selbständig im Netz" — jahrelang der
Treffpunkt deutscher Einzelunternehmer — ist geschlossen. Deutsche Fachforen sterben;
die Gespräche sind zu LinkedIn, Facebook-Gruppen und Reddit abgewandert. **Belastbare
Mitgliederzahlen deutschsprachiger KI-Gruppen ließen sich nicht finden** — das ist zu
zählen, bevor dort Zeit hineingeht.

---

## 4 · Die Automatisierungskette

| Schritt | Werkzeug | Kosten | Lizenz |
|---|---|---|---|
| Erwähnungen finden | **F5Bot** — durchsucht Reddit, Hacker News, Lobsters alle paar Minuten, schickt E-Mail | **0 €**; 9,99 $/Mon für 20 Stichwörter | fremder Dienst |
| Ablaufmotor | **Activepieces** | 0 € selbst betrieben | **MIT — darf ins eigene Produkt** |
| Ablaufmotor (Alternative) | **n8n** | 0 € selbst betrieben | **Sustainable Use License — Selbstbetrieb ja, Weiterverkauf als eigener Dienst verboten** |
| Veröffentlichen und planen | **Postiz** | 0 € | **AGPL-3.0 — nur als getrennter Dienst** |
| Newsletter | **listmonk** | 0 € | **AGPL-3.0 — nur als getrennter Dienst** |
| Messen | **Umami** | 0 € | **MIT** |
| Server | VPS | 5–15 $ im Monat für die ganze Kette | — |

**Gesamtkosten unter 20 € im Monat.**

**Die Lizenzfalle, die leicht übersehen wird:** n8n darf **nicht** Teil des Abos
werden, das RepoCity verkauft. Activepieces (MIT) darf es. AGPL-Werkzeuge laufen als
eigenständige Dienste **neben** dem Produkt, nicht darin.

---

## 5 · Die ersten 90 Tage

**Es gibt keinen belegten 90-Tage-Ablauf mit offengelegten Ergebnissen.** Alles
Auffindbare ist Agenturwerbung ohne Zahlen. Was sich aus den belegten Einzelteilen
zusammensetzen lässt:

**Tage 1–30 — Fundament, kein Lärm.**
Kostenlose Einträge: alleKI.de, OMR Reviews, Capterra. Erwähnungsmelder mit drei bis
fünf Stichwörtern. Messung und Newsletter aufsetzen. **Zwei kostenlose Kleinwerkzeuge
bauen und veröffentlichen** — nach der Ahrefs-Rechnung kostet jedes Cent-Beträge,
nicht Tage.

**Tage 31–60 — Rhythmus.**
Der Wochenablauf läuft an. Ziel ist nicht Reichweite, sondern **eine belegte Zahl**:
Wie viele Besucher bringt Werkzeug A, und wie viele davon starten die Testphase? Zwei
weitere Werkzeuge. Newsletter jede Woche, egal wie klein die Liste.

**Tage 61–90 — ein Ereignis.**
**Erst jetzt** der öffentliche Start, wenn Newsletter-Liste und Werkzeugbesucher da
sind, die man am Starttag anschreiben kann. Ein dokumentierter Fall (Product Hunt,
2020, `EINZELFALL`): 700+ Stimmen, Platz 2 des Tages, 110-facher Besucherstrom,
20-fache Anmeldungen, 1.000+ Newsletter-Abonnenten — **aber der größte Teil kam von
einem Reddit-Beitrag, der nach 12 Stunden gelöscht wurde.** Der Ausschlag hält Tage,
nicht Wochen. Der Wert steckt in den Adressen, die hängenbleiben.

---

## 6 · Was sich nicht belegen ließ

- **Kein einziger kontrollierter Versuch** zu irgendeinem dieser Kanäle. Alles ist
  Einzelfall oder Korrelation.
- **Wiederverwertung von Inhalten** („ein Stück in zehn Formate"): kein Beleg mit
  Zahlen, nur Agenturblogs. `MEINUNG`
- **Vergleichsseiten** („X gegen Y", „Alternative zu Z"): überall empfohlen, nirgends
  mit Daten unterlegt. `MEINUNG`
- **Freie Agentur-Vorlagen** (Briefing, Freigabeketten): nichts Belastbares.
- **Deutschsprachige Gemeinschaften mit Größenangaben:** nicht gefunden. Der einzige
  harte Befund ist negativ — das SiN-Forum ist zu.
- **Stundenzahlen aus offengelegten Wochenplänen:** der Rhythmus ist belegt, die
  Stunden nicht.
