"""Windowed spectral analysis of subglacial bedform fields.

For each square window of a DEM (projected, metres) we estimate:
  - flow azimuth (deg from north, 0-180) from the anisotropy of the spectrum
  - lateral (cross-flow) and longitudinal (along-flow) characteristic wavelengths
    from peaks of the background-normalised power spectrum (Perron et al. 2008 style)
  - regularity indices from the band-passed autocorrelation (secondary-peak height),
    which separates genuinely periodic spacing from randomly placed bumps of a
    characteristic size (those give a spectral hump but no ACF secondary peak).

Conventions: array row 0 is north; x = east, y = north.
"""
from __future__ import annotations
import numpy as np
from numpy.fft import fft2, ifft2, fftshift, fftfreq
from scipy.ndimage import gaussian_filter, map_coordinates


def hann2d(n: int) -> np.ndarray:
    w = np.hanning(n)
    return np.outer(w, w)


def detrend_plane(z: np.ndarray) -> np.ndarray:
    n0, n1 = z.shape
    yy, xx = np.mgrid[0:n0, 0:n1]
    A = np.c_[xx.ravel(), yy.ravel(), np.ones(z.size)]
    c, *_ = np.linalg.lstsq(A, z.ravel(), rcond=None)
    return z - (A @ c).reshape(z.shape)


def _freq_grid(n: int, dx: float):
    f = fftshift(fftfreq(n, d=dx))           # cycles / m
    kx = f[None, :].repeat(n, 0)             # east
    ky = -f[:, None].repeat(n, 1)            # north (row 0 = north)
    return kx, ky


def analyze_window(z: np.ndarray, dx: float, lam_min: float = 150.0,
                   lam_max: float = 3000.0, wedge_deg: float = 15.0) -> dict:
    n = z.shape[0]
    assert z.shape == (n, n)
    z = detrend_plane(z.astype(float))
    w = hann2d(n)
    zw = z * w
    F = fftshift(fft2(zw))
    P = np.abs(F) ** 2 / (w ** 2).sum()
    kx, ky = _freq_grid(n, dx)
    kr = np.hypot(kx, ky)
    band = (kr >= 1 / lam_max) & (kr <= 1 / lam_min)

    # --- power-law background fit (median log power in log-spaced radial bins)
    edges = np.logspace(np.log10(1 / lam_max), np.log10(1 / lam_min), 25)
    lk, lp = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (kr >= a) & (kr < b)
        if m.sum() >= 4:
            lk.append(np.log10(np.sqrt(a * b)))
            lp.append(np.median(np.log10(P[m] + 1e-30)))
    slope, icpt = np.polyfit(lk, lp, 1)
    bg = np.zeros_like(P)
    bg[kr > 0] = 10 ** (icpt + slope * np.log10(kr[kr > 0]))
    # median of exponential distribution = ln2 * mean -> correct to mean
    bg /= np.log(2)
    Pn = np.where(kr > 0, P / np.maximum(bg, 1e-30), 0)
    Pn_s = gaussian_filter(Pn, 1.0)

    # --- orientation from spectral inertia tensor of excess normalised power
    wgt = np.where(band, np.clip(Pn_s - 1, 0, None), 0)
    if wgt.sum() <= 0:
        wgt = np.where(band, Pn_s, 0)
    Ixx = (wgt * kx * kx).sum(); Iyy = (wgt * ky * ky).sum(); Ixy = (wgt * kx * ky).sum()
    evals, evecs = np.linalg.eigh(np.array([[Ixx, Ixy], [Ixy, Iyy]]))
    v = evecs[:, 1]                           # major k-axis = cross-flow direction
    anis = float(1 - evals[0] / evals[1]) if evals[1] > 0 else 0.0
    ang_k = np.arctan2(v[1], v[0])            # math angle of cross-flow k-axis
    # flow direction is perpendicular; azimuth from north, clockwise, folded 0-180
    flow_vec = np.array([-v[1], v[0]])
    flow_az = float(np.degrees(np.arctan2(flow_vec[0], flow_vec[1])) % 180)

    out = dict(flow_az=flow_az, anisotropy=anis, beta=float(-slope))
    for name, axis_ang in (("lat", ang_k), ("long", ang_k + np.pi / 2)):
        ka = np.arctan2(ky, kx)
        d = np.abs(((ka - axis_ang + np.pi / 2) % np.pi) - np.pi / 2)
        wedge = band & (d <= np.radians(wedge_deg))
        if wedge.sum() == 0:
            out.update({f"lam_{name}": np.nan, f"pk_{name}": np.nan}); continue
        # radial profile within wedge
        prof_k, prof_p = [], []
        rb = np.linspace(1 / lam_max, 1 / lam_min, 60)
        for a, b in zip(rb[:-1], rb[1:]):
            m = wedge & (kr >= a) & (kr < b)
            if m.any():
                prof_k.append(0.5 * (a + b)); prof_p.append(Pn[m].mean())
        prof_k = np.array(prof_k); prof_p = gaussian_filter(np.array(prof_p), 1.0)
        i = int(np.argmax(prof_p))
        out[f"lam_{name}"] = float(1 / prof_k[i])
        out[f"pk_{name}"] = float(prof_p[i])
        # peak sharpness Q = k_peak / FWHM of (profile - 1) excess above background
        ex = prof_p - 1.0; half = ex[i] / 2
        q = np.nan
        if ex[i] > 0:
            l = i
            while l > 0 and ex[l] > half: l -= 1
            r = i
            while r < len(ex) - 1 and ex[r] > half: r += 1
            fw = prof_k[r] - prof_k[l]
            if fw > 0 and l > 0 and r < len(ex) - 1:
                q = float(prof_k[i] / fw)
        out[f"q_{name}"] = q

    # --- regularity from band-passed, taper-corrected autocorrelation
    lk2 = np.log(np.maximum(kr, 1e-12))
    lo, hi = np.log(1 / lam_max), np.log(1 / lam_min)
    # smooth (log-Gaussian-edged) band-pass to limit ringing
    bp = np.clip((lk2 - lo) / 0.35, 0, 1) * np.clip((hi - lk2) / 0.35, 0, 1)
    bp = np.where(kr > 0, bp, 0)
    Fb = F * bp
    acf = np.real(fftshift(ifft2(np.fft.ifftshift(np.abs(Fb) ** 2))))
    Wf = fft2(w)
    wacf = np.real(fftshift(ifft2(np.abs(Wf) ** 2)))
    c = n // 2
    acf = acf / np.maximum(wacf / wacf[c, c], 1e-3)
    acf /= acf[c, c]
    rmax_px = int(0.4 * n)
    lags = np.arange(1, rmax_px)
    for name, axis_ang in (("lat", ang_k), ("long", ang_k + np.pi / 2)):
        ux, uy = np.cos(axis_ang), np.sin(axis_ang)
        cols = c + lags * ux; rows = c - lags * uy
        prof = map_coordinates(acf, [rows, cols], order=1)
        # first minimum then highest subsequent maximum within 0.4 n
        reg, reg_lag = 0.0, np.nan
        dmin = np.where((prof[1:-1] < prof[:-2]) & (prof[1:-1] <= prof[2:]))[0]
        if len(dmin):
            j0 = dmin[0] + 1
            seg = prof[j0:]
            if len(seg) > 2:
                j = int(np.argmax(seg))
                if 0 < j < len(seg) - 1 or seg[j] > seg[0]:
                    reg = float(max(seg[j], 0.0)); reg_lag = float((lags[j0 + j]) * dx)
        out[f"reg_{name}"] = reg
        out[f"reglag_{name}"] = reg_lag
    out["relief_std"] = float(np.std(z))
    return out


def iter_windows(dem: np.ndarray, win: int, step: int, valid: np.ndarray | None = None,
                 min_valid: float = 0.9):
    H, W = dem.shape
    for r in range(0, H - win + 1, step):
        for cc in range(0, W - win + 1, step):
            if valid is not None:
                fv = valid[r:r + win, cc:cc + win].mean()
                if fv < min_valid:
                    continue
            yield r, cc


# ---------------------------------------------------------------- synthetics
def fractal_noise(n: int, dx: float, beta: float, amp: float, rng) -> np.ndarray:
    kx, ky = _freq_grid(n, dx)
    kr = np.hypot(kx, ky); kr[kr == 0] = np.inf
    spec = kr ** (-beta / 2) * np.exp(2j * np.pi * rng.random((n, n)))
    z = np.real(ifft2(np.fft.ifftshift(spec)))
    return amp * z / z.std()


def synthetic_field(n: int = 512, dx: float = 20.0, lat_spacing: float = 500.0,
                    long_spacing: float = 1500.0, flow_az: float = 30.0,
                    width: float = 250.0, elong: float = 3.0, height: float = 15.0,
                    jitter: float = 0.15, size_cv: float = 0.25, placement: str = "lattice",
                    noise_amp: float = 5.0, noise_beta: float = 2.5, seed: int = 0,
                    regional_slope: float = 0.003, hc_factor: float = 1.0,
                    return_centers: bool = False):
    """Field of elongated Gaussian drumlins. placement='lattice' (staggered rows with
    jitter) or 'poisson' (same density, random positions)."""
    rng = np.random.default_rng(seed)
    L = n * dx
    az = np.radians(flow_az)
    fx, fy = np.sin(az), np.cos(az)        # flow unit vector (east, north)
    cx_, cy_ = fy, -fx                      # cross-flow unit vector
    ext = 1.6 * L
    pts = []
    if placement == "lattice":
        nu = int(ext / long_spacing) + 2; nv = int(ext / lat_spacing) + 2
        for i in range(-nu, nu + 1):
            for j in range(-nv, nv + 1):
                u = i * long_spacing; v = j * lat_spacing + (0.5 * lat_spacing if i % 2 else 0)
                u += rng.normal(0, jitter * long_spacing); v += rng.normal(0, jitter * lat_spacing)
                pts.append((u, v))
    elif placement == "poisson":
        dens = 1.0 / (lat_spacing * long_spacing)
        npts = rng.poisson(dens * (2 * ext) ** 2)
        pts = list(zip(rng.uniform(-ext, ext, npts), rng.uniform(-ext, ext, npts)))
    elif placement == "hardcore":
        # random sequential adsorption of non-overlapping drumlins at the lattice density:
        # in coordinates scaled by elongation (u/elong, v) footprints are ~circles of
        # diameter `width`; reject candidates closer than hc_factor*width.
        dens = 1.0 / (lat_spacing * long_spacing)
        target = int(dens * (2 * ext) ** 2)
        dmin = hc_factor * width
        cell = dmin
        grid = {}
        tries = 0
        while len(pts) < target and tries < 60 * target:
            tries += 1
            u, v = rng.uniform(-ext, ext, 2)
            us = u / elong
            gi, gj = int(np.floor(us / cell)), int(np.floor(v / cell))
            ok = True
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    for (pu, pv) in grid.get((gi + a, gj + b), ()):
                        if (pu - us) ** 2 + (pv - v) ** 2 < dmin ** 2:
                            ok = False; break
                    if not ok: break
                if not ok: break
            if ok:
                grid.setdefault((gi, gj), []).append((us, v)); pts.append((u, v))
    else:
        raise ValueError(placement)
    xs = (np.arange(n) + 0.5) * dx - L / 2
    X, Y = np.meshgrid(xs, -xs)
    z = np.zeros((n, n))
    centers = []
    for (u0, v0) in pts:
        # centre in map coords
        x0 = u0 * fx + v0 * cx_; y0 = u0 * fy + v0 * cy_
        s = np.exp(rng.normal(0, size_cv))
        wv = width * s / 2.5; wu = width * elong * s / 2.5
        R = 4 * wu
        c0 = int((x0 + L / 2) / dx); r0 = int((L / 2 - y0) / dx); rp = int(R / dx) + 1
        ra, rb = max(r0 - rp, 0), min(r0 + rp, n); ca, cb = max(c0 - rp, 0), min(c0 + rp, n)
        if ra >= rb or ca >= cb:
            continue
        Xs = X[ra:rb, ca:cb] - x0; Ys = Y[ra:rb, ca:cb] - y0
        du = (Xs * fx + Ys * fy) / wu; dv = (Xs * cx_ + Ys * cy_) / wv
        z[ra:rb, ca:cb] += height * s * np.exp(-(du ** 2 + dv ** 2))
        if 0 <= r0 < n and 0 <= c0 < n:
            centers.append((r0, c0))
    z += fractal_noise(n, dx, noise_beta, noise_amp, rng)
    z += regional_slope * (X + 0.5 * Y)
    return (z, np.array(centers)) if return_centers else z
