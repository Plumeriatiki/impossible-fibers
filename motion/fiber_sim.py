"""
Simulation of the one-dimensional visco-piezoelectric fiber model from
Impossible Fibers white paper draft, Appendix A / Eqs (A.12)-(A.14),
reproducing the three behaviours of Fig. 2.2.

Parameters taken verbatim from the Fig. 2.2 caption:
    k0^2 = 0.2, g = 0.2, ge = 0.3,
    Dc = (0.30, 0.20), De = (0.25, -0.10),
    tau = (1, 0.125), ell = (0.30, 0.10)

Model (dimensionless, N internal relaxation modes x = (xi_1..xi_N)):
    s      = u + w.x
    Aeff   = A + f.x
    h      = 2s / (Aeff + sqrt(Aeff^2 + 4 B s))        (A.12)  strain
    T xdot = p h - q h^2 - x - r (eta.x)               (A.14a)
    y      = -( h + G h^2 + eta.x )                    (A.14b)  open-circuit voltage
"""

import json
import numpy as np

# ----------------------------------------------------------------------------
# paper parameters (Fig. 2.2)
# ----------------------------------------------------------------------------
P = dict(
    k0sq=0.2,
    g=0.2,
    ge=0.3,
    Dc=np.array([0.30, 0.20]),
    De=np.array([0.25, -0.10]),
    tau=np.array([1.0, 0.125]),
    ell=np.array([0.30, 0.10]),
)


class Fiber:
    """Reduced open-circuit model, Table A.1 coefficients."""

    def __init__(self, k0sq, g, ge, Dc, De, tau, ell, nonlinear=True):
        if not nonlinear:
            # "identical memory and couplings, nonlinear terms off" (Fig 2.2 caption)
            g, ge, ell = 0.0, 0.0, np.zeros_like(ell)

        self.Dc, self.De, self.tau, self.ell = Dc, De, tau, ell
        self.k0sq, self.g, self.ge = k0sq, g, ge

        # Table A.1
        self.A = 1.0 + k0sq                      # open-circuit stiffened modulus
        self.B = g + 1.5 * ge * k0sq             # instantaneous quadratic stiffness
        self.G = ge / 2.0                        # square-law charge coefficient
        self.w = Dc - k0sq * De                  # open-circuit relaxation strength
        self.eta = De                            # charge per unit mode excursion
        self.f = 2 * Dc * ell + ge * k0sq * De   # strain-state cross stiffness
        self.r = k0sq * De / Dc                  # field-mediated feedback weight
        self.p = 1.0 - self.r                    # linear drive of each mode
        self.q = ell + self.G * self.r           # quadratic drive of each mode

        self.check_stability()

    def check_stability(self):
        """Eq. (A.9)."""
        c1 = self.k0sq < 1
        c2 = 1 - self.Dc.sum() > 0
        c3 = 1 - self.k0sq * np.sum(self.De**2 / self.Dc) > 0
        assert c1 and c2 and c3, f"unstable rest state: {c1} {c2} {c3}"

    def strain(self, u, x):
        """Eq. (A.12): mechanical balance fixes strain at each instant."""
        s = u + self.w @ x
        Aeff = self.A + self.f @ x
        disc = Aeff**2 + 4.0 * self.B * s
        if disc < 0:
            raise ValueError("drive pushed past weakly-nonlinear regime (A.12 radicand < 0)")
        return 2.0 * s / (Aeff + np.sqrt(disc))

    def rhs(self, u, x):
        h = self.strain(u, x)
        return (self.p * h - self.q * h * h - x - self.r * (self.eta @ x)) / self.tau

    def readout(self, u, x):
        h = self.strain(u, x)
        return -(h + self.G * h * h + self.eta @ x)

    def run(self, u_of_t, t):
        """RK4 integration; returns (y, x_traj)."""
        n = len(t)
        dt = t[1] - t[0]
        x = np.zeros(len(self.tau))
        y = np.empty(n)
        for i in range(n):
            ti = t[i]
            y[i] = self.readout(u_of_t(ti), x)
            k1 = self.rhs(u_of_t(ti), x)
            k2 = self.rhs(u_of_t(ti + dt / 2), x + dt / 2 * k1)
            k3 = self.rhs(u_of_t(ti + dt / 2), x + dt / 2 * k2)
            k4 = self.rhs(u_of_t(ti + dt), x + dt * k3)
            x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        return y


def make_pair():
    return Fiber(**P, nonlinear=True), Fiber(**P, nonlinear=False)


def lowpass(sig, sigma_samples):
    """Zero-phase Gaussian FIR low-pass, edge-padded.

    Gaussian response exp(-2 pi^2 sigma^2 f^2): with sigma = 2 t0 this passes
    the modulation at fm = 0.04 (gain 0.88) and annihilates the carrier at
    fc = 0.5 (gain ~3e-9), so any surviving slow component is genuinely
    rectified rather than carrier leakage.
    """
    s = float(sigma_samples)
    half = int(np.ceil(4 * s))
    k = np.exp(-0.5 * (np.arange(-half, half + 1) / s) ** 2)
    k /= k.sum()
    pad = np.r_[np.full(half, sig[0]), sig, np.full(half, sig[-1])]
    return np.convolve(pad, k, mode="same")[half:-half]


# ----------------------------------------------------------------------------
# (a) frequency mixing: two-tone drive
# ----------------------------------------------------------------------------
def experiment_mixing(u0=0.06, f1=0.13, f2=0.21, T=100.0, dt=1e-3, washout=20.0):
    t = np.arange(0, T + washout, dt)

    def u(tt):
        return u0 * (np.cos(2 * np.pi * f1 * tt) + np.cos(2 * np.pi * f2 * tt))

    nl, lin = make_pair()
    out = {}
    keep = t >= washout
    n_keep = int(T / dt)
    for name, fib in (("nonlinear", nl), ("linear", lin)):
        y = fib.run(u, t)[keep][:n_keep]
        Y = np.fft.rfft(y * 1.0) / n_keep
        freqs = np.fft.rfftfreq(n_keep, dt)
        mag = np.abs(Y)
        mag[1:] *= 2.0  # single-sided
        sel = freqs <= 1.0
        out[name] = dict(freqs=freqs[sel].tolist(), mag=mag[sel].tolist())

    # time traces for display (a few periods)
    tt = np.arange(0, 40, 0.02)
    disp_t = np.arange(0, 60 + 0.02, 0.02)

    def run_disp(fib):
        return fib.run(u, disp_t)

    y_nl = run_disp(nl)
    y_li = run_disp(lin)
    m = disp_t >= 20
    out["trace"] = dict(
        t=(disp_t[m] - 20).tolist(),
        u=u(disp_t[m]).tolist(),
        y_nonlinear=y_nl[m].tolist(),
        y_linear=y_li[m].tolist(),
    )
    out["params"] = dict(u0=u0, f1=f1, f2=f2)

    # label the interesting spectral lines
    lines = {
        "f2-f1": f2 - f1,
        "f1": f1,
        "f2": f2,
        "2f1": 2 * f1,
        "f1+f2": f1 + f2,
        "2f2": 2 * f2,
    }
    out["lines"] = lines
    return out


# ----------------------------------------------------------------------------
# (b) energy detection: DC offset vs drive amplitude
# ----------------------------------------------------------------------------
def experiment_energy(f=0.2, amps=None, T=60.0, dt=1e-3, washout=20.0):
    if amps is None:
        amps = np.linspace(0.02, 0.30, 15)
    nl, lin = make_pair()
    res = {"amps": amps.tolist(), "nonlinear": [], "linear": []}
    t = np.arange(0, T + washout, dt)
    keep = t >= washout
    for u0 in amps:
        def u(tt, u0=u0):
            return u0 * np.cos(2 * np.pi * f * tt)
        for name, fib in (("nonlinear", nl), ("linear", lin)):
            y = fib.run(u, t)[keep]
            res[name].append(float(y.mean()))
    res["params"] = dict(f=f)
    return res


# ----------------------------------------------------------------------------
# (c) amplitude demodulation
# ----------------------------------------------------------------------------
def experiment_am(u0=0.14, fc=0.5, fm=0.04, depth=0.8, T=75.0, dt=2e-3,
                  washout=20.0, tail=20.0, lp_sigma=1.5):
    """Fast carrier, slowly modulated. A `tail` longer than the filter's
    support is simulated past the displayed window and then discarded, so the
    low-pass never reads its own edge padding inside the analysed record."""
    t = np.arange(0, washout + T + tail, dt)

    def env(tt):
        return 1.0 + depth * np.cos(2 * np.pi * fm * tt)

    def u(tt):
        return u0 * env(tt) * np.cos(2 * np.pi * fc * tt)

    nl, lin = make_pair()
    keep = (t >= washout) & (t < washout + T)
    res = {"params": dict(u0=u0, fc=fc, fm=fm, depth=depth, lp_sigma=lp_sigma)}
    for name, fib in (("nonlinear", nl), ("linear", lin)):
        y = fib.run(u, t)
        lp = lowpass(y, lp_sigma / dt)[keep]
        res[name] = (lp - lp.mean()).tolist()
        res[name + "_raw"] = y[keep].tolist()
    tk = t[keep] - t[keep][0]
    ref = env(t[keep]) ** 2
    res["t"] = tk.tolist()
    res["u"] = u(t[keep]).tolist()
    res["reference_sq_envelope"] = (ref - ref.mean()).tolist()
    return res


def dec(a, n=700):
    """Decimate to about n points for export."""
    a = np.asarray(a)
    k = max(1, len(a) // n)
    return np.round(a[::k], 6).tolist()


# ----------------------------------------------------------------------------
# (b') energy detection, shown in the time domain: amplitude staircase
# ----------------------------------------------------------------------------
def experiment_energy_trace(levels=(0.07, 0.15, 0.26), hold=45.0, f=0.2,
                            dt=1e-3, washout=15.0, tail=12.0, lp_sigma=2.5):
    """A single tone whose amplitude steps up. The low-passed output is a
    passive amplitude meter: it should climb in steps for the nonlinear fiber
    and stay pinned at zero for the linear one."""
    total = washout + hold * len(levels) + tail
    t = np.arange(0, total, dt)

    def amp(tt):
        idx = np.clip(((tt - washout) // hold).astype(int), 0, len(levels) - 1)
        return np.asarray(levels)[idx] * (tt >= washout)

    def u(tt):
        tt = np.asarray(tt, dtype=float)
        return amp(tt) * np.cos(2 * np.pi * f * tt)

    nl, lin = make_pair()
    keep = (t >= washout) & (t < washout + hold * len(levels))
    res = {"params": dict(levels=list(levels), hold=hold, f=f, lp_sigma=lp_sigma)}
    for name, fib in (("nonlinear", nl), ("linear", lin)):
        y = fib.run(u, t)
        res[name] = dec(y[keep])
        res[name + "_dc"] = dec(lowpass(y, lp_sigma / dt)[keep])
    res["t"] = dec(t[keep] - t[keep][0])
    res["u"] = dec(u(t[keep]))
    res["amp"] = dec(amp(t[keep]))
    return res


if __name__ == "__main__":
    print("== stability + coefficient check ==")
    nl, lin = make_pair()
    for k in ("A", "B", "G"):
        print(f"  {k} = {getattr(nl, k):.4f}")
    for k in ("w", "eta", "f", "r", "p", "q"):
        print(f"  {k} = {np.round(getattr(nl, k), 4)}")

    print("\n== (a) frequency mixing ==")
    mix = experiment_mixing()
    fr = np.array(mix["nonlinear"]["freqs"])
    for lbl, fv in mix["lines"].items():
        i = int(np.argmin(np.abs(fr - fv)))
        a = mix["nonlinear"]["mag"][i]
        b = mix["linear"]["mag"][i]
        print(f"  {lbl:>6} f={fv:5.2f}   nonlinear={a:.3e}   linear={b:.3e}   ratio={a/max(b,1e-30):.1e}")

    print("\n  top 12 nonlinear spectral bins:")
    mg = np.array(mix["nonlinear"]["mag"])
    mgl = np.array(mix["linear"]["mag"])
    for i in np.argsort(mg)[::-1][:12]:
        print(f"    f={fr[i]:5.3f}  nl={mg[i]:.3e}  lin={mgl[i]:.3e}")
    print(f"  nonlinear floor (median) = {np.median(mg):.2e}")
    print(f"  linear    floor (median) = {np.median(mgl):.2e}")
    print(f"  linear    max off-tone   = "
          f"{np.max(np.delete(mgl, [int(round(mix['params']['f1']/0.01)), int(round(mix['params']['f2']/0.01))])):.2e}")

    order_gap = np.log10(mix["nonlinear"]["mag"][8] / mix["linear"]["mag"][8])
    print(f"  orders of magnitude between models at f2-f1: {order_gap:.2f}")
    mix["order_gap"] = float(order_gap)

    print("\n== (b) energy detection ==")
    en = experiment_energy()
    for u0, a, b in list(zip(en["amps"], en["nonlinear"], en["linear"]))[::4]:
        print(f"  u0={u0:.3f}  <y>_nl={a:+.5f}   <y>_lin={b:+.2e}")
    A = np.array(en["amps"]); Y = np.array(en["nonlinear"])
    pw = np.polyfit(np.log(A), np.log(np.abs(Y)), 1)[0]
    print(f"  power-law exponent of <y> vs u0: {pw:.3f}  (expect ~2)")

    print("\n== (c) AM demodulation ==")
    am = experiment_am()
    ref = np.array(am["reference_sq_envelope"])
    for name in ("nonlinear", "linear"):
        s = np.array(am[name])
        c = np.corrcoef(s, ref)[0, 1]
        print(f"  {name:>9}: corr with squared envelope = {c:+.4f}   rms = {s.std():.3e}")

    print("\n== (b') amplitude staircase ==")
    ent = experiment_energy_trace()
    lv = ent["params"]["levels"]
    for name in ("nonlinear", "linear"):
        d = np.array(ent[name + "_dc"])
        tt = np.array(ent["t"])
        plateaus = [float(np.median(d[(tt > (i + 0.55) * 45) & (tt < (i + 0.95) * 45)]))
                    for i in range(len(lv))]
        print(f"  {name:>9} DC plateaus = {np.round(plateaus, 5)}")

    # trim the exported traces
    for k in ("t", "u", "y_nonlinear", "y_linear"):
        mix["trace"][k] = dec(mix["trace"][k])
    for k in ("t", "u", "nonlinear", "linear", "reference_sq_envelope",
              "nonlinear_raw", "linear_raw"):
        am[k] = dec(am[k])

    data = dict(mixing=mix, energy=en, energy_trace=ent, am=am,
                params={k: (v.tolist() if isinstance(v, np.ndarray) else v)
                        for k, v in P.items()})
    with open("fiber_data.json", "w") as fh:
        json.dump(data, fh)
    print("\nwrote fiber_data.json")
