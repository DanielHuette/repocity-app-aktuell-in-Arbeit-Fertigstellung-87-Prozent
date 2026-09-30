/* Der Bezahlteil des Hubs.
 *
 * Er nimmt selbst keine Kartennummern, keine IBAN und kein Passwort entgegen.
 * Er baut beim Bezahlanbieter (Stripe) eine Kasse auf und schickt den Besucher
 * dorthin; alles Heikle passiert dort, nicht hier. Zurueck kommt nur die
 * Nachricht, dass bezahlt wurde.
 *
 * Solange kein Schluessel hinterlegt ist, sagt der Hub das ehrlich und
 * setzt den Besucher auf die Warteliste — er tut nicht so, als ginge es schon.
 *
 * Was hinterlegt werden muss (siehe ABO-EINRICHTEN.md):
 *   STRIPE_SCHLUESSEL     Geheimnis, per `wrangler secret put`
 *   STRIPE_HAKEN_GEHEIM   Geheimnis, per `wrangler secret put`
 *   PREIS_CREATIVE_MONAT  offener Wert in wrangler.jsonc
 *   PREIS_CREATIVE_JAHR
 *   PREIS_MADNESS_MONAT
 *   PREIS_MADNESS_JAHR
 */

import { adminListe } from "./konten.js";

const STUFEN = ["creative", "madness"];
const TAKTE = ["monat", "jahr"];

function json(daten, status = 200) {
  return new Response(JSON.stringify(daten), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

/** Die Preis-Kennung fuer Stufe und Takt aus den Umgebungswerten holen. */
function preisKennung(env, stufe, takt) {
  const name = "PREIS_" + stufe.toUpperCase() + "_" + takt.toUpperCase();
  const wert = env[name];
  return wert && String(wert).trim() ? String(wert).trim() : null;
}

export function bezahlungBereit(env) {
  if (!env.STRIPE_SCHLUESSEL) return false;
  return STUFEN.every((s) => TAKTE.every((t) => preisKennung(env, s, t)));
}

/* ------------------------------------------------------------ Kasse oeffnen */

export async function kasse(request, env, kennung) {
  if (request.method !== "POST") return json({ fehler: "nur POST" }, 405);

  let stufe = "", takt = "";
  try {
    const k = await request.json();
    stufe = String(k.stufe || "");
    takt = String(k.takt || "");
  } catch (e) {
    return json({ fehler: "unlesbare Anfrage" }, 400);
  }

  if (!STUFEN.includes(stufe)) return json({ fehler: "unbekannte Stufe" }, 400);
  if (!TAKTE.includes(takt)) return json({ fehler: "unbekannter Takt" }, 400);

  if (!bezahlungBereit(env)) {
    return json({
      bereit: false,
      hinweis:
        "Die Bezahlung ist noch nicht freigeschaltet. Schreib an " +
        "info@speedofthespirit.dev — dann sagen wir Bescheid, sobald es losgeht.",
    });
  }

  const preis = preisKennung(env, stufe, takt);
  const herkunft = new URL(request.url).origin;

  const feld = new URLSearchParams();
  feld.set("mode", "subscription");
  feld.set("line_items[0][price]", preis);
  feld.set("line_items[0][quantity]", "1");
  feld.set("success_url", herkunft + "/app/abo/?stand=danke&sitzung={CHECKOUT_SESSION_ID}");
  feld.set("cancel_url", herkunft + "/app/abo/?stand=abgebrochen");
  feld.set("locale", "de");
  feld.set("currency", "eur");
  feld.set("allow_promotion_codes", "true");
  feld.set("billing_address_collection", "required");
  /* Karte traegt Google Pay und Apple Pay mit; PayPal und Bankeinzug stehen
     daneben. Welche davon erscheinen, entscheidet Stripe nach Geraet und Land. */
  ["card", "paypal", "sepa_debit"].forEach((w, i) => {
    feld.set("payment_method_types[" + i + "]", w);
  });
  feld.set("metadata[stufe]", stufe);
  feld.set("metadata[takt]", takt);
  if (kennung) {
    feld.set("customer_email", kennung);
    feld.set("metadata[kennung]", kennung);
  }

  let antwort;
  try {
    antwort = await fetch("https://api.stripe.com/v1/checkout/sessions", {
      method: "POST",
      headers: {
        authorization: "Bearer " + env.STRIPE_SCHLUESSEL,
        "content-type": "application/x-www-form-urlencoded",
      },
      body: feld.toString(),
    });
  } catch (e) {
    return json({ fehler: "Der Bezahlanbieter ist nicht erreichbar." }, 502);
  }

  const daten = await antwort.json().catch(() => null);
  if (!antwort.ok || !daten || !daten.url) {
    const grund = daten && daten.error && daten.error.message ? daten.error.message : "unbekannt";
    return json({ fehler: "Die Kasse liess sich nicht oeffnen.", grund }, 502);
  }

  return json({ bereit: true, weiter: daten.url });
}

/* ------------------------------------------------- Rueckmeldung von Stripe */

function hexAus(puffer) {
  return [...new Uint8Array(puffer)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Prueft die Unterschrift, mit der Stripe seine Meldungen versieht. */
async function unterschriftStimmt(rumpf, kopf, geheim) {
  if (!kopf || !geheim) return false;
  const teile = Object.fromEntries(
    kopf.split(",").map((s) => {
      const i = s.indexOf("=");
      return [s.slice(0, i).trim(), s.slice(i + 1).trim()];
    })
  );
  if (!teile.t || !teile.v1) return false;

  /* Meldungen, die aelter als fuenf Minuten sind, werden nicht angenommen. */
  const alter = Math.abs(Math.floor(Date.now() / 1000) - Number(teile.t));
  if (!Number.isFinite(alter) || alter > 300) return false;

  const schluessel = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(geheim),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const gerechnet = hexAus(await crypto.subtle.sign(
    "HMAC", schluessel, new TextEncoder().encode(teile.t + "." + rumpf)
  ));

  /* Zeichenweiser Vergleich ohne Abkuerzung, damit die Laufzeit nichts verraet. */
  if (gerechnet.length !== teile.v1.length) return false;
  let gleich = 0;
  for (let i = 0; i < gerechnet.length; i++) gleich |= gerechnet.charCodeAt(i) ^ teile.v1.charCodeAt(i);
  return gleich === 0;
}

export async function haken(request, env) {
  if (request.method !== "POST") return json({ fehler: "nur POST" }, 405);

  const rumpf = await request.text();
  const echt = await unterschriftStimmt(
    rumpf, request.headers.get("stripe-signature"), env.STRIPE_HAKEN_GEHEIM
  );
  if (!echt) return json({ fehler: "Unterschrift stimmt nicht" }, 400);

  let meldung;
  try { meldung = JSON.parse(rumpf); } catch (e) { return json({ fehler: "unlesbar" }, 400); }

  const art = meldung.type || "";
  const gegenstand = (meldung.data && meldung.data.object) || {};

  /* Wer was gebucht hat, kommt in den Speicher. Ist keiner gebunden, wird die
     Meldung nur bestaetigt — Stripe wiederholt sie sonst endlos. */
  if (env.ABOS) {
    const kennung =
      (gegenstand.metadata && gegenstand.metadata.kennung) ||
      gegenstand.customer_email || gegenstand.customer || null;

    if (kennung && (art === "checkout.session.completed" ||
                    art === "customer.subscription.created" ||
                    art === "customer.subscription.updated")) {
      await env.ABOS.put("abo:" + kennung, JSON.stringify({
        stufe: (gegenstand.metadata && gegenstand.metadata.stufe) || null,
        takt: (gegenstand.metadata && gegenstand.metadata.takt) || null,
        stand: gegenstand.status || "aktiv",
        kunde: gegenstand.customer || null,
        stand_seit: new Date().toISOString(),
      }));
    }
    if (kennung && (art === "customer.subscription.deleted" ||
                    art === "invoice.payment_failed")) {
      await env.ABOS.put("abo:" + kennung, JSON.stringify({
        stufe: null, stand: "beendet", stand_seit: new Date().toISOString(),
      }));
    }
  }

  return json({ angenommen: true });
}

/* --------------------------------------------------- Was habe ich gebucht? */

export async function meinAbo(env, kennung) {
  if (!kennung) return { stufe: "free", angemeldet: false };
  /* Ein Admin sieht alles - App wie Webseite. Daniel, 10.09.2026: die
     Sperre macht "nur sinn wenn ich als admin eingeloggt bin und nicht
     unter free laufe". Die Rolle steht in ADMIN_LISTE, nicht im Code. */
  if (adminListe(env).includes(String(kennung).toLowerCase())) {
    return { stufe: "madness", rolle: "admin", angemeldet: true };
  }
  if (!env.ABOS) return { stufe: "free", angemeldet: true, gespeichert: false };
  const roh = await env.ABOS.get("abo:" + kennung);
  if (!roh) return { stufe: "free", angemeldet: true };
  try {
    const a = JSON.parse(roh);
    return { stufe: a.stufe || "free", stand: a.stand, angemeldet: true };
  } catch (e) {
    return { stufe: "free", angemeldet: true };
  }
}
