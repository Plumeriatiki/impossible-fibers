// Home page: the shapes for the particle scene (js/scene.js).
//   0 cloud · 1 hollow tube (Glass Noodle) · 2 fingertip ridges (robotic touch) · 3 shell (open science) · 4 cloud (contact)
(() => {
  const {rnd, TAU, sph} = Particles;
  const TIP = .45, YAW = .75;                         // the tube leans and turns a little, to show its hollow core
  const AX = 1.55, AY = 2.15, H = .95, RIDGE = .17;   // fingertip: half-width, half-height, dome height, ridge spacing (as in js/sensors.js)

  const cloud = i => [...sph(2.4, false), i % 3 ? "#0E7C7B" : "#7FCFCB"];
  const shapes = [
    cloud,
    i => { const a = rnd() * TAU, r = .8 + rnd() * .06, x = (rnd() * 2 - 1) * 2.2;
           const px = x * Math.cos(TIP) - Math.cos(a) * r * Math.sin(TIP), py = x * Math.sin(TIP) + Math.cos(a) * r * Math.cos(TIP), pz = Math.sin(a) * r;
           return [px * Math.cos(YAW) + pz * Math.sin(YAW), py, -px * Math.sin(YAW) + pz * Math.cos(YAW), i % 4 ? "#BFEFF0" : "#7FCFCB"]; },
    i => { for (;;) {
             const x = (rnd() * 2 - 1) * AX, y = (rnd() * 2 - 1) * AY, e = (x / AX) ** 2 + (y / AY) ** 2;
             if (e > 1) continue;
             const cy = y + .25, v = (Math.hypot(x * 1.1, cy * .85) / RIDGE - Math.atan2(cy, x) / TAU + 100) % 1;
             if (Math.abs(v - .5) < .15) return [x, y, H * Math.sqrt(1 - e), i % 3 ? "#EDEBE6" : "#7FCFCB"];
           } },
    i => [...sph(2.1, true), i % 2 ? "#7FCFCB" : "#E8B27A"],
    cloud,
  ];

  Particles.start({shapes});
})();
