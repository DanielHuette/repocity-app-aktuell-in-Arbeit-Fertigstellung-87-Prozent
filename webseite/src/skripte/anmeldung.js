/* Anmelden und Konto anlegen auf der Webseite.
 *
 * Bis zum 10.09.2026 ging das nur in der App. Die Webseite kannte zwar
 * Cloudflare Access, aber der Hub verlangt einen Kontoausweis - und den
 * konnte die Seite gar nicht bekommen. Wer hier einen Auftrag abschickte,
 * bekam "Aufträge nimmt der Hub nur von angemeldeten Ausweisen an" und
 * fand nirgends eine Stelle, sich anzumelden. Das war Punkt A12.
 *
 * Der Weg, den diese Datei bedient:
 *
 *   POST /api/konten/anlegen   {email, passwort, code?}  -> {angelegt}
 *   POST /api/konten/anmelden  {email, passwort}         -> {ausweis, konto}
 *   GET  /api/konten/stand     Bearer                    -> {angemeldet, konto}
 *   POST /api/konten/abmelden  Bearer
 *
 * Anlegen gibt KEINEN Ausweis zurueck. Darum meldet diese Datei nach dem
 * Anlegen gleich an - sonst stuende der Nutzer vor derselben Wand wie
 * vorher, nur eine Maske weiter.
 */

import { ausweis, ausweisMerken, ausweisVergessen, kopf } from "./ausweis.js";

(function () {
  const kasten = document.getElementById("anmeldung");
  if (!kasten) return;

  const formular = document.getElementById("an-formular");
  const stand = document.getElementById("an-stand");
  const meldung = document.getElementById("an-meldung");
  const feldMail = document.getElementById("an-email");
  const feldPass = document.getElementById("an-passwort");
  const feldPass2 = document.getElementById("an-passwort2");
  const feldCode = document.getElementById("an-code");
  const zeilePass2 = document.getElementById("an-zeile-passwort2");
  const zeileCode = document.getElementById("an-zeile-code");
  const knopfAn = document.getElementById("an-anmelden");
  const knopfNeu = document.getElementById("an-anlegen");
  const knopfAb = document.getElementById("an-abmelden");
  const umschalter = document.getElementById("an-umschalten");

  /* Zwei Zustaende: "anmelden" und "anlegen". Dieselben zwei Felder,
     beim Anlegen kommen Wiederholung und Einladungscode dazu. */
  let modus = "anmelden";

  function sage(text, schlimm) {
    meldung.textContent = text || "";
    meldung.dataset.schlimm = schlimm ? "ja" : "nein";
  }

  function zeigeModus() {
    const neu = modus === "anlegen";
    zeilePass2.hidden = !neu;
    zeileCode.hidden = !neu;
    knopfAn.hidden = neu;
    knopfNeu.hidden = !neu;
    umschalter.textContent = neu
      ? "Ich habe schon ein Konto"
      : "Ich brauche ein Konto";
    feldPass.setAttribute("autocomplete", neu ? "new-password" : "current-password");
    sage("");
  }

  function zeigeAngemeldet(konto) {
    formular.hidden = true;
    knopfAb.hidden = false;
    const rolle = konto.rolle === "admin" ? "Admin"
      : konto.rolle === "beta" ? "Beta-Tester" : "Nutzer";
    stand.textContent = "Angemeldet als " + konto.email + " — " + rolle
      + ", Stufe " + (konto.stufe || "free") + ".";
    sage("");
  }

  function zeigeAbgemeldet(text) {
    formular.hidden = false;
    knopfAb.hidden = true;
    stand.textContent = text || "Nicht angemeldet.";
  }

  async function ruf(weg, satz) {
    const antwort = await fetch(weg, {
      method: satz ? "POST" : "GET",
      headers: kopf(),
      body: satz ? JSON.stringify(satz) : undefined,
    });
    let daten = {};
    try {
      daten = await antwort.json();
    } catch (e) {
      /* eine leere Antwort ist auch eine */
    }
    return { code: antwort.status, ok: antwort.ok, d: daten };
  }

  /* --- beim Laden: gilt der Ausweis, den wir haben, noch? ------------- */

  async function nachsehen() {
    if (!ausweis()) {
      zeigeAbgemeldet();
      zeigeModus();
      return;
    }
    stand.textContent = "einen Moment …";
    let r;
    try {
      r = await ruf("/api/konten/stand");
    } catch (e) {
      /* Kein Netz ist kein Grund, den Ausweis wegzuwerfen. */
      zeigeAbgemeldet("Der Hub antwortet gerade nicht. Dein Ausweis bleibt liegen.");
      formular.hidden = true;
      return;
    }
    if (r.ok && r.d.angemeldet) {
      zeigeAngemeldet(r.d.konto);
      return;
    }
    /* 401 heisst: der Ausweis gilt nicht mehr - weg damit, sonst schickt
       ihn die Seite bei jedem Auftrag wieder mit und niemand versteht,
       warum es nicht geht. */
    ausweisVergessen();
    zeigeAbgemeldet("Deine Anmeldung ist abgelaufen. Melde dich neu an.");
    zeigeModus();
  }

  /* --- Anmelden ------------------------------------------------------ */

  async function anmelden(email, passwort, still) {
    const r = await ruf("/api/konten/anmelden", { email: email, passwort: passwort });
    if (r.ok && r.d.ausweis) {
      ausweisMerken(r.d.ausweis);
      zeigeAngemeldet(r.d.konto);
      return true;
    }
    if (!still) sage(r.d.fehler || "Das hat nicht geklappt.", true);
    return false;
  }

  knopfAn.addEventListener("click", async () => {
    const email = (feldMail.value || "").trim();
    const passwort = feldPass.value || "";
    if (!email || !passwort) {
      sage("E-Mail-Adresse und Passwort, bitte.", true);
      return;
    }
    knopfAn.disabled = true;
    sage("einen Moment …");
    try {
      if (await anmelden(email, passwort)) feldPass.value = "";
    } catch (e) {
      sage("Die Verbindung kam nicht zustande.", true);
    }
    knopfAn.disabled = false;
  });

  /* --- Konto anlegen ------------------------------------------------- */

  knopfNeu.addEventListener("click", async () => {
    const email = (feldMail.value || "").trim();
    const passwort = feldPass.value || "";
    if (passwort !== (feldPass2.value || "")) {
      sage("Die beiden Passworte sind nicht gleich.", true);
      return;
    }
    if (passwort.length < 10) {
      sage("Mindestens zehn Zeichen. Länge hilft mehr als Sonderzeichen.", true);
      return;
    }
    knopfNeu.disabled = true;
    sage("einen Moment …");
    try {
      const satz = { email: email, passwort: passwort };
      const code = (feldCode.value || "").trim();
      if (code) satz.code = code;
      const r = await ruf("/api/konten/anlegen", satz);
      if (!r.ok) {
        sage(r.d.fehler || "Das hat nicht geklappt.", true);
        knopfNeu.disabled = false;
        return;
      }
      /* Anlegen gibt keinen Ausweis. Also gleich anmelden.
         Der Hub antwortet auch dann mit "angelegt", wenn es die Adresse
         schon gibt - er verraet nicht, wer hier ein Konto hat. Klappt das
         Anmelden danach nicht, ist genau das der Fall. */
      const drin = await anmelden(email, passwort, true);
      if (drin) {
        feldPass.value = "";
        feldPass2.value = "";
        /* Neuer Zugang: Mia nimmt den Nutzer sofort an die Hand. Die
           Fuehrung springt nach /app/ und beginnt dort von vorn. */
        if (typeof window.repocityFuehrung === "function") window.repocityFuehrung();
        return;
      }
      sage("Es gibt hier schon ein Konto mit dieser Adresse. Melde dich mit "
        + "deinem Passwort an — oder setz es über „Passwort "
        + "vergessen“ neu.", true);
      modus = "anmelden";
      zeigeModus();
    } catch (e) {
      sage("Die Verbindung kam nicht zustande.", true);
    }
    knopfNeu.disabled = false;
  });

  /* --- Abmelden ------------------------------------------------------ */

  knopfAb.addEventListener("click", async () => {
    knopfAb.disabled = true;
    try {
      await ruf("/api/konten/abmelden", {});
    } catch (e) {
      /* Der Ausweis wird hier so oder so weggeworfen. Bleibt er am Hub
         noch kurz stehen, laeuft er von selbst ab. */
    }
    ausweisVergessen();
    knopfAb.disabled = false;
    zeigeAbgemeldet("Abgemeldet.");
    zeigeModus();
  });

  umschalter.addEventListener("click", () => {
    modus = modus === "anmelden" ? "anlegen" : "anmelden";
    zeigeModus();
  });

  zeigeModus();
  nachsehen();
})();
