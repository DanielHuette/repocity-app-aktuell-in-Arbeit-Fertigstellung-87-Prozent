/* Der zweite Faktor auf der Zugangsseite.

   Das Geheimnis wird hier nur angezeigt, nie gespeichert: weder im
   Browser noch sonstwo. Wer das Fenster schliesst, ohne den Eintrag
   angelegt zu haben, faengt von vorn an - das ist gewollt. */

(function () {
  "use strict";

  var block = document.getElementById("zweifaktor");
  if (!block) return;

  var stand = document.getElementById("zf-stand");
  var knopf = document.getElementById("zf-einrichten");
  var kasten = document.getElementById("zf-kasten");
  var geheimnis = document.getElementById("zf-geheimnis");
  var bild = document.getElementById("zf-qr");
  var eingabe = document.getElementById("zf-code");
  var bestaetigen = document.getElementById("zf-bestaetigen");
  var meldung = document.getElementById("zf-meldung");
  var codesKasten = document.getElementById("zf-codes");
  var codesListe = document.getElementById("zf-codes-liste");
  var whFeld = document.getElementById("zf-wh");
  var whKnopf = document.getElementById("zf-wh-knopf");

  function sagen(text, schlimm) {
    meldung.textContent = text;
    meldung.setAttribute("data-schlimm", schlimm ? "ja" : "nein");
  }

  function rufen(weg, daten) {
    return fetch("/api/2fa" + weg, {
      method: daten ? "POST" : "GET",
      headers: daten ? { "content-type": "application/json" } : {},
      body: daten ? JSON.stringify(daten) : undefined,
    }).then(function (a) {
      return a.json().then(function (s) { return { stand: a.status, satz: s }; });
    });
  }

  function zeigen() {
    rufen("/stand").then(function (a) {
      if (a.stand === 401) {
        stand.textContent = "Nicht angemeldet. Der zweite Faktor kommt nach "
          + "dem ersten.";
        knopf.hidden = true;
        return;
      }
      var s = a.satz;
      if (s.bestaetigt) {
        stand.textContent = "Eingerichtet und bestaetigt"
          + (s.seit ? " am " + s.seit.slice(0, 10) : "") + ". "
          + (s.scharf ? "Er wird verlangt." : "Er wird noch nicht verlangt.");
        knopf.hidden = true;
      } else if (s.eingerichtet) {
        stand.textContent = "Angelegt, aber nicht bestaetigt. Solange gilt er "
          + "nicht.";
        kasten.hidden = false;
        knopf.hidden = true;
      } else {
        stand.textContent = s.hinweis || "Noch nicht eingerichtet.";
        knopf.hidden = false;
      }
    }).catch(function () {
      stand.textContent = "Der Hub antwortet nicht.";
    });
  }

  knopf.addEventListener("click", function () {
    knopf.disabled = true;
    rufen("/einrichten", {}).then(function (a) {
      if (a.satz && a.satz.wiederherstellungscodes && codesListe) {
        codesListe.textContent = a.satz.wiederherstellungscodes.join("\n");
        codesKasten.hidden = false;
      }
      knopf.disabled = false;
      if (a.stand !== 200) { sagen(a.satz.fehler || "ging nicht", true); return; }
      geheimnis.textContent = a.satz.geheimnis;
      /* Das Bild kommt fertig gerechnet vom Hub. Es wird nicht
         gespeichert - wer die Seite neu laedt, faengt von vorn an. */
      if (bild && a.satz.qr) bild.innerHTML = a.satz.qr;
      kasten.hidden = false;
      knopf.hidden = true;
      sagen(a.satz.hinweis, false);
    });
  });

  bestaetigen.addEventListener("click", function () {
    rufen("/bestaetigen", { code: eingabe.value }).then(function (a) {
      if (a.stand !== 200) { sagen(a.satz.fehler || "ging nicht", true); return; }
      sagen("Bestaetigt. Ab jetzt gilt er.", false);
      kasten.hidden = true;
      zeigen();
    });
  });

  zeigen();

  /* Handy weg: ein Wiederherstellungscode entfernt den zweiten Faktor.
     Er meldet niemanden an - danach wird neu eingerichtet. */
  if (whKnopf) {
    whKnopf.addEventListener("click", function () {
      var code = (whFeld.value || "").trim();
      if (!code) { sagen("Bitte einen Wiederherstellungscode eingeben.", true); return; }
      whKnopf.disabled = true;
      rufen("/wiederherstellen", { code: code }).then(function (a) {
        whKnopf.disabled = false;
        if (a.satz && a.satz.geloest) {
          whFeld.value = "";
          sagen(a.satz.hinweis, false);
          zeigen();
        } else {
          var text = (a.satz && a.satz.fehler) || "Das hat nicht geklappt.";
          if (a.satz && typeof a.satz.versuche_uebrig === "number") {
            text += " Noch " + a.satz.versuche_uebrig + " Versuche in dieser Stunde.";
          }
          sagen(text, true);
        }
      }).catch(function () {
        whKnopf.disabled = false;
        sagen("Keine Verbindung.", true);
      });
    });
  }
})();
