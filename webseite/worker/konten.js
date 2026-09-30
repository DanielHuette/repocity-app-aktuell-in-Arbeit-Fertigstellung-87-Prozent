/* Die Konten des Universe — wer ist das, und was darf er.
 *
 * Bis hierher kam die Antwort aus Cloudflare Access: wer im Browser
 * angemeldet war, wurde erkannt, alle anderen waren "nutzer". Die App
 * bekam davon nichts mit und war deshalb für jeden Free. Access schickt
 * seine Kennung nur im Browser mit.
 *
 * Darum hat der Hub jetzt eigene Konten. Ein Konto ist:
 *
 *   E-Mail  ─►  Passwort (nie im Klartext gespeichert)  ─►  Rolle
 *
 * Drei Rollen, mehr gibt es nicht:
 *
 *   admin   Daniel. Sieht alles, kommt überall hin, erzeugt Einladungen.
 *   beta    Beta-Tester. Wie ein Nutzer, sieht aber auch, was noch nicht
 *           freigegeben ist. Wird man nur mit Einladungscode.
 *   nutzer  Alle anderen.
 *
 * Was hier NICHT liegt: die Zugangsdaten fremder Dienste. Die liegen im
 * Tresor (tresor.js), hinter einer eigenen Tür und verschlüsselt. Ein
 * Kontospeicher, der auch die Passwörter zu Postfach und Portalen hält,
 * verliert bei einem einzigen Fehler alles auf einmal.
 *
 * Speicher: KV-Bindung KONTEN.
 *
 *   konto:<email>        das Konto selbst
 *   sitzung:<abdruck>    eine offene Anmeldung
 *   code:<CODE>          eine Einladung
 *   neustart:<abdruck>   ein laufendes "Passwort vergessen"
 *   sperre:<email>       Fehlversuche
 *
 * Bei Sitzung und Neustart liegt im Schlüssel der ABDRUCK, nicht der Wert:
 * wer den Speicher liest, hält damit trotzdem keinen gültigen Ausweis in
 * der Hand.
 */

/* Wie lange eine Anmeldung hält, ohne dass man sich neu anmelden muss.
   30 Tage: kurz genug, dass ein verlorenes Handy nicht ewig offen bleibt,
   lang genug, dass niemand sich wöchentlich neu anmeldet. */
const SITZUNG_SEK = 60 * 60 * 24 * 30;

/* Ein Rückstell-Link ist 30 Minuten gültig. Wer eine Mail liest, tut das
   in dieser Zeit; alles darüber ist nur ein längeres Fenster für den,
   der die Mail abfängt. */
const NEUSTART_SEK = 60 * 30;

/* Nach so vielen Fehlversuchen ist das Konto für eine Viertelstunde zu.
   Gerechnet: fünf Versuche je 15 Minuten sind 480 am Tag. Gegen ein
   Passwort aus zehn Zeichen ist das nichts — und für einen Menschen, der
   sich vertippt, reicht es dreimal. */
const FEHLVERSUCHE = 5;
const SPERRE_SEK = 60 * 15;

/* Runden der Passwort-Verwahrung.
 *
 * Die Empfehlung für dieses Verfahren (PBKDF2 mit SHA-256) liegt bei
 * 210.000 Runden. Cloudflare lässt aber höchstens 100.000 in einem Zug zu
 * und wirft darüber einen Fehler — am 09.09. am Netz gemessen: die
 * Anmeldung antwortete mit 500 statt 401, weil die Rechnung gar nicht
 * erst lief.
 *
 * Darum drei Durchgänge zu je 100.000, jeder mit dem Ergebnis des
 * vorigen: 3 × 100.000 = 300.000 Runden, mehr als die Empfehlung
 * verlangt. Kosten: rund 240 ms je Anmeldung — spürbar für den, der
 * Passwörter durchprobiert, unmerklich für den, der sich anmeldet.
 */
const RUNDEN = 100000;
const DURCHGAENGE = 3;

const MINDESTLAENGE = 10;

function json(daten, status = 200) {
  return new Response(JSON.stringify(daten), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

/* ----------------------------------------------------------- Werkzeug */

const roh = new TextEncoder();

function b64(puffer) {
  const bytes = new Uint8Array(puffer);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function zufall(bytes = 32) {
  return b64(crypto.getRandomValues(new Uint8Array(bytes)));
}

/** Der Abdruck eines Ausweises. Aus ihm lässt sich der Ausweis nicht
 *  zurückrechnen — darum steht er im Speicher und nicht der Ausweis. */
async function abdruck(text) {
  return b64(await crypto.subtle.digest("SHA-256", roh.encode(text)));
}

/** Vergleich, der immer gleich lange dauert. Ein Vergleich, der bei der
 *  ersten falschen Stelle abbricht, verrät über die Dauer, wie viel schon
 *  stimmte. */
function gleich(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  if (a.length !== b.length) return false;
  let rest = 0;
  for (let i = 0; i < a.length; i++) rest |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return rest === 0;
}

/** Aus dem Passwort wird ein Abdruck, aus dem sich das Passwort nicht
 *  zurückrechnen lässt. Das Salz sorgt dafür, dass zwei Menschen mit
 *  demselben Passwort verschiedene Abdrücke bekommen. */
async function passwortAbdruck(passwort, salzB64, runden = RUNDEN,
                               durchgaenge = DURCHGAENGE) {
  const salz = Uint8Array.from(
    atob(salzB64.replace(/-/g, "+").replace(/_/g, "/")),
    (c) => c.charCodeAt(0),
  );
  let stoff = roh.encode(passwort);
  let bits = null;
  for (let i = 0; i < durchgaenge; i++) {
    const schluessel = await crypto.subtle.importKey(
      "raw", stoff, "PBKDF2", false, ["deriveBits"],
    );
    bits = await crypto.subtle.deriveBits(
      { name: "PBKDF2", hash: "SHA-256", salt: salz, iterations: runden },
      schluessel, 256,
    );
    /* Das Ergebnis ist das Passwort des nächsten Durchgangs. So kommen
       drei erlaubte Rechnungen auf dieselbe Arbeit wie eine verbotene. */
    stoff = new Uint8Array(bits);
  }
  return b64(bits);
}

function saubereEmail(wert) {
  return String(wert || "").trim().toLowerCase().slice(0, 200);
}

/** Sieht das wie eine E-Mail-Adresse aus? Keine Wissenschaft — es geht
 *  darum, Tippfehler zu fangen, nicht darum, das Format zu beweisen.
 *  Ob die Adresse wirklich jemandem gehört, zeigt erst die Bestätigung. */
function emailPlausibel(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);
}

/** Was an einem Passwort auszusetzen ist — oder "" wenn nichts. */
function passwortMangel(passwort) {
  const p = String(passwort || "");
  if (p.length < MINDESTLAENGE) {
    return `Das Passwort braucht mindestens ${MINDESTLAENGE} Zeichen. ` +
      "Länge hilft mehr als Sonderzeichen.";
  }
  if (p.length > 200) return "Das Passwort ist zu lang (höchstens 200 Zeichen).";
  return "";
}

/* ------------------------------------------------------------ Konten */

/* Wer Admin ist - aus ADMIN_LISTE, nicht aus dem Code. Auch abo.js und
   index.js fragen hier, damit es die Regel nur einmal gibt. */
export function adminListe(env) {
  return String(env.ADMIN_LISTE || "dhuette@gmx.net,info@speedofthespirit.dev")
    .split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
}

async function kontoLesen(env, email) {
  const roh_ = await env.KONTEN.get("konto:" + email);
  if (!roh_) return null;
  try {
    return JSON.parse(roh_);
  } catch (e) {
    return null;
  }
}

async function kontoSchreiben(env, konto) {
  await env.KONTEN.put("konto:" + konto.email, JSON.stringify(konto));
  return konto;
}

/** Was von einem Konto nach draußen geht. Nie der Abdruck, nie das Salz. */
function nachAussen(konto) {
  return {
    email: konto.email,
    rolle: konto.rolle,
    stufe: konto.stufe,
    bestaetigt: !!konto.bestaetigt,
    eingerichtet: !!konto.eingerichtet,
    angelegt: konto.angelegt,
  };
}

/* ---------------------------------------------------------- Sitzungen */

async function sitzungAnlegen(env, konto) {
  const ausweis = zufall(32);
  await env.KONTEN.put(
    "sitzung:" + (await abdruck(ausweis)),
    JSON.stringify({ email: konto.email, seit: new Date().toISOString() }),
    { expirationTtl: SITZUNG_SEK },
  );
  return ausweis;
}

/** Wer klopft — aus dem mitgeschickten Ausweis. Gibt das Konto zurück
 *  oder null. Ein abgelaufener Ausweis ist wie keiner. */
/** Der Ausweis aus dem Kopf - oder, bei einem normalen Seitenaufruf, aus dem
 *  Cookie repocity_ausweis, das ausweis.js beim Anmelden setzt. Ein Browser
 *  schickt bei einem Klick keinen Authorization-Kopf; ohne das Cookie waere
 *  jeder angemeldete Mensch am Tor ein Gast. */
function ausweisAus(request) {
  const kopf = request.headers.get("authorization") || "";
  if (kopf.toLowerCase().startsWith("bearer ")) return kopf.slice(7).trim();
  const kekse = request.headers.get("cookie") || "";
  const m = /(?:^|;\s*)repocity_ausweis=([^;]+)/.exec(kekse);
  if (!m) return "";
  try {
    return decodeURIComponent(m[1]).trim();
  } catch (e) {
    return "";
  }
}

export async function kontoZuAusweis(env, request) {
  if (!env.KONTEN) return null;
  const ausweis = ausweisAus(request);
  if (!ausweis) return null;
  const eintrag = await env.KONTEN.get("sitzung:" + (await abdruck(ausweis)));
  if (!eintrag) return null;
  try {
    const { email, seit } = JSON.parse(eintrag);
    const konto = await kontoLesen(env, email);
    if (!konto) return null;
    /* Seit wann diese Anmeldung laeuft - das Dashboard zeigt es als deine
       Laufzeit. Wird nicht gespeichert, nur mitgegeben. */
    konto.sitzungSeit = seit || null;
    /* Wer sein Passwort zurücksetzt, will genau das: alle offenen
       Anmeldungen sind ab dann wertlos. Die einzelnen Sitzungen lassen
       sich im Speicher nicht auffinden, darum trägt das Konto den
       Zeitpunkt — was davor ausgestellt wurde, gilt nicht mehr. */
    if (konto.sitzungenAbGueltig && seit &&
        new Date(seit) < new Date(konto.sitzungenAbGueltig)) {
      return null;
    }
    return konto;
  } catch (e) {
    return null;
  }
}

/* --------------------------------------------------------- Einladungen */

async function codeEinloesen(env, code) {
  const schluessel = "code:" + String(code || "").trim().toUpperCase().slice(0, 40);
  const eintrag = await env.KONTEN.get(schluessel);
  if (!eintrag) return null;
  let daten;
  try {
    daten = JSON.parse(eintrag);
  } catch (e) {
    return null;
  }
  if (daten.offen <= 0) return null;
  if (daten.gueltigBis && new Date(daten.gueltigBis) < new Date()) return null;
  return { schluessel, daten };
}

/* ------------------------------------------------------ Post an den Nutzer

   Der Hub verschickt selbst keine Mail — er hat kein Postfach. Er legt sie
   in den Ausgang, und der Rechner holt sie ab und verschickt sie über das
   Postfach, das der E-Mail-Manager ohnehin bedient. Ein zweiter Maildienst
   wäre ein zweiter Zugang, ein zweiter Preis und eine zweite Stelle, an der
   etwas ausfallen kann.

   Solange kein Rechner läuft, bleibt die Mail im Ausgang liegen. Das sagt
   die Antwort dem Nutzer auch — sie behauptet nicht, etwas sei unterwegs. */

async function inDenAusgang(env, brief) {
  if (!env.HUB) return false;
  const id = "postausgang:" + Date.now().toString(36) + "-" +
    Math.random().toString(36).slice(2, 8);
  await env.HUB.put(id, JSON.stringify({
    id,
    an: brief.an,
    betreff: brief.betreff,
    text: brief.text,
    angelegt: new Date().toISOString(),
    abgeholt: false,
  }), { expirationTtl: 60 * 60 * 24 * 7 });
  return true;
}

/* ---------------------------------------------------------------- Wege */

export async function konten(request, env, url) {
  if (!env.KONTEN) {
    return json({ fehler: "Der Hub hat keinen Kontospeicher. In " +
      "wrangler.jsonc fehlt die Bindung KONTEN." }, 503);
  }

  const weg = url.pathname.replace("/api/konten", "") || "/";
  const post = request.method === "POST";

  let satz = {};
  if (post) {
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
  }

  /* --- Anlegen ------------------------------------------------------- */
  if (weg === "/anlegen" && post) {
    const email = saubereEmail(satz.email);
    if (!emailPlausibel(email)) {
      return json({ fehler: "Diese E-Mail-Adresse sieht nicht richtig aus." }, 400);
    }
    const mangel = passwortMangel(satz.passwort);
    if (mangel) return json({ fehler: mangel }, 400);

    if (await kontoLesen(env, email)) {
      /* Wir sagen NICHT "die Adresse gibt es schon" — das wäre eine
         Auskunft darüber, wer hier ein Konto hat. Stattdessen dasselbe
         wie beim Erfolg, und wer die Adresse besitzt, bekommt eine Mail
         mit dem Hinweis. */
      await inDenAusgang(env, {
        an: email,
        betreff: "Anmeldeversuch bei RepoCity",
        text: "Jemand hat versucht, mit deiner Adresse ein Konto bei " +
          "RepoCity anzulegen. Du hast dort bereits eines. Warst du das " +
          "nicht, kannst du diese Nachricht wegwerfen — es ist nichts " +
          "passiert.",
      });
      return json({ angelegt: true, bestaetigung: "unterwegs" });
    }

    /* Rolle: Admin steht fest, beta gibt es nur mit Einladung.
     *
     * Hier stand vom 08. bis zum 09.09.2026 `if (false)`. Der Rest einer
     * abgebrochenen Gegenprobe, die diese Stelle verstellt und nicht
     * zurueckgesetzt hatte - und der Rest wurde eingecheckt. Wirkung: die
     * Adressen aus ADMIN_LISTE bekamen die Rolle "nutzer". Damit konnte
     * niemand Einladungen erzeugen, also auch kein Beta-Tester entstehen.
     * Aufgefallen ist es, weil zwei Pruefungen rot standen; gefunden wurde
     * es erst, als die Erklaerung "das ist das Tageslimit des Speichers"
     * nachgeprueft wurde und nicht stimmte.
     *
     * Wer eine Gegenprobe abbricht, sieht danach nach, was sie stehen
     * gelassen hat. */
    let rolle = "nutzer";
    if (adminListe(env).includes(email)) {
      rolle = "admin";
    } else if (satz.code) {
      const eingeloest = await codeEinloesen(env, satz.code);
      if (!eingeloest) {
        return json({ fehler: "Diesen Einladungscode kenne ich nicht, " +
          "oder er ist aufgebraucht." }, 400);
      }
      rolle = eingeloest.daten.rolle === "beta" ? "beta" : "nutzer";
      eingeloest.daten.offen -= 1;
      eingeloest.daten.eingeloest = (eingeloest.daten.eingeloest || []).concat(email);
      await env.KONTEN.put(eingeloest.schluessel, JSON.stringify(eingeloest.daten));
    }

    const salz = zufall(16);
    const konto = {
      email,
      rolle,
      /* Die gebuchte Stufe. Sie steht hier, damit die App sie ohne einen
         zweiten Weg erfährt; gepflegt wird sie von der Kasse (abo.js).
         Ein neues Konto hat immer die unterste. */
      stufe: "free",
      salz,
      runden: RUNDEN,
      durchgaenge: DURCHGAENGE,
      abdruck: await passwortAbdruck(satz.passwort, salz),
      bestaetigt: false,
      eingerichtet: false,
      angelegt: new Date().toISOString(),
    };
    await kontoSchreiben(env, konto);

    /* Bestätigung der Adresse. Bis sie da ist, kann man sich anmelden —
       gesperrt wird nur, was nach außen wirkt (siehe /stand). Ein Konto,
       das man erst nach dem Mailklick benutzen darf, sperrt bei jedem
       Mailproblem den Neuen aus. */
    const marke = zufall(24);
    await env.KONTEN.put(
      "neustart:" + (await abdruck(marke)),
      JSON.stringify({ email, zweck: "bestaetigung" }),
      { expirationTtl: 60 * 60 * 24 * 3 },
    );
    await inDenAusgang(env, {
      an: email,
      betreff: "Willkommen bei RepoCity — bitte bestätige deine Adresse",
      text: "Klick auf diesen Link, dann weiß ich, dass die Adresse dir " +
        "gehört:\n\nhttps://speedofthespirit.dev/zugang/?bestaetigen=" +
        encodeURIComponent(marke) + "\n\nWarst du das nicht, wirf diese " +
        "Nachricht weg.",
    });

    const ausweis = await sitzungAnlegen(env, konto);
    return json({ angelegt: true, ausweis, konto: nachAussen(konto) });
  }

  /* --- Anmelden ------------------------------------------------------ */
  if (weg === "/anmelden" && post) {
    const email = saubereEmail(satz.email);
    const gesperrt = await env.KONTEN.get("sperre:" + email);
    if (gesperrt && Number(gesperrt) >= FEHLVERSUCHE) {
      return json({ fehler: "Zu viele Fehlversuche. Warte eine " +
        "Viertelstunde, dann geht es wieder." }, 429);
    }

    const konto = await kontoLesen(env, email);
    /* Auch wenn es das Konto nicht gibt, wird gerechnet — sonst verrät die
       Antwortzeit, welche Adressen hier ein Konto haben. */
    const salz = konto ? konto.salz : zufall(16);
    const versuch = await passwortAbdruck(
      String(satz.passwort || ""), salz,
      konto ? konto.runden || RUNDEN : RUNDEN,
      konto ? konto.durchgaenge || 1 : DURCHGAENGE,
    );

    if (!konto || !gleich(versuch, konto.abdruck)) {
      const zahl = Number(gesperrt || 0) + 1;
      await env.KONTEN.put("sperre:" + email, String(zahl),
        { expirationTtl: SPERRE_SEK });
      return json({ fehler: "E-Mail-Adresse oder Passwort stimmt nicht." }, 401);
    }

    await env.KONTEN.delete("sperre:" + email);
    const ausweis = await sitzungAnlegen(env, konto);
    return json({ ausweis, konto: nachAussen(konto) });
  }

  /* --- Wer bin ich --------------------------------------------------- */
  if (weg === "/stand" && !post) {
    const konto = await kontoZuAusweis(env, request);
    if (!konto) return json({ angemeldet: false }, 401);
    return json({ angemeldet: true, konto: nachAussen(konto),
                  sitzung_seit: konto.sitzungSeit || null });
  }

  /* --- Abmelden ------------------------------------------------------ */
  if (weg === "/abmelden" && post) {
    const ausweis = ausweisAus(request);
    if (ausweis) {
      await env.KONTEN.delete("sitzung:" + (await abdruck(ausweis)));
    }
    return json({ abgemeldet: true });
  }

  /* --- Einrichtung abgehakt ------------------------------------------ */
  if (weg === "/eingerichtet" && post) {
    const konto = await kontoZuAusweis(env, request);
    if (!konto) return json({ fehler: "nicht angemeldet" }, 401);
    konto.eingerichtet = true;
    await kontoSchreiben(env, konto);
    return json({ konto: nachAussen(konto) });
  }

  /* --- Passwort vergessen -------------------------------------------- */
  if (weg === "/vergessen" && post) {
    const email = saubereEmail(satz.email);
    const konto = await kontoLesen(env, email);
    /* Die Antwort ist immer dieselbe. Sonst wäre dieser Weg eine Auskunft
       darüber, welche Adressen hier ein Konto haben. */
    if (konto) {
      const marke = zufall(24);
      await env.KONTEN.put(
        "neustart:" + (await abdruck(marke)),
        JSON.stringify({ email, zweck: "neustart" }),
        { expirationTtl: NEUSTART_SEK },
      );
      await inDenAusgang(env, {
        an: email,
        betreff: "Neues Passwort für RepoCity",
        text: "Über diesen Link setzt du ein neues Passwort. Er gilt eine " +
          "halbe Stunde:\n\nhttps://speedofthespirit.dev/zugang/?neu=" +
          encodeURIComponent(marke) + "\n\nWarst du das nicht, ist nichts " +
          "passiert — dein altes Passwort gilt weiter.",
      });
    }
    return json({
      losgeschickt: true,
      hinweis: "Wenn es zu dieser Adresse ein Konto gibt, ist eine Mail " +
        "unterwegs. Sie geht über den Rechner hinaus, auf dem dein " +
        "Universe läuft — steht der still, kommt sie erst, wenn er wieder da ist.",
    });
  }

  /* --- Neues Passwort setzen ----------------------------------------- */
  if (weg === "/neues-passwort" && post) {
    const marke = String(satz.marke || "");
    const schluessel = "neustart:" + (await abdruck(marke));
    const eintrag = await env.KONTEN.get(schluessel);
    if (!eintrag) {
      return json({ fehler: "Dieser Link gilt nicht mehr. Fordere einen " +
        "neuen an." }, 400);
    }
    const mangel = passwortMangel(satz.passwort);
    if (mangel) return json({ fehler: mangel }, 400);

    const { email } = JSON.parse(eintrag);
    const konto = await kontoLesen(env, email);
    if (!konto) return json({ fehler: "Das Konto gibt es nicht mehr." }, 400);

    konto.salz = zufall(16);
    konto.runden = RUNDEN;
    konto.durchgaenge = DURCHGAENGE;
    konto.abdruck = await passwortAbdruck(satz.passwort, konto.salz);
    konto.bestaetigt = true; /* Wer die Mail lesen konnte, besitzt die Adresse. */
    /* Ab hier gilt keine ältere Anmeldung mehr — geprüft in kontoZuAusweis.
       Die gleich darunter ausgestellte neue Sitzung überlebt: verglichen
       wird echt kleiner, und ihr Zeitpunkt liegt danach. */
    konto.sitzungenAbGueltig = new Date().toISOString();
    await kontoSchreiben(env, konto);
    await env.KONTEN.delete(schluessel);

    return json({ gesetzt: true, ausweis: await sitzungAnlegen(env, konto) });
  }

  /* --- Adresse bestätigen -------------------------------------------- */
  if (weg === "/bestaetigen" && post) {
    const schluessel = "neustart:" + (await abdruck(String(satz.marke || "")));
    const eintrag = await env.KONTEN.get(schluessel);
    if (!eintrag) return json({ fehler: "Dieser Link gilt nicht mehr." }, 400);
    const { email } = JSON.parse(eintrag);
    const konto = await kontoLesen(env, email);
    if (!konto) return json({ fehler: "Das Konto gibt es nicht mehr." }, 400);
    konto.bestaetigt = true;
    await kontoSchreiben(env, konto);
    await env.KONTEN.delete(schluessel);
    return json({ bestaetigt: true });
  }

  /* --- Einladung erzeugen (nur Admin) -------------------------------- */
  if (weg === "/einladung" && post) {
    const konto = await kontoZuAusweis(env, request);
    if (!konto || konto.rolle !== "admin") {
      return json({ fehler: "Einladungen erzeugt nur der Admin." }, 403);
    }
    /* Lesbar am Telefon: keine 0/O, keine 1/I/L. */
    const zeichen = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
    const bytes = crypto.getRandomValues(new Uint8Array(10));
    let code = "";
    for (let i = 0; i < 10; i++) {
      code += zeichen[bytes[i] % zeichen.length];
      if (i === 4) code += "-";
    }
    const daten = {
      code,
      rolle: satz.rolle === "beta" ? "beta" : "nutzer",
      offen: Math.max(1, Math.min(500, Number(satz.anzahl || 1))),
      gueltigBis: satz.gueltigBis || null,
      erzeugt: new Date().toISOString(),
      von: konto.email,
      eingeloest: [],
    };
    await env.KONTEN.put("code:" + code, JSON.stringify(daten));
    return json({ einladung: daten });
  }

  /* --- Was der Nutzer eingestellt hat ----------------------------------
     Hier steht, was RepoCity in seinem Namen von sich aus tun darf: auf
     Post antworten, Bewerbungen abschicken, auf Wohnungsanzeigen
     antworten, Termine bestätigen. Es steht am Hub und nicht nur in der
     App, weil der Rechner es wissen muss — er ist derjenige, der es tut.

     Dazu je Bereich eine Obergrenze am Tag. Sie hat keinen Vorgabewert:
     wer das Selbstabschicken einschaltet, sagt auch, wie viel. Eine
     geratene Zahl wäre entweder zu klein und ärgerlich oder zu groß und
     teuer. Ohne Zahl bleibt es beim Vorlegen. */
  if (weg === "/einstellungen" && !post) {
    const gezeigt = (request.headers.get("authorization") || "")
      .replace(/^bearer /i, "").trim();
    const alsRechner = env.HUB_SCHLUESSEL && gleich(gezeigt, env.HUB_SCHLUESSEL);
    const wessen = alsRechner
      ? saubereEmail(url.searchParams.get("nutzer"))
      : (await kontoZuAusweis(env, request) || {}).email;
    if (!wessen) return json({ fehler: "nicht angemeldet" }, 401);
    const konto = await kontoLesen(env, wessen);
    if (!konto) return json({ fehler: "unbekanntes Konto" }, 404);
    return json({ einstellungen: konto.einstellungen || {} });
  }

  if (weg === "/einstellungen" && post) {
    const konto = await kontoZuAusweis(env, request);
    if (!konto) return json({ fehler: "nicht angemeldet" }, 401);

    /* Nur die Felder, die es geben darf, und nur in der Form, die sie
       haben dürfen. Was der Hub ungeprüft übernimmt, steht später als
       Wahrheit da — auch ein Tippfehler. */
    const erlaubt = ["post", "bewerbung", "wohnung", "termine"];
    const alt = konto.einstellungen || {};
    const neu = {};

    /* Nur was mitkommt, wird geändert. Wer das Selbstabschicken gar nicht
       schickt — etwa die Schalterkarte der Tiefenrecherche —, soll es auch
       nicht auf aus setzen. Sonst löscht ein Formular die Einstellungen
       eines anderen, ohne dass jemand es sieht. */
    if (satz.selbstAbschicken || satz.hoechstensAmTag) {
      neu.selbstAbschicken = {};
      neu.hoechstensAmTag = {};
      for (const feld of erlaubt) {
        const an = !!(satz.selbstAbschicken || {})[feld];
        const zahl = Math.max(0, Math.min(500,
          Number((satz.hoechstensAmTag || {})[feld] || 0)));
        /* Einschalten ohne Obergrenze geht nicht. Sonst stünde da "darf
           selbst abschicken, so viel er will" — und niemand hätte das
           entschieden. */
        neu.selbstAbschicken[feld] = an && zahl > 0;
        neu.hoechstensAmTag[feld] = zahl;
      }
    }
    /* Die Tiefenrecherche — zwei Schalter, beide ab Werk aus. Eine Suche
       kostet Geld, also wird sie eingeschaltet und nicht ausgeschaltet.

         an               läuft der Tiefenrechercheur überhaupt
         ueberKontingent  darf er weitersuchen, wenn die 750 freien Suchen
                          des Monats verbraucht sind — erst dann wird
                          überhaupt etwas abgerechnet

       Wer den Satz nicht mitschickt, ändert nichts: der alte Stand bleibt
       stehen, statt von einem fremden Formular auf aus gesetzt zu werden. */
    if (satz.tiefenrecherche && typeof satz.tiefenrecherche === "object") {
      neu.tiefenrecherche = {
        an: !!satz.tiefenrecherche.an,
        ueberKontingent: !!satz.tiefenrecherche.ueberKontingent,
      };
    }
    neu.geaendert = new Date().toISOString();
    konto.einstellungen = { ...alt, ...neu };
    await kontoSchreiben(env, konto);
    return json({ einstellungen: konto.einstellungen });
  }

  /* --- Für wen arbeitet der Rechner? ----------------------------------
     Die Dauerläufer auf dem Rechner - Post, Wohnung, Termine - müssen
     wissen, für wen sie laufen. Sie fragen hier nach und holen sich zu
     jedem Namen die Zugänge aus dem Tresor.

     Nur der Rechner darf das: eine Liste aller Konten in der Hand eines
     Nutzers wäre eine Adressliste. Und herausgegeben wird auch ihm nur,
     was er zum Arbeiten braucht - Kennung, Rolle, Stufe. Kein Salz, kein
     Abdruck, kein Datum. */
  if (weg === "/liste" && !post) {
    const gezeigt = (request.headers.get("authorization") || "")
      .replace(/^bearer /i, "").trim();
    if (!env.HUB_SCHLUESSEL || !gleich(gezeigt, env.HUB_SCHLUESSEL)) {
      return json({ fehler: "nur der Rechner" }, 403);
    }
    const gefunden = await env.KONTEN.list({ prefix: "konto:", limit: 1000 });
    const aus = [];
    for (const e of gefunden.keys) {
      const r = await env.KONTEN.get(e.name);
      if (!r) continue;
      try {
        const k = JSON.parse(r);
        aus.push({ email: k.email, rolle: k.rolle, stufe: k.stufe });
      } catch (x) { /* ein kaputtes Konto hält den Rest nicht auf */ }
    }
    return json({ konten: aus });
  }

  /* --- Einladungen ansehen (nur Admin) ------------------------------- */
  if (weg === "/einladungen" && !post) {
    const konto = await kontoZuAusweis(env, request);
    if (!konto || konto.rolle !== "admin") {
      return json({ fehler: "nur der Admin" }, 403);
    }
    const gefunden = await env.KONTEN.list({ prefix: "code:", limit: 200 });
    const aus = [];
    for (const e of gefunden.keys) {
      const r = await env.KONTEN.get(e.name);
      if (r) {
        try {
          aus.push(JSON.parse(r));
        } catch (x) { /* ein kaputter Eintrag hält den Rest nicht auf */ }
      }
    }
    return json({ einladungen: aus });
  }

  return json({ fehler: "unbekannter Weg: " + weg }, 404);
}

export const _pruefbar = {
  passwortMangel, emailPlausibel, saubereEmail, gleich, abdruck,
  passwortAbdruck, MINDESTLAENGE, FEHLVERSUCHE, RUNDEN, DURCHGAENGE,
};
