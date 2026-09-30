/* Die Klappen der Kopfleiste.
 *
 * Warum Skript und nicht nur CSS: auf dem Handy gibt es kein Zeigen. Ein
 * Menü, das sich nur mit der Maus öffnet, ist dort kein Menü. Also geht
 * jede Klappe auf Zeigen UND auf Antippen auf.
 *
 * Es ist immer höchstens eine Klappe offen — zwei übereinander liegende
 * Listen kann niemand lesen.
 */
(function () {
  "use strict";

  var leiste = document.querySelector(".kopfleiste");
  if (!leiste) return;

  var knopf = leiste.querySelector("[data-menue-knopf]");
  var menue = leiste.querySelector("[data-menue]");
  var klappen = Array.prototype.slice.call(leiste.querySelectorAll("[data-klappe]"));

  function schmal() {
    return window.matchMedia("(max-width: 1180px)").matches;
  }

  function zu(ausser) {
    klappen.forEach(function (k) {
      if (k === ausser) return;
      k.removeAttribute("data-offen");
      var b = k.querySelector(".klappe-knopf");
      if (b) b.setAttribute("aria-expanded", "false");
    });
  }

  function umlegen(k, an) {
    if (an) k.setAttribute("data-offen", "ja");
    else k.removeAttribute("data-offen");
    var b = k.querySelector(".klappe-knopf");
    if (b) b.setAttribute("aria-expanded", an ? "true" : "false");
  }

  klappen.forEach(function (k) {
    var b = k.querySelector(".klappe-knopf");
    if (!b) return;

    b.addEventListener("click", function (e) {
      e.preventDefault();
      var offen = k.hasAttribute("data-offen");
      zu(k);
      umlegen(k, !offen);
    });

    /* Zeigen gilt nur auf breiten Geräten - sonst springt die Klappe beim
       Scrollen mit dem Finger auf. */
    k.addEventListener("mouseenter", function () {
      if (schmal()) return;
      zu(k);
      umlegen(k, true);
    });
    k.addEventListener("mouseleave", function () {
      if (schmal()) return;
      umlegen(k, false);
    });
  });

  if (knopf && menue) {
    knopf.addEventListener("click", function () {
      var offen = menue.hasAttribute("data-offen");
      if (offen) {
        menue.removeAttribute("data-offen");
        zu(null);
      } else {
        menue.setAttribute("data-offen", "ja");
      }
      knopf.setAttribute("aria-expanded", offen ? "false" : "true");
    });
  }

  /* Ein Klick daneben schließt alles. Sonst bleibt eine Klappe offen
     stehen, während man längst woanders liest. */
  document.addEventListener("click", function (e) {
    if (leiste.contains(e.target)) return;
    zu(null);
    if (menue) menue.removeAttribute("data-offen");
    if (knopf) knopf.setAttribute("aria-expanded", "false");
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    zu(null);
    if (menue) menue.removeAttribute("data-offen");
    if (knopf) knopf.setAttribute("aria-expanded", "false");
  });
})();
