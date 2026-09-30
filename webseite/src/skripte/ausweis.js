/* Der Ausweis der offenen Anmeldung - an genau EINER Stelle.
 *
 * Warum hier und nicht in jeder Datei einzeln: legt die eine ihn unter
 * einem anderen Namen ab als die andere sucht, gilt die Anmeldung auf
 * der einen Seite und auf der anderen nicht - und niemand sieht warum.
 * Eine Quelle je Sache.
 *
 * Er liegt im Speicher des Browsers. Das ist bewusst NICHT dasselbe wie
 * in der App: dort liegt er im Schluesselspeicher des Geraets. Ein
 * Browser hat so etwas nicht. Wer seinen Rechner teilt, meldet sich ab.
 *
 * Der Ausweis ist kein Passwort. Das Passwort verlaesst die Seite genau
 * einmal, beim Anmelden, und wird nirgends behalten.
 */

const SCHLUESSEL = "repocity.ausweis";

/* Jeder Zugriff in try/catch: im privaten Fenster und bei gesperrten
   Seitendaten wirft schon das Lesen, und dann stuende die ganze Seite. */

export function ausweis() {
  try {
    return localStorage.getItem(SCHLUESSEL) || "";
  } catch (e) {
    return "";
  }
}

/* Zusaetzlich als Cookie: ein normaler Seitenaufruf schickt keinen
   Authorization-Kopf mit - nur eigene fetch-Aufrufe tun das. Ohne Cookie
   saehe das Tor im Worker bei jedem Klick auf einen Bereich einen Gast
   und zeigte "Noch nicht freigeschaltet", obwohl man angemeldet ist.
   Secure und SameSite=Strict: nur ueber https, nur an diese Seite. */
const KEKS = "repocity_ausweis";

function keksSetzen(wert) {
  try {
    document.cookie = KEKS + "=" + encodeURIComponent(wert) +
      "; Path=/; Max-Age=" + (60 * 60 * 24 * 30) + "; Secure; SameSite=Strict";
  } catch (e) {
    /* dann gilt nur der Kopf bei eigenen Abfragen */
  }
}

function keksLoeschen() {
  try {
    document.cookie = KEKS + "=; Path=/; Max-Age=0; Secure; SameSite=Strict";
  } catch (e) {
    /* nichts zu loeschen */
  }
}

export function ausweisMerken(wert) {
  try {
    localStorage.setItem(SCHLUESSEL, wert);
  } catch (e) {
    /* Dann gilt die Anmeldung nur, solange die Seite offen ist. */
  }
  keksSetzen(wert);
}

export function ausweisVergessen() {
  try {
    localStorage.removeItem(SCHLUESSEL);
  } catch (e) {
    /* nichts zu vergessen */
  }
  keksLoeschen();
}

export function angemeldet() {
  return ausweis() !== "";
}

/** Kopfzeilen fuer einen Ruf an den Hub - mit Ausweis, wenn einer da ist. */
export function kopf(weitere) {
  const k = Object.assign({ "content-type": "application/json" }, weitere || {});
  const a = ausweis();
  if (a) k["authorization"] = "Bearer " + a;
  return k;
}
