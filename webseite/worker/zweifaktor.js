/* ═══════════════════════════════════════════════════════════════════
 *  ZWEITER FAKTOR - gebaut, nicht scharf
 *
 *  Der erste Faktor ist die Anmeldung ueber Cloudflare Access: sie sagt,
 *  welche E-Mail-Adresse anklopft. Der zweite Faktor beweist, dass auch
 *  das Geraet dazugehoert - eine sechsstellige Zahl aus Google
 *  Authenticator, die sich alle 30 Sekunden aendert.
 *
 *  Warum das Geheimnis hier liegt und nicht in der App: es darf das Haus
 *  nicht verlassen. Die App fragt nur die sechs Ziffern ab und schickt
 *  sie hierher. So kann man aus einer auseinandergenommenen App keine
 *  Codes erzeugen.
 *
 *  SCHARF ODER NICHT
 *
 *  Solange env.ZWEI_FAKTOR_SCHARF nicht genau "ja" ist, wird nichts
 *  erzwungen: einrichten und ausprobieren geht, aber keine Seite
 *  verlangt den Code. So laesst sich alles in Ruhe aufsetzen, ohne dass
 *  jemand vor verschlossener Tuer steht.
 *
 *  UND EINE SPERRE, DIE WICHTIGER IST ALS DER REST
 *
 *  Scharf schalten geht nur, wenn mindestens ein Admin den zweiten
 *  Faktor bestaetigt hat. Sonst sperrt der Schalter genau die Person
 *  aus, die ihn wieder umlegen koennte.
 * ═══════════════════════════════════════════════════════════════════ */

import { svg as qrBild } from "./qr.js";

const VORSATZ = "zweifaktor:";
const SCHRITT_SEK = 30;
const STELLEN = 6;

/* Wie viele Schritte Abweichung geduldet werden. Eine Handyuhr, die eine
   halbe Minute nachgeht, soll nicht aussperren. Mehr als einer waere zu
   grosszuegig: er verlaengert das Zeitfenster fuer einen abgefangenen
   Code. */
const FENSTER = 1;

const BASE32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

/* ---------------------------------------------------------- Base32 */

export function base32Kodieren(bytes) {
  let bits = 0;
  let wert = 0;
  let aus = "";
  for (const b of bytes) {
    wert = (wert << 8) | b;
    bits += 8;
    while (bits >= 5) {
      aus += BASE32[(wert >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) aus += BASE32[(wert << (5 - bits)) & 31];
  return aus;
}

export function base32Dekodieren(text) {
  const rein = String(text).toUpperCase().replace(/[^A-Z2-7]/g, "");
  let bits = 0;
  let wert = 0;
  const aus = [];
  for (const z of rein) {
    wert = (wert << 5) | BASE32.indexOf(z);
    bits += 5;
    if (bits >= 8) {
      aus.push((wert >>> (bits - 8)) & 255);
      bits -= 8;
    }
  }
  return new Uint8Array(aus);
}

/* ------------------------------------------------------------ TOTP */

/** Der Code zu einem Zeitpunkt. sekunden = Unix-Zeit. */
export async function code(geheimnis, sekunden) {
  const zaehler = Math.floor(sekunden / SCHRITT_SEK);
  return await codeZuZaehler(geheimnis, zaehler);
}

export async function codeZuZaehler(geheimnis, zaehler) {
  const block = new Uint8Array(8);
  let rest = zaehler;
  for (let i = 7; i >= 0; i--) {
    block[i] = rest & 255;
    rest = Math.floor(rest / 256);
  }
  const schluessel = await crypto.subtle.importKey(
    "raw", base32Dekodieren(geheimnis),
    { name: "HMAC", hash: "SHA-1" }, false, ["sign"]);
  const roh = new Uint8Array(await crypto.subtle.sign("HMAC", schluessel, block));
  const versatz = roh[roh.length - 1] & 15;
  const zahl = ((roh[versatz] & 127) << 24) | (roh[versatz + 1] << 16)
    | (roh[versatz + 2] << 8) | roh[versatz + 3];
  return String(zahl % 10 ** STELLEN).padStart(STELLEN, "0");
}

/** Stimmt die Eingabe? Gibt den benutzten Zaehler zurueck oder null. */
export async function pruefen(geheimnis, eingabe, sekunden) {
  const rein = String(eingabe || "").replace(/\D/g, "");
  if (rein.length !== STELLEN) return null;
  const jetzt = Math.floor(sekunden / SCHRITT_SEK);
  for (let d = -FENSTER; d <= FENSTER; d++) {
    if (gleich(await codeZuZaehler(geheimnis, jetzt + d), rein)) {
      return jetzt + d;
    }
  }
  return null;
}

/* Zeichen fuer Zeichen, ohne fruehen Abbruch: sonst verraet die Laufzeit,
   wie viele Stellen schon stimmten. */
function gleich(a, b) {
  if (a.length !== b.length) return false;
  let unterschied = 0;
  for (let i = 0; i < a.length; i++) unterschied |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return unterschied === 0;
}

export function geheimnisWuerfeln() {
  const roh = new Uint8Array(20);   // 160 Bit, wie es der Standard vorsieht
  crypto.getRandomValues(roh);
  return base32Kodieren(roh);
}

/** Die Zeile, aus der Google Authenticator seinen Eintrag macht. */
export function otpauth(geheimnis, kennung, haus = "RepoCity") {
  return "otpauth://totp/" + encodeURIComponent(haus + ":" + kennung)
    + "?secret=" + geheimnis
    + "&issuer=" + encodeURIComponent(haus)
    + "&algorithm=SHA1&digits=" + STELLEN + "&period=" + SCHRITT_SEK;
}


/* ------------------------------------------- Wiederherstellungscodes
 *
 * Warum es sie braucht: angemeldet wird ueber Cloudflare Access, ein
 * Passwort gibt es hier nicht. Verlieren kann man nur den zweiten Faktor.
 * Und /aus verlangt einen gueltigen Code - den ein verlorenes Handy nicht
 * mehr liefert. Ohne diese Codes ist ein verlorenes Handy eine Sperre
 * fuer immer.
 *
 * Gespeichert wird nur der Abdruck (SHA-256), nie der Code selbst. Wer den
 * Speicher liest, findet nichts, womit er hineinkommt. Jeder Code gilt
 * genau einmal.
 */

export const CODES_ANZAHL = 8;

/** Ein Code: 10 Zeichen aus dem Base32-Alphabet, in zwei Fuenfergruppen.
 *  Rechnung: 32 Moeglichkeiten hoch 10 sind rund 1,1 Billiarden - mit der
 *  Bremse von 5 Versuchen je Stunde ist Raten aussichtslos. */
export function codeWuerfeln() {
  const roh = new Uint8Array(10);
  crypto.getRandomValues(roh);
  const zeichen = [...roh].map((b) => BASE32[b % 32]).join("");
  return zeichen.slice(0, 5) + "-" + zeichen.slice(5);
}

export function codeSaeubern(eingabe) {
  return String(eingabe || "").toUpperCase().replace(/[^A-Z2-7]/g, "");
}

export async function abdruck(code) {
  const roh = new TextEncoder().encode(codeSaeubern(code));
  const hash = await crypto.subtle.digest("SHA-256", roh);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function codesWuerfeln() {
  const codes = [];
  const abdruecke = [];
  for (let i = 0; i < CODES_ANZAHL; i += 1) {
    const code = codeWuerfeln();
    codes.push(code);
    abdruecke.push(await abdruck(code));
  }
  return { codes, abdruecke };
}

/** Bremse: fuenf Fehlversuche je Kennung und Stunde, dann ist eine Stunde Ruhe.
 *  Ohne sie waere die Wiederherstellung die schwaechste Stelle im Haus. */
const VERSUCHE_JE_STUNDE = 5;

async function versuchZaehlen(env, kennung) {
  const schluessel = VORSATZ + "versuche:" + kennung;
  const stand = Number((await env.HUB.get(schluessel)) || 0) + 1;
  await env.HUB.put(schluessel, String(stand), { expirationTtl: 3600 });
  return stand;
}

async function gebremst(env, kennung) {
  const stand = Number((await env.HUB.get(VORSATZ + "versuche:" + kennung)) || 0);
  return stand >= VERSUCHE_JE_STUNDE;
}

/* ----------------------------------------------------------- Ablage */

async function lesen(env, kennung) {
  if (!env.HUB) return null;
  const roh = await env.HUB.get(VORSATZ + kennung);
  if (!roh) return null;
  try {
    return JSON.parse(roh);
  } catch (e) {
    return null;
  }
}

async function schreiben(env, kennung, satz) {
  await env.HUB.put(VORSATZ + kennung, JSON.stringify(satz));
  return satz;
}

export function scharf(env) {
  return String(env && env.ZWEI_FAKTOR_SCHARF || "").toLowerCase() === "ja";
}

/* ------------------------------------------------------------ Wege */

export async function zweifaktor(request, env, url, wer) {
  if (!env.HUB) {
    return antwort({ fehler: "Kein Speicher. In wrangler.jsonc fehlt die "
      + "Bindung HUB." }, 503);
  }
  if (!wer || !wer.kennung) {
    return antwort({ fehler: "Erst anmelden - der zweite Faktor kommt nach "
      + "dem ersten." }, 401);
  }

  const weg = url.pathname.replace(/^\/api\/2fa/, "") || "/";
  const post = request.method === "POST";
  const kennung = wer.kennung;
  const satz = await lesen(env, kennung);
  const jetzt = Math.floor(Date.now() / 1000);

  /* --- Wie steht es? -------------------------------------------- */
  if (weg === "/stand" && !post) {
    return antwort({
      scharf: scharf(env),
      eingerichtet: !!satz,
      bestaetigt: !!(satz && satz.bestaetigt_am),
      seit: satz ? satz.bestaetigt_am || null : null,
      codes_uebrig: satz && satz.codes
        ? satz.codes.length - (satz.codes_benutzt || []).length : 0,
      hinweis: scharf(env)
        ? "Der zweite Faktor wird verlangt."
        : "Gebaut, aber nicht scharf: der Code wird noch nicht verlangt.",
    });
  }

  /* --- Einrichten: das Geheimnis wird einmal gezeigt ------------- */
  if (weg === "/einrichten" && post) {
    if (satz && satz.bestaetigt_am) {
      return antwort({ fehler: "Es ist schon einer eingerichtet. Erst "
        + "abschalten, dann neu einrichten." }, 409);
    }
    const geheimnis = geheimnisWuerfeln();
    const { codes, abdruecke } = await codesWuerfeln();
    await schreiben(env, kennung, {
      geheimnis, angelegt_am: new Date().toISOString(),
      bestaetigt_am: null, letzter_zaehler: 0,
      codes: abdruecke, codes_benutzt: [],
    });
    const zeile = otpauth(geheimnis, kennung);
    return antwort({
      otpauth: zeile,
      geheimnis,
      qr: qrBild(zeile),
      wiederherstellungscodes: codes,
      hinweis: "Diesen Eintrag jetzt in Google Authenticator anlegen - "
        + "Code scannen oder den Schluessel eintippen. Beides wird nicht "
        + "noch einmal gezeigt. Danach mit einem Code bestaetigen; vorher "
        + "gilt er nicht.",
      hinweis_codes: "Die acht Wiederherstellungscodes jetzt ausdrucken oder "
        + "abschreiben und getrennt vom Handy aufbewahren. Sie sind der "
        + "einzige Weg zurueck, wenn das Handy weg ist. Sie werden nie "
        + "wieder gezeigt - hier steht nur ihr Abdruck.",
    });
  }

  /* --- Bestaetigen: erst damit gilt er -------------------------- */
  if (weg === "/bestaetigen" && post) {
    if (!satz) return antwort({ fehler: "Nichts eingerichtet." }, 404);
    const eingabe = (await koerper(request)).code;
    const zaehler = await pruefen(satz.geheimnis, eingabe, jetzt);
    if (zaehler === null) return antwort({ fehler: "Der Code stimmt nicht." }, 400);
    satz.bestaetigt_am = new Date().toISOString();
    satz.letzter_zaehler = zaehler;
    await schreiben(env, kennung, satz);
    return antwort({ bestaetigt: true, seit: satz.bestaetigt_am });
  }

  /* --- Pruefen: das, was eine Anmeldung spaeter aufruft ---------- */
  if (weg === "/pruefen" && post) {
    if (!scharf(env)) {
      return antwort({ scharf: false, gut: true,
        hinweis: "Nicht scharf - es wird nichts verlangt." });
    }
    if (!satz || !satz.bestaetigt_am) {
      return antwort({ fehler: "Fuer diese Kennung ist kein zweiter Faktor "
        + "bestaetigt." }, 403);
    }
    const eingabe = (await koerper(request)).code;
    const zaehler = await pruefen(satz.geheimnis, eingabe, jetzt);
    if (zaehler === null) return antwort({ gut: false, fehler: "Der Code "
      + "stimmt nicht." }, 403);
    /* Ein Code gilt genau einmal. Wer ihn abfaengt, kann ihn nicht in
       derselben halben Minute noch einmal benutzen. */
    if (zaehler <= (satz.letzter_zaehler || 0)) {
      return antwort({ gut: false, fehler: "Dieser Code wurde schon "
        + "benutzt. Den naechsten abwarten." }, 403);
    }
    satz.letzter_zaehler = zaehler;
    await schreiben(env, kennung, satz);
    return antwort({ gut: true, scharf: true });
  }

  /* --- Handy weg: mit einem Wiederherstellungscode zurueck ------ *
   * Der Code loescht den zweiten Faktor, er ersetzt ihn nicht. Danach
   * richtet man ihn neu ein. Ein Code, der eine Anmeldung durchwinkt,
   * waere ein zweites Passwort - und genau das soll es hier nicht geben.
   */
  if (weg === "/wiederherstellen" && post) {
    if (await gebremst(env, kennung)) {
      return antwort({ fehler: "Zu viele Versuche. In einer Stunde wieder "
        + "versuchen." }, 429);
    }
    if (!satz || !satz.bestaetigt_am) {
      await versuchZaehlen(env, kennung);
      return antwort({ fehler: "Fuer diese Kennung ist kein zweiter Faktor "
        + "eingerichtet." }, 404);
    }
    const eingabe = (await koerper(request)).code;
    const gesucht = await abdruck(eingabe);
    const benutzt = satz.codes_benutzt || [];
    const kennt = (satz.codes || []).includes(gesucht);
    if (!kennt || benutzt.includes(gesucht)) {
      const stand = await versuchZaehlen(env, kennung);
      return antwort({ fehler: benutzt.includes(gesucht)
        ? "Dieser Code wurde schon benutzt. Jeder gilt genau einmal."
        : "Der Code stimmt nicht.",
        versuche_uebrig: Math.max(0, VERSUCHE_JE_STUNDE - stand) }, 403);
    }
    await env.HUB.delete(VORSATZ + kennung);
    await env.HUB.delete(VORSATZ + "versuche:" + kennung);
    return antwort({
      geloest: true,
      hinweis: "Der zweite Faktor ist entfernt. Richte ihn jetzt neu ein - "
        + "du bekommst dabei acht neue Wiederherstellungscodes. Die alten "
        + "gelten nicht mehr.",
    });
  }

  /* --- Neue Codes, wenn die alten aufgebraucht oder gesehen wurden --- */
  if (weg === "/codes-neu" && post) {
    if (!satz || !satz.bestaetigt_am) {
      return antwort({ fehler: "Erst den zweiten Faktor bestaetigen." }, 409);
    }
    const eingabe = (await koerper(request)).code;
    if (await pruefen(satz.geheimnis, eingabe, jetzt) === null) {
      await versuchZaehlen(env, kennung);
      return antwort({ fehler: "Dafuer braucht es einen gueltigen Code aus "
        + "der App." }, 403);
    }
    const { codes, abdruecke } = await codesWuerfeln();
    satz.codes = abdruecke;
    satz.codes_benutzt = [];
    await schreiben(env, kennung, satz);
    return antwort({
      wiederherstellungscodes: codes,
      hinweis: "Acht neue Codes. Die alten gelten ab sofort nicht mehr.",
    });
  }

  /* --- Abschalten ----------------------------------------------- */
  if (weg === "/aus" && post) {
    if (!satz) return antwort({ fehler: "Nichts eingerichtet." }, 404);
    if (satz.bestaetigt_am) {
      const eingabe = (await koerper(request)).code;
      if (await pruefen(satz.geheimnis, eingabe, jetzt) === null) {
        return antwort({ fehler: "Zum Abschalten braucht es einen "
          + "gueltigen Code." }, 403);
      }
    }
    await env.HUB.delete(VORSATZ + kennung);
    return antwort({ aus: true });
  }

  /* --- Scharf schalten: nur mit einem Weg zurueck ---------------- */
  if (weg === "/scharfschalten" && post) {
    if (wer.ebene !== "admin") {
      return antwort({ fehler: "Nur ein Admin." }, 403);
    }
    if (!satz || !satz.bestaetigt_am) {
      return antwort({ fehler: "Erst den eigenen zweiten Faktor "
        + "bestaetigen. Sonst sperrt der Schalter genau die Person aus, "
        + "die ihn wieder umlegen koennte." }, 409);
    }
    return antwort({
      bereit: true,
      hinweis: "Jetzt im Ordner universe\\webseite ausfuehren:\n"
        + "  npx wrangler secret put ZWEI_FAKTOR_SCHARF\n"
        + "und als Wert 'ja' eingeben. Zum Abschalten denselben Befehl "
        + "mit einem anderen Wert.",
    });
  }

  return antwort({ fehler: "unbekannter Weg" }, 404);
}

async function koerper(request) {
  try {
    return await request.json();
  } catch (e) {
    return {};
  }
}

function antwort(daten, status = 200) {
  return new Response(JSON.stringify(daten), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}
