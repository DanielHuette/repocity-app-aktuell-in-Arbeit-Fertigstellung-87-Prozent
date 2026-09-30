# OBERSTE PRIORITAET: MAXIMAL VIELE TREFFER

Was zaehlt, ist die Zahl der Strukturen, die genau so getroffen werden, wie der
Trader sie gezeichnet hat. Nichts anderes wird dagegen aufgewogen - nicht
Laufzeit, nicht Rechenaufwand, nicht Einfachheit.

Ein schlechteres Ergebnis ist nie erwuenscht. Es wird nicht vorgeschlagen, nicht
als Kompromiss angeboten und nicht mit Ersparnis begruendet. Daniel am
25.09.2026: "wenn ein ergebnis schlechter ist ist es nicht erwuenscht, die
oberste prioritaet ist es maximal viele treffer zu haben, der rest ist mir
voellig scheiss egal."

# SK-Wissen des Handelsbeobachters

Abstraktes Regelwerk. Gilt fuer jedes Asset, jede Boerse, jeden Takt. Jede Regel ist aus dem
Abgleich mit den Sequenzen des Traders gewonnen und so formuliert, dass sie ohne Nachschlagen
angewendet wird.

## Begriffe

- **0**: Beginn des Impulses (Docht). **A**: Extrem des Impulses. **B**: Extrem der Korrektur
  nach A. **Lauf**: laufendes Extrem nach der Aktivierung. **C**: Extrem des Laufs, sobald das
  1,618 erreicht ist. **Impuls** = |A - 0|. **ATR**: mittlere Kerzenspanne (14 Kerzen).

## Rechnen

- Retracement-Stufe r: Preis = A + r x (0 - A). Stufen: 0,236 / 0,382 / 0,5 / 0,559 / 0,618 /
  0,667 / 0,786 / 0,882.
- Extension-Ziel k: Preis = B + k x (A - 0). Ziele 1,618 / 1,809 / 2; 2,618 = Ueberextension.
- Aus zwei beschrifteten Stufen einer Zeichnung lassen sich 0 und A exakt zurueckrechnen; eine
  dritte Stufe ist die Gegenprobe.
- Punkte werden exakt gesetzt, auch wo eine Zeichnung zur Veranschaulichung grober ist: 0, A und B
  liegen auf dem tatsaechlichen Extrem, das laufende Extrem (Lauf, C) wird immer nachgezogen. Auch ein
  einzelner Crash-Docht zaehlt als Extrem - streng nach Regel.
- Punkte liegen genau auf Hoch bzw. Tief einer Kerze (Docht). Haben zwei Kerzen dasselbe
  Extrem, zaehlt die erste.
- Das laufende Extrem (A, Lauf, C) wird live nachgefuehrt: Der Trader zieht den Zug bis zum
  hoechsten bzw. tiefsten Kurs bis jetzt, auch wenn die Kerze des Chart-Takts noch laeuft. Der
  Handelsbeobachter nimmt dafuer den kleinsten Takt (5 Minuten).
- Gerechnet wird auf den Kerzen genau des Instruments und der Boerse, auf der gehandelt wird.
  Dieselbe Struktur hat auf jeder Boerse eigene Zahlen; fremde Kerzen fuehren zu falschen Punkten.

- Fibonacci-Retracement zeigt genau die Stufen 0,5 / 0,559 / 0,618 / 0,667 / 0,786. Es wird ueber einen
  Zug gelegt, um dessen Korrekturzone zu zeigen - das kann jeder Zug sein, nicht nur 0 bis A.
- Fibonacci-Extension zeigt genau die Stufen 1,618 / 1,809 / 2 / 2,618. Nur sie misst eine Sequenz:
  gemessen von 0 bis A, angesetzt an B. Retracement und Extension nie verwechseln.
  (Daniel bestaetigt 21.09.2026)

## Sequenz bestimmen
- Matroschka-Prinzip, immer: Sequenzen werden auf Woche, Tag, 4 Stunden, 1 Stunde und 15 Minuten
  bestimmt, jeweils bullisch und baerisch. Eine Sequenz im 1-Stunden-Chart wird nur im Zusammenhang mit
  den uebergeordneten Takten und den internen Sequenzen im 15-Minuten-Chart beurteilt. Ohne die anderen
  Takte gibt es kein Urteil. (Daniel 21.09.2026)

- **Mindestimpuls:** |A - 0| mindestens 3 ATR, sonst keine Sequenz.
- **Moegliche Sequenz:** Stehen 0 und A mit Mindestimpuls, werden die Levels sofort angelegt -
  die Limit-Order liegt in der Box, bevor der Kurs dort ist.
- **Bestaetigt:** Die Korrektur erreicht 0,5-0,667 (Docht genuegt). B wandert mit bis zur
  Aktivierung.
- **Aktiviert:** Der Kurs uebersteigt A. **Abgearbeitet:** Der Kurs erreicht das 1,618.
- **Vier Fibonacci-Zuege, alle mit denselben Stufen:**
  1. bestaetigt -> 0 -> A;
  2. bestaetigt, B steht und der Kurs dreht von B weg -> B -> Extrem seit B (die Gegenbewegung
     vor der Aktivierung hat ihre eigene Box);
  3. aktiviert -> B -> Lauf (Korrektur des Laufs, Nachkauf-Zone);
  4. abgearbeitet -> 0 -> C (Gesamtkorrektur).
- **Nach dem 1,618 ist die Suche frei.** Kam der Lauf nach B um mindestens 3 ATR zurueck, ohne das
  0,5 auf 0 -> Lauf zu erreichen, ist das Ende dieser Gegenbewegung der Punkt 0 der naechsten
  Sequenz; das neue Extrem ist A. Bei mehreren Gegenbewegungen zaehlt die weiteste.
- **Eine kleinere Gegenbewegung beendet den groesseren Impuls nicht.** Aktiviert die Gegenrichtung
  eine Sequenz mit kleinerem Impuls als dem wartenden, bleibt dessen Punkt 0 stehen.
- **Interne Sequenzen gibt es, gehandelt werden sie nicht.** Punkt 0 einer offenen Sequenz haelt sie
  am Leben, sperrt aber keine kleinere Sequenz derselben Richtung: Sobald die Gegenrichtung eine
  Sequenz bestaetigt oder aktiviert, entsteht darin eine interne Sequenz (die Sequenz eines kleineren
  Takts). Sie dient zur Orientierung - ihre Levels und Ziele zeigen, wo die grosse Sequenz ihre Box
  erreicht. Gehandelt wird nur die Sequenz des eigenen Takts; die interne gehoert in den kleineren.
- **Jeder Takt hat eigene Sequenzen.** Eine Sequenz, die nur im kleineren Takt entsteht, zeichnet
  der Trader auch im groesseren Chart. Gesucht wird deshalb in jedem Takt (Woche bis 15 Minuten)
  getrennt, bis hinunter zum 5-Minuten-Takt; alle gefundenen Zuege gelten nebeneinander.
- **Nur ein Bruch von Punkt 0 beendet eine Sequenz.**
- **Ziel unter null:** Ein Zug, dessen 1,618 unter null laege, ist keine handelbare Sequenz; seine
  Levels bleiben als Zone bestehen.
- **Wochenchart:** Der ganze Anstieg vom Beginn der Kurshistorie bis zum Allzeithoch ist ein Zug;
  seine Box 0,5-0,667 ist die langfristige Kaufzone.
- **Grosser Zug:** 0,236 und 0,382 sind die Ziele der Gegenbewegung (C-Box am 0,236).

## Einstieg

- **Box 0,5 bis 0,667**, die Limit-Order am 0,5 bzw. zwischen 0,5 und 0,618. Darunter bis 0,786
  die zweite Zone; 0,882 ist die letzte Stufe vor Punkt 0.
- **Doppelter Vorteil = das beste Setup im SK-System.** Es liegt vor, wenn die Einstiegszone eines
  Zugs mit einem Extension-Ziel (1,618 / 1,809 / 2) eines anderen Zugs zusammenfaellt: Der Kurs
  erreicht dort gleichzeitig das Ziel der einen und den Einstieg der anderen Struktur. Es ist keine
  Rechenregel, die immer eintritt, sondern das Setup, auf das gewartet wird - es wird bevorzugt
  gehandelt, wenn es sich ergibt. Ohne doppelten Vorteil gilt die normale Box.
- **Ziel und Einstieg an derselben Stelle:** Liegen die Ziele einer Sequenz in der Box eines Zugs der
  Gegenrichtung (doppelter Vorteil), wird dort geschlossen und gegenlaeufig eroeffnet.

## Stop und Ziele

- Stop zwischen 0,667 und 0,786, oder knapp hinter der 2-Extension der kleineren Struktur;
  spaetestens vor Punkt 0.
- Ziel ist die C-Box von 1,618 bis 2.
- Standardannahme fuer jedes Setup: Chance-Risiko etwa 3 - das Ziel ist rund das Dreifache des
  Stopabstands (Daniel bestaetigt 18.09.2026; im Film gemessen 2,9 und 2,98).
- Teilgewinn (rund 40 %) kurz vor Punkt A der Sequenz, die gehandelt wird.
- Laeuft der Trade, wird der Stop in den Gewinn nachgezogen (knapp ueber bzw. unter den Einstieg).
- Short und Long derselben Struktur koennen gleichzeitig offen sein: Short vom Bereich nahe 0,
  Long in deren Box.

## Planung

- Der erwartete Weg wird vor dem Einstieg festgelegt: erst das Ziel der laufenden Sequenz, dann
  die Gegenbewegung.

## Urteilen ueber eine Sequenz (22.09.2026, gemessen)

- **Massstab ist das Level, nicht der Takt.** Die Sequenz, die der Trader auf einem 4h-Chart
  zeichnet, fuehrt der Kern oft im 1h-, 30m- oder 5m-Takt - mit denselben Punkten und
  denselben Extensionspreisen. Wer nur im Takt des gezeigten Charts sucht, erklaert eine
  vorhandene Sequenz zum Fehlschlag. Gepruefte Zahl: von 28 Sequenzen, die als "Kern hat keine
  passende Sequenz" gefuehrt waren, sind 16 in einem anderen Takt vorhanden, die Level exakt.
- **So wird geprueft:** `quelle\levelsuche.py <boerse> <paar> "<JJJJ-MM-TT HH:MM UTC>" <1,618>
  [2] [Toleranz %]` geht 1W, 1D, 4h, 1h, 30m, 15m, 5m, 1m durch und zeigt jede Sequenz, deren
  1,618 und 2 die Preise des Traders treffen. Zwei getroffene Level sind der Nachweis; ein
  einzelnes getroffenes Level kann Zufall sein (Beispiel Sequenz 118 und 358).
  `quelle\punktsuche.py` sucht umgekehrt die Punktfolge 0/A/B zu einem abgelesenen B und einer
  abgelesenen Spanne in den Kerzen.
- **Offene Regelfrage: Zustaende.** In mehreren Sequenzen fuehrt der Kern die Sequenz des Traders,
  aber als `ungueltig` mit Grund "Tief unter Punkt 0" (Sequenzen 365, 610) oder als `abgeloest`
  (162, 213, 392, 478, 581), waehrend der Trader sie im Bild weiter zeichnet und ihre Ziele
  benennt. Der Trader ist der Massstab - also stimmt hier entweder die Abloesebedingung oder
  die Ungueltigkeit des Kerns nicht. Das ist die naechste Sache, die am Bild entschieden wird.

## Was im Bild des Traders steht (Daniel 22.09.2026)

- **Die Reihenfolge der Level sagt die Richtung.** Steigen die Preise von 1,618 ueber 1,809 zu 2 an,
  ist die Sequenz bullisch; fallen sie, ist sie baerisch. Das gilt fuer jedes Bild und fuer jede
  abgelesene Zeile - die Richtung muss nie geraten werden.
- **Ein weisser Strich am Hoch heisst: die Sequenz ist noch nicht gueltig.** Der Trader zeigt den
  Zuschauern, was passieren muss - der Kurs muss dieses Hoch erst brechen. Solche Zeichnungen sind
  spekulativ: er zeichnet, was gueltig werden koennte. Der Kern hat sie folgerichtig noch nicht, und
  das ist kein Fehlschlag, sondern derselbe Stand.
  Punkt 0 ueberein und liegt A woanders, wird mit seinem A weitergerechnet, bis klar ist, warum er
  dieses A nimmt - statt den Sequenz als "kein Treffer" abzulegen.
- **Punkt A liegt am Docht, wo der Docht eindeutig ist** (Sequenz 32: A gehoert an den Docht bei rund
  4.660, der Kern setzt ihn woanders).
- **Eine Sequenz, die ein spaeteres Hoch ueberholt hat, ist erledigt** und darf nicht mehr als
  laufende Sequenz gezeigt werden (Sequenz 219).

## Unumstoessliche Regel (Daniel 22.09.2026)

**Ich sehe mir jedes Bild selbst an, vergroessert wenn noetig, und ich zeichne die Sequenz selbst ein.**
Ich bestimme 0, A und B am Bild. Der Kern zeichnet nicht fuer mich; er ist ein Werkzeug wie Regelwerk,
Kontext und Lehrsaetze. Kein Sequenz wird beurteilt, ohne dass ich das Bild angesehen habe. Wo meine
Lesung und der Kern auseinandergehen, ist das mein Befund am Werkzeug - und der Befund steht erst,
wenn ich die Stelle im Bild gemessen habe.

## Befund 22.09.2026: der Mindestimpuls ist die Bremse (Sequenzen 215 und 546)

Der Kern verlangt, dass der Weg von 0 nach A mindestens **3,0 Kerzenspannen** betraegt, gemessen
an der Kerze von A (MINDEST_ATR in sequenz.py). Genau daran scheitern beide Sequenzen:

- **215** (Render 1 Stunde): 0 = 1,448 am 25.06. 15:00, A = 1,543 am 25.06. 18:00. Der Weg ist
  0,095, verlangt sind 3 x 0,0325 = 0,0975. Es fehlen 2,5 Prozent - die Sequenz entsteht nicht.
- **546** (Ethereum 4 Stunden): der Weg der gezeichneten Struktur betraegt rund 79 Punkte, verlangt
  waren zu dieser Zeit 132 bis 180. Das sind etwa 1,8 statt 3,0 Kerzenspannen.

**Die Schwelle laesst sich nicht einfach senken.** Ueber alle 48 nachgemessenen Sequenzen:

| Mindestimpuls | gefundene Sequenzen | Sequenzen insgesamt |
|---|---|---|
| 3,0 | 21 | 1.290 |
| 2,0 | 23 (neu 160, 219, 556; verloren 524, 572) | 2.325 |
| 1,5 | 24 (zusaetzlich 559; 524 bleibt verloren) | 3.510 |

Der Grund fuer die Verluste steht im Kern selbst: solange eine Sequenz offen ist, ruht die Suche
(R6). Mit einer kleineren Schwelle entsteht vorher eine kleinere Sequenz, besetzt die Suche - und
die groessere, die vorher getroffen hat, wird nie gezeichnet. Die Schwelle ist also kein Filter,
der nur wegnimmt; sie entscheidet mit, welche Sequenzen ueberhaupt entstehen.

Bei 215 bleibt selbst mit kleinerer Schwelle ein Rest: der Kern zeichnet dann 0 1,448 / A 1,543 /
B 1,455 mit Ziel 1,6087, der Trader hat 1,601. Die 0,5 Prozent sind der Abstand zwischen seinem
Krypto-Index-Chart und den Binance-Kerzen.

## Nachtrag 23.09.2026: was der Umbau gebracht hat

Der Kern laeuft jetzt ohne Mindestimpuls und ohne ruhende Suche, dafuer mit dem Sieb
(Punkt 0 am Extrem der letzten 20 Kerzen) und dem Anker je Zeiteinheit.

- Belege: 23 von 25 im alten Stand, **25 von 25** mit Sieb und ohne ruhende Suche (Mindestimpuls
  noch auf 3,0), 23 von 25 ohne Mindestimpuls. Die ruhende Suche war also die groessere Bremse.
- Bildsequenzen: 22 von 48 statt 21, neu getroffen 154 und 219 (beides bullische TAO-Sequenzen),
  verloren 397 und 462.
- Der Wirkungsgrad (Anteil des Weges 0->A an der Summe der Kerzenspannen) taugt **nicht** als
  Ersatz fuer den Mindestimpuls: ab 0,2 fallen Belege weg, bei 0,35 nur noch 12 von 25.
- Was der Mindestimpuls wirklich geleistet hat: er liess A bis zum echten Hoch laufen. Ohne ihn
  entsteht am selben Punkt 0 zuerst eine kleine Sequenz mit zu fruehem A. Der Ersatz muss also
  dieselbe Aufgabe erfuellen - naheliegend und noch zu messen: der Impuls muss einen Anteil der
  Strecke 0->A der Sequenz darueber erreichen (die der Anker ohnehin liefert).


## L-2.7  Wo ein Nullpunkt liegen darf (Matroschka)

Der Nullpunkt einer Sequenz liegt dort, wo eine Bewegung endet:

- auf dem Wendepunkt der Gegenrichtung - deren A oder B, oder
- auf deren erreichtem Ziel C,
- und zwar im eigenen Takt **oder in jeder groesseren Zeiteinheit**.

Das Ziel der Tagessequenz kann der Nullpunkt einer 15-Minuten-Sequenz sein
(Beleg uuI8FUMt3Cg, 04.09.2026: "das Ziel der Tagessequenz wird ihr 0-Punkt", 82.300).
Der Trader sagt es dort selbst; die 4-Stunden- und die Stundensequenz haben an
demselben Punkt ihr A.

Liegt der Nullpunkt an keinem solchen Punkt, ist es eine Hilfssequenz: sie wird
gezeichnet, aber nicht gehandelt (L-2.2).

Keine Zahl, kein Abstand, keine Kerzenzahl - der Punkt liegt in derselben Kerze
oder er liegt es nicht.

Gemessen am 23.09.2026: alle 24 vom Kern gefundenen Belegstrukturen des Traders
erfuellen diese Regel, keine einzige faellt darunter durch.

## L-2.8  Kein spekulativer B-Punkt mehr - der CHoCH macht ihn gueltig (Daniel 24.09.2026)

Gehandelt wird nicht der noch spekulative B-Punkt, sondern ausschliesslich das
**B-C-Korrekturlevel einer gueltigen Sequenz**.

Gueltig wird eine Sequenz erst mit dem CHoCH: dem Bruch des alten C-Punktes nach
dem Gesamtkorrekturanlauf. Vorher gibt es sie nicht - auch dann nicht, wenn die
Korrektur schon sauber im Level liegt.

Die Sequenz bleibt stehen, solange der B-C-Korrekturlauf B nicht unterschreitet.

Unterschreitet der B-C-Korrekturlauf B, ohne 0 zu unterschreiten:
- der Tiefpunkt dieses Laufs wird ein **Anwaerter** auf den neuen B-Punkt,
- er wird erst dann wirklich B, wenn der Kurs danach den Hochpunkt des
  urspruenglichen B-C-Laufs ueberschreitet (CHoCH),
- fuer Shorts spiegelbildlich.

Fuer das Handeln heisst das: mit dem Bruch des B-C-Korrekturlevels sind wir
ausgestoppt. Danach wird nicht nachgefasst. Gehandelt wird erst wieder das
B-C-Korrekturlevel, das die nach dem CHoCH neu aktivierte Sequenz gibt.

Im Kern: `sequenz.py`, Felder `b_warte`, `b_warte_preis`, `choch_marke`.
Der Schalter `ERST_BEI_BRUCH` ist geloescht; das Verhalten ist fest so.


## L-2.9  Docht statt Schlusskurs, keine Toleranz (Daniel 24.09.2026)

Ein Level ist erreicht, wenn der **Docht** es beruehrt - nicht erst, wenn eine
Kerze darunter schliesst. Das gilt fuer die Gesamtkorrektur 0->C ebenso wie fuer
das B-C-Korrekturlevel.

Beim Abgleich mit der Zeichnung des Traders gibt es **keine Spanne** um den
Preis: es zaehlt der naechstliegende Kurs, sonst nichts (`abgleich.py`,
Toleranz = 0).

Gemessen am 24.09.2026 an den Belegen: der Docht bringt den Beleg
8H5xnTS4NTs (NEAR 1D long) zurueck, den der Schlusskurs verlor.


## L-2.10  Was die neue Regel kostet - ehrlich gemessen (24.09.2026)

25 Belegstrukturen, Toleranz 0:

| Kern | gefunden |
|---|---|
| vor dem 24.09. (spekulativer B erlaubt, Schlusskurs) | 25 |
| nach dem 24.09. (nur CHoCH, Docht) | 24 |

Der eine verlorene Beleg: `Ejnmg0wUEjg | BTC-USDT | 1D | short 0=97924.49
A=60000.0 B=79485.66`. Er ist genau der Fall, den L-2.8 ausschliesst - der
Trader zeichnet die Sequenz, bevor sie durch den Bruch gueltig wird.

Das ist kein Fehler des Kerns, sondern der bewusste Preis der Regel: lieber
einen gezeichneten Aufbau verpassen als einen spekulativen B-Punkt handeln.


---

# Bildrunde 1 — 24.09.2026

Vorgehen: Bilder, in denen das Fibonacci-Werkzeug sichtbar anliegt (720 von 36601) und in denen er gleichzeitig über eine der drei offenen Fragen spricht. Fragenkette durchgehen, mit seiner Zeichnung vergleichen.

## Fund 1 — die Umbenennung beim Stufenwechsel (neu, programmierbar)

Beleg: **b2gUEDmqd_o 1:11:25**, Bild `b2gUEDmqd_o-1-11-25.jpg`, SOL/USDT Tageschart Binance.

> „Aus der kleinen hellgrünen wird eine nächstgrößere, nämlich das Tief bleibt das gleiche. Null bleibt null. Startpunkt-Sequenz bleibt Startpunkt-Sequenz. Das Ziellevel C, der höchste Punkt, wird der neue A-Punkt, was ehemalig hier unten war. Und deine Korrektur in dieses Korrektur-Level, Gesamtkorrektur-Level, wird dein neuer B-Punkt."

Damit ist die Matroschka-Kette maschinell fortschreibbar:
- neuer Nullpunkt = alter Nullpunkt, unverändert
- neuer A-Punkt = der höchste erreichte Punkt in der Zielzone (das alte C)
- neuer B-Punkt = das Extrem der Korrektur ins Gesamtkorrekturlevel

**Im Bild nachgeprüft:** beschriftet sind (A) bei 78, (B) bei 62, (C) bei 93. Rechts daneben zwei gesetzte Punkte bei rund 97 und rund 78 — genau der höchste Punkt der Zielzone und das Tief der Korrektur danach. Das zweite Fibonacci-Werkzeug (0,5 bei 82,96 bis 0,786 bei 69,90) liegt über dieser neuen Strecke.

**Meine Abweichung:** Ich hätte das nicht gewusst. Frage 12 der Fragenkette fragte nur, ob das Gesamtkorrekturlevel zugleich das B-C-Korrekturlevel der nächstgrößeren Stufe ist — nicht, wie die Punkte weiterbenannt werden. Die Frage war zu schwach.

## Fund 2 — Bedingung für die nächstgrößere Struktur

Beleg: **b2gUEDmqd_o 1:10:54**

> „Wenn der Markt jetzt runterkommen würde, hier reinkommt und dann nach diesem Anlauf von mindestens 50 Prozent nach Ziellevel-Erreichung, das ist immer das Minimum, mindestens 50 Prozent und dann höheres Hoch schreibt, dann hast du eine neue Struktur, eine neue Sequenz."

Dieselbe 50-Prozent-Schwelle wie bei der Erstsequenz, angewandt auf das Gesamtkorrekturlevel. Bestätigt, dass 0.5 die durchgehende Schwelle des Systems ist — und nicht 0.382.

## Fund 3 — schwacher B-Punkt sagt den nächsten Kursverlauf voraus

Beleg: **b2gUEDmqd_o 1:11:59 / 1:12:32**

> „die hat kein starkes Fundament. Weil das Fundament stellt beispielsweise auch der B-Punkt dar. Der ist nur kurz einmal rein und wieder hoch. Das ist eher wie der schiefe Turm von Pisa."
> „Wenn wir sowas sehen, läuft der Markt gerne noch einmal ein Gesamtkorrektur-Level an."

Das ist mehr als eine Qualitätsnote: aus einem B-Punkt, der nur kurz ins Korrekturlevel sticht und sofort wieder heraus ist, folgt die Erwartung eines erneuten Anlaufs des Gesamtkorrekturlevels. Handelsfolge: nicht am B-C einsteigen, sondern auf das Gesamtkorrekturlevel warten.

**Das ist zugleich ein Zugang zur dritten offenen Frage** (ab wann heißt eine Bewegung impulsiv). Im selben Atemzug sagt er: „Ziellevel abgearbeitet und 50 Prozent Korrektur, aber sehr, sehr impulsiv wieder hoch. Dementsprechend sehr, sehr hässliche Struktur." Das Merkmal ist nicht die Steilheit allein, sondern **wie lange und wie tief der B-Punkt im Korrekturlevel stand**. Ein kurzes Reinstechen macht die Struktur schwach; ein Verweilen macht sie stabil. Das ist an einem Chart messbar, ohne dass er eine Zahl nennt.

## Fund 4 — Bestätigung von §3.1 und §4.4 am Bild

Beleg: **KhOUkdAQCXc 1:46:09**, INJ/USDT 15m

> „brauche ich immer noch den Bruch des letzten lokalen Hochs für den bullischen Aufbau, um das Tief zu bestätigen. Höheres Tief, solange das nicht passiert, ein höheres Hoch, also dieses Hoch, kann der sukzessive immer weiter absacken und sogar tiefere Tiefs reinschreiben."

Dazu eine Regel über die Gültigkeit hinaus: „wenn er sie aktiviert. Eine schlechte Sequenz, keine geile Sequenz. Würde ich auch nicht traden daher." Er handelt eine gültige Sequenz nicht, weil sie schlecht ist. Gültigkeit und Handelbarkeit sind zwei verschiedene Dinge.

## Fund 5 — Verlust des Sequenzcharakters hat einen Grund

Beleg: **IfizdLYaJ-s 0:17:25**

> Frage aus dem Chat: „Sequenz Charakter hat die Short Sequenz doch eh nicht mehr durch den Trendkanal oder?" — Antwort: „Ja, absolut verloren."

§5.4 hat damit ein Kriterium, das nicht nur Zeit ist: Läuft der Kurs in einem Trendkanal statt in Sequenzform, verliert die Sequenz ihren Charakter. Passt zu uuI8FUMt3Cg 1:03:55 („Trendkanal statt Sequenz bei 3 Touchpoints").

## Was diese Runde über das Vorgehen gelehrt hat

Bilder an einer Zitatstelle zu greifen reicht nicht — der Chart ist dort oft weggescrollt, die Punkte sind unmarkiert, er zeigt mit der Maus. Brauchbar sind nur die Bilder, in denen das Fibonacci-Werkzeug sichtbar anliegt: dort stehen die Punkte als Linien im Bild und lassen sich nachprüfen. Auswahl liegt in `quelle\_fibobilder.json` (720 Bilder) und, gekreuzt mit den Methodenstellen, in `quelle\_luecken_bilder.json` (29 Bilder zu den drei offenen Fragen).


# Bildrunde 2 — 24.09.2026

Körbe „Docht" und „impulsiv" durchgegangen. Beide Lücken geschlossen, und zwar an derselben Stelle: es ist ein und dieselbe Regel.

## Die Frage war falsch gestellt

Ich hatte gefragt: ab wann heißt eine Bewegung impulsiv, und ab welcher Länge zählt ein Docht. Beide Male habe ich nach einer Schwelle gesucht, die es nicht gibt. Der Trader misst etwas ganz anderes.

Ein Zuschauer fragt ihn wörtlich danach:

> „Verstehe das mit impulsiv, impulsiv nicht ganz. Wie müsste eine ideale Struktur aussehen? **Ideale Struktur ist sowas. Du hast einen Impuls und dann hast du eine Korrektur und Konsolidierung. Sowas. Ein schönes Konstrukt. Impulsiv, korrektiv, impulsiv.**" — NThURZNZdpk 0:24:12
> „Das, was du hier hast, ist **Impuls, Impuls, Impuls, Impuls. Alles schwach dann. Keine Konsolidierungen, keine Konstruktbildungen.**" — NThURZNZdpk 0:24:42

Gemessen wird nicht die Steilheit einer Bewegung, sondern **ob zwischen den beiden Impulsen eine Konsolidierung liegt.** Das ist an jedem Chart ablesbar und braucht keine Zahl.

## Das löst zwei Widersprüche auf einmal

**§18.4 (impulsiv als Gütesiegel und Ausschlussgrund):** Die Stellen, die eine Impuls-Impuls-Impuls-Struktur nennen, sagen nichts über ihre Güte, sondern welches Korrekturlevel dort erlaubt ist. Man darf dort das Gesamtkorrekturlevel handeln, weil man es **braucht** — das B-C hält bei dieser Struktur oft nicht. Erlaubnis, nicht Lob.

**§18.5 (Docht gültig oder nicht):** Ein Docht trägt, wenn davor konsolidiert wurde, und trägt nicht, wenn nicht.
> „Du hast 50% Level angelaufen. Ist aber sehr sehr schwach, ne? So 50% Wick. **Aber du musst festhalten, du hast halt davor immens viel Stabilisierung, Seitwärtsphase gesehen.**" — Lu2sbdCtuxs 0:39:52
> Gegenprobe: „nur den Impuls runter, einmal kurz reingewickt in das 50er Level wieder hoch, **hat auch wenig Sequenzcharakter das Ding.**" — EZcHb7fHDCk 1:07:49

## Meine eigene Korrektur aus Runde 1

In Runde 1 hatte ich aus b2gUEDmqd_o 1:11:59 geschlossen, das Merkmal sei die **Verweildauer** des B-Punkts im Korrekturlevel. Das war falsch. Der Gegenbeleg steht in zRsxxhqGtVg 0:20:35:

> „**Impulsiv, korrektiv, starkes Konstrukt, einmal kurz rein, impulsiv hoch.**"

Hier ist „einmal kurz rein" ausdrücklich stark. Der Unterschied zu b2gUEDmqd_o liegt nicht in der Dauer, sondern darin, dass dort keine korrektive Phase davor lag. Frage 4b der Fragenkette ist entsprechend ersetzt.

**Lehre:** Aus einem einzelnen Beleg eine Messgröße abzuleiten geht schief, wenn die Gegenprobe fehlt. Die Gegenprobe war einen Korb weiter und hätte in derselben Runde gefunden werden können.

## Weitere Funde

**Ausführung und Bewertung sind zu trennen.** Für die Order zählt der Docht in voller Länge:
> „ein Wick abholt … dann stehst du da mit deinem Limit am 50er" — bReMFDyXLK0 1:03:37

**Eine rein korrektive Bewegung ist keine eigene Sequenz.**
> „das ist Konsolidierung, korrektive Bewegung vor dem nächsten Impuls. Deswegen würde ich dem ganzen keinen bärischen Sequenzcharakter hier zuordnen, keine bärische Sequenz draus basteln, nichts shorten" — SwCcY7KSSg0 1:54:00

Damit sind beide Ränder Ausschlussgründe: zu impulsiv ist instabil, rein korrektiv ist gar keine Sequenz.

**Bei zu impulsiver Struktur gehört der Einstieg ans Gesamtkorrekturlevel.**
> „Ich finde den nicht so geil, weil sehr sehr impulsiv diese gesamte Struktur. Sie hätte auch die Möglichkeit durchaus das Gesamtkorrekturlevel anzulaufen." — se-nh6TTg5c 2:12:56

## Offen

Nur noch die Pivot-Frage: was ein „markantes" Hoch ist, sagt er nirgends mit einer Kerzenzahl. Der Korb A hat dafür 11 Bilder, davon sind 2 angesehen.


# Bildrunde 3 — 24.09.2026

Besserer Filter gefunden: **Zuschauerfragen.** Die drei stärksten Funde des Abends waren alle Antworten auf Fragen aus dem Chat. Wenn der Trader gefragt wird, muss er erklären, was er sonst stillschweigend tut. 284 solcher Stellen mit Bezug zur Punktwahl liegen in `quelle\_fragen_punktwahl.json`.

## Die Pivot-Frage ist beantwortet — sie war falsch gestellt

Ein Zuschauer schlägt vor, das Gesamtkorrekturlevel über eine bestimmte Strecke zu ziehen. Absage:

> „Ne. **Das hat nichts mit einem validen Einstieg nach SK-System zu tun. Ist einfach das Fibu gezogen von dem Tief zu dem Hoch. Aber das hat nichts mit einer Sequenz zu tun** und ein klassischer GKL-Entry startet im Nichts, **startet an einem lokalen Hoch deine Sequenz, startet innerhalb eines Zielbereiches deine Sequenz, macht aus SK-System sich keinen Sinn. Wo neue Strukturen entstehen könnten, wären hier unten drin.**" — 7PidOAoT3zY 0:50:16 / 0:50:47

Ich hatte gesucht: nach welcher Regel wählt er unter allen Hochs und Tiefs des Charts das richtige aus — wie viele Kerzen links und rechts. **Er wählt gar nicht aus.** Er weiß vorher, wo er zu suchen hat: im Korrekturlevel oder Zielbereich der übergeordneten Struktur. Dort gibt es nur ein Extrem, und das ist der Nullpunkt.

Deshalb nennt er nie eine Kerzenzahl. Er braucht keine.

Vierfach gegenbelegt durch die Ausschluss-Seite: KhOUkdAQCXc 0:08:53 · _IqdNTyJ5xw 1:06:06 · QEVvnlkmf0w 1:42:28 · A4GQUKfwNmw 0:31:49 — alle sagen, eine Bewegung, die „mitten im Nichts" oder „mitten in der Struktur" startet, ist keine gültige Sequenz.

**Für das Programm heißt das:** Pivot-Erkennung ist kein Mustererkennungsproblem. Der Ablauf ist umgekehrt — übergeordnete Struktur bestimmen, deren Korrekturlevel und Zielbereiche berechnen, und nur dort in der kleineren Zeiteinheit nach dem Extrem suchen. Die Matroschka löst die Pivot-Frage.

Dazu passt, dass Signifikanz ausdrücklich relativ ist:
> „**Also aus diesem Ausschnitt** haben wir signifikantes Tief und signifikantes Hoch … **in diesem Chartausschnitt** wieder höheres Tief, tieferes Hoch." — 6xhYOT3-6U8 0:21:07

## Zwei weitere Schwächemerkmale

**Docht als Nullpunkt** — was §20.4 für B sagt, gilt auch für den Startpunkt:
> „Wir haben Wick als Basis als Nullpunkt. Nie geil." — 5x2AkRB1xQI 2:08:44

**Bewegung überwiegend auf Futures entstanden** — im Regelwerk bisher gar nicht enthalten:
> „diese gesamte Bewegung primär Future basiert gewesen … Deswegen finde ich nicht geil. Deswegen trade ich es persönlich nicht." — 5x2AkRB1xQI 2:08:44
> „Plus Fundament auf Futures." — 5x2AkRB1xQI 3:07:13

Für den Handelsbeobachter prüfbar: Spot-Volumen gegen Futures-Volumen im fraglichen Abschnitt. An dieser Stelle nennt er drei Schwächemerkmale in einem Atemzug — Docht als Nullpunkt, Impuls ohne Konsolidierung, Bewegung nur auf Futures — und handelt deshalb nicht.

## Was die Fragenkette gelernt hat

Die Kette begann bisher mit „wo liegt der Nullpunkt". Das war die falsche erste Frage. Vor ihr steht jetzt: **in welchem Bereich der übergeordneten Struktur stehen wir?** Erst diese Antwort sagt, wo überhaupt gesucht wird.

Damit ist die Kette in derselben Richtung aufgebaut, in der der Trader arbeitet — von oben nach unten (§14.1), nicht vom Chartbild aufwärts.

## Stand der drei offenen Fragen

Alle drei beantwortet, und alle drei waren falsch gestellt. Jedes Mal hatte ich nach einer Zahl gesucht, die es nicht gibt:
- „Wie viele Kerzen macht einen Pivot?" → Die übergeordnete Struktur sagt, wo gesucht wird.
- „Ab wann ist eine Bewegung impulsiv?" → Nicht die Steilheit zählt, sondern ob dazwischen konsolidiert wurde.
- „Ab welcher Länge zählt ein Docht?" → Für die Ausführung immer, für die Güte nur mit Konsolidierung davor.

**Lehre für die weitere Arbeit:** Wenn der Trader zu etwas nie eine Zahl nennt, ist das kein Beleg für eine Lücke im Material, sondern ein Hinweis, dass die Frage nicht seine ist. Bevor eine Zahl gesucht wird, ist zu prüfen, ob er das Problem überhaupt so stellt.
