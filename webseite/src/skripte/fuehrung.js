/* Mias Fuehrung durch die Oberflaeche.
 *
 * Dieselben Texte wie in der App: sie stehen in universe/fuehrung.json und
 * werden beim Bauen in die Seite gelegt (App.astro, Kasten "fuehrung").
 * Kein Satz steht zweimal.
 *
 * Der Unterschied zur App: hier ist jeder Halt eine eigene Seite. Die
 * Fuehrung ueberlebt den Seitenwechsel, indem sie ihren Stand in den
 * Sitzungsspeicher legt und beim Laden wieder aufnimmt. "Gesehen" steht
 * dagegen dauerhaft im Speicher des Browsers - sonst ginge sie bei jedem
 * neuen Tab wieder auf.
 *
 * Wie in der App laeuft sie UEBER den echten Seiten. Wer sie wegschickt,
 * bekommt sie nicht wieder vorgesetzt; aufrufen kann er sie im
 * Fragefenster jederzeit.
 */

(function () {
  "use strict";

  var kasten = document.getElementById("fuehrung");
  if (!kasten) return;

  var t;
  try {
    t = JSON.parse(kasten.textContent || "{}");
  } catch (e) {
    return;
  }
  if (!t || !t.halte || !t.halte.length) return;

  var GESEHEN = "repocity.fuehrung.gesehen";
  var STAND = "repocity.fuehrung.bei";

  /* Der Speicher kann fehlen - privates Fenster, abgestellte Daten. Dann
     laeuft die Fuehrung eben nicht von selbst; sie darf nicht abstuerzen. */
  function lies(speicher, name) {
    try {
      return speicher.getItem(name);
    } catch (e) {
      return null;
    }
  }
  function schreib(speicher, name, wert) {
    try {
      speicher.setItem(name, wert);
    } catch (e) {
      /* nichts - ohne Speicher keine Erinnerung, aber auch kein Fehler */
    }
  }

  /* ── Welche Halte diese Stufe sieht ─────────────────────────────── */
  var raenge = {};
  var unten = "free";
  try {
    var r = JSON.parse(
      (document.getElementById("stufen-raenge") || {}).textContent || "{}",
    );
    raenge = r.raenge || {};
    unten = r.unten || "free";
  } catch (e) {
    /* ohne Raenge gilt unten */
  }
  function rang(s) {
    return Object.prototype.hasOwnProperty.call(raenge, s)
      ? raenge[s]
      : raenge[unten] || 0;
  }

  var meine = unten;
  function halte() {
    return t.halte.filter(function (h) {
      return rang(h.stufe) <= rang(meine);
    });
  }

  /* ── Wo stehen wir? ─────────────────────────────────────────────── */
  function bei() {
    var v = lies(sessionStorage, STAND);
    return v === null ? null : parseInt(v, 10);
  }
  function setzeBei(i) {
    schreib(sessionStorage, STAND, String(i));
  }
  function beenden() {
    try {
      sessionStorage.removeItem(STAND);
    } catch (e) {
      /* nichts */
    }
    schreib(localStorage, GESEHEN, "ja");
    zeichnen();
  }

  function wegZu(route) {
    return "/app/" + route + "/";
  }

  /* Auf welcher Seite sind wir gerade? */
  function hierRoute() {
    var m = window.location.pathname.match(/\/app\/([a-z]+)\/?$/);
    return m ? m[1] : "";
  }

  function gehZu(i) {
    var liste = halte();
    setzeBei(i);
    var ziel;
    if (i < 0 || i >= liste.length) {
      ziel = "/app/";
    } else {
      ziel = wegZu(liste[i].route);
    }
    if (window.location.pathname !== ziel) {
      window.location.href = ziel;
    } else {
      zeichnen();
    }
  }

  /* ── Die Sprechblase ────────────────────────────────────────────── */
  var aufsatz = null;

  function raeumen() {
    if (aufsatz && aufsatz.parentNode) aufsatz.parentNode.removeChild(aufsatz);
    aufsatz = null;
  }

  function knopf(text, wieHervor, tun) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "fuehrung-knopf" + (wieHervor ? " ist-hervor" : "");
    b.textContent = text;
    b.addEventListener("click", tun);
    return b;
  }

  function absatz(text, klasse) {
    var p = document.createElement("p");
    if (klasse) p.className = klasse;
    p.textContent = text;
    return p;
  }

  function zeichnen() {
    raeumen();
    var i = bei();
    if (i === null) return;
    var liste = halte();

    aufsatz = document.createElement("div");
    aufsatz.className = "fuehrung-grund";
    aufsatz.setAttribute("role", "dialog");
    aufsatz.setAttribute("aria-label", "Führung durch RepoCity");

    var blase = document.createElement("section");
    blase.className = "fuehrung-blase";
    aufsatz.appendChild(blase);

    var reihe = document.createElement("div");
    reihe.className = "fuehrung-knoepfe";

    if (i < 0) {
      blase.appendChild(absatz(t.name, "fuehrung-marke"));
      blase.appendChild(absatz(t.eroeffnung.gruss, "fuehrung-gross"));
      if (t.eroeffnung.hinweis) {
        blase.appendChild(absatz(t.eroeffnung.hinweis, "fuehrung-leise"));
      }
      reihe.appendChild(
        knopf(t.eroeffnung.weiter, true, function () {
          gehZu(0);
        }),
      );
      reihe.appendChild(knopf(t.eroeffnung.abbruch, false, beenden));
    } else if (i >= liste.length) {
      blase.appendChild(absatz(t.name, "fuehrung-marke"));
      blase.appendChild(absatz(t.abschluss.text, "fuehrung-gross"));
      reihe.appendChild(knopf(t.abschluss.weiter, true, beenden));
    } else {
      var h = liste[i];

      /* Steht die Seite nicht zum Halt, ist der Nutzer selbst woanders
         hingegangen. Dann wird nicht heimlich zurueckgesprungen - die
         Blase sagt es und bietet den Weg an. */
      if (hierRoute() && hierRoute() !== h.route) {
        blase.appendChild(absatz(h.titel, "fuehrung-marke"));
        blase.appendChild(
          absatz(
            "Der nächste Halt liegt auf einer anderen Seite.",
            "fuehrung-gross",
          ),
        );
        reihe.appendChild(
          knopf("Dorthin", true, function () {
            gehZu(i);
          }),
        );
        reihe.appendChild(knopf("Später", false, beenden));
        blase.appendChild(reihe);
        document.body.appendChild(aufsatz);
        return;
      }

      var kopf = document.createElement("div");
      kopf.className = "fuehrung-kopf";
      kopf.appendChild(absatz(h.titel, "fuehrung-marke"));
      kopf.appendChild(absatz(i + 1 + " von " + liste.length, "fuehrung-zahl"));
      blase.appendChild(kopf);

      blase.appendChild(absatz(h.kurz, "fuehrung-gross"));

      if (h.einstellen && h.einstellen.length) {
        blase.appendChild(absatz("Was du hier einstellst", "fuehrung-marke"));
        var ul = document.createElement("ul");
        ul.className = "fuehrung-liste";
        h.einstellen.forEach(function (z) {
          var li = document.createElement("li");
          li.textContent = z;
          ul.appendChild(li);
        });
        blase.appendChild(ul);
      }

      var mehrOffen = false;
      var mehrKasten = document.createElement("div");
      mehrKasten.hidden = true;
      if (h.warum) {
        mehrKasten.appendChild(absatz("Warum", "fuehrung-marke"));
        mehrKasten.appendChild(absatz(h.warum, "fuehrung-leise"));
      }
      if (h.mehr) mehrKasten.appendChild(absatz(h.mehr, "fuehrung-leise"));
      blase.appendChild(mehrKasten);

      reihe.appendChild(
        knopf("Weiter", true, function () {
          gehZu(i + 1);
        }),
      );
      if (i > 0) {
        reihe.appendChild(
          knopf("Zurück", false, function () {
            gehZu(i - 1);
          }),
        );
      }
      if (h.warum || h.mehr) {
        var mehrKnopf = knopf("Mehr dazu", false, function () {
          mehrOffen = !mehrOffen;
          mehrKasten.hidden = !mehrOffen;
          mehrKnopf.textContent = mehrOffen ? "Weniger" : "Mehr dazu";
        });
        reihe.appendChild(mehrKnopf);
      }
      reihe.appendChild(knopf("Später", false, beenden));
    }

    blase.appendChild(reihe);
    document.body.appendChild(aufsatz);
  }

  /* ── Anfangen ───────────────────────────────────────────────────── */
  function anfangen(vonHand) {
    if (!vonHand && lies(localStorage, GESEHEN) === "ja") return;
    /* Von selbst geht sie nur in der Oberflaeche auf. Auf der oeffentlichen
       Seite waere sie eine Fuehrung durch etwas, das der Besucher noch gar
       nicht benutzt. */
    if (!vonHand && window.location.pathname.indexOf("/app/") !== 0) return;
    if (bei() === null) setzeBei(-1);
    zeichnen();
  }

  /* Der Knopf im Fragefenster - dort und nur dort steht sie danach
     bereit. Sie draengt sich nicht auf. */
  var starter = document.getElementById("fuehrung-start");
  if (starter) {
    starter.addEventListener("click", function () {
      window.repocityFuehrung();
    });
  }

  /* Von aussen aufrufbar: der Knopf im Fragefenster. */
  window.repocityFuehrung = function () {
    setzeBei(-1);
    if (window.location.pathname !== "/app/") {
      window.location.href = "/app/";
    } else {
      zeichnen();
    }
  };

  /* Die Stufe entscheidet, welche Halte ueberhaupt vorkommen. Bis die
     Auskunft da ist, gilt die unterste - wie ueberall sonst auch. */
  function los() {
    if (bei() !== null) zeichnen();
    else anfangen(false);
  }

  los();
  fetch("/api/abo/stand", { headers: { accept: "application/json" } })
    .then(function (a) {
      if (!a.ok) throw new Error("keine Auskunft");
      return a.json();
    })
    .then(function (d) {
      if (d && d.stufe && d.stufe !== meine) {
        meine = d.stufe;
        if (bei() !== null) zeichnen();
      }
    })
    .catch(function () {
      /* ohne Auskunft bleibt es bei der untersten Stufe */
    });
})();
