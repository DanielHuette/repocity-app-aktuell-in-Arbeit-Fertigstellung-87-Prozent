/* Muster, Dateien und Termine — was der Nutzer vorgibt und was RepoCity daraus macht.
 *
 * Warum an einer Stelle: alle drei gehören demselben Konto, werden von
 * derselben Oberfläche gefüllt und vom selben Rechner gelesen. Drei Wege
 * mit drei eigenen Ausweisprüfungen wären dreimal dieselbe Regel.
 *
 *   MUSTER   Text, den der Nutzer vorgibt: wie seine Bewerbung aussieht, wie
 *            er auf ein Wohnungsangebot antwortet, wie er formell, normal und
 *            locker schreibt. Der Agent schreibt danach, statt zu raten.
 *
 *   DATEIEN  Was dabei herauskommt und was hineingeht: das eigene
 *            Bewerbungsmuster als PDF, und die fertigen Anschreiben und
 *            Lebensläufe zum Gegenlesen. Nichts geht hinaus, bevor der
 *            Nutzer es gesehen hat.
 *
 *   TERMINE  Was der Terminkoordinator führt. Mit Art, Zeit und der Frage,
 *            wann geweckt wird.
 *
 * Wer darf was:
 *   Anmeldung        der Nutzer: seine eigenen Muster, Dateien, Termine
 *   HUB_SCHLUESSEL   der Rechner: lesen für den Nutzer, an dem er arbeitet,
 *                    und Erzeugtes zurücklegen. Er sieht kein fremdes Fach.
 *
 * Die Fächer stehen im Schlüssel, wie überall am Hub:
 *   muster:<email>:<art>     datei:<email>:<id>     termin:<email>:<id>
 */
import { kontoZuAusweis } from "./konten.js";

const MUSTER = "muster:";
const DATEI = "datei:";
const TERMIN = "termin:";

/* Welche Muster es gibt. Nicht mehr: was hier nicht steht, wird nicht
   gespeichert - sonst legt ein Tippfehler ein zweites Fach an, das niemand
   je wieder liest. */
const MUSTERARTEN = [
  "bewerbung",        // wie eine Bewerbung von ihm aussieht
  "wohnung",          // wie er auf ein Wohnungsangebot antwortet
  "email-formell",    // offizielle Korrespondenz
  "email-normal",     // die gewöhnliche Antwort
  "email-casual",     // locker
  "kalender",         // verknuepfte Kalenderadressen, eine je Zeile
];

/* Wofür eine Datei da ist. "vorlage" kommt vom Nutzer, "entwurf" vom Agenten
   und wartet auf sein Ja. */
const DATEIARTEN = ["vorlage", "entwurf"];

/* Eine Datei darf so groß sein. Gerechnet, nicht geraten: der Speicher nimmt
   25 MB je Eintrag, Base64 bläht um ein Drittel auf, und der Kopf braucht
   auch Platz - 15 MB roh bleiben sicher darunter. Ein Lebenslauf mit Bild
   liegt bei unter 2 MB. */
const HOECHSTENS_BYTE = 15 * 1024 * 1024;

/* Wie lange ein Entwurf liegen bleibt, wenn ihn niemand ansieht: 90 Tage.
   Vorlagen des Nutzers verfallen nie - er hat sie selbst hinterlegt. */
const ENTWURF_HALTBAR_SEK = 60 * 60 * 24 * 90;

function json(daten, status = 200) {
  return new Response(JSON.stringify(daten), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function gleich(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let x = 0;
  for (let i = 0; i < a.length; i++) x |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return x === 0;
}

function saubereEmail(roh) {
  return String(roh || "").trim().toLowerCase();
}

/* Für wen wird gearbeitet? Der Rechner sagt es mit ?nutzer=, ein Mensch
   beweist es mit seinem Ausweis. Ohne beides: niemand. */
async function wessenFach(request, env, url) {
  const gezeigt = (request.headers.get("authorization") || "")
    .replace(/^bearer /i, "").trim();
  if (env.HUB_SCHLUESSEL && gleich(gezeigt, env.HUB_SCHLUESSEL)) {
    const wer = saubereEmail(url.searchParams.get("nutzer"));
    return wer ? { email: wer, alsRechner: true } : null;
  }
  const konto = await kontoZuAusweis(env, request);
  return konto ? { email: saubereEmail(konto.email), alsRechner: false } : null;
}

export async function muster(request, env, url) {
  const weg = url.pathname.replace(/^\/api\/(muster|dateien|termine)/, "") || "/";
  const bereich = url.pathname.split("/")[2];
  const post = request.method === "POST";

  const wer = await wessenFach(request, env, url);
  if (!wer) return json({ fehler: "nicht angemeldet" }, 401);

  let satz = {};
  if (post) {
    try { satz = await request.json(); } catch (e) { satz = {}; }
  }

  /* ---------------------------------------------------------- Muster */

  if (bereich === "muster" && weg === "/" && !post) {
    const aus = {};
    for (const art of MUSTERARTEN) {
      const r = await env.HUB.get(MUSTER + wer.email + ":" + art);
      if (r) {
        try { aus[art] = JSON.parse(r); } catch (e) { /* ein kaputtes Fach hält den Rest nicht auf */ }
      }
    }
    return json({ muster: aus });
  }

  if (bereich === "muster" && weg === "/" && post) {
    const art = String(satz.art || "");
    if (!MUSTERARTEN.includes(art)) {
      return json({ fehler: "unbekannte Art", erlaubt: MUSTERARTEN }, 400);
    }
    const text = String(satz.text || "");
    /* 40.000 Zeichen sind rund 20 Seiten - mehr ist kein Muster mehr,
       sondern ein Buch, und das Modell liest es ohnehin nicht zu Ende. */
    if (text.length > 40000) return json({ fehler: "zu lang, höchstens 40.000 Zeichen" }, 400);

    const eintrag = {
      art,
      text,
      geaendert: new Date().toISOString(),
      von: wer.alsRechner ? "rechner" : "nutzer",
    };
    if (!text.trim()) {
      await env.HUB.delete(MUSTER + wer.email + ":" + art);
      return json({ geloescht: art });
    }
    await env.HUB.put(MUSTER + wer.email + ":" + art, JSON.stringify(eintrag));
    return json({ muster: eintrag });
  }

  /* --------------------------------------------------------- Dateien */

  if (bereich === "dateien" && weg === "/" && !post) {
    /* Nur die Köpfe, nie der Inhalt: eine Liste mit zehn Lebensläufen darin
       wäre ein paar Megabyte, und angesehen wird immer nur einer. */
    const nurArt = url.searchParams.get("art");
    const gefunden = await env.HUB.list({ prefix: DATEI + wer.email + ":", limit: 200 });
    const aus = [];
    for (const e of gefunden.keys) {
      const k = e.metadata || {};
      if (nurArt && k.art !== nurArt) continue;
      aus.push({
        id: e.name.slice((DATEI + wer.email + ":").length),
        name: k.name || "",
        art: k.art || "",
        wofuer: k.wofuer || "",
        typ: k.typ || "",
        bytes: k.bytes || 0,
        stand: k.stand || "",
        abgelegt: k.abgelegt || "",
      });
    }
    aus.sort((a, b) => (b.abgelegt || "").localeCompare(a.abgelegt || ""));
    return json({ dateien: aus });
  }

  if (bereich === "dateien" && weg.startsWith("/holen/") && !post) {
    const id = decodeURIComponent(weg.slice("/holen/".length));
    const r = await env.HUB.getWithMetadata(DATEI + wer.email + ":" + id, { type: "text" });
    if (!r || r.value === null) return json({ fehler: "nicht gefunden" }, 404);
    return json({ datei: { id, ...(r.metadata || {}), inhalt: r.value } });
  }

  if (bereich === "dateien" && weg === "/ablegen" && post) {
    const art = String(satz.art || "");
    if (!DATEIARTEN.includes(art)) {
      return json({ fehler: "unbekannte Art", erlaubt: DATEIARTEN }, 400);
    }
    const inhalt = String(satz.inhalt || "");
    if (!inhalt) return json({ fehler: "leer" }, 400);
    /* Base64 trägt drei Byte in vier Zeichen. */
    const roh = Math.floor(inhalt.length * 3 / 4);
    if (roh > HOECHSTENS_BYTE) {
      return json({ fehler: "zu groß", hoechstens_byte: HOECHSTENS_BYTE, gemessen_byte: roh }, 413);
    }
    const id = (satz.id ? String(satz.id) : (Date.now() + "-" + Math.random().toString(36).slice(2, 8)));
    const kopf = {
      name: String(satz.name || "ohne Namen").slice(0, 200),
      art,
      /* Wofür: bewerbung, wohnung, email - damit der Agent seine Vorlage findet. */
      wofuer: String(satz.wofuer || "").slice(0, 40),
      typ: String(satz.typ || "application/pdf").slice(0, 80),
      bytes: roh,
      /* Ein Entwurf wartet, bis der Nutzer ihn freigibt oder verwirft. */
      stand: art === "entwurf" ? String(satz.stand || "wartet") : "vorlage",
      abgelegt: new Date().toISOString(),
    };
    const optionen = { metadata: kopf };
    if (art === "entwurf") optionen.expirationTtl = ENTWURF_HALTBAR_SEK;
    await env.HUB.put(DATEI + wer.email + ":" + id, inhalt, optionen);
    return json({ datei: { id, ...kopf } });
  }

  if (bereich === "dateien" && weg.startsWith("/stand/") && post) {
    /* Freigeben oder verwerfen. Der Rechner darf das nicht - er hat den
       Entwurf gemacht, er beurteilt ihn nicht. */
    if (wer.alsRechner) return json({ fehler: "nur der Nutzer entscheidet" }, 403);
    const id = decodeURIComponent(weg.slice("/stand/".length));
    const stand = String(satz.stand || "");
    if (!["wartet", "freigegeben", "verworfen"].includes(stand)) {
      return json({ fehler: "unbekannter Stand" }, 400);
    }
    const schluessel = DATEI + wer.email + ":" + id;
    const r = await env.HUB.getWithMetadata(schluessel, { type: "text" });
    if (!r || r.value === null) return json({ fehler: "nicht gefunden" }, 404);
    const kopf = { ...(r.metadata || {}), stand, entschieden: new Date().toISOString() };
    await env.HUB.put(schluessel, r.value, { metadata: kopf, expirationTtl: ENTWURF_HALTBAR_SEK });
    return json({ datei: { id, ...kopf } });
  }

  if (bereich === "dateien" && weg.startsWith("/loeschen/") && post) {
    if (wer.alsRechner) return json({ fehler: "nur der Nutzer löscht" }, 403);
    const id = decodeURIComponent(weg.slice("/loeschen/".length));
    await env.HUB.delete(DATEI + wer.email + ":" + id);
    return json({ geloescht: id });
  }

  /* --------------------------------------------------------- Termine */

  if (bereich === "termine" && weg === "/" && !post) {
    const von = url.searchParams.get("von") || "";
    const bis = url.searchParams.get("bis") || "";
    const gefunden = await env.HUB.list({ prefix: TERMIN + wer.email + ":", limit: 1000 });
    const aus = [];
    for (const e of gefunden.keys) {
      const r = await env.HUB.get(e.name);
      if (!r) continue;
      try {
        const t = JSON.parse(r);
        if (von && t.beginn < von) continue;
        if (bis && t.beginn > bis) continue;
        aus.push(t);
      } catch (x) { /* ein kaputter Termin hält den Kalender nicht auf */ }
    }
    aus.sort((a, b) => String(a.beginn).localeCompare(String(b.beginn)));
    return json({ termine: aus });
  }

  if (bereich === "termine" && weg === "/" && post) {
    const beginn = String(satz.beginn || "");
    /* Ohne Zeitpunkt ist es kein Termin. Geprüft wird die Form, nicht der
       Geschmack: 2026-09-20T14:30 */
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(beginn)) {
      return json({ fehler: "beginn fehlt oder hat die falsche Form (2026-09-20T14:30)" }, 400);
    }
    const id = satz.id ? String(satz.id) : (Date.now() + "-" + Math.random().toString(36).slice(2, 8));
    const termin = {
      id,
      beginn,
      ende: String(satz.ende || ""),
      titel: String(satz.titel || "").slice(0, 200),
      art: String(satz.art || "sonstiges").slice(0, 40),
      beschreibung: String(satz.beschreibung || "").slice(0, 4000),
      ort: String(satz.ort || "").slice(0, 200),
      /* Wie viele Minuten vorher geweckt wird. 0 heißt: gar nicht. */
      weckenMin: Math.max(0, Math.min(10080, Number(satz.weckenMin || 0))),
      /* Woher er kommt: von Hand, oder aus einem verknüpften Kalender. */
      quelle: String(satz.quelle || "hand").slice(0, 40),
      geaendert: new Date().toISOString(),
    };
    await env.HUB.put(TERMIN + wer.email + ":" + id, JSON.stringify(termin));
    return json({ termin });
  }

  if (bereich === "termine" && weg.startsWith("/loeschen/") && post) {
    const id = decodeURIComponent(weg.slice("/loeschen/".length));
    await env.HUB.delete(TERMIN + wer.email + ":" + id);
    return json({ geloescht: id });
  }

  return json({ fehler: "unbekannter Weg" }, 404);
}
