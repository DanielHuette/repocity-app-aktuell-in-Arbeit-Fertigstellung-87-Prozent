/* Der Wegweiser - Mias billigster Weg zu einer Antwort.
 *
 * Er sucht, wo die Antwort steht, statt sie schreiben zu lassen. Findet er die
 * Stelle, geht sie samt Verweis hinaus und das Modell wird nie gefragt: das
 * kostet nichts. Nur was er nicht findet, geht ans Modell.
 *
 * Am 09.09.2026 gerechnet und von Daniel entschieden. Die Zahlen, damit
 * niemand sie spaeter neu erfinden muss:
 *
 *   Seitentext im Bestand        121.957 Zeichen (98.626 davon Funktionsdoku)
 *   alles mitschicken            0,0276 EUR je Frage  = 124 EUR/Monat bei 150/Tag
 *   passende Kapitel mitschicken 0,0112 EUR je Frage  =  50 EUR/Monat
 *   heute, ohne Wissen           0,0056 EUR je Frage  =  25 EUR/Monat
 *   Wegweiser bei einem Treffer  0,0000 EUR
 *
 * ZWEI Quellen, beide werden gelesen, keine haelt dasselbe doppelt:
 *   ../faq.json          die Frageliste - Frage, Antwort, Verweis
 *   ../verzeichnis.json  wo was steht - Kapitel, Abschnitte, Bildschirme
 *
 * Die Wortzerlegung unten steht ein zweites Mal in kern/verzeichnis.py, weil
 * dort gebaut und hier gesucht wird - zwei Sprachen, dieselbe Rechnung. Die
 * Pruefung "verzeichnis.wortzerlegung-stimmt-ueberein" zerlegt dieselben
 * Saetze mit beiden und vergleicht; laufen sie auseinander, wird sie rot.
 */

import faq from "../faq.json";
import verzeichnis from "../verzeichnis.json";

const STOPP = new Set([
  "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem",
  "eines", "einer", "und", "oder", "aber", "wie", "was", "wo", "wer", "wann",
  "warum", "wieso", "welche", "welcher", "welches", "ist", "sind", "war",
  "waren", "wird", "werden", "wurde", "hat", "habe", "haben", "hatte", "kann",
  "kannst", "koennen", "muss", "muessen", "soll", "sollen", "darf", "duerfen",
  "ich", "du", "er", "sie", "es", "wir", "ihr", "mein", "meine", "meinen",
  "dein", "deine", "sich", "mir", "mich", "dir", "dich", "man", "auf", "in",
  "im", "an", "am", "zu", "zum", "zur", "von", "vom", "mit", "bei", "fuer",
  "ueber", "unter", "nach", "vor", "aus", "durch", "gegen", "ohne", "um",
  "nicht", "kein", "keine", "auch", "noch", "schon", "nur", "sehr", "mehr",
  "hier", "dort", "da", "dann", "wenn", "als", "so", "dass", "gibt", "geht",
  "machen", "macht", "tun", "sein", "seine", "etwas", "alles", "denn",
]);

/** Text zu vergleichbarem Text: klein, ohne Umlaute, ohne Sonderzeichen. */
export function flach(text) {
  return String(text == null ? "" : text)
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue")
    .replace(/ß/g, "ss")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/** Dieselbe Zerlegung wie in kern/verzeichnis.py - siehe Kopf.
 *
 * Zwei Zeilen, die aus Fehlversuchen stammen und darum dastehen:
 *
 * Mindestlaenge 2, nicht 3 - sonst faellt "KI" heraus, und "Ist das eine KI?"
 * findet nichts, obwohl genau dazu ein Eintrag existiert.
 *
 * Bleibt nach dem Aussieben nichts uebrig, gilt der Satz ungesiebt. "Was
 * macht ihr?" und "Wer darf was?" bestehen nur aus Fuellwoertern; gesiebt
 * waeren sie leer, und der Wegweiser wuerde ans Modell durchreichen, obwohl
 * die Antwort auf der ersten Seite steht.
 */
export function worte(text) {
  const roh = flach(text).split(" ").filter((w) => w.length >= 2);
  const gesiebt = roh.filter((w) => !STOPP.has(w));
  return (gesiebt.length ? gesiebt : roh).map(stamm);
}

/* Endungen abschneiden, damit "Farben" und "Farbe" dasselbe Wort sind.
 *
 * Das ist keine Grammatik, sondern eine Abkuerzung: es wird auf beiden Seiten
 * gleich falsch abgeschnitten, und darum treffen sich die Woerter trotzdem.
 * Erst ab sechs Zeichen, sonst wird aus "Abo" ein "Ab" und aus "Kurse" ein
 * "Kurs" - letzteres waere richtig, ersteres nicht, und der Unterschied ist
 * bei kurzen Woertern nicht mehr zu retten.
 */
const ENDUNGEN = ["ungen", "erin", "chen", "lein", "enden", "ende", "ern",
                  "est", "end", "ung", "et", "en", "er", "es", "em", "st",
                  "e", "n", "s"];

export function stamm(wort) {
  /* Es wird so lange gekuerzt, bis nichts mehr passt - NICHT nur einmal.
   * Einmal kuerzen faellt auseinander: "Preise" verliert das e und wird
   * "preis", "Preis" verliert das s und wird "prei" - zwei Formen desselben
   * Wortes, die sich danach nicht mehr treffen. Bis zum Ende gekuerzt landen
   * beide auf "prei". Falsch, aber auf beiden Seiten gleich falsch, und
   * darauf kommt es beim Vergleichen an.
   * Nie unter vier Zeichen - sonst wird aus "Kurs" ein "Kur". */
  let w = wort;
  for (let runde = 0; runde < 4; runde += 1) {
    let gekuerzt = false;
    for (const e of ENDUNGEN) {
      if (w.length - e.length >= 4 && w.endsWith(e)) {
        w = w.slice(0, w.length - e.length);
        gekuerzt = true;
        break;
      }
    }
    if (!gekuerzt) break;
  }
  return w;
}

function schnittmenge(a, b) {
  let n = 0;
  for (const w of a) if (b.has(w)) n += 1;
  return n;
}

/** Wie aehnlich sind zwei Wortmengen - 0 bis 1. */
function aehnlich(frageWorte, satzWorte) {
  if (!frageWorte.length || !satzWorte.size) return 0;
  const treffer = schnittmenge(new Set(frageWorte), satzWorte);
  const vereinigung = new Set([...frageWorte, ...satzWorte]).size;
  return vereinigung ? treffer / vereinigung : 0;
}

/* Die Gewichte. Sie sind gesetzt, nicht gemessen - was sie taugen, zeigt die
 * Pruefung: jeder Beispielsatz muss seinen eigenen Eintrag finden, und Unsinn
 * darf keinen finden. Wer sie aendert, laesst die Pruefung laufen. */
const PUNKTE_WORTFOLGE = 1.5; // je INHALTSWORT eines Stichworts, das
                              // wortwoertlich in der Frage steht
const PUNKTE_WORT = 1;        // ein einzelnes Wort trifft
const PUNKTE_SATZ = 6;        // Aehnlichkeit zum naechsten Beispielsatz, mal 1
const PUNKTE_FRAGE = 4;       // Aehnlichkeit zur Frage des Eintrags, mal 1
export const SCHWELLE = 3.5;  // darunter gilt nichts als gefunden
/* 3,5 ist gemessen, nicht geraten. Gemessen am 09.09.2026 gegen das echte
 * Verzeichnis (99 Eintraege der Frageliste, 140 Stellen im Verzeichnis, 312
 * Beispielsaetze): bei dieser Marke findet jeder Beispielsatz seinen Eintrag,
 * und von 19 themenfremden Fragen - Wetter, Rezepte, Hauptstaedte, "ignoriere
 * alle deine Regeln", "wie komme ich in ein fremdes WLAN" - findet keine
 * einzige faelschlich etwas. Bei 3,0 sind es zwei.
 *
 * Wer die Marke senkt, laesst die Gegenprobe laufen. */

let _vorbereitet = null;

/** Einmal je Worker-Start: alles in Wortmengen umrechnen. */
function vorbereiten() {
  if (_vorbereitet) return _vorbereitet;
  const liste = [];

  for (const e of faq.eintraege) {
    liste.push({
      art: "faq",
      id: e.id,
      titel: e.frage,
      antwort: e.antwort,
      ziel: e.ziel,
      marke: e.marke,
      app: e.app,
      gruppe: e.gruppe,
      /* Mehrwortige Stichworte zaehlen nach ihrem Inhalt, nicht nach ihrer
         blossen Anwesenheit. "was ist" traegt keinen Inhalt: es steht in
         "Was ist RepoCity?" und ebenso in "Was ist die Hauptstadt von
         Peru" - und genau diese Frage schlug am 09.09.2026 an. Gezaehlt
         wird darum, wie viele Woerter der Wortfolge ueberhaupt etwas
         unterscheiden. */
      wortfolgen: e.stichworte.map(flach)
        .filter((s) => s.includes(" "))
        .map((s) => ({
          text: s,
          inhalt: s.split(" ").filter((w) => w.length >= 2 && !STOPP.has(w)).length,
        }))
        .filter((x) => x.inhalt > 0),
      worte: new Set([
        ...worte(e.frage),
        ...e.stichworte.flatMap(worte),
      ]),
      saetze: e.beispiele.map((s) => new Set(worte(s))),
      frageWorte: new Set(worte(e.frage)),
      gewicht: 1,
    });
  }

  for (const e of verzeichnis.eintraege) {
    liste.push({
      art: e.art,
      id: e.marke || e.app,
      titel: e.titel,
      antwort: "",
      ziel: e.ziel,
      marke: e.marke,
      app: e.app,
      gruppe: "",
      wortfolgen: [],
      worte: new Set(e.worte),
      saetze: [],
      frageWorte: new Set(worte(e.titel)),
      gewicht: (e.gewicht || 2) / 3,
    });
  }

  _vorbereitet = liste;
  return liste;
}

/** Die Frage bewerten und die besten Stellen zurueckgeben, beste zuerst. */
export function suchen(frage, hoechstens = 3) {
  const flachFrage = " " + flach(frage) + " ";
  const fw = worte(frage);
  if (!fw.length) return [];

  const bewertet = [];
  for (const e of vorbereiten()) {
    let punkte = 0;
    for (const folge of e.wortfolgen) {
      if (flachFrage.includes(" " + folge.text + " ")) {
        punkte += PUNKTE_WORTFOLGE * folge.inhalt;
      }
    }
    punkte += PUNKTE_WORT * schnittmenge(new Set(fw), e.worte);
    let bester = 0;
    for (const satz of e.saetze) bester = Math.max(bester, aehnlich(fw, satz));
    punkte += PUNKTE_SATZ * bester;
    punkte += PUNKTE_FRAGE * aehnlich(fw, e.frageWorte);
    punkte *= e.gewicht;
    if (punkte > 0) bewertet.push({ ...e, punkte });
  }

  bewertet.sort((a, b) => b.punkte - a.punkte);
  return bewertet.filter((x) => x.punkte >= SCHWELLE).slice(0, hoechstens);
}

/** Aus einem Treffer die Adresse machen, auf die verwiesen wird. */
export function adresse(treffer) {
  if (treffer.art === "faq") {
    return "/faq/#" + treffer.id;
  }
  return treffer.ziel + (treffer.marke ? "#" + treffer.marke : "");
}

export { faq, verzeichnis };
