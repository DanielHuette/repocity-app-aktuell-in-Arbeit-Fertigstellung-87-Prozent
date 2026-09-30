/* Die zwei Schalter der Tiefenrecherche.
 *
 * Anders als die übrigen Schalter dieser Seite liegen diese NICHT im
 * Speicher des Browsers, sondern am Hub. Der Grund ist schlicht: sie
 * kosten Geld, und derjenige, der Geld ausgibt, ist der Rechner. Was nur
 * im Browser stünde, würde er nie sehen — der Schalter sähe aus wie ein
 * Schalter und hielte nichts an.
 *
 * Ohne Anmeldung gibt es keine Schalter, sondern den Weg zur Anmeldung:
 * am Hub hängt jede Einstellung an einem Konto.
 *
 *   GET  /api/konten/einstellungen  -> { einstellungen: { tiefenrecherche } }
 *   POST /api/konten/einstellungen  <- { tiefenrecherche: { an, ueberKontingent } }
 */
import { angemeldet, kopf } from "./ausweis.js";

const KASTEN = document.querySelector("[data-tr-kasten]");
if (KASTEN) {
  const anSchalter = KASTEN.querySelector('[data-tr="an"]');
  const ueberSchalter = KASTEN.querySelector('[data-tr="ueber"]');
  const hinweis = KASTEN.querySelector("[data-tr-hinweis]");
  const anmeldeteil = KASTEN.querySelector("[data-tr-anmeldung]");
  const schalterteil = KASTEN.querySelector("[data-tr-schalter]");

  function sagen(text, schlimm) {
    if (!hinweis) return;
    hinweis.textContent = text || "";
    hinweis.classList.toggle("warnung", !!schlimm);
  }

  /* Der zweite Schalter hat ohne den ersten keinen Sinn: was nicht läuft,
     kann auch nicht über sein Kontingent hinauslaufen. */
  function nachziehen() {
    if (!ueberSchalter || !anSchalter) return;
    ueberSchalter.disabled = !anSchalter.checked;
    if (!anSchalter.checked) ueberSchalter.checked = false;
  }

  async function holen() {
    try {
      const antwort = await fetch("/api/konten/einstellungen", { headers: kopf() });
      if (!antwort.ok) {
        sagen("Der Stand ist gerade nicht abrufbar (" + antwort.status +
              "). Solange bleibt alles aus.", true);
        return;
      }
      const satz = await antwort.json();
      const tr = (satz.einstellungen || {}).tiefenrecherche || {};
      if (anSchalter) anSchalter.checked = !!tr.an;
      if (ueberSchalter) ueberSchalter.checked = !!tr.ueberKontingent;
      nachziehen();
      sagen("");
    } catch (e) {
      sagen("Der Hub ist nicht erreichbar. Solange bleibt alles aus.", true);
    }
  }

  async function senden() {
    nachziehen();
    try {
      const antwort = await fetch("/api/konten/einstellungen", {
        method: "POST",
        headers: kopf(),
        body: JSON.stringify({
          tiefenrecherche: {
            an: !!(anSchalter && anSchalter.checked),
            ueberKontingent: !!(ueberSchalter && ueberSchalter.checked),
          },
        }),
      });
      if (!antwort.ok) {
        sagen("Nicht gespeichert (" + antwort.status + ") — es gilt der alte Stand.", true);
        await holen();
        return;
      }
      sagen("gespeichert");
    } catch (e) {
      sagen("Nicht gespeichert: der Hub ist nicht erreichbar.", true);
      await holen();
    }
  }

  if (!angemeldet()) {
    if (anmeldeteil) anmeldeteil.hidden = false;
    if (schalterteil) schalterteil.hidden = true;
  } else {
    if (anmeldeteil) anmeldeteil.hidden = true;
    if (schalterteil) schalterteil.hidden = false;
    if (anSchalter) anSchalter.addEventListener("change", senden);
    if (ueberSchalter) ueberSchalter.addEventListener("change", senden);
    holen();
  }
}
