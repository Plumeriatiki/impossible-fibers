// The spinning line: a small particle simulation of nature's fiber-making mechanisms, drawn down
// the left edge in document coordinates, so the part you see depends on how far you have scrolled.
//   store    droplets wait in a wide reservoir
//   sort     the channel narrows and they line up single-file
//   trigger  the pH falls and each droplet opens into a protein chain (teal → orange)
//   align    the stretching flow turns the chains along the line, and they become a fiber
// Stages start at the sections marked data-stage (four of them, in that order); a section with
// class "night" is drawn on dark. Schematic: the geometry and pH values are illustrative.
// Motion is kept slow and smooth on purpose: droplets sway on their own slow rhythm, and chains
// swing into line, rather than jittering.
(() => {
  const cv = document.getElementById("spine");
  if (!cv) return;
  const g = cv.getContext("2d"), out = document.querySelector(".readout");
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const C = {teal:css("--teal"), light:css("--teal-light"), orange:css("--orange"), ink:css("--ink"),
             rule:css("--rule"), paper:css("--paper"), night:css("--night")};
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ss = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

  const NARROW = 7, FIB = 2.6, R = 3.3, VN = 38, DENSITY = 0.0055;   // half-widths (px), droplet radius, px/s in the narrow channel, droplets per px²
  const LABELS = ["STORE", "SORT", "TRIGGER", "ALIGN"];
  let W = 0, H = 0, CX = 0, big = 60, S = [0, 1, 2, 3, 4], night = [0, 0], t = 0, P = [];

  function hw(y){                                  // channel half-width along the page
    if (y < S[2]){
      const open = ss(S[0] + 40, S[0] + 260, y);   // rounded top of the reservoir
      return Math.max(2, NARROW + (big - NARROW) * (1 - ss(S[1] - 160, S[1] + 420, y)) * Math.sqrt(open));
    }
    return FIB + (NARROW - FIB) * (1 - ss(S[2] + 120, S[3] - 60, y));
  }
  const pH = y => 8 - 3 * ss(S[2] + 60, S[3] - 120, y);    // illustrative: 8 in storage, 5 at the fiber
  const v = y => VN * NARROW / Math.max(hw(y), FIB);        // same flux everywhere: faster where narrower
  const isNight = y => y >= night[0] && y < night[1];

  const spawn = y => ({y, u0:(Math.random() * 2 - 1) * .8, amp:.08 + Math.random() * .12,
    f:.04 + Math.random() * .07, ph:Math.random() * 6.28, type:Math.random() < .5 ? 0 : 1, trig:false, a0:0, age:0});

  function seed(){
    // Steady state: linear density ∝ 1/v, so sample y by rejection.
    P = []; const top = S[0] + 50, end = S[4], vmin = v(S[0] + 300);
    const target = Math.round((S[1] - S[0]) * big * 2 * DENSITY + 30);
    for (let guard = 0; P.length < target && guard < target * 60; guard++){
      const y = top + Math.random() * (end - top);
      if (Math.random() < vmin / v(y)) P.push(spawn(y));
    }
    for (let k = 0; k < 240; k++) step(1 / 30);
  }

  function step(dt){
    t += dt;
    const top = S[0] + 50, end = S[4] - 10;
    for (const p of P){
      p.y += v(p.y) * dt;
      if (!p.trig && pH(p.y) < 6.4 && Math.random() < dt * 3){ p.trig = true; p.a0 = (Math.random() - .5) * 2.1; p.age = 0; }
      if (p.trig) p.age += dt;
      if (p.y > end) Object.assign(p, spawn(top + Math.random() * 30));
    }
  }
  function sway(p){                                // lateral position, as a fraction of the half-width
    const u = p.u0 + p.amp * Math.sin(6.283 * p.f * t + p.ph);
    const lim = Math.max(0, 1 - R / Math.max(hw(p.y), R + .5));
    return Math.max(-lim, Math.min(lim, u)) * (p.trig ? Math.exp(-2 * p.age) : 1);
  }
  const angle = p => p.a0 * Math.exp(-(0.6 + 3 * ss(S[2], S[3], p.y)) * p.age);   // flow swings chains into line

  function bounds(){                               // sections move as fonts and images load
    const st = [...document.querySelectorAll("[data-stage]")].map(e => e.getBoundingClientRect().top + scrollY);
    S = [st[0], st[1], st[2], st[3], document.documentElement.scrollHeight];
    const n = document.querySelector(".night");
    if (n){ const r = n.getBoundingClientRect(); night = [r.top + scrollY, r.bottom + scrollY]; }
  }
  function measure(){
    const dpr = Math.min(2, devicePixelRatio || 1);
    W = cv.clientWidth; H = innerHeight; CX = W / 2; big = W * 0.36;
    cv.width = W * dpr; cv.height = H * dpr; g.setTransform(dpr, 0, 0, dpr, 0, 0);
    bounds(); seed();
  }

  function draw(){
    const y0 = scrollY, y1 = y0 + H;
    g.clearRect(0, 0, W, H);
    for (const side of [-1, 1]){                   // channel walls
      g.beginPath(); let first = true;
      for (let y = Math.max(S[0] + 40, y0 - 10); y < Math.min(S[3] + 40, y1 + 10); y += 5){
        const x = CX + side * (hw(y) + 1.5), sy = y - y0;
        first ? g.moveTo(x, sy) : g.lineTo(x, sy); first = false;
      }
      g.strokeStyle = C.rule; g.lineWidth = 1.2; g.stroke();
    }
    const f0 = Math.max(S[3] - 80, y0), f1 = Math.min(S[4], y1);   // the solid fiber
    if (f1 > f0){
      const grad = g.createLinearGradient(0, S[3] - 80 - y0, 0, S[3] + 60 - y0);
      grad.addColorStop(0, "rgba(234,88,12,0)"); grad.addColorStop(1, C.orange);
      g.fillStyle = grad; g.fillRect(CX - 2.5, f0 - y0, 5, f1 - f0);
    }
    let n = 0, order = 0;
    for (const p of P){
      if (p.y < y0 - 20 || p.y > y1 + 20 || p.y > S[3] + 60) continue;
      const x = CX + sway(p) * hw(p.y), sy = p.y - y0;
      if (!p.trig){
        g.globalAlpha = .9; g.beginPath(); g.arc(x, sy, R, 0, 7);
        g.fillStyle = p.type ? C.light : C.teal; g.fill();
        g.lineWidth = 1; g.strokeStyle = isNight(p.y) ? C.night : C.paper; g.stroke(); g.globalAlpha = 1;
      } else {
        const a = angle(p), L = 7, dx = Math.sin(a) * L, dy = Math.cos(a) * L;
        g.beginPath(); g.moveTo(x - dx, sy - dy); g.lineTo(x + dx, sy + dy);
        g.strokeStyle = C.orange; g.lineWidth = 2.2; g.lineCap = "round"; g.stroke();
        order += Math.max(0, Math.cos(2 * a));
      }
      if (sy > 0 && sy < H) n++;
    }
    if (W > 100){                                  // mechanism labels where each stage starts
      g.font = "500 10px 'DM Mono', monospace"; g.textAlign = "left";
      LABELS.forEach((label, i) => {
        const y = S[i] + [140, 60, 80, 70][i], sy = y - y0;
        if (sy < -20 || sy > H + 20) return;
        g.fillStyle = isNight(y) ? "#8E979C" : C.ink; g.fillText(label, 10, sy);
      });
    }
    if (out){
      const mid = y0 + H * .5;
      out.classList.toggle("on-night", isNight(y0 + H - 30));
      out.innerHTML = `pH <b>${pH(mid).toFixed(1)}</b> · alignment <b>${(n ? order / n : 0).toFixed(2)}</b><br>${pH(mid) < 6.4 ? "<i>triggered</i>" : "stored"} · schematic`;
    }
  }

  let last = 0;
  function frame(now){
    const dt = Math.min(.05, (now - (last || now)) / 1000); last = now;
    if (!calm) step(dt);
    draw(); requestAnimationFrame(frame);
  }
  addEventListener("resize", () => { clearTimeout(measure.t); measure.t = setTimeout(measure, 150); });
  addEventListener("load", bounds);
  setInterval(bounds, 1000);
  document.fonts.ready.then(() => { measure(); requestAnimationFrame(frame); });
})();
