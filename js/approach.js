// Approach page: the shapes for the particle scene (js/scene.js). The particles act out the process:
//   0 cloud · 1 droplets (store) · 2 droplets in a line (sort) · 3 twisted fiber (trigger and align) · 4 cloud
(() => {
  const {rnd, TAU, gauss, sph, N} = Particles;

  // particle i keeps droplet k = i % K from store → sort → fiber, so droplets line up, then stretch into the fiber
  const K = 7, GAP = 4.4 / (K - 1);
  const ringC = [...Array(K)].map((_, k) => { const a = k / K * TAU; return [Math.cos(a) * 1.7 + gauss() * .2, Math.sin(a) * 1.15 + gauss() * .2, gauss() * .6]; });
  const fiberX = new Float32Array(N);
  for (let i = 0; i < N; i++) fiberX[i] = -2.2 + (i % K) * GAP + (rnd() - .5) * GAP;

  const cloud = i => [...sph(2.4, false), i % 3 ? "#0E7C7B" : "#7FCFCB"];
  const shapes = [
    cloud,
    i => { const c = ringC[i % K], p = sph(.5, rnd() < .75); return [c[0] + p[0], c[1] + p[1], c[2] + p[2], i % K % 2 ? "#0E9C9A" : "#7FCFCB"]; },
    i => { const x = -2.2 + (i % K) * GAP, p = sph(.3, rnd() < .75); return [x + p[0], p[1], p[2], i % K % 2 ? "#0E9C9A" : "#7FCFCB"]; },
    i => { const s = Math.floor(rnd() * 7), x = fiberX[i], a = s / 7 * TAU + x * 1.15, r = .3 + gauss() * .03; return [x, Math.cos(a) * r, Math.sin(a) * r, i % 5 ? "#EA580C" : "#F6A35C"]; },
    cloud,
  ];

  Particles.start({shapes});
})();
