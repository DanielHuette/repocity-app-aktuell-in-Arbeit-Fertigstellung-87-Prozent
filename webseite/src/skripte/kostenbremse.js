/* Die Kostenbremse — dieselben Regeln wie in der App und im Universe.
 *
 * RepoCity setzt dem Nutzer keine Grenze. Was er ausgibt, entscheidet er.
 * Er kann sich für jede Produktionsstraße und jede Kette eine eigene Marke
 * setzen; Voreinstellung ist keine.
 *
 * Dieselben Zahlen stehen an drei Stellen: hier, in kern/Kostenbremse.kt der
 * App und in universe/kern/bremse.py. Die Prüfung
 * webseite.kostenbremse-stimmt-mit-app-und-universe vergleicht sie.
 */

/** Ab diesem Anteil der Marke wird gewarnt. Muss zu bremse.py passen. */
export const WARNSCHWELLE = 0.8;

/** Beim Vielfachen der Lauf-Marke bricht auch ein laufender Auftrag ab. */
export const ABBRUCH_FAKTOR = 2.0;

export const FREI = "frei";
export const WARNUNG = "warnung";
export const STOPP = "stopp";
export const ABBRUCH = "abbruch";

/** Wo die Marken im Browser liegen, bis sie am Hub liegen (siehe F8). */
const SCHLUESSEL = "repocity.kostenbremse";

export function markenLesen() {
  try {
    return JSON.parse(localStorage.getItem(SCHLUESSEL) || "{}");
  } catch {
    return {};
  }
}

export function markeSetzen(kennung, monatEur, laufEur) {
  const alle = markenLesen();
  alle[kennung] = {
    kennung,
    aktiv: true,
    monatEur: Number(monatEur) || 0,
    laufEur: Number(laufEur) || 0,
    gesetztAm: new Date().toISOString(),
  };
  localStorage.setItem(SCHLUESSEL, JSON.stringify(alle));
  return alle[kennung];
}

/** Marke lösen. Der Wert bleibt stehen, damit er nicht neu getippt wird. */
export function markeLoesen(kennung) {
  const alle = markenLesen();
  if (alle[kennung]) {
    alle[kennung].aktiv = false;
    localStorage.setItem(SCHLUESSEL, JSON.stringify(alle));
  }
  return alle[kennung];
}

/* Gesucht wird von genau nach allgemein: prod.video.clip, dann prod.video,
   dann prod. So kann der Nutzer eine Marke für alle Videos setzen, ohne jede
   einzelne Straße anzufassen. */
export function geltendeMarke(kennung, marken) {
  let teil = kennung;
  for (;;) {
    const m = marken[teil];
    if (m && m.aktiv) return m;
    const punkt = teil.lastIndexOf(".");
    if (punkt < 0) return null;
    teil = teil.slice(0, punkt);
  }
}

/** Euro so, wie ein Mensch sie liest — kleine Beträge genauer. */
export function euro(betrag) {
  if (!betrag) return "0,00 €";
  if (betrag < 0.01) return betrag.toFixed(5).replace(".", ",") + " €";
  return betrag.toFixed(2).replace(".", ",") + " €";
}

/**
 * Welche Stufe für den nächsten Schritt gilt.
 * Gibt { stufe, text, laeuftWeiter } zurück.
 */
export function stufe(kennung, marken, betragEur, schonImLauf = 0, imMonat = 0) {
  const marke = geltendeMarke(kennung, marken);
  if (!marke) {
    return urteil(FREI, "Keine Marke gesetzt — du entscheidest.");
  }

  const gilt = marke.kennung;
  const imLauf = schonImLauf + betragEur;
  const monat = imMonat + betragEur;

  if (marke.laufEur > 0 && imLauf > marke.laufEur * ABBRUCH_FAKTOR) {
    return urteil(
      ABBRUCH,
      `Dieser Lauf käme auf ${euro(imLauf)}. Das ist mehr als das Doppelte ` +
        `deiner Marke von ${euro(marke.laufEur)} (${gilt}) — hier bricht auch ` +
        `ein angefangener Lauf ab.`,
    );
  }

  if (marke.monatEur > 0 && monat > marke.monatEur) {
    return schonImLauf > 0
      ? urteil(
          WARNUNG,
          `Du bist über deiner Monatsmarke von ${euro(marke.monatEur)} ` +
            `(${gilt}): ${euro(monat)}. Der angefangene Lauf wird noch fertig.`,
        )
      : urteil(
          STOPP,
          `Angehalten, weil deine Marke von ${euro(marke.monatEur)} erreicht ` +
            `ist (${gilt}). Hier fängt nichts Neues mehr an, bis du die Marke änderst.`,
        );
  }

  if (marke.laufEur > 0 && imLauf > marke.laufEur) {
    return schonImLauf > 0
      ? urteil(
          WARNUNG,
          `Dieser Lauf ist über deiner Marke von ${euro(marke.laufEur)} ` +
            `(${gilt}): ${euro(imLauf)}. Angefangen ist angefangen, er läuft zu Ende.`,
        )
      : urteil(
          STOPP,
          `Angehalten, weil deine Marke von ${euro(marke.laufEur)} je Lauf ` +
            `erreicht ist (${gilt}).`,
        );
  }

  if (marke.monatEur > 0 && monat >= marke.monatEur * WARNSCHWELLE) {
    return urteil(
      WARNUNG,
      `Du hast ${euro(monat)} von ${euro(marke.monatEur)} verbraucht (${gilt}).`,
    );
  }

  if (marke.laufEur > 0 && imLauf >= marke.laufEur * WARNSCHWELLE) {
    return urteil(
      WARNUNG,
      `Dieser Lauf liegt bei ${euro(imLauf)} von ${euro(marke.laufEur)} (${gilt}).`,
    );
  }

  return urteil(FREI, "Im Rahmen deiner Marke.");
}

function urteil(name, text) {
  return { stufe: name, text, laeuftWeiter: name === FREI || name === WARNUNG };
}
