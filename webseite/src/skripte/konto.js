/* Die Konto-Wege auf der Webseite: Adresse bestätigen, Passwort neu setzen.
 *
 * Beide Wege kommen aus einer Mail, die der Hub in den Ausgang gelegt und
 * der E-Mail-Manager verschickt hat:
 *
 *     /zugang/?bestaetigen=<marke>    die Adresse gehört dir
 *     /zugang/?neu=<marke>            ein neues Passwort setzen
 *
 * Ohne Marke in der Adresse passiert hier gar nichts — dann ist die Seite
 * die gewöhnliche Zugangsseite.
 */

(function () {
  const suche = new URLSearchParams(location.search);
  const bestaetigen = suche.get("bestaetigen");
  const neu = suche.get("neu");
  const kasten = document.getElementById("konto-kasten");
  const meldung = document.getElementById("konto-meldung");
  const formular = document.getElementById("konto-formular");
  if (!kasten) return;

  function sagen(text, schlimm) {
    if (!meldung) return;
    meldung.textContent = text;
    meldung.dataset.schlimm = schlimm ? "ja" : "nein";
  }

  async function ruf(weg, satz) {
    const antwort = await fetch(weg, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(satz),
    });
    let daten = {};
    try {
      daten = await antwort.json();
    } catch (e) { /* eine leere Antwort ist auch eine */ }
    return { ok: antwort.ok, daten };
  }

  if (bestaetigen) {
    kasten.hidden = false;
    sagen("einen Moment …", false);
    ruf("/api/konten/bestaetigen", { marke: bestaetigen }).then((r) => {
      if (r.ok && r.daten.bestaetigt) {
        sagen("Danke — deine Adresse ist bestätigt. Du kannst die Seite " +
          "schließen und in der App weitermachen.", false);
      } else {
        sagen(r.daten.fehler || "Dieser Link gilt nicht mehr.", true);
      }
    });
    return;
  }

  if (neu) {
    kasten.hidden = false;
    if (formular) formular.hidden = false;
    sagen("Vergib ein neues Passwort. Mindestens zehn Zeichen — Länge hilft " +
      "mehr als Sonderzeichen.", false);

    const knopf = document.getElementById("konto-setzen");
    const feld = document.getElementById("konto-passwort");
    const feld2 = document.getElementById("konto-passwort2");
    if (!knopf || !feld || !feld2) return;

    knopf.addEventListener("click", async () => {
      if (feld.value !== feld2.value) {
        sagen("Die beiden Eingaben sind nicht gleich.", true);
        return;
      }
      knopf.disabled = true;
      sagen("einen Moment …", false);
      const r = await ruf("/api/konten/neues-passwort", {
        marke: neu, passwort: feld.value,
      });
      knopf.disabled = false;
      if (r.ok && r.daten.gesetzt) {
        if (formular) formular.hidden = true;
        sagen("Das neue Passwort gilt. Alle offenen Anmeldungen auf anderen " +
          "Geräten sind damit ungültig — melde dich in der App neu an.", false);
      } else {
        sagen(r.daten.fehler || "Das hat nicht geklappt.", true);
      }
    });
  }
})();
