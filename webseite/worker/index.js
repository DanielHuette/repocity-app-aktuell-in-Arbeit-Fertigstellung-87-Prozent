/* Der Hub der Webseite.
 *
 * Er arbeitet nicht, er vermittelt und verwahrt: er liefert die Seite aus,
 * beantwortet Fragen aus dem Fragefenster, sagt, welche Zugangsebene der
 * Besucher hat, verwahrt Konten und Zugangsdaten und oeffnet die Kasse
 * fuer das Abo.
 *
 * Drei Ebenen:
 *
 *   admin   — Daniel. Steuerung des Universe.
 *   beta    — Beta-Tester. Sieht fertige Produktionsstrassen vor der Freigabe.
 *   nutzer  — alle anderen.
 *
 * Die Ebene kommt aus ZWEI Quellen, und die Reihenfolge ist Absicht:
 *
 *   1. dem Konto (konten.js), wenn ein Ausweis mitkommt — so meldet sich
 *      die App an, und nur so bekommt sie ueberhaupt eine Ebene. Vorher
 *      war jeder App-Nutzer Free, weil Cloudflare Access seine Kennung
 *      nur im Browser mitschickt.
 *   2. Cloudflare Access, wenn kein Ausweis da ist — der Weg im Browser.
 *
 * Passwoerter nimmt dieser Worker entgegen, speichert sie aber nie im
 * Klartext (siehe konten.js). Zugangsdaten fremder Dienste liegen
 * verschluesselt im Tresor (tresor.js). Kartennummern und IBAN sieht nur
 * der Bezahlanbieter.
 */

import { kasse, haken, meinAbo, bezahlungBereit } from "./abo.js";
import { hub, wer } from "./hub.js";
import { adminListe, konten, kontoZuAusweis } from "./konten.js";
import { muster } from "./muster.js";
import { tresor } from "./tresor.js";
import { zweifaktor } from "./zweifaktor.js";
import { bereiche } from "../src/daten/bereiche.ts";
import { reichtAus, STUFE_UNTEN } from "../src/daten/abo.ts";

/* adminListe kommt aus konten.js - eine Regel an einer Stelle. */

/** Wer ist das — aus dem Konto, sonst aus Cloudflare Access. */
async function ebeneVon(request, env) {
  const konto = await kontoZuAusweis(env, request);
  if (konto) return { ebene: konto.rolle, kennung: konto.email, konto };

  const kennung = request.headers.get("cf-access-authenticated-user-email");
  if (!kennung) return { ebene: "nutzer", kennung: null };
  const email = kennung.toLowerCase();
  if (adminListe(env).includes(email)) return { ebene: "admin", kennung: email };
  const beta = (env && env.BETA_LISTE ? env.BETA_LISTE : "")
    .split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
  if (beta.includes(email)) return { ebene: "beta", kennung: email };
  return { ebene: "nutzer", kennung: email };
}

/* ------------------------------------------------------- Abo-Sperre

   Eine Sperre, die nur im Browser sichtbar ist, ist keine Sperre: wer die
   Adresse direkt eintippt, waere drin. Darum wird hier entschieden, ob die
   Seite eines Bereichs ueberhaupt herausgeht.

   Welcher Bereich welche Stufe braucht, steht in src/daten/bereiche.ts - in
   derselben Datei, aus der auch die Oberflaeche liest. Zwei Listen wuerden
   irgendwann auseinanderlaufen; dann waere die eine falsch und niemand
   wuesste welche. */

/** Der Bereich hinter einer Adresse - oder null. Erwartet /app/<weg>/ . */
function bereichVonWeg(pfad) {
  const teile = pfad.split("/").filter(Boolean);
  if (teile.length !== 2 || teile[0] !== "app") return null;
  return bereiche.find((b) => b.route === teile[1]) || null;
}

/** Welche Stufe dieser Besucher gebucht hat.
 *
 * Kommt keine Auskunft - kein Speicher, kaputter Eintrag, Fehler unterwegs -
 * gilt die UNTERSTE Stufe. Nie die hoechste: ein Fehler darf nicht
 * aufschliessen. Genau darum steht der Rueckfallwert im catch und nicht
 * irgendwo weiter oben, wo ihn eine spaetere Zeile ueberschreiben koennte. */
async function gebuchteStufe(env, kennung) {
  try {
    const abo = await meinAbo(env, kennung);
    return (abo && abo.stufe) || STUFE_UNTEN;
  } catch (e) {
    return STUFE_UNTEN;
  }
}

/** Statt der gesperrten Seite kommt die Sperrseite - unter derselben Adresse.
 *  403, nicht 302: eine Umleitung koennte ein Zwischenspeicher fuer alle
 *  ablegen, und die Seite des Bereichs selbst geht so nie hinaus. */
async function sperrseite(request, env, bereich) {
  const weg = new URL(request.url);
  weg.pathname = "/app/gesperrt/";
  weg.search = "?bereich=" + encodeURIComponent(bereich.route);
  const antwort = await env.ASSETS.fetch(new Request(weg.toString(), { method: "GET" }));
  const kopf = new Headers(antwort.headers);
  kopf.set("cache-control", "no-store");
  return new Response(antwort.body, { status: 403, headers: kopf });
}

function json(daten, status = 200) {
  return new Response(JSON.stringify(daten), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

import { frageBeantworten, buchungenAbholen } from "./mia.js";
import { eigeneAngaben } from "./angaben.js";

/* Mia bekommt die Stufe aus der geprueften Anmeldung - nie aus dem Fragetext.
 * Ohne Anmeldung ist jemand Gast. Das ist strenger als ebeneVon(), das ohne
 * Kennung "nutzer" zurueckgibt: fuer die Oberflaeche ist das richtig, fuer
 * das Fragefenster waere es eine offene Tuer. */
function stufeFuerMia(z) {
  if (!z.kennung) return { ebene: "gast", kennung: "" };
  if (z.ebene === "beta") return { ebene: "betatester", kennung: z.kennung };
  return { ebene: z.ebene, kennung: z.kennung };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    /* --------------------------------------------------------- Konten */

    if (url.pathname.startsWith("/api/konten")) {
      return konten(request, env, url);
    }

    if (url.pathname === "/api/zugang") {
      const z = await ebeneVon(request, env);
      return json({ ebene: z.ebene, kennung: z.kennung });
    }

    /* Der Rechner holt Mias Buchungen ab. Nur er - der Schluessel entscheidet. */
    if (url.pathname === "/api/hub/mia/buchungen") {
      const w = await wer(request, env, false, null);
      if (!w || w.rolle !== "rechner") return json({ fehler: "nur der Rechner" }, 403);
      return json({ buchungen: await buchungenAbholen(env) });
    }

    if (url.pathname === "/api/frage") {
      if (request.method !== "POST") return json({ fehler: "nur POST" }, 405);
      let frage = "";
      try {
        const koerper = await request.json();
        frage = String(koerper.frage || "").slice(0, 2000);
      } catch (e) {
        return json({ fehler: "keine Frage erkannt" }, 400);
      }
      if (!frage.trim()) return json({ fehler: "leere Frage" }, 400);

      const { ebene, kennung } = stufeFuerMia(await ebeneVon(request, env));
      try {
        /* Die eigenen Daten des Fragenden - nur seine, nie ein Geheimnis
           daraus, und nur wenn er angemeldet ist (siehe angaben.js).
           Uebergeben wird die Vorschrift, nicht das Ergebnis: der Wegweiser
           antwortet ohne Angaben, und was er beantwortet, muss auch nicht
           erst aus dem Speicher geholt werden. */
        return json(await frageBeantworten(env, {
          frage, ebene, kennung,
          angaben: () => eigeneAngaben(env, kennung, ebene),
        }));
      } catch (fehler) {
        return json({ antwort: "Ich komme gerade nicht an meine Angaben. Versuch es spaeter noch mal.",
                      beantwortet: false }, 200);
      }
    }

    /* ---------------------------------------------------------------- Abo */

    if (url.pathname === "/api/abo/stand") {
      const { kennung } = await ebeneVon(request, env);
      const abo = await meinAbo(env, kennung);
      return json({ ...abo, bezahlungBereit: bezahlungBereit(env) });
    }

    if (url.pathname === "/api/abo/kasse") {
      const { kennung } = await ebeneVon(request, env);
      return kasse(request, env, kennung);
    }

    if (url.pathname === "/api/abo/haken") {
      return haken(request, env);
    }

    /* -------------------------------------------------------------- Tresor
       Der Nutzer kommt an sein eigenes Fach. Der Rechner an das Fach des
       Nutzers, dessen Auftrag er gerade abarbeitet — er muss dazusagen,
       welches (?nutzer=), sonst hat er keins. */

    /* --------------------------------- Muster, Dateien und Termine
     Was der Nutzer vorgibt, was die Agenten daraus machen, und was der
     Terminkoordinator fuehrt. Alle drei haengen am Konto und werden vom
     Rechner gelesen - siehe worker/muster.js. */
  if (url.pathname.startsWith("/api/muster")
      || url.pathname.startsWith("/api/dateien")
      || url.pathname.startsWith("/api/termine")) {
    return muster(request, env, url);
  }

  if (url.pathname.startsWith("/api/tresor")) {
      const w = await wer(request, env, false, url.searchParams.get("nutzer"));
      if (!w) return json({ fehler: "nicht angemeldet" }, 401);
      return tresor(request, env, url, {
        kennung: w.kennung,
        istRechner: w.rolle === "rechner",
      });
    }

    /* ---------------------------------------------------------------- Hub */

    if (url.pathname.startsWith("/api/2fa")) {
      const z = await ebeneVon(request, env);
      return zweifaktor(request, env, url, { ebene: z.ebene, kennung: z.kennung });
    }

    if (url.pathname.startsWith("/api/hub")) {
      const { ebene } = await ebeneVon(request, env);
      return hub(request, env, url, ebene === "admin");
    }

    if (url.pathname.startsWith("/api/")) return json({ fehler: "unbekannt" }, 404);

    /* Gehoert diese Adresse zu einem Bereich, wird vor der Auslieferung
       gefragt, ob die gebuchte Stufe dafuer reicht. */
    const bereich = bereichVonWeg(url.pathname);
    if (bereich) {
      const { ebene, kennung } = await ebeneVon(request, env);
      /* Daniel kommt ueberall hin. Sonst sperrt die Sperre den aus, der sie
         wieder aufmachen koennte - derselbe Grund wie beim zweiten Faktor. */
      if (ebene !== "admin") {
        const stufe = await gebuchteStufe(env, kennung);
        if (!reichtAus(stufe, bereich.stufe)) {
          return sperrseite(request, env, bereich);
        }
      }
    }

    return env.ASSETS.fetch(request);
  },
};
