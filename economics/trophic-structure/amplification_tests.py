"""
Is it the chains or the links?  Amplification vs composition.

Farmer's model: an economy's growth ≈ L̄ x γ̃, chain length times the speed at
which its industries improve. If longer-chain countries grow faster, two
stories fit:
  amplification  the same productivity gains are multiplied along longer chains
                 (what the model says);
  composition    long-chain countries simply contain faster-improving industries
                 (manufacturing), and the chain itself adds nothing.

Tests (WIOD 2016, 43 economies; outcome = growth of real GDP per hour, PWT 11.0)
  1  g ~ L̄ (+ catch-up)                         baseline
  2  g ~ L̄ + γ̃ (+ catch-up)                     does chain length survive γ̃?
  3  g ~ model prediction θ'(I-Aᵀ)⁻¹γ           the full network model
  4  g ~ final-stage part + network part         does the upstream (network) part
                                                 carry information of its own?
  5  forecast 2007->2014 with L̄(2007) x γ̃(2000-07), the paper's zero-parameter
     forecast (PNAS Fig. 6C), against simpler benchmarks.

Output: amplification_results.csv, forecast_results.csv
"""
import numpy as np
import pandas as pd
from robustness_tests import ols, hc1_t, perm_p, pval_from_t, growth, pwt

amp = pd.read_csv("wiod_amplification.csv")
ROWS = []


def level(c, y):
    return pwt.loc[(c, y), "log_level_hour"] if (c, y) in pwt.index else np.nan


def sample(y0, y1, gdef="gamma", drop=()):
    d = amp[(amp.y0 == y0) & (amp.y1 == y1) & (amp.gamma_def == gdef)].copy()
    d = d[~d.code.isin(drop)]
    d["g"] = [growth(c, y0, y1) for c in d.code]
    d["log_y0"] = [level(c, y0) for c in d.code]
    d["network_part"] = d.pred_network - d.pred_no_network
    return d.dropna(subset=["g", "log_y0"])


def fit(d, xs, label, focus, variant):
    X = np.column_stack([np.ones(len(d))] + [d[x].to_numpy(float) for x in xs])
    y = d.g.to_numpy(float)
    out = dict(spec=label, variant=variant, n=len(d))
    _, e = ols(y, X)
    out["r2"] = 1 - e.var() / y.var()
    for k, x in enumerate(xs, start=1):
        if x not in focus:
            continue
        b, t = hc1_t(y, X, k)
        out[f"b_{x}"] = b
        out[f"t_{x}"] = t
        out[f"p_{x}"] = pval_from_t(t, len(y) - X.shape[1])
        out[f"pperm_{x}"] = perm_p(y, X, k, t)
        if x == "L_bar":
            out["beta_sd_L_bar"] = b * d.L_bar.std()
    ROWS.append(out)
    msg = "  ".join(f"{x}: {out[f'b_{x}']:+.2f} (p={out[f'pperm_{x}']:.3f})" for x in focus)
    print(f"  {label:44s} {variant:22s} {msg}  R²={out['r2']:.2f} n={len(d)}")


if __name__ == "__main__":
    print("2000-2014, growth of GDP per hour (% a year)")
    variants = [("all 43", "gamma", ()),
                ("excl. Russia (41% imputed)", "gamma", ("RUS",)),
                ("γ net of capital", "gamma_k", ())]
    for vlabel, gdef, drop in variants:
        d = sample(2000, 2014, gdef, drop)
        fit(d, ["L_bar", "log_y0"], "1 chain length + catch-up", ["L_bar"], vlabel)
        fit(d, ["L_bar", "gamma_tilde", "log_y0"], "2 + industry productivity growth γ̃",
            ["L_bar", "gamma_tilde"], vlabel)
        fit(d, ["pred_network", "log_y0"], "3 full model prediction", ["pred_network"], vlabel)
        fit(d, ["pred_no_network", "network_part", "log_y0"], "4 final-stage + network part",
            ["pred_no_network", "network_part"], vlabel)
        if vlabel == "all 43":
            r = np.corrcoef(d.L_bar, d.gamma_tilde)[0, 1]
            print(f"  corr(L̄, γ̃) = {r:.2f}")
            ROWS.append(dict(spec="corr(L_bar, gamma_tilde)", variant=vlabel, n=len(d), r2=r ** 2,
                             corr=r))

    # ---- forecast, PNAS Fig. 6C style ---------------------------------------
    print("\nForecast of mean growth 2007-2014 from information available in 2007")
    a07 = amp[(amp.y0 == 2007) & (amp.y1 == 2014) & (amp.gamma_def == "gamma")].set_index("code")
    a00 = amp[(amp.y0 == 2000) & (amp.y1 == 2007) & (amp.gamma_def == "gamma")].set_index("code")
    f = pd.DataFrame({"L07": a07.L_bar, "gam_0007": a00.gamma_tilde})
    f["actual"] = [growth(c, 2007, 2014) for c in f.index]
    f["past"] = [growth(c, 2000, 2007) for c in f.index]
    f = f.dropna()
    cands = {
        "Farmer: L̄(2007) x γ̃(2000-07)": f.L07 * f.gam_0007,
        "same γ̃, average chain length": f.L07.mean() * f.gam_0007,
        "past growth 2000-07 (persistence)": f.past,
        "everyone grows at the 2000-07 average": pd.Series(f.past.mean(), index=f.index),
    }
    frows = []
    for name, pred in cands.items():
        err = f.actual - pred
        frows.append(dict(forecast=name, rmse=float(np.sqrt((err ** 2).mean())),
                          corr=float(np.corrcoef(pred, f.actual)[0, 1]) if pred.std() > 0 else np.nan,
                          n=len(f)))
        print(f"  {name:42s} RMSE {frows[-1]['rmse']:.2f}  corr {frows[-1]['corr']:+.2f}")
    pd.DataFrame(frows).round(4).to_csv("forecast_results.csv", index=False)
    f.round(5).to_csv("forecast_sample.csv")
    pd.DataFrame(ROWS).round(5).to_csv("amplification_results.csv", index=False)
    print("\nsaved amplification_results.csv, forecast_results.csv")
