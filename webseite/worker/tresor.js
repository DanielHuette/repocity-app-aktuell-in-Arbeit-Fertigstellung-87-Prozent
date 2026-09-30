/* Der Tresor — der vierte Teil des Hubs.
 *
 * Hier liegen die Zugangsdaten, die ein Nutzer bei der Einrichtung angibt:
 * sein Postfach, seine Portale, seine Schlüssel. Sie liegen NICHT bei den
 * Konten und NICHT in der Poststelle, sondern in einem eigenen Speicher
 * hinter einer eigenen Tür. Wer eine der drei Türen aufbekommt, hat damit
 * die anderen beiden noch nicht.
 *
 *   KONTEN   wer ist das            (konten.js)
 *   HUB      Aufträge und Meldungen (hub.js)
 *   TRESOR   seine Zugangsdaten     (hier)
 *
 * Verschlüsselt wird mit AES-GCM. Der Schlüssel dafür steht nicht im
 * Quelltext und nicht im Speicher, sondern in den Einstellungen des
 * Workers (TRESOR_SCHLUESSEL) — und aus ihm wird je Nutzer ein eigener
 * abgeleitet. Damit ist ein Nutzer nicht mit dem Schlüssel eines anderen
 * zu öffnen, und ein gestohlener Speicherauszug allein nützt nichts.
 *
 * Fehlt TRESOR_SCHLUESSEL, ist der Tresor ZU — er nimmt dann nichts an
 * und gibt nichts heraus. Ein Tresor, der unverschlüsselt weiterarbeitet,
 * weil ein Wert fehlt, ist schlimmer als einer, der nicht läuft.
 *
 * Wer hereindarf:
 *
 *   der Nutzer selbst   mit seinem Ausweis aus der Anmeldung
 *   der Rechner         mit HUB_SCHLUESSEL, und nur für den Nutzer,
 *                       dessen Auftrag er gerade abarbeitet
 *
 * Zwei Dinge kommen NIE hier hinein: die Zugänge zu den Handelsplätzen
 * (die bleiben im Schlüsselspeicher des Handys — dienste.json führt sie
 * mit "nur_geraet") und Zahlungsdaten (die sieht nur der Bezahlanbieter).
 */

const roh = new TextEncoder();
const text = new TextDecoder();

function json(daten, status = 200) {
  return new Response(JSON.stringify(daten), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function b64(puffer) {
  const bytes = new Uint8Array(puffer);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
}

function ausB64(s) {
  return Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
}

/** Der Schlüssel dieses Nutzers — abgeleitet aus dem Hausschlüssel des
 *  Workers und seiner Kennung. Zwei Nutzer bekommen nie denselben. */
async function schluesselFuer(env, kennung) {
  const stoff = await crypto.subtle.importKey(
    "raw", roh.encode(env.TRESOR_SCHLUESSEL), "HKDF", false, ["deriveKey"],
  );
  return crypto.subtle.deriveKey(
    {
      name: "HKDF",
      hash: "SHA-256",
      salt: roh.encode("repocity-tresor-v1"),
      info: roh.encode(kennung),
    },
    stoff,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}

async function zusperren(env, kennung, klartext) {
  const schluessel = await schluesselFuer(env, kennung);
  /* Zwölf Zufallsbytes je Eintrag. Derselbe Wert zweimal ergibt damit
     zwei verschiedene Geheimtexte — sonst sähe man von außen, wer
     dasselbe Passwort zweimal benutzt. */
  const wuerfel = crypto.getRandomValues(new Uint8Array(12));
  const geheim = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: wuerfel }, schluessel, roh.encode(klartext),
  );
  return { w: b64(wuerfel), g: b64(geheim) };
}

async function aufsperren(env, kennung, paket) {
  const schluessel = await schluesselFuer(env, kennung);
  const klar = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: ausB64(paket.w) }, schluessel, ausB64(paket.g),
  );
  return text.decode(klar);
}

/* --------------------------------------------------------------- Ablage */

function fach(kennung, dienst) {
  return "tresor:" + kennung + ":" + dienst;
}

/** Was von einem Eintrag nach draußen geht, ohne ihn aufzusperren:
 *  dass er da ist, wann er zuletzt angefasst wurde, und welche Felder
 *  gefüllt sind — aber nie deren Werte. Genau das braucht die
 *  Einrichtungsmaske, um Häkchen zu setzen. */
function ohneGeheimnis(eintrag) {
  return {
    dienst: eintrag.dienst,
    gesetzt: true,
    felder: eintrag.felder || [],
    geaendert: eintrag.geaendert,
    /* Der Rechner meldet hierher zurück, ob der Zugang tatsächlich
       funktioniert hat. "unbekannt", solange es niemand versucht hat —
       nicht "in Ordnung". */
    geprueft: eintrag.geprueft || "unbekannt",
    gepruefteZeit: eintrag.gepruefteZeit || null,
    fehler: eintrag.fehler || "",
  };
}

/* ---------------------------------------------------------------- Wege */

/**
 * @param wer  { kennung, istRechner } — kennung ist die E-Mail des Nutzers,
 *             dessen Fächer angesprochen werden.
 */
export async function tresor(request, env, url, wer) {
  if (!env.TRESOR) {
    return json({ fehler: "Der Tresor hat keinen Speicher. In " +
      "wrangler.jsonc fehlt die Bindung TRESOR." }, 503);
  }
  if (!env.TRESOR_SCHLUESSEL) {
    return json({ fehler: "Der Tresor hat keinen Schlüssel und bleibt " +
      "darum zu. Siehe universe/HUB-EINRICHTEN.md." }, 503);
  }
  if (!wer || !wer.kennung) return json({ fehler: "nicht angemeldet" }, 401);

  const weg = url.pathname.replace("/api/tresor", "") || "/";
  const post = request.method === "POST";

  /* --- Was ist eingerichtet? ------------------------------------------ */
  if (weg === "/stand" && !post) {
    const gefunden = await env.TRESOR.list({
      prefix: "tresor:" + wer.kennung + ":", limit: 200,
    });
    const aus = [];
    for (const e of gefunden.keys) {
      const r = await env.TRESOR.get(e.name);
      if (!r) continue;
      try {
        aus.push(ohneGeheimnis(JSON.parse(r)));
      } catch (x) { /* ein kaputtes Fach hält die anderen nicht auf */ }
    }
    return json({ eintraege: aus });
  }

  /* --- Einen Zugang ablegen ------------------------------------------- */
  if (weg === "/ablegen" && post) {
    let satz;
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
    const dienst = String(satz.dienst || "").trim().slice(0, 60);
    if (!dienst) return json({ fehler: "ohne Dienst kein Fach" }, 400);
    const werte = satz.werte && typeof satz.werte === "object" ? satz.werte : null;
    if (!werte) return json({ fehler: "keine Werte" }, 400);

    const eintrag = {
      dienst,
      felder: Object.keys(werte).slice(0, 20),
      inhalt: await zusperren(env, wer.kennung, JSON.stringify(werte)),
      geaendert: new Date().toISOString(),
      /* Frisch abgelegt heißt nicht geprüft. Erst wenn der Rechner sich
         damit wirklich angemeldet hat, steht hier etwas anderes. */
      geprueft: "unbekannt",
      gepruefteZeit: null,
      fehler: "",
    };
    await env.TRESOR.put(fach(wer.kennung, dienst), JSON.stringify(eintrag));
    return json({ abgelegt: true, eintrag: ohneGeheimnis(eintrag) });
  }

  /* --- Einen Zugang holen --------------------------------------------- */
  if (weg.startsWith("/holen/") && !post) {
    const dienst = weg.slice("/holen/".length);
    const r = await env.TRESOR.get(fach(wer.kennung, dienst));
    if (!r) return json({ fehler: "nichts abgelegt" }, 404);
    const eintrag = JSON.parse(r);
    try {
      const werte = JSON.parse(await aufsperren(env, wer.kennung, eintrag.inhalt));
      return json({ dienst, werte });
    } catch (e) {
      /* Passiert, wenn TRESOR_SCHLUESSEL gewechselt wurde. Dann ist der
         Inhalt nicht kaputt, sondern nur nicht mehr aufzusperren — und
         der Nutzer muss ihn neu eingeben. Das sagen wir auch so. */
      return json({ fehler: "Dieses Fach lässt sich nicht mehr öffnen. " +
        "Trag den Zugang bitte neu ein." }, 409);
    }
  }

  /* --- Einen Zugang wegwerfen ------------------------------------------ */
  if (weg.startsWith("/loeschen/") && post) {
    const dienst = weg.slice("/loeschen/".length);
    await env.TRESOR.delete(fach(wer.kennung, dienst));
    return json({ geloescht: true, dienst });
  }

  /* --- Der Rechner meldet, ob ein Zugang funktioniert hat -------------- */
  if (weg === "/befund" && post) {
    if (!wer.istRechner) {
      return json({ fehler: "Befunde meldet nur der Rechner" }, 403);
    }
    let satz;
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
    const dienst = String(satz.dienst || "").slice(0, 60);
    const r = await env.TRESOR.get(fach(wer.kennung, dienst));
    if (!r) return json({ fehler: "nichts abgelegt" }, 404);
    const eintrag = JSON.parse(r);
    eintrag.geprueft = satz.inOrdnung ? "in Ordnung" : "abgelehnt";
    eintrag.gepruefteZeit = new Date().toISOString();
    eintrag.fehler = String(satz.fehler || "").slice(0, 300);
    await env.TRESOR.put(fach(wer.kennung, dienst), JSON.stringify(eintrag));
    return json({ angenommen: true, eintrag: ohneGeheimnis(eintrag) });
  }

  return json({ fehler: "unbekannter Weg: " + weg }, 404);
}

export const _pruefbar = { zusperren, aufsperren, ohneGeheimnis, fach };
