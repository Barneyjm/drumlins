"""Conditional spacing test: are drumlins more evenly spaced than the same footprints
placed at random, without overlap, inside the same drumlin patch?

Statistic: coefficient of variation (CV) of centroid nearest-neighbour distance.
Regular patterns have low CV; the null keeps every footprint's exact shape/size/orientation
and the patch outline, so packing (hard-core) and patchiness effects are matched.
Also reports Clark-Evans-like ratio mean_NN(obs)/mean_NN(null)."""
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree


def nn_stats(pts: np.ndarray):
    if len(pts) < 5:
        return np.nan, np.nan
    d, _ = cKDTree(pts).query(pts, k=2)
    nn = d[:, 1]
    return float(nn.std() / nn.mean()), float(nn.mean())


def patch_domain(lab: np.ndarray, valid: np.ndarray, dx: float, close_m: float = 600.0):
    fp = lab > 0
    r = max(int(close_m / dx), 1)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (xx ** 2 + yy ** 2) <= r * r
    dom = ndi.binary_closing(fp, structure=disk, iterations=1) | fp
    dom = ndi.binary_dilation(dom, structure=disk[::2, ::2] if r > 4 else disk)
    return dom & valid


def footprints(lab: np.ndarray):
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        if sl is None:
            continue
        m = lab[sl] == i
        if m.any():
            rr, cc = np.nonzero(m)
            out.append((m, rr.mean(), cc.mean(), rr.mean() + sl[0].start, cc.mean() + sl[1].start))
    return out


def rsa_once(fps, dom: np.ndarray, rng, max_tries: int = 400):
    H, W = dom.shape
    occ = np.zeros((H + 2, W + 2), bool)          # padded occupancy (1-px buffer)
    dr, dc = np.nonzero(dom)
    order = np.argsort([-f[0].sum() for f in fps])  # largest first
    cents = []
    for k in order:
        m, cr, cc = fps[k][:3]
        h, w = m.shape
        for _ in range(max_tries):
            j = rng.integers(len(dr))
            r0 = dr[j] - int(round(cr)); c0 = dc[j] - int(round(cc))   # put centroid on a domain pixel
            if r0 < 0 or c0 < 0 or r0 + h > H or c0 + w > W:
                continue
            if not dom[r0:r0 + h, c0:c0 + w][m].all():
                continue
            if occ[r0:r0 + h + 2, c0:c0 + w + 2][1:-1, 1:-1][m].any():
                continue
            # occupy footprint + 1 px buffer
            occ[r0:r0 + h + 2, c0:c0 + w + 2] |= ndi.binary_dilation(np.pad(m, 1), iterations=1)
            cents.append((dr[j], dc[j]))
            break
    return np.array(cents, float), len(cents) / len(fps)


def rsa_place(masks, dom: np.ndarray, rng, max_tries: int = 400, order=None):
    """Random sequential placement of footprint masks inside dom without overlap.
    Returns list of (index, r0, c0) for placed masks."""
    H, W = dom.shape
    occ = np.zeros((H + 2, W + 2), bool)
    dr, dc = np.nonzero(dom)
    if order is None:
        order = np.argsort([-m.sum() for m in masks])
    placed = []
    for k in order:
        m = masks[k]; h, w = m.shape
        for _ in range(max_tries):
            j = rng.integers(len(dr))
            r0 = dr[j] - h // 2; c0 = dc[j] - w // 2
            if r0 < 0 or c0 < 0 or r0 + h > H or c0 + w > W:
                continue
            if not dom[r0:r0 + h, c0:c0 + w][m].all():
                continue
            if occ[r0 + 1:r0 + h + 1, c0 + 1:c0 + w + 1][m].any():
                continue
            occ[r0:r0 + h + 2, c0:c0 + w + 2] |= ndi.binary_dilation(np.pad(m, 1))
            placed.append((k, r0, c0))
            break
    return placed


def object_shuffle_test(z_relief: np.ndarray, lab: np.ndarray, valid: np.ndarray, dx: float,
                        nsim: int = 49, seed: int = 0, min_n: int = 15, lam_max: float = 5000.0):
    """Spectral sharpness of the observed object arrangement vs. random non-overlapping
    rearrangements of the same relief objects within the same patch domain."""
    from spectral import analyze_window
    objs = []
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        if sl is None:
            continue
        m = lab[sl] == i
        if m.any():
            objs.append((m, np.where(m, z_relief[sl], 0.0), sl))
    if len(objs) < min_n:
        return None
    n = lab.shape[0]
    obs = np.zeros(lab.shape)
    for m, rel, sl in objs:
        obs[sl] += rel
    ro = analyze_window(obs, dx, lam_max=lam_max)
    dom = patch_domain(lab, valid, dx)
    rng = np.random.default_rng(seed)
    masks = [o[0] for o in objs]
    qn, pkn, fills = [], [], []
    for _ in range(nsim):
        pl = rsa_place(masks, dom, rng)
        fills.append(len(pl) / len(objs))
        cv = np.zeros(lab.shape)
        for k, r0, c0 in pl:
            m, rel, _ = objs[k]; h, w = m.shape
            cv[r0:r0 + h, c0:c0 + w] += rel
        r = analyze_window(cv, dx, lam_max=lam_max)
        qn.append(np.nan_to_num(r["q_lat"])); pkn.append(r["pk_lat"])
    qn, pkn = np.array(qn), np.array(pkn)
    qo = np.nan_to_num(ro["q_lat"])
    return dict(n=len(objs), q_obs=float(qo), q_null_med=float(np.median(qn)),
                p_q=float((1 + np.sum(qn >= qo)) / (1 + nsim)),
                pk_obs=float(ro["pk_lat"]), pk_null_med=float(np.median(pkn)),
                p_pk=float((1 + np.sum(pkn >= ro["pk_lat"])) / (1 + nsim)),
                lam_lat=float(ro["lam_lat"]), flow_az=float(ro["flow_az"]),
                fill=float(np.mean(fills)))


def conditional_test(lab: np.ndarray, valid: np.ndarray, dx: float, nsim: int = 99,
                     seed: int = 0, min_n: int = 15):
    fps = footprints(lab)
    if len(fps) < min_n:
        return None
    pts = np.array([[f[3], f[4]] for f in fps]) * dx
    cv_obs, mnn_obs = nn_stats(pts)
    dom = patch_domain(lab, valid, dx)
    rng = np.random.default_rng(seed)
    cvs, mnns, fills = [], [], []
    for _ in range(nsim):
        c, f = rsa_once(fps, dom, rng)
        fills.append(f)
        cv, mnn = nn_stats(c * dx)
        cvs.append(cv); mnns.append(mnn)
    cvs = np.array(cvs)
    p = (1 + np.sum(cvs <= cv_obs)) / (1 + nsim)
    return dict(n=len(fps), cv_obs=cv_obs, cv_null_med=float(np.median(cvs)),
                cv_null_sd=float(np.std(cvs)), z=float((cv_obs - cvs.mean()) / (cvs.std() + 1e-12)),
                p_regular=float(p), mnn_ratio=float(mnn_obs / np.median(mnns)),
                fill=float(np.mean(fills)), mnn_obs_m=mnn_obs)
