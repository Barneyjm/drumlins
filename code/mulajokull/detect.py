"""Individual drumlin detection from a projected DEM."""
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import h_maxima
from skimage.segmentation import watershed


def tophat_relief(z: np.ndarray, dx: float, element_m: float = 1000.0) -> np.ndarray:
    k = int(element_m / dx) | 1
    return z - ndi.grey_opening(z, size=(k, k))


def detect(z: np.ndarray, dx: float, valid: np.ndarray | None = None, flow_az=None,
           h_thresh: float = 2.0, h_split: float = 2.0, min_area: float = 0.01e6,
           max_area: float = 3.0e6, min_elong: float = 1.3, max_dev: float = 30.0,
           element_m: float = 1000.0, h_peak: float = 6.0, half_frac: float = 0.5,
           pre_close_px: int = 0):
    """Return (labels, props). props: list of dicts with row/col centroid, area_m2,
    length_m, width_m, az (deg 0-180). flow_az: scalar or callable(row, col)->deg; drumlins
    whose long axis deviates more than max_dev are rejected (removes non-streamlined ridges)."""
    if valid is None:
        valid = np.isfinite(z)
    if pre_close_px:
        # fill narrow linear cuts (roads, rail, ditches) narrower than the element
        z = ndi.grey_closing(z, size=(pre_close_px, pre_close_px))
    th = ndi.gaussian_filter(tophat_relief(np.where(valid, z, np.nanmin(z)), dx, element_m), 1.0)
    fg = (th > h_thresh) & valid
    mk = h_maxima(np.where(fg, th, 0), h_split) & fg & (th >= h_peak)
    markers, _ = ndi.label(mk)
    ws = watershed(-th, markers, mask=fg)
    # trim each basin to its half-height footprint (compact drumlin outline)
    peak = ndi.maximum(th, ws, index=np.arange(ws.max() + 1))
    peak = np.asarray(peak); peak[0] = np.inf
    ws = np.where(th >= half_frac * peak[ws], ws, 0)
    # keep only the connected piece containing the peak
    lab = np.zeros_like(ws)
    props, keep = [], np.zeros(ws.max() + 1, bool)
    for i, sl in enumerate(ndi.find_objects(ws), start=1):
        if sl is None:
            continue
        sub = ws[sl] == i
        cl, nc = ndi.label(sub)
        if nc > 1:
            pk = np.unravel_index(np.argmax(np.where(sub, th[sl], -np.inf)), sub.shape)
            sub = cl == cl[pk]
        lab[sl][sub] = i
    objs = ndi.find_objects(lab)
    for i, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        m = lab[sl] == i
        a = m.sum() * dx * dx
        if a < min_area or a > max_area:
            continue
        rr, cc = np.nonzero(m)
        rr = rr + sl[0].start; cc = cc + sl[1].start
        x, y = cc * dx, -rr * dx
        C = np.cov(np.vstack([x, y]))
        ev, evec = np.linalg.eigh(C)
        if ev[0] <= 0:
            continue
        L, W = 4 * np.sqrt(ev[1]), 4 * np.sqrt(ev[0])
        if L / W < min_elong:
            continue
        vx, vy = evec[:, 1]
        az = float(np.degrees(np.arctan2(vx, vy)) % 180)
        if flow_az is not None:
            fa = flow_az(rr.mean(), cc.mean()) if callable(flow_az) else flow_az
            d = abs(az - fa) % 180; d = min(d, 180 - d)
            if d > max_dev:
                continue
        keep[i] = True
        props.append(dict(label=i, row=float(rr.mean()), col=float(cc.mean()), area_m2=float(a),
                          length_m=float(L), width_m=float(W), az=az,
                          height_m=float(th[rr, cc].max())))
    lab = np.where(keep[lab], lab, 0)
    return lab, props
