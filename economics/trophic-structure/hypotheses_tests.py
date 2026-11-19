"""
Two hypotheses about production chains and growth.

  H1 (Farmer / McNerney et al.)  Longer chains -> faster growth, wherever the
     steps happen. Chain length L̄ is measured on the world table.
  H2 (this study)                Where the steps happen matters: the part of the
     chain located at home predicts growth beyond total length.

Decomposition (same final-demand weights for both parts):
     L̄ = L̄_home + L̄_abroad
L̄_home counts the steps reachable without leaving the country; L̄_abroad the
extra steps that happen abroad. Under H1 only the total matters, so the two
parts should carry the same coefficient. H2 says L̄_home carries more.

Tests
  1  growth ~ L̄_home + L̄_abroad (+ catch-up)    each part's own effect
  2  growth ~ L̄ + L̄_home (+ catch-up)           H2 directly: does home matter
                                                beyond total length? (= the
                                                difference of the two slopes in 1)
     cross-sections on both databases and all horizons, also without the fast
     convergers; pooled non-overlapping windows; within-country windows.
  3  prices: do industry prices fall faster with home stages or with stages
     abroad? (WIOD industries, country FE, then + industry FE)

Permutation p (cross-sections), wild-cluster bootstrap p (panels).
Output: hypotheses_results.csv
"""
import numpy as np
import pandas as pd
from robustness_tests import (ols, hc1_t, cluster_t, perm_p, wcb_p, pval_from_t, growth, pwt,
                              CONVERGERS)

icio = pd.read_csv("icio_country_year.csv")
wiod = pd.read_csv("wiod_country_year.csv")
ROWS = []


def level(c, y):
    return pwt.loc[(c, y), "log_level_hour"] if (c, y) in pwt.index else np.nan


def X_of(d, cols, fe=()):
    X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in cols])
    for f in fe:
        X = np.column_stack([X, pd.get_dummies(d[f], drop_first=True, dtype=float).to_numpy()])
    return X


def record(d, y, X, cols, focus, meta, clustered=False):
    out = dict(meta, n=len(y))
    for k, c in enumerate(cols, start=1):
        if c not in focus:
            continue
        if clustered:
            b, t = cluster_t(y, X, k, d.code.to_numpy())
            p_a = pval_from_t(t, d.code.nunique() - 1)
            p_r = wcb_p(y, X, k, d.code.to_numpy(), t)
        else:
            b, t = hc1_t(y, X, k)
            p_a = pval_from_t(t, len(y) - X.shape[1])
            p_r = perm_p(y, X, k, t)
        sd = d[c].std()
        out.update({f"b_{c}": b, f"bsd_{c}": b * sd, f"t_{c}": t,
                    f"p_{c}": p_a, f"pres_{c}": p_r})
    ROWS.append(out)
    msg = "  ".join(f"{c}: {out[f'bsd_{c}']:+.2f}/SD (p={out[f'pres_{c}']:.3f})" for c in focus)
    print(f"  {meta['dataset']} {meta['window']:10s} {meta['spec']:34s} {msg}  n={len(y)}")


def cross_section(name, panel, y0, y1, drop_conv=False):
    d = panel[panel.year == y0].copy()
    if drop_conv:
        d = d[~d.code.isin(CONVERGERS)]
    d["g"] = [growth(c, y0, y1) for c in d.code]
    d["log_y0"] = [level(c, y0) for c in d.code]
    d = d.dropna(subset=["g", "log_y0"])
    y = d.g.to_numpy(float)
    sub = " (no convergers)" if drop_conv else ""
    for cols, focus, spec in [
        (["home_depth", "abroad_depth", "log_y0"], ["home_depth", "abroad_depth"], "home + abroad" + sub),
        (["farmer_depth", "home_depth", "log_y0"], ["farmer_depth", "home_depth"], "H2: total + home" + sub),
    ]:
        record(d, y, X_of(d, cols), cols, focus,
               dict(test="cross-section", dataset=name, window=f"{y0}-{y1}", spec=spec))


def windows(name, panel, wins):
    rows = []
    for y0, y1 in wins:
        for r in panel[panel.year == y0].itertuples():
            rows.append(dict(code=r.code, period=y0, home_depth=r.home_depth,
                             abroad_depth=r.abroad_depth, farmer_depth=r.farmer_depth,
                             g=growth(r.code, y0, y1), log_y0=level(r.code, y0)))
    d = pd.DataFrame(rows).dropna()
    y = d.g.to_numpy(float)
    for cols, fe, spec in [(["home_depth", "abroad_depth", "log_y0"], ("period",), "pooled windows: home + abroad"),
                           (["home_depth", "abroad_depth"], ("code", "period"), "within-country: home + abroad")]:
        record(d, y, X_of(d, cols, fe), cols, ["home_depth", "abroad_depth"],
               dict(test="windows", dataset=name, window=str(len(wins)) + " windows", spec=spec),
               clustered=True)


def prices():
    d = pd.read_csv("wiod_industry_2000.csv")
    d = d[np.isfinite(d.real_price_change) & (d.output > 0)].copy()
    lo, hi = d.real_price_change.quantile([0.01, 0.99])
    d["rpc"] = 100 * d.real_price_change.clip(lo, hi)
    d["L_home"] = d.L_domestic
    d["L_abroad"] = d.L_global - d.L_domestic
    y = d.rpc.to_numpy(float)
    for fe, spec in [(("code",), "prices: country FE"), (("code", "sector"), "prices: + industry FE")]:
        record(d, y, X_of(d, ["L_home", "L_abroad"], fe), ["L_home", "L_abroad"], ["L_home", "L_abroad"],
               dict(test="prices", dataset="WIOD", window="2000-2014", spec=spec), clustered=True)


if __name__ == "__main__":
    print("Cross-sections: growth of GDP per hour on the two parts of chain length")
    for name, panel, y0, y1 in [("ICIO", icio, 2011, 2019), ("ICIO", icio, 2011, 2023),
                                ("WIOD", wiod, 2000, 2014), ("WIOD", wiod, 2000, 2019),
                                ("WIOD", wiod, 2000, 2023)]:
        cross_section(name, panel, y0, y1)
    for name, panel, y0, y1 in [("ICIO", icio, 2011, 2019), ("WIOD", wiod, 2000, 2019)]:
        cross_section(name, panel, y0, y1, drop_conv=True)
    print("\nNon-overlapping windows")
    windows("WIOD", wiod, [(2000, 2005), (2005, 2010), (2010, 2015)])
    windows("ICIO", icio, [(2011, 2015), (2015, 2019)])
    print("\nIndustry prices relative to wages, 2000-2014")
    prices()
    pd.DataFrame(ROWS).round(5).to_csv("hypotheses_results.csv", index=False)
    print("\nsaved hypotheses_results.csv")
