/* RepoCity - Anflug.
   Die Kamerafahrt endet in genau der Pose des App-Startbildschirms.
   Stadt, Projektion, Glyphen und Farben stammen unveraendert aus dem
   Logo-Generator (universe/marke/LOGO-STAND.md, Fassung T1) - derselbe
   Zufallskeim erzeugt dieselbe Stadt, deshalb ist das Standbild am Ende
   der Fahrt nicht nachempfunden, sondern dasselbe Bild. */

import { erstelleErde } from "./erde.js";

(function () {
  "use strict";

  var cv = document.getElementById("anflug");
  if (!cv) return;
  /* Landing ohne Anflug: die Buehne ist versteckt, die Fahrt faellt aus. */
  if (document.documentElement.getAttribute("data-ohne-anflug") === "ja") return;
  var ctx = cv.getContext("2d");
  var erdeCv = document.getElementById("erde");
  var erde = null;

  /* ---------- Bildraum des Logos ---------- */
  var W = 1180, H = 720;

  /* ---------- Endpose (LOGO-STAND) ---------- */
  var RAD = 790;
  var P_END = 30 * Math.PI / 180;
  var FOV = 53 * Math.PI / 180;
  var DIST_END = 1900;
  var TY = 250;
  var f = (H / 2) / Math.tan(FOV / 2);

  /* ---------- Stadt, gleicher Keim wie im Generator ---------- */
  function rng(seed) {
    var s = seed >>> 0;
    return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  }
  var city = [];
  (function () {
    var r = rng(20260902), SP = 92;
    for (var i = -10; i <= 10; i++) for (var j = -10; j <= 10; j++) {
      var cx = i * SP + (r() - 0.5) * 18, cz = j * SP + (r() - 0.5) * 18;
      var d = Math.sqrt(cx * cx + cz * cz);
      if (d > RAD) continue;
      if (r() < 0.13) continue;
      var core = Math.exp(-(d * d) / (2 * 380 * 380));
      var rim = 1 - Math.pow(d / RAD, 3);
      var h = (34 + r() * 66) * (0.35 + 0.65 * rim);
      h *= 1 + 3.3 * core;
      var w = 30 + r() * 30, dp = 30 + r() * 30, spire = false;
      if (r() < 0.20 * (0.25 + core)) { h *= 2.05; w *= 0.72; dp *= 0.72; spire = true; }
      var set = null;
      if (h > 175 && r() < 0.55) set = { w: w * (0.52 + r() * 0.18), d: dp * (0.52 + r() * 0.18), h: h * (0.20 + r() * 0.20) };
      var mast = spire && r() < 0.42 ? h * (0.05 + r() * 0.05) : 0;
      city.push({ x: cx, z: cz, w: w, d: dp, h: h, g: 52 + Math.floor(r() * 40), set: set, mast: mast });
    }
  })();

  var hs = city.map(function (b) { return b.h + (b.set ? b.set.h : 0) + b.mast; })
               .sort(function (a, b) { return a - b; });
  var yText = hs[Math.floor(hs.length * 0.965)];

  /* ---------- Kamera ---------- */
  function makeCam(pitch, dist) {
    var fwd = [0, -Math.sin(pitch), -Math.cos(pitch)];
    var right = [1, 0, 0];
    var up = [0, Math.cos(pitch), -Math.sin(pitch)];
    var pos = [0, TY + dist * Math.sin(pitch), dist * Math.cos(pitch)];
    return { fwd: fwd, right: right, up: up, pos: pos };
  }
  function project(c, P) {
    var vx = P[0] - c.pos[0], vy = P[1] - c.pos[1], vz = P[2] - c.pos[2];
    var zv = vx * c.fwd[0] + vy * c.fwd[1] + vz * c.fwd[2];
    if (zv <= 8) return null;
    return [W / 2 + f * (vx * c.right[0] + vy * c.right[1] + vz * c.right[2]) / zv,
            H / 2 - f * (vx * c.up[0] + vy * c.up[1] + vz * c.up[2]) / zv, zv];
  }
  var CAM_END = makeCam(P_END, DIST_END);

  /* ---------- Grund und Licht der Endszene ---------- */
  function drawGround(g, blick, px, py, deckung) {
    if (deckung === undefined) deckung = 1;
    if (deckung > 0.002) {
      g.save();
      g.globalAlpha = Math.min(1, deckung);
      g.fillStyle = "#020204";
      g.fillRect(-px, -py, W + 2 * px, H + 2 * py);
      g.restore();
    }
    if (blick <= 0) return;
    g.save();
    g.globalAlpha = blick;
    g.globalCompositeOperation = "lighter";
    function pool(cx, cy, r, col, a) {
      var gr = g.createRadialGradient(cx, cy, 0, cx, cy, r);
      gr.addColorStop(0, "rgba(" + col + "," + a + ")");
      gr.addColorStop(0.42, "rgba(" + col + "," + (a * 0.28).toFixed(3) + ")");
      gr.addColorStop(1, "rgba(" + col + ",0)");
      g.fillStyle = gr; g.beginPath(); g.arc(cx, cy, r, 0, 6.2832); g.fill();
    }
    pool(W * 0.455, H * 0.545, W * 0.44, "255,206,140", 0.74);
    pool(W * 0.455, H * 0.545, W * 0.18, "255,240,210", 0.58);
    pool(W * 0.80, H * 0.58, W * 0.24, "116,168,224", 0.16);
    [[0.30, -0.40, 0.08, 0.15], [0.68, -0.30, 0.13, 0.09]].forEach(function (s) {
      g.save(); g.translate(s[0] * W, -H * 0.3); g.rotate(s[1]);
      var sw = s[2] * W, gg = g.createLinearGradient(-sw / 2, 0, sw / 2, 0);
      gg.addColorStop(0, "rgba(255,214,150,0)");
      gg.addColorStop(0.5, "rgba(255,214,150," + s[3] + ")");
      gg.addColorStop(1, "rgba(255,214,150,0)");
      g.fillStyle = gg; g.filter = "blur(30px)"; g.fillRect(-sw / 2, 0, sw, H * 2);
      g.filter = "none"; g.restore();
    });
    g.restore();
  }

  /* ---------- Stadt zeichnen ---------- */
  function drawCity(g, cam, alpha) {
    if (alpha <= 0.004) return;
    g.save();
    g.globalAlpha = alpha;
    var list = city.slice().map(function (b) {
      var dx = b.x - cam.pos[0], dz = b.z - cam.pos[2];
      b._d = Math.sqrt(dx * dx + cam.pos[1] * cam.pos[1] + dz * dz);
      return b;
    }).sort(function (a, b) { return b._d - a._d; });

    function poly(pts, fill) {
      for (var i = 0; i < pts.length; i++) if (!pts[i]) return;
      g.beginPath(); g.moveTo(pts[0][0], pts[0][1]);
      for (var k = 1; k < pts.length; k++) g.lineTo(pts[k][0], pts[k][1]);
      g.closePath(); g.fillStyle = fill; g.fill();
    }
    function box(cx, cz, w, d, y0, y1, gv) {
      var hw = w / 2, hd = d / 2, x0 = cx - hw, x1 = cx + hw, z0 = cz - hd, z1 = cz + hd;
      var t = [project(cam, [x0, y1, z0]), project(cam, [x1, y1, z0]),
               project(cam, [x1, y1, z1]), project(cam, [x0, y1, z1])];
      var b = [project(cam, [x0, y0, z0]), project(cam, [x1, y0, z0]),
               project(cam, [x1, y0, z1]), project(cam, [x0, y0, z1])];
      function c(k) {
        var v = Math.round(Math.min(255, gv * k));
        return "rgb(" + v + "," + Math.round(v * 1.02) + "," + Math.round(v * 1.08) + ")";
      }
      if (cam.pos[2] > z1) poly([t[0], t[1], b[1], b[0]], c(0.56));
      if (cam.pos[2] < z0) poly([t[3], t[2], b[2], b[3]], c(0.40));
      if (cam.pos[0] > x1) poly([t[1], t[2], b[2], b[1]], c(0.32));
      if (cam.pos[0] < x0) poly([t[0], t[3], b[3], b[0]], c(0.32));
      poly(t, c(1.42));
    }
    for (var n = 0; n < list.length; n++) {
      var b = list[n];
      var t = Math.max(0, Math.min(1, (b._d - 1150) / 1500));
      var gv = b.g * (0.72 + 1.55 * t);
      box(b.x, b.z, b.w, b.d, 0, b.h, gv);
      if (b.set) box(b.x, b.z, b.set.w, b.set.d, b.h, b.h + b.set.h, gv);
      if (b.mast) { var top = b.h + (b.set ? b.set.h : 0); box(b.x, b.z, b.w * 0.26, b.d * 0.26, top, top + b.mast, gv); }
    }
    g.restore();
  }

  function drawVignette(g, px, py) {
    var vg = g.createRadialGradient(W / 2, H * 0.46, Math.min(W, H) * 0.18, W / 2, H * 0.5, Math.max(W + 2 * px, H + 2 * py) * 0.78);
    vg.addColorStop(0, "rgba(2,2,4,0)");
    vg.addColorStop(1, "rgba(2,2,4,.80)");
    g.fillStyle = vg; g.fillRect(-px, -py, W + 2 * px, H + 2 * py);
  }

  /* ---------- Glyphen ---------- */
  var WORD = "RepoCity", FS = 230;
  var CUTS = {
    "R": [[0.19, 0.185, 0.075, 0.27], [0.55, 0.455, 0.45, 0.05]],
    "e": [[0.36, 0.545, 0.66, 0.055], [0.00, 0.70, 0.34, 0.05]],
    "p": [[0.17, 0.515, 0.075, 0.29], [0.46, 0.70, 0.54, 0.05]],
    "o": [[0.40, 0.395, 0.16, 0.055], [0.00, 0.635, 0.30, 0.05]],
    "C": [[0.00, 0.44, 0.28, 0.062], [0.60, 0.20, 0.40, 0.055]],
    "i": [[0.00, 0.605, 1.00, 0.05]],
    "t": [[0.00, 0.465, 0.32, 0.055], [0.42, 0.72, 0.58, 0.05]],
    "y": [[0.36, 0.645, 0.30, 0.055], [0.00, 0.50, 0.26, 0.05]]
  };

  function glyphSet(shear) {
    var out = [], m = document.createElement("canvas").getContext("2d");
    m.font = "700 " + FS + "px Outfit, system-ui, sans-serif";
    for (var i = 0; i < WORD.length; i++) {
      var ch = WORD[i];
      var drawCh = (ch === "y") ? null : ch;
      var adv = m.measureText(ch).width;
      var gw = Math.ceil(adv * 1.35 + shear * FS * 1.1) + 20;
      var gh = Math.ceil(FS * 1.62), base = Math.round(gh * 0.66);

      var mask = document.createElement("canvas"); mask.width = gw; mask.height = gh;
      var mc = mask.getContext("2d");
      mc.font = "700 " + FS + "px Outfit, system-ui, sans-serif";
      mc.textBaseline = "alphabetic"; mc.fillStyle = "#fff"; mc.strokeStyle = "#fff";
      mc.translate(0, base); mc.transform(1, 0, -shear, 1, 0, 0); mc.translate(0, -base);

      if (drawCh) {
        mc.fillText(drawCh, 6, base);
      } else {
        var st = FS * 0.150, xh = FS * 0.515, tail = FS * 0.315, wY = m.measureText("y").width;
        var L = 6, Rw = 6 + wY, topY = base - xh, vx = 6 + wY / 2;
        mc.lineCap = "butt"; mc.lineJoin = "miter"; mc.lineWidth = st;
        mc.beginPath();
        mc.moveTo(L + st / 2, topY); mc.lineTo(vx, base); mc.lineTo(Rw - st / 2, topY);
        mc.stroke();
        mc.fillRect(vx - st / 2, base - st * 0.55, st, tail);
      }

      var inkW = adv, x0 = gw, x1 = 0, y0 = gh, y1 = 0;
      try {
        var id = mc.getImageData(0, 0, gw, gh).data;
        for (var yy = 0; yy < gh; yy += 2) {
          var row = yy * gw;
          for (var xx = 0; xx < gw; xx++) {
            if (id[(row + xx) * 4 + 3] > 40) {
              if (xx < x0) x0 = xx; if (xx > x1) x1 = xx;
              if (yy < y0) y0 = yy; if (yy > y1) y1 = yy;
            }
          }
        }
        if (x1 > x0) inkW = x1 - x0; else { x0 = 0; x1 = Math.max(1, Math.round(adv)); }
      } catch (e) {}

      mc.globalCompositeOperation = "destination-out";
      var cuts = (ch === "y") ? [] : (CUTS[ch] || []);
      for (var q = 0; q < cuts.length; q++)
        mc.fillRect(cuts[q][0] * gw, cuts[q][1] * gh * 0.86 + gh * 0.03, cuts[q][2] * gw, cuts[q][3] * gh);
      mc.globalCompositeOperation = "source-over";

      var face = document.createElement("canvas"); face.width = gw; face.height = gh;
      var fc = face.getContext("2d");
      fc.drawImage(mask, 0, 0);
      fc.globalCompositeOperation = "source-in";
      var top = gh * 0.13, bot = gh * 0.70;
      var g = fc.createLinearGradient(0, top, 0, bot);
      g.addColorStop(0.00, "#FFFDF3"); g.addColorStop(0.12, "#FCEDC6");
      g.addColorStop(0.355, "#E2C177"); g.addColorStop(0.362, "#FFFFFF");
      g.addColorStop(0.408, "#FFF7DF"); g.addColorStop(0.415, "#DCB25C");
      g.addColorStop(0.600, "#BC8F37"); g.addColorStop(0.616, "#F2D79B");
      g.addColorStop(0.800, "#FCF0D0"); g.addColorStop(1.00, "#FFF9E7");
      fc.fillStyle = g; fc.fillRect(0, 0, gw, gh);

      function band(off, col) {
        var c = document.createElement("canvas"); c.width = gw; c.height = gh;
        var x = c.getContext("2d"); x.drawImage(mask, 0, 0);
        x.globalCompositeOperation = "destination-out"; x.drawImage(mask, 0, off);
        x.globalCompositeOperation = "source-in"; x.fillStyle = col; x.fillRect(0, 0, gw, gh);
        return c;
      }
      fc.globalCompositeOperation = "source-over";
      fc.drawImage(band(Math.max(2, FS * 0.020), "#FFFFFF"), 0, 0);
      fc.drawImage(band(-Math.max(2, FS * 0.015), "rgba(92,56,16,.9)"), 0, 0);

      function tint(stops) {
        var c = document.createElement("canvas"); c.width = gw; c.height = gh;
        var x = c.getContext("2d"); x.drawImage(mask, 0, 0);
        x.globalCompositeOperation = "source-in";
        var gg = x.createLinearGradient(0, top, 0, bot);
        for (var t = 0; t < stops.length; t++) gg.addColorStop(stops[t][0], stops[t][1]);
        x.fillStyle = gg; x.fillRect(0, 0, gw, gh);
        return c;
      }
      out.push({
        face: face,
        side: tint([[0, "#FBE7B6"], [0.45, "#E0BC6C"], [1, "#C29A45"]]),
        dark: tint([[0, "#B08C3A"], [0.5, "#8E6E28"], [1, "#6E5520"]]),
        cont: tint([[0, "#000000"], [1, "#000000"]]),
        w: gw, h: gh, adv: adv, inkW: inkW, x0: x0, x1: x1, y0: y0, y1: y1, base: base
      });
    }
    return out;
  }

  /* ---------- Schriftlage in der Endpose ---------- */
  var BASE = { depth: 0.576, lit: 0.40, sh: 0.62, big: 1.20, over: 2, sag: 0.115, persp: 0.14, tilt: 1.0, gap: 0.055 };
  var GL = null, PLACE = null, KSCALE = 1, EXS = null, BOX = null;

  function layoutText() {
    var gl = GL, i;
    var iR = WORD.indexOf("R"), iC = WORD.indexOf("C");
    var mR = gl[iC].inkW / gl[iR].inkW;
    var EX = []; for (i = 0; i < gl.length; i++) EX.push({ x: 1, y: 1 });
    EX[iR] = { x: mR * BASE.big, y: BASE.big };
    EX[iC] = { x: BASE.big, y: BASE.big };

    var iwg = []; for (i = 0; i < gl.length; i++) iwg.push((gl[i].x1 - gl[i].x0) * EX[i].x);
    var sumIw = 0; for (i = 0; i < iwg.length; i++) sumIw += iwg[i];
    var meanIw = sumIw / iwg.length;

    var cl = project(CAM_END, [-RAD, 0, 0]), cr = project(CAM_END, [RAD, 0, 0]);
    var cityL = Math.min(cl[0], cr[0]), cityR = Math.max(cl[0], cr[0]);
    var cityPx = cityR - cityL;

    var kGuess = (cityPx / sumIw) * 0.9;
    var overPx = (BASE.over / 2) * meanIw * kGuess;
    var xL = cityL - overPx, xR = cityR + overPx;
    var span = xR - xL, midX = (xL + xR) / 2, halfSpan = span / 2;
    var sag = span * BASE.sag, persp = BASE.persp;
    var baseY = (project(CAM_END, [0, yText, 0]) || [0, H * 0.36])[1];

    function tAt(x) { var t = (x - midX) / halfSpan; return Math.max(-1.3, Math.min(1.3, t)); }
    function layout(k) {
      var gapPx = BASE.gap * FS * k, cur = xL, C = [];
      for (var j = 0; j < gl.length; j++) {
        var tE = tAt(cur), psE = 1 + persp * (1 - tE * tE);
        var hw = (iwg[j] / 2) * k * psE;
        var cx = cur + hw, t = tAt(cx), ps = 1 + persp * (1 - t * t);
        hw = (iwg[j] / 2) * k * ps; cx = cur + hw; t = tAt(cx);
        C.push({ cx: cx, t: t, ps: 1 + persp * (1 - t * t), hw: hw });
        cur = cx + hw + gapPx;
      }
      return { C: C, right: cur - gapPx };
    }
    var k = kGuess, lay = layout(k);
    for (var it = 0; it < 10; it++) {
      k *= (xR - xL) / Math.max(1, (lay.right - xL));
      lay = layout(k);
    }
    var P = [];
    for (i = 0; i < gl.length; i++) {
      var c = lay.C[i], t = c.t;
      var cy = baseY - sag * ((1 - t * t) - 0.42);
      var slope = (2 * sag * t) / halfSpan;
      P.push({ x: c.cx, y: cy, ps: c.ps, t: t, rot: Math.atan(slope) * BASE.tilt, mid: midX });
    }
    KSCALE = k; EXS = EX; PLACE = P;

    /* Umriss des ganzen Logos im Bildraum - daran haengt die Klickflaeche.
       Oben die Schriftkante, unten der vordere Stadtrand, seitlich der Ueberstand. */
    var oben = 1e9, unten = -1e9;
    for (i = 0; i < gl.length; i++) {
      var gg = gl[i], ee = P[i];
      var syi = k * ee.ps * 1.4 * EX[i].y;
      var oyi = -gg.base + (0.175 * gg.h) / EX[i].y;
      var kante = ee.y + (gg.y0 + oyi) * syi;
      if (kante < oben) oben = kante;
      var fuss = ee.y + (gg.y1 + oyi) * syi;
      if (fuss > unten) unten = fuss;
    }
    var vorn = project(CAM_END, [0, 0, RAD]);
    var links = project(CAM_END, [-RAD, 0, 0]), rechts = project(CAM_END, [RAD, 0, 0]);
    if (vorn && vorn[1] > unten) unten = vorn[1];
    BOX = {
      x1: Math.min(xL, links[0], rechts[0]),
      x2: Math.max(xR, links[0], rechts[0]),
      y1: oben,
      y2: unten
    };
  }

  /* Einflugbahnen: jeder Buchstabe kommt aus einer eigenen Richtung. */
  var ANFLUG = [
    { dx: -1.55, dy: -0.55, rot: -0.55, sc: 1.9 },
    { dx: 0.30, dy: -1.70, rot: 0.42, sc: 2.2 },
    { dx: -1.20, dy: 1.05, rot: 0.62, sc: 1.7 },
    { dx: 1.60, dy: 0.85, rot: -0.48, sc: 2.0 },
    { dx: -0.35, dy: 1.85, rot: -0.35, sc: 2.3 },
    { dx: 1.45, dy: -1.05, rot: 0.58, sc: 1.8 },
    { dx: 1.85, dy: 0.20, rot: -0.62, sc: 2.1 },
    { dx: 0.55, dy: 1.55, rot: 0.50, sc: 1.9 }
  ];

  function drawText(g, tNorm) {
    if (!PLACE || tNorm <= 0) return;
    var gl = GL, k = KSCALE, i;
    g.save();
    g.shadowColor = "rgba(250,214,140,.38)";
    g.shadowBlur = 14;

    for (var pass = 0; pass < 2; pass++) {
      for (i = 0; i < gl.length; i++) {
        var gg = gl[i], e = PLACE[i], a = ANFLUG[i % ANFLUG.length];

        /* gestaffelter Auftritt, weiches Einrasten mit leichtem Ueberschwingen */
        var start = i * 0.055;
        var u = (tNorm - start) / (1 - start * 0.6);
        u = Math.max(0, Math.min(1, u));
        var e1 = 1 - Math.pow(1 - u, 3.2);
        var over = Math.sin(u * Math.PI) * 0.055 * (1 - u);
        var vis = Math.min(1, u * 4.5);
        if (vis <= 0) continue;

        var offX = a.dx * W * (1 - e1);
        var offY = a.dy * H * (1 - e1);
        var addRot = a.rot * (1 - e1);
        var addSc = 1 + (a.sc - 1) * (1 - e1) + over;

        var kk = k * e.ps * addSc, rot = e.rot + addRot;
        var cap = FS * 0.72 * kk * 1.4, depth = cap * BASE.depth, ST = 54;
        var dx = depth * 0.32 / ST, dy = depth * 0.86 / ST;
        var sx = kk * EXS[i].x, sy = kk * 1.4 * EXS[i].y;

        g.save();
        g.globalAlpha = vis;
        g.translate(e.x + offX, e.y + offY);
        g.rotate(rot);
        g.scale(sx, sy);
        var ox = -(gg.x0 + (gg.x1 - gg.x0) / 2), oy = -gg.base + (0.175 * gg.h) / EXS[i].y;
        if (pass === 0) {
          g.shadowBlur = 0;
          g.save();
          g.globalCompositeOperation = "multiply";
          g.globalAlpha = Math.min(1, BASE.sh * 1.15) * vis;
          try { g.filter = "blur(" + (18 / sy) + "px)"; } catch (err) {}
          g.drawImage(gg.cont, ox + (dx * ST * 2.6) / sx, oy + (dy * ST * 2.6) / sy);
          g.restore();
          for (var st = ST; st >= 1; st--)
            g.drawImage(st > ST * BASE.lit ? gg.dark : gg.side, ox + (dx * st) / sx, oy + (dy * st) / sy);
        } else {
          g.drawImage(gg.face, ox, oy);
        }
        g.restore();
      }
      g.shadowBlur = 0;
    }
    g.restore();
  }

  /* ---------- Agenten ---------- */
  var AG = new Image(), AG_OK = false;
  AG.onload = function () { AG_OK = true; };
  AG.src = "/agenten.png";
  var agCache = null;

  function drawAgents(g, alpha) {
    if (!AG_OK || !PLACE || alpha <= 0.01) return;
    var gl = GL, k = KSCALE, i;
    var io = WORD.indexOf("o"), go = gl[io], eo = PLACE[io];
    var syO = k * eo.ps * 1.4 * EXS[io].y;
    var agH = (go.y1 - go.y0) * syO;
    var agW = agH * (AG.width / AG.height);

    var low = -1e9;
    for (i = 0; i < gl.length; i++) {
      var gg = gl[i], ee = PLACE[i];
      if (Math.abs(ee.t) > 0.42) continue;
      var syI = k * ee.ps * 1.4 * EXS[i].y;
      var oyI = -gg.base + (0.175 * gg.h) / EXS[i].y;
      var bt = ee.y + (gg.y1 + oyI) * syI;
      if (bt > low) low = bt;
    }
    var capMid = FS * 0.72 * k * eo.ps * 1.4;
    var agX = PLACE[0].mid, agY = low + capMid * BASE.depth * 0.86 + agH * 0.14;

    if (!agCache || agCache.w !== Math.round(agW)) {
      function agTint(stops) {
        var c = document.createElement("canvas");
        c.width = Math.max(2, Math.round(agW)); c.height = Math.max(2, Math.round(agH));
        var x = c.getContext("2d");
        x.drawImage(AG, 0, 0, c.width, c.height);
        x.globalCompositeOperation = "source-in";
        var gg2 = x.createLinearGradient(0, 0, 0, c.height);
        for (var t = 0; t < stops.length; t++) gg2.addColorStop(stops[t][0], stops[t][1]);
        x.fillStyle = gg2; x.fillRect(0, 0, c.width, c.height);
        return c;
      }
      agCache = {
        w: Math.round(agW),
        face: agTint([[0, "#FFF7E1"], [0.30, "#F0D091"], [0.415, "#FFFFFF"],
                      [0.425, "#DDB463"], [0.70, "#B98F3B"], [0.72, "#F0D398"], [1, "#FFF3D8"]]),
        side: agTint([[0, "#F7E3B4"], [0.5, "#DCB76A"], [1, "#BE9544"]]),
        back: agTint([[0, "#AC8836"], [0.5, "#8B6C27"], [1, "#6B531F"]]),
        dark: agTint([[0, "#000000"], [1, "#000000"]])
      };
    }

    var agD = agH * 0.11, ST2 = 34;
    var adx = agD * 0.32 / ST2, ady = agD * 0.86 / ST2;

    g.save();
    g.globalAlpha = alpha;
    g.translate(agX, agY);
    g.save();
    g.globalCompositeOperation = "multiply";
    g.globalAlpha = 0.78 * alpha;
    try { g.filter = "blur(" + (agH * 0.05) + "px)"; } catch (e2) {}
    g.drawImage(agCache.dark, -agW / 2 + adx * ST2 * 2.4, ady * ST2 * 2.4, agW, agH);
    g.restore();
    for (var st2 = ST2; st2 >= 1; st2--)
      g.drawImage(st2 > ST2 * 0.42 ? agCache.back : agCache.side, -agW / 2 + adx * st2, ady * st2, agW, agH);
    g.drawImage(agCache.face, -agW / 2, 0, agW, agH);
    g.restore();
  }

  /* ---------- Weltall und Wolken (die Kugel selbst macht erde.js) ---------- */
  var sterne = (function () {
    var r = rng(7714), a = [];
    for (var i = 0; i < 320; i++)
      a.push({ x: r(), y: r(), s: 0.4 + r() * 1.5, h: 0.25 + r() * 0.75, ph: r() * 6.28 });
    return a;
  })();

  var wolken = (function () {
    var r = rng(31337), a = [];
    for (var i = 0; i < 46; i++)
      a.push({ x: r(), y: r(), r: 0.16 + r() * 0.42, t0: r(), warm: r() < 0.42, s: 0.6 + r() * 0.9 });
    return a;
  })();

  function drawSterne(g, alpha, t, drift, px, py) {
    if (alpha <= 0.01) return;
    g.save();
    g.globalAlpha = alpha;
    for (var i = 0; i < sterne.length; i++) {
      var s = sterne[i];
      var x = ((s.x + drift * (0.2 + s.h * 0.8)) % 1 + 1) % 1;
      var fl = 0.72 + 0.28 * Math.sin(t * 1.7 + s.ph);
      g.fillStyle = "rgba(226,236,250," + (s.h * fl).toFixed(3) + ")";
      g.fillRect(x * (W + 2 * px) - px, s.y * (H + 2 * py) - py, s.s, s.s);
    }
    g.restore();
  }

  /* Wolkenschichten beim Eintauchen. waerme 0 = Tageslicht, 1 = Bernstein. */
  function drawWolken(g, fort, alpha, waerme) {
    if (alpha <= 0.01) return;
    function misch(k, w) {
      var kalt = [222, 234, 248], warm = [255, 214, 164], o = [];
      for (var i = 0; i < 3; i++) o.push(Math.round(kalt[i] * (1 - w) + warm[i] * w * (k ? 1 : 0.92)));
      return o.join(",");
    }
    g.save();
    g.globalAlpha = alpha;
    g.globalCompositeOperation = "lighter";
    for (var i = 0; i < wolken.length; i++) {
      var c = wolken[i];
      var u = (fort * c.s + c.t0) % 1;
      var z = Math.pow(u, 2.2);
      var sk = 0.10 + z * 4.6;
      var a = Math.sin(u * Math.PI) * 0.5;
      if (a <= 0.004) continue;
      var cx = W / 2 + (c.x - 0.5) * W * sk * 1.25;
      var cy = H * 0.52 + (c.y - 0.5) * H * sk * 1.25;
      var rr2 = c.r * Math.min(W, H) * sk;
      var col = misch(c.warm, waerme);
      var gr = g.createRadialGradient(cx, cy, 0, cx, cy, rr2);
      gr.addColorStop(0, "rgba(" + col + "," + (a * 0.40).toFixed(3) + ")");
      gr.addColorStop(0.45, "rgba(" + col + "," + (a * 0.14).toFixed(3) + ")");
      gr.addColorStop(1, "rgba(" + col + ",0)");
      g.fillStyle = gr;
      g.beginPath(); g.arc(cx, cy, rr2, 0, 6.2832); g.fill();
    }
    g.restore();
  }

  /* Seitlicher Nebel am Rand des Sichtfelds. */
  function drawNebel(g, staerke, t, waerme) {
    if (staerke <= 0.01) return;
    var kern = waerme > 0.5 ? "255,226,186" : "226,238,252";
    var saum = waerme > 0.5 ? "255,206,140" : "200,222,248";
    g.save();
    g.globalCompositeOperation = "lighter";
    g.globalAlpha = staerke;
    for (var s = -1; s <= 1; s += 2) {
      for (var i = 0; i < 5; i++) {
        var ph = (t * (0.85 + i * 0.22) + i * 0.31) % 1;
        var y = H * (1.15 - ph * 1.5);
        var br = W * (0.10 + 0.09 * ((i + 1) % 3));
        var x = W / 2 + s * (W * 0.40 + i * W * 0.045);
        var gr = g.createRadialGradient(x, y, 0, x, y, br);
        var a = Math.sin(ph * Math.PI) * 0.28;
        gr.addColorStop(0, "rgba(" + kern + "," + (a * 0.5).toFixed(3) + ")");
        gr.addColorStop(1, "rgba(" + saum + ",0)");
        g.fillStyle = gr;
        g.beginPath(); g.ellipse(x, y, br, br * 2.1, 0, 0, 6.2832); g.fill();
      }
    }
    g.restore();
  }

  /* ---------- Zeitachse ----------
     orbit     hoher Orbit, Flug nach vorne, die Erde zieht auf uns zu
     sinkflug  wir sinken, der Blick legt sich nach unten
     wolken    Eintritt in die Wolken; hier geht das Bild ins Brandkit ueber
     stadt     nach den Wolken wird die Sicht auf RepoCity frei
     schrift   der Schriftzug faehrt ein                                   */
  var T = { orbit: 2.4, sinkflug: 4.8, wolken: 7.2, stadt: 10.3, schrift: 11.9 };
  var DAUER = T.schrift;

  function ease(a, b, x) { return Math.max(0, Math.min(1, (x - a) / (b - a))); }
  function smooth(x) { return x * x * (3 - 2 * x); }
  function inOut(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }

  function frame(t) {
    var g = ctx;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, cv.width, cv.height);
    g.save();
    var sc = Math.min(cv.width / W, cv.height / H);
    var px = Math.max(0, (cv.width / sc - W) / 2);
    var py = Math.max(0, (cv.height / sc - H) / 2);
    g.setTransform(sc, 0, 0, sc, (cv.width - W * sc) / 2, (cv.height - H * sc) / 2);

    /* Die Erde laeuft von Anfang an bis kurz hinter den Wolkeneintritt */
    var uErde = ease(0, T.wolken, t);
    var erdSicht = 1 - smooth(ease(T.wolken - 1.1, T.wolken - 0.1, t));
    if (erde) {
      if (erdSicht > 0.005) {
        erdeCv.style.opacity = erdSicht.toFixed(3);
        erde.render(uErde);
      } else if (erdeCv.style.opacity !== "0") {
        erdeCv.style.opacity = "0";
      }
    }

    /* Das Brandkit springt erst beim Wolkeneintritt an */
    var waerme = smooth(ease(T.wolken - 0.9, T.wolken + 0.5, t));
    var grundHell = smooth(ease(T.wolken - 0.4, T.stadt - 0.9, t));
    drawGround(g, grundHell, px, py, 1 - erdSicht);

    /* Der Grund in der Wolke: erst Tageslicht, dann kippt er ins Bernstein und
       dunkelt zur Markenszene ab. So geht es nie durch Schwarz. */
    var wolkenGrund = smooth(ease(T.wolken - 1.7, T.wolken - 0.5, t)) *
                      (1 - smooth(ease(T.wolken + 0.8, T.stadt - 0.4, t)));
    if (wolkenGrund > 0.004) {
      var kalt = [206, 216, 230], warmT = [104, 68, 30], mi = [];
      for (var mk = 0; mk < 3; mk++)
        mi.push(Math.round(kalt[mk] * (1 - waerme) + warmT[mk] * waerme));
      g.save();
      g.globalAlpha = wolkenGrund;
      g.fillStyle = "rgb(" + mi.join(",") + ")";
      g.fillRect(-px, -py, W + 2 * px, H + 2 * py);
      g.restore();
    }


    /* Wolken: ziehen nach aussen vorbei, waehrend wir hindurchtauchen */
    var wAlpha = smooth(ease(T.sinkflug - 0.9, T.wolken - 1.0, t)) *
                 (1 - smooth(ease(T.stadt - 1.5, T.stadt - 0.05, t)));
    drawWolken(g, ease(T.sinkflug - 1.0, T.stadt, t) * 1.30, wAlpha, waerme);

    /* Stadt: Kamera legt sich aus der Steilsicht in die Endpose */
    var pStadt = ease(T.wolken + 0.9, T.stadt, t);
    if (pStadt > 0) {
      var q = inOut(pStadt);
      var pitch = (74 * (1 - q) + 30 * q) * Math.PI / 180;
      var dist = 9400 * (1 - q) + DIST_END * q;
      var cam = (pStadt >= 1) ? CAM_END : makeCam(pitch, dist);
      drawCity(g, cam, smooth(pStadt));
    }

    var nStaerke = smooth(ease(T.sinkflug - 0.6, T.wolken - 0.8, t)) *
                   (1 - smooth(ease(T.stadt - 1.0, T.stadt + 0.2, t)));
    drawNebel(g, nStaerke * 0.85, t, waerme);

    if (grundHell > 0.02) drawVignette(g, px, py);

    var pText = ease(T.stadt - 0.15, T.schrift, t);
    if (pText > 0) {
      drawText(g, pText);
      drawAgents(g, smooth(ease(T.schrift - 0.45, T.schrift, t)));
    }

    g.restore();
  }

  /* ---------- Ablauf ---------- */
  var start = null, laeuft = true, fertig = false;
  /* Die Fahrt kommt je Sitzung einmal. Wer die Seite noch einmal aufruft,
     landet ohne Wartezeit in der Endpose. */
  var schonGesehen = false;
  try { schonGesehen = sessionStorage.getItem("rc_anflug") === "1"; } catch (e) {}
  var sparsam = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function passeAn() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = Math.round(cv.clientWidth * dpr);
    cv.height = Math.round(cv.clientHeight * dpr);
    if (erde) erde.groesse();
    legeTor();
    if (fertig || !laeuft) frame(DAUER);
  }

  /* Das Tor liegt genau auf dem Logo - ein Klick irgendwo darauf fuehrt weiter. */
  function legeTor() {
    var tor = document.getElementById("tor");
    if (!tor || !BOX) return;
    var bw = cv.clientWidth || 1, bh = cv.clientHeight || 1;
    var s = Math.min(bw / W, bh / H);
    var ox = (bw - W * s) / 2, oy = (bh - H * s) / 2;
    var rand = 24 * s;
    tor.style.left = (ox + BOX.x1 * s - rand) + "px";
    tor.style.top = (oy + BOX.y1 * s - rand) + "px";
    tor.style.width = ((BOX.x2 - BOX.x1) * s + 2 * rand) + "px";
    tor.style.height = ((BOX.y2 - BOX.y1) * s + 2 * rand) + "px";
  }

  /* Der Anflug fuehrt auf die Startseite hinunter, NICHT in die Oberflaeche:
     zwei Sekunden nach der Ankunft von allein, auf Klick oder Taste sofort.
     In die Oberflaeche geht es erst von der Startseite aus, ueber die
     Kopfleiste oder den Knopf (Daniel, 14.09.2026). */
  var gegangen = false;
  function weiter() {
    if (gegangen) return;
    gegangen = true;
    var ziel = document.getElementById("weiter");
    if (ziel && ziel.scrollIntoView) {
      ziel.scrollIntoView({ behavior: "smooth", block: "start" });
      document.body.classList.add("gescrollt");
    } else {
      window.location.hash = "#weiter";
    }
  }

  function ende() {
    if (fertig) return;
    fertig = true; laeuft = false;
    if (erdeCv) erdeCv.style.opacity = "0";
    try { sessionStorage.setItem("rc_anflug", "1"); } catch (e) {}
    frame(DAUER);
    document.body.classList.add("angekommen");
    if (!schonGesehen && !sparsam) setTimeout(weiter, 2000);
  }

  function wegklicken() {
    if (schonGesehen || sparsam) { ende(); return; }
    ende();
    weiter();
  }

  function schleife(ts) {
    if (!laeuft) return;
    if (start === null) start = ts;
    var t = (ts - start) / 1000;
    if (t >= DAUER) { ende(); return; }
    frame(t);
    requestAnimationFrame(schleife);
  }

  function los() {
    GL = glyphSet(0.12);
    layoutText();
    if (erdeCv) {
      try { erde = erstelleErde(erdeCv); } catch (e) { erde = null; }
    }
    passeAn();
    if (sparsam || schonGesehen) { ende(); return; }
    requestAnimationFrame(schleife);
  }

  window.addEventListener("resize", passeAn);
  window.addEventListener("keydown", function (e) {
    if (e.key === "Escape" || e.key === " ") wegklicken();
  });
  cv.addEventListener("pointerdown", wegklicken);

  if (document.fonts && document.fonts.load) {
    document.fonts.load("700 230px Outfit").then(los).catch(los);
  } else {
    setTimeout(los, 300);
  }
})();
