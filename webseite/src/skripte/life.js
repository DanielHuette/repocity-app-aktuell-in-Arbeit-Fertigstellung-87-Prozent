/* Life Automation — Muster, Dateien, Termine.
 *
 * Alles hängt am Hub, nicht am Browser: was hier eingetragen wird, liest der
 * Rechner. Ein Muster, das nur im Browser läge, würde kein Agent je sehen.
 *
 *   GET/POST /api/muster            die Textmuster
 *   GET      /api/dateien           die Köpfe, nie der Inhalt
 *   GET      /api/dateien/holen/:id eine Datei
 *   POST     /api/dateien/ablegen   hochladen
 *   POST     /api/dateien/stand/:id freigeben oder verwerfen
 *   GET/POST /api/termine           der Kalender
 *
 * Ohne Anmeldung geht nichts - die Fächer hängen am Konto.
 */
import { angemeldet, kopf } from "./ausweis.js";

const melder = document.querySelector("[data-melder]");

function sagen(text, schlimm) {
  if (!melder) return;
  melder.textContent = text || "";
  melder.hidden = !text;
  melder.classList.toggle("schlimm", !!schlimm);
  if (text && !schlimm) setTimeout(() => { if (melder.textContent === text) melder.hidden = true; }, 4000);
}

async function hole(weg, optionen) {
  const antwort = await fetch(weg, Object.assign({ headers: kopf() }, optionen || {}));
  if (!antwort.ok) {
    const grund = antwort.status === 401
      ? "Dafür musst du angemeldet sein."
      : "Der Hub antwortet mit " + antwort.status + ".";
    throw new Error(grund);
  }
  return antwort.json();
}

/* ---------------------------------------------------------- Die Reiter */

const tafeln = Array.from(document.querySelectorAll("[data-feld]"));
const reiter = Array.from(document.querySelectorAll("[data-reiter]"));

function zeige(feld) {
  reiter.forEach((r) => r.setAttribute("aria-selected", String(r.dataset.reiter === feld)));
  tafeln.forEach((t) => { t.hidden = t.dataset.feld !== feld; });
  try { sessionStorage.setItem("rc_life_reiter", feld); } catch (e) {}
  if (feld === "kalender") kalenderZeichnen();
}

reiter.forEach((r) => r.addEventListener("click", () => zeige(r.dataset.reiter)));

/* Die drei Tonlagen der E-Mail. */
const tonknoepfe = Array.from(document.querySelectorAll("[data-ton]"));
tonknoepfe.forEach((k) => k.addEventListener("click", () => {
  tonknoepfe.forEach((x) => x.setAttribute("aria-selected", String(x === k)));
  document.querySelectorAll("[data-tonfeld]").forEach((f) => {
    f.hidden = f.dataset.tonfeld !== k.dataset.ton;
  });
}));

/* ---------------------------------------------------------- Die Muster */

const musterfelder = Array.from(document.querySelectorAll("[data-muster]"));

async function musterLaden() {
  const d = await hole("/api/muster");
  musterfelder.forEach((f) => {
    const m = (d.muster || {})[f.dataset.muster];
    if (m && typeof m.text === "string") f.value = m.text;
  });
}

/* Gespeichert wird beim Verlassen des Feldes, nicht bei jedem Tastendruck:
   sonst schreibt ein Absatz zweihundert Mal in den Speicher. */
musterfelder.forEach((f) => {
  let zuletzt = f.value;
  f.addEventListener("blur", async () => {
    if (f.value === zuletzt) return;
    try {
      await hole("/api/muster", {
        method: "POST",
        body: JSON.stringify({ art: f.dataset.muster, text: f.value }),
      });
      zuletzt = f.value;
      sagen("Muster gespeichert");
    } catch (e) {
      sagen("Nicht gespeichert: " + e.message, true);
    }
  });
});

/* --------------------------------------------------------- Die Dateien */

function lesbar(bytes) {
  if (bytes > 1048576) return (bytes / 1048576).toFixed(1) + " MB";
  if (bytes > 1024) return Math.round(bytes / 1024) + " KB";
  return bytes + " Byte";
}

function datum(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("de-DE",
      { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch (e) { return iso.slice(0, 10); }
}

const listen = Array.from(document.querySelectorAll("[data-liste]"));

async function dateienLaden() {
  let d;
  try { d = await hole("/api/dateien"); } catch (e) { sagen(e.message, true); return; }
  const alle = d.dateien || [];
  listen.forEach((ul) => {
    const art = ul.dataset.liste;
    const wofuer = ul.dataset.wofuer;
    const meine = alle.filter((x) => x.art === art && (!wofuer || x.wofuer === wofuer));
    ul.innerHTML = "";
    if (!meine.length) {
      const li = document.createElement("li");
      li.className = "klein";
      li.textContent = art === "entwurf"
        ? "Noch nichts vorgelegt."
        : "Noch nichts hinterlegt.";
      ul.appendChild(li);
      return;
    }
    meine.forEach((x) => ul.appendChild(zeile(x, art)));
  });
}

function zeile(x, art) {
  const li = document.createElement("li");

  const name = document.createElement("span");
  name.className = "name";
  name.textContent = x.name;
  li.appendChild(name);

  const klein = document.createElement("span");
  klein.className = "klein";
  klein.textContent = lesbar(x.bytes) + " · " + datum(x.abgelegt)
    + (art === "entwurf" && x.stand ? " · " + x.stand : "");
  if (x.stand === "freigegeben") klein.classList.add("stand-freigegeben");
  if (x.stand === "verworfen") klein.classList.add("stand-verworfen");
  li.appendChild(klein);

  const ansehen = document.createElement("button");
  ansehen.type = "button";
  ansehen.textContent = "Ansehen";
  ansehen.addEventListener("click", () => oeffne(x));
  li.appendChild(ansehen);

  if (art === "entwurf") {
    const ja = document.createElement("button");
    ja.type = "button"; ja.className = "ja"; ja.textContent = "Freigeben";
    ja.addEventListener("click", () => stand(x.id, "freigegeben"));
    li.appendChild(ja);

    const nein = document.createElement("button");
    nein.type = "button"; nein.textContent = "Verwerfen";
    nein.addEventListener("click", () => stand(x.id, "verworfen"));
    li.appendChild(nein);
  } else {
    const weg = document.createElement("button");
    weg.type = "button"; weg.textContent = "Entfernen";
    weg.addEventListener("click", () => loeschen(x.id));
    li.appendChild(weg);
  }
  return li;
}

async function oeffne(x) {
  try {
    const d = await hole("/api/dateien/holen/" + encodeURIComponent(x.id));
    const roh = atob(d.datei.inhalt);
    const feld = new Uint8Array(roh.length);
    for (let i = 0; i < roh.length; i++) feld[i] = roh.charCodeAt(i);
    const adresse = URL.createObjectURL(new Blob([feld], { type: d.datei.typ || "application/pdf" }));
    window.open(adresse, "_blank", "noopener");
    /* Nach einer Minute freigeben - vorher liest der neue Tab noch daraus. */
    setTimeout(() => URL.revokeObjectURL(adresse), 60000);
  } catch (e) {
    sagen("Nicht zu öffnen: " + e.message, true);
  }
}

async function stand(id, wie) {
  try {
    await hole("/api/dateien/stand/" + encodeURIComponent(id), {
      method: "POST", body: JSON.stringify({ stand: wie }),
    });
    sagen(wie === "freigegeben" ? "Freigegeben — geht hinaus." : "Verworfen.");
    dateienLaden();
  } catch (e) { sagen(e.message, true); }
}

async function loeschen(id) {
  try {
    await hole("/api/dateien/loeschen/" + encodeURIComponent(id), {
      method: "POST", body: "{}",
    });
    dateienLaden();
  } catch (e) { sagen(e.message, true); }
}

document.querySelectorAll("[data-hochladen]").forEach((feld) => {
  feld.addEventListener("change", async () => {
    const dateien = Array.from(feld.files || []);
    if (!dateien.length) return;
    for (const f of dateien) {
      try {
        sagen("Lade " + f.name + " …");
        const inhalt = await alsBase64(f);
        await hole("/api/dateien/ablegen", {
          method: "POST",
          body: JSON.stringify({
            art: feld.dataset.hochladen,
            wofuer: feld.dataset.wofuer,
            name: f.name,
            typ: f.type || "application/octet-stream",
            inhalt,
          }),
        });
      } catch (e) {
        sagen(f.name + ": " + e.message, true);
      }
    }
    feld.value = "";
    sagen("Hochgeladen.");
    dateienLaden();
  });
});

function alsBase64(datei) {
  return new Promise((ok, fehl) => {
    const leser = new FileReader();
    leser.onerror = () => fehl(new Error("nicht lesbar"));
    leser.onload = () => {
      const s = String(leser.result || "");
      const komma = s.indexOf(",");
      ok(komma >= 0 ? s.slice(komma + 1) : s);
    };
    leser.readAsDataURL(datei);
  });
}

/* --------------------------------------------------------- Die Termine */

let termine = [];
let monat = new Date();
monat.setDate(1);

async function termineLaden() {
  try {
    const d = await hole("/api/termine");
    termine = d.termine || [];
  } catch (e) {
    termine = [];
    sagen(e.message, true);
  }
  kalenderZeichnen();
  weckerPruefen();
}

function kalenderZeichnen() {
  const raster = document.querySelector("[data-raster]");
  const titel = document.querySelector("[data-monatstitel]");
  if (!raster || !titel) return;

  titel.textContent = monat.toLocaleDateString("de-DE", { month: "long", year: "numeric" });

  /* Montag ist der erste Tag der Woche - getDay() zählt ab Sonntag. */
  const ersterTag = (new Date(monat.getFullYear(), monat.getMonth(), 1).getDay() + 6) % 7;
  const tageImMonat = new Date(monat.getFullYear(), monat.getMonth() + 1, 0).getDate();
  const heute = new Date();

  raster.innerHTML = "";
  for (let i = 0; i < ersterTag; i++) {
    const leer = document.createElement("div");
    leer.className = "tag leer";
    raster.appendChild(leer);
  }
  for (let t = 1; t <= tageImMonat; t++) {
    const zelle = document.createElement("div");
    zelle.className = "tag";
    if (heute.getFullYear() === monat.getFullYear()
        && heute.getMonth() === monat.getMonth() && heute.getDate() === t) {
      zelle.classList.add("heute");
    }
    const zahl = document.createElement("span");
    zahl.className = "zahl";
    zahl.textContent = String(t);
    zelle.appendChild(zahl);

    const tagesschluessel = monat.getFullYear() + "-"
      + String(monat.getMonth() + 1).padStart(2, "0") + "-" + String(t).padStart(2, "0");
    termine.filter((x) => String(x.beginn).startsWith(tagesschluessel)).forEach((x) => {
      const p = document.createElement("span");
      p.className = "punkt";
      p.textContent = String(x.beginn).slice(11, 16) + " " + (x.titel || "");
      p.title = (x.art || "") + (x.ort ? " · " + x.ort : "");
      zelle.appendChild(p);
    });
    raster.appendChild(zelle);
  }

  const liste = document.querySelector("[data-terminliste]");
  if (!liste) return;
  liste.innerHTML = "";
  const jetzt = new Date().toISOString().slice(0, 16);
  const kommend = termine.filter((x) => x.beginn >= jetzt).slice(0, 12);
  if (!kommend.length) {
    const li = document.createElement("li");
    li.className = "klein";
    li.textContent = "Keine kommenden Termine.";
    liste.appendChild(li);
    return;
  }
  kommend.forEach((x) => {
    const li = document.createElement("li");
    const zeit = document.createElement("span");
    zeit.className = "zeit";
    zeit.textContent = new Date(x.beginn).toLocaleString("de-DE",
      { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
    li.appendChild(zeit);

    const titel = document.createElement("span");
    titel.className = "titel";
    titel.textContent = x.titel + (x.ort ? " · " + x.ort : "");
    li.appendChild(titel);

    const art = document.createElement("span");
    art.className = "klein";
    art.textContent = x.art || "";
    li.appendChild(art);

    const weg = document.createElement("button");
    weg.type = "button"; weg.textContent = "Löschen";
    weg.addEventListener("click", async () => {
      try {
        await hole("/api/termine/loeschen/" + encodeURIComponent(x.id),
          { method: "POST", body: "{}" });
        termineLaden();
      } catch (e) { sagen(e.message, true); }
    });
    li.appendChild(weg);
    liste.appendChild(li);
  });
}

document.querySelectorAll("[data-monat]").forEach((k) => {
  k.addEventListener("click", () => {
    monat.setMonth(monat.getMonth() + Number(k.dataset.monat));
    kalenderZeichnen();
  });
});

const terminform = document.querySelector("[data-terminform]");
if (terminform) {
  terminform.addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = new FormData(terminform);
    try {
      await hole("/api/termine", {
        method: "POST",
        body: JSON.stringify({
          titel: f.get("titel"), art: f.get("art"),
          beginn: f.get("beginn"), ende: f.get("ende"),
          ort: f.get("ort"), beschreibung: f.get("beschreibung"),
          weckenMin: Number(f.get("weckenMin") || 0),
        }),
      });
      terminform.reset();
      sagen("Termin eingetragen.");
      termineLaden();
    } catch (x) { sagen(x.message, true); }
  });
}

/* ---------------------------------------------- Verknüpfte Kalender */

/* Die Adressen liegen als eigenes Muster "kalender" - eine Zeile je Kalender.
   Der Rechner liest dasselbe Fach und holt von dort die fremden Termine. */

async function kalenderLaden() {
  try {
    const d = await hole("/api/muster");
    const text = ((d.muster || {}).kalender || {}).text || "";
    zeigeKalender(text.split("\n").map((z) => z.trim()).filter(Boolean));
  } catch (e) { /* ohne Kalenderliste laeuft der Rest weiter */ }
}

function zeigeKalender(adressen) {
  const ul = document.querySelector("[data-kalenderliste]");
  if (!ul) return;
  ul.innerHTML = "";
  if (!adressen.length) {
    const li = document.createElement("li");
    li.className = "klein";
    li.textContent = "Noch kein Kalender verknüpft.";
    ul.appendChild(li);
    return;
  }
  adressen.forEach((a) => {
    const li = document.createElement("li");
    const n = document.createElement("span");
    n.className = "name"; n.textContent = a;
    li.appendChild(n);
    const weg = document.createElement("button");
    weg.type = "button"; weg.textContent = "Trennen";
    weg.addEventListener("click", async () => {
      const rest = adressen.filter((x) => x !== a);
      try {
        await hole("/api/muster", {
          method: "POST",
          body: JSON.stringify({ art: "kalender", text: rest.join("\n") }),
        });
        zeigeKalender(rest);
        sagen("Getrennt.");
      } catch (e) { sagen(e.message, true); }
    });
    li.appendChild(weg);
    ul.appendChild(li);
  });
}

const kalenderKnopf = document.querySelector("[data-kalenderspeichern]");
if (kalenderKnopf) {
  kalenderKnopf.addEventListener("click", async () => {
    const feld = document.querySelector("[data-kalenderadresse]");
    const adresse = ((feld && feld.value) || "").trim();
    if (!adresse) return;
    if (!/^https?:\/\//i.test(adresse)) {
      sagen("Das ist keine Adresse — sie muss mit https:// anfangen.", true);
      return;
    }
    try {
      const vorhanden = await hole("/api/muster");
      const alt = ((vorhanden.muster || {}).kalender || {}).text || "";
      const zeilen = alt.split("\n").map((z) => z.trim()).filter(Boolean);
      if (zeilen.includes(adresse)) { sagen("Steht schon drin."); return; }
      zeilen.push(adresse);
      await hole("/api/muster", {
        method: "POST",
        body: JSON.stringify({ art: "kalender", text: zeilen.join("\n") }),
      });
      feld.value = "";
      sagen("Kalender verknüpft.");
      zeigeKalender(zeilen);
    } catch (e) { sagen(e.message, true); }
  });
}

/* ------------------------------------------------------- Der Wecker */

const wecker = document.querySelector("[data-wecker]");
const geweckt = new Set();

function weckerPruefen() {
  if (!wecker) return;
  const jetzt = Date.now();
  for (const t of termine) {
    if (!t.weckenMin) continue;
    if (geweckt.has(t.id)) continue;
    const beginn = new Date(t.beginn).getTime();
    if (isNaN(beginn)) continue;
    const wann = beginn - t.weckenMin * 60000;
    if (jetzt >= wann && jetzt < beginn) {
      geweckt.add(t.id);
      zeigeWecker(t);
      break;
    }
  }
}

function zeigeWecker(t) {
  wecker.querySelector("[data-weckertitel]").textContent = t.titel || "Termin";
  wecker.querySelector("[data-weckerzeit]").textContent =
    new Date(t.beginn).toLocaleString("de-DE",
      { weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })
    + (t.ort ? " · " + t.ort : "");
  wecker.querySelector("[data-weckertext]").textContent = t.beschreibung || "";
  wecker.hidden = false;

  /* Zusätzlich die Benachrichtigung des Browsers, falls erlaubt - sie kommt
     auch durch, wenn das Fenster im Hintergrund liegt. Auf dem Handy
     übernimmt das die App und legt sie auf den Sperrbildschirm. */
  try {
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(t.titel || "Termin", {
        body: new Date(t.beginn).toLocaleString("de-DE") + (t.ort ? "\n" + t.ort : ""),
        tag: "rc-termin-" + t.id,
      });
    }
  } catch (e) { /* ohne Benachrichtigung bleibt das Fenster im Bild */ }
}

const weckerZu = document.querySelector("[data-weckerzu]");
if (weckerZu) weckerZu.addEventListener("click", () => { wecker.hidden = true; });

/* ------------------------------------------------------------ Start */

if (!angemeldet()) {
  sagen("Melde dich an — deine Muster, Unterlagen und Termine hängen an deinem Konto.", true);
} else {
  musterLaden().catch((e) => sagen(e.message, true));
  dateienLaden();
  termineLaden();
  kalenderLaden();
  /* Jede Minute nachsehen, ob ein Termin ansteht. */
  setInterval(weckerPruefen, 60000);
  /* Alle fünf Minuten nachsehen, ob ein Agent etwas vorgelegt hat. */
  setInterval(dateienLaden, 300000);
  try {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  } catch (e) {}
}

try {
  const gemerkt = sessionStorage.getItem("rc_life_reiter");
  if (gemerkt) zeige(gemerkt);
} catch (e) {}
