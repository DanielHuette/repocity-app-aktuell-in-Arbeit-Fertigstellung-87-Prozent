/* Die Erde als echte Kugel: Textur aus Kuestenlinien, Wolkenschicht, Atmosphaere.
   Der Flug geht nach vorne - die Kamera laeuft auf ihrer Bahn voraus, die
   Oberflaeche zieht dabei auf uns zu und unter uns hindurch. */

import * as THREE from "three";

export function erstelleErde(cv) {
  var renderer = new THREE.WebGLRenderer({ canvas: cv, alpha: true, antialias: true });
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  var szene = new THREE.Scene();
  var kamera = new THREE.PerspectiveCamera(53, 1, 0.001, 100);

  var lader = new THREE.TextureLoader();
  var erdKarte = lader.load("/erde.jpg");
  var wolkenKarte = lader.load("/wolken.png");
  if ("SRGBColorSpace" in THREE) {
    erdKarte.colorSpace = THREE.SRGBColorSpace;
    wolkenKarte.colorSpace = THREE.SRGBColorSpace;
  }
  erdKarte.anisotropy = renderer.capabilities.getMaxAnisotropy();

  var R = 1;

  /* Kugel mit eigener Beleuchtung: weiches Tageslicht, harter Terminator,
     Nachtseite tief blau statt schwarz. */
  var erde = new THREE.Mesh(
    new THREE.SphereGeometry(R, 128, 96),
    new THREE.ShaderMaterial({
      uniforms: {
        karte: { value: erdKarte },
        sonne: { value: new THREE.Vector3(0.55, 0.28, 0.79) }
      },
      vertexShader: [
        "varying vec2 vUv; varying vec3 vN;",
        "void main(){ vUv = uv; vN = normalize(mat3(modelMatrix) * normal);",
        "gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }"
      ].join("\n"),
      fragmentShader: [
        "uniform sampler2D karte; uniform vec3 sonne;",
        "varying vec2 vUv; varying vec3 vN;",
        "void main(){",
        "  vec3 c = texture2D(karte, vUv).rgb;",
        "  float d = dot(normalize(vN), normalize(sonne));",
        "  float tag = smoothstep(-0.22, 0.30, d);",
        "  vec3 nacht = c * vec3(0.10, 0.13, 0.24) * 0.55;",
        "  vec3 licht = c * (0.30 + 1.05 * max(d, 0.0));",
        "  vec3 o = mix(nacht, licht, tag);",
        "  float saum = smoothstep(0.34, -0.02, abs(d - 0.03));",
        "  o += vec3(0.42, 0.24, 0.10) * saum * 0.16;",
        "  gl_FragColor = vec4(o, 1.0);",
        "}"
      ].join("\n")
    })
  );
  szene.add(erde);

  var wolken = new THREE.Mesh(
    new THREE.SphereGeometry(R * 1.006, 96, 64),
    new THREE.ShaderMaterial({
      uniforms: {
        karte: { value: wolkenKarte },
        sonne: { value: new THREE.Vector3(0.55, 0.28, 0.79) },
        staerke: { value: 0.88 }
      },
      transparent: true,
      depthWrite: false,
      vertexShader: [
        "varying vec2 vUv; varying vec3 vN;",
        "void main(){ vUv = uv; vN = normalize(mat3(modelMatrix) * normal);",
        "gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }"
      ].join("\n"),
      fragmentShader: [
        "uniform sampler2D karte; uniform vec3 sonne; uniform float staerke;",
        "varying vec2 vUv; varying vec3 vN;",
        "void main(){",
        "  float a = texture2D(karte, vUv).a;",
        "  float d = dot(normalize(vN), normalize(sonne));",
        "  float tag = smoothstep(-0.18, 0.32, d);",
        "  vec3 c = mix(vec3(0.10,0.13,0.22), vec3(1.0,0.99,0.97), tag);",
        "  gl_FragColor = vec4(c, a * staerke * (0.30 + 0.70 * tag));",
        "}"
      ].join("\n")
    })
  );
  szene.add(wolken);

  /* Atmosphaere: leuchtet zum Rand hin auf, von innen wie von aussen sichtbar. */
  var luft = new THREE.Mesh(
    new THREE.SphereGeometry(R * 1.035, 96, 64),
    new THREE.ShaderMaterial({
      uniforms: { sonne: { value: new THREE.Vector3(0.55, 0.28, 0.79) } },
      transparent: true,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      vertexShader: [
        "varying vec3 vN; varying vec3 vP;",
        "void main(){ vN = normalize(normalMatrix * normal);",
        "  vec4 mv = modelViewMatrix * vec4(position,1.0); vP = mv.xyz;",
        "  gl_Position = projectionMatrix * mv; }"
      ].join("\n"),
      fragmentShader: [
        "uniform vec3 sonne; varying vec3 vN; varying vec3 vP;",
        "void main(){",
        "  float f = pow(1.0 - abs(dot(normalize(vN), normalize(vP))), 2.6);",
        "  float d = max(dot(normalize(vN), normalize(sonne)) * -1.0, 0.0);",
        "  vec3 c = mix(vec3(0.22,0.44,0.86), vec3(0.60,0.78,1.0), f);",
        "  gl_FragColor = vec4(c, f * 0.85 * (0.25 + 0.75 * d));",
        "}"
      ].join("\n")
    })
  );
  szene.add(luft);

  /* Sternenfeld: gehoert in die Szene, damit die Wolkenebene darueber liegen kann */
  (function () {
    var n = 1400, pos = new Float32Array(n * 3), hel = new Float32Array(n);
    var seed = 20260904;
    function zufall() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
    for (var i = 0; i < n; i++) {
      var u = zufall() * 2 - 1, ph = zufall() * Math.PI * 2, r = 60;
      var si = Math.sqrt(1 - u * u);
      pos[i*3] = r * si * Math.cos(ph);
      pos[i*3+1] = r * u;
      pos[i*3+2] = r * si * Math.sin(ph);
      hel[i] = 0.25 + zufall() * 0.75;
    }
    var geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("hel", new THREE.BufferAttribute(hel, 1));
    var mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false,
      vertexShader: [
        "attribute float hel; varying float vH;",
        "void main(){ vH = hel; vec4 mv = modelViewMatrix * vec4(position,1.0);",
        "  gl_PointSize = 1.0 + hel * 1.6; gl_Position = projectionMatrix * mv; }"
      ].join("\n"),
      fragmentShader: [
        "varying float vH;",
        "void main(){ gl_FragColor = vec4(0.886,0.925,0.980, vH); }"
      ].join("\n")
    });
    szene.add(new THREE.Points(geo, mat));
  })();

  function groesse() {
    var b = cv.clientWidth || 1, h = cv.clientHeight || 1;
    renderer.setSize(b, h, false);
    kamera.aspect = b / h;
    /* senkrechter Bildwinkel wie beim Logo, damit der Eindruck durchgehend bleibt */
    kamera.fov = 53;
    kamera.updateProjectionMatrix();
  }

  /* u = 0 .. 1 ueber die ganze Erdphase.
     Erst eine kurze Totale von aussen, dann das Einschwenken auf Bahnhoehe und die
     Fahrt nach vorne, danach fliessend in den Sinkflug. Zum Schluss wird die
     Wolkendecke dichter, damit wir durch Weiss abtauchen und nicht ueber offenes Land. */
  function render(u) {
    var q = Math.max(0, Math.min(1, u));

    function weich(x) {
      x = Math.max(0, Math.min(1, x));
      return x * x * x * (x * (x * 6 - 15) + 10);
    }
    function zwischen(a, b, x) { return a + (b - a) * x; }

    /* Eine einzige, durchgehende Abwaertsbewegung: sie faellt zuerst zuegig auf
       Bahnhoehe, laeuft dort langsamer weiter und wird zum Abtauchen wieder
       schneller. Die Sinkrate wird nie null - deshalb kein zweiter Abstieg. */
    function rampe(x) {
      x = Math.max(0, Math.min(1, x));
      return 0.75 * (x * x * (3 - 2 * x)) + 0.25 * x;
    }
    var hoehe = R * (3.70 - 2.15 * rampe(q / 0.55) - 0.534 * rampe((q - 0.50) / 0.50));

    /* Der Blickwinkel haengt an der Hoehe: zuerst die ganze Kugel im Bild,
       dann der Horizont knapp ueber der Bildmitte, zuletzt der Sinkflug. */
    var randWinkel = Math.asin(Math.min(1, R / hoehe)) * 180 / Math.PI;
    var versatz = zwischen(-randWinkel, -9, weich(q / 0.35));
    var horizont = Math.max(5, Math.min(88, 90 - randWinkel - versatz));
    var legen = weich((q - 0.45) / 0.55);
    var neigung = zwischen(horizont, 82, legen) * Math.PI / 180;

    var bahn = 0.20 + q * 1.30;

    var radial = new THREE.Vector3(Math.sin(bahn), 0.20, Math.cos(bahn)).normalize();
    var tang = new THREE.Vector3(Math.cos(bahn), 0.0, -Math.sin(bahn));
    tang.addScaledVector(radial, -tang.dot(radial)).normalize();

    kamera.position.copy(radial).multiplyScalar(hoehe);
    var blick = tang.clone().multiplyScalar(Math.cos(neigung))
                    .addScaledVector(radial, -Math.sin(neigung)).normalize();

    /* Die Oben-Richtung wird aus der Bahnnormalen gebildet und steht damit immer
       senkrecht auf der Blickrichtung. Sonst kippt das Bild im ersten Moment,
       wenn der Blick fast senkrecht nach unten geht. */
    var seit = new THREE.Vector3().crossVectors(tang, radial).normalize();
    kamera.up.copy(new THREE.Vector3().crossVectors(seit, blick).normalize());
    kamera.lookAt(kamera.position.clone().add(blick));

    /* die Erde dreht sich unter uns weiter */
    erde.rotation.y = -0.22 - q * 0.20;
    wolken.rotation.y = -0.30 - q * 0.17;

    /* letzter Abschnitt: die Wolken schliessen sich */
    wolken.material.uniforms.staerke.value = zwischen(0.88, 2.4, weich((q - 0.70) / 0.30));

    renderer.render(szene, kamera);
  }

  groesse();
  return { render: render, groesse: groesse };
}
