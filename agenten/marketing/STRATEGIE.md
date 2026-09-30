# Agentische Marketing-Abteilung — Strategie

Stand 2026-09-04. Erarbeitet, nicht abgenommen.
Ziel: Bekanntheit nach Fertigstellung des Universe, kostengünstig und wirksam.

## Befund: es gibt nichts zu kaufen

Die Kategorie "Marketing-Agent" ist auf GitHub praktisch leer — nur Demos
(`Agentfy`, `Marketing-Swarm-Template`, `kai-cmo-harness`, alle unter 800 Sterne,
keine belastbare Basis).

**Brauchbar sind genau drei Sachen:**

| Repo | Sterne | Lizenz | Wozu |
|---|---|---|---|
| `gitroomhq/postiz-app` | 34,7k | AGPL-3.0 | Der Verteiler. Docker, API, 14 Netze. Node — läuft als Dienst hinter unserer Python-Schnittstelle. AGPL ist unkritisch, solange wir ihn nicht forken und weiterverkaufen. |
| `harry0703/MoneyPrinterTurbo` | ~110k | MIT | Python 3.11, Docker, Kurzvideo am Fließband mit edge-tts. Steht schon in unserer Bestandsaufnahme. |
| `AJaySi/AI-Writer` | 1,2k | MIT | Python/FastAPI, Recherche → Text. Vorlage für Texter und SEO. |

## Sieben Rollen

1. **Beobachter** — HN-Algolia, Reddit, GitHub-Trending, RSS. Kostenlos.
2. **Themenfinder** — verknüpft Beobachtung mit dem 2nd Brain, liefert drei Themen am Tag **mit Beleg**.
3. **Texter** — eine Kernaussage, daraus Fassungen je Kanal.
4. **Bildner** — MoneyPrinterTurbo-Straße, Terminal-Aufnahmen. Echte Vorführung schlägt KI-Bild.
5. **Planer** — Kadenz, Sperrfristen, Dublettenprüfung über Kanäle hinweg.
6. **Verteiler** — schreibt ausschließlich gegen die Postiz-Schnittstelle.
7. **Auswerter** — Plausible/Umami, GitHub-Sterne, Herkunft der Besucher. Rückkopplung an den Themenfinder.

**Der Verteiler veröffentlicht nicht selbst.** Freigabe durch dich, wie beim Warenausgang
der Video-Werkstatt. Das ist zugleich die rechtliche Absicherung.

## Kanäle: was kostet, was sperrt

| Kanal | Kosten | Grenze |
|---|---|---|
| Bluesky | 0 € | Freie Schnittstelle, großzügige Grenzen. Bestes Verhältnis. |
| Mastodon | 0 € | Bots erlaubt bei Kennzeichnung. Kleines, aber richtiges Publikum. |
| dev.to | 0 € | ~7,1 Mio. Besuche/Monat, 48 % über Suche. **`canonical_url` setzen**, sonst rankt dev.to statt uns. |
| YouTube | 0 € | 10.000 Einheiten/Tag, ein Upload kostet 1.600 → rund 6 am Tag. Reicht. |
| LinkedIn | 0 € | Eigenes Profil erlaubt. Firmenseite braucht Freigabe, 1–2 Wochen. |
| Discord | 0 € | Webhook, trivial. |
| X | teuer | Freie Stufe abgeschafft. 0,015 $ je Beitrag, **0,20 $ mit Link**. |
| Reddit | — | Technisch möglich, **sozial gefährlich**. Nur von Hand. |
| TikTok | 0 € | Ohne Audit sind alle Beiträge zwangsweise privat. Praktisch gesperrt. |
| Instagram | 0 € | Meta-Prüfung nötig, Grenzen wurden 2025 unangekündigt stark gesenkt. |

## Was nachweislich wirkt

- **Show HN**: Titelseite bringt 5.000–30.000 Besucher in 24 Stunden, bei offener Software
  500–2.000 Sterne. Aber nur **2,3 %** aller Einreichungen schaffen es dorthin; nötig sind
  30–50 Stimmen in der ersten Stunde. Der Mittelwert eines Show HN liegt bei **2 Punkten**.
- **Product Hunt**: Platz 1–3 bringt 5.000–15.000 Besucher, dafür 400+ Stimmen nötig.
  Platz 11–30 bringt unter 700 Besucher — also lohnt nur der Vollangriff.
- **dev.to**: kein Einzeltreffer, sondern Kadenz; die Suche trägt.

## Was nicht funktioniert — ehrlich

- **Automatisiertes Reddit-Posten.** 90/10-Regel, gleicher Text in mehreren Unterforen
  führt zur stillen Sperre über die ganze Seite.
- **LinkedIn-Automatisierungswerkzeuge.** Die Nutzungsbedingungen verbieten Bots. Nur die offizielle Schnittstelle.
- **X-Interaktionsautomatisierung** (Auto-Folgen, Auto-Liken) — die am härtesten durchgesetzte Regel.
- **TikTok** vor bestandener Prüfung — sinnlos.
- **Allerwelts-Beiträge aus dem Sprachmodell.** Auf HN fallen Buzzwords sofort durch.
  Unsere Verbotsliste (revolutionär, nahtlos, KI-gestützt, Game-Changer) gilt hier doppelt.

## EU-KI-Verordnung Art. 50

Gilt seit 02.08.2026, Übergang bis 02.12.2026.

- **Bild, Ton, Video:** maschinenlesbare Markierung Pflicht → C2PA in die Video- und Musikstraße.
- **Text:** Kennzeichnung nur bei Themen öffentlichen Interesses — und **entfällt bei
  menschlicher Redaktion**. Genau deshalb gibst du frei.
- Bußgeld bis 15 Mio. € oder 3 % Umsatz.
- Praktisch: sichtbarer Hinweis "KI-gestützt erstellt, redaktionell geprüft" im Profil und unter Videos.

## Fahrplan

**Vor dem Start (zwei Wochen):** Postiz-Container, Beobachter, Themenfinder, Texter.
Konten auf Bluesky, Mastodon, dev.to, LinkedIn, YouTube. Täglich ein Beitrag über den
Bau selbst. Kosten 0 €.

**Startwoche:** **Dienstagmorgen Show HN** (8–10 Uhr Ostküstenzeit, Titel ohne Superlative,
laufende Vorführung verlinkt, den ganzen Tag von Hand antworten). Bei Erfolg drei Tage
später Product Hunt. Reddit erst danach, von Hand, ein Unterforum.

**Danach dauerhaft:** dev.to ein Artikel je Woche (canonical auf die eigene Domain),
YouTube zwei Kurzvideos je Woche **aus der eigenen Straße**, Bluesky/Mastodon/LinkedIn
täglich, X zwei bis drei Beiträge je Woche ohne Link (Link in die Antwort).

**Monatlich:** VPS 6–12 € · Modell-Kosten 10–20 € · X 5 € · Plausible 9 € · Domain 1 €
= **30–50 €**. Alles andere kostenlos.

## Der eigentliche Hebel

RepoCity vermarktet sich am glaubwürdigsten dadurch, dass es **sein eigenes
Marketingmaterial selbst herstellt** — sichtbar, mit offenem Protokoll. Das ist kein
Werbespruch, das ist die Vorführung.
