# Wohnungsportale — der legale Korridor, vermessen

Stand 07.09.2026. Rechtslage Deutschland/EU. **Kein Rechtsrat** — Darstellung der
Lage; mehrere tragende Punkte hängen am Einzelfall.

## Die kurze Antwort

| Weg | Bewertung |
|---|---|
| **Eigener Server sammelt Portalangebote in eine eigene Datenbank** | **Kein legaler Korridor.** Verstößt frontal gegen die AGB aller großen Portale, und der EuGH hat 2021 genau diesen Fall entschieden. |
| **Werkzeug läuft beim angemeldeten Nutzer** | Rechtlich deutlich besser, **aber kein Freibrief.** Trägt für Datenbankrecht und Strafrecht — trägt **nicht** gegen die AGB. |
| **E-Mail-Alerts des Nutzers auswerten + alles nach dem Fund + portalfreie Quellen** | **Sauber.** Und zugleich der einzige Weg mit echter Alleinstellung. |

---

## 1 · Was die Portale verbieten

| Portal | Klausel | Fundstelle, abgerufen 07.09.2026 |
|---|---|---|
| ImmobilienScout24 | Ziff. 8.2: „Eine automatisierte Abfrage durch Skripte, Bots, Crawler, o.ä., durch Umgehung der Suchmaske, durch Suchsoftware oder vergleichbare Maßnahmen (insbesondere Data Mining, Data Extraction) sind nicht gestattet." Erlaubt ist nur, „unter Verwendung der von ImmoScout24 zur Verfügung gestellten Online-Suchmasken einzelne Datensätze auf seinem Bildschirm sichtbar zu machen" | Verbraucher-AGB, Stand 17.02.2024 |
| ImmobilienScout24 | Ziff. 8.3: keine Verwendung der Daten „zum Aufbau einer eigenen Datenbank … und/oder für eine gewerbliche Datenverwertung" | ebd. |
| ImmobilienScout24 | Ziff. 5.3: „Ebenfalls ausdrücklich nicht gestattet ist die Account-Nutzung oder Account-Mitbenutzung durch Dritte." | ebd. |
| Kleinanzeigen | § 5 Nr. 1: keine „Crawler, Spider, Scraper oder andere automatisierte Mechanismen"; ebenso Verbot, Kontaktdaten anderer Nutzer zu sammeln | Nutzungsbedingungen, Stand 17.02.2024 |
| Immowelt/Immonet (AVIV) | Ziff. 9.3: Inhalte anderer dürfen nicht „heruntergeladen, vervielfältigt, bearbeitet" werden. **Kein** ausdrückliches Bot-Verbot gefunden | AGB gültig ab 01.10.2024 |
| wg-gesucht | robots.txt sperrt Nachrichtenversand, `userdata.php`, `/api` und mehrere Bots namentlich | wg-gesucht.de/robots.txt |

**Ziff. 8.2 und 5.3 sind der Knackpunkt:** Sie verbieten die automatisierte Abfrage
**dem angemeldeten Nutzer selbst** und die Mitbenutzung des Kontos durch Dritte. Genau
das trifft den nutzergesteuerten Weg. Realistische Folge ist Kontosperrung, nicht
Strafverfolgung — aber ein gesperrtes Konto ist für den Nutzer der Totalausfall.

---

## 2 · Was das Gesetz sagt, unabhängig von den AGB

**EuGH 03.06.2021, C-762/19 (CV-Online/Melons)** — der einschlägigste Fall: Eine
spezialisierte Metasuchmaschine über Anzeigenportale, die Inhalte kopiert, indexiert
und auf eigenen Servern durchsuchbar macht, ist verbietbare Entnahme, „wenn dadurch
die Investitionsrentabilität des Datenbankherstellers gefährdet wird".
**Das ist exakt der Server-Weg.**

**BGH 22.06.2011, I ZR 159/10 (Automobil-Onlinebörse)** — spricht für den
nutzergesteuerten Weg: Einzelne, **vom Nutzer ausgelöste** Suchabfragen über mehrere
Portale verletzten das Datenbankrecht nicht; es wurde kein wesentlicher Teil kopiert.
Einschränkung: das war vor dem heutigen Anmeldezwang.

**BGH 30.04.2014, I ZR 224/12 (Flugvermittlung)** — Screen Scraping ist nicht zwingend
gezielte Behinderung. Zentral: sich über akzeptierte AGB hinwegzusetzen ist **nicht
dasselbe** wie eine technische Schutzvorrichtung zu umgehen.

**BGH 19.04.2018, I ZR 154/16 (Werbeblocker II)** — die beste Analogie für den
nutzergesteuerten Weg: Ein vom Nutzer selbst installiertes und gesteuertes Werkzeug
ist keine gezielte Behinderung. **Vorsicht:** BGH 2025, I ZR 131/23 (Werbeblocker IV)
hat aufgeworfen, ob das Umschreiben der Seitenstruktur im Browser in Rechte am
Computerprogramm eingreift — zurückverwiesen, **offen**.

**§ 202a StGB** — erfordert das Überwinden einer „besonderen Zugangssicherung". Wer
sich mit **eigenen, gültigen Zugangsdaten** anmeldet, überwindet nichts. Strafrechtlich
unauffällig. **Umgekehrt beginnt genau dort das Risiko**, wo Captchas umgangen, Konten
geteilt oder Bot-Erkennung ausgetrickst wird.

**EuGH 15.01.2015, C-30/14 (Ryanair)** — paradox, aber wichtig: Ist die Datenbank
**nicht** geschützt, darf der Betreiber vertraglich *mehr* verbieten als das Gesetz.
Die Schranke des § 87e UrhG greift nur bei geschützten Datenbanken.

**DSGVO:** Inserate privater Vermieter enthalten personenbezogene Daten. Eine
serverseitige Vorratssammlung braucht Rechtsgrundlage und Informationspflichten —
ein weiteres Argument gegen den Server-Weg.

---

## 3 · Der Grund, warum „Grauzone" hier besonders teuer wäre

**ImmobilienScout24 verkauft die Funktion selbst.** Der „Bewerbungsassistent" im Abo
„Suchen+ Unlimitiert" sendet „in deinem Namen eine professionelle Kontaktanfrage".

Ein fremdes Werkzeug greift damit ein **bezahltes Produktmerkmal des Portals** an. Das
erhöht die Wahrscheinlichkeit einer Abmahnung erheblich — unabhängig davon, wer am
Ende recht bekäme. Und ein Rechtsstreit gegen ein Portal dieser Größe ist für einen
Einzelgründer kein Risiko, sondern das Ende.

**Alle legalen Aggregatoren** (Nestoria, Trovit, Immobilo) arbeiten mit
**Feed-Verträgen**, nicht mit Auslesen.

---

## 4 · Die legalen Wege, nach Aufwand sortiert

### 1. Die E-Mail-Meldungen des Nutzers auswerten — der saubere Einstieg

Der Nutzer richtet **beim Portal selbst** seine Suchagenten ein und leitet die
Benachrichtigungen an eine eigene Adresse weiter. Er verarbeitet **seine eigene Post**.
Keine automatisierte Abfrage der Suchmaske, kein fremder Zugriff auf sein Konto.

**Auflagen, damit es sauber bleibt:** je Nutzer verarbeiten, **keine gemeinsame
Angebotsdatenbank** aufbauen, kurz löschen. Sonst greift Ziff. 8.3 (gewerbliche
Datenverwertung).

**Das passt zum bestehenden Bau:** Der E-Mail-Agent existiert bereits.

### 2. Alles nach dem Fund — hier gilt keine Portalklausel

Kriterienprüfung, Priorisierung, Anschreiben-Entwurf, Unterlagenmappe, Fristen,
Nachfassen, Terminverwaltung. **Nichts davon ist durch Portal-AGB gedeckelt** — und
es ist der Teil, an dem Suchende tatsächlich scheitern.

### 3. Portalfreie Quellen — hier liegt die Alleinstellung

| Quelle | Warum sie zählt |
|---|---|
| Kommunale Wohnungsgesellschaften | eigene Angebotsseiten und Wartelisten, keine Portalklausel |
| Genossenschaften | dito, und oft die günstigsten Wohnungen |
| Makler direkt über **OpenImmo-XML** | der kostenlose Branchenstandard, mit dem Makler ihre Objekte an **beliebige Empfänger** ausspielen — ein direkter Feed-Vertrag ist realistisch |
| Zeitungsanzeigen, Aushänge, Stellen für den Wohnberechtigungsschein | von keinem Portal abgedeckt |

**Das ist der eigentliche Wettbewerbsvorteil.** Wer nur die Portale spiegelt, ist eine
schlechtere Kopie. Wer die Quellen zusammenführt, **die die Portale nicht haben**, hat
etwas Eigenes.

### 4. Offizielle Schnittstelle ImmoScout24 — passt nicht

Existiert, aber: Vertrag und Registrierung nötig (Registrierungen werden „ohne
Begründung" abgelehnt), kostenpflichtig, Speicherung „zeitlich beschränkt auf einen
Tag", Markenkennzeichnungspflicht. Und ausdrücklich: „Die Lizenznehmer:innen dürfen
den Endkund:innen nicht die Möglichkeit einräumen, selbst und unmittelbar Abfragen
über die API" zu richten. **Das schließt das Produktbild in der Standardform aus.**

---

## 5 · Das Anschreiben

Vorschreiben, Nutzer gibt frei, Nutzer sendet — rechtlich klar besser, aber nicht
risikofrei.

§ 7 Abs. 2 Nr. 2 UWG betrifft **Werbung**; die Antwort eines Suchenden auf ein Inserat
ist keine Werbung, sondern die erbetene Kontaktaufnahme.

**Warnschuss aus der Gegenrichtung:** LG Stuttgart, 05.06.2025, 33 O 10/25 —
Makler-Nachrichten über das Kleinanzeigen-Postfach ohne Einwilligung sind Spam,
„schon ein einziger Verstoß begründet einen Unterlassungsanspruch".

**Grenzen, die einzuhalten sind:** keine Massenversendung an Inserate außerhalb des
Suchprofils · keine Eigenwerbung im Text · sichtbare Freigabe je Nachricht · Begrenzung
der Menge.

---

## 6 · Was ungeklärt ist — Anwaltsfragen

- Ist ein Immobilienportal eine geschützte Datenbank nach § 87a UrhG? **Kein
  einschlägiges deutsches Urteil gefunden.**
- Ist Ziff. 8.2 gegenüber Verbrauchern in dieser Breite AGB-fest (§ 307 BGB), oder
  überdehnt sie den gesetzlichen Schutz?
- Wo genau liegt die Linie zwischen „liest die geöffnete Seite" und „ruft selbst ab"?
- Reichweite von Werbeblocker IV für browserseitige Werkzeuge
- DSGVO-Rolle: Auftragsverarbeiter des Nutzers oder eigener Verantwortlicher?
- Vertragliche Bewertung der Alert-Weiterleitung nach Ziff. 8.3

---

## 7 · Was daraus folgt

**Der Wohnungs-Brückenkopf trägt — aber nicht als Portal-Spiegel.**

Der Satz ändert sich damit. Nicht mehr „Alle Wohnungsportale auf einmal", sondern:

> **Die Wohnungen, die du auf den Portalen nicht siehst — und die Anfrage schon
> geschrieben, wenn du sie brauchst.**

Das ist ehrlicher, rechtlich sauber, und es ist ein Versprechen, das ein Portal
nicht einlösen kann.
