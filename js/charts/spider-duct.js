// The spider's silk duct: stored proteins become a fiber as the pH drops. Runs continuously.
// Schematic simulation after Rising & Harrington, Chem. Rev. 123, 2155–2199 (2023).
//   Flow: 2-D continuity, so speed rises as the duct narrows (u ∝ 1/width).
//   Orientation: rigid rods in planar extensional flow, dθ/dt = −ε̇·sin2θ + rotational noise,
//     with ε̇ = du/dx taken from the duct geometry. Noise falls once NT ends lock; rods stop
//     rotating once CT ends trigger (β-sheet formation).
//   Storage: proteins held in micelles until the sac narrows and shear begins. NT ends lock in pairs below
//     pH ~6.6; CT ends trigger below ~5.9. These thresholds are illustrative.
//   Readouts: 2-D nematic order |⟨e^{2iθ}⟩| of the rods in each zone, measured every frame.
// Draws into <canvas id="spider-duct">. Animates while its slide is showing; ?print renders a still.
(() => {
const cv = document.getElementById("spider-duct");
if (!cv) return;
const W = 1728, H = 560, CY = 250;
const X_SAC = 40, X_TAPER = 380, X_DUCT = 620, X_SPIG = 1480, X_OUT = 1540;
const PH_LOCK = 6.6, PH_TRIG = 5.9, U0 = 45, WSAC = 150;

function halfWidth(x){
  if (x < 0) return 0;
  if (x < X_SAC) return WSAC * Math.sqrt(1 - ((X_SAC - x) / X_SAC) ** 2);
  if (x < X_TAPER) return WSAC;
  if (x < X_DUCT){ const k = (x - X_TAPER) / (X_DUCT - X_TAPER); return 64 + (WSAC - 64) * (1 + Math.cos(Math.PI * k)) / 2; }
  if (x < X_SPIG) return 64 - 40 * (x - X_DUCT) / (X_SPIG - X_DUCT);
  if (x < X_OUT) return 24 - 14 * (x - X_SPIG) / (X_OUT - X_SPIG);
  return 3;
}
const pH = x => x < 460 ? 8 : x > 1380 ? 5 : 8 - 3 * (x - 460) / 920;
const speed = x => U0 * WSAC / Math.max(10, halfWidth(Math.max(X_SAC, x)));
const strain = x => (speed(x + 2) - speed(x - 2)) / 4;       // ε̇ = du/dx

const css = k => getComputedStyle(document.documentElement).getPropertyValue(k).trim();
const dpr = Math.max(2, window.devicePixelRatio || 1);
cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + "px"; cv.style.height = H + "px";
const g = cv.getContext("2d"); g.scale(dpr, dpr);

function rng(seed){ return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
  t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = r => Math.sqrt(-2 * Math.log(r() + 1e-12)) * Math.cos(2 * Math.PI * r());
const LANES = [-0.55, -0.28, 0, 0.28, 0.55];

let mols, micelles, r, spawnAcc, t;
function reset(){ mols = []; micelles = []; r = rng(5); spawnAcc = 0; t = 0; }
function spawnMicelle(x){
  const m = {x, y: CY + (r() * 2 - 1) * (WSAC - 34)}; micelles.push(m);
  const n = 12, base = mols.length;
  for (let k = 0; k < n; k++){
    const a = k / n * Math.PI * 2 + r() * 0.3;
    mols.push({m, a, rad: 14 + r() * 8, x: m.x, eta: 0, th: a, free: 0, lock: false, trig: false,
               partner: base + (k ^ 1), lane: LANES[(r() * LANES.length) | 0]});
  }
}
// fill the sac at start so the first frame isn't empty
function prefill(){ for (let x = X_SAC + 10; x < X_TAPER - 20; x += 12) spawnMicelle(x); }

function step(dt){
  t += dt;
  spawnAcc += dt * 4.0;
  while (spawnAcc >= 1){ spawnMicelle(X_SAC + 6); spawnAcc -= 1; }
  micelles.forEach(m => { m.x += speed(m.x) * dt; });
  for (const p of mols){
    if (!p.free){
      p.x = p.m.x + Math.cos(p.a) * p.rad; const y = p.m.y + Math.sin(p.a) * p.rad;
      p.th = p.a;
      if (p.m.x > X_TAPER + 30){ p.free = 1; p.eta = Math.max(-0.85, Math.min(0.85, (y - CY) / halfWidth(p.x))); }
      continue;
    }
    const ph = pH(p.x);
    if (!p.lock && ph < PH_LOCK) p.lock = true;
    if (!p.trig && ph < PH_TRIG) p.trig = true;
    p.x += speed(p.x) * dt;
    if (p.trig){ p.th *= Math.exp(-6 * dt); p.eta += (p.lane - p.eta) * Math.min(1, 2.5 * dt); }
    else {
      const Dr = p.lock ? 0.35 : 1.4;
      p.th += -strain(p.x) * Math.sin(2 * p.th) * dt + Math.sqrt(2 * Dr * dt) * gauss(r);
      p.eta += (Math.sqrt(0.02 * dt) * gauss(r)) * (p.lock ? 0.4 : 1);
      p.eta = Math.max(-0.85, Math.min(0.85, p.eta));
    }
    if (p.x > X_OUT) p.eta *= Math.exp(-5 * dt);
  }
  mols = mols.filter(p => p.x < W + 20);
  micelles = micelles.filter(m => m.x < X_TAPER + 60);
}
const yOf = p => p.free ? CY + p.eta * halfWidth(p.x) * 0.9 : p.m.y + Math.sin(p.a) * p.rad;

// pH colour: teal at 8 → orange at 5
function phColor(ph, alpha){
  const k = Math.max(0, Math.min(1, (8 - ph) / 3)), a = [14, 124, 123], b = [234, 88, 12];
  return `rgba(${a.map((v, i) => Math.round(v + (b[i] - v) * k)).join(",")},${alpha})`;
}

function order(x0, x1){
  let c = 0, s = 0, n = 0;
  for (const p of mols) if (p.x >= x0 && p.x < x1){ c += Math.cos(2 * p.th); s += Math.sin(2 * p.th); n++; }
  return n ? Math.hypot(c, s) / n : 0;
}

function draw(){
  const C = {fg:css("--fg"), fg2:css("--fg2"), muted:css("--muted"), rule:css("--rule"), panel:css("--panel"), teal:css("--teal"), orange:css("--orange")};
  g.clearRect(0, 0, W, H);

  // duct outline, tinted by pH
  const top = [], bot = [];
  for (let x = 0; x <= X_OUT; x += 4){ top.push([x, CY - halfWidth(x)]); bot.push([x, CY + halfWidth(x)]); }
  g.beginPath(); top.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); bot.reverse().forEach(([x, y]) => g.lineTo(x, y)); g.closePath();
  const grad = g.createLinearGradient(0, 0, X_OUT, 0);
  for (let k = 0; k <= 10; k++){ const x = k / 10 * X_OUT; grad.addColorStop(k / 10, phColor(pH(x), 0.13)); }
  g.fillStyle = C.panel; g.fill(); g.fillStyle = grad; g.fill();
  g.strokeStyle = "#B9B4AC"; g.lineWidth = 2.5; g.stroke();

  // the fiber leaving the spigot
  g.strokeStyle = C.fg; g.lineWidth = 4; g.lineCap = "round";
  g.beginPath(); g.moveTo(X_OUT, CY); g.lineTo(W - 10, CY); g.stroke();

  // molecules: a rod with an NT end (teal once locked) and a CT end (orange once triggered)
  for (const p of mols){
    if (p.x > X_OUT + 6) continue;
    const y = yOf(p), L = 9, cs = Math.cos(p.th), sn = Math.sin(p.th);
    const ax = p.x - L * cs, ay = y - L * sn, bx = p.x + L * cs, by = y + L * sn;
    g.strokeStyle = "#4B5563"; g.lineWidth = 2; g.beginPath(); g.moveTo(ax, ay); g.lineTo(bx, by); g.stroke();
    g.fillStyle = p.lock ? C.teal : "#C3C7CD"; g.beginPath(); g.arc(ax, ay, 2.8, 0, 7); g.fill();
    g.fillStyle = p.trig ? C.orange : "#C3C7CD"; g.beginPath(); g.arc(bx, by, 2.8, 0, 7); g.fill();
  }

  // zones, with live alignment
  const zones = [["Storage", "concentrated, in micelles", 60, X_SAC, X_TAPER],
                 ["Duct", "pH falls · shear rises · ions exchange", 700, X_DUCT, X_SPIG],
                 ["Spigot", "a solid fiber", 1470, X_SPIG, X_OUT + 1]];
  zones.forEach(([name, sub, lx, x0, x1]) => {
    g.textAlign = "left"; g.fillStyle = C.fg; g.font = "600 26px 'DM Sans', sans-serif"; g.fillText(name, lx, 34);
    g.fillStyle = C.muted; g.font = "400 20px 'DM Sans', sans-serif"; g.fillText(sub, lx, 62);
    g.fillStyle = C.fg2; g.font = "500 20px 'DM Sans', sans-serif"; g.fillText(`alignment ${order(x0, x1).toFixed(2)}`, lx, 88);
  });

  // lock / trigger markers
  const mark = (ph, label, col) => {
    const x = 460 + (8 - ph) / 3 * 920, w = halfWidth(x);
    g.strokeStyle = col; g.lineWidth = 2; g.setLineDash([4, 5]);
    g.beginPath(); g.moveTo(x, CY + w + 6); g.lineTo(x, CY + w + 44); g.stroke(); g.setLineDash([]);
    g.fillStyle = col; g.font = "600 20px 'DM Sans', sans-serif"; g.textAlign = "center"; g.fillText(label, x, CY + w + 68);
  };
  mark(PH_LOCK, "NT ends lock", C.teal);
  mark(PH_TRIG, "CT ends trigger", C.orange);

  // pH scale
  const sy = 470, sx0 = 460, sx1 = 1380;
  const bar = g.createLinearGradient(sx0, 0, sx1, 0);
  bar.addColorStop(0, phColor(8, 1)); bar.addColorStop(1, phColor(5, 1));
  g.fillStyle = phColor(8, 1); g.fillRect(X_SAC, sy, sx0 - X_SAC, 10);
  g.fillStyle = bar; g.fillRect(sx0, sy, sx1 - sx0, 10);
  g.fillStyle = phColor(5, 1); g.fillRect(sx1, sy, X_OUT - sx1, 10);
  g.fillStyle = C.muted; g.font = "400 19px 'DM Sans', sans-serif"; g.textAlign = "center";
  for (const v of [8, 7, 6, 5]) g.fillText(`pH ${v}`, 460 + (8 - v) / 3 * 920, sy + 38);
  g.textAlign = "left"; g.fillText("pH along the gland", X_SAC, sy + 38);

  // legend
  g.textAlign = "left"; g.font = "400 19px 'DM Sans', sans-serif";
  let lx = X_SAC; const ly = 540;
  const key = (col, label) => { g.fillStyle = col; g.beginPath(); g.arc(lx + 6, ly - 6, 6, 0, 7); g.fill(); g.fillStyle = C.fg2; g.fillText(label, lx + 18, ly); lx += g.measureText(label).width + 50; };
  key(C.teal, "NT end, locked");
  key(C.orange, "CT end, triggered");
  key("#C3C7CD", "not yet");
}

// ── run ──
const still = location.search.includes("print");
let raf = 0, last = 0;
function tick(now){
  const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now;
  for (let k = 0; k < 2; k++) step(dt / 2);
  draw();
  raf = requestAnimationFrame(tick);
}
function warm(){ reset(); prefill(); for (let k = 0; k < 2200; k++) step(1 / 120); }   // run to steady state (~18 s)
function start(){ cancelAnimationFrame(raf); last = 0; raf = requestAnimationFrame(tick); }
function stop(){ cancelAnimationFrame(raf); raf = 0; }
document.fonts.ready.then(() => {
  warm(); draw();
  if (still) return;
  document.addEventListener("slidechange", e => e.detail.slide.contains(cv) ? start() : stop());
  if (cv.closest(".slide").classList.contains("active")) start();
});
})();
