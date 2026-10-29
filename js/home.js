// Home page: the shapes for the particle scene (js/scene.js), and the turning wheel of projects.
//   0 cloud · 1 droplets (store) · 2 droplets in a line (sort) · 3 twisted fiber (trigger & align)
//   4 hollow tube (Glass Noodle) · 5 nonwoven mesh (robotic touch) · 6 shell (open science)
//   7 ring (projects wheel) · 8 cloud (contact)
(() => {
  const {rnd, TAU, gauss, sph, N} = Particles;

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

  // particle i keeps droplet k = i % K from store → sort → fiber → tube, so droplets line up, then stretch into the fiber
  const K = 7, GAP = 4.4 / (K - 1);
  const ringC = [...Array(K)].map((_, k) => { const a = k / K * TAU; return [Math.cos(a) * 1.7 + gauss() * .2, Math.sin(a) * 1.15 + gauss() * .2, gauss() * .6]; });
  const fiberX = new Float32Array(N);
  for (let i = 0; i < N; i++) fiberX[i] = -2.2 + (i % K) * GAP + (rnd() - .5) * GAP;
  const F = 150, mesh = [...Array(F)].map(() => ({cx: (rnd() - .5) * 4.2, cy: (rnd() - .5) * 3.4, a: rnd() * Math.PI, len: 1.1 + rnd() * 2.2, bend: (rnd() - .5) * .5}));
  const TIP = .45, YAW = .75;                         // the tube leans and turns a little further, to show its hollow core

  const cloud = i => [...sph(2.4, false), i % 3 ? "#0E7C7B" : "#7FCFCB"];
  const shapes = [
    cloud,
    i => { const c = ringC[i % K], p = sph(.5, rnd() < .75); return [c[0] + p[0], c[1] + p[1], c[2] + p[2], i % K % 2 ? "#0E9C9A" : "#7FCFCB"]; },
    i => { const x = -2.2 + (i % K) * GAP, p = sph(.3, rnd() < .75); return [x + p[0], p[1], p[2], i % K % 2 ? "#0E9C9A" : "#7FCFCB"]; },
    i => { const s = Math.floor(rnd() * 7), x = fiberX[i], a = s / 7 * TAU + x * 1.15, r = .3 + gauss() * .03; return [x, Math.cos(a) * r, Math.sin(a) * r, i % 5 ? "#EA580C" : "#F6A35C"]; },
    i => { const a = rnd() * TAU, r = .8 + rnd() * .06, x = fiberX[i] * .85;
           const px = x * Math.cos(TIP) - Math.cos(a) * r * Math.sin(TIP), py = x * Math.sin(TIP) + Math.cos(a) * r * Math.cos(TIP), pz = Math.sin(a) * r;
           return [px * Math.cos(YAW) + pz * Math.sin(YAW), py, -px * Math.sin(YAW) + pz * Math.cos(YAW), i % 4 ? "#BFEFF0" : "#7FCFCB"]; },
    i => { const f = mesh[i % F], t = rnd() - .5, dx = Math.cos(f.a), dy = Math.sin(f.a), b = f.bend * (1 - 4 * t * t);
           return [f.cx + dx * t * f.len - dy * b, f.cy + dy * t * f.len + dx * b, (rnd() - .5) * .14, i % 3 ? "#E8B27A" : "#EA580C"]; },
    i => [...sph(2.1, true), i % 2 ? "#7FCFCB" : "#E8B27A"],
    i => { const a = rnd() * TAU, b = rnd() * TAU, R = 2.4, r = .15 + rnd() * .12;
           return [(R + r * Math.cos(b)) * Math.cos(a), r * Math.sin(b) * 1.4, (R + r * Math.cos(b)) * Math.sin(a), i % 2 ? "#EA580C" : "#7FCFCB"]; },
    cloud,
  ];

  Particles.start({shapes, onScroll: ({frac, sec}) => { if (sec.classList.contains("wheel")) wheel(frac); }});
})();
