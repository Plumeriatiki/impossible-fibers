"""
Physical reservoir computing in a ripple tank -- a re-run of Fernando &
Sojakka, "Pattern recognition in a bucket" (cited in the white paper, s3.1),
built as the general-audience illustration of reservoir computing.

The pipeline is exactly Eq. (3.9) of the paper, u -> psi -> x -> yhat:

  B  two binary inputs drive two motors at the rim of a circular tank
  F  the water surface obeys a damped 2D wave equation (the reservoir)
  M  a camera measures the surface (Eq. 3.8) -- see note on nonlinearity
  W  one memoryless linear readout, ridge regression (Eq. 3.5), is trained

The control is the same linear readout trained on the raw two-bit input.
XOR is not linearly separable, so the control must sit at chance; the
question the simulation answers is whether the water makes it separable.
Train and test sets use independent noise draws, so the reported test
accuracy is not a memorisation artefact.

TWO FINDINGS WORTH KEEPING, both of which the paper predicts:

1. A linear reservoir cannot do this. With a linear wave equation, linear
   input coupling and a plain block-average camera, the whole chain
   B -> F -> M is linear, so superposition forces
   I(1,1) = I(0,1) + I(1,0) and no linear readout can separate XOR. The
   first version of this script scored 48% on test for exactly that
   reason. Section 3.2.2: "For the reservoir to be reasonably expressive,
   some nonlinearity must be supplied by the chain B -> F -> M."

2. The nonlinearity here lives in the measurement, not the medium -- which
   is also how the original bucket worked (a camera looking at light
   refracted through the surface). The camera is a square-law detector with
   a finite exposure and a saturating sensor:

       I = tanh( <u^2>_exposure / I_sat )

   This is the paper's own example of nonlinearity supplied by M: "a
   transducer operating outside its linear range". The square-law step is
   the same rectification that gives the fiber of Fig. 2.2 its energy
   detection, so the two graphics share one mechanism.

Time integration is the damped leapfrog

    u_next = [ 2u - (1 - g) u_prev + c^2 lap(u) + f ] / (1 + g),   g = gamma*dt

which is unconditionally dissipative. The naive "subtract DAMP*(u - u_prev)"
form pumps energy into the grid-Nyquist mode and diverges.
"""

import itertools
import json
import numpy as np

# ---------------------------------------------------------------------------
# tank geometry and physics
# ---------------------------------------------------------------------------
N = 120                  # simulation grid
C = 0.45                 # wave speed, grid units/step (CFL needs < 1/sqrt(2))
GAMMA = 0.0015           # gamma*dt -- dissipation, hence fading memory
DRIVE_PERIOD = 18        # integer, so the exported frames form a seamless loop
DRIVE_FREQ = 1.0 / DRIVE_PERIOD
DRIVE_AMP = 0.55
STEPS = 1200
EXP_START, EXP_END = 1060, 1100      # camera exposure window (~2.2 periods)
LOOP_START, LOOP_FRAMES = 1060, 36   # 2 drive periods -> seamless loop
CAM = 22                 # camera grid
MOTOR_ANGLES = (240.0, 300.0)

yy, xx = np.mgrid[0:N, 0:N]
cx = cy = (N - 1) / 2.0
rad = (N - 1) / 2.0 - 2.0
R = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
INSIDE = (R <= rad).astype(float)


def rim_point(angle_deg, inset=6.0):
    a = np.deg2rad(angle_deg)
    return (cx + (rad - inset) * np.cos(a), cy + (rad - inset) * np.sin(a))


MOTORS = [rim_point(a) for a in MOTOR_ANGLES]
MASKS = [np.exp(-0.5 * (((xx - p[0]) ** 2 + (yy - p[1]) ** 2) / 3.2**2)) * INSIDE
         for p in MOTORS]

PATTERNS = [(0, 0), (0, 1), (1, 0), (1, 1)]
LABELS = {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 0}       # XOR
_K = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2)
_K /= _K.sum()


def smooth_noise(rng):
    """Spatially correlated surface disturbance. Uncorrelated grid noise would
    be a pure grid-Nyquist forcing, which is not a physical disturbance."""
    n = rng.standard_normal((N, N))
    for ax in (0, 1):
        n = np.apply_along_axis(lambda m: np.convolve(m, _K, mode="same"), ax, n)
    return n * INSIDE


def coarsen(field):
    """Spatial part of the measurement map M: block-average onto CAM x CAM."""
    b = N // CAM
    t = field[: b * CAM, : b * CAM]
    return t.reshape(CAM, b, CAM, b).mean(axis=(1, 3))


CAM_INSIDE = coarsen(INSIDE) > 0.5


def simulate(bits, gain=(1.0, 1.0), noise=0.0, rng=None, collect_loop=False):
    """Returns (exposure-averaged u^2 on the camera grid, loop frames, diagnostics)."""
    if rng is None:
        rng = np.random.default_rng(0)
    u_prev = np.zeros((N, N))
    u_cur = np.zeros((N, N))
    acc = np.zeros((N, N))
    n_acc = 0
    frames = []
    rms_trace = []

    for step in range(STEPS):
        f = np.zeros((N, N))
        drive = DRIVE_AMP * np.sin(2 * np.pi * DRIVE_FREQ * step)
        for b, g, mask in zip(bits, gain, MASKS):
            if b:
                f += g * drive * mask
        if noise:
            f += noise * smooth_noise(rng)

        lap = (np.roll(u_cur, 1, 0) + np.roll(u_cur, -1, 0)
               + np.roll(u_cur, 1, 1) + np.roll(u_cur, -1, 1) - 4 * u_cur)
        u_next = (2 * u_cur - (1 - GAMMA) * u_prev + C**2 * lap + f) / (1 + GAMMA)
        u_next *= INSIDE                       # rigid tank wall
        u_prev, u_cur = u_cur, u_next

        if EXP_START <= step < EXP_END:
            acc += u_cur * u_cur
            n_acc += 1
        if collect_loop and LOOP_START <= step < LOOP_START + LOOP_FRAMES:
            frames.append(coarsen(u_cur))
        if step % 100 == 0:
            rms_trace.append(float(u_cur[INSIDE > 0].std()))

    assert n_acc > 0 and np.isfinite(acc).all(), "field diverged"
    return coarsen(acc / n_acc), frames, rms_trace


def saturate(I, isat):
    """Saturating sensor -- the nonlinear half of the measurement map."""
    return np.tanh(I / isat)


def features(I_cam, isat):
    return saturate(I_cam, isat)[CAM_INSIDE]


def build_dataset(n_per_class, seed, isat):
    rng = np.random.default_rng(seed)
    X, Xraw, Y, tags = [], [], [], []
    for bits in PATTERNS:
        for _ in range(n_per_class):
            gain = 1.0 + 0.03 * rng.standard_normal(2)      # motor jitter
            I, _, _ = simulate(bits, gain=gain, noise=8e-4, rng=rng)
            X.append(features(I, isat))
            Xraw.append(np.array(bits, float))
            Y.append(LABELS[bits])
            tags.append(f"{bits[0]}{bits[1]}")
    return np.array(X), np.array(Xraw), np.array(Y), tags


def ridge_fit(X, y, lam=1e-2):
    """The one trained stage: memoryless linear readout, Eq. (3.5).
    Scaled globally, not per-feature: every observable is the same physical
    quantity in the same units, so per-feature whitening would just amplify
    the quietest cells."""
    mu, s = X.mean(0), X.std()
    Xn = np.c_[(X - mu) / s, np.ones(len(X))]
    A = Xn.T @ Xn + lam * len(X) * np.eye(Xn.shape[1])
    return dict(w=np.linalg.solve(A, Xn.T @ (2.0 * y - 1.0)), mu=mu, s=s)


def ridge_predict(m, X):
    return np.c_[(X - m["mu"]) / m["s"], np.ones(len(X))] @ m["w"]


def accuracy(m, X, y):
    return float(np.mean((ridge_predict(m, X) > 0).astype(int) == y))


if __name__ == "__main__":
    np.seterr(all="ignore")   # BLAS emits spurious denormal warnings on matmul

    print("== tank ==")
    print(f"  grid {N}x{N}   camera {CAM}x{CAM}   in-tank cells n = {int(CAM_INSIDE.sum())}")
    print(f"  CFL = {C:.3f} (< {1/np.sqrt(2):.3f})   gamma*dt = {GAMMA}   "
          f"drive period = {DRIVE_PERIOD} steps")

    raw = {}
    for b in PATTERNS:
        I, _, rms = simulate(b)
        raw[b] = I
    print(f"  rms(u) per 100 steps for (1,1): {np.round(rms, 3)}  <- steady state reached")

    isat = float(np.median(raw[(1, 1)][CAM_INSIDE]) * 1.5)
    print(f"  I_sat = {isat:.4f} (1.5x median intensity of the (1,1) case)")

    print("\n== is the chain nonlinear? ==")
    lhs = saturate(raw[(1, 1)], isat)[CAM_INSIDE]
    rhs = (saturate(raw[(0, 1)], isat) + saturate(raw[(1, 0)], isat))[CAM_INSIDE]
    print(f"  ||I(11) - [I(01)+I(10)]|| / ||I(11)|| = "
          f"{np.linalg.norm(lhs - rhs)/np.linalg.norm(lhs):.3f}   "
          f"(0 would mean a linear chain, hence XOR impossible)")

    print("\n== training ==")
    Xtr, Rtr, Ytr, _ = build_dataset(10, seed=11, isat=isat)
    Xte, Rte, Yte, tags_te = build_dataset(10, seed=99, isat=isat)
    print(f"  train {Xtr.shape}   test {Xte.shape} (independent noise draws)")

    print("  regularisation sweep (test accuracy must not depend on tuning):")
    for lam in (1e-4, 1e-3, 1e-2, 1e-1, 3e-1):
        m = ridge_fit(Xtr, Ytr, lam)
        print(f"    lam={lam:<7} train {accuracy(m, Xtr, Ytr):.0%}  "
              f"test {accuracy(m, Xte, Yte):.0%}")

    m_res, m_raw = ridge_fit(Xtr, Ytr), ridge_fit(Rtr, Ytr)
    acc = dict(raw_train=accuracy(m_raw, Rtr, Ytr), raw_test=accuracy(m_raw, Rte, Yte),
               res_train=accuracy(m_res, Xtr, Ytr), res_test=accuracy(m_res, Xte, Yte))
    print(f"\n  raw 2-bit input -> train {acc['raw_train']:.0%}  test {acc['raw_test']:.0%}")
    print(f"  water surface   -> train {acc['res_train']:.0%}  test {acc['res_test']:.0%}")

    Xc = Xtr - Xtr.mean(0)
    ev = np.clip(np.linalg.eigvalsh(Xc.T @ Xc / len(Xtr))[::-1], 0, None)
    rank = int(np.sum(ev > ev[0] * 1e-6))
    print(f"  rank(Sigma) = {rank} of {Xtr.shape[1]} cells "
          f"(s3.3.1: capacity is bounded by this, not the cell count)")

    print("\n== frames ==")
    _, frames, _ = simulate((1, 1), collect_loop=True)
    frames = np.array(frames)
    scale = float(np.percentile(np.abs(frames), 99.0))
    print(f"  {len(frames)} frames = {LOOP_FRAMES/DRIVE_PERIOD:.0f} drive periods "
          f"(seamless loop), normalised by p99 = {scale:.3f}")

    z1 = ridge_predict(m_res, Xte)
    Xn = (Xte - m_res["mu"]) / m_res["s"]
    wn = m_res["w"][:-1] / np.linalg.norm(m_res["w"][:-1])
    resid = Xn - np.outer(Xn @ wn, wn)
    resid -= resid.mean(0)
    _, _, vt = np.linalg.svd(resid, full_matrices=False)
    z2 = resid @ vt[0]

    isat_imgs = {f"{b[0]}{b[1]}": np.round(saturate(raw[b], isat), 4).tolist()
                 for b in PATTERNS}

    out = dict(
        meta=dict(N=N, CAM=CAM, loop_frames=int(len(frames)),
                  drive_period=DRIVE_PERIOD, exp_start=EXP_START, exp_end=EXP_END,
                  steps=STEPS, gamma=GAMMA, c=C, isat=isat, scale=scale,
                  n_observables=int(CAM_INSIDE.sum()), rank_sigma=rank,
                  motor_angles=list(MOTOR_ANGLES),
                  motors_cam=[[p[0] * CAM / N, p[1] * CAM / N] for p in MOTORS],
                  nonlinearity_ratio=float(np.linalg.norm(lhs - rhs) / np.linalg.norm(lhs))),
        acc=acc,
        inside=CAM_INSIDE.tolist(),
        frames=np.round(frames / scale, 3).tolist(),
        intensity=isat_imgs,
        labels={f"{b[0]}{b[1]}": LABELS[b] for b in PATTERNS},
        scatter=dict(z1=np.round(z1, 4).tolist(), z2=np.round(z2, 4).tolist(),
                     y=Yte.tolist(), tags=tags_te),
        eigenvalues=np.round(ev / ev[0], 6).tolist(),
    )
    with open("tank_data.json", "w") as fh:
        json.dump(out, fh)
    print("  wrote tank_data.json")
