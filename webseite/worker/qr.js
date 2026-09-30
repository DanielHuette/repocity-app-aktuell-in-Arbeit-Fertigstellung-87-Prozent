/* ═══════════════════════════════════════════════════════════════════
 *  QR-CODE - selbst gerechnet, damit die Seite nichts nachlaedt
 *
 *  Gebraucht wird genau ein Fall: die otpauth-Zeile fuer Google
 *  Authenticator, rund 150 Zeichen. Darum kann dieser Erzeuger weniger
 *  als eine fertige Bibliothek und ist dafuer ein Zehntel so gross:
 *  nur Byte-Modus, nur Fehlerstufe M, nur die Versionen 1 bis 10.
 *
 *  Warum nicht einfach eine Bibliothek: der QR-Code enthaelt den
 *  Schluessel fuer den zweiten Faktor. Fremder Code, der genau in dem
 *  Moment mitliest, waere die unangenehmste Stelle im ganzen Haus.
 *
 *  Geprueft wird gegen eine anerkannte Umsetzung, nicht gegen die
 *  eigene Rechnung: die erwarteten Muster liegen eingefroren in der
 *  Pruefung des Webseitenbetreuers.
 * ═══════════════════════════════════════════════════════════════════ */

/* Datenwoerter je Block und Fehlerwoerter je Block, Fehlerstufe M.
   [Fehlerwoerter je Block, [[Anzahl Bloecke, Datenwoerter je Block], ...]] */
const BAUART = {
  1: [10, [[1, 16]]],
  2: [16, [[1, 28]]],
  3: [26, [[1, 44]]],
  4: [18, [[2, 32]]],
  5: [24, [[2, 43]]],
  6: [16, [[4, 27]]],
  7: [18, [[4, 31]]],
  8: [22, [[2, 38], [2, 39]]],
  9: [22, [[3, 36], [2, 37]]],
  10: [26, [[4, 43], [1, 44]]],
};

/* Wieviele Zeichen eine Version im Byte-Modus fasst. */
const FASST = { 1: 14, 2: 26, 3: 42, 4: 62, 5: 84, 6: 106, 7: 122, 8: 152,
                9: 180, 10: 213 };

/* Mitten der Ausrichtungsmuster. */
const AUSRICHTUNG = {
  1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
  7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
};

/* Die 15 Bit Formatangabe je Maske, Fehlerstufe M - niedrigstes Bit
   zuerst, also genau in der Reihenfolge, in der die Felder abgelaufen
   werden. */
const FORMAT_M = [
  "101010000010010", "101000100100101", "101111001111100", "101101101001011",
  "100010111111001", "100000011001110", "100111110010111", "100101010100000",
];

/* Die 18 Bit Versionsangabe, erst ab Version 7 noetig. */
const VERSION_BITS = {
  7: "000111110010010100", 8: "001000010110111100",
  9: "001001101010011001", 10: "001010010011010011",
};

/* ------------------------------------------------- Rechnen im GF(256) */

const EXP = new Uint8Array(512);
const LOG = new Uint8Array(256);
(function aufbauen() {
  let x = 1;
  for (let i = 0; i < 255; i++) {
    EXP[i] = x;
    LOG[x] = i;
    x <<= 1;
    if (x & 256) x ^= 0x11d;
  }
  for (let i = 255; i < 512; i++) EXP[i] = EXP[i - 255];
})();

function mal(a, b) {
  if (a === 0 || b === 0) return 0;
  return EXP[LOG[a] + LOG[b]];
}

function erzeuger(anzahl) {
  let p = [1];
  for (let i = 0; i < anzahl; i++) {
    const neu = new Array(p.length + 1).fill(0);
    for (let j = 0; j < p.length; j++) {
      neu[j] ^= mal(p[j], 1);
      neu[j + 1] ^= mal(p[j], EXP[i]);
    }
    p = neu;
  }
  return p;
}

function fehlerwoerter(daten, anzahl) {
  const g = erzeuger(anzahl);
  const rest = new Array(daten.length + anzahl).fill(0);
  for (let i = 0; i < daten.length; i++) rest[i] = daten[i];
  for (let i = 0; i < daten.length; i++) {
    const f = rest[i];
    if (f === 0) continue;
    for (let j = 0; j < g.length; j++) rest[i + j] ^= mal(g[j], f);
  }
  return rest.slice(daten.length);
}

/* ------------------------------------------------------ Daten packen */

function version_fuer(laenge) {
  for (let v = 1; v <= 10; v++) if (laenge <= FASST[v]) return v;
  return null;
}

function datenstrom(bytes, version) {
  const [ecJeBlock, bloecke] = BAUART[version];
  const datenwoerter = bloecke.reduce((s, [n, d]) => s + n * d, 0);

  const bits = [];
  const schieben = (wert, breite) => {
    for (let i = breite - 1; i >= 0; i--) bits.push((wert >> i) & 1);
  };
  schieben(0b0100, 4);                       // Byte-Modus
  schieben(bytes.length, version < 10 ? 8 : 16);
  for (const b of bytes) schieben(b, 8);

  const platz = datenwoerter * 8;
  for (let i = 0; i < 4 && bits.length < platz; i++) bits.push(0);
  while (bits.length % 8 !== 0) bits.push(0);

  const woerter = [];
  for (let i = 0; i < bits.length; i += 8) {
    woerter.push(parseInt(bits.slice(i, i + 8).join(""), 2));
  }
  /* Auffuellen mit den beiden festgelegten Fuellwoertern. */
  const fuellung = [0xec, 0x11];
  let n = 0;
  while (woerter.length < datenwoerter) woerter.push(fuellung[n++ % 2]);

  /* In Bloecke teilen, Fehlerwoerter rechnen, verzahnt zusammensetzen. */
  const datenBloecke = [];
  const ecBloecke = [];
  let ab = 0;
  for (const [anzahl, laenge] of bloecke) {
    for (let i = 0; i < anzahl; i++) {
      const block = woerter.slice(ab, ab + laenge);
      ab += laenge;
      datenBloecke.push(block);
      ecBloecke.push(fehlerwoerter(block, ecJeBlock));
    }
  }

  const aus = [];
  const laengste = Math.max(...datenBloecke.map((b) => b.length));
  for (let i = 0; i < laengste; i++) {
    for (const block of datenBloecke) if (i < block.length) aus.push(block[i]);
  }
  for (let i = 0; i < ecJeBlock; i++) {
    for (const block of ecBloecke) aus.push(block[i]);
  }
  return aus;
}

/* ------------------------------------------------------ Muster legen */

function leer(groesse) {
  return Array.from({ length: groesse }, () => new Array(groesse).fill(null));
}

function sucher(feld, zeile, spalte) {
  for (let i = -1; i <= 7; i++) {
    for (let j = -1; j <= 7; j++) {
      const z = zeile + i;
      const s = spalte + j;
      if (z < 0 || s < 0 || z >= feld.length || s >= feld.length) continue;
      const rand = i === -1 || i === 7 || j === -1 || j === 7;
      const aussen = (i >= 0 && i <= 6 && (j === 0 || j === 6))
        || (j >= 0 && j <= 6 && (i === 0 || i === 6));
      const kern = i >= 2 && i <= 4 && j >= 2 && j <= 4;
      feld[z][s] = (!rand && (aussen || kern)) ? 1 : 0;
    }
  }
}

function grundmuster(version) {
  const groesse = 17 + 4 * version;
  const feld = leer(groesse);

  sucher(feld, 0, 0);
  sucher(feld, 0, groesse - 7);
  sucher(feld, groesse - 7, 0);

  for (let i = 8; i < groesse - 8; i++) {
    feld[6][i] = i % 2 === 0 ? 1 : 0;
    feld[i][6] = i % 2 === 0 ? 1 : 0;
  }

  const mitten = AUSRICHTUNG[version];
  const erste = mitten[0];
  const letzte = mitten[mitten.length - 1];
  for (const z of mitten) {
    for (const s of mitten) {
      /* Nur die drei Ecken auslassen - dort stehen die Sucher. Ein
         Ausrichtungsmuster auf der Taktspur gehoert dagegen hin. */
      if ((z === erste && s === erste) || (z === erste && s === letzte)
          || (z === letzte && s === erste)) {
        continue;
      }
      for (let i = -2; i <= 2; i++) {
        for (let j = -2; j <= 2; j++) {
          const rand = Math.max(Math.abs(i), Math.abs(j));
          feld[z + i][s + j] = (rand === 1) ? 0 : 1;
        }
      }
    }
  }

  feld[groesse - 8][8] = 1;                 // das immer dunkle Feld

  /* Plaetze der Formatangabe freihalten. */
  for (let i = 0; i <= 8; i++) {
    if (feld[8][i] === null) feld[8][i] = 0;
    if (feld[i][8] === null) feld[i][8] = 0;
  }
  for (let i = 0; i < 8; i++) {
    if (feld[8][groesse - 1 - i] === null) feld[8][groesse - 1 - i] = 0;
    if (feld[groesse - 1 - i][8] === null) feld[groesse - 1 - i][8] = 0;
  }

  if (version >= 7) {
    const bits = VERSION_BITS[version];
    for (let i = 0; i < 18; i++) {
      const bit = Number(bits[17 - i]);
      const z = Math.floor(i / 3);
      const s = groesse - 11 + (i % 3);
      feld[z][s] = bit;
      feld[s][z] = bit;
    }
  }
  return feld;
}

function belegt(version) {
  /* Wo schon etwas liegt - dieselbe Rechnung, nur als Merkfeld. */
  const feld = grundmuster(version);
  return feld.map((zeile) => zeile.map((wert) => wert !== null));
}

function daten_legen(feld, fest, woerter) {
  const groesse = feld.length;
  const bits = [];
  for (const wort of woerter) {
    for (let i = 7; i >= 0; i--) bits.push((wort >> i) & 1);
  }
  let n = 0;
  let hoch = true;
  for (let s = groesse - 1; s > 0; s -= 2) {
    if (s === 6) s--;                        // die senkrechte Taktspur
    for (let k = 0; k < groesse; k++) {
      const z = hoch ? groesse - 1 - k : k;
      for (const versatz of [0, 1]) {
        const spalte = s - versatz;
        if (fest[z][spalte]) continue;
        feld[z][spalte] = n < bits.length ? bits[n] : 0;
        n++;
      }
    }
    hoch = !hoch;
  }
}

const MASKEN = [
  (i, j) => (i + j) % 2 === 0,
  (i) => i % 2 === 0,
  (i, j) => j % 3 === 0,
  (i, j) => (i + j) % 3 === 0,
  (i, j) => (Math.floor(i / 2) + Math.floor(j / 3)) % 2 === 0,
  (i, j) => ((i * j) % 2) + ((i * j) % 3) === 0,
  (i, j) => ((((i * j) % 2) + ((i * j) % 3)) % 2) === 0,
  (i, j) => ((((i + j) % 2) + ((i * j) % 3)) % 2) === 0,
];

function strafe(feld) {
  const n = feld.length;
  let summe = 0;

  /* 1: fuenf oder mehr gleiche in einer Reihe */
  for (let i = 0; i < n; i++) {
    for (const waagerecht of [true, false]) {
      let lauf = 1;
      for (let j = 1; j < n; j++) {
        const a = waagerecht ? feld[i][j] : feld[j][i];
        const b = waagerecht ? feld[i][j - 1] : feld[j - 1][i];
        if (a === b) {
          lauf++;
        } else {
          if (lauf >= 5) summe += lauf - 2;
          lauf = 1;
        }
      }
      if (lauf >= 5) summe += lauf - 2;
    }
  }

  /* 2: gleichfarbige Zweierbloecke */
  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - 1; j++) {
      const w = feld[i][j];
      if (w === feld[i][j + 1] && w === feld[i + 1][j] && w === feld[i + 1][j + 1]) {
        summe += 3;
      }
    }
  }

  /* 3: das sucherartige Muster */
  const muster1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0];
  const muster2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1];
  for (let i = 0; i < n; i++) {
    for (let j = 0; j + 11 <= n; j++) {
      for (const richtung of [true, false]) {
        const stueck = [];
        for (let k = 0; k < 11; k++) {
          stueck.push(richtung ? feld[i][j + k] : feld[j + k][i]);
        }
        const gleich = (m) => m.every((w, k) => w === stueck[k]);
        if (gleich(muster1) || gleich(muster2)) summe += 40;
      }
    }
  }

  /* 4: Verhaeltnis dunkel zu hell */
  let dunkel = 0;
  for (const zeile of feld) for (const w of zeile) dunkel += w;
  const anteil = (dunkel * 100) / (n * n);
  summe += Math.floor(Math.abs(anteil - 50) / 5) * 10;
  return summe;
}

function format_legen(feld, maske) {
  const bits = FORMAT_M[maske];
  const n = feld.length;
  for (let i = 0; i < 15; i++) {
    const bit = Number(bits[i]);
    /* erste Kopie: um den linken oberen Sucher */
    if (i < 6) feld[8][i] = bit;
    else if (i === 6) feld[8][7] = bit;
    else if (i === 7) feld[8][8] = bit;
    else if (i === 8) feld[7][8] = bit;
    else feld[14 - i][8] = bit;
    /* Zweite Kopie: sieben Felder in der Spalte links unten, acht in
       der Zeile rechts oben. Andersherum bleibt das linke Feld der
       Zeile leer und wird faelschlich zu einem Datenfeld. */
    if (i < 7) feld[n - 1 - i][8] = bit;
    else feld[8][n - 15 + i] = bit;
  }
}

/* --------------------------------------------------------- Erzeugen */

export function muster(text) {
  const bytes = new TextEncoder().encode(String(text));
  const version = version_fuer(bytes.length);
  if (!version) {
    throw new Error("Zu lang fuer diesen Erzeuger: " + bytes.length + " Bytes");
  }
  const woerter = datenstrom(bytes, version);
  const fest = belegt(version);

  let bestes = null;
  let besteStrafe = Infinity;
  for (let maske = 0; maske < 8; maske++) {
    const feld = grundmuster(version).map((z) => z.slice());
    daten_legen(feld, fest, woerter);
    for (let i = 0; i < feld.length; i++) {
      for (let j = 0; j < feld.length; j++) {
        if (!fest[i][j] && MASKEN[maske](i, j)) feld[i][j] ^= 1;
      }
    }
    format_legen(feld, maske);
    const wert = strafe(feld);
    if (wert < besteStrafe) {
      besteStrafe = wert;
      bestes = feld;
    }
  }
  return bestes;
}

/** Als SVG - eine Zeichnung, kein Bild: scharf in jeder Groesse. */
export function svg(text, rand = 4, dunkel = "#111111", hell = "#ffffff") {
  const feld = muster(text);
  const n = feld.length;
  const kante = n + 2 * rand;
  const wege = [];
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (feld[i][j]) wege.push("M" + (j + rand) + " " + (i + rand) + "h1v1h-1z");
    }
  }
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + kante + " "
    + kante + '" shape-rendering="crispEdges" role="img" '
    + 'aria-label="QR-Code fuer den zweiten Faktor">'
    + '<rect width="' + kante + '" height="' + kante + '" fill="' + hell + '"/>'
    + '<path fill="' + dunkel + '" d="' + wege.join("") + '"/></svg>';
}
