/* Spracheingabe fuer genau EIN Feld: "Was soll gebaut werden?" auf dem
   Dashboard. Sonst wird auf dieser Seite nichts per Sprache bedient.
 *
 * Benutzt wird die Spracherkennung, die im Browser schon eingebaut ist
 * (SpeechRecognition / webkitSpeechRecognition). Kein Schluessel, keine
 * fremde Bibliothek, nichts von aussen nachgeladen — was das Mikrofon
 * hoert, geht denselben Weg wie in Chrome ueblich und nicht ueber uns.
 *
 * Kann der Browser das nicht (Firefox zum Beispiel), verschwindet der Knopf
 * stillschweigend. Getippt wird dann wie vorher — kein Fehler, kein Hinweis.
 */

(function () {
  "use strict";

  var knopf = document.getElementById("sprach-knopf");
  var feld = document.getElementById("auftrag-text");
  var stand = document.getElementById("sprach-stand");
  if (!knopf || !feld) return;

  var Erkennung = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Erkennung) {
    /* Still verschwinden. Ein Hinweis auf etwas, das dieser Browser nie
       koennen wird, hilft niemandem. */
    knopf.remove();
    if (stand) stand.remove();
    return;
  }

  var laeuft = false;
  var erkenner = null;
  var grundtext = "";   /* was im Feld stand, bevor das Zuhoeren anfing */

  function sage(text, art) {
    if (!stand) return;
    stand.textContent = text;
    stand.setAttribute("data-art", art || "bereit");
  }

  function zeige(an) {
    laeuft = an;
    knopf.setAttribute("aria-pressed", an ? "true" : "false");
    knopf.classList.toggle("hoert", an);
    knopf.setAttribute("aria-label", an ? "Aufnahme beenden" : "Mit der Stimme diktieren");
  }

  /* Erkanntes an das anhaengen, was schon im Feld stand. Nichts wird
     ueberschrieben, und abgeschickt wird auch nichts — der Text steht danach
     ganz normal zum Weitertippen da. */
  function einsetzen(text) {
    var neu = grundtext ? grundtext.replace(/\s+$/, "") + " " + text : text;
    feld.value = neu;
    /* Damit andere Teile der Seite (Zaehler, Knopfzustand) es mitbekommen. */
    feld.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function bauen() {
    var e = new Erkennung();
    e.lang = "de-DE";
    e.continuous = false;
    e.interimResults = true;
    e.maxAlternatives = 1;

    e.onstart = function () {
      zeige(true);
      sage("Hört zu — sprich einfach.", "hoert");
    };

    e.onresult = function (ereignis) {
      var fertig = "";
      var vorlaeufig = "";
      for (var i = ereignis.resultIndex; i < ereignis.results.length; i++) {
        var stueck = ereignis.results[i][0].transcript;
        if (ereignis.results[i].isFinal) fertig += stueck;
        else vorlaeufig += stueck;
      }
      einsetzen((fertig + vorlaeufig).trim());
      if (fertig) {
        grundtext = feld.value;
        sage("Erkannt. Du kannst weiterreden oder den Text ändern.", "erkannt");
      } else {
        sage("Erkennt …", "erkannt");
      }
    };

    e.onerror = function (ereignis) {
      var grund = ereignis && ereignis.error ? ereignis.error : "";
      if (grund === "not-allowed" || grund === "service-not-allowed") {
        sage(
          "Das Mikrofon ist nicht freigegeben. Tippen geht ganz normal weiter. " +
          "Freigeben kannst du es über das Schloss-Symbol links in der Adresszeile.",
          "fehler"
        );
      } else if (grund === "no-speech") {
        sage("Ich habe nichts gehört. Tipp noch einmal auf das Mikrofon.", "fehler");
      } else if (grund === "audio-capture") {
        sage("Kein Mikrofon gefunden. Tippen geht ganz normal weiter.", "fehler");
      } else if (grund === "aborted") {
        sage("Abgebrochen.", "bereit");
      } else if (grund === "network") {
        sage("Die Spracherkennung ist gerade nicht erreichbar. Tipp den Text ein.", "fehler");
      } else {
        sage("Das hat nicht geklappt. Tippen geht ganz normal weiter.", "fehler");
      }
    };

    e.onend = function () {
      zeige(false);
      if (stand && stand.getAttribute("data-art") === "hoert") {
        sage("Bereit. Tipp auf das Mikrofon und sprich.", "bereit");
      }
    };

    return e;
  }

  knopf.addEventListener("click", function () {
    if (laeuft) {
      if (erkenner) erkenner.stop();
      return;
    }
    grundtext = feld.value;
    erkenner = bauen();
    try {
      /* Beim ersten Mal fragt der Browser hier selbst nach der Erlaubnis.
         Sagt der Nutzer nein, kommt onerror mit "not-allowed" — behandelt. */
      erkenner.start();
      sage("Bereit — der Browser fragt gleich nach dem Mikrofon.", "bereit");
    } catch (fehler) {
      zeige(false);
      sage("Das hat nicht geklappt. Tippen geht ganz normal weiter.", "fehler");
    }
  });
})();
