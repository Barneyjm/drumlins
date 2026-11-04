"""Linear stability of the Fowler & Chapwanya (2014, Proc. R. Soc. A 470:20140185) ice-water-till model.

Two independent evaluations of the growth rate Sigma(k1, k2):
  (a) direct: the 4x4 linear system (their eq. 3.7) for (h, Psi, s, N); det = 0 is a polynomial
      in Sigma, obtained by exact polynomial algebra on its Sigma-linear entries;
  (b) paper:  the quadratic f2 S^2 + f1 S + f0 = 0 with coefficients from their eqs. 3.10-3.11.
Conventions: Fourier kernel e^{i k.x}; k1 downstream, k2 transverse; lengths scaled by l_D.
"""
from __future__ import annotations
import numpy as np
from numpy.polynomial import polynomial as P_

SLOW = True   # slow (bedform) root; the fast root is film relaxation
FIG4 = dict(alpha=0.1, beta=1e-3, gamma=0.3e-2, delta=0.5e-3, eps=2.7e-2, kappa=2e-3, mu=0.6,
            sigma=0.64, b=0.3, C=1.0, B=1.0, ubar=1.0, R=1.0, r=917 / 1000)


def kernels(k1, k2, sigma):
    k = np.hypot(k1, k2)
    j = k / sigma                       # ice depth / bedform length * k  (deep ice: sigma->0, j->inf)
    jj = np.minimum(j, 300.0)           # sinh overflow guard (U->1, V->0 there)
    Sh, Ch = np.sinh(jj), np.cosh(jj)
    U = np.where(j > 300, 1.0, (jj + Sh * Ch) / Sh ** 2)
    V = np.where(j > 300, 0.0, 1j * k1 * jj ** 2 / (k * Sh ** 2))
    return k, U, V


def coeffs(k1, k2, Pi, p):
    a, be, ga, de, ep, ka, mu, sg, bb, C, B, ub, R, r = (p[x] for x in
        ("alpha", "beta", "gamma", "delta", "eps", "kappa", "mu", "sigma", "b", "C", "B", "ubar", "R", "r"))
    k, U, V = kernels(k1, k2, sg)
    A = 0.5 * (1 / mu - 1 / Pi)
    fN = bb * Pi
    E = ga * ((C / 3 - B) * k2 ** 2 - (2 / 3) * C * k1 ** 2)
    T = ka * (B * k2 ** 2 + C * k1 ** 2)
    M = 1 - 2j * k1 * k * ub * U
    S = 1j * k1 * R - be * A ** 3 * k ** 2          # R = ubar*A'
    return dict(k=k, U=U, V=V, A=A, fN=fN, E=E, T=T, M=M, S=S, a=a, de=de, ep=ep, sg=sg, r=r)


def sigma_direct(k1, k2, Pi, p=FIG4):
    """Unstable root from det of the 4x4 system; rows linear in Sigma -> exact polynomial det."""
    c = coeffs(k1, k2, Pi, p)
    k, U, M, S, E, T, fN, V = c["k"], c["U"], c["M"], c["S"], c["E"], c["T"], c["fN"], c["V"]
    a, de, ep, sg, r = c["a"], c["de"], c["ep"], c["sg"], c["r"]
    # matrix entries as (const, coeff of Sigma); unknown order (h, Psi, s, N)
    Z = (0, 0)
    rows = [
        [(3 * sg * 1j * k1, 0), (-k ** 2, 0), Z, Z],
        [Z, (1, 0), (-M, -2 * k * U * a), (1 + fN * V, 0)],
        [(1, ep * r), Z, Z, (Pi, 0)],
        [(-de * T, -de), (-E, 0), (T, 1), (-S, 0)],
    ]
    def det(mat):
        n = len(mat)
        if n == 1:
            return np.array(mat[0][0], dtype=complex)
        tot = np.zeros(1, complex)
        for jcol in range(n):
            e = np.array(mat[0][jcol], dtype=complex)
            if not np.any(e):
                continue
            minor = [row[:jcol] + row[jcol + 1:] for row in mat[1:]]
            term = P_.polymul(e, det(minor)) * (-1) ** jcol
            tot = P_.polyadd(tot, term)
        return tot
    poly = np.trim_zeros(det(rows), "b")
    roots = np.roots(poly[::-1])
    if SLOW:
        ref = sigma_slow_eps0(k1, k2, Pi, p)
        return roots[np.argmin(np.abs(roots - ref))]
    return roots[np.argmax(roots.real)]


def sigma_paper(k1, k2, Pi, p=FIG4):
    c = coeffs(k1, k2, Pi, p)
    k, U, M, S, E, T, fN, V = c["k"], c["U"], c["M"], c["S"], c["E"], c["T"], c["fN"], c["V"]
    a, de, ep, sg, r = c["a"], c["de"], c["ep"], c["sg"], c["r"]
    W = 1 - 2 * a * k * U * E
    PP = 1 + fN * V - 2 * a * k * U * S
    f2 = (ep * r * PP + 2 * de * a * Pi * k * U) * k ** 2
    f1 = -3 * sg * 1j * k1 * Pi * W + k ** 2 * (PP - ep * r * (S * M - (1 + fN * V) * T) + de * Pi * (M + 2 * a * k * U * T))
    f0 = M * (3 * sg * 1j * k1 * Pi * E - k ** 2 * S) + T * ((1 + fN * V + de * Pi * M) * k ** 2 - 3 * sg * 1j * k1 * Pi)
    d = np.sqrt(f1 ** 2 - 4 * f0 * f2)
    r1, r2 = (d - f1) / (2 * f2), (-d - f1) / (2 * f2)
    if SLOW:
        ref = sigma_slow_eps0(k1, k2, Pi, p)
        return r1 if abs(r1 - ref) <= abs(r2 - ref) else r2
    return r1 if r1.real >= r2.real else r2


def growth_map(Pi, k1s, k2s, p=FIG4, fn=sigma_direct):
    G = np.full((len(k2s), len(k1s)), np.nan)
    for i, k2 in enumerate(k2s):
        for jx, k1 in enumerate(k1s):
            G[i, jx] = fn(k1, k2, Pi, p).real
    return G


def fastest(Pi, k1s, k2s, p=FIG4, fn=sigma_direct):
    G = growth_map(Pi, k1s, k2s, p, fn)
    i, jx = np.unravel_index(np.nanargmax(G), G.shape)
    return k1s[jx], k2s[i], G[i, jx], G


def sigma_slow_eps0(k1, k2, Pi, p=FIG4):
    """Paper eq. 3.14 (epsilon -> 0, beta=kappa=delta=0) as an independent check of root selection."""
    c = coeffs(k1, k2, Pi, p)
    k, U, M, S, E, fN, V, a, sg = c["k"], c["U"], c["M"], c["S"], c["E"], c["fN"], c["V"], c["a"], c["sg"]
    W = 1 - 2 * a * k * U * E; PP = 1 + fN * V - 2 * a * k * U * S
    return M * (3 * sg * 1j * k1 * Pi * E - k ** 2 * S) / (3 * sg * 1j * k1 * Pi * W - k ** 2 * PP)
