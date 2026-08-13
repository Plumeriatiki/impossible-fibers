"""
Reference implementation of the fading-memory test of white paper s3.3.2,
used as ground truth for the JavaScript port in `fading-memory.html`.

The test: drive two identical fibers with two DIFFERENT conditioning histories,
then apply the SAME drive to both and watch the responses. If they converge to
the noise floor and stay there, the substrate has fading memory over that drive
regime. If they settle onto persistently different responses, it does not, and
the material is useless as a reservoir because the same input yields different
readouts depending on an unobservable past.

Base model is the visco-piezoelectric fiber of Appendix A (see fiber_sim.py).

The failure case is not invented. Section 3.2.3 names ferroelectric switching
as a way fading memory fails, and s2.2.1 notes ferroelectricity is native to
protein systems (crystalline beta- and gamma-glycine). So the counterexample
adds one bistable polarisation mode with a double-well potential:

    tau_P * dP/dt = P - P^3 + kappa * h

which has stable states at P = +/-1. Conditioning drops each fiber into a
different well; the well it lands in is never forgotten, so the two readouts
stay apart forever.
"""

import json
import numpy as np

from fiber_sim import P as PARAMS, Fiber


class LatchingFiber(Fiber):
    """Appendix A fiber plus one optional bistable (ferroelectric) mode."""

    def __init__(self, *a, latch=0.0, tau_P=0.8, kappa=0.55, **kw):
        super().__init__(*a, **kw)
        self.latch = latch          # readout weight of the bistable mode
        self.tau_P = tau_P
        self.kappa = kappa

    def rhs_full(self, u, x, Pv):
        h = self.strain(u, x)
        dx = (self.p * h - self.q * h * h - x - self.r * (self.eta @ x)) / self.tau
        dP = (Pv - Pv**3 + self.kappa * h) / self.tau_P
        return dx, dP

    def readout_full(self, u, x, Pv):
        h = self.strain(u, x)
        return -(h + self.G * h * h + self.eta @ x) - self.latch * Pv

    def run(self, u_of_t, t, x0=None, P0=0.0):
        n = len(t)
        dt = t[1] - t[0]
        x = np.zeros(len(self.tau)) if x0 is None else np.array(x0, float)
        Pv = float(P0)
        y = np.empty(n)
        xs = np.empty((n, len(self.tau)))
        Ps = np.empty(n)
        for i in range(n):
            ti = t[i]
            y[i] = self.readout_full(u_of_t(ti), x, Pv)
            xs[i] = x
            Ps[i] = Pv
            k1x, k1p = self.rhs_full(u_of_t(ti), x, Pv)
            k2x, k2p = self.rhs_full(u_of_t(ti + dt/2), x + dt/2*k1x, Pv + dt/2*k1p)
            k3x, k3p = self.rhs_full(u_of_t(ti + dt/2), x + dt/2*k2x, Pv + dt/2*k2p)
            k4x, k4p = self.rhs_full(u_of_t(ti + dt), x + dt*k3x, Pv + dt*k3p)
            x = x + dt/6*(k1x + 2*k2x + 2*k3x + k4x)
            Pv = Pv + dt/6*(k1p + 2*k2p + 2*k3p + k4p)
        return y, xs, Ps


def make(latch, tau_slow=1.0):
    p = dict(PARAMS)
    p["tau"] = np.array([tau_slow, tau_slow * 0.125])
    return LatchingFiber(**p, latch=latch)


def experiment(latch=0.0, tau_slow=1.0, u0=0.10, f=0.21, cond=0.16,
               T_cond=14.0, T_common=26.0, dt=2e-3, noise_floor=1e-6):
    """Two conditioning histories, then one shared drive."""
    def u_common(tt):
        return u0 * np.sin(2 * np.pi * f * tt)

    # phase 1: opposite-sign conditioning, plus a shared wobble so both
    # fibers are genuinely driven rather than merely offset
    def u_cond(sign):
        def f_(tt):
            return sign * cond * (1.0 + 0.35 * np.sin(2 * np.pi * 0.13 * tt))
        return f_

    tc = np.arange(0, T_cond, dt)
    ends = []
    for sign in (+1.0, -1.0):
        fib = make(latch, tau_slow)
        _, xs, Ps = fib.run(u_cond(sign), tc)
        ends.append((xs[-1], Ps[-1]))

    t = np.arange(0, T_common, dt)
    ys, Pt = [], []
    for x0, P0 in ends:
        fib = make(latch, tau_slow)
        y, _, Ps = fib.run(u_common, t, x0=x0, P0=P0)
        ys.append(y)
        Pt.append(Ps)

    d = np.abs(ys[0] - ys[1])
    d_floored = np.maximum(d, noise_floor)

    # conditional Lyapunov exponent: slope of log|dy| while above the floor
    m = (d > noise_floor * 20) & (t > 0.5)
    lam = np.polyfit(t[m], np.log(d[m]), 1)[0] if m.sum() > 50 else 0.0

    settled = float(np.median(d[t > T_common * 0.75]))
    return dict(
        t=t.tolist(), y1=ys[0].tolist(), y2=ys[1].tolist(),
        d=d_floored.tolist(), lam=float(lam), settled=settled,
        P_end=[float(Pt[0][-1]), float(Pt[1][-1])],
        has_fm=bool(settled < noise_floor * 10),
    )


if __name__ == "__main__":
    print("== fading-memory test, white paper s3.3.2 ==")
    print("two fibers, opposite conditioning histories, then an identical drive\n")

    for name, latch in (("plain viscoelastic fiber", 0.0),
                        ("with a bistable (ferroelectric) mode", 0.45)):
        r = experiment(latch=latch)
        print(f"{name}:")
        print(f"   final polarisation states P = {r['P_end'][0]:+.4f}, {r['P_end'][1]:+.4f}")
        print(f"   settled |y1-y2|            = {r['settled']:.3e}")
        print(f"   conditional Lyapunov slope = {r['lam']:+.4f} per t0")
        print(f"   fading memory              = {'YES' if r['has_fm'] else 'NO'}\n")

    print("== memory depth vs relaxation time ==")
    print("faster forgetting converges sooner but recalls less (Eq. 3.10)")
    for ts in (0.4, 1.0, 2.5):
        r = experiment(latch=0.0, tau_slow=ts)
        # time for the gap to fall below 1e-4
        t = np.array(r["t"]); d = np.array(r["d"])
        below = np.where(d < 1e-4)[0]
        t_conv = t[below[0]] if len(below) else float("nan")
        print(f"   tau_slow={ts:<4} lambda={r['lam']:+.4f}   "
              f"gap < 1e-4 after {t_conv:5.2f} t0")

    with open("fading_memory_ref.json", "w") as fh:
        json.dump({"plain": experiment(latch=0.0),
                   "latching": experiment(latch=0.45)}, fh)
    print("\nwrote fading_memory_ref.json")
