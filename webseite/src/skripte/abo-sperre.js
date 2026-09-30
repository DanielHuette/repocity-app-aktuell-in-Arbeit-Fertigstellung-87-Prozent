/* Zeigt an, welche Bereiche mit der gebuchten Stufe offen sind und welche
   nicht. Gesperrte Bereiche werden NICHT versteckt — sie bleiben sichtbar und
   bekommen ein Schloss und den Namen der Stufe, die sie aufmacht.
 *
 * Das hier ist nur die Anzeige. Die Sperre selbst steht im Worker
 * (worker/index.js): wer die Adresse direkt eintippt, bekommt die Seite gar
 * nicht erst geliefert. Was hier passiert, kann jeder im Browser abschalten —
 * darum darf sich nichts darauf verlassen.
 *
 * Welcher Bereich welche Stufe braucht, steht in src/daten/bereiche.ts; die
 * Seite reicht es als data-stufe an jedem Punkt herein. Die Reihenfolge der
 * Stufen kommt aus src/daten/abo.ts und steht als JSON in der Seite.
 */

import { kopf } from "./ausweis.js";

(function () {
  "use strict";

  var kasten = document.getElementById("stufen-raenge");
  if (!kasten) return;

  var raenge = {};
  var unten = "free";
  var namen = {};
  try {
    var gelesen = JSON.parse(kasten.textContent || "{}");
    raenge = gelesen.raenge || {};
    namen = gelesen.namen || {};
    unten = gelesen.unten || "free";
  } catch (e) {
    return;
  }

  function rang(schluessel) {
    /* Alles Unbekannte zaehlt als unterste Stufe — nie als hoechste. */
    return Object.prototype.hasOwnProperty.call(raenge, schluessel)
      ? raenge[schluessel]
      : raenge[unten];
  }

  function zeichnen(gebucht) {
    var punkte = document.querySelectorAll("[data-stufe]");
    Array.prototype.forEach.call(punkte, function (p) {
      var braucht = p.getAttribute("data-stufe");
      var zu = rang(gebucht) < rang(braucht);
      if (zu) {
        p.setAttribute("data-gesperrt", "ja");
        p.setAttribute("data-stufe-name", namen[braucht] || braucht);
      } else {
        p.removeAttribute("data-gesperrt");
        p.removeAttribute("data-stufe-name");
      }
    });
  }

  /* Solange nichts feststeht, gilt die unterste Stufe. Damit ist die Seite
     schon vor der Antwort richtig gezeichnet, und wenn keine Antwort kommt,
     bleibt es dabei. Ein Fehler schliesst nichts auf. */
  zeichnen(unten);

  /* Mit dem Ausweis des Angemeldeten - sonst sieht der Hub einen Gast und
     antwortet "free", und ein Admin bekaeme Schloesser gezeigt, durch die
     ihn das Tor laengst laesst. Bis zum 10.09. war genau das der Fall. */
  fetch("/api/abo/stand", { headers: kopf({ accept: "application/json" }) })
    .then(function (a) {
      if (!a.ok) throw new Error("keine Auskunft");
      return a.json();
    })
    .then(function (d) {
      zeichnen(d && d.stufe ? d.stufe : unten);
    })
    .catch(function () {
      zeichnen(unten);
    });
})();
