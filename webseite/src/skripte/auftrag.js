/* Das Auftragsfeld auf dem Dashboard: Art waehlen, sagen was gebaut werden
   soll, absenden. Abgesendet wird an den Hub, dieselbe Stelle, an die auch
   die App ihre Auftraege gibt.
 *
 * Der Hub nimmt einen Auftrag nur von jemandem an, der sich ausgewiesen hat.
 * Kommt eine Absage, wird sie im Klartext hingeschrieben — nicht so getan,
 * als waere der Auftrag unterwegs.
 */

import { kopf } from "./ausweis.js";

(function () {
  "use strict";

  var feld = document.getElementById("auftrag-text");
  var senden = document.getElementById("auftrag-senden");
  var leeren = document.getElementById("auftrag-leeren");
  var hinweis = document.getElementById("auftrag-hinweis");
  var laeuftAn = document.getElementById("laeuft-an");
  if (!feld || !senden) return;

  function gewaehlt() {
    return document.querySelector('input[name="art"]:checked');
  }

  function agentZeigen() {
    if (!laeuftAn) return;
    var a = gewaehlt();
    var agent = a ? a.getAttribute("data-agent") : "";
    laeuftAn.textContent = agent ? "Läuft an: " + agent : "";
  }

  /* ------------------------------------------------------------ Die Länge
   *
   * Bereich, Schritt und Voreinstellung stehen am gewählten Knopf — sie
   * kommen aus universe/auftragsarten.json und werden hier nur angezeigt.
   * Der Regler geht nicht über den Bereich hinaus: die Grenzen sind hart.
   */
  var block = document.getElementById("laenge-block");
  var regler = document.getElementById("auftrag-laenge");
  var wertFeld = document.getElementById("laenge-wert");
  var frageFeld = document.getElementById("laenge-frage");
  var vonFeld = document.getElementById("laenge-von");
  var bisFeld = document.getElementById("laenge-bis");
  var satzFeld = document.getElementById("laenge-satz");
  var preisFeld = document.getElementById("laenge-preis");

  /* Dieselbe Zahl wie in universe/kern/laenge.py: eine Szene ist vier
     Sekunden lang, und jede braucht ein Endbild. Der Preis je Endbild steht
     am Block und kommt aus kosten.json. */
  var SZENE_SEKUNDEN = 4;

  function lesbar(sekunden, einheit) {
    if (einheit === "sekunden" || sekunden < 60) {
      return Math.round(sekunden) + " Sekunden";
    }
    var minuten = sekunden / 60;
    if (Math.abs(minuten - Math.round(minuten)) < 0.01) {
      return Math.round(minuten) === 1 ? "1 Minute" : Math.round(minuten) + " Minuten";
    }
    var m = Math.floor(minuten);
    var s = Math.round((minuten - m) * 60);
    return m + ":" + (s < 10 ? "0" : "") + s + " Minuten";
  }

  function reglerZeigen() {
    if (!block || !regler) return;
    var a = gewaehlt();
    var roh = a ? a.getAttribute("data-regler") : "";
    if (!roh) {
      block.hidden = true;
      return;
    }
    var r;
    try { r = JSON.parse(roh); } catch (e) { block.hidden = true; return; }

    block.hidden = false;
    regler.min = r.von;
    regler.max = r.bis;
    regler.step = r.schritt;
    regler.value = r.voreinstellung;
    if (frageFeld) {
      frageFeld.textContent =
        r.art === "vortragsdauer" ? "Wie lange soll der Vortrag dauern?" : "Wie lang?";
    }
    if (vonFeld) vonFeld.textContent = lesbar(r.von, r.einheit);
    if (bisFeld) bisFeld.textContent = lesbar(r.bis, r.einheit);
    if (satzFeld) satzFeld.textContent = r.was || "";
    wertZeigen();
  }

  function wertZeigen() {
    if (!regler || block.hidden) return;
    var a = gewaehlt();
    var r = JSON.parse(a.getAttribute("data-regler"));
    var sekunden = Number(regler.value);
    if (wertFeld) wertFeld.textContent = lesbar(sekunden, r.einheit);

    if (!preisFeld) return;
    if (!r.kosten_sichtbar) {
      preisFeld.hidden = true;
      return;
    }
    var jeBild = Number(block.getAttribute("data-endbild-eur") || 0);
    var szenen = Math.max(1, Math.round(sekunden / SZENE_SEKUNDEN));
    var betrag = szenen * jeBild;
    preisFeld.hidden = false;
    preisFeld.textContent =
      "Geschätzt " + betrag.toFixed(2).replace(".", ",") + " € — " + szenen +
      " Szenen zu je einem Endbild (" + jeBild.toFixed(4).replace(".", ",") +
      " €). Der Modellaufruf für das Drehbuch kommt dazu.";
  }

  if (regler) regler.addEventListener("input", wertZeigen);

  function sage(text) {
    if (!hinweis) return;
    hinweis.textContent = text;
    hinweis.hidden = !text;
  }

  Array.prototype.forEach.call(
    document.querySelectorAll('input[name="art"]'),
    function (r) {
      r.addEventListener("change", agentZeigen);
      r.addEventListener("change", reglerZeigen);
    }
  );
  agentZeigen();
  reglerZeigen();

  if (leeren) {
    leeren.addEventListener("click", function () {
      feld.value = "";
      sage("");
      feld.focus();
    });
  }

  /* ---- Der Fortschritt eines abgeschickten Auftrags ------------------
     Zwei Quellen, beide vom Hub: der Zustand des Auftrags (gesendet,
     angenommen, laeuft, pruefung, vorlage, fertig) gibt den Rahmen; die
     Stationen, die die Werkstatt unterwegs meldet (Drehbuch, Sprecher,
     Bildmaterial, Schnitt ...), ruecken den Balken innerhalb von "laeuft"
     weiter. Wie viele Stationen eine Werkstatt hat, weiss diese Seite nicht -
     der Balken ist darum ungefaehr, aber er bewegt sich, wenn wirklich etwas
     passiert. Daniel: "muss nicht absolut perfekt sein, aber live". */
  var lauf = document.getElementById("auftrag-lauf");
  var laufStation = document.getElementById("lauf-station");
  var laufProzent = document.getElementById("lauf-prozent");
  var laufFuellung = document.getElementById("lauf-fuellung");
  var laufStationen = document.getElementById("lauf-stationen");
  var laufUhr = null;

  var RAHMEN = { gesendet: 0.05, kostenfreigabe: 0.1, rueckfrage: 0.1, angenommen: 0.15,
                 laeuft: 0.2, pruefung: 0.85, vorlage: 0.95, fertig: 1, fehler: 1, abgebrochen: 1 };

  /* ---- Die Rueckfrage des Sekretaers ------------------------------------
     Zustand "rueckfrage" beim Hub: der Sekretaer hat den Auftrag nicht
     verstanden und hat seine Fragen als Meldung (art "rueckfrage") ins Fach
     gelegt. Die Antwort geht als Entscheidung "ja" mit Text zurueck, das
     Zurueckziehen als "nein" mit Satz - derselbe Weg wie jede Freigabe. */
  var rueckfrage = document.getElementById("rueckfrage");
  var rueckfrageText = document.getElementById("rueckfrage-text");
  var rueckfrageAntwort = document.getElementById("rueckfrage-antwort");
  var rueckfrageSenden = document.getElementById("rueckfrage-senden");
  var rueckfrageZurueck = document.getElementById("rueckfrage-zurueck");
  var rueckfrageHinweis = document.getElementById("rueckfrage-hinweis");
  var rueckfrageMeldung = null;

  function rueckfrageZeigen(meldung) {
    if (!rueckfrage) return;
    rueckfrageMeldung = meldung || null;
    rueckfrage.hidden = !meldung;
    if (meldung && rueckfrageText) rueckfrageText.textContent = meldung.text || meldung.zusammenfassung || "";
  }

  function entscheiden(wahl, grund) {
    if (!rueckfrageMeldung) return;
    rueckfrageSenden.disabled = true;
    fetch("/api/hub/entscheidung", {
      method: "POST", headers: kopf(),
      body: JSON.stringify({ meldung: rueckfrageMeldung.id, wahl: wahl, grund: grund }),
    })
      .then(function (a) { return a.json().then(function (d) { return { code: a.status, d: d }; }); })
      .then(function (r) {
        if (r.d && r.d.angenommen) {
          rueckfrageAntwort.value = "";
          rueckfrageZeigen(null);
          zeigeLauf(0.12, wahl === "ja" ? "Antwort unterwegs zum Sekret\u00e4r" : "zur\u00fcckgezogen");
          return;
        }
        if (rueckfrageHinweis) {
          rueckfrageHinweis.textContent = (r.d && r.d.fehler) || "Das hat nicht geklappt.";
          rueckfrageHinweis.hidden = false;
        }
      })
      .catch(function () {
        if (rueckfrageHinweis) {
          rueckfrageHinweis.textContent = "Die Verbindung kam nicht zustande - versuch es gleich noch einmal.";
          rueckfrageHinweis.hidden = false;
        }
      })
      .then(function () { rueckfrageSenden.disabled = false; });
  }

  if (rueckfrageSenden) {
    rueckfrageSenden.addEventListener("click", function () {
      var antwort = (rueckfrageAntwort.value || "").trim();
      if (!antwort) {
        rueckfrageHinweis.textContent = "Schreib zuerst deine Antwort.";
        rueckfrageHinweis.hidden = false;
        return;
      }
      entscheiden("ja", antwort);
    });
  }
  if (rueckfrageZurueck) {
    rueckfrageZurueck.addEventListener("click", function () {
      entscheiden("nein", "Auf die R\u00fcckfrage hin zur\u00fcckgezogen");
    });
  }
  var STATIONEN_ETWA = 6;

  function verfolgen(id) {
    if (!lauf) return;
    lauf.hidden = false;
    lauf.removeAttribute("data-zustand");
    laufStationen.innerHTML = "";
    zeigeLauf(0.02, "an den Hub \u00fcbergeben");
    if (laufUhr) clearInterval(laufUhr);
    var vorgang = id.replace(/:/g, "-");
    function tick() {
      Promise.all([
        fetch("/api/hub/auftraege", { headers: kopf() }).then(function (r) { return r.ok ? r.json() : {}; }),
        fetch("/api/hub/meldungen?anzahl=150", { headers: kopf() }).then(function (r) { return r.ok ? r.json() : {}; }),
      ]).then(function (beide) {
        var auftrag = ((beide[0] && beide[0].auftraege) || []).filter(function (x) { return x.id === id; })[0];
        var alleMeldungen = (beide[1] && beide[1].meldungen) || [];
        var schritte = alleMeldungen.filter(function (m) {
          return m.vorgang === vorgang && m.art === "schritt" && m.daten;
        }).reverse();
        /* Der Sekretaer schreibt die Kennung roh in den Vorgang, die Werkstaetten
           bereinigt - beide Formen gelten. */
        var frage = alleMeldungen.filter(function (m) {
          return m.art === "rueckfrage" && !m.entscheidung &&
            (m.vorgang === id || m.vorgang === vorgang);
        })[0];
        var stationen = [];
        var laufende = null;
        schritte.forEach(function (m) {
          var name = m.daten.schritt || m.zusammenfassung || "";
          if (!name) return;
          if (m.daten.zustand === "fertig") {
            if (stationen.indexOf(name) < 0) stationen.push(name);
            if (laufende === name) laufende = null;
          } else {
            laufende = name;
          }
        });
        var zustand = auftrag ? auftrag.zustand : "gesendet";
        var wert = RAHMEN[zustand] !== undefined ? RAHMEN[zustand] : 0.05;
        if (zustand === "laeuft") {
          wert = 0.2 + 0.6 * Math.min(1, (stationen.length + (laufende ? 0.5 : 0)) / STATIONEN_ETWA);
        }
        var text = laufende ? laufende + " l\u00e4uft \u2026"
          : stationen.length ? stationen[stationen.length - 1] + " fertig"
          : (auftrag && auftrag.rueckmeldung) || zustand;
        if (zustand === "fertig") text = (auftrag && auftrag.rueckmeldung) || "fertig";
        if (zustand === "rueckfrage") {
          text = "R\u00fcckfrage an dich - bitte unten antworten";
          rueckfrageZeigen(frage || null);
        } else {
          rueckfrageZeigen(null);
        }
        if (zustand === "fehler" || zustand === "abgebrochen") {
          lauf.setAttribute("data-zustand", "fehler");
          text = (auftrag && auftrag.rueckmeldung) || zustand;
        }
        zeigeLauf(wert, text);
        laufStationen.innerHTML = "";
        stationen.forEach(function (s) {
          var li = document.createElement("li"); li.textContent = s; laufStationen.appendChild(li);
        });
        if (laufende) {
          var li = document.createElement("li"); li.className = "laeuft"; li.textContent = laufende;
          laufStationen.appendChild(li);
        }
        if (zustand === "fertig" || zustand === "fehler" || zustand === "abgebrochen") {
          clearInterval(laufUhr); laufUhr = null;
        }
      }).catch(function () { /* naechster Tick */ });
    }
    tick();
    laufUhr = setInterval(tick, 5000);
  }

  function zeigeLauf(wert, text) {
    var p = Math.max(0, Math.min(100, Math.round(wert * 100)));
    laufFuellung.style.width = p + "%";
    laufProzent.textContent = p + " %";
    laufStation.textContent = text;
  }

  senden.addEventListener("click", function () {
    var text = (feld.value || "").trim();
    if (!text) {
      sage("Schreib oder sprich zuerst, was gebaut werden soll.");
      feld.focus();
      return;
    }
    var art = gewaehlt();
    if (!art) {
      sage("Wähl zuerst aus, worum es geht.");
      return;
    }

    var alt = senden.textContent;
    senden.disabled = true;
    senden.textContent = "Geht raus …";
    sage("");

    fetch("/api/hub/auftrag", {
      method: "POST",
      /* Mit Ausweis, wenn einer da ist - sonst weist der Hub ab. */
      headers: kopf(),
      body: JSON.stringify({
        art: art.value,
        text: text,
        trocken: true,
        /* Die bestellte Länge geht mit. Der Sekretär prüft sie gegen den
           Bereich und sagt ab, wenn sie nicht passt — er biegt nichts
           zurecht. */
        laenge_sek: block && !block.hidden ? Number(regler.value) : null,
      }),
    })
      .then(function (a) {
        return a.json().then(function (d) { return { code: a.status, d: d }; });
      })
      .then(function (r) {
        if (r.code === 401 || r.code === 403) {
          sage("Aufträge nimmt der Hub nur von angemeldeten Ausweisen an. " +
               "Melde dich unter Zugang an, dann geht es weiter.");
          return;
        }
        if (r.d && r.d.angenommen) {
          sage("");
          feld.value = "";
          if (r.d.auftrag && r.d.auftrag.id) verfolgen(r.d.auftrag.id);
          return;
        }
        sage((r.d && r.d.fehler) || "Das hat nicht geklappt.");
      })
      .catch(function () {
        sage("Die Verbindung kam nicht zustande. Dein Text steht noch da — " +
             "versuch es gleich noch einmal.");
      })
      .then(function () {
        senden.disabled = false;
        senden.textContent = alt;
      });
  });
})();
