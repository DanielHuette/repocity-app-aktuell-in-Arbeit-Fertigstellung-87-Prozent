/* Die Schalter der Einstellungsseite. Dieselbe Regel wie in der App:
   ein ausgeschaltetes Elternteil nimmt seine Kinder mit, und stumm kann
   nur sein, was ueberhaupt laeuft.

   Gemerkt wird im Browser. Die App fuehrt vorerst ihre eigenen Schalter --
   zusammengefuehrt werden beide, sobald die App am Hub haengt. */

(function () {
  "use strict";

  function lies(schluessel, standard) {
    try {
      var w = localStorage.getItem(schluessel);
      return w === null ? standard : w === "an";
    } catch (e) { return standard; }
  }
  function schreib(schluessel, an) {
    try { localStorage.setItem(schluessel, an ? "an" : "aus"); } catch (e) {}
  }

  /* ---- Betrieb und Startbildschirm ------------------------------- */
  var einfache = Array.prototype.slice.call(
    document.querySelectorAll("[data-schalter]"));
  var echtZeile = document.querySelector('[data-zeile="echt"]');

  function zeigeEcht(an) {
    if (echtZeile) {
      echtZeile.textContent = an
        ? "Auftraege werden wirklich ausgefuehrt"
        : "trocken: nichts verlaesst das Haus";
    }
  }

  einfache.forEach(function (s) {
    var name = s.getAttribute("data-schalter");
    var standard = name === "startbildschirm";
    s.checked = lies("rc_" + name, standard);
    if (name === "echtbetrieb") zeigeEcht(s.checked);
    s.addEventListener("change", function () {
      schreib("rc_" + name, s.checked);
      if (name === "echtbetrieb") zeigeEcht(s.checked);
    });
  });

  /* ---- Die Teile des Universe ------------------------------------ */
  var betrieb = Array.prototype.slice.call(document.querySelectorAll("[data-betrieb]"));
  var meldung = Array.prototype.slice.call(document.querySelectorAll("[data-meldung]"));
  if (!betrieb.length) return;

  function betriebEigen(id) { return lies("rc_betrieb_" + id, true); }
  function meldungEigen(id) { return lies("rc_meldung_" + id, true); }

  /* Wirksam ist ein Teil nur, wenn auch sein Elternteil laeuft. */
  function wirksam(feld) {
    var id = feld.getAttribute("data-betrieb") || feld.getAttribute("data-meldung");
    var eltern = feld.getAttribute("data-eltern");
    return betriebEigen(id) && (!eltern || betriebEigen(eltern));
  }

  function zeichne() {
    betrieb.forEach(function (f) {
      var eltern = f.getAttribute("data-eltern");
      var elternAn = !eltern || betriebEigen(eltern);
      f.checked = betriebEigen(f.getAttribute("data-betrieb"));
      f.disabled = !elternAn;
    });
    meldung.forEach(function (f) {
      var an = wirksam(f);
      f.checked = meldungEigen(f.getAttribute("data-meldung"));
      f.disabled = !an;
    });
    Array.prototype.slice.call(document.querySelectorAll("[data-modul]"))
      .forEach(function (zeile) {
        var feld = zeile.querySelector("[data-betrieb]");
        zeile.setAttribute("data-aus", feld && wirksam(feld) ? "nein" : "ja");
        var text = zeile.querySelector("[data-aufgabe]");
        if (!text || !feld) return;
        var eltern = feld.getAttribute("data-eltern");
        text.textContent = (eltern && !betriebEigen(eltern))
          ? "durch uebergeordneten Teil aus"
          : text.getAttribute("data-aufgabe");
      });
  }

  betrieb.forEach(function (f) {
    f.addEventListener("change", function () {
      schreib("rc_betrieb_" + f.getAttribute("data-betrieb"), f.checked);
      zeichne();
    });
  });
  meldung.forEach(function (f) {
    f.addEventListener("change", function () {
      schreib("rc_meldung_" + f.getAttribute("data-meldung"), f.checked);
      zeichne();
    });
  });

  zeichne();
})();
