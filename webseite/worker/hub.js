/* Der Hub des Universe — die Poststelle zwischen App, Webseite und Rechner.
 *
 * Warum es ihn braucht: Die Agenten laufen auf einem Rechner, die App
 * liegt auf einem Handy. Beide können einander nicht direkt erreichen —
 * der Rechner hat keine feste Adresse im Netz, und das Handy ist nicht
 * immer da. Also gibt es eine Stelle dazwischen, die beide erreichen: hier.
 *
 * Der Hub arbeitet nicht. Er nimmt entgegen und gibt heraus:
 *
 *   App  ─── Auftrag ──►  HUB  ◄── holt ab ─── Sekretär (Rechner)
 *   App  ◄── Meldung ───  HUB  ◄── meldet ──── Agenten (Rechner)
 *
 * Der Rechner FRAGT NACH, er wird nicht angerufen. Das ist Absicht: so
 * braucht der Rechner keine offene Tür ins Internet, und es funktioniert
 * hinter jedem Router.
 *
 * JEDER EINTRAG GEHÖRT EINEM NUTZER. Sein Fach steht im Schlüssel:
 *
 *   auftrag:<kennung>:<lauf>      meldung:<kennung>:<lauf>
 *
 * Ein angemeldeter Nutzer sieht nur sein eigenes Fach — nicht, weil die
 * Oberfläche das andere nicht anzeigt, sondern weil der Hub es nicht
 * herausgibt. Der Rechner sieht alle Fächer; er arbeitet für alle.
 *
 * Wer darf was:
 *
 *   HUB_SCHLUESSEL     der Rechner: Aufträge abholen, Zustände melden,
 *                      Meldungen einliefern, Post abholen
 *   Anmeldung          ein Nutzer: eigene Aufträge aufgeben, eigene
 *                      Meldungen lesen, entscheiden (konten.js)
 *   APP_SCHLUESSEL     die App VOR der Anmeldung — nur noch dafür da,
 *                      dass ein altes Paket nicht plötzlich stumm ist.
 *                      Ohne Kennung landet sie im Fach "gast".
 *   Cloudflare Access  Daniel im Browser, ohne Schlüssel
 *
 * Fehlt jeder Schlüssel in den Einstellungen des Workers, ist die
 * betreffende Seite ZU. Nicht offen: ein Hub ohne Schlüssel, der jeden
 * hereinlässt, wäre schlimmer als einer, der nicht läuft.
 */

import { kontoZuAusweis } from "./konten.js";

const AUFTRAG = "auftrag:";
const MELDUNG = "meldung:";
const POST = "postausgang:";
/* Der Puls des Rechners: die Leitung meldet alle zehn Minuten, seit wann sie
   laeuft. Ein Schluessel, der ueberschrieben wird - 144 Schreibvorgaenge am Tag,
   keine Meldung, die jemand lesen muesste. Verfaellt nach einer Stunde:
   dann gilt der Rechner als weg. */
const PULS = "puls:rechner";

/* Wohin ein Weckruf geht. Das Handy meldet seine Adresse bei jedem Start -
   sie aendert sich von selbst, bei Neuinstallation und nach geloeschten
   Daten. Sie verfaellt nach 90 Tagen: ein Geraet, das ein Vierteljahr nichts
   von sich hoeren laesst, ist keins mehr, und ein Ruf dorthin geht ins Leere. */
const GERAET = "geraet:";
const GERAET_HALTBAR_SEK = 60 * 60 * 24 * 90;

/* Wie lange ein Eintrag liegen bleibt. Danach räumt Cloudflare ihn weg -
   der Hub ist eine Poststelle, kein Archiv. Das Archiv ist der Vault. */
const HALTBAR_SEK = 60 * 60 * 24 * 30;

/* Mehr als das gibt der Hub nie auf einmal heraus. */
const HOECHSTENS = 200;

function json(daten, status = 200) {
  return new Response(JSON.stringify(daten), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

/* --------------------------------------------------------------- Zugang */

function ausweis(request) {
  const kopf = request.headers.get("authorization") || "";
  return kopf.toLowerCase().startsWith("bearer ") ? kopf.slice(7).trim() : "";
}

/* Zeitgleicher Vergleich: ein Vergleich, der bei der ersten falschen
   Stelle abbricht, verrät über die Dauer, wie viel schon stimmte. */
function gleich(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  if (a.length !== b.length) return false;
  let rest = 0;
  for (let i = 0; i < a.length; i++) rest |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return rest === 0;
}

/**
 * Wer klopft. Gibt { rolle, kennung } zurück — oder null.
 *
 *   rolle "rechner"  arbeitet für alle, kennung ist das Fach, das er
 *                    gerade bedient (aus ?nutzer=), sonst leer
 *   rolle "nutzer"   ein angemeldetes Konto, kennung ist seine Adresse
 *
 * Die Reihenfolge ist Absicht: erst der Rechnerschlüssel, dann die
 * Anmeldung, zuletzt der alte App-Schlüssel. Wer sich anmeldet, bekommt
 * sein Fach — nicht das Sammelfach.
 */
export async function wer(request, env, istAdmin, kennungAusWeg) {
  const gezeigt = ausweis(request);

  if (env.HUB_SCHLUESSEL && gleich(gezeigt, env.HUB_SCHLUESSEL)) {
    return { rolle: "rechner", kennung: kennungAusWeg || "" };
  }

  const konto = await kontoZuAusweis(env, request);
  if (konto) return { rolle: "nutzer", kennung: konto.email, konto };

  if (env.APP_SCHLUESSEL && gleich(gezeigt, env.APP_SCHLUESSEL)) {
    /* Ein Paket ohne Anmeldung. Es bekommt ein eigenes Fach und sieht
       darum nichts von irgendjemandem. */
    return { rolle: "nutzer", kennung: "gast" };
  }

  if (istAdmin) return { rolle: "nutzer", kennung: adminKennung(env) };

  return null;
}

/* Ein kurzer, gleichbleibender Name fuer eine Geraetemarke. Damit
   ueberschreibt dasselbe Handy beim naechsten Start seinen eigenen Eintrag,
   statt einen zweiten anzulegen - sonst haette ein Geraet nach einem Jahr
   dreihundert Faecher und der Hub riefe dreihundertmal. */
async function markenkennung(marke) {
  const roh = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(marke));
  return [...new Uint8Array(roh)].slice(0, 8)
    .map((b) => b.toString(16).padStart(2, "0")).join("");
}

function adminKennung(env) {
  return String(env.ADMIN_LISTE || "dhuette@gmx.net").split(",")[0].trim().toLowerCase();
}

/* --------------------------------------------------------------- Ablage */

function kennungFuer(vorsatz, fach) {
  return vorsatz + fach + ":" + Date.now().toString(36) + "-" +
    Math.random().toString(36).slice(2, 8);
}

async function ablegen(env, schluessel, wert) {
  await env.HUB.put(schluessel, JSON.stringify(wert),
    { expirationTtl: HALTBAR_SEK });
  return wert;
}

/** Die Einträge eines Fachs. Ohne Fach (Rechner) die aller Fächer. */
async function liste(env, vorsatz, fach, anzahl) {
  const prefix = fach ? vorsatz + fach + ":" : vorsatz;
  const gefunden = await env.HUB.list({ prefix, limit: HOECHSTENS });
  const aus = [];
  for (const eintrag of gefunden.keys) {
    const roh = await env.HUB.get(eintrag.name);
    if (roh) {
      try {
        aus.push(JSON.parse(roh));
      } catch (e) {
        /* Ein kaputter Eintrag hält den Rest nicht auf. */
      }
    }
  }
  /* Neueste zuerst - die Kennung trägt die Zeit im Namen. */
  aus.sort((a, b) => String(b.id || "").localeCompare(String(a.id || "")));
  return anzahl ? aus.slice(0, anzahl) : aus;
}

/** Gehört dieser Eintrag dem, der ihn anfasst? Der Rechner darf an alle,
 *  ein Nutzer nur an seine. Ohne diese Prüfung könnte jeder mit einer
 *  fremden Kennung in der Hand entscheiden, was ihm nicht gehört. */
function darfAn(id, w) {
  if (w.rolle === "rechner") return true;
  return String(id).startsWith("auftrag:" + w.kennung + ":") ||
    String(id).startsWith("meldung:" + w.kennung + ":");
}

/* ---------------------------------------------------------------- Wege */

export async function hub(request, env, url, istAdmin) {
  if (!env.HUB) {
    return json({ fehler: "Der Hub hat keinen Speicher. In wrangler.jsonc " +
      "fehlt die Bindung HUB." }, 503);
  }
  if (!env.HUB_SCHLUESSEL && !env.APP_SCHLUESSEL && !env.KONTEN) {
    return json({ fehler: "Der Hub hat keine Schlüssel und lässt darum " +
      "niemanden herein. Siehe universe/HUB-EINRICHTEN.md." }, 503);
  }

  const w = await wer(request, env, istAdmin, url.searchParams.get("nutzer"));
  if (!w) return json({ fehler: "kein gültiger Ausweis" }, 401);

  const weg = url.pathname.replace("/api/hub", "") || "/";
  const post = request.method === "POST";

  /* --- Der Rechner liefert eine Meldung ein ---------------------------- */
  if (weg === "/push" && post) {
    if (w.rolle !== "rechner") return json({ fehler: "nur der Rechner" }, 403);
    let satz;
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
    /* An wen geht die Meldung? Der Rechner sagt es; sagt er nichts, geht
       sie an den Admin — nicht an alle. Eine Meldung ohne Empfänger in
       jedem Fach liegen zu lassen, wäre eine Datenpanne mit Ansage. */
    const fach = String(satz.nutzer || w.kennung || adminKennung(env)).toLowerCase();
    const id = kennungFuer(MELDUNG, fach);
    const meldung = {
      id,
      nutzer: fach,
      absender: String(satz.absender || "unbekannt").slice(0, 80),
      art: String(satz.art || "info").slice(0, 40),
      zusammenfassung: String(satz.zusammenfassung || "").slice(0, 300),
      text: String(satz.text || "").slice(0, 8000),
      vorgang: satz.vorgang ? String(satz.vorgang).slice(0, 80) : null,
      daten: satz.daten && typeof satz.daten === "object" ? satz.daten : {},
      zeit: new Date().toISOString(),
      gelesen: false,
      entscheidung: satz.entscheidung || null,
      grund: "",
    };
    await ablegen(env, id, meldung);
    return json({ angenommen: true, id });
  }

  /* --- Meldungen lesen -------------------------------------------------
     Ein Nutzer bekommt sein Fach. Der Rechner alle, oder das eine, das
     er in ?nutzer= genannt hat. */
  if (weg === "/meldungen" && !post) {
    const anzahl = Number(url.searchParams.get("anzahl") || 60);
    const fach = w.rolle === "rechner" ? w.kennung : w.kennung;
    return json({ meldungen: await liste(env, MELDUNG, fach, anzahl) });
  }

  /* --- Einen Auftrag aufgeben ------------------------------------------ */
  /* --- Einen Auftrag wegwerfen ------------------------------------------
     Bis zum 10.09.2026 konnte man einen Auftrag anlegen und seinen Zustand
     aendern - aber nicht loeschen. Ein Fehlversuch blieb dreissig Tage
     stehen, bis er von selbst verfiel.

     Geloescht wird der Eintrag, nicht die Anzeige: was nur versteckt ist,
     holt der Sekretaer beim naechsten Mal wieder ab. Und es loescht nur,
     wem er gehoert - darfAn() entscheidet das, nicht die Oberflaeche. */
  if (weg.startsWith("/auftrag/") && request.method === "DELETE") {
    const id = decodeURIComponent(weg.slice("/auftrag/".length));
    if (!id.startsWith(AUFTRAG)) {
      return json({ fehler: "das ist keine Auftragskennung" }, 400);
    }
    if (!darfAn(id, w)) return json({ fehler: "nicht deiner" }, 403);
    if (!(await env.HUB.get(id))) {
      return json({ fehler: "den gibt es nicht (mehr)" }, 404);
    }
    await env.HUB.delete(id);
    return json({ geloescht: id });
  }

  if (weg === "/auftrag" && post) {
    if (w.rolle !== "nutzer") return json({ fehler: "nur ein Nutzer" }, 403);
    let satz;
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
    if (!String(satz.art || "").trim()) {
      return json({ fehler: "ohne Auftragsart weiß der Sekretär nicht, " +
        "wen er anlaufen lassen soll" }, 400);
    }
    const id = kennungFuer(AUFTRAG, w.kennung);
    const auftrag = {
      id,
      nutzer: w.kennung,
      art: String(satz.art).slice(0, 60),
      text: String(satz.text || "").slice(0, 4000),
      modul: satz.modul ? String(satz.modul).slice(0, 60) : null,
      laengeSek: Number(satz.laengeSek || 0),
      trocken: satz.trocken !== false,
      zustand: "gesendet",
      angelegt: new Date().toISOString(),
      geaendert: new Date().toISOString(),
      rueckmeldung: "an den Hub übergeben, wartet auf den Sekretär",
      fortschritt: -1,
    };
    await ablegen(env, id, auftrag);
    return json({ angenommen: true, auftrag });
  }

  /* --- Aufträge ansehen / abholen -------------------------------------- */
  if (weg === "/auftraege" && !post) {
    const alle = await liste(env, AUFTRAG, w.kennung, HOECHSTENS);
    const nur = url.searchParams.get("zustand");
    return json({ auftraege: nur ? alle.filter((a) => a.zustand === nur) : alle });
  }

  /* --- Der Rechner meldet einen Zustandswechsel ------------------------ */
  if (weg.startsWith("/auftrag/") && post) {
    if (w.rolle !== "rechner") return json({ fehler: "nur der Rechner" }, 403);
    const id = weg.slice("/auftrag/".length);
    const roh = await env.HUB.get(id);
    if (!roh) return json({ fehler: "unbekannter Auftrag" }, 404);
    let satz;
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
    const auftrag = JSON.parse(roh);
    if (satz.zustand) auftrag.zustand = String(satz.zustand).slice(0, 40);
    if (satz.rueckmeldung !== undefined) {
      auftrag.rueckmeldung = String(satz.rueckmeldung).slice(0, 1000);
    }
    if (satz.fortschritt !== undefined) auftrag.fortschritt = Number(satz.fortschritt);
    if (satz.warenausgang) auftrag.warenausgang = String(satz.warenausgang).slice(0, 40);
    auftrag.geaendert = new Date().toISOString();
    await ablegen(env, id, auftrag);
    return json({ angenommen: true, auftrag });
  }

  /* --- Der Nutzer entscheidet ------------------------------------------ */
  if (weg === "/entscheidung" && post) {
    if (w.rolle !== "nutzer") return json({ fehler: "nur ein Nutzer" }, 403);
    let satz;
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
    const id = String(satz.meldung || "");
    if (!darfAn(id, w)) return json({ fehler: "nicht dein Fach" }, 403);
    const roh = await env.HUB.get(id);
    if (!roh) return json({ fehler: "unbekannte Meldung" }, 404);
    const meldung = JSON.parse(roh);
    const wahl = satz.wahl === "ja" ? "ja" : "nein";
    const grund = String(satz.grund || "").slice(0, 1000);
    /* Ein Nein ohne Satz geht nicht durch - dieselbe Regel wie überall
       sonst im Universe. Ohne Grund lernt niemand etwas. */
    if (wahl === "nein" && !grund.trim()) {
      return json({ fehler: "Ein Nein braucht einen Satz — woran lag es?" }, 400);
    }
    meldung.entscheidung = wahl;
    meldung.grund = grund;
    meldung.gelesen = true;
    await ablegen(env, id, meldung);
    return json({ angenommen: true, meldung });
  }

  /* --- Post, die hinausgehen soll --------------------------------------
     Der Hub hat kein Postfach. Konten-Mails (Bestätigung, neues Passwort)
     legt er hier ab; der E-Mail-Manager auf dem Rechner holt sie und
     verschickt sie über das Postfach, das er ohnehin bedient. */
  if (weg === "/postausgang" && !post) {
    if (w.rolle !== "rechner") return json({ fehler: "nur der Rechner" }, 403);
    const gefunden = await env.HUB.list({ prefix: POST, limit: 50 });
    const aus = [];
    for (const e of gefunden.keys) {
      const r = await env.HUB.get(e.name);
      if (!r) continue;
      try {
        const brief = JSON.parse(r);
        if (!brief.abgeholt) aus.push(brief);
      } catch (x) { /* ein kaputter Brief hält den Rest nicht auf */ }
    }
    return json({ briefe: aus });
  }

  if (weg.startsWith("/postausgang/") && post) {
    if (w.rolle !== "rechner") return json({ fehler: "nur der Rechner" }, 403);
    const id = weg.slice("/postausgang/".length);
    const r = await env.HUB.get(id);
    if (!r) return json({ fehler: "unbekannter Brief" }, 404);
    const brief = JSON.parse(r);
    brief.abgeholt = true;
    brief.verschickt = new Date().toISOString();
    /* Zwei Tage bleibt der Beleg liegen, dann räumt Cloudflare ihn weg.
       Länger wäre ein Archiv von Adressen, und das gehört nicht in eine
       Poststelle. */
    await env.HUB.put(id, JSON.stringify(brief), { expirationTtl: 60 * 60 * 48 });
    return json({ abgehakt: true });
  }

  /* --- Wohin geweckt wird ---------------------------------------------- */
  /* Das Handy meldet die Adresse, unter der Firebase es erreicht. Es meldet
     sie in sein eigenes Fach - der Rechner darf lesen, aber nichts eintragen:
     wer ein fremdes Geraet eintragen koennte, koennte fremde Handys wecken. */
  if (weg === "/geraet" && post) {
    if (w.rolle === "rechner") return json({ fehler: "nur das Geraet selbst" }, 403);
    let satz;
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
    const marke = String(satz.marke || "").trim();
    /* Eine Firebase-Marke ist gut 150 Zeichen lang. Kuerzer als 20 ist keine,
       laenger als 4096 passt in keinen Schluessel und in keine Anfrage. */
    if (marke.length < 20 || marke.length > 4096) {
      return json({ fehler: "keine brauchbare Geraetemarke" }, 400);
    }
    const fach = String(w.kennung || adminKennung(env)).toLowerCase();
    const eintrag = {
      marke,
      nutzer: fach,
      name: String(satz.name || "Handy").slice(0, 60),
      art: String(satz.art || "android").slice(0, 20),
      zuletzt: new Date().toISOString(),
    };
    await env.HUB.put(GERAET + fach + ":" + (await markenkennung(marke)),
      JSON.stringify(eintrag), { expirationTtl: GERAET_HALTBAR_SEK });
    return json({ angenommen: true });
  }

  /* Wohin darf ich rufen? Der Rechner fragt fuer den Nutzer, an dem er
     arbeitet (?nutzer=); ein Mensch sieht seine eigenen Geraete. */
  if (weg === "/geraete" && !post) {
    const fach = String(w.kennung || "").toLowerCase();
    if (!fach) return json({ fehler: "kein Fach genannt (?nutzer=)" }, 400);
    const gefunden = await env.HUB.list({ prefix: GERAET + fach + ":", limit: 50 });
    const aus = [];
    for (const e of gefunden.keys) {
      const r = await env.HUB.get(e.name);
      if (!r) continue;
      try {
        aus.push(JSON.parse(r));
      } catch (x) { /* ein kaputtes Fach haelt die anderen nicht auf */ }
    }
    return json({ geraete: aus });
  }

  /* --- Lebenszeichen ---------------------------------------------------- */
  /* --- Der Puls des Rechners ------------------------------------------ */
  if (weg === "/puls" && post) {
    if (w.rolle !== "rechner") return json({ fehler: "nur der Rechner" }, 403);
    let satz;
    try {
      satz = await request.json();
    } catch (e) {
      return json({ fehler: "kein lesbarer Inhalt" }, 400);
    }
    const puls = {
      seit: String(satz.seit || "").slice(0, 40),
      takte: Number(satz.takte) || 0,
      takt_sekunden: Number(satz.takt_sekunden) || 0,
      zuletzt: new Date().toISOString(),
    };
    /* Die Kostenzusammenfassung des Monats faehrt mit dem Puls (kern/leitung.py).
       Nur Zahlen und kurze Namen, gedeckelt - der Puls ist kein Buch. */
    if (satz.kosten && typeof satz.kosten === "object") {
      const roh = JSON.stringify(satz.kosten);
      if (roh.length <= 16000) puls.kosten = satz.kosten;
    }
    await env.HUB.put(PULS, JSON.stringify(puls), { expirationTtl: 60 * 60 });
    return json({ angenommen: true });
  }

  if (weg === "/stand" && !post) {
    const meldungen = await liste(env, MELDUNG, w.kennung, HOECHSTENS);
    const auftraege = await liste(env, AUFTRAG, w.kennung, HOECHSTENS);
    let rechner = null;
    try {
      const roh = await env.HUB.get(PULS);
      if (roh) rechner = JSON.parse(roh);
    } catch (e) {
      rechner = null;
    }
    return json({
      hub: "läuft",
      rolle: w.rolle,
      kennung: w.kennung,
      meldungen: meldungen.length,
      auftraege: auftraege.length,
      offen: auftraege.filter((a) => a.zustand === "gesendet").length,
      rechner,
      webseite_seit: env.BAUZEIT || null,
      zeit: new Date().toISOString(),
    });
  }

  return json({ fehler: "unbekannter Weg: " + weg }, 404);
}

export const _pruefbar = { darfAn, kennungFuer, gleich };
