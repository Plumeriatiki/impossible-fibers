# Motion graphics for the Computational Fibers white paper

Two animated, self-contained SVGs for general audiences. Both are
**simulation-driven**: every curve, spectrum, water frame and accuracy figure
is computed output, not illustration. Nothing is hand-drawn to look
convincing.

| File | What it explains | Source in the paper |
|---|---|---|
| `fiber-three-tricks.svg` | Three computations a nonlinear fiber performs that a clean sensor cannot | §2.1.1, Fig. 2.2, Appendix A |
| `bucket-reservoir.svg` | What reservoir computing is, via a ripple tank solving XOR | §3.1, §3.2.2, Eq. 3.9 |

## Regenerating

Requires Python with `numpy` only.

```bash
python fiber_sim.py && python make_fiber_svg.py
```

```bash
python tank_sim.py && python make_tank_svg.py
```

The `*_sim.py` scripts run the physics and write `*_data.json`; the
`make_*_svg.py` scripts bake that JSON into the SVG. Both simulations print a
diagnostic summary you can check against the paper. `fiber_sim.py` takes about
75 s, `tank_sim.py` about 60 s.

## Previewing

`preview.html` inlines an SVG and lets you scrub the timeline (it pauses all
CSS animations and sets `currentTime`, so you can inspect any frame):

```bash
python -m http.server 8765
```

Then open `http://127.0.0.1:8765/preview.html?f=bucket-reservoir.svg`.

## Embedding

Both files are standalone: no external scripts, fonts, or images.

### Do not use `<img>`

**Verified in Chrome:** an SVG loaded through `<img>` renders, but its CSS
animation clock never advances — every element freezes at t = 0, where the
acts are still at `opacity: 0`. The result is a near-blank frame showing only
the title, the device sketch and the footer. (In `bucket-reservoir.svg` it is
worse: the water is SMIL, which *does* run in `<img>`, so you get a rippling
tank with no captions at all.)

Use `<object>` — confirmed animating correctly:

```html
<object type="image/svg+xml" data="motion/fiber-three-tricks.svg"
        style="width:100%;height:auto" aria-label="Three computations performed by a single nonlinear protein fiber"></object>
```

Or paste the SVG markup inline, which is better still: the page's
already-loaded DM Sans / DM Serif Display then render the type, instead of
falling back to Helvetica/Georgia.

### Sizing — read this before putting them on a page

These are 1120 px wide with 10.5–14.5 px type, and **the site's content column
caps at 620–740 px**. At 740 px everything scales by 0.66, so the smallest
labels land at ~7 px and captions at ~9.6 px — legible only if the reader
leans in. At mobile width (~340 px) the small type is around 3 px, i.e. gone.

So do one of:

- give them a full-bleed container that escapes the text column, and/or
- link out to them at full size rather than inlining, and/or
- build portrait reflows for narrow screens (not yet done).

They are currently **desktop, wide-container assets**. Treat that as a real
constraint, not a detail.

### Reduced motion

Both honour `prefers-reduced-motion: reduce` by disabling animation entirely,
at which point the un-animated base state renders **Act 1, complete** — traces
drawn, spectrum built, labels in place. This is deliberate and verified: the
first version froze at the *final* keyframe instead and produced a blank
graphic, which is why the rule is `animation: none` rather than
`animation-duration: 0s`.

The same trick does not rescue `<img>`, because there the animation is applied
and merely frozen at t = 0, so the keyframe wins over the base state. Making
`<img>` work would mean retiming the loop so that t = 0 is a hold frame with
Act 1 already built, with the build moved to the tail of the loop. Not done.

### Size

203 KB and 392 KB uncompressed. They gzip well (highly repetitive numerics) —
with compression on they go over the wire at roughly a quarter of that.

## Two things worth knowing about the content

**The fiber graphic** uses the parameters printed in the Fig. 2.2 caption
verbatim, but at a lower drive amplitude (`u₀ = 0.06` rather than 0.15). At the
higher amplitude, high-order intermodulation products fill every spectral bin
and the plot reads as hash rather than as discrete manufactured tones. Lower
drive puts the model in the weakly nonlinear regime it was derived for and
separates the orders cleanly.

**The bucket graphic** found something. The first version had a linear wave
equation, linear input coupling and a plain block-averaging camera — so the
whole chain `B → F → M` was linear, superposition forced
`I(1,1) = I(0,1) + I(1,0)`, and no linear readout could ever separate XOR. It
scored 48% on held-out data, i.e. chance. This is exactly the requirement in
§3.2.2 that *some* nonlinearity must be supplied by the chain. The fix is the
measurement, not the medium: the camera is now a square-law detector with a
finite exposure and a saturating sensor,

```
I = tanh( ⟨u²⟩_exposure / I_sat )
```

which is both how the original bucket actually worked (a camera reading light
refracted through the surface) and the paper's own example of nonlinearity
supplied by `M`. Test accuracy went to 100%, stable across four orders of
magnitude of ridge regularisation. The square-law step is the same
rectification that gives the fiber its energy detection in Act 2 of the other
graphic, so the two pieces share one mechanism — worth saying out loud if these
are ever narrated together.

The graphic also reports `rank(Σ) ≈ 30` against 388 camera cells, which is the
§3.3.1 point that capacity is bounded by the number of *independent*
observables rather than the number of wires.

## Caveat to state if these are presented as science

The bucket runs the **spatial** version of the task — two switches presented
simultaneously — because that is the form the cited 2003 experiment took and it
is the most legible. The paper's actual interest is **temporal** processing, and
the honest sequel is a delay or parity task driven by a bit *sequence* through a
single motor, which would demonstrate fading memory rather than assume it. That
is a different graphic (concept ⑤ in the earlier list).
