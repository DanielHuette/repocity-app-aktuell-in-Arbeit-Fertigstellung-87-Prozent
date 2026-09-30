/* Der Rohling des Organigramms traegt statt Farben Platzhalter. Hier stehen
   die zwei Handgriffe, die daraus ein fertiges Bild machen — einmal
   geschrieben, von beiden Seiten benutzt: Astro setzt beim Bauen das
   Standard-Design ein, der Browser tauscht es beim Design-Wechsel aus.

   Platzhalter:  %%c:linie%%       die Farbe des Werts --linie
                 %%a:linie%%       seine Deckkraft
                 %%a:linie*2.2%%   seine Deckkraft mal 2,2, gedeckelt bei 1

   Erzeugt wird der Rohling von mein_ki_gehirn/bilder/diagramme/bau_diagramm.py.
   Er wird hier nicht von Hand geaendert. */

const PLATZHALTER = /%%([ca]):([a-z-]+)(?:\*([\d.]+))?%%/g;

/** '#RRGGBB', '#RGB' oder 'rgba(r,g,b,a)' -> { farbe, deckkraft } */
export function zerlege(wert) {
  const w = String(wert || "").trim();
  const m = w.match(/rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+))?\s*\)/);
  if (m) {
    const zahl = (n) => Math.round(Number(n)).toString(16).padStart(2, "0");
    return {
      farbe: "#" + zahl(m[1]) + zahl(m[2]) + zahl(m[3]),
      deckkraft: m[4] === undefined ? 1 : Number(m[4]),
    };
  }
  // Auch die Kurzformen mit Deckkraft: beim Bauen wird die Seite
  // zusammengekuerzt, und rgba(255,255,255,0.459) wird dabei zu #ffffff75.
  // Wer das nicht liest, macht aus einer halbdurchsichtigen weissen Flaeche
  // ein deckendes Schwarz - und das Bild wird in hellen Designs finster.
  let h = w.replace("#", "");
  if (h.length === 3 || h.length === 4) h = h.split("").map((c) => c + c).join("");
  if (/^[0-9a-fA-F]{6}$/.test(h)) return { farbe: "#" + h, deckkraft: 1 };
  if (/^[0-9a-fA-F]{8}$/.test(h)) {
    return { farbe: "#" + h.slice(0, 6), deckkraft: parseInt(h.slice(6, 8), 16) / 255 };
  }
  // reine Zahl, etwa --glanz: 0.19
  const z = Number(w);
  if (Number.isFinite(z)) return { farbe: null, deckkraft: z };
  // Nichts davon: der Wert bleibt ungefuellt stehen, damit es auffaellt,
  // statt still schwarz zu werden.
  return { farbe: null, deckkraft: null };
}

/** Setzt die Werte eines Designs in den Rohling ein. */
export function fuelle(rohling, werte) {
  return String(rohling).replace(PLATZHALTER, (ganz, art, name, faktor) => {
    const wert = werte[name];
    if (wert === undefined || wert === "") return ganz;
    const t = zerlege(wert);
    if (art === "c") return t.farbe === null ? ganz : t.farbe;
    if (t.deckkraft === null) return ganz;
    const d = Math.min(1, t.deckkraft * (faktor ? Number(faktor) : 1));
    return String(Math.round(d * 10000) / 10000);
  });
}

/** Welche Werte der Rohling braucht — mehr wird nicht gelesen. */
export function benoetigteWerte(rohling) {
  const namen = new Set();
  String(rohling).replace(PLATZHALTER, (_, __, name) => namen.add(name));
  return [...namen];
}

/** Beim Bauen: die Design-Bloecke aus kits.css lesen. */
export function liesKitsAusCss(css) {
  const kits = {};
  const bloecke = /\[data-kit="(\w+)"\]\s*\{([^}]*)\}/g;
  let b;
  while ((b = bloecke.exec(css)) !== null) {
    const ziel = (kits[b[1]] ||= {});
    const werte = /--([a-z-]+)\s*:\s*([^;]+);/g;
    let w;
    while ((w = werte.exec(b[2])) !== null) {
      if (ziel[w[1]] === undefined) ziel[w[1]] = w[2].trim();
    }
  }
  return kits;
}
