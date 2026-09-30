// Store, sequence, spin: two dopes are encapsulated, a switch releases capsules in a programmed
// order, and they merge into a fiber whose pattern is the sequence. Each click changes the program:
//   s0 gradient · s1 periodic · s2 localized · s3 encoded.
// Schematic animation (not a physical simulation). Draws into <canvas id="pattern-program">;
// highlights the matching .pattern-card. ?print renders the gradient state with all cards lit.
(() => {
const cv = document.getElementById("pattern-program");
if (!cv) return;
const W = 1140, H = 300, CY = 150, V = 150, SLOT = 0.22;           // px/s, seconds per capsule
const X_SWITCH = 300, X_SPIN = 560, FIBER_END = W - 10;
const css = k => getComputedStyle(document.documentElement).getPropertyValue(k).trim();
const dpr = Math.max(2, window.devicePixelRatio || 1);
cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + "px"; cv.style.height = H + "px";
const g = cv.getContext("2d"); g.scale(dpr, dpr);
const A = [14, 124, 123], B = [234, 88, 12];
const mix = f => `rgb(${A.map((a, i) => Math.round(a + (B[i] - a) * f)).join(",")})`;

const BITS = "0100100101000110";   // "IF" in ASCII, as the encoded barcode
const PROGRAMS = [
  {name:"Gradient",  pick:i => { const ramp = (i % 40) / 39; return ((i * 0.618034) % 1) < ramp ? 1 : 0; }, win:6},
  {name:"Periodic",  pick:i => Math.floor(i / 2) % 2, win:1},
  {name:"Localized", pick:i => i % 9 === 4 ? 1 : 0, win:1},
  {name:"Encoded",   pick:i => +BITS[i % BITS.length], win:1},
];
let prog = 0, t = 0, n = 0, caps = [], seq = [], fiber = [];
function reset(){ t = 0; n = 0; caps = []; seq = []; fiber = []; }

function step(dt){
  t += dt;
  while (n * SLOT < t){                                   // release the next capsule from the switch
    caps.push({x:X_SWITCH, c:PROGRAMS[prog].pick(n)}); n++;
  }
  caps.forEach(c => c.x += V * dt);
  while (caps.length && caps[0].x >= X_SPIN){             // capsules merge into the fiber
    seq.push(caps.shift().c);
    const w = PROGRAMS[prog].win, recent = seq.slice(-w);
    fiber.unshift({f:recent.reduce((a, b) => a + b, 0) / recent.length, x:X_SPIN});
  }
  fiber.forEach(s => s.x += V * dt);
  while (fiber.length && fiber[fiber.length - 1].x > FIBER_END + 40) fiber.pop();
}
function warm(){ reset(); for (let k = 0; k < 600; k++) step(1 / 60); }

function capsule(x, y, c, a = 1){
  g.globalAlpha = a;
  g.beginPath(); g.arc(x, y, 13, 0, 7); g.fillStyle = "#FBF9F5"; g.fill(); g.strokeStyle = "#C9C3B8"; g.lineWidth = 1.5; g.stroke();
  g.beginPath(); g.arc(x, y, 8, 0, 7); g.fillStyle = mix(c); g.fill();
  g.globalAlpha = 1;
}
function draw(){
  const fg = css("--fg"), fg2 = css("--fg2"), muted = css("--muted"), rule = "#CFC8BC";
  g.clearRect(0, 0, W, H);
  // channels
  g.strokeStyle = rule; g.lineWidth = 34; g.lineCap = "round";
  g.beginPath(); g.moveTo(40, CY - 80); g.quadraticCurveTo(X_SWITCH - 60, CY - 80, X_SWITCH, CY); g.stroke();
  g.beginPath(); g.moveTo(40, CY + 80); g.quadraticCurveTo(X_SWITCH - 60, CY + 80, X_SWITCH, CY); g.stroke();
  g.beginPath(); g.moveTo(X_SWITCH, CY); g.lineTo(X_SPIN, CY); g.stroke();
  g.strokeStyle = "#E7E2DA"; g.lineWidth = 28;
  [[CY - 80], [CY + 80]].forEach(([y]) => { g.beginPath(); g.moveTo(40, y); g.quadraticCurveTo(X_SWITCH - 60, y, X_SWITCH, CY); g.stroke(); });
  g.beginPath(); g.moveTo(X_SWITCH, CY); g.lineTo(X_SPIN, CY); g.stroke();
  // waiting capsules in each feed (stored)
  for (let k = 0; k < 5; k++){ capsule(60 + k * 34, CY - 80, 0); capsule(60 + k * 34, CY + 80, 1); }
  // switch
  g.beginPath(); g.arc(X_SWITCH, CY, 22, 0, 7); g.fillStyle = css("--panel"); g.fill(); g.strokeStyle = fg2; g.lineWidth = 2.5; g.stroke();
  g.fillStyle = fg2; g.font = "700 16px 'DM Sans', sans-serif"; g.textAlign = "center"; g.fillText("⇄", X_SWITCH, CY + 6);
  // released capsules
  caps.forEach(c => capsule(c.x, CY, c.c));
  // spinner nozzle
  g.fillStyle = fg; g.beginPath(); g.moveTo(X_SPIN - 16, CY - 26); g.lineTo(X_SPIN + 14, CY - 10); g.lineTo(X_SPIN + 14, CY + 10); g.lineTo(X_SPIN - 16, CY + 26); g.closePath(); g.fill();
  // fiber
  fiber.forEach((s, i) => { const nx = i ? fiber[i - 1].x : X_SPIN + 14; g.fillStyle = mix(s.f); g.fillRect(Math.max(X_SPIN + 14, s.x), CY - 11, Math.min(nx, FIBER_END) - Math.max(X_SPIN + 14, s.x) + 1, 22); });
  g.fillStyle = "rgba(255,255,255,.18)"; g.fillRect(X_SPIN + 14, CY - 11, FIBER_END - X_SPIN - 14, 6);
  // labels
  g.textAlign = "left"; g.font = "600 20px 'DM Sans', sans-serif"; g.fillStyle = muted;
  g.fillText("1 Encapsulate", 40, CY - 116); g.fillText("2 Sort", X_SWITCH - 30, CY - 42); g.fillText("3 Spin", X_SPIN - 24, CY - 44);
  g.font = "500 18px 'DM Sans', sans-serif";
  g.fillStyle = mix(0); g.fillText("Dope A", 40, CY - 48);
  g.fillStyle = mix(1); g.fillText("Dope B", 40, CY + 122);
  g.fillStyle = fg; g.font = "700 26px 'DM Sans', sans-serif"; g.textAlign = "right";
  g.fillText(PROGRAMS[prog].name, FIBER_END, CY - 30);
  g.font = "400 18px 'DM Sans', sans-serif"; g.fillStyle = fg2; g.fillText("programmed fiber", FIBER_END, CY + 44);
}

const cards = [...document.querySelectorAll(".pattern-card")];
function setProgram(p){ prog = Math.min(3, p); cards.forEach((c, i) => c.classList.toggle("on", i === prog)); warm(); draw(); }

const still = location.search.includes("print");
let raf = 0, last = 0;
function tick(now){ const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now; step(dt); draw(); raf = requestAnimationFrame(tick); }
document.fonts.ready.then(() => {
  setProgram(0);
  if (still){ cards.forEach(c => c.classList.add("on")); return; }
  document.addEventListener("stepchange", e => { if (e.detail.slide.contains(cv)) setProgram(e.detail.step); });
  document.addEventListener("slidechange", e => { cancelAnimationFrame(raf); if (e.detail.slide.contains(cv)){ last = 0; raf = requestAnimationFrame(tick); } });
  if (cv.closest(".slide").classList.contains("active")) raf = requestAnimationFrame(tick);
});
})();
