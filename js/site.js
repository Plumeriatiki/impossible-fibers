// Impossible Fibers site runtime. Load this BEFORE the chart scripts in js/charts/.
//
// The charts are copied unchanged from the talks repo, where the deck drives them with two events:
//   "slidechange"  start animating if your slide is showing, stop otherwise
//   "stepchange"   show build step n (what a clicker press does in a talk)
// Here each chart sits in <figure class="fig" data-w data-h data-steps> around a .stage drawn at the
// chart's native slide size and scaled to the column. A chart animates while it is on screen, and its
// build steps play through once, the first time it is mostly in view; Replay runs them again.
(() => {
  // Deck charts answer every slidechange (start if it's mine, else stop), which would restart charts
  // that are already running whenever another one scrolls in. So their slidechange listeners are
  // collected here and each is called only for its own figure.
  const slideHandlers = [];
  const addListener = document.addEventListener.bind(document);
  document.addEventListener = (type, fn, opts) =>
    type === "slidechange" ? void slideHandlers.push(fn) : addListener(type, fn, opts);

  const owners = new Map();   // figure → its charts' slidechange handlers
  const drive = (fig, on) => (owners.get(fig) || []).forEach(fn => fn({detail:{slide:{contains: () => on}}}));
  function claimHandlers(){
    // Ask each handler which element it checks for, then file it under that element's figure.
    slideHandlers.splice(0).forEach(fn => {
      let node = null;
      fn({detail:{slide:{contains(n){ node = node || n; return false; }}}});
      const fig = node && node.closest && node.closest(".fig");
      if (fig) owners.set(fig, [...(owners.get(fig) || []), fn]);
    });
  }

  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ── Scale each stage to its column ──
  const MIN_SCALE = 0.42;   // below this the chart text drops under ~9 px: scroll sideways instead
  function fit(fig){
    const box = fig.querySelector(".fig-box"), sizer = box.firstElementChild, stage = sizer.firstElementChild;
    const W = +fig.dataset.w, H = +fig.dataset.h;
    let k = Math.min(1, box.clientWidth / W);
    fig.classList.toggle("scrolls", k < MIN_SCALE);
    k = Math.max(k, MIN_SCALE);
    stage.style.width = W + "px"; stage.style.height = H + "px"; stage.style.transform = `scale(${k})`;
    sizer.style.width = W * k + "px"; sizer.style.height = H * k + "px";
  }

  // ── Build steps ──
  function setStep(fig, s){
    document.dispatchEvent(new CustomEvent("stepchange", {detail:{slide:fig, step:s}}));
    (fig.closest("section") || fig).querySelectorAll("[data-at]").forEach(el => el.classList.toggle("on", s >= +el.dataset.at));
  }
  // ?print shows every figure finished, as the deck's ?print does (the charts read it too).
  const still = location.search.includes("print");
  function play(fig){
    const n = +fig.dataset.steps || 0, hold = +fig.dataset.hold || 2800, loop = "loop" in fig.dataset;
    clearTimeout(fig._timer);
    if (still || (calm && !loop)){ setStep(fig, n); return; }
    let s = 0;
    const next = () => {
      setStep(fig, s);
      if (s < n){ s++; fig._timer = setTimeout(next, hold); }
      else if (loop){ s = 0; fig._timer = setTimeout(next, hold * 1.6); }
    };
    next();
  }

  function init(){
    claimHandlers();
    const figs = [...document.querySelectorAll(".fig[data-w]")];
    figs.forEach(fig => {
      fit(fig);
      if (+fig.dataset.steps && !("loop" in fig.dataset)){
        const tools = document.createElement("div"); tools.className = "fig-tools";
        const btn = document.createElement("button"); btn.className = "replay"; btn.type = "button"; btn.textContent = "Replay";
        btn.addEventListener("click", () => play(fig));
        tools.appendChild(btn); fig.querySelector(".fig-box").after(tools);
      }
      if (still) play(fig); else setStep(fig, 0);
    });
    if (still){ document.querySelectorAll(".reveal").forEach(el => el.classList.add("visible")); return; }
    const rs = new ResizeObserver(entries => entries.forEach(e => fit(e.target.closest(".fig"))));
    figs.forEach(fig => rs.observe(fig.querySelector(".fig-box")));

    // Watch the chart itself, not the whole figure, so captions don't count toward "in view".
    const io = new IntersectionObserver(entries => entries.forEach(e => {
      const fig = e.target.closest(".fig");
      if (e.isIntersecting !== !!fig._on){ fig._on = e.isIntersecting; drive(fig, fig._on); }
      if (!fig._played && e.intersectionRatio >= 0.5){ fig._played = true; play(fig); }
    }), {threshold:[0, 0.5]});
    figs.forEach(fig => io.observe(fig.querySelector(".fig-box")));
  }
  // Charts register their listeners inside document.fonts.ready, so claim them after that.
  addListener("DOMContentLoaded", () => document.fonts.ready.then(() => setTimeout(init, 0)));

  // ── Reveal on scroll ──
  addListener("DOMContentLoaded", () => {
    const ro = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting){ e.target.classList.add("visible"); ro.unobserve(e.target); }
    }), {threshold:0.12});
    document.querySelectorAll(".reveal").forEach(el => ro.observe(el));
  });

  // ── Hero particles (home page only): the site's original drifting-fiber field ──
  addListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("particle-canvas");
    if (!canvas || calm) return;
    const ctx = canvas.getContext("2d"), host = canvas.parentElement;
    let w, h; const mouse = {x:null, y:null}, pts = [];
    const size = () => { w = canvas.width = host.clientWidth; h = canvas.height = host.clientHeight; };
    size(); addEventListener("resize", size);
    host.addEventListener("mousemove", e => { const r = host.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; });
    host.addEventListener("mouseleave", () => { mouse.x = mouse.y = null; });
    for (let i = 0; i < 46; i++) pts.push({x:Math.random() * w, y:Math.random() * h, vx:(Math.random() - .5) * .35, vy:(Math.random() - .5) * .35, r:1.2 + Math.random() * 1.2});
    let running = true;
    new IntersectionObserver(([e]) => { const was = running; running = e.isIntersecting; if (running && !was) requestAnimationFrame(frame); }).observe(host);
    function frame(){
      if (!running) return;
      ctx.clearRect(0, 0, w, h);
      pts.forEach(p => {
        p.x = (p.x + p.vx + w) % w; p.y = (p.y + p.vy + h) % h;
        if (mouse.x !== null){ const dx = p.x - mouse.x, dy = p.y - mouse.y, d = Math.hypot(dx, dy);
          if (d < 120 && d > 0){ const f = (120 - d) / 120; p.x += dx / d * f * 2; p.y += dy / d * f * 2; } }
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fillStyle = "rgba(14,124,123,.35)"; ctx.fill();
      });
      for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++){
        const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
        if (d < 110){ ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y);
          ctx.strokeStyle = `rgba(234,88,12,${(1 - d / 110) * .18})`; ctx.lineWidth = 1; ctx.stroke(); }
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  });
})();
