/* Die Kostenansicht im Browser — dasselbe Verhalten wie im neunten Feld der App.
 *
 * Die Regeln stehen nicht hier, sondern in kostenbremse.js: eine Stelle für
 * die Rechnung, damit Anzeige und Urteil nicht auseinanderlaufen können.
 */
import {
  WARNSCHWELLE,
  euro,
  geltendeMarke,
  markeLoesen,
  markeSetzen,
  markenLesen,
} from "./kostenbremse.js";

const zeilen = Array.from(document.querySelectorAll(".kosten-zeile"));

function zeichne(li, marken) {
  const kennung = li.dataset.kennung;
  const verbraucht = Number(li.dataset.verbraucht) || 0;
  const jeLauf = Number(li.dataset.jeLauf) || 0;
  /* Die Marke wird in Schritten des gemessenen Laufpreises geschoben, nicht in
     glatten Euro: so entspricht jeder Schritt einer echten Produktion. Kostet
     ein Lauf nichts, gilt ein Cent als kleinster sinnvoller Schritt. */
  const schritt = jeLauf > 0 ? jeLauf : 0.01;

  const eigene = marken[kennung];
  const geltend = geltendeMarke(kennung, marken);
  const aktiv = Boolean(eigene && eigene.aktiv);
  const monat = aktiv && eigene.monatEur > 0 ? eigene.monatEur : schritt * 20;

  const betrag = li.querySelector('[data-rolle="betrag"]');
  const stand = li.querySelector('[data-rolle="stand"]');
  const balken = li.querySelector('[data-rolle="balken"]');
  const standtext = li.querySelector('[data-rolle="standtext"]');
  const anaus = li.querySelector('[data-rolle="anaus"]');
  const regler = li.querySelector('[data-rolle="regler"]');
  const schieber = li.querySelector('[data-rolle="schieber"]');
  const reglertext = li.querySelector('[data-rolle="reglertext"]');
  const ohnetext = li.querySelector('[data-rolle="ohnetext"]');

  betrag.textContent = euro(verbraucht);
  anaus.checked = aktiv;
  schieber.value = String(Math.max(1, Math.round(monat / schritt)));

  if (aktiv) {
    const anteil = Math.min(1, verbraucht / monat);
    const gestoppt = verbraucht >= monat;
    const gewarnt = anteil >= WARNSCHWELLE;

    stand.hidden = false;
    balken.style.width = `${anteil * 100}%`;
    betrag.dataset.stufe = gestoppt ? "stopp" : gewarnt ? "warnung" : "";
    standtext.dataset.stufe = gestoppt ? "stopp" : "";
    standtext.textContent = gestoppt
      ? `Angehalten, weil deine Marke von ${euro(monat)} erreicht ist. ` +
        "Was schon läuft, wird fertig."
      : gewarnt
        ? `Du hast ${euro(verbraucht)} von ${euro(monat)} verbraucht.`
        : `deine Marke: ${euro(monat)} im Monat`;

    regler.hidden = false;
    reglertext.textContent =
      `${euro(monat)} im Monat — das sind rund ${Math.round(monat / schritt)} ` +
      `Läufe zu ${euro(jeLauf)}.`;
    ohnetext.textContent = "";
  } else {
    stand.hidden = true;
    betrag.dataset.stufe = "";
    regler.hidden = true;
    ohnetext.textContent =
      geltend && geltend.kennung !== kennung
        ? `Es gilt deine Marke für „${geltend.kennung}“.`
        : `Keine Grenze. Ein Lauf kostet gemessen ${euro(jeLauf)}.`;
  }
}

/* ── Echte Zahlen vom Hub ──────────────────────────────────────────────
   Der Rechner schickt mit seinem Puls die Monatszusammenfassung des
   Verbrauchsbuchs (verbrauch.zusammenfassung). Hier werden sie je Kostenstelle
   in die Zeilen gelegt und oben als Kategorien gezeigt. Kommt nichts, bleibt
   es bei 0,00 - und der Kasten sagt, dass der Rechner nicht gemeldet hat. */
function kostenVomHub() {
  fetch("/api/hub/stand", { headers: { accept: "application/json" } })
    .then((a) => (a.ok ? a.json() : null))
    .then((d) => {
      const k = d && d.rechner && d.rechner.kosten;
      const kasten = document.getElementById("kosten-kategorien");
      if (!k) {
        if (kasten) kasten.textContent = "Der Rechner hat diesen Monat noch keine Zahlen gemeldet.";
        return;
      }
      const je = k.je_kostenstelle || {};
      zeilen.forEach((li) => {
        const kennung = li.dataset.kennung;
        /* Eine Kette (z.B. "video") sammelt ihre Strasse ("prod.video.stueck")
           nicht automatisch - gezeigt wird, was unter genau dieser Kennung
           gebucht wurde. */
        if (je[kennung] != null) li.dataset.verbraucht = String(je[kennung]);
      });
      if (kasten) {
        const namen = { modell: "Sprachmodelle", produktion: "Bilder, Stimme, Einbettungen",
                        betrieb: "Feste Betriebskosten", kontingent: "Freie Kontingente" };
        const teile = Object.keys(k.je_kategorie || {}).map((kat) =>
          "<span><b>" + euro(k.je_kategorie[kat]) + "</b> " + (namen[kat] || kat) + "</span>");
        let text = teile.join("");
        const ohne = Object.keys(k.ohne_preis || {});
        if (ohne.length) text += "<span class=\"kosten-warn\">Ohne Preis gebucht: " + ohne.join(", ") + "</span>";
        kasten.innerHTML = text;
      }
      const summe = document.getElementById("kosten-summe");
      if (summe && k.gesamt_eur != null) summe.textContent = euro(k.gesamt_eur);
      const seit = document.getElementById("kosten-seit");
      if (seit && k.seit) seit.textContent = "seit " + k.seit;
    })
    .catch(() => {});
}

function alleZeichnen() {
  const marken = markenLesen();
  let summe = 0;
  for (const li of zeilen) {
    summe += Number(li.dataset.verbraucht) || 0;
    zeichne(li, marken);
  }
  const feld = document.getElementById("kosten-summe");
  if (feld && !feld.dataset.vomHub) feld.textContent = euro(summe);
}

for (const li of zeilen) {
  const kennung = li.dataset.kennung;
  const jeLauf = Number(li.dataset.jeLauf) || 0;
  const schritt = jeLauf > 0 ? jeLauf : 0.01;

  const kopf = li.querySelector(".kosten-kopfzeile");
  const marke = li.querySelector('[data-rolle="marke"]');
  kopf.addEventListener("click", () => {
    const offen = marke.hidden;
    marke.hidden = !offen;
    kopf.setAttribute("aria-expanded", String(offen));
  });

  li.querySelector('[data-rolle="anaus"]').addEventListener("change", (e) => {
    const schieber = li.querySelector('[data-rolle="schieber"]');
    if (e.target.checked) {
      markeSetzen(kennung, Number(schieber.value) * schritt, 0);
    } else {
      markeLoesen(kennung);
    }
    alleZeichnen();
  });

  li.querySelector('[data-rolle="schieber"]').addEventListener("input", (e) => {
    markeSetzen(kennung, Number(e.target.value) * schritt, 0);
    alleZeichnen();
  });
}

alleZeichnen();

kostenVomHub();
