"""
Builds `fiber-three-tricks.svg` -- an animated, self-contained SVG in which
every plotted number comes from fiber_sim.py integrating Eqs. (A.12)-(A.14)
of the white paper with the parameters of the Fig. 2.2 caption.

Animation is pure CSS keyframes on one shared 33 s timeline, so the file works
standalone, as an <img>, or inlined into a page.
"""

import json
import math

D = json.load(open("fiber_data.json"))

W, H = 1120, 730
DUR = 33.0
ACT_T0 = [0.0, 11.0, 22.0]
ACT_LEN = 11.0

INK = "#111827"
MUTED = "#6B7280"
FAINT = "#9CA3AF"
BORDER = "#D8D6D2"
PANEL = "#FFFFFF"
BG = "#F2F0EC"
TEAL = "#0E7C7B"
TEAL_DEEP = "#0B4F4E"
ORANGE = "#EA580C"
SANS = "'DM Sans','Helvetica Neue',Helvetica,Arial,sans-serif"
SERIF = "'DM Serif Display',Georgia,'Times New Roman',serif"

KEYFRAMES = []
RULES = []


def kf(stops, prop, fmt=lambda v: f"{v}"):
    """Register a keyframes block from [(t_seconds, value), ...]."""
    name = f"k{len(KEYFRAMES)}"
    seen, parts = set(), []
    for t, v in stops:
        p = round(100.0 * t / DUR, 3)
        if p in seen:
            continue
        seen.add(p)
        parts.append(f"{p}%{{{prop}:{fmt(v)}}}")
    KEYFRAMES.append(f"@keyframes {name}{{{''.join(parts)}}}")
    return name


def cls(body):
    name = f"c{len(RULES)}"
    RULES.append(f".{name}{{{body}}}")
    return name


def anim(name, extra=""):
    return cls(f"animation:{name} {DUR}s linear infinite;{extra}")


def act_class(i, fade_in=0.5, hold_out=10.3, fade_out=10.8):
    t0 = ACT_T0[i]
    stops = [] if t0 == 0 else [(0.0, 0)]
    stops += [(t0, 0), (t0 + fade_in, 1), (t0 + hold_out, 1),
              (t0 + fade_out, 0), (DUR, 0)]
    return anim(kf(stops, "opacity"), "opacity:0;")


def draw_class(i, length, t_start, t_end):
    """Reveal a stroked path left-to-right over [t_start, t_end] within act i."""
    t0 = ACT_T0[i]
    a, b = t0 + t_start, t0 + t_end
    stops = [(0.0, length)] + ([] if a == 0 else [(a, length)]) + [(b, 0.0), (DUR, 0.0)]
    name = kf(stops, "stroke-dashoffset", lambda v: f"{v:.1f}")
    return anim(name, f"stroke-dasharray:{length:.1f};stroke-dashoffset:{length:.1f};")


def grow_class(i, t_start, t_end):
    """Scale a group up from its own baseline over [t_start, t_end] within act i."""
    t0 = ACT_T0[i]
    a, b = t0 + t_start, t0 + t_end
    stops = [(0.0, 0.0)] + ([] if a == 0 else [(a, 0.0)]) + [(b, 1.0), (DUR, 1.0)]
    name = kf(stops, "transform", lambda v: f"scaleY({v:.3f})")
    return anim(name, "transform-box:fill-box;transform-origin:bottom;"
                      "transform:scaleY(0);")


def fade_in_class(i, t_start, dur=0.6):
    t0 = ACT_T0[i]
    a = t0 + t_start
    stops = [(0.0, 0)] + ([] if a == 0 else [(a, 0)]) + [(a + dur, 1), (DUR, 1)]
    return anim(kf(stops, "opacity"), "opacity:0;")


# ---------------------------------------------------------------------------
class Plot:
    def __init__(self, x, y, w, h, xlim, ylim, ylog=False):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.x0, self.x1 = xlim
        self.ylog = ylog
        self.y0, self.y1 = (math.log10(ylim[0]), math.log10(ylim[1])) if ylog else ylim

    def X(self, v):
        return self.x + (v - self.x0) / (self.x1 - self.x0) * self.w

    def Y(self, v):
        if self.ylog:
            v = math.log10(max(v, 10 ** self.y0))
        t = (v - self.y0) / (self.y1 - self.y0)
        return self.y + self.h - t * self.h

    def frame(self, fill=PANEL):
        return (f'<rect x="{self.x}" y="{self.y}" width="{self.w}" height="{self.h}" '
                f'rx="3" fill="{fill}" stroke="{BORDER}" stroke-width="1"/>')

    def path(self, xs, ys):
        pts = [(self.X(a), self.Y(b)) for a, b in zip(xs, ys)]
        d = "M" + " L".join(f"{a:.2f},{b:.2f}" for a, b in pts)
        ln = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        return d, ln


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def txt(x, y, s, size=13, fill=INK, family=SANS, weight="400", anchor="start",
        ls="0", extra=""):
    s = esc(s)
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
            f'letter-spacing="{ls}"{extra}>{s}</text>')


def label(x, y, s):
    return txt(x, y, s, 10.5, MUTED, weight="600", ls="1.4")


out = []
add = out.append

# ---------------------------------------------------------------------------
# static chrome
# ---------------------------------------------------------------------------
add(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
add(txt(56, 50, "The mess is the point", 31, INK, SERIF))
add(txt(56, 76, "One protein fiber, three computations — none of them available to a clean sensor",
        14.5, MUTED))
add(f'<line x1="56" y1="97" x2="{W-56}" y2="97" stroke="{BORDER}" stroke-width="1"/>')

# --- fiber schematic (persistent) ---
sx, sy = 56, 122
add(f'<g transform="translate({sx},{sy})">')
add(label(0, 8, "THE DEVICE"))
# electrodes
add(f'<rect x="6" y="26" width="9" height="38" rx="2" fill="{TEAL_DEEP}"/>')
add(f'<rect x="171" y="26" width="9" height="38" rx="2" fill="{TEAL_DEEP}"/>')
# fiber strands
for k, off in enumerate((-9, -3, 3, 9)):
    yc = 45 + off
    add(f'<path d="M15,{yc} C60,{yc-4} 126,{yc+4} 171,{yc}" fill="none" '
        f'stroke="{TEAL}" stroke-width="2" opacity="{0.9 - 0.13*k:.2f}"/>')
# stress arrow, pulsing
pulse = anim(kf([(0, 0), (0.55, -4), (1.1, 0)] if False else
                [(0, 0.0), (DUR, 0.0)], "opacity"))
add(f'<g><path d="M93,6 L93,20 M87,15 L93,21 L99,15" fill="none" stroke="{ORANGE}" '
    f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></g>')
add(txt(104, 18, "stress in", 11.5, ORANGE, weight="600"))
# readout leads
add(f'<path d="M180,45 L206,45" fill="none" stroke="{TEAL_DEEP}" stroke-width="1.6"/>')
add(f'<circle cx="216" cy="45" r="11" fill="none" stroke="{TEAL_DEEP}" stroke-width="1.6"/>')
add(txt(216, 49.5, "V", 12, TEAL_DEEP, SANS, "700", "middle"))
add(txt(232, 41, "voltage", 11.5, TEAL_DEEP, weight="600"))
add(txt(232, 54, "out", 11.5, TEAL_DEEP, weight="600"))
add("</g>")

# --- legend ---
lx, ly = W - 56, 130
add(f'<line x1="{lx-176}" y1="{ly-4}" x2="{lx-150}" y2="{ly-4}" stroke="{ORANGE}" stroke-width="2.6"/>')
add(txt(lx - 142, ly, "the fiber as it is", 12.5, INK, weight="600"))
add(f'<line x1="{lx-176}" y1="{ly+18}" x2="{lx-150}" y2="{ly+18}" stroke="{TEAL}" stroke-width="2.6" stroke-dasharray="1 0"/>')
add(txt(lx - 142, ly + 22, "same fiber, nonlinearities off", 12.5, MUTED))
add(txt(lx - 142, ly + 38, "identical memory and couplings", 10.5, FAINT))

# --- act progress bar ---
pbx, pby, pbw = 56, 612, W - 112
seg = (pbw - 16) / 3
for i in range(3):
    x = pbx + i * (seg + 8)
    add(f'<rect x="{x:.1f}" y="{pby}" width="{seg:.1f}" height="3" rx="1.5" fill="{BORDER}"/>')
    fill_kf = kf([(0.0, 0.0)] + ([] if ACT_T0[i] == 0 else [(ACT_T0[i], 0.0)])
                 + [(ACT_T0[i] + ACT_LEN, 1.0), (DUR, 1.0)],
                 "transform", lambda v: f"scaleX({v:.3f})")
    c = anim(fill_kf, "transform-box:fill-box;transform-origin:left;transform:scaleX(0);")
    add(f'<rect class="{c}" x="{x:.1f}" y="{pby}" width="{seg:.1f}" height="3" rx="1.5" fill="{ORANGE}"/>')

# --- footer / provenance ---
p = D["params"]
add(txt(56, 682, "Every curve here is simulated output, not illustration.", 11.5, MUTED, weight="600"))
add(txt(56, 699,
        "Numerical integration (RK4) of the reduced visco-piezoelectric model, Eqs. (A.12)–(A.14), "
        "at the parameters of the Fig. 2.2 caption:", 11, FAINT))
add(txt(56, 714,
        f"k₀²={p['k0sq']}, g={p['g']}, gₑ={p['ge']}, "
        f"Δc=({p['Dc'][0]}, {p['Dc'][1]}), Δe=({p['De'][0]}, {p['De'][1]}), "
        f"τ̃=({p['tau'][0]}, {p['tau'][1]}), ℓ=({p['ell'][0]}, {p['ell'][1]}). "
        "The teal reference is the same system with g = gₑ = ℓ = 0.", 11, FAINT))

# ---------------------------------------------------------------------------
# per-act geometry
# ---------------------------------------------------------------------------
IN = dict(x=56, y=226, w=498, h=84)
OUT = dict(x=56, y=352, w=498, h=108)
RP = dict(x=610, y=226, w=454, h=234)


def sym(xs, ys, pad=1.12):
    m = max(abs(min(ys)), abs(max(ys))) * pad or 1.0
    return (-m, m)


def act_header(i, name):
    return (txt(328, 152, f"ACT {i+1}", 11, ORANGE, weight="700", ls="2.2")
            + txt(378, 152, name.upper(), 11, TEAL_DEEP, weight="700", ls="2.2"))


def caption(head, body1, body2=""):
    s = txt(56, 524, head, 21, INK, SERIF)
    s += txt(56, 552, body1, 14.5, INK)
    if body2:
        s += txt(56, 574, body2, 14.5, MUTED)
    return s


def trace_panel(geom, xs, ys, color, i, t0, t1, ylim=None, width=1.9, dash=None):
    pl = Plot(geom["x"], geom["y"], geom["w"], geom["h"],
              (min(xs), max(xs)), ylim or sym(xs, ys))
    d, ln = pl.path(xs, ys)
    c = draw_class(i, ln, t0, t1)
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return pl, (f'<path class="{c}" d="{d}" fill="none" stroke="{color}" '
                f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"'
                f'{extra}/>')


def zero_line(pl):
    yy = pl.Y(0)
    return (f'<line x1="{pl.x}" y1="{yy:.1f}" x2="{pl.x+pl.w}" y2="{yy:.1f}" '
            f'stroke="{BORDER}" stroke-width="1" stroke-dasharray="3 3"/>')


# =========================================================================
# ACT 1 -- frequency mixing
# =========================================================================
A = []
mix, tr = D["mixing"], D["mixing"]["trace"]
f1, f2, u0 = mix["params"]["f1"], mix["params"]["f2"], mix["params"]["u0"]

A.append(act_header(0, "Frequency mixing"))

A.append(label(IN["x"], IN["y"] - 10, "STRESS IN   u(t)"))
plin, s = trace_panel(IN, tr["t"], tr["u"], INK, 0, 0.7, 4.6)
A += [plin.frame(), zero_line(plin), s]
A.append(txt(IN["x"] + IN["w"] - 4, IN["y"] - 10,
             f"two pure tones added: f₁ = {f1}, f₂ = {f2}", 11, MUTED, anchor="end"))

A.append(label(OUT["x"], OUT["y"] - 10, "VOLTAGE OUT   y(t)"))
yl = sym(tr["t"], tr["y_nonlinear"] + tr["y_linear"])
plo = Plot(OUT["x"], OUT["y"], OUT["w"], OUT["h"], (min(tr["t"]), max(tr["t"])), yl)
A += [plo.frame(), zero_line(plo)]
for key, col, w in (("y_linear", TEAL, 1.7), ("y_nonlinear", ORANGE, 1.9)):
    d, ln = plo.path(tr["t"], tr[key])
    c = draw_class(0, ln, 1.0, 4.9)
    A.append(f'<path class="{c}" d="{d}" fill="none" stroke="{col}" stroke-width="{w}" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
A.append(txt(OUT["x"] + OUT["w"] - 4, OUT["y"] - 10,
             "the two traces look nearly identical — look at the spectrum instead",
             11, MUTED, anchor="end"))

# --- spectrum panel ---
# Axis floor is 1e-8: below that the "linear" model's off-tone bins are pure
# RK4 round-off, not physics, so plotting them would overstate the comparison.
FLOOR = 1e-8
sp = Plot(RP["x"] + 46, RP["y"] + 40, RP["w"] - 62, RP["h"] - 86,
          (-0.014, 0.6), (FLOOR, 1.0), ylog=True)
A.append(f'<rect x="{RP["x"]}" y="{RP["y"]}" width="{RP["w"]}" height="{RP["h"]}" rx="3" '
         f'fill="{PANEL}" stroke="{BORDER}" stroke-width="1"/>')
A.append(label(RP["x"] + 16, RP["y"] + 22, "SPECTRUM OF THE OUTPUT   |Y(f)|"))
for e in range(-8, 1, 2):
    yy = sp.Y(10.0 ** e)
    A.append(f'<line x1="{sp.x}" y1="{yy:.1f}" x2="{sp.x+sp.w}" y2="{yy:.1f}" '
             f'stroke="{BORDER}" stroke-width="0.7" stroke-dasharray="2 4"/>')
    A.append(txt(sp.x - 7, yy + 3.2, f"10{'⁻' if e else ''}"
                 + ("".join("⁰¹²³⁴⁵⁶⁷⁸⁹"[int(ch)]
                            for ch in str(abs(e))) if e else "⁰"),
                 9.5, FAINT, anchor="end"))
A.append(f'<line x1="{sp.x}" y1="{sp.y+sp.h:.1f}" x2="{sp.x+sp.w}" y2="{sp.y+sp.h:.1f}" '
         f'stroke="{BORDER}" stroke-width="1"/>')
for fv in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
    A.append(txt(sp.X(fv), sp.y + sp.h + 15, f"{fv:g}", 9.5, FAINT, anchor="middle"))
A.append(txt(sp.X(0.3), sp.y + sp.h + 30, "frequency   [1/t₀]", 10.5, MUTED, anchor="middle"))

fr = mix["nonlinear"]["freqs"]
mg_nl, mg_li = mix["nonlinear"]["mag"], mix["linear"]["mag"]
tone_bins = {round(f1, 3), round(f2, 3)}
new_lines = [(0.00, "DC"), (round(f2 - f1, 3), "f₂−f₁"), (round(2 * f1, 3), "2f₁"),
             (round(f1 + f2, 3), "f₁+f₂"), (round(2 * f2, 3), "2f₂")]
second_order = {fv for fv, _ in new_lines}


def stems(mags, color, keep, bw, opacity=1.0):
    r = []
    for fv, mv in zip(fr, mags):
        if fv > 0.605 or round(fv, 3) not in keep or mv < FLOOR:
            continue
        y_top, y_bot = sp.Y(mv), sp.Y(FLOOR)
        r.append(f'<rect x="{sp.X(fv)-bw/2:.2f}" y="{y_top:.2f}" width="{bw}" '
                 f'height="{max(y_bot-y_top, 0.6):.2f}" fill="{color}" '
                 f'opacity="{opacity}"/>')
    return "".join(r)


all_bins = {round(f, 3) for f in fr}
tail_bins = all_bins - tone_bins - second_order

# stage 1: the linear reference -- two lines and nothing else above the floor
g1 = grow_class(0, 5.1, 6.0)
A.append(f'<g class="{g1}">{stems(mg_li, TEAL, tone_bins, 3.6)}</g>')
lab1 = fade_in_class(0, 6.1)
A.append(f'<g class="{lab1}">'
         + txt(sp.X(f1), sp.Y(mg_nl[int(round(f1/0.01))]) - 9, "f₁", 11.5, TEAL_DEEP,
               weight="700", anchor="middle")
         + txt(sp.X(f2), sp.Y(mg_nl[int(round(f2/0.01))]) - 9, "f₂", 11.5, TEAL_DEEP,
               weight="700", anchor="middle")
         + txt(sp.x + sp.w, sp.y + 11,
               "nonlinearity off: nothing else clears the floor",
               10.5, TEAL_DEEP, anchor="end")
         + "</g>")

# stage 2: the second-order lines the real fiber manufactures
g2 = grow_class(0, 6.9, 7.9)
A.append(f'<g class="{g2}">{stems(mg_nl, ORANGE, second_order, 4.2)}</g>')
lab2 = fade_in_class(0, 7.9)
inner = ""
for fv, name in new_lines:
    idx = int(round(fv / 0.01))
    inner += txt(sp.X(fv), sp.Y(max(mg_nl[idx], FLOOR)) - 8, name, 10.5, ORANGE,
                 weight="700", anchor="middle")
A.append(f'<g class="{lab2}">{inner}</g>')

# stage 3: and the tail of higher-order products underneath
g3 = grow_class(0, 8.5, 9.4)
A.append(f'<g class="{g3}">{stems(mg_nl, ORANGE, tail_bins, 2.2, 0.38)}</g>')
lab3 = fade_in_class(0, 9.4)
A.append(f'<g class="{lab3}">'
         + f'<rect x="{sp.x+sp.w-104:.1f}" y="{sp.y+sp.h-14:.1f}" width="2.2" '
           f'height="10" fill="{ORANGE}" opacity="0.38"/>'
         + txt(sp.x + sp.w - 96, sp.y + sp.h - 5, "higher-order products", 10, ORANGE,
               extra=' opacity="0.85"')
         + "</g>")

A.append(caption(
    "Frequencies it was never given",
    "Feed the fiber two pure tones and its voltage comes back carrying their sum, their difference "
    "and their doubles — lines that were",
    "nowhere in the input. Switch the nonlinearity off and those lines fall away into the numerical "
    f"floor, {D['mixing']['order_gap']:.1f} orders of magnitude down."))

# =========================================================================
# ACT 2 -- energy detection
# =========================================================================
B = []
et, en = D["energy_trace"], D["energy"]
B.append(act_header(1, "Energy detection"))

# Act 2 uses three stacked strips: the running average is ~10x smaller than the
# raw swing, so sharing one vertical scale would hide the whole point.
IN2 = dict(x=56, y=226, w=498, h=74)
RAW2 = dict(x=56, y=330, w=498, h=52)
AVG2 = dict(x=56, y=408, w=498, h=52)

B.append(label(IN2["x"], IN2["y"] - 10, "STRESS IN   u(t)"))
pl2, s = trace_panel(IN2, et["t"], et["u"], INK, 1, 0.7, 4.6)
B += [pl2.frame(), zero_line(pl2), s]
env = fade_in_class(1, 4.6)
d_env, _ = pl2.path(et["t"], et["amp"])
d_env2, _ = pl2.path(et["t"], [-v for v in et["amp"]])
B.append(f'<g class="{env}">'
         f'<path d="{d_env}" fill="none" stroke="{FAINT}" stroke-width="1.4" stroke-dasharray="4 3"/>'
         f'<path d="{d_env2}" fill="none" stroke="{FAINT}" stroke-width="1.4" stroke-dasharray="4 3"/>'
         f'</g>')
lv = et["params"]["levels"]
B.append(txt(IN2["x"] + IN2["w"] - 4, IN2["y"] - 10,
             f"one tone; amplitude steps {lv[0]} → {lv[1]} → {lv[2]}", 11, MUTED, anchor="end"))

B.append(label(RAW2["x"], RAW2["y"] - 9, "VOLTAGE OUT   y(t)"))
plr = Plot(RAW2["x"], RAW2["y"], RAW2["w"], RAW2["h"], (min(et["t"]), max(et["t"])),
           sym(et["t"], et["nonlinear"] + et["linear"]))
B += [plr.frame(), zero_line(plr)]
for key, col in (("linear", TEAL), ("nonlinear", ORANGE)):
    d, ln = plr.path(et["t"], et[key])
    c = draw_class(1, ln, 1.0, 4.9)
    B.append(f'<path class="{c}" d="{d}" fill="none" stroke="{col}" stroke-width="1.2" '
             f'opacity="0.55" stroke-linejoin="round"/>')
B.append(txt(RAW2["x"] + RAW2["w"] - 4, RAW2["y"] - 9,
             "both fibers swing symmetrically about zero", 11, MUTED, anchor="end"))

B.append(label(AVG2["x"], AVG2["y"] - 9, "ITS RUNNING AVERAGE   ⟨y⟩"))
dc_max = max(et["nonlinear_dc"])
pla = Plot(AVG2["x"], AVG2["y"], AVG2["w"], AVG2["h"], (min(et["t"]), max(et["t"])),
           (-dc_max * 0.16, dc_max * 1.18))
B += [pla.frame(), zero_line(pla)]
for key, col, w in (("linear_dc", TEAL, 2.4), ("nonlinear_dc", ORANGE, 2.8)):
    d, ln = pla.path(et["t"], et[key])
    c = draw_class(1, ln, 1.2, 5.4)
    B.append(f'<path class="{c}" d="{d}" fill="none" stroke="{col}" stroke-width="{w}" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
B.append(txt(AVG2["x"] + AVG2["w"] - 4, AVG2["y"] - 9,
             "orange climbs in steps; teal never leaves zero", 11, MUTED, anchor="end"))
_mag = ((plr.y1 - plr.y0) / plr.h) / ((pla.y1 - pla.y0) / pla.h)
B.append(txt(AVG2["x"] + 4, AVG2["y"] + AVG2["h"] + 14,
             f"note the vertical scale: this strip is magnified {_mag:.0f}× "
             f"relative to the raw trace above", 10, FAINT))

# --- right: DC vs amplitude ---
amps, ynl, yli = en["amps"], en["nonlinear"], en["linear"]
ep = Plot(RP["x"] + 56, RP["y"] + 34, RP["w"] - 76, RP["h"] - 74,
          (0, max(amps) * 1.04), (-0.004, max(ynl) * 1.12))
B.append(f'<rect x="{RP["x"]}" y="{RP["y"]}" width="{RP["w"]}" height="{RP["h"]}" rx="3" '
         f'fill="{PANEL}" stroke="{BORDER}" stroke-width="1"/>')
B.append(label(RP["x"] + 16, RP["y"] + 22, "AVERAGE OUTPUT ⟨y⟩  VS  DRIVE AMPLITUDE u₀"))
for frac in (0, 0.25, 0.5, 0.75, 1.0):
    v = frac * max(ynl) * 1.12
    yy = ep.Y(v)
    B.append(f'<line x1="{ep.x}" y1="{yy:.1f}" x2="{ep.x+ep.w}" y2="{yy:.1f}" '
             f'stroke="{BORDER}" stroke-width="0.7" stroke-dasharray="2 4"/>')
    B.append(txt(ep.x - 8, yy + 3.2, f"{v:.02f}", 9.5, FAINT, anchor="end"))
B.append(f'<line x1="{ep.x}" y1="{ep.Y(0):.1f}" x2="{ep.x+ep.w}" y2="{ep.Y(0):.1f}" '
         f'stroke="{BORDER}" stroke-width="1"/>')
for av in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3):
    B.append(txt(ep.X(av), ep.y + ep.h + 15, f"{av:g}", 9.5, FAINT, anchor="middle"))
B.append(txt(ep.X(0.16), ep.y + ep.h + 30, "drive amplitude   u₀", 10.5, MUTED, anchor="middle"))

for key, col, w, t0, t1 in (("linear", TEAL, 2.4, 5.2, 6.6), ("nonlinear", ORANGE, 2.8, 5.2, 6.6)):
    d, ln = ep.path(amps, en[key])
    c = draw_class(1, ln, t0, t1)
    B.append(f'<path class="{c}" d="{d}" fill="none" stroke="{col}" stroke-width="{w}" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
dots = fade_in_class(1, 6.6)
inner = ""
for av, yv in zip(amps, ynl):
    inner += f'<circle cx="{ep.X(av):.1f}" cy="{ep.Y(yv):.1f}" r="2.6" fill="{ORANGE}"/>'
inner += txt(ep.x + 10, ep.y + 16, "slope of a log–log fit:  2.06", 11.5, ORANGE,
             weight="700")
inner += txt(ep.x + 10, ep.y + 32, "output ∝ amplitude² — i.e. input power", 10.5, MUTED)
B.append(f'<g class="{dots}">{inner}</g>')

B.append(caption(
    "A meter that measures loudness",
    "The input has no average — it swings symmetrically about zero. Yet the fiber's output "
    "acquires a steady offset that grows",
    "as the square of the drive: a passive power meter, built from nothing but rectification. "
    "The linear fiber reports zero at every amplitude."))

# =========================================================================
# ACT 3 -- AM demodulation
# =========================================================================
Cc = []
am = D["am"]
Cc.append(act_header(2, "Amplitude demodulation"))

Cc.append(label(IN["x"], IN["y"] - 10, "STRESS IN   u(t)"))
pl3, s = trace_panel(IN, am["t"], am["u"], INK, 2, 0.7, 4.6)
Cc += [pl3.frame(), zero_line(pl3), s]
Cc.append(txt(IN["x"] + IN["w"] - 4, IN["y"] - 10,
              f"carrier fᶜ = {am['params']['fc']}, modulated at fᵐ = {am['params']['fm']}",
              11, MUTED, anchor="end"))

Cc.append(label(OUT["x"], OUT["y"] - 10, "VOLTAGE OUT   y(t)   — RAW"))
plo3 = Plot(OUT["x"], OUT["y"], OUT["w"], OUT["h"], (min(am["t"]), max(am["t"])),
            sym(am["t"], am["nonlinear_raw"]))
Cc += [plo3.frame(), zero_line(plo3)]
d, ln = plo3.path(am["t"], am["nonlinear_raw"])
c = draw_class(2, ln, 1.0, 4.9)
Cc.append(f'<path class="{c}" d="{d}" fill="none" stroke="{ORANGE}" stroke-width="1.3" '
          f'opacity="0.6" stroke-linejoin="round"/>')
Cc.append(txt(OUT["x"] + OUT["w"] - 4, OUT["y"] - 10,
              "a fast blur — the message is not visible here", 11, MUTED, anchor="end"))

# --- right: low-passed output ---
def norm(v):
    m = max(abs(min(v)), abs(max(v))) or 1.0
    return [a / m for a in v]

nl_n = norm(am["nonlinear"])
ref_n = norm(am["reference_sq_envelope"])
mx = max(abs(min(am["nonlinear"])), abs(max(am["nonlinear"])))
li_n = [a / mx for a in am["linear"]]

lp = Plot(RP["x"] + 30, RP["y"] + 44, RP["w"] - 52, RP["h"] - 88,
          (min(am["t"]), max(am["t"])), (-1.25, 1.35))
Cc.append(f'<rect x="{RP["x"]}" y="{RP["y"]}" width="{RP["w"]}" height="{RP["h"]}" rx="3" '
          f'fill="{PANEL}" stroke="{BORDER}" stroke-width="1"/>')
Cc.append(label(RP["x"] + 16, RP["y"] + 22, "THE SAME OUTPUT, LOW‑PASS FILTERED"))
Cc.append(f'<line x1="{lp.x}" y1="{lp.Y(0):.1f}" x2="{lp.x+lp.w}" y2="{lp.Y(0):.1f}" '
          f'stroke="{BORDER}" stroke-width="1" stroke-dasharray="3 3"/>')

d, ln = lp.path(am["t"], ref_n)
c = draw_class(2, ln, 5.1, 6.3)
Cc.append(f'<path class="{c}" d="{d}" fill="none" stroke="{INK}" stroke-width="4" '
          f'opacity="0.16" stroke-linejoin="round" stroke-linecap="round"/>')
d, ln = lp.path(am["t"], nl_n)
c = draw_class(2, ln, 5.4, 6.9)
Cc.append(f'<path class="{c}" d="{d}" fill="none" stroke="{ORANGE}" stroke-width="2.8" '
          f'stroke-linejoin="round" stroke-linecap="round"/>')
d, ln = lp.path(am["t"], li_n)
c = draw_class(2, ln, 5.4, 6.9)
Cc.append(f'<path class="{c}" d="{d}" fill="none" stroke="{TEAL}" stroke-width="2.4" '
          f'stroke-linejoin="round" stroke-linecap="round"/>')

leg = fade_in_class(2, 7.0)
inner = (f'<line x1="{lp.x+2}" y1="{lp.y-12:.1f}" x2="{lp.x+22}" y2="{lp.y-12:.1f}" '
         f'stroke="{INK}" stroke-width="4" opacity="0.16"/>'
         + txt(lp.x + 28, lp.y - 8, "the envelope actually sent, squared", 10.5, MUTED)
         + txt(lp.x + lp.w, lp.y - 8, "correlation 0.975", 11.5, ORANGE, weight="700", anchor="end")
         + txt(lp.x + 2, lp.y + lp.h - 7,
               "linear fiber: 2400× smaller, correlation 0.001", 10.5, TEAL_DEEP))
Cc.append(f'<g class="{leg}">{inner}</g>')
Cc.append(txt(lp.X((min(am["t"]) + max(am["t"]))/2), lp.y + lp.h + 28,
              "time   [t₀]", 10.5, MUTED, anchor="middle"))

Cc.append(caption(
    "Reading the message out of the shaking",
    "A slow signal riding on a fast vibration. Averaging the fiber's own output recovers that slow "
    "signal almost perfectly,",
    "with no amplifier, no clock and no power supply. The linear fiber recovers nothing: it can only "
    "relay the frequencies it is handed."))

# ---------------------------------------------------------------------------
for i, body in enumerate((A, B, Cc)):
    add(f'<g class="{act_class(i)}">' + "".join(body) + "</g>")

style = ("<style>\n" + "\n".join(RULES) + "\n" + "\n".join(KEYFRAMES)
         + "\n@media (prefers-reduced-motion:reduce){*{animation-duration:0s !important;"
           "animation-iteration-count:1 !important}}\n</style>")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
       f'height="{H}" font-family="{SANS}" role="img" '
       f'aria-label="Three computations performed by a single nonlinear protein fiber, '
       f'simulated from the white paper model">'
       + f"<title>The mess is the point — three tricks of a nonlinear fiber</title>"
       + style + "".join(out) + "</svg>")

open("fiber-three-tricks.svg", "w").write(svg)
print(f"wrote fiber-three-tricks.svg  ({len(svg)/1024:.1f} KB, "
      f"{len(KEYFRAMES)} keyframe blocks)")
