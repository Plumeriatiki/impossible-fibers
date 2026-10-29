// Sensors page: the shapes for the particle scene (js/scene.js).
//   0 fingertip ridges · 1 a finger pressing a soft sheet (pressure) · 2 orb web with prey (vibration)
//   3 whiskers touching a ball (shape) · 4 gripper holding an egg (our sensors) · 5 cloud (contact)
// A glow runs outward from each point of touch. It shows what the sensors are for, never how they're
// made: no materials, structure or layout.
(() => {
  const {rnd, TAU, gauss, unit, sph, mixColor} = Particles;
  const norm = v => { const d = Math.hypot(...v); return v.map(c => c / d); };
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

  // 0: a fingertip, a dome of ridges in a whorl
  const AX = 1.55, AY = 2.15, H = .95, RIDGE = .17;
  function fingertip(i){
    for (;;) {
      const x = (rnd() * 2 - 1) * AX, y = (rnd() * 2 - 1) * AY, e = (x / AX) ** 2 + (y / AY) ** 2;
      if (e > 1) continue;
      const cy = y + .25, v = (Math.hypot(x * 1.1, cy * .85) / RIDGE - Math.atan2(cy, x) / TAU + 100) % 1;
      if (Math.abs(v - .5) < .15) return [x, y, H * Math.sqrt(1 - e), i % 3 ? "#EDEBE6" : "#7FCFCB", -1];
    }
  }

  // 1: a finger pressing into a soft sheet; the glow spreads out from the dent
  const DENT = .75, SIG = .6, TILT = .7, FR = .55;
  const fdir = norm([.45, .72, -.47]), fe1 = norm(cross(fdir, [0, 0, 1])), fe2 = cross(fdir, fe1);
  function press(i){
    let p, c, d = -1;
    if (rnd() < .75) {
      const r = 2.5 * Math.sqrt(rnd()), a = rnd() * TAU, t = Math.exp(-r * r / (2 * SIG * SIG));
      p = [r * Math.cos(a), -DENT * t, r * Math.sin(a)];
      c = t > .2 ? mixColor("#0E9C9A", "#EA580C", Math.min(1, (t - .2) * 2)) : (i % 2 ? "#0E9C9A" : "#7FCFCB");
      d = r;
    } else {
      const tip = [0, -DENT + FR, 0];
      if (rnd() < .3) {
        let u = unit(); if (u[0] * fdir[0] + u[1] * fdir[1] + u[2] * fdir[2] > 0) u = u.map(v => -v);
        p = tip.map((v, n) => v + u[n] * FR);
      } else {
        const t = rnd() * 2.8, a = rnd() * TAU, ca = Math.cos(a) * FR, sa = Math.sin(a) * FR;
        p = tip.map((v, n) => v + fdir[n] * t + fe1[n] * ca + fe2[n] * sa);
      }
      c = i % 3 ? "#8E979C" : "#C9CDD0";
    }
    const ct = Math.cos(TILT), st = Math.sin(TILT);     // tip the sheet toward the camera
    return [p[0], p[1] * ct - p[2] * st - .2, p[1] * st + p[2] * ct, c, d];
  }

  // 2: an orb web with a spider at the hub and prey caught in the silk; the glow runs out from the prey
  const SP = 22, R0 = .45, R1 = 2.15, TURNS = 16, PREY = [1.25, -.95];
  const frameR = [...Array(SP)].map(() => 2.35 + rnd() * .35);
  const at = (r, a) => [r * Math.cos(a), r * Math.sin(a)];
  const rOf = ph => R0 + (R1 - R0) * ph / (TURNS * TAU);
  const legs = [...Array(8)].map((_, j) => {
    const s = j < 4 ? 1 : -1, th = [.55, 1.15, 1.95, 2.55][j % 4], dir = [s * Math.sin(th), Math.cos(th)];
    const bend = (j % 4 < 2 ? 1 : -1) * .35, d2 = [dir[0] * Math.cos(bend) - dir[1] * Math.sin(bend) * s, dir[1] * Math.cos(bend) + dir[0] * Math.sin(bend) * s];
    const k = [dir[0] * .5, .14 + dir[1] * .5, .2];
    return [[0, .14, 0], k, [k[0] + d2[0] * .62, k[1] + d2[1] * .62, 0]];
  });
  function web(i){
    const q = rnd(); let x, y, z = gauss() * .02, c = i % 3 ? "#BFEFF0" : "#EDEBE6";
    if (q < .27) {                                     // spokes
      const k = Math.floor(rnd() * SP); [x, y] = at(.1 + rnd() * (frameR[k] - .1), k / SP * TAU);
    } else if (q < .34) {                              // frame
      const k = Math.floor(rnd() * SP), t = rnd(), A = at(frameR[k], k / SP * TAU), B = at(frameR[(k + 1) % SP], (k + 1) / SP * TAU);
      x = A[0] + (B[0] - A[0]) * t; y = A[1] + (B[1] - A[1]) * t;
    } else if (q < .9) {                               // capture spiral, straight between spokes
      const r = Math.sqrt(R0 * R0 + rnd() * (R1 * R1 - R0 * R0)), seg = TAU / SP, ph = (r - R0) / (R1 - R0) * TURNS * TAU;
      const j = Math.floor(ph / seg), f = ph / seg - j, A = at(rOf(j * seg), j * seg), B = at(rOf((j + 1) * seg), (j + 1) * seg);
      x = A[0] + (B[0] - A[0]) * f; y = A[1] + (B[1] - A[1]) * f;
    } else if (q < .91) {                              // hub
      [x, y] = at(.32 * Math.sqrt(rnd()), rnd() * TAU);
    } else if (q < .985) {                             // spider: two body parts and eight legs
      c = i % 3 ? "#EDEBE6" : "#E8B27A";
      if (rnd() < .4) { const big = rnd() < .6, p = sph(big ? .28 : .19, false); x = p[0]; y = p[1] + (big ? -.32 : .14); z = p[2] * .8; }
      else {
        const L = legs[Math.floor(rnd() * 8)], t = rnd() * 2, s = Math.min(1, Math.floor(t)), f = t - s;
        [x, y, z] = [0, 1, 2].map(n => L[s][n] + (L[s + 1][n] - L[s][n]) * f);
      }
    } else {                                           // prey
      const p = sph(.14, false);
      return [PREY[0] + p[0], PREY[1] + p[1], p[2], i % 2 ? "#EA580C" : "#F6A35C", -1];
    }
    return [x, y, z, c, Math.hypot(x - PREY[0], y - PREY[1])];
  }

  // 3: a rat's head in profile, whiskers fanned forward; one whisker touches a ball and the glow runs to its base
  const rho = u => .08 + .85 * Math.pow(u, .6);       // head radius, from the nose (u = 0) back (u = 1)
  const whiskers = [];
  for (const s of [1, -1]) for (let row = 0; row < 5; row++) for (let col = 0; col < 3; col++) {
    const u = .16 + col * .06, x = -u * 2.6, y = (2 - row) * .09 - .05, r = rho(u) * .9;
    const L = 1.5 + col * .45 + (row === 2 ? .2 : 0);
    whiskers.push({b: [x, y, s * Math.sqrt(Math.max(0, r * r - y * y))], dir: norm([.62, (2 - row) * .3, s * .75]), L, bend: [.3, -.12, -s * .2]});
  }
  const wp = (w, t) => w.b.map((v, n) => v + w.dir[n] * w.L * t + w.bend[n] * w.L * t * t);
  const TOUCH = whiskers[7], tipT = wp(TOUCH, 1), BALLR = .32;  // near side, middle row, last column
  const tan = norm(TOUCH.dir.map((v, n) => v + 2 * TOUCH.bend[n])), BALL = tipT.map((v, n) => v + tan[n] * BALLR);
  const whisk = i => { const [x, y, z, c, d] = rat(i); return [x * .8 + .7, y * .8, z * .8, c, d]; };
  function rat(i){
    const q = rnd();
    if (q < .25) {                                     // head
      let u; do u = rnd(); while (rnd() > rho(u) / .93);
      const a = rnd() * TAU, r = rho(u);
      return [-u * 2.6, r * .85 * Math.sin(a), r * Math.cos(a), i % 2 ? "#0E7C7B" : "#0E9C9A", -1];
    }
    if (q < .31) {                                     // ears
      const s = rnd() < .5 ? 1 : -1, [x, y] = at(Math.sqrt(rnd()), rnd() * TAU);
      return [-2.15 + x * .38, .72 + y * .42, s * .55, "#0E9C9A", -1];
    }
    if (q < .33) {                                     // eyes and nose
      const eye = rnd() < .5, p = sph(eye ? .07 : .1, false), s = rnd() < .5 ? 1 : -1;
      return eye ? [-1.25 + p[0], .33 + p[1], s * .5 + p[2], "#EDEBE6", -1] : [.02 + p[0], p[1], p[2], "#E8B27A", -1];
    }
    if (q < .92) {                                     // whiskers
      const w = whiskers[Math.floor(rnd() * whiskers.length)], t = rnd(), p = wp(w, t);
      return w === TOUCH ? [...p, "#F6A35C", (1 - t) * w.L] : [...p, i % 3 ? "#EDEBE6" : "#C9CDD0", -1];
    }
    const p = sph(BALLR, true).map((v, n) => v + BALL[n]), hit = Math.hypot(...p.map((v, n) => v - tipT[n])) < .22;
    return [...p, hit ? "#EA580C" : i % 2 ? "#8E979C" : "#C9CDD0", -1];
  }

  // 4: a robot gripper holding an egg; the glow spreads over the finger pads from where they touch it
  function boxPt(cx, cy, cz, hx, hy, hz){
    const h = [hx, hy, hz], p = [0, 0, 0];
    if (rnd() < .4) {                                  // edges
      const a = rnd() * (hx + hy + hz) < hx ? 0 : rnd() * (hy + hz) < hy ? 1 : 2;
      for (let n = 0; n < 3; n++) p[n] = n === a ? (rnd() * 2 - 1) * h[n] : (rnd() < .5 ? -h[n] : h[n]);
    } else {                                           // faces, by area
      const A = [hy * hz, hx * hz, hx * hy], f = rnd() * (A[0] + A[1] + A[2]), a = f < A[0] ? 0 : f < A[0] + A[1] ? 1 : 2;
      for (let n = 0; n < 3; n++) p[n] = n === a ? (rnd() < .5 ? -h[n] : h[n]) : (rnd() * 2 - 1) * h[n];
    }
    return [cx + p[0], cy + p[1], cz + p[2]];
  }
  const EGG = -.45, Y0 = -.75;                        // egg centre; shift to centre the whole gripper
  function gripper(i){
    const q = rnd(), metal = i % 3 ? "#8E979C" : "#C9CDD0";
    let p, c = metal, d = -1;
    if (q < .3) {                                      // egg
      const u = unit(), rx = .84 * (1 - .1 * u[1]);
      p = [u[0] * rx, EGG + u[1] * 1.1, u[2] * rx]; c = i % 4 ? "#EDEBE6" : "#E8B27A";
    } else if (q < .42) {                              // finger pads
      const s = rnd() < .5 ? 1 : -1, y = -1.05 + rnd() * 1.2, z = (rnd() * 2 - 1) * .42, r = Math.hypot(y - EGG, z);
      p = [s * .85, y, z]; c = mixColor("#EA580C", "#7A2E0A", Math.min(1, r / .8)); d = r * 3;
    } else if (q < .72) {                              // fingers
      const s = rnd() < .5 ? 1 : -1; p = boxPt(s * 1.02, .06, 0, .16, 1.36, .45);
    } else if (q < .86) {                              // palm
      p = boxPt(0, 1.62, 0, 1.35, .2, .55);
    } else {                                           // wrist
      const a = rnd() * TAU, r = rnd() < .25 ? .55 * Math.sqrt(rnd()) : .38, y = r > .38 ? 1.84 : 1.82 + rnd() * 1.2;
      p = [Math.cos(a) * r, y, Math.sin(a) * r];
    }
    return [p[0], p[1] + Y0, p[2], c, d];
  }

  const shapes = [fingertip, press, web, whisk, gripper, i => [...sph(2.4, false), i % 3 ? "#0E7C7B" : "#7FCFCB"]];
  Particles.start({shapes});
})();
