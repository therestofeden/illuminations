"""
Industry productivity growth (gamma) and the full network prediction of
McNerney et al. (PNAS 2022), on WIOD 2016.

Why: chain length alone is only half of Farmer's prediction. The model says a
country grows at roughly  g ≈ L̄ x γ̃ : the average chain length *times* how fast
its industries improve. The cross-country link between L̄ and growth could come
from that multiplication (amplification) or simply from long-chain countries
having faster-improving industries (composition). Separating the two needs γ.

gamma_i (annual, % a year) = growth of real gross output minus share-weighted
growth of real inputs. Following the paper, inputs are intermediates and labour:

    gamma_i = dln GO_QI - s_II * dln II_QI - s_L * dln EMP

s_II, s_L = average cost shares (II/GO, LAB/GO) at the two ends of the window.
Labour = persons engaged (hours are missing for China). A variant also nets out
capital (s_K * dln real K, K deflated with the value-added price index).

Outputs
  wiod_gamma.csv          industry x window: gamma (with/without capital)
  wiod_amplification.csv  country x window: L̄, γ̃, model-predicted growth
                          (network and no-network parts)

Usage: python3 build_productivity.py [wiod_data]
"""
import os
import sys
import numpy as np
import pandas as pd
from measures import multipliers
from build_wiod import load_year

DATA = sys.argv[1] if len(sys.argv) > 1 else "wiod_data"
WINDOWS = [(2000, 2014), (2000, 2007), (2007, 2014)]

sea = pd.read_excel(os.path.join(DATA, "SEA.xlsx"), sheet_name="DATA")
sea = sea.rename(columns={"country": "code", "code": "sector"})


def var(name, year):
    d = sea[sea.variable == name].set_index(["code", "sector"])[year]
    return d.astype(float)


def gamma_window(y0, y1):
    T = y1 - y0
    with np.errstate(divide="ignore", invalid="ignore"):
        dq = np.log(var("GO_QI", y1) / var("GO_QI", y0))
        dm = np.log(var("II_QI", y1) / var("II_QI", y0))
        dl = np.log(var("EMP", y1) / var("EMP", y0))
        kr0 = var("K", y0) / var("VA_PI", y0)
        kr1 = var("K", y1) / var("VA_PI", y1)
        dk = np.log(kr1 / kr0)
        s_ii = 0.5 * (var("II", y0) / var("GO", y0) + var("II", y1) / var("GO", y1))
        s_l = 0.5 * (var("LAB", y0) / var("GO", y0) + var("LAB", y1) / var("GO", y1))
        s_k = 0.5 * (var("CAP", y0) / var("GO", y0) + var("CAP", y1) / var("GO", y1))
    g = pd.DataFrame({
        "gamma": 100 * (dq - s_ii * dm - s_l * dl) / T,
        "gamma_k": 100 * (dq - s_ii * dm - s_l * dl - s_k.clip(lower=0) * dk) / T,
        "go0": var("GO", y0),
    }).replace([np.inf, -np.inf], np.nan)
    g["y0"], g["y1"] = y0, y1
    return g.reset_index()


def fill_and_trim(g, col):
    """Winsorise at 1/99% and impute missing industries (and RoW) with the
    output-weighted cross-country mean of the same industry."""
    lo, hi = g[col].quantile([0.01, 0.99])
    g[col] = g[col].clip(lo, hi)
    ok = g[col].notna() & (g.go0 > 0)
    wmean = (g[ok].assign(w=g.go0 * g[col]).groupby("sector")
             .apply(lambda d: d.w.sum() / d.go0.sum(), include_groups=False))
    return g, wmean


if __name__ == "__main__":
    gam_rows, amp_rows = [], []
    tables = {}
    for y0, y1 in WINDOWS:
        g = gamma_window(y0, y1)
        if y0 not in tables:
            tables[y0] = load_year(y0)
        labels, Z, x, y, va = tables[y0]
        sector_of = np.array([s.split("_", 1)[1] for s in labels])
        code_of = np.array([s.split("_", 1)[0] for s in labels])
        L = multipliers(Z, x)
        act = x > 0
        A = Z / np.where(act, x, 1.0)
        A[~act, :] = 0
        A[:, ~act] = 0
        for col in ("gamma", "gamma_k"):
            g, wmean = fill_and_trim(g, col)
            gi = g.set_index(["code", "sector"])[col]
            vec = np.array([gi.get((c, s), np.nan) for c, s in zip(code_of, sector_of)])
            imputed = np.isnan(vec)
            vec[imputed] = [wmean.get(s, np.nan) for s in sector_of[imputed]]
            vec = np.nan_to_num(vec)
            # model: industry price change r = -(I - A^T)^-1 gamma  =>  growth of
            # what final demand can buy = theta . (I - A^T)^-1 gamma
            Hg = np.linalg.solve(np.eye(len(x)) - A.T, vec)
            for c in sorted(set(code_of) - {"ROW"}):
                k = code_of == c
                yc = np.clip(y[k], 0, None)
                th = yc / yc.sum()
                eta = x[k] / x[k].sum()
                amp_rows.append(dict(
                    code=c, y0=y0, y1=y1, gamma_def=col,
                    L_bar=float(th @ L[k]),                     # chain length (eq. 5)
                    gamma_tilde=float(eta @ vec[k]),            # output-weighted γ
                    pred_network=float(th @ Hg[k]),             # full model: θ'(I-Aᵀ)⁻¹γ
                    pred_no_network=float(th @ vec[k]),         # final stage only
                    pred_simple=float(th @ L[k]) * float(eta @ vec[k]),   # L̄ x γ̃
                    share_imputed=float(imputed[k].mean())))
            g[f"missing_{col}"] = g[col].isna()
        gam_rows.append(g)
        print(f"window {y0}-{y1}: gamma built for {g.code.nunique()} economies", flush=True)

    pd.concat(gam_rows).round(5).to_csv("wiod_gamma.csv", index=False)
    amp = pd.DataFrame(amp_rows)
    amp.round(6).to_csv("wiod_amplification.csv", index=False)
    m = amp[(amp.gamma_def == "gamma") & (amp.y0 == 2000) & (amp.y1 == 2014)]
    print(m[["L_bar", "gamma_tilde", "pred_network", "pred_no_network"]].describe().round(3))
    print("corr(L̄, γ̃) 2000-2014:", round(np.corrcoef(m.L_bar, m.gamma_tilde)[0, 1], 2),
          "| max share of industries imputed:", round(m.share_imputed.max(), 3))
