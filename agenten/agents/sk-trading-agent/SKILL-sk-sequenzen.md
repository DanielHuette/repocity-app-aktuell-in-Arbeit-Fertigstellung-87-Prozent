# Fertigkeit: SK-Sequenzen bestimmen und handeln

Vorgehen je Markt und Takt. Die Regeln dahinter stehen in WISSEN-SK.md; diese Datei ist die
Reihenfolge. Sie wird mit jedem Abgleich gegen den Trader nachgezogen.

1. **Kerzen der Handelsboerse in jedem Takt laden** (Woche, Tag, 4 Stunden, 1 Stunde, 15 Minuten, 5 Minuten) (nicht die einer anderen Boerse). Punkte sind Dochte.
2. **Sequenzen finden** mit dem Rechenkern (`sequenz.beide`): je Richtung die offenen Sequenzen
   0-A-B (auch die kleineren daneben), ihren Zustand (bestaetigt, aktiviert, abgearbeitet)
   und den Lauf; dazu `sequenz.KANDIDATEN`, die moeglichen Sequenzen, deren Box noch nicht
   erreicht ist - dort liegt die Limit-Order schon vorher.
3. **Den passenden Fibonacci-Zug waehlen:**
   bestaetigt -> 0 -> A; bestaetigt und von B weggedreht -> zusaetzlich B -> Extrem seit B;
   aktiviert -> B -> Lauf; abgearbeitet -> 0 -> C.
4. **Groessere und kleinere Struktur pruefen:** Interne Sequenzen (`intern` im Kern) werden
   gezeichnet, aber nicht gehandelt - sie zeigen nur, wo die Sequenz des eigenen Takts ihre Box
   erreicht. Gehandelt wird die Sequenz des Takts, in dem sie entstanden ist.
5. **Einstiegszone:** 0,5 bis 0,667 des gewaehlten Zugs. Vorrang hat der doppelte Vorteil - das
   beste Setup im SK-System: die Box eines Zugs faellt mit einem Extension-Ziel (1,618 / 1,809 / 2)
   eines anderen Zugs zusammen. Danach suchen, nicht voraussetzen.
6. **Weg festlegen, bevor die Order liegt:** Ziel der Sequenz ist die C-Box 1,618 bis 2
   (= B + k x (A - 0)), danach die erwartete Gegenbewegung.
7. **Order:** Limit in der Zone (0,5-0,618), Stop zwischen 0,667 und 0,786 bzw. knapp hinter
   der 2-Extension der kleineren Struktur, spaetestens vor Punkt 0; Ziele auf den Extensions. Liegt ein Ziel in der Box der
   Gegenrichtung, dort schliessen und gegenlaeufig eroeffnen.
   Laeuft der Trade, Stop in den Gewinn nachziehen.
8. **Nach dem 1,618** ist die Suche in dieser Richtung wieder frei (siehe WISSEN-SK.md,
   "Sequenz bestimmen").


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


**Eine Sequenz wird erst mit dem CHoCH gueltig.** CHoCH = Bruch des alten C-Punktes
nach dem Gesamtkorrekturanlauf. Vor dem CHoCH gibt es keine handelbare Sequenz,
auch wenn die Korrektur schon im Level liegt. Ein spekulativer B-Punkt wird nicht
gehandelt.

**Gehandelt wird nur das B-C-Korrekturlevel** der gueltigen Sequenz - nicht das
Gesamtkorrekturlevel, solange die Sequenz nicht ins Ziellevel gelaufen ist.

Welches Level gilt (die Unterscheidung von Daniel, 23.09.2026):
- Sequenz **ist ins Ziellevel gelaufen** und korrigiert danach ins 0,5er
  Gesamtkorrekturlevel -> Folgesequenz auf demselben 0-Punkt; das C der gelaufenen
  Sequenz wird A der Folgesequenz, der Tiefpunkt der Gesamtkorrektur wird ihr B,
  gueltig ab dem Moment, in dem der Kurs wieder ueber das alte C steigt.
- Sequenz ist **nicht ins Ziellevel gelaufen**, der Kurs hat vorher gedreht ->
  es gilt das **B-C-Korrekturlevel**, nicht das Gesamtkorrekturlevel.
- Fuer Shorts jeweils spiegelbildlich.

**Wenn das B-C-Korrekturlevel bricht:**
1. Der Trade ist ausgestoppt. Es wird nicht nachgefasst.
2. Unterschreitet der Lauf B, aber nicht 0, ist sein Tiefpunkt nur ein Anwaerter
   auf einen neuen B-Punkt.
3. Erst wenn der Kurs danach den Hochpunkt des urspruenglichen B-C-Laufs
   ueberschreitet (CHoCH), steht der neue B-Punkt und die Sequenz ist wieder aktiv.
4. Gehandelt wird dann das B-C-Korrekturlevel dieser neu aktivierten Sequenz.
5. Unterschreitet der Lauf auch 0, ist die Sequenz tot (R10).

**Beruehrung zaehlt, nicht der Schlusskurs.** Ein Level ist erreicht, sobald der
Docht es beruehrt. Keine Toleranzspanne um einen Preis.

**Preis der Regel, gemessen:** 24 von 25 Belegstrukturen statt 25. Der eine
verlorene Beleg ist ein vom Trader vorweggezeichneter, noch nicht gueltiger
Aufbau. Bewusst in Kauf genommen.
