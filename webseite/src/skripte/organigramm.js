/* Die Organigramm-Teile nehmen das eingestellte Design an. Beim Bauen steckt
   schon das Standard-Design in den Bildern; hier werden sie getauscht, sobald
   ein anderes gewaehlt ist — und bei jedem weiteren Wechsel.

   Seit dem 14.09.2026 sind es vier Bilder statt eines. Sie werden gemeinsam
   gefuellt, weil sie dasselbe Design tragen.

   Die Werte kommen aus derselben Stelle wie alles andere auf der Seite: den
   Design-Werten am Wurzelelement. Es gibt keinen zweiten Farbsatz. */

import { fuelle, benoetigteWerte } from "./organigramm-fuellen.js";

(function () {
  "use strict";

  const wurzel = document.documentElement;
  const bilder = [...document.querySelectorAll("[data-organigramm]")];
  if (!bilder.length) return;

  const teile = bilder
    .map((rahmen) => {
      const id = rahmen.getAttribute("data-organigramm");
      const quelle = document.querySelector(
        '[data-organigramm-rohling="' + id + '"]');
      if (!quelle) return null;
      const rohling = quelle.textContent;
      return { rahmen, rohling, namen: benoetigteWerte(rohling) };
    })
    .filter(Boolean);

  // Beim Laden steht das Design schon fest; nur wenn es nicht das ist, das
  // beim Bauen eingesetzt wurde, muss neu gezeichnet werden.
  let zuletzt = bilder[0].getAttribute("data-gebaut-mit");

  function zeichne() {
    const kit = wurzel.getAttribute("data-kit") || "blende";
    if (kit === zuletzt) return;
    zuletzt = kit;
    const stil = getComputedStyle(wurzel);
    for (const teil of teile) {
      const werte = {};
      for (const name of teil.namen) {
        werte[name] = stil.getPropertyValue("--" + name).trim();
      }
      teil.rahmen.innerHTML = fuelle(teil.rohling, werte);
    }
  }

  zeichne();

  new MutationObserver(zeichne).observe(wurzel, {
    attributes: true,
    attributeFilter: ["data-kit"],
  });
})();
