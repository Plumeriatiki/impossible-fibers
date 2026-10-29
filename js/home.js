// Home page scene. A cloud of particles ("proteins") sits behind the page; each section names a shape
// (data-shape) and which side its text is on (data-side). Scrolling turns the camera around the cloud and
// reshapes it into that section's step:
//   0 cloud · 1 droplets (store) · 2 droplets in a line (sort) · 3 twisted fiber (trigger & align)
//   4 hollow tube (Glass Noodle) · 5 nonwoven mesh (robotic touch) · 6 shell (open science)
//   7 ring (projects wheel) · 8 cloud (contact)
// The blend between two shapes runs on the GPU (vertex shader); JavaScript only swaps the pair of shapes
// when the section changes. Illustrative, not a simulation. Needs three.js (r128) loaded first.
(() => {
  const root = document.documentElement;
  const canvas = document.getElementById("scene");
  const secs = [...document.querySelectorAll("[data-shape]")];
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const small = innerWidth < 760;
  const modest = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;
  const N = small ? 3000 : modest ? 4000 : 6500;

  // ── reveal text and mark the current section, even without WebGL ──
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) e.target.classList.add("in"); }), {threshold: .25});
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));
  const dots = document.querySelector(".dots");
  secs.forEach(() => dots.appendChild(document.createElement("i")));

  function progress(){
    const y = scrollY; let i = 0;
    for (let k = 0; k < secs.length; k++) if (secs[k].offsetTop <= y + 1) i = k;
    const s = secs[i], span = Math.max(1, s.offsetHeight - (s.classList.contains("wheel") ? innerHeight : 0));
    return {i, frac: Math.min(1, Math.max(0, (y - s.offsetTop) / span))};
  }

  // ── the wheel: project names on a turning cylinder, driven by scroll inside its pinned section ──
  const items = [...document.querySelectorAll(".ring a")], STEP = 34;
  function wheel(frac){
    const R = innerHeight * .42, turn = frac * (items.length - 1) * STEP;
    items.forEach((a, n) => {
      const ang = n * STEP - turn;
      a.style.transform = `rotateX(${-ang}deg) translateZ(${R}px)`;
      a.style.opacity = Math.max(0, Math.cos(ang * Math.PI / 180) ** 3).toFixed(3);
      const front = Math.abs(ang) < STEP / 2;
      a.style.pointerEvents = front ? "auto" : "none";
      a.tabIndex = front ? 0 : -1;
    });
  }
  wheel(0);

  const ui = () => {
    const {i, frac} = progress();
    [...dots.children].forEach((d, n) => d.classList.toggle("on", n === i));
    if (secs[i].classList.contains("wheel")) wheel(frac);
    return {i, frac};
  };

  // ── WebGL, with a graceful fallback ──
  if (!window.THREE) { root.classList.add("no-gl"); addEventListener("scroll", ui, {passive: true}); return; }
  let renderer;
  try { renderer = new THREE.WebGLRenderer({canvas, antialias: !small}); }
  catch (e) { root.classList.add("no-gl"); addEventListener("scroll", ui, {passive: true}); return; }

  // ── target shapes ──
  const rnd = Math.random, TAU = Math.PI * 2;
  const gauss = () => { let u = 0, v = 0; while (!u) u = rnd(); while (!v) v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * v); };
  const ss = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  const sph = (r, shell) => { let x, y, z, d; do { x = gauss(); y = gauss(); z = gauss(); d = Math.hypot(x, y, z); } while (!d);
    const rr = shell ? r * (0.9 + 0.1 * rnd()) : r * Math.cbrt(rnd()); return [x / d * rr, y / d * rr, z / d * rr]; };

  // particle i keeps droplet k = i % K from store → sort → fiber → tube, so droplets line up, then stretch into the fiber
  const K = 7, GAP = 4.4 / (K - 1);
  const ringC = [...Array(K)].map((_, k) => { const a = k / K * TAU; return [Math.cos(a) * 1.7 + gauss() * .2, Math.sin(a) * 1.15 + gauss() * .2, gauss() * .6]; });
  const fiberX = new Float32Array(N);
  for (let i = 0; i < N; i++) fiberX[i] = -2.2 + (i % K) * GAP + (rnd() - .5) * GAP;
  const F = 150, mesh = [...Array(F)].map(() => ({cx: (rnd() - .5) * 4.2, cy: (rnd() - .5) * 3.4, a: rnd() * Math.PI, len: 1.1 + rnd() * 2.2, bend: (rnd() - .5) * .5}));

  const shapeFns = [
    i => sph(2.4, false),
    i => { const c = ringC[i % K], p = sph(.5, rnd() < .75); return [c[0] + p[0], c[1] + p[1], c[2] + p[2]]; },
    i => { const x = -2.2 + (i % K) * GAP, p = sph(.3, rnd() < .75); return [x + p[0], p[1], p[2]]; },
    i => { const s = Math.floor(rnd() * 7), x = fiberX[i], a = s / 7 * TAU + x * 1.15, r = .3 + gauss() * .03; return [x, Math.cos(a) * r, Math.sin(a) * r]; },
    i => { const a = rnd() * TAU, r = .8 + rnd() * .06, x = fiberX[i] * .85, tip = .45;
           return [x * Math.cos(tip) - Math.cos(a) * r * Math.sin(tip), x * Math.sin(tip) + Math.cos(a) * r * Math.cos(tip), Math.sin(a) * r]; },
    i => { const f = mesh[i % F], t = rnd() - .5, dx = Math.cos(f.a), dy = Math.sin(f.a), b = f.bend * (1 - 4 * t * t);
           return [f.cx + dx * t * f.len - dy * b, f.cy + dy * t * f.len + dx * b, (rnd() - .5) * .14]; },
    i => sph(2.1, true),
    i => { const a = rnd() * TAU, b = rnd() * TAU, R = 2.4, r = .15 + rnd() * .12; return [(R + r * Math.cos(b)) * Math.cos(a), r * Math.sin(b) * 1.4, (R + r * Math.cos(b)) * Math.sin(a)]; },
  ];
  const hex = h => new THREE.Color(h);
  const palFns = [
    i => (i % 3 ? hex("#0E7C7B") : hex("#7FCFCB")),
    i => (i % K % 2 ? hex("#0E9C9A") : hex("#7FCFCB")),
    i => (i % K % 2 ? hex("#0E9C9A") : hex("#7FCFCB")),
    i => (i % 5 ? hex("#EA580C") : hex("#F6A35C")),
    i => (i % 4 ? hex("#BFEFF0") : hex("#7FCFCB")),
    i => (i % 3 ? hex("#E8B27A") : hex("#EA580C")),
    i => (i % 2 ? hex("#7FCFCB") : hex("#E8B27A")),
    i => (i % 2 ? hex("#EA580C") : hex("#7FCFCB")),
  ];
  const ANGLE = .85;                                   // camera turn per section
  const shapeOf = secs.map(s => +s.dataset.shape);
  const cache = {};
  function shape(k){                                   // positions, turned to face the camera at section k
    if (cache["s" + k]) return cache["s" + k];
    const fnIdx = k === 8 ? 0 : k, a = new Float32Array(N * 3);
    const th = k * ANGLE + (k === 4 ? .75 : 0), c = Math.cos(th), sn = Math.sin(th);
    for (let i = 0; i < N; i++) { const p = shapeFns[fnIdx](i); a[i * 3] = p[0] * c + p[2] * sn; a[i * 3 + 1] = p[1]; a[i * 3 + 2] = -p[0] * sn + p[2] * c; }
    return (cache["s" + k] = a);
  }
  function colors(k){
    if (cache["c" + k]) return cache["c" + k];
    const fnIdx = k === 8 ? 0 : k, a = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) { const c = palFns[fnIdx](i); a[i * 3] = c.r; a[i * 3 + 1] = c.g; a[i * 3 + 2] = c.b; }
    return (cache["c" + k] = a);
  }

  // ── scene ──
  const PR = Math.min(small ? 1.5 : 2, devicePixelRatio || 1);
  renderer.setPixelRatio(PR);
  renderer.setClearColor(0x0b0f12, 1);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, .1, 100);
  const geo = new THREE.BufferGeometry();
  const attr = (n, size) => new THREE.BufferAttribute(new Float32Array(N * size), size);
  geo.setAttribute("position", attr("position", 3));
  geo.setAttribute("posB", attr("posB", 3));
  geo.setAttribute("colA", attr("colA", 3));
  geo.setAttribute("colB", attr("colB", 3));
  const ph = new Float32Array(N); for (let i = 0; i < N; i++) ph[i] = rnd() * TAU;
  geo.setAttribute("phase", new THREE.BufferAttribute(ph, 1));
  const mat = new THREE.ShaderMaterial({
    uniforms: {uMix: {value: 0}, uTime: {value: 0}, uSize: {value: small ? 4.6 : 4.2}, uJit: {value: calm ? 0 : .02}, uPR: {value: PR}},
    vertexShader: `
      attribute vec3 posB; attribute vec3 colA; attribute vec3 colB; attribute float phase;
      uniform float uMix, uTime, uSize, uJit, uPR; varying vec3 vCol;
      void main(){
        vec3 p = mix(position, posB, uMix);
        p += uJit * vec3(sin(uTime * 1.3 + phase), sin(uTime * 1.1 + phase * 1.7), sin(uTime * .9 + phase * 2.3));
        vCol = mix(colA, colB, uMix);
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        gl_Position = projectionMatrix * mv;
        gl_PointSize = uSize * uPR * (10.0 / -mv.z);
      }`,
    fragmentShader: `
      varying vec3 vCol;
      void main(){
        float d = length(gl_PointCoord - .5);
        if (d > .5) discard;
        float a = smoothstep(.5, .0, d);
        gl_FragColor = vec4(vCol * a, a);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending
  });
  scene.add(new THREE.Points(geo, mat));

  let pair = "";
  function setPair(i){
    const a = shapeOf[i], b = shapeOf[Math.min(i + 1, secs.length - 1)];
    if (pair === a + ">" + b) return;
    pair = a + ">" + b;
    geo.attributes.position.array.set(shape(a)); geo.attributes.posB.array.set(shape(b));
    geo.attributes.colA.array.set(colors(a)); geo.attributes.colB.array.set(colors(b));
    for (const n of ["position", "posB", "colA", "colB"]) geo.attributes[n].needsUpdate = true;
  }

  function resize(){ renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
  addEventListener("resize", resize); resize();

  const sideX = {left: 2.9, right: -2.9, center: 0};
  let offX = small ? 0 : 2.9, last = performance.now();
  const t0 = last;
  function frame(now){
    const t = (now - t0) / 1000, dt = Math.min(.1, (now - last) / 1000); last = now;
    const {i, frac} = ui();
    setPair(i);
    const isWheel = secs[i].classList.contains("wheel");
    mat.uniforms.uMix.value = isWheel ? ss(.82, 1, frac) : ss(.35, .92, frac);
    mat.uniforms.uTime.value = t;

    // the camera turns as you scroll
    const sPos = i + frac, theta = sPos * ANGLE + (calm ? 0 : .12 * Math.sin(t * .25)), phi = .28 * Math.sin(sPos * .9 + .4);
    const R = small ? 13.5 : 9.5;
    camera.position.set(R * Math.sin(theta) * Math.cos(phi), R * Math.sin(phi), R * Math.cos(theta) * Math.cos(phi));
    camera.lookAt(0, 0, 0);
    const f = mat.uniforms.uMix.value;
    const want = small ? 0 : sideX[secs[i].dataset.side] * (1 - f) + sideX[(secs[i + 1] || secs[i]).dataset.side] * f;
    offX += (want - offX) * (1 - Math.exp(-dt * 5));
    camera.translateX(-offX);
    if (small) camera.translateY(-2.6);              // phones: object in the upper part, text below it

    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
