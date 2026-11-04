"""Theoretical bounds on bedform length L and width W from the Fowler & Chapwanya linear stability model.
L = pi*l_D/k1, W = pi*l_D/k2 (half-wavelengths); l_D = sqrt(eta*u0/(drho_wi*g))."""
import json, numpy as np
from stability import growth_map

k1s = np.geomspace(0.03, 60, 110); k2s = np.r_[0.0, np.geomspace(0.03, 120, 120)]
out = {}
for Pi in (0.8, 1.0, 1.3, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 20.0):
    G = growth_map(Pi, k1s, k2s)                           # rows k2, cols k1
    gmax = np.nanmax(G); i, j = np.unravel_index(np.nanargmax(G), G.shape)
    K1, K2 = np.meshgrid(k1s, k2s)
    unst = G > 0; half = G >= 0.5 * gmax
    def rng(mask):
        k1v, k2v = K1[mask], K2[mask]; k2p = k2v[k2v > 0]
        return dict(L_min=float(np.pi / k1v.max()), L_max=float(np.pi / k1v.min()),
                    W_min=float(np.pi / k2p.max()) if k2p.size else None, W_max=float(np.pi / k2p.min()) if k2p.size else None,
                    E_min=float(np.min((k2v[k2v > 0]) / k1v[k2v > 0])) if k2p.size else None,
                    E_max=float(np.max((k2v[k2v > 0]) / k1v[k2v > 0])) if k2p.size else None)
    out[Pi] = dict(Lstar=float(np.pi / k1s[j]), Wstar=float(np.pi / k2s[i]) if k2s[i] > 0 else None, gmax=float(gmax),
                   unstable=rng(unst), halfmax=rng(half),
                   unstable_hits_grid_edge=bool(unst[:, -1].any() or unst[-1, :].any()))
    u, h = out[Pi]["unstable"], out[Pi]["halfmax"]
    ws = f"{out[Pi]['Wstar']:.2f}" if out[Pi]["Wstar"] else "inf"
    print(f"Pi {Pi:5.1f}: fastest L*={out[Pi]['Lstar']:.2f} W*={ws} (x l_D) | half-max band L {h['L_min']:.2f}-{h['L_max']:.2f}, "
          f"W {h['W_min'] if h['W_min'] is None else round(h['W_min'],2)}-{h['W_max'] if h['W_max'] is None else round(h['W_max'],2)}, "
          f"L/W {h['E_min'] if h['E_min'] is None else round(h['E_min'],2)}-{h['E_max'] if h['E_max'] is None else round(h['E_max'],2)} | "
          f"growth>0 reaches smallest grid scale: {out[Pi]['unstable_hits_grid_edge']}; largest unstable L {u['L_max']:.1f}, W {u['W_max'] if u['W_max'] is None else round(u['W_max'],1)}")
json.dump({str(k): v for k, v in out.items()}, open("bounds.json", "w"), indent=1)

# theory's own speed exponents at fixed eta, l_c*, Gamma: l_D ~ u^(1/2), Pi ~ u^(-1/2)
curve = json.load(open("stability_curve.json")); c = [r for r in curve if 2 <= r["Pi"] <= 8]
lp = np.log([r["Pi"] for r in c])
aL = np.polyfit(lp, np.log([r["L"] for r in c]), 1)[0]; aW = np.polyfit(lp, np.log([r["W"] for r in c]), 1)[0]
print(f"\nshape sensitivity (Pi 2-8): dlnL*/dlnPi={aL:+.2f}, dlnW*/dlnPi={aW:+.2f}")
print(f"theory speed exponents: L ~ u^{0.5 - 0.5*aL:.2f}, W ~ u^{0.5 - 0.5*aW:.2f}, L/W ~ u^{-0.5*(aL - aW):.2f}")
print("\nl_D (m) = sqrt(eta*u0/(83*9.81)):")
for eta in (3e13, 1e14, 3e14):
    print(f"  eta={eta:.0e} Pa s: " + ", ".join(f"u0={u0:>4} m/a -> {np.sqrt(eta * u0 / 31556926 / (83 * 9.81)):5.0f}" for u0 in (30, 100, 300, 1000)))
