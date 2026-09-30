# Marketing — was belegt ist und was auf der Platte liegt

Stand 07.09.2026. Drei parallele Recherchen: der eigene Repo-Bestand, die
Belegelage zu Methoden, die Quellen für aktuelle Themen.
Ergänzt `STRATEGIE.md` (04.09.) und die Vorrecherche `marketing-strategie.md`.

**Belegstärke steht an jeder Aussage** — sonst behandelt ein Agent später eine
Korrelation wie ein Naturgesetz:
`BELEGT` kontrolliertes Experiment oder Metaanalyse · `KORRELATIV` Zusammenhang
gemessen, Ursache offen · `EINZELFALL` · `MEINUNG`

---

## 1 · Was im eigenen Bestand liegt und ungenutzt ist

Durchsucht: `github_cache` (329 Repos, Ordner- und Inhaltssuche), `mein_ki_gehirn\repos`
(1.523 Notizen), `vault\20_Repos`.

| Pfad unter `github_cache\` | Was es tut | Lizenz | Wofür hier | Dateien |
|---|---|---|---|---|
| `openclaudia_openclaudia-skills` | 78 ausführende Marketing-Skills: SEO-Prüfung, Sichtbarkeit in KI-Antworten, ICP, Newsletter, Anzeigen, Umwandlungsrate, Inhalte | MIT | **Rückgrat der Abteilung** | 100 |
| `msitarzewski_agency-agents` | 319 Rollen-Agenten, davon 34 Marketing, 9 Vertrieb, 7 bezahlte Medien, dazu Phasen-Ablaufpläne | MIT | Personal des Schwarms | 348 |
| `phuryn_pm-skills` | ~70 Skills auf der Strategieebene: Zielgruppe, Positionierung, Wettbewerb, Marktgröße, Preis, Wachstumsschleifen | MIT | **Die Ebene, die den anderen fehlt** | 141 |
| `coreyhaines31_makerskills` | 21 Skills für den Betrieb: Beitragsrotation, Beitragsabruf, Firmengedächtnis, Zeitpläne | MIT | Betrieb, Anschluss ans 2nd Brain | 86 |
| `coreyhaines31_marketingskills` | 65+ Marketing-Skills, `product-marketing` als Wurzel, die anderen fragen sie ab | MIT | war schon bekannt | 461 |
| `nexu-io_open-design` | ~150 Design-Skills, darunter Werbetexte, Marketing-Psychologie, Anzeigen der Konkurrenz auslesen | Apache 2.0 | Werbemittel — **nur die 357 Skill-Dateien**, nicht das Repo | 13.200 |
| `panniantong_agent-reach` | Lese-Zugänge zu X, LinkedIn, Reddit, YouTube, Instagram, RSS | MIT | Beobachten — **liest nur, veröffentlicht nicht** | 120 |
| `posthog_posthog` | Produkt- und Reichweitenmessung, selbst betreibbar | MIT (außer `ee/`) | Wirkungsmessung | 47.557 |
| `blader_humanizer`, `petergyang_no-ai-slop`, `millwright-labs_minto-pyramid-skill` | KI-Sprache entfernen, Botschaftsaufbau nach Minto | MIT | Redaktionsstufe | klein |
| `knadh_listmonk` | Newsletter, selbst betreibbar | **AGPL-3.0** | nur als **getrennter Dienst** — kein Code-Einbau | 507 |
| `mvanhorn_printing-press-library` | Katalog fertiger Kommandozeilen-Werkzeuge | **keine Lizenzdatei** | intern ja, weitergeben nein | 92.453 |

**Die drei wichtigsten, genauer:**

**`openclaudia_openclaudia-skills`** — keine Ratgeber, sondern ausführende Skills.
`icp-builder` liefert fertige Raster mit Firmenmerkmalen, Kaufauslösern und
Ausschlusskriterien. `geo-analysis`, `geo-query-finder`, `geo-difficulty` und
`ai-citations-report` decken die Frage ab, ob man in KI-Antworten zitiert wird.
Dazu `newsletter`, `email-sequence`, `demand-gen`, `programmatic-seo`,
`launch-strategy`, `pricing-strategy`, `product-marketing`, `competitor-analysis`,
`content-calendar`.
**Warnung:** `ai-citations-report` ist nur eine Hülle um eine **kostenpflichtige**
fremde Schnittstelle. Viele weitere Skills brauchen Ahrefs-, SemRush- oder
Similarweb-Konten. **Der Code ist frei, die Datenquellen sind es nicht.**

**`msitarzewski_agency-agents`** — fertige Rollen, auf Deutsch umzubenennen (Regel 1).
Im Ordner `marketing/` unter anderem Sichtbarkeit in KI-Antworten, E-Mail-Strategie,
Veröffentlichung über mehrere Plattformen, Pressearbeit. Dazu `strategy/playbooks/phase-5-launch.md`
und `strategy/runbooks/scenario-marketing-campaign.md` — ein durchgeschriebener
Kampagnenablauf mit Übergabevorlagen. **Ein knappes Drittel zielt auf chinesische
Plattformen und ist hier nutzlos.**

**`phuryn_pm-skills`** — die Strategieebene: Zielgruppe, Brückenkopf-Segment,
Markteinführung, Wachstumsschleifen, Wettbewerbskarte, Positionierung,
Wertversprechen, Marktgröße, Nordstern-Kennzahl, Preis. Sauber in Bausteine
geschnitten, jeder mit eigener Beschreibung — **direkt als Abteilungsstruktur
übernehmbar**.

### Was im Bestand fehlt

- **Belege und Studien zur Werbewirkung: nichts.** Gezielt nach Metaanalysen, Byron
  Sharp, Ehrenberg, Binet, kontrollierten Versuchen gesucht — kein Treffer im ganzen
  Bestand. Es gibt Rezepte, aber keine Beweisgrundlage. Muss von außen kommen.
- **Kein Werkzeug, das selbst veröffentlicht.** `agent-reach` liest nur. Postiz ist
  die einzige Verteilstelle.
- **Kein deutschsprachiges Material.** Alles Englisch oder Chinesisch.
- **Kein Rechtsrahmen für Werbung** (Einwilligung für Newsletter, Impressum, UWG).

---

## 2 · Was belegt ist — und was der Agent nicht nachplappern darf

### Die ersten hundert Nutzer

**Es gibt dazu keine belastbaren Zahlen.** Gezielt nach kontrollierten Studien
gesucht; gefunden wurden Blogs, Interviews, Sammlungen von Erfolgsgeschichten.
*Das ist selbst der Befund:* Wer behauptet, es gebe einen belegten Weg zu den ersten
hundert Nutzern, hat keinen Beleg.

**Eine Ausnahme, und sie ist eine Warnung.** `BELEGT` (natürliches Experiment,
5.742 Produktstarts auf Product Hunt, Okt. 2016 – Okt. 2018): An einem typischen Tag
sind neun von zehn Nutzern dort Männer. Produkte für weibliche Zielgruppen wuchsen
ein Jahr nach dem Start **45 % weniger**. An Tagen mit zufällig mehr Frauen schrumpfte
der Unterschied gegen null. **Die Reaktion auf einer Startplattform misst das Publikum
der Plattform, nicht den Markt.** Ein schwacher Start dort ist kein Urteil über das
Produkt — ein starker keine Marktbestätigung.
→ NBER w28882

### Empfehlungsmechanik — hier ist die Datenlage gut und widerspricht dem Üblichen

**Empfohlene Kunden sind wertvoller, aber der Vorsprung läuft ab.** `KORRELATIV`
(deutsche Großbank, 5.181 empfohlene gegen 4.633 nicht empfohlene Kunden, 33 Monate):
rund **25 % mehr Deckungsbeitrag**, **18 % seltener gekündigt**, auf sechs Jahre rund
**40 € mehr wert**. **Aber:** der Ertragsvorsprung war nach ca. **857 Tagen**
aufgebraucht. Deutsche Daten.
→ Schmitt/Skiera/Van den Bulte 2011, Journal of Marketing

**Prämie nur für den Werber ist die schlechteste Bauart.** `BELEGT` (randomisierte
Feldexperimente): Beide *nicht* selbstsüchtigen Varianten — 50/50 und alles an den
Geworbenen — schlagen die Werber-Prämie.
→ Jung/Bapna/Gupta/Sen, JMIS 38(1) 2021

**Der Gegenbefund, der RepoCity direkt trifft.** `BELEGT` (1 Feldexperiment n=480 +
4 Online-Experimente): Bei **innovativen** Produkten *senkt* eine **öffentlich
sichtbare** Empfehlungsprämie die Empfehlungsbereitschaft gegenüber gar keiner Prämie.
Grund: Wer etwas Neues empfiehlt, will klug wirken; eine sichtbare Prämie zerstört
diesen Grund. Abgeschwächt durch **stille** Prämien (der Geworbene erfährt nichts
davon), **große** Prämien und **beidseitige** Prämien.
**Folge: Eine laut beworbene „Wirb einen Freund"-Mechanik kann hier nach hinten
losgehen.**
→ Unintended reward costs, JAMS 2019

### Testphase und Umwandlung

**Längere Testphase hilft — aber anders als erwartet.** `BELEGT` (randomisiertes
Feldexperiment, **N = 680.588** Nutzer, 190 Länder, Juli 2022 – Juli 2024),
3 gegen 7 Tage:

| | 3 Tage | 7 Tage | Änderung |
|---|---|---|---|
| Testphase gestartet | 0,856 % | 0,951 % | **+11,1 %** |
| **sofortige** Umwandlung | — | — | kein belegbarer Unterschied |
| **verzögerte** Umwandlung | 0,144 % | 0,205 % | **+42,4 %** |
| Abos gesamt | 0,368 % | 0,445 % | **+20,9 %** |

**Wer nur die erste Woche misst, hält die Wirkung fälschlich für null.**
→ Frontiers in Psychology 2025, CC BY 4.0

**Umwandlungsraten nach Modell** `KORRELATIV` (Befragung, 200 B2B-Produkte, Jan. 2026,
überwiegend 1–10 Mio. $ Umsatz — **nicht** Ein-Personen-Betriebe): Median 8 %.
Kostenlose Basisversion 3–5 % · Test ohne Karte 4–6 % · Test **mit** Karte 25–35 %.

### Deutschland — was Kampagnen unmöglich macht

**Kaltakquise per Telefon bei Firmen ist enger als fast alle glauben.** `BELEGT`
(höchstrichterlich): Bundesverwaltungsgericht **6 C 3.23, 29.01.2025** — öffentlich
zugängliche Telefonnummern begründen **keine** mutmaßliche Einwilligung nach § 7
Abs. 2 UWG. Und: Das berechtigte Interesse der DSGVO kann keine Werbeform
rechtfertigen, die das Wettbewerbsrecht verbietet.

**Die Bestätigungsmail beim Newsletter darf keine Werbung enthalten.** `EINZELFALL`
(OLG München 29 U 1682/12) — sonst ist sie selbst unzulässige Werbung.

**Kündigungsbutton ist Pflicht** für ein Abo-Modell: § 312k BGB, gut sichtbar, ohne
Anmeldung erreichbar. Fehlt er, kann jederzeit fristlos gekündigt werden.

### Was ein Ein-Personen-Betrieb mit KI schafft

`KORRELATIV` (160.143 Produktstarts, April 2020 – Juli 2025): Der Markteintritt von
Einzelgründern stieg rund **90 % stärker** als der von Teams. **Der Deckel:** An der
Spitze änderte sich nichts — Teams steigerten ihren Anteil unter den Top 10 von 50 %
auf 53 %. **KI senkt die Eintrittsschwelle, hebt aber nicht die Qualitätsspitze.**

`BELEGT` als Gegengewicht: KI-Produktivitätsgewinne bei geistiger Arbeit liegen in
kontrollierten Versuchen bei **+15 bis +56 %**, nicht bei Faktor 10 — und am größten
bei den *schwächsten* Bearbeitern.
→ Noy/Zhang Science 2023 (n=453) · Brynjolfsson/Li/Raymond QJE 2025 (5.179
Mitarbeiter) · Demirer et al. (4.867 Entwickler)

### Messen ohne ausreichende Fallzahlen

**Wirkung an einer Zeitreihe ablesen.** Aus der Vergangenheit wird vorhergesagt, was
ohne die Maßnahme passiert wäre; gemessen wird die Abweichung. **Braucht keine zweite
Nutzergruppe.** `BELEGT`, Software frei (Apache 2.0).
→ Brodersen et al., Annals of Applied Statistics 9(1) 2015 · CausalImpact

**Laufend prüfen dürfen, statt auf eine Endzahl zu warten.** Normale A/B-Tests werden
falsch, wenn man zwischendurch hineinsieht und abbricht. Dieses Verfahren erlaubt
genau das. `BELEGT`
→ Johari/Koomen/Pekelis/Walsh, Operations Research 70(3) 2022

**Regionale Tests** brauchen viele vergleichbare Regionen — **für einen Anbieter ohne
Kunden noch nicht anwendbar.** Vormerken, nicht bauen.

### Die sieben Sätze, die der Agent nicht nachplappern darf

1. „Empfehlungsprämien wirken immer positiv" — **falsch bei innovativen Produkten**
2. „Prämie an den Werber" — **schlechteste Variante**
3. „Empfohlene Kunden sind dauerhaft profitabler" — **nur die halbe Zeit**
4. „Ein starker Start auf einer Launch-Plattform bestätigt den Markt" — **nein**
5. „Längere Testphase bringt nichts" — **Messfehler**, der Effekt kommt verzögert
6. „Wir rufen einfach Firmen an, B2B ist erlaubt" — **in Deutschland nein**
7. „KI macht einen Einzelnen so stark wie ein Team" — **Eintritt ja, Spitze nein**

---

## 3 · Woher die aktuellen Themen kommen

### Google Trends — der Stand

Die offizielle Schnittstelle ist **seit Juli 2025 im Alpha-Stadium** und nimmt weiter
nur Bewerbungen an. Kein Preis, keine Abfragegrenze veröffentlicht. **Nicht planbar.**

`pytrends` ist **am 17.04.2025 archiviert** worden; letzte Veröffentlichung 4.9.2 vom
April 2023, 136 offene Fehlermeldungen. Der Aufruf, den es macht, antwortet
**schon beim ersten Versuch mit „zu viele Anfragen"**. Automatisiertes Abgreifen
verstößt zudem gegen Googles Nutzungsbedingungen.

**Was heute funktioniert und erlaubt ist:** der RSS-Ausgang von Google Trends —
`trends.google.com/trending/rss?geo=DE`. Kein Schlüssel, kein Konto, von Google selbst
bereitgestellt. Geprüft am 07.09.2026.

**Lesefallen** `BELEGT`:
- **Wiederholte identische Abfragen liefern verschiedene Zahlen.** Zwischen drei
  Stichproben derselben Anfrage nur Korrelationen von **0,50**, bei seltenen Begriffen
  bis **0,01**. Eine deutsche Untersuchung (Uni Hannover/Oldenburg mit dem NDR, 2020)
  fand: schon **eine Stunde Abstand** ergibt stark abweichende Verläufe.
- **0–100 ist immer relativ** zum Zeitraum und zur Region. Zwei getrennte Abfragen
  sind nie vergleichbar. 100 heißt „Höchststand dieser Abfrage", nicht „viel".

**Als Vorhersagegröße** `BELEGT`: Google Flu Trends meldete **in 100 von 108 Wochen**
zu hohe Werte, im Februar 2013 mehr als das Doppelte. Ein simples Modell mit drei
Wochen alten Behördendaten war besser.
→ Lazer/Kennedy/King/Vespignani, Science 2014
**Merksatz: Ergänzung, nie alleiniger Wert.**

### Die Quellen im Vergleich

| Quelle | Kostenlos | Zugang | Grenze | Erlaubt | Wofür |
|---|---|---|---|---|---|
| **Google Trends RSS** | ja | kein Schlüssel | nicht veröffentlicht | ja | Tagesthemen DE, grobe Größe |
| **Wikipedia-Abrufzahlen** | ja | kein Schlüssel | aussagekräftige Kennung verlangt | ja, Daten CC0 | **echte absolute Zahlen** |
| **Hacker News** (Firebase + Algolia) | ja | kein Schlüssel | Doku: keine Grenze | ja | Entwicklerpublikum |
| **RSS heise, t3n, golem** | ja | keiner | keine | ja | **deutschsprachige Themenlage** |
| **Reddit** | ja | **Anmeldung zwingend** | 100/Minute | ja mit Konto | Fachforen |
| — ohne Anmeldung | — | — | wird blockiert | nein | — |
| **YouTube-Schnittstelle** | ja | Schlüssel | 10.000 Einheiten/Tag, davon nur **100 Suchen** | ja | knapp, nur gezielt |
| **Google/YouTube-Suchvorschläge** | ja | kein Schlüssel | keine | **Graubereich** | echte deutsche Suchformulierungen |
| **GitHub** | ja | Token | 5.000/h mit Token | ja | neue Projekte |
| **Mastodon** | ja | meist ohne Konto | 300 je 5 Min | ja | Fachnischen |
| **Bluesky** | ja | ohne Konto möglich | großzügig | ja | schnelle Tech-Diskussion |
| **X** | nein | kostenpflichtig | — | ja | auslassen |
| **pytrends** | ja | Bibliothek | gesperrt | **nein** | nichts |

### Ein aktuelles Thema aufgreifen — was belegt ist

**Die Beweislage ist schwach.** Praktisch alle kursierenden Zahlen zum Wirkungsgewinn
stammen aus Marketing-Blogs ohne offengelegte Methode. `MEINUNG`

**Halbwertszeit eines Beitrags** `KORRELATIV` (eine Quelle, 5,6 Mio. Beiträge aus 2025,
nicht begutachtet): X **52 Minuten** · Facebook **86 Minuten** · Instagram **~18
Stunden** · LinkedIn **~23 Stunden** · YouTube **~10,6 Tage**.
**Für ein Videoprodukt die gute Nachricht: ein Tagesrhythmus reicht.**

**Das Risiko ist dagegen belegt:** Marken-Fehltritte in sozialen Medien senken
Markenvertrauen und Sympathie messbar. `EINZELFALL/KORRELATIV`
**Eine unsymmetrische Wette** — die Verlustseite ist belegt, die Gewinnseite nicht.

**Folge für den Agenten:** Themen als *Anlass* nutzen, nicht als Inhalt. Kein
Aufspringen auf Unglücke, Politik, Todesfälle, Prominente. Fachthemen aufgreifen —
neues Modell, neues Werkzeug, neue Rechtslage —, nicht Tagesaufregung.

### Zwei Bauregeln daraus

1. **Ein Thema wird erst vorgeschlagen, wenn es in mindestens zwei Quellen auftaucht.**
   Das fängt das Stichprobenrauschen ab.
2. **Jeder Vorschlag trägt seinen Beleg mit** — Quelle, Datum, Rohwert. Wo nur Google
   Trends anschlägt, wird der Wert als „relativ, nicht vergleichbar" gekennzeichnet.

### Rechtliches beim Aufgreifen fremder Themen

- **KI-Kennzeichnung, seit 02.08.2026 in Kraft** (Art. 50 EU-KI-Verordnung):
  künstlich erzeugte Bild-, Ton- und Videoinhalte **maschinenlesbar markieren** und
  erkennbar machen. **Trifft dieses Produkt direkt.**
- **Werbekennzeichnung** (BGH 09.09.2021, I ZR 90/20 u. a.): Gegenleistung von Dritten
  → kennzeichnen. Werbung für **eigene** Produkte braucht keine Kennzeichnung, wenn
  der geschäftliche Zweck offensichtlich ist. Im Zweifel kennzeichnen — kostet nichts.
- **Bildzitat** (§ 51 UrhG): nur mit **Belegfunktion**. Nicht zur Verschönerung.
  Quelle und Urheber immer nennen.
- **Marken** (§ 14 MarkenG): Namen nennen ist erlaubt, wenn es der Beschreibung dient.
  **Keine fremden Logos im Vorschaubild.**
- **Bilder erkennbarer Personen** (§ 22 KUG): grundsätzlich Einwilligung nötig.
- **Praxisregel:** nur eigene oder frei lizenzierte Bilder, fremde Quellen
  **verlinken statt einbetten**, Marken nur im Fließtext.

---

## 4 · Was in die Wissensdatenbank darf

Frei lizenziert, Volltext einspeisbar:

| Quelle | Lizenz |
|---|---|
| OpenStax: Principles of Marketing — vollständiges Lehrbuch, 17 Kapitel | CC |
| MIT OCW 15.810 Marketing Management, ~20 Vorlesungsunterlagen | CC BY-NC-SA |
| Ehrenberg-Bass Open-Access-Berichte, 12 Stück | offen |
| Generative AI Fuels Solo Entrepreneurship (arXiv 2605.10291) | **CC BY 4.0** |
| Testphasen-Feldexperiment, Frontiers in Psychology 2025 | **CC BY 4.0** |
| Brodersen et al., Inferring Causal Impact (AoAS 2015) | Open Access |
| CausalImpact — Software und Anleitung | **Apache 2.0** |
| § 312k BGB, Gesetzestext | amtlich, gemeinfrei |
| OLG München 29 U 1682/12, Volltext | amtliche Entscheidung |
| EXIST Monitoringbericht Nr. 5 | Behördenveröffentlichung |
| IHK Stuttgart, Übersicht erlaubter Werbewege | frei abrufbar |

Frei abrufbar, aber **verlinken statt kopieren** (Rechte beim Herausgeber):
NBER w28882 · NBER w31161 · Noy & Zhang (MIT-Fassung) · Demirer et al. ·
Schmitt/Skiera/Van den Bulte (Autorenfassung) · Binet & Field, Effectiveness in
Context · LinkedIn B2B Institute · Sethuraman-Metaanalyse · Lewis & Rao ·
Gordon et al. · Bitkom-Studie 2026

**Nicht einspeisen, nur zitieren:** JAMS 2019 · JMIS 2021 · IJRM 2017 ·
ChartMogul-Bericht · Operations Research 2022

**Jede Notiz bekommt ein Feld „Belegstärke".** Ohne das behandelt der Agent die
60/40-Regel wie ein Naturgesetz — sie beruht auf selbstselektierten
Award-Einreichungen und ist korrelativ; für B2B nennen Binet & Field selbst rund
46/54. Ebenso ist die 95-5-Regel eine Modellrechnung, kein Messergebnis.

---

## 5 · Die ehrlichen Lücken

1. **Kontrollierte Studien zu den ersten hundert Nutzern existieren nicht.** Der Agent
   muss das wissen, sonst zitiert er Blogs als Belege.
2. **Kausale Wirkung von Forenpräsenz eines Anbieters:** kein Beleg für „geh in Foren,
   es wirkt".
3. **Verzeichnis- und Marktplatzeinträge für kleine Anbieter:** kein Beleg.
4. **Preisexperimente bei sehr kleinen Anbietern:** nichts. **Die 14,99 € und 29,99 €
   sind durch nichts belegbar — das ist eine Setzung, keine Rechnung.** Ehrlicher
   wäre, sie als Annahme zu kennzeichnen.
5. **Deutsche Fachverzeichnisse:** nur Eigenwerbung der Anbieter, keine unabhängige
   Messung.
6. **Integrations- und Partnerlisten als Startkanal:** kein Beleg.
7. **Eine eigenständige deutsche Trendquelle mit belastbaren Zahlen:** nicht gefunden.

---

## 6 · Was daraus unmittelbar folgt

**Zwei Bauentscheidungen, die aus den Belegen direkt kommen:**

1. **Die Empfehlungsmechanik wird still und beidseitig gebaut**, nicht als sichtbare
   Werber-Prämie. Bei einem neuartigen Produkt ist die Standardbauart belegbar
   schädlich.
2. **Die Testphasen-Umwandlung wird über mindestens acht Wochen gemessen**, nicht über
   die Testdauer — sonst hält man eine Wirkung von +21 % für null.

**Und die eine Entscheidung, die alles andere blockiert:** für wen genau ist RepoCity,
und was ist der eine Satz? Ohne Zielgruppenbeschreibung und Botschaftshaus produziert
jede Marketing-Abteilung nur Text.
