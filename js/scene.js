// Particle scene shared by the home and sensors pages. A cloud of particles sits behind the page; each
// section names a shape (data-shape) and which side its text is on (data-side). Scrolling turns the camera
// around the cloud and reshapes it into that section's shape. The blend between two shapes runs on the GPU
// (vertex shader); JavaScript only swaps the pair of shapes when the section changes. Illustrative, not a
// simulation. Needs three.js (r128) loaded first.
//
// Particles.start({shapes, onScroll}):
//   shapes[k](i) → [x, y, z, colour, glow] for particle i of shape k, drawn facing the camera (+z).
//     colour is a hex string or a THREE.Color. glow, if given and ≥ 0, is the particle's distance from a
//     point of touch: a band of light travels out from that point every few seconds.
//   onScroll({i, frac, sec}) runs every frame (on scroll, without WebGL) for page-specific UI.
// A section with class "wheel" is pinned while it scrolls and changes shape only at its end.
window.Particles = (() => {
  const small = innerWidth < 760;
  const modest = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;
  const N = small ? 3000 : modest ? 4000 : 6500;

  const rnd = Math.random, TAU = Math.PI * 2;
  const gauss = () => { let u = 0, v = 0; while (!u) u = rnd(); while (!v) v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * v); };
  const ss = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  const unit = () => { let x, y, z, d; do { x = gauss(); y = gauss(); z = gauss(); d = Math.hypot(x, y, z); } while (!d); return [x / d, y / d, z / d]; };
  const sph = (r, shell) => { const u = unit(), rr = shell ? r * (0.9 + 0.1 * rnd()) : r * Math.cbrt(rnd()); return [u[0] * rr, u[1] * rr, u[2] * rr]; };
  const pal = {};
  const color = h => typeof h === "string" ? pal[h] || (pal[h] = new THREE.Color(h)) : h;
  const mixColor = (a, b, t) => color(a).clone().lerp(color(b), t);

  function start({shapes, onScroll = () => {}}){
    const root = document.documentElement;
    const canvas = document.getElementById("scene");
    const secs = [...document.querySelectorAll("[data-shape]")];
    const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;

    // ── reveal text and mark the current section, even without WebGL ──
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) e.target.classList.add("in"); }), {threshold: .25});
    document.querySelectorAll(".reveal").forEach(el => io.observe(el));
    const dots = document.querySelector(".dots");
    secs.forEach(() => dots.appendChild(document.createElement("i")));

    function progress(){
      const y = scrollY; let i = 0;
      for (let k = 0; k < secs.length; k++) if (secs[k].offsetTop <= y + 1) i = k;
      const s = secs[i], span = Math.max(1, s.offsetHeight - (s.classList.contains("wheel") ? innerHeight : 0));
      return {i, frac: Math.min(1, Math.max(0, (y - s.offsetTop) / span)), sec: s};
    }
    const ui = () => {
      const p = progress();
      [...dots.children].forEach((d, n) => d.classList.toggle("on", n === p.i));
      onScroll(p);
      return p;
    };

    // ── WebGL, with a graceful fallback ──
    if (!window.THREE) { root.classList.add("no-gl"); addEventListener("scroll", ui, {passive: true}); return; }
    let renderer;
    try { renderer = new THREE.WebGLRenderer({canvas, antialias: !small}); }
    catch (e) { root.classList.add("no-gl"); addEventListener("scroll", ui, {passive: true}); return; }

    const ANGLE = .85;                                 // camera turn per section
    const shapeOf = secs.map(s => +s.dataset.shape);
    const cache = {};
    function build(k){                                 // positions, colours and glow, turned to face the camera at section k
      if (cache[k]) return cache[k];
      const pos = new Float32Array(N * 3), col = new Float32Array(N * 3), glow = new Float32Array(N);
      const c = Math.cos(k * ANGLE), sn = Math.sin(k * ANGLE);
      for (let i = 0; i < N; i++) {
        const [x, y, z, cc, d = -1] = shapes[k](i), C = color(cc);
        pos[i * 3] = x * c + z * sn; pos[i * 3 + 1] = y; pos[i * 3 + 2] = -x * sn + z * c;
        col[i * 3] = C.r; col[i * 3 + 1] = C.g; col[i * 3 + 2] = C.b;
        glow[i] = d;
      }
      return (cache[k] = {pos, col, glow});
    }

    // ── scene ──
    const PR = Math.min(small ? 1.5 : 2, devicePixelRatio || 1);
    renderer.setPixelRatio(PR);
    renderer.setClearColor(0x0b0f12, 1);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, 1, .1, 100);
    const geo = new THREE.BufferGeometry();
    const attr = size => new THREE.BufferAttribute(new Float32Array(N * size), size);
    geo.setAttribute("position", attr(3));
    geo.setAttribute("posB", attr(3));
    geo.setAttribute("colA", attr(3));
    geo.setAttribute("colB", attr(3));
    geo.setAttribute("dA", attr(1));
    geo.setAttribute("dB", attr(1));
    const ph = new Float32Array(N); for (let i = 0; i < N; i++) ph[i] = rnd() * TAU;
    geo.setAttribute("phase", new THREE.BufferAttribute(ph, 1));
    const mat = new THREE.ShaderMaterial({
      uniforms: {uMix: {value: 0}, uTime: {value: 0}, uSize: {value: small ? 4.6 : 4.2}, uJit: {value: calm ? 0 : .02}, uPR: {value: PR}, uGlow: {value: calm ? 0 : 1}},
      vertexShader: `
        attribute vec3 posB; attribute vec3 colA; attribute vec3 colB; attribute float phase; attribute float dA; attribute float dB;
        uniform float uMix, uTime, uSize, uJit, uPR, uGlow; varying vec3 vCol;
        float ring(float d){                     // a band that travels out from the point of touch every few seconds
          if (d < 0.0) return 0.0;
          float x = d - mod(uTime * 1.2, 5.0);
          return exp(-x * x * 14.0);
        }
        void main(){
          vec3 p = mix(position, posB, uMix);
          p += uJit * vec3(sin(uTime * 1.3 + phase), sin(uTime * 1.1 + phase * 1.7), sin(uTime * .9 + phase * 2.3));
          float g = uGlow * mix(ring(dA), ring(dB), uMix);
          vCol = mix(colA, colB, uMix) + g * vec3(.95, .45, .15);
          vec4 mv = modelViewMatrix * vec4(p, 1.0);
          gl_Position = projectionMatrix * mv;
          gl_PointSize = uSize * uPR * (10.0 / -mv.z) * (1.0 + .8 * g);
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
      const A = build(a), B = build(b), ga = geo.attributes;
      ga.position.array.set(A.pos); ga.posB.array.set(B.pos);
      ga.colA.array.set(A.col); ga.colB.array.set(B.col);
      ga.dA.array.set(A.glow); ga.dB.array.set(B.glow);
      for (const n of ["position", "posB", "colA", "colB", "dA", "dB"]) ga[n].needsUpdate = true;
    }

    function resize(){ renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
    addEventListener("resize", resize); resize();

    const sideX = {left: 2.9, right: -2.9, center: 0};
    let offX = small ? 0 : 2.9, last = performance.now();
    const t0 = last;
    function frame(now){
      const t = (now - t0) / 1000, dt = Math.min(.1, (now - last) / 1000); last = now;
      const {i, frac, sec} = ui();
      setPair(i);
      mat.uniforms.uMix.value = sec.classList.contains("wheel") ? ss(.82, 1, frac) : ss(.35, .92, frac);
      mat.uniforms.uTime.value = t;

      // the camera turns as you scroll
      const sPos = i + frac, theta = sPos * ANGLE + (calm ? 0 : .12 * Math.sin(t * .25)), phi = .28 * Math.sin(sPos * .9 + .4);
      const R = small ? 13.5 : 9.5;
      camera.position.set(R * Math.sin(theta) * Math.cos(phi), R * Math.sin(phi), R * Math.cos(theta) * Math.cos(phi));
      camera.lookAt(0, 0, 0);
      const f = mat.uniforms.uMix.value;
      const want = small ? 0 : sideX[sec.dataset.side] * (1 - f) + sideX[(secs[i + 1] || sec).dataset.side] * f;
      offX += (want - offX) * (1 - Math.exp(-dt * 5));
      camera.translateX(-offX);
      if (small) camera.translateY(-2.6);            // phones: object in the upper part, text below it

      renderer.render(scene, camera);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  return {start, N, rnd, TAU, gauss, ss, unit, sph, mixColor};
})();
