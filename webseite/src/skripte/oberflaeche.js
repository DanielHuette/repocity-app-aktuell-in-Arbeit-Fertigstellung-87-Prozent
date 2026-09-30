/* Bedienung der Oberfläche: Design umschalten, Leiste ein- und ausklappen,
   Fragefenster. Nichts davon braucht einen Server. */

(function () {
  "use strict";

  /* ── Design ──────────────────────────────────────────── */
  var wurzel = document.documentElement;
  var knoepfe = Array.prototype.slice.call(document.querySelectorAll("[data-kit-knopf]"));

  function zeige(kit) {
    knoepfe.forEach(function (k) {
      k.setAttribute("aria-pressed", k.getAttribute("data-kit-knopf") === kit ? "true" : "false");
    });
  }
  function setze(kit) {
    wurzel.setAttribute("data-kit", kit);
    try { localStorage.setItem("rc_kit", kit); } catch (e) {}
    zeige(kit);
  }
  knoepfe.forEach(function (k) {
    k.addEventListener("click", function () { setze(k.getAttribute("data-kit-knopf")); });
  });
  /* Was wirklich gilt, steht am HTML-Kopf - das Startskript hat es dort
     gesetzt, bevor das erste Bild stand. Vorher fiel diese Zeile auf
     "blende" zurueck, und dann sah der Knopf Blende angewaehlt aus, obwohl
     etwas anderes galt. */
  zeige(wurzel.getAttribute("data-kit") || "rechenwerk");

  /* ── Landing ohne Anflug ─────────────────────────────── */
  /* Wer aus der Oberflaeche auf Landing geht, will die Landing sehen, nicht
     erst den Logo-Auftritt. Der Wunsch wird im Sitzungsspeicher abgelegt -
     nicht in der Adresse, sonst bleibt er im Verlauf haengen. */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    if (href !== "/" && href !== "/?landing") return;
    try { sessionStorage.setItem("rc_ohne_anflug", "ja"); } catch (err) {}
  });

  /* ── Leiste auf schmalen Schirmen ────────────────────── */
  var schalter = document.getElementById("leiste-schalter");
  var leiste = document.getElementById("leiste");
  if (schalter && leiste) {
    schalter.addEventListener("click", function () { leiste.classList.toggle("offen"); });
    leiste.addEventListener("click", function (e) {
      if (e.target.closest("a")) leiste.classList.remove("offen");
    });
  }

  /* ── Mia ─────────────────────────────────────────────── */
  /* Offen, bis der Besucher sie schliesst - und dann fuer diese Sitzung
     zu. Sonst spraenge sie bei jedem Seitenwechsel wieder auf. */
  var MIA_ZU = "rc_mia_zu";
  var knopf = document.getElementById("frage-knopf");
  var fenster = document.getElementById("frage-fenster");
  var zu = document.getElementById("frage-zu");
  var form = document.getElementById("frage-form");
  var feld = document.getElementById("frage-text");
  var verlauf = document.getElementById("frage-verlauf");

  function oeffne(auf, still) {
    if (!fenster) return;
    fenster.hidden = !auf;
    if (auf && feld && !still) feld.focus();
    try { sessionStorage.setItem(MIA_ZU, auf ? "" : "ja"); } catch (e) {}
  }
  var vorherZu = "";
  try { vorherZu = sessionStorage.getItem(MIA_ZU) || ""; } catch (e) {}
  if (fenster) fenster.hidden = vorherZu === "ja";
  if (knopf) knopf.addEventListener("click", function () { oeffne(fenster.hidden); });
  if (zu) zu.addEventListener("click", function () { oeffne(false); });

  function zeigeVerweis(v) {
    if (!v || !v.adresse) return;
    var a = document.createElement("a");
    a.className = "frage-verweis";
    a.href = v.adresse;
    a.textContent = (v.titel || "Dort steht es") + " →";
    verlauf.appendChild(a);
  }

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var text = (feld.value || "").trim();
      if (!text) return;
      var hinweis = verlauf.querySelector(".frage-hinweis");
      if (hinweis) hinweis.remove();

      var du = document.createElement("p");
      du.className = "frage-du";
      du.textContent = text;
      verlauf.appendChild(du);
      feld.value = "";

      var antwort = document.createElement("p");
      antwort.className = "frage-antwort";
      antwort.textContent = "…";
      verlauf.appendChild(antwort);
      verlauf.scrollTop = verlauf.scrollHeight;

      fetch("/api/frage", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ frage: text }),
      })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          antwort.textContent = d.antwort || "Dazu habe ich noch keine Antwort.";
          /* Der Wegweiser antwortet mit einem Verweis - der gehoert als Link
             darunter, sonst muesste der Leser die Adresse abtippen. Kommt
             keiner mit, bleibt es beim Satz. */
          zeigeVerweis(d.verweis);
          (d.weitere || []).forEach(zeigeVerweis);
        })
        .catch(function () {
          antwort.textContent = "Die Antwort kommt später vom Hub — der ist noch nicht angeschlossen.";
        })
        .then(function () { verlauf.scrollTop = verlauf.scrollHeight; });
    });
  }
})();
