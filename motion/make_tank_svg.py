"""
Builds `bucket-reservoir.svg` -- an animated, self-contained SVG retelling
Fernando & Sojakka's "Pattern recognition in a bucket" (white paper s3.1).

Every number and every water frame comes from tank_sim.py: a damped 2D wave
equation, a square-law saturating camera, and one ridge-regression readout
trained and tested on independent noise draws.

The rippling water is 388 SMIL colour animations (one per in-tank camera cell)
playing a seamless 2-drive-period loop. Everything else is CSS keyframes on a
shared 34 s act timeline.
"""

import json
import math

T = json.load(open("tank_data.json"))
M = T["meta"]

W, H = 1120, 792
DUR = 34.0
ACT_T0 = [0.0, 8.5, 17.0, 25.5]
ACT_LEN = 8.5
LOOP = 2.6                      # seconds for the 2-period water loop

INK = "#111827"
MUTED = "#6B7280"
FAINT = "#9CA3AF"
BORDER = "#D8D6D2"
PANEL = "#FFFFFF"
BG = "#F2F0EC"
TEAL = "#0E7C7B"
TEAL_DEEP = "#0B4F4E"
ORANGE = "#EA580C"
SLATE = "#2F3E46"
PALE = "#EFEDE7"
SANS = "'DM Sans','Helvetica Neue',Helvetica,Arial,sans-serif"
SERIF = "'DM Serif Display',Georgia,'Times New Roman',serif"

KEYFRAMES, RULES = [], []


def kf(stops, prop, fmt=lambda v: f"{v}"):
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


def act_class(i, first=0.5, last=7.8, gone=8.3):
    t0 = ACT_T0[i]
    stops = [] if t0 == 0 else [(0.0, 0)]
    stops += [(t0, 0), (t0 + first, 1), (t0 + last, 1), (t0 + gone, 0), (DUR, 0)]
    return anim(kf(stops, "opacity"), "opacity:0;")


def show_from(t_abs, dur=0.6):
    """Visible from t_abs to the end of the loop."""
    stops = [(0.0, 0)] + ([] if t_abs == 0 else [(t_abs, 0)]) + [(t_abs + dur, 1), (DUR, 1)]
    return anim(kf(stops, "opacity"), "opacity:0;")


def fade_in(i, t_local, dur=0.5):
    return show_from(ACT_T0[i] + t_local, dur)


def draw_class(i, length, t0, t1):
    a, b = ACT_T0[i] + t0, ACT_T0[i] + t1
    stops = [(0.0, length)] + ([] if a == 0 else [(a, length)]) + [(b, 0.0), (DUR, 0.0)]
    return anim(kf(stops, "stroke-dashoffset", lambda v: f"{v:.1f}"),
                f"stroke-dasharray:{length:.1f};stroke-dashoffset:{length:.1f};")


def hexlerp(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a[k] + (b[k]-a[k])*t):02x}" for k in range(3))


def water(v):
    """Diverging map: crests teal, troughs slate, still water pale."""
    v = max(-1.0, min(1.0, v))
    t = abs(v) ** 0.75
    return hexlerp(PALE, TEAL if v >= 0 else SLATE, t)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def txt(x, y, s, size=13, fill=INK, family=SANS, weight="400", anchor="start",
        ls="0", extra=""):
    s = esc(s)
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
            f'letter-spacing="{ls}"{extra}>{s}</text>')


def label(x, y, s, fill=MUTED):
    return txt(x, y, s, 10.5, fill, weight="600", ls="1.4")


out = []
add = out.append

add(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
add(txt(56, 50, "Pattern recognition in a bucket", 31, INK, SERIF))
add(txt(56, 76, "A tank of water computes something its own input cannot", 14.5, MUTED))
add(f'<line x1="56" y1="97" x2="{W-56}" y2="97" stroke="{BORDER}" stroke-width="1"/>')

# ===========================================================================
# the tank (persistent)
# ===========================================================================
CAM = M["CAM"]
TCX, TCY, TR = 286, 348, 158
cell = 2 * TR / CAM
inside = T["inside"]
frames = T["frames"]
nf = len(frames)

add(f'<g>')
add(f'<circle cx="{TCX}" cy="{TCY}" r="{TR+9}" fill="none" stroke="{BORDER}" stroke-width="9"/>')
add(f'<circle cx="{TCX}" cy="{TCY}" r="{TR+3}" fill="{PALE}"/>')
add(f'<clipPath id="tank"><circle cx="{TCX}" cy="{TCY}" r="{TR+2}"/></clipPath>')

# still water shown during act 1, then the ripple loop takes over
still = anim(kf([(0.0, 1), (ACT_T0[1] - 0.4, 1), (ACT_T0[1] + 0.3, 0), (DUR, 0)], "opacity"))
add(f'<circle class="{still}" cx="{TCX}" cy="{TCY}" r="{TR+2}" fill="{PALE}"/>')

ripple_on = show_from(ACT_T0[1] - 0.1, 0.7)
add(f'<g class="{ripple_on}" clip-path="url(#tank)">')
for j in range(CAM):
    for i in range(CAM):
        if not inside[j][i]:
            continue
        x = TCX - TR + i * cell
        y = TCY - TR + j * cell
        vals = ";".join(water(frames[f][j][i]) for f in range(nf))
        add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell+0.6:.2f}" height="{cell+0.6:.2f}" '
            f'fill="{water(frames[0][j][i])}">'
            f'<animate attributeName="fill" values="{vals};{water(frames[0][j][i])}" '
            f'dur="{LOOP}s" repeatCount="indefinite" calcMode="linear"/></rect>')
add("</g>")

# motors on the rim
mot = []
for k, ang in enumerate(M["motor_angles"]):
    a = math.radians(ang)
    mx = TCX + (TR - 14) * math.cos(a)
    my = TCY + (TR - 14) * math.sin(a)
    mot.append((mx, my))
    add(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="14" fill="{BG}" opacity="0.92"/>')
    add(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="9" fill="{PANEL}" stroke="{INK}" stroke-width="2"/>')
    add(txt(mx, my + 4, "AB"[k], 11, INK, SANS, "700", "middle"))
    lx = TCX + (TR + 34) * math.cos(a)
    ly = TCY + (TR + 34) * math.sin(a)
    add(txt(lx, ly + 4, f"motor {'AB'[k]}", 11, MUTED, anchor="middle"))
add(txt(TCX, TCY + TR + 74, "one tank of water. Nothing inside it is ever adjusted.",
        12, MUTED, anchor="middle"))
add(label(TCX, 128, "THE RESERVOIR", TEAL_DEEP))
add("</g>")

# shutter pulse during act 3
sh = anim(kf([(0.0, 0), (ACT_T0[2] + 1.0, 0), (ACT_T0[2] + 1.25, 0.85),
              (ACT_T0[2] + 2.1, 0), (DUR, 0)], "opacity"))
add(f'<circle class="{sh}" cx="{TCX}" cy="{TCY}" r="{TR+6}" fill="none" '
    f'stroke="{ORANGE}" stroke-width="4"/>')

# ===========================================================================
RX, RY, RW, RH = 520, 140, 544, 430


def caption(head, body1, body2=""):
    s = txt(56, 640, head, 21, INK, SERIF)
    s += txt(56, 668, body1, 14.5, INK)
    if body2:
        s += txt(56, 690, body2, 14.5, MUTED)
    return s


def act_header(i, name):
    return (txt(RX, 128, f"STEP {i+1}", 11, ORANGE, weight="700", ls="2.2")
            + txt(RX + 62, 128, name.upper(), 11, TEAL_DEEP, weight="700", ls="2.2"))


def rpanel():
    return (f'<rect x="{RX}" y="{RY}" width="{RW}" height="{RH}" rx="3" fill="{PANEL}" '
            f'stroke="{BORDER}" stroke-width="1"/>')


PATS = ["00", "01", "10", "11"]
LAB = T["labels"]

# ===========================================================================
# ACT 1 -- the problem
# ===========================================================================
A = [act_header(0, "The problem"), rpanel()]
A.append(txt(RX + 28, RY + 40, "Two switches. Answer YES when exactly one is on.",
             15, INK, weight="600"))
A.append(txt(RX + 28, RY + 62, "This is exclusive-or, and no straight line can carve it apart.",
             13, MUTED))

# truth table
tx, ty = RX + 30, RY + 96
A.append(label(tx + 4, ty - 8, "A"))
A.append(label(tx + 40, ty - 8, "B"))
A.append(txt(tx + 118, ty - 8, "ANSWER", 10.5, MUTED, weight="600", ls="1.4", anchor="middle"))
A.append(f'<line x1="{tx}" y1="{ty-2}" x2="{tx+148}" y2="{ty-2}" stroke="{BORDER}" stroke-width="1"/>')
for r, p in enumerate(PATS):
    yy = ty + 14 + r * 25
    ans = LAB[p]
    col = ORANGE if ans else SLATE
    A.append(txt(tx + 4, yy, p[0], 13.5, INK, weight="600"))
    A.append(txt(tx + 40, yy, p[1], 13.5, INK, weight="600"))
    A.append(f'<rect x="{tx+92}" y="{yy-11}" width="52" height="16" rx="8" fill="{col}" opacity="0.13"/>')
    A.append(txt(tx + 118, yy, "yes" if ans else "no", 12, col, weight="700", anchor="middle"))

# input space
gx, gy, gs = RX + 250, RY + 108, 118
A.append(label(gx, gy - 18, "THE RAW INPUT SPACE"))
A.append(f'<rect x="{gx}" y="{gy}" width="{gs}" height="{gs}" fill="none" '
         f'stroke="{BORDER}" stroke-width="1"/>')
A.append(f'<clipPath id="ispace"><rect x="{gx}" y="{gy}" width="{gs}" height="{gs}"/></clipPath>')
spin = anim(kf([(0.0, 0), (ACT_T0[0] + 1.6, 0), (ACT_T0[0] + 7.4, 900), (DUR, 900)],
               "transform", lambda v: f"rotate({v:.1f}deg)"),
            f"transform-box:view-box;transform-origin:{gx+gs/2}px {gy+gs/2}px;")
A.append(f'<g clip-path="url(#ispace)"><g class="{spin}">'
         f'<line x1="{gx-90}" y1="{gy+gs/2}" x2="{gx+gs+90}" y2="{gy+gs/2}" '
         f'stroke="{ORANGE}" stroke-width="2" stroke-dasharray="6 4"/></g></g>')
for p in PATS:
    px = gx + (int(p[0]) * 0.72 + 0.14) * gs
    py = gy + ((1 - int(p[1])) * 0.72 + 0.14) * gs
    col = ORANGE if LAB[p] else SLATE
    A.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="{col}"/>')
    A.append(txt(px, py + 3.5, p, 9.5, "#FFFFFF", SANS, "700", "middle"))
A.append(txt(gx, gy + gs + 16, "switch A →", 10.5, FAINT))
A.append(txt(gx - 6, gy - 4, "switch B ↑", 10.5, FAINT, anchor="end"))

res = fade_in(0, 5.2)
A.append(f'<g class="{res}">'
         + txt(RX + 30, RY + 300, f"{T['acc']['raw_test']*100:.0f}%", 46, SLATE, SERIF)
         + txt(RX + 30, RY + 330, "best a single straight line can do on the raw switches",
               12.5, MUTED)
         + txt(RX + 30, RY + 348, "— exactly chance. The information is there; the shape is wrong.",
               12.5, MUTED)
         + "</g>")

A.append(caption(
    "A problem with the wrong shape",
    "Two switches, and the answer is YES when exactly one of them is on. A single linear rule "
    "cannot express that,",
    "no matter how its coefficients are tuned. So we will not tune it — we will change the shape "
    "of the question instead."))

# ===========================================================================
# ACT 2 -- the machine
# ===========================================================================
B = [act_header(1, "The machine"), rpanel()]
B.append(txt(RX + 28, RY + 40, "Drive the switches into the water and watch.", 15, INK, weight="600"))
B.append(txt(RX + 28, RY + 62,
             "Each switch turns a motor at the rim. The waves cross, reflect and interfere.",
             13, MUTED))

stages = [
    ("two bits", "u", "the input", "the motors stir the water"),
    ("water surface", "ψ", "the reservoir — fixed, never trained", "a camera watches it"),
    (f"{M['n_observables']} camera cells", "x", "the measurement", "one line is fitted"),
    ("one number", "ŷ", "the answer", None),
]
by = RY + 108
for k, (name, symb, sub, arrow) in enumerate(stages):
    yy = by + k * 60
    c = fade_in(1, 1.4 + k * 0.75)
    trained = k == 3
    col = ORANGE if trained else TEAL_DEEP
    dash = "" if trained else ' stroke-dasharray="4 3"'
    inner = (f'<rect x="{RX+30}" y="{yy}" width="200" height="40" rx="4" '
             f'fill="{col}" fill-opacity="0.08" stroke="{col}" stroke-width="1.4"{dash}/>'
             + txt(RX + 44, yy + 25, symb, 15, col, SERIF)
             + txt(RX + 66, yy + 25, name, 13, INK, weight="600")
             + txt(RX + 246, yy + 20, sub, 12, MUTED)
             + (txt(RX + 246, yy + 35, "nothing to learn", 11, FAINT) if k in (0, 1, 2) else
                txt(RX + 246, yy + 35, "one linear fit — the only trained part", 11, ORANGE,
                    weight="600")))
    if arrow:
        inner += (f'<path d="M{RX+130},{yy+40} L{RX+130},{yy+60}" stroke="{FAINT}" '
                  f'stroke-width="1.4" marker-end="url(#ar)"/>'
                  + txt(RX + 140, yy + 55, arrow, 10.5, FAINT))
    B.append(f'<g class="{c}">{inner}</g>')

note = fade_in(1, 5.4)
B.append(f'<g class="{note}">'
         + txt(RX + 30, RY + 392, "Three of the four stages have nothing to learn.",
               13, TEAL_DEEP, weight="700")
         + "</g>")

B.append(caption(
    "Let the physics do the work",
    "Reservoir computing turns the usual arrangement inside out. The complicated part — the water — "
    "is left completely alone,",
    "and the only thing fitted to the task is one straight-line readout at the very end."))

# ===========================================================================
# ACT 3 -- what the camera sees
# ===========================================================================
Cc = [act_header(2, "What the camera sees"), rpanel()]
Cc.append(txt(RX + 28, RY + 40, "Open the shutter for two wave periods.", 15, INK, weight="600"))
Cc.append(txt(RX + 28, RY + 62,
              "The camera is a square-law sensor: it records brightness, which goes as the "
              "square of the", 13, MUTED))
Cc.append(txt(RX + 28, RY + 80, "surface height — then saturates. That squaring is where the "
              "nonlinearity comes from.", 13, MUTED))

def intensity_grid(img, x0, y0, size, cap=1.0):
    """Render one camera image; `cap` clips values the sensor could not reach."""
    s = (f'<rect x="{x0-3}" y="{y0-3}" width="{size+6}" height="{size+6}" rx="3" '
         f'fill="{PALE}" stroke="{BORDER}" stroke-width="1"/>')
    cs = size / CAM
    for j in range(CAM):
        for i in range(CAM):
            if not inside[j][i]:
                continue
            v = min(cap, img[j][i]) / cap
            s += (f'<rect x="{x0+i*cs:.2f}" y="{y0+j*cs:.2f}" width="{cs+0.4:.2f}" '
                  f'height="{cs+0.4:.2f}" fill="{hexlerp(PALE, TEAL_DEEP, min(1.0, max(v,0.0)**0.7))}"/>')
    return s


gsz = 84
gap = 22
gx0 = RX + 34
gy0 = RY + 104
for k, p in enumerate(PATS):
    x0 = gx0 + k * (gsz + gap)
    c = fade_in(2, 2.2 + k * 0.45)
    inner = intensity_grid(T["intensity"][p], x0, gy0, gsz)
    col = ORANGE if LAB[p] else SLATE
    inner += txt(x0 + gsz / 2, gy0 + gsz + 19, f"{p[0]} – {p[1]}", 13, INK, SANS, "700", "middle")
    inner += (f'<rect x="{x0+gsz/2-22}" y="{gy0+gsz+27}" width="44" height="15" rx="7.5" '
              f'fill="{col}" opacity="0.13"/>')
    inner += txt(x0 + gsz / 2, gy0 + gsz + 38, "yes" if LAB[p] else "no", 11, col,
                 SANS, "700", "middle")
    Cc.append(f'<g class="{c}">{inner}</g>')

# ---- the decisive comparison: what adding predicts vs what the water does ----
sum_img = [[T["intensity"]["01"][j][i] + T["intensity"]["10"][j][i]
            for i in range(CAM)] for j in range(CAM)]
over = max(v for row in sum_img for v in row)

cy2 = gy0 + gsz + 66
Cc.append(f'<line x1="{RX+34}" y1="{cy2-8}" x2="{RX+RW-34}" y2="{cy2-8}" '
          f'stroke="{BORDER}" stroke-width="1"/>')
key = fade_in(2, 4.4)
Cc.append(f'<g class="{key}">'
          + txt(RX + 34, cy2 + 12,
                "If the water were linear, 1–1 would be exactly 0–1 plus 1–0.", 13, INK)
          + "</g>")

s2 = 78
pairy = cy2 + 26
lx0 = RX + 60
rx0 = RX + 60 + s2 + 108
cmp1 = fade_in(2, 5.0)
Cc.append(f'<g class="{cmp1}">'
          + intensity_grid(sum_img, lx0, pairy, s2)
          + txt(lx0 + s2 / 2, pairy + s2 + 18, "0–1  plus  1–0", 11.5, MUTED,
                anchor="middle", weight="600")
          + txt(lx0 + s2 / 2, pairy + s2 + 33, "what adding predicts", 10.5, FAINT, anchor="middle")
          + txt(lx0 + s2 + 54, pairy + s2 / 2 + 8, "≠", 30, ORANGE, SERIF, anchor="middle")
          + intensity_grid(T["intensity"]["11"], rx0, pairy, s2)
          + txt(rx0 + s2 / 2, pairy + s2 + 18, "1–1", 11.5, MUTED, anchor="middle", weight="600")
          + txt(rx0 + s2 / 2, pairy + s2 + 33, "what the water does", 10.5, FAINT, anchor="middle")
          + "</g>")

cmp2 = fade_in(2, 6.0)
Cc.append(f'<g class="{cmp2}">'
          + txt(rx0 + s2 + 42, pairy + 24, "Adding predicts a brightness", 12.5, ORANGE, weight="700")
          + txt(rx0 + s2 + 42, pairy + 40, f"{over:.1f}× past what the sensor", 12.5, ORANGE, weight="700")
          + txt(rx0 + s2 + 42, pairy + 56, "can even reach.", 12.5, ORANGE, weight="700")
          + txt(rx0 + s2 + 42, pairy + 78, "That gap is the computation.", 12, MUTED)
          + "</g>")

Cc.append(caption(
    "Interference is the arithmetic",
    "Two motors running together do not simply add: their waves reinforce in some places and "
    "cancel in others, and the",
    "camera's squaring turns that pattern into a genuinely new quantity. Without it, this trick "
    "provably cannot work."))

# ===========================================================================
# ACT 4 -- the answer
# ===========================================================================
Dd = [act_header(3, "The answer"), rpanel()]
Dd.append(txt(RX + 28, RY + 40, "Now fit one straight line — to the camera cells.",
              15, INK, weight="600"))
Dd.append(txt(RX + 28, RY + 62,
              "Same linear rule that failed on the switches, same XOR target. Only the input "
              "has changed.", 13, MUTED))

# The readout lands every run at almost exactly -1 or +1, so a 2-D scatter
# collapses into two blobs. A strip plot per input pattern shows all 40 runs
# and, more usefully, which pattern went to which side.
sc = T["scatter"]
z1, tags = sc["z1"], sc["tags"]
x0v, x1v = -1.32, 1.32
PX, PY, PW, PH = RX + 92, RY + 100, RW - 148, 168
ROW = PH / 4


def SX(v):
    return PX + (v - x0v) / (x1v - x0v) * PW


Dd.append(f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="{BG}" '
          f'stroke="{BORDER}" stroke-width="1" rx="2"/>')
bl = fade_in(3, 1.5)
Dd.append(f'<g class="{bl}">'
          f'<rect x="{PX}" y="{PY}" width="{SX(0)-PX:.1f}" height="{PH}" fill="{SLATE}" opacity="0.05"/>'
          f'<rect x="{SX(0):.1f}" y="{PY}" width="{PX+PW-SX(0):.1f}" height="{PH}" fill="{ORANGE}" opacity="0.05"/>'
          f'<line x1="{SX(0):.1f}" y1="{PY-4}" x2="{SX(0):.1f}" y2="{PY+PH+4}" stroke="{INK}" '
          f'stroke-width="1.8" stroke-dasharray="5 4"/>'
          + txt(SX(0), PY - 10, "the readout's dividing line", 10.5, INK,
                weight="600", anchor="middle")
          + txt(PX + 10, PY + PH + 16, "◀  it answers NO", 11, SLATE, weight="700")
          + txt(PX + PW - 10, PY + PH + 16, "it answers YES  ▶", 11, ORANGE,
                weight="700", anchor="end")
          + "</g>")

for r, p in enumerate(PATS):
    ry = PY + (r + 0.5) * ROW
    want = LAB[p]
    col = ORANGE if want else SLATE
    Dd.append(f'<line x1="{PX}" y1="{PY + (r+1)*ROW:.1f}" x2="{PX+PW}" '
              f'y2="{PY + (r+1)*ROW:.1f}" stroke="{BORDER}" stroke-width="0.7"/>'
              if r < 3 else "")
    Dd.append(txt(PX - 14, ry + 4, f"{p[0]} – {p[1]}", 12.5, INK, weight="700", anchor="end"))
    Dd.append(txt(PX - 14, ry + 17, "should say " + ("yes" if want else "no"), 9.5,
                  FAINT, anchor="end"))
    vals = [v for v, t in zip(z1, tags) if t == p]
    for k, v in enumerate(vals):
        # deterministic vertical spread so all ten runs are visible
        jy = ry + ((k % 5) - 2) * 4.4 + (2.2 if k >= 5 else 0)
        c = fade_in(3, 2.3 + r * 0.42 + (k % 5) * 0.05)
        Dd.append(f'<circle class="{c}" cx="{SX(v):.1f}" cy="{jy:.1f}" r="4.2" '
                  f'fill="{col}" fill-opacity="0.8"/>')

Dd.append(txt(PX + PW / 2, PY + PH + 36,
              "each dot is one run the readout had never seen — 40 in all",
              11, MUTED, anchor="middle"))

fin = fade_in(3, 4.6)
Dd.append(f'<g class="{fin}">'
          + txt(RX + 34, RY + 384, f"{T['acc']['res_test']*100:.0f}%", 44, ORANGE, SERIF)
          + txt(RX + 152, RY + 366,
                f"correct on held-out runs, up from {T['acc']['raw_test']*100:.0f}%",
                13.5, INK, weight="600")
          + txt(RX + 152, RY + 384,
                f"{M['n_observables']} cells are read, but only about {M['rank_sigma']} "
                "carry independent information", 11.5, MUTED)
          + txt(RX + 152, RY + 400,
                "unchanged across four orders of magnitude of regularisation", 11.5, MUTED)
          + "</g>")

Dd.append(caption(
    "The water changed the shape of the question",
    "Nothing was taught to the tank. Its ripples simply spread two bits across hundreds of "
    "vantage points, and in that",
    "spread the answer became something a straight line could reach. This is what a "
    "computational fiber is being asked to do."))

# ===========================================================================
add(f'<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" '
    f'markerHeight="5" orient="auto"><path d="M0,1 L8,5 L0,9" fill="none" '
    f'stroke="{FAINT}" stroke-width="1.6"/></marker></defs>')

for i, body in enumerate((A, B, Cc, Dd)):
    add(f'<g class="{act_class(i)}">' + "".join(body) + "</g>")

# progress bar
pbx, pby, pbw = 56, 724, W - 112
seg = (pbw - 24) / 4
for i in range(4):
    x = pbx + i * (seg + 8)
    add(f'<rect x="{x:.1f}" y="{pby}" width="{seg:.1f}" height="3" rx="1.5" fill="{BORDER}"/>')
    name = kf([(0.0, 0.0)] + ([] if ACT_T0[i] == 0 else [(ACT_T0[i], 0.0)])
              + [(ACT_T0[i] + ACT_LEN, 1.0), (DUR, 1.0)],
              "transform", lambda v: f"scaleX({v:.3f})")
    c = anim(name, "transform-box:fill-box;transform-origin:left;transform:scaleX(0);")
    add(f'<rect class="{c}" x="{x:.1f}" y="{pby}" width="{seg:.1f}" height="3" rx="1.5" fill="{ORANGE}"/>')

add(txt(56, 756, "Simulated, not illustrated.", 11.5, MUTED, weight="600"))
add(txt(196, 756,
        f"Damped 2D wave equation on a {M['N']}×{M['N']} grid (γ·dt={M['gamma']}, c={M['c']}), "
        f"read by a saturating square-law camera on a {CAM}×{CAM} grid. The water frames above "
        f"are {nf} consecutive steps of that simulation.", 11, FAINT))
add(txt(56, 772,
        "One ridge-regression readout, trained on 40 runs and scored on 40 independent runs. "
        "After Fernando & Sojakka (2003), “Pattern recognition in a bucket”.", 11, FAINT))

style = ("<style>\n" + "\n".join(RULES) + "\n" + "\n".join(KEYFRAMES)
         + "\n@media (prefers-reduced-motion:reduce){*{animation-duration:0s !important;"
           "animation-iteration-count:1 !important}}\n</style>")

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
       f'height="{H}" font-family="{SANS}" role="img" '
       f'aria-label="A simulated ripple tank used as a physical reservoir computer solving '
       f'exclusive-or">'
       + "<title>Pattern recognition in a bucket</title>"
       + style + "".join(out) + "</svg>")

open("bucket-reservoir.svg", "w").write(svg)
print(f"wrote bucket-reservoir.svg  ({len(svg)/1024:.1f} KB, "
      f"{len(KEYFRAMES)} keyframe blocks, {nf}-frame water loop)")
