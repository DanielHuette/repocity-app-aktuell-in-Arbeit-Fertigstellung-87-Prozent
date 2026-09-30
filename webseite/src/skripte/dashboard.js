/* Das Dashboard: Zahlen, Verlauf, Lernfortschritt - aus dem Hub gelesen.
 *
 * Bis zum 10.09.2026 stand hier die Auftragsmaske. Daniel: "die
 * Auftragseingabe unter Dashboard zu fuehren ist einfach Unsinn ... im
 * Dashboard muessen Grafiken und Performance zu sehen sein". Die Maske
 * liegt jetzt in der Kreativwerkstatt (auftrag.js).
 *
 * Gelesen wird mit dem Ausweis des Angemeldeten - er sieht sein Fach.
 * Ohne Ausweis steht hier nichts Erfundenes, sondern der Hinweis, sich
 * anzumelden. Keine Zahl wird geschaetzt: was nicht da ist, ist ein Strich.
 */

import { kopf, angemeldet } from "./ausweis.js";

(function () {
  const wurzel = document.getElementById("dashboard");
  if (!wurzel) return;
  const hinweis = document.getElementById("db-hinweis");

  function setze(id, wert) {
    const el = document.getElementById(id);
    if (el) el.textContent = wert;
  }

  async function hole(weg) {
    const a = await fetch(weg, { headers: kopf() });
    if (!a.ok) throw new Error(String(a.status));
    return a.json();
  }

  function geld(x) {
    const n = Number(x);
    return isNaN(n) ? "\u2013" : (n > 0 ? "+" : "") + n.toFixed(2).replace(".", ",") + " USDT";
  }
  /* "seit 3 h 12 min" - aus einem Zeitpunkt. */
  function dauer(iso) {
    const t = Date.parse(iso || "");
    if (isNaN(t)) return "\u2013";
    let s = Math.max(0, Math.floor((Date.now() - t) / 1000));
    const tage = Math.floor(s / 86400); s -= tage * 86400;
    const h = Math.floor(s / 3600); s -= h * 3600;
    const min = Math.floor(s / 60);
    if (tage) return tage + " d " + h + " h";
    if (h) return h + " h " + min + " min";
    return min + " min";
  }
  function seitWann(iso) {
    const d = dauer(iso);
    return d === "\u2013" ? "" : "vor " + d;
  }

  /* Aufträge je Tag, letzte sieben Tage, aeltester zuerst. */
  function jeTag(auftraege, tage) {
    const tagMs = 24 * 60 * 60 * 1000;
    const heute = Math.floor(Date.now() / tagMs);
    const aus = [];
    for (let z = tage - 1; z >= 0; z--) {
      const tag = heute - z;
      aus.push(auftraege.filter((a) => {
        const t = Date.parse(a.angelegt || "");
        return !isNaN(t) && Math.floor(t / tagMs) === tag;
      }).length);
    }
    return aus;
  }

  function balken(werte) {
    const svg = document.getElementById("db-verlauf");
    if (!svg) return;
    const hoechst = Math.max(1, ...werte);
    const B = 300, H = 96, luecke = 6;
    const breite = (B - luecke * (werte.length - 1)) / werte.length;
    svg.setAttribute("viewBox", "0 0 " + B + " " + H);
    svg.innerHTML = werte.map((n, i) => {
      const h = n === 0 ? 2 : (H * n) / hoechst;
      const x = i * (breite + luecke);
      const klasse = n === 0 ? "leer" : "voll";
      return '<rect class="' + klasse + '" x="' + x.toFixed(1) +
        '" y="' + (H - h).toFixed(1) + '" width="' + breite.toFixed(1) +
        '" height="' + h.toFixed(1) + '" rx="2"><title>' + n +
        '</title></rect>';
    }).join("");
  }

  async function laden() {
    if (!angemeldet()) {
      hinweis.textContent = "Melde dich unter Zugang an — dann stehen hier deine Zahlen.";
      hinweis.hidden = false;
      return;
    }
    let auftraege = [], meldungen = [], stand = {}, konto = {};
    try {
      auftraege = (await hole("/api/hub/auftraege")).auftraege || [];
      meldungen = (await hole("/api/hub/meldungen?anzahl=200")).meldungen || [];
      stand = await hole("/api/hub/stand").catch(() => ({}));
      konto = await hole("/api/konten/stand").catch(() => ({}));
    } catch (e) {
      hinweis.textContent = "Der Hub antwortet gerade nicht (" + e.message + ").";
      hinweis.hidden = false;
      return;
    }
    hinweis.hidden = true;

    const offen = ["gesendet", "kostenfreigabe", "angenommen", "laeuft", "pruefung"];
    const z = (s) => auftraege.filter((a) => a.zustand === s).length;
    setze("db-laufen", auftraege.filter((a) => offen.includes(a.zustand)).length);
    setze("db-wartet", z("vorlage") + z("kostenfreigabe"));
    setze("db-fertig", z("fertig"));
    setze("db-fehler", z("fehler"));
    const kosten = auftraege.reduce((s, a) => s + (Number(a.kosten) || 0), 0);
    setze("db-kosten", kosten.toFixed(2).replace(".", ",") + " €");

    balken(jeTag(auftraege, 7));

    /* Zuletzt: der juengste Auftrag. */
    const juengst = auftraege.slice().sort((a, b) =>
      String(b.angelegt || "").localeCompare(String(a.angelegt || "")))[0];
    if (juengst) {
      setze("db-zuletzt-art", juengst.art || "\u2013");
      setze("db-zuletzt-zustand", (juengst.zustand || "") + " \u00b7 " + seitWann(juengst.angelegt));
      setze("db-zuletzt-text", (juengst.text || "").slice(0, 160));
    }

    /* Trading: dieselbe Meldung wie auf der Trading-Seite (absender "trading"). */
    const handel = meldungen.filter((m) => m.absender === "trading" && m.daten &&
      (m.daten.positionen || m.daten.trades))[0];
    if (handel) {
      const pos = handel.daten.positionen || [];
      const trades = handel.daten.trades || [];
      const summe = (l) => l.reduce((s, x) => s + (Number(x.pnl) || 0), 0);
      setze("db-pnl-offen", geld(summe(pos)));
      setze("db-pnl-fuenf", geld(summe(trades.slice(0, 5))));
      setze("db-trades", trades.length);
      const tl = document.getElementById("db-trade-liste");
      if (tl && trades.length) {
        tl.innerHTML = "";
        trades.slice(0, 5).forEach((t) => {
          const li = document.createElement("li");
          li.textContent = String(t.wann || "").slice(0, 16).replace("T", " ") + " \u00b7 " +
            (t.markt || "") + " " + (t.seite || "") + " \u00b7 " + geld(t.pnl);
          tl.appendChild(li);
        });
      }
    }

    /* Laufzeiten. Der Rechner meldet alle zehn Minuten einen Puls; bleibt er
       eine Stunde aus, gilt er als weg. */
    const r = stand.rechner;
    if (r && r.seit) {
      setze("db-rechner", dauer(r.seit));
      setze("db-rechner-zeile", "Rechner l\u00e4uft \u00b7 letzter Puls " + seitWann(r.zuletzt));
    } else {
      setze("db-rechner", "aus");
      setze("db-rechner-zeile", "Rechner \u2013 kein Puls seit \u00fcber einer Stunde");
    }
    if (stand.webseite_seit) setze("db-webseite", dauer(stand.webseite_seit));
    if (konto.sitzung_seit) setze("db-sitzung", dauer(konto.sitzung_seit));

    const liste = document.getElementById("db-wartend");
    /* Offene Entscheidungen - und die Rueckfragen des Sekretaers (art
       "rueckfrage", noch ohne Antwort): beantwortet werden sie dort, wo der
       Auftrag bestellt wurde, oder in der App. */
    const wartend = meldungen.filter((m) =>
      m.entscheidung === "offen" || (m.art === "rueckfrage" && !m.entscheidung));
    if (liste) {
      liste.innerHTML = "";
      wartend.slice(0, 8).forEach((m) => {
        const li = document.createElement("li");
        const vorsatz = m.art === "rueckfrage" ? "R\u00fcckfrage" : (m.absender || "");
        li.textContent = vorsatz + ": " + (m.zusammenfassung || m.text || "");
        liste.appendChild(li);
      });
      const kasten = document.getElementById("db-wartend-kasten");
      if (kasten) kasten.hidden = wartend.length === 0;
    }
  }

  laden();
  /* Alle 30 Sekunden nachsehen - derselbe Takt wie die Leitung. */
  setInterval(laden, 30000);
})();
