/* Handelsanzeige und Boersenschalter. Laeuft ohne Server: der Kurs kommt aus
   den offenen Schnittstellen der Boersen, die Schalterstellung aus dem Browser.
   Schluessel werden hier nie angefasst — eine Webseite ist kein Ort dafuer. */

import { kopf, angemeldet } from "./ausweis.js";

(function () {
  "use strict";

  var QUELLEN = {
    okx: {
      url: "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT",
      lies: function (d) { return d && d.data && d.data[0] ? d.data[0].last : null; },
    },
    pionex: {
      url: "https://api.pionex.com/api/v1/market/tickers?symbol=BTC_USDT",
      lies: function (d) {
        var t = d && d.data && d.data.tickers && d.data.tickers[0];
        return t ? t.close : null;
      },
    },
  };

  function an(id) {
    try { return localStorage.getItem("rc_boerse_" + id) !== "aus"; } catch (e) { return true; }
  }
  function setze(id, wert) {
    try { localStorage.setItem("rc_boerse_" + id, wert ? "an" : "aus"); } catch (e) {}
  }
  function aktive() {
    return Object.keys(QUELLEN).filter(an);
  }

  /* ---- Schalter (Einstellungen) ---------------------------------- */
  var schalter = Array.prototype.slice.call(document.querySelectorAll("[data-boerse]"));
  schalter.forEach(function (s) {
    var id = s.getAttribute("data-boerse");
    s.checked = an(id);
    s.addEventListener("change", function () {
      setze(id, s.checked);
      zeichne();
    });
  });

  /* ---- Anzeige (Trading) ----------------------------------------- */
  var kursFeld = document.getElementById("handel-kurs");
  var quelleFeld = document.getElementById("handel-quelle");
  var lageFeld = document.getElementById("handel-lage");
  var zeilen = Array.prototype.slice.call(document.querySelectorAll("[data-boerse-zeile]"));

  function zeichne() {
    var liste = aktive();
    zeilen.forEach(function (z) {
      var id = z.getAttribute("data-boerse-zeile");
      var marke = z.querySelector("[data-stand]");
      var ist = liste.indexOf(id) >= 0;
      z.setAttribute("data-aus", ist ? "nein" : "ja");
      if (marke) marke.textContent = ist ? "an" : "aus";
    });
    if (lageFeld) {
      lageFeld.textContent = liste.length
        ? "Gehandelt wird ueber: " + liste.map(gross).join(", ")
        : "Keine Boerse eingeschaltet — es wird weder beobachtet noch gehandelt.";
    }
    if (quelleFeld) {
      quelleFeld.textContent = liste.length ? "beobachtet " + gross(liste[0]) : "nichts eingeschaltet";
    }
    if (!liste.length && kursFeld) kursFeld.textContent = "--";
  }

  function gross(id) { return id === "okx" ? "OKX" : "Pionex"; }

  function holeKurs() {
    var liste = aktive();
    if (!liste.length || !kursFeld) return;
    var q = QUELLEN[liste[0]];
    fetch(q.url, { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var p = q.lies(d);
        kursFeld.textContent = p ? Number(p).toLocaleString("de-DE", { maximumFractionDigits: 2 }) : "--";
      })
      .catch(function () { kursFeld.textContent = "--"; });
  }

  /* ---- Setups, Positionen, Verlauf --------------------------------
     Der Vertrag mit der Trading-Strasse: der Handelsbeobachter legt am Hub
     eine Meldung mit absender "trading" ab, in deren daten stehen

       setups:     [{markt, seite, stand, einstieg, stop, ziele[],
                     groesse, pnl, pnlReal, grund, wann}]
       positionen: [{markt, seite, groesse, einstieg, stop, ziele[],
                     pnl, pnlReal}]
       trades:     [{wann, markt, seite, einstieg, ausstieg, pnl}]

     pnl ist das Offene (unrealized), pnlReal das schon Verbuchte
     (realized) - bei einer Position, von der ein Teil am ersten Ziel
     mitgenommen wurde, stehen beide nebeneinander. Bei einem Setup, das noch
     nicht gefuellt ist, sind beide leer: es gibt nichts zu gewinnen und
     nichts zu verlieren, solange nichts laeuft. Was dann auf dem Spiel
     stuende, steht als Risiko und Chance daneben - gerechnet aus Einstieg,
     Stop und erstem Ziel mal Groesse.

     `ziel` (Einzahl) wird weiter gelesen: aeltere Meldungen tragen nur eins.

     Die neueste solche Meldung zaehlt. Gibt es keine, bleiben die Platzhalter
     stehen - eine erfundene Zahl steht hier nie. Dieselbe Meldung liest die
     App (Regel: Webseite wie App und umgekehrt). */

  function zahl(x) {
    var n = Number(x);
    return isNaN(n) || x === null || x === "" || x === undefined
      ? "–" : n.toLocaleString("de-DE", { maximumFractionDigits: 2 });
  }
  function pnlKlasse(x) {
    var n = Number(x);
    return isNaN(n) || n === 0 ? "" : (n > 0 ? "plus" : "minus");
  }
  function pnlText(x) {
    var n = Number(x);
    if (isNaN(n) || x === null || x === "" || x === undefined) return "–";
    return (n > 0 ? "+" : "") + zahl(n);
  }
  function pnlMarke(el, summe, vorsatz) {
    if (!el) return;
    var n = Number(summe);
    el.textContent = vorsatz + " " + (isNaN(n) ? "–" : (n > 0 ? "+" : "") + zahl(n) + " USDT");
    el.setAttribute("data-vorzeichen", isNaN(n) || n === 0 ? "0" : (n > 0 ? "1" : "-1"));
  }
  function td(text, klasse) {
    var z = document.createElement("td");
    z.textContent = text;
    if (klasse) z.className = klasse;
    return z;
  }

  /** Die drei Ziele einer Zeile - egal ob als Liste oder als einzelnes Ziel. */
  function ziele(o) {
    var z = o.ziele;
    if (!z || !z.length) z = (o.ziel === undefined || o.ziel === null) ? [] : [o.ziel];
    return [z[0], z[1], z[2]];
  }

  /**
   * Was auf dem Spiel steht, in USDT: bis zum Stop und bis zum ersten Ziel.
   * Gerechnet, nicht geschaetzt - Abstand mal Groesse, Vorzeichen nach Seite.
   * Fehlt eine der Zahlen, kommt nichts heraus: ein halb gerechnetes Risiko
   * waere schlimmer als gar keins.
   */
  function spanne(o, bis) {
    var ein = Number(o.einstieg), ziel = Number(bis), gr = Number(o.groesse);
    if (isNaN(ein) || isNaN(ziel) || isNaN(gr)) return null;
    var lang = String(o.seite || "").toLowerCase().indexOf("short") < 0;
    return (lang ? (ziel - ein) : (ein - ziel)) * gr;
  }

  /** Eine Zeile fuer beide Felder - sie tragen dieselben Spalten. */
  function handelsZeile(o, mitStand) {
    var tr = document.createElement("tr");
    var z = ziele(o);
    tr.appendChild(td(o.markt || "–"));
    tr.appendChild(td(o.seite || "–"));
    if (mitStand) {
      var s = document.createElement("td");
      var marke = document.createElement("span");
      marke.className = "stand-marke";
      marke.textContent = o.stand || "erkannt";
      s.appendChild(marke);
      tr.appendChild(s);
    } else {
      tr.appendChild(td(zahl(o.groesse)));
    }
    tr.appendChild(td(zahl(o.einstieg)));
    tr.appendChild(td(zahl(o.stop), "stop"));
    tr.appendChild(td(zahl(z[0]), z[0] === undefined ? "" : "ziel"));
    tr.appendChild(td(zahl(z[1]), z[1] === undefined ? "" : "ziel"));
    tr.appendChild(td(zahl(z[2]), z[2] === undefined ? "" : "ziel"));
    var risiko = spanne(o, o.stop);
    var chance = spanne(o, z[0]);
    tr.appendChild(td(risiko === null ? "–" : pnlText(risiko), pnlKlasse(risiko)));
    tr.appendChild(td(chance === null ? "–" : pnlText(chance), pnlKlasse(chance)));
    tr.appendChild(td(pnlText(o.pnl), pnlKlasse(o.pnl)));
    tr.appendChild(td(pnlText(o.pnlReal), pnlKlasse(o.pnlReal)));
    return tr;
  }

  function fuelle(koerperId, liste, mitStand, unId, realId) {
    var kb = document.getElementById(koerperId);
    if (!kb || !liste.length) return;
    kb.innerHTML = "";
    var offen = 0, echt = 0, hatOffen = false, hatEcht = false;
    liste.forEach(function (o) {
      kb.appendChild(handelsZeile(o, mitStand));
      if (o.pnl !== undefined && o.pnl !== null && o.pnl !== "") {
        offen += Number(o.pnl) || 0; hatOffen = true;
      }
      if (o.pnlReal !== undefined && o.pnlReal !== null && o.pnlReal !== "") {
        echt += Number(o.pnlReal) || 0; hatEcht = true;
      }
    });
    pnlMarke(document.getElementById(unId), hatOffen ? offen : NaN, "offen");
    pnlMarke(document.getElementById(realId), hatEcht ? echt : NaN, "realisiert");
  }

  function zeigeHandel(d) {
    fuelle("setup-zeilen", (d && d.setups) || [], true, "setup-pnl-un", "setup-pnl-real");
    fuelle("pos-zeilen", (d && d.positionen) || [], false, "pos-pnl-un", "pos-pnl-real");

    var trades = (d && d.trades) || [];
    var vz = document.getElementById("verlauf-zeilen");
    if (vz && trades.length) {
      vz.innerHTML = "";
      var gesamt = 0;
      trades.slice(0, 20).forEach(function (t) {
        var tr = document.createElement("tr");
        tr.appendChild(td(String(t.wann || "").slice(0, 16).replace("T", " ")));
        tr.appendChild(td(t.markt || "–"));
        tr.appendChild(td(t.seite || "–"));
        tr.appendChild(td(zahl(t.einstieg)));
        tr.appendChild(td(zahl(t.ausstieg)));
        tr.appendChild(td(pnlText(t.pnl), pnlKlasse(t.pnl)));
        vz.appendChild(tr);
        gesamt += Number(t.pnl) || 0;
      });
      pnlMarke(document.getElementById("verlauf-pnl"), gesamt, "gesamt");
    }
  }

  function holeHandel() {
    if (!document.getElementById("pos-zeilen") || !angemeldet()) return;
    fetch("/api/hub/meldungen?anzahl=200", { headers: kopf() })
      .then(function (r) { return r.ok ? r.json() : { meldungen: [] }; })
      .then(function (d) {
        var m = (d.meldungen || []).filter(function (x) {
          return x.absender === "trading" && x.daten &&
            (x.daten.positionen || x.daten.setups || x.daten.trades);
        });
        if (m.length) zeigeHandel(m[0].daten);
      })
      .catch(function () { /* Platzhalter bleiben stehen */ });
  }

  zeichne();
  if (kursFeld) {
    holeKurs();
    setInterval(holeKurs, 15000);
    holeHandel();
    setInterval(holeHandel, 30000);
  }
})();
