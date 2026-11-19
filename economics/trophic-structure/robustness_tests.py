"""
"Does it hold?" -- every v2 test of Farmer's claim in one place.

Inputs (built by earlier scripts):
  icio_country_year.csv   OECD ICIO 2023 ed., 30 economies, 2011-2020
  wiod_country_year.csv   WIOD 2016 release, 43 economies, 2000-2014
  wiod_industry_2000.csv  WIOD industry multipliers + SEA prices (mechanism test)
  pwt_growth.csv          Penn World Table 11.0 (GDP per hour / per capita)

Output: robustness_results.csv (one row per estimate) + a printed summary.

Tests
  A  Cross-section, Farmer's own design: depth at the start of a window vs mean
     annual growth of real GDP per hour over the window. Two datasets, several
     windows, with and without a catch-up control and an import-intensity control.
     Inference: HC1 and a Freedman-Lane permutation test (small n).
  B  Non-overlapping panel windows (pooled with period effects, and within-country).
  C  'Deepening' (v1's best result) re-run out of sample on WIOD.
  D  Mechanism: do industries with longer chains see faster price declines
     relative to wages? (McNerney et al.'s first prediction.) ~2,300 industries.
  B-D use wild-cluster bootstrap p-values (Rademacher, restricted), by country.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(20261119)
N_PERM = 4999
N_BOOT = 4999
RESULTS = []

icio = pd.read_csv("icio_country_year.csv")
wiod = pd.read_csv("wiod_country_year.csv")
pwt = pd.read_csv("pwt_growth.csv").set_index(["code", "year"])
# fast-converging economies a sceptic would drop: China, Vietnam and the EU
# members that joined in 2004 or later (EU accession drove both deeper supply
# chains and catch-up growth)
CONVERGERS = {"CHN", "VNM", "CZE", "EST", "HUN", "LVA", "LTU", "POL", "SVK", "SVN",
              "CYP", "MLT", "BGR", "ROU", "HRV"}
MEASURES = {"farmer_depth": "Farmer (global, final-demand weights)",
            "domestic_depth": "v1 domestic depth (output weights)"}


# ---------------------------------------------------------------- helpers ----
def ols(y, X):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b, y - X @ b


def hc1_t(y, X, k):
    n, p = X.shape
    b, e = ols(y, X)
    XtXi = np.linalg.pinv(X.T @ X)
    V = XtXi @ (X.T * e**2) @ X @ XtXi * n / (n - p)
    return b[k], b[k] / np.sqrt(V[k, k])


def cluster_t(y, X, k, g):
    n, p = X.shape
    b, e = ols(y, X)
    XtXi = np.linalg.pinv(X.T @ X)
    G = np.unique(g)
    meat = np.zeros((p, p))
    for c in G:
        s = X[g == c].T @ e[g == c]
        meat += np.outer(s, s)
    nG = len(G)
    V = XtXi @ meat @ XtXi * nG / (nG - 1) * (n - 1) / (n - p)
    return b[k], b[k] / np.sqrt(V[k, k])


def perm_p(y, X, k, t_obs):
    """Freedman-Lane: permute residuals of y on the controls, refit, compare t."""
    Xc = np.delete(X, k, axis=1)
    bc, ec = ols(y, Xc)
    fit = Xc @ bc
    hits = 0
    for _ in range(N_PERM):
        _, t = hc1_t(fit + RNG.permutation(ec), X, k)
        hits += abs(t) >= abs(t_obs)
    return (hits + 1) / (N_PERM + 1)


def wcb_p(y, X, k, g, t_obs):
    """Wild cluster bootstrap-t, restricted residuals, Rademacher weights."""
    Xc = np.delete(X, k, axis=1)
    bc, ec = ols(y, Xc)
    fit = Xc @ bc
    G, gi = np.unique(g, return_inverse=True)
    hits = 0
    for _ in range(N_BOOT):
        v = RNG.choice([-1.0, 1.0], size=len(G))[gi]
        _, t = cluster_t(fit + v * ec, X, k, g)
        hits += abs(t) >= abs(t_obs)
    return (hits + 1) / (N_BOOT + 1)


def design(df, xvar, controls, fe=()):
    cols = [np.ones(len(df)), df[xvar].to_numpy(float)]
    names = ["const", xvar]
    for c in controls:
        cols.append(df[c].to_numpy(float))
        names.append(c)
    X = np.column_stack(cols)
    for f in fe:
        D = pd.get_dummies(df[f], drop_first=True, dtype=float)
        X = np.column_stack([X, D.to_numpy()])
    return X


def record(**kw):
    RESULTS.append(kw)
    p2 = kw.get("p_resample")
    print(f"  {kw['dataset']:5s} {kw['spec']:44s} {kw['measure'][:14]:14s} "
          f"β/SD={kw['beta_sd']:+.2f}  p(HC/CR)={kw['p_analytic']:.3f}"
          + (f"  p(resample)={p2:.3f}" if p2 is not None else "") + f"  n={kw['n']}")


def growth(code, y0, y1, var="log_gdp_hour"):
    try:
        a, b = pwt.loc[(code, y0), var], pwt.loc[(code, y1), var]
    except KeyError:
        return np.nan
    return 100 * (b - a) / (y1 - y0)


def pval_from_t(t, dof):
    from scipy import stats
    return 2 * stats.t.sf(abs(t), dof)


# ---------------------------------------------------- A. cross-section ---------
def test_A():
    print("\nA. Cross-section: depth at start vs mean annual growth of GDP per hour")
    windows = [("ICIO", icio, 2011, 2019), ("ICIO", icio, 2011, 2023),
               ("WIOD", wiod, 2000, 2014), ("WIOD", wiod, 2000, 2019),
               ("WIOD", wiod, 2000, 2023)]
    for name, panel, y0, y1 in windows:
        d = panel[panel.year == y0].copy()
        d["g"] = [growth(c, y0, y1) for c in d.code]
        d["g_pc"] = [growth(c, y0, y1, "log_gdp_pc") for c in d.code]
        d["log_y0"] = [pwt.loc[(c, y0), "log_level_hour"] if (c, y0) in pwt.index else np.nan
                       for c in d.code]
        d = d.dropna(subset=["g", "log_y0"])
        for m, mlab in MEASURES.items():
            sd = d[m].std()
            for spec, ctrl, outcome in [
                ("raw", [], "g"),
                ("+ catch-up", ["log_y0"], "g"),
                ("+ catch-up + import intensity", ["log_y0", "import_int"], "g"),
                ("+ catch-up, per-capita growth", ["log_y0"], "g_pc"),
                ("+ catch-up + import int., per-capita", ["log_y0", "import_int"], "g_pc"),
                ("+ catch-up, excl. fast convergers", ["log_y0"], "g"),
            ]:
                if m == "domestic_depth" and spec != "+ catch-up":
                    continue
                dd = d[~d.code.isin(CONVERGERS)] if "excl." in spec else d
                y = dd[outcome].to_numpy(float)
                X = design(dd, m, ctrl)
                b, t = hc1_t(y, X, 1)
                loo = [ols(np.delete(y, i), np.delete(X, i, axis=0))[0][1] for i in range(len(y))]
                record(test="A cross-section", dataset=name, window=f"{y0}-{y1}",
                       spec=f"{y0}->{y1} {spec}", measure=mlab,
                       beta=b, beta_sd=b * sd, t=t, p_analytic=pval_from_t(t, len(y) - X.shape[1]),
                       p_resample=perm_p(y, X, 1, t), n=len(y),
                       loo_min_sd=min(loo) * sd, loo_max_sd=max(loo) * sd)
                if m == "farmer_depth" and spec == "raw":
                    r = np.corrcoef(d[m], d.g)[0, 1]
                    print(f"      raw Pearson r = {r:+.2f}")


# ---------------------------------------------- B. non-overlapping windows -----
def test_B():
    print("\nB. Non-overlapping windows (depth at start -> growth over window)")
    sets = [("WIOD", wiod, [(2000, 2005), (2005, 2010), (2010, 2015)]),
            ("ICIO", icio, [(2011, 2015), (2015, 2019)])]
    for name, panel, wins in sets:
        rows = []
        for y0, y1 in wins:
            for r in panel[panel.year == y0].itertuples():
                rows.append(dict(code=r.code, period=y0, farmer_depth=r.farmer_depth,
                                 domestic_depth=r.domestic_depth, import_int=r.import_int,
                                 g=growth(r.code, y0, y1),
                                 log_y0=pwt.loc[(r.code, y0), "log_level_hour"]
                                 if (r.code, y0) in pwt.index else np.nan))
        d = pd.DataFrame(rows).dropna()
        for m, mlab in MEASURES.items():
            sd = d[m].std()
            for spec, ctrl, fe in [("pooled + period FE + catch-up", ["log_y0"], ("period",)),
                                   ("within-country (country + period FE)", [], ("code", "period"))]:
                y = d.g.to_numpy(float)
                X = design(d, m, ctrl, fe)
                g = d.code.to_numpy()
                b, t = cluster_t(y, X, 1, g)
                record(test="B windows", dataset=name, window=str(wins), spec=spec,
                       measure=mlab, beta=b, beta_sd=b * sd, t=t,
                       p_analytic=pval_from_t(t, d.code.nunique() - 1),
                       p_resample=wcb_p(y, X, 1, g, t), n=len(y))


# ------------------------------------------------------- C. deepening ----------
def test_C():
    print("\nC. Deepening (Δdepth over prior 3y -> growth over next 3y), out of sample")
    for name, panel, bases in [("WIOD", wiod, range(2003, 2015)),
                               ("ICIO", icio, range(2014, 2017))]:
        P = panel.set_index(["code", "year"])
        rows = []
        for c in panel.code.unique():
            for t in bases:
                if (c, t) not in P.index or (c, t - 3) not in P.index:
                    continue
                rows.append(dict(
                    code=c, year=t,
                    d_farmer_depth=P.loc[(c, t), "farmer_depth"] - P.loc[(c, t - 3), "farmer_depth"],
                    d_domestic_depth=P.loc[(c, t), "domestic_depth"] - P.loc[(c, t - 3), "domestic_depth"],
                    fwd=growth(c, t, t + 3), past=growth(c, t - 3, t),
                    log_y0=pwt.loc[(c, t), "log_level_hour"] if (c, t) in pwt.index else np.nan))
        d = pd.DataFrame(rows).dropna()
        for m, mlab in MEASURES.items():
            x = "d_" + m
            sd = d[x].std()
            for spec, ctrl in [("Δdepth + catch-up + year FE", ["log_y0"]),
                               ("... + past-3y growth (momentum)", ["log_y0", "past"])]:
                y = d.fwd.to_numpy(float)
                X = design(d, x, ctrl, ("year",))
                g = d.code.to_numpy()
                b, t = cluster_t(y, X, 1, g)
                record(test="C deepening", dataset=name, window=f"base {min(bases)}-{max(bases)}",
                       spec=spec, measure=mlab, beta=b, beta_sd=b * sd, t=t,
                       p_analytic=pval_from_t(t, d.code.nunique() - 1),
                       p_resample=wcb_p(y, X, 1, g, t), n=len(y))


# ------------------------------------------------------- D. mechanism ----------
def test_D():
    print("\nD. Mechanism: price change relative to wages, 2000-2014, vs multiplier (2000)")
    d = pd.read_csv("wiod_industry_2000.csv")
    d = d[np.isfinite(d.real_price_change) & (d.output > 0)].copy()
    lo, hi = d.real_price_change.quantile([0.01, 0.99])
    d["rpc"] = 100 * d.real_price_change.clip(lo, hi)        # % per year, winsorised 1%
    d["id"] = d.code
    for lv, mlab in [("L_global", "Industry multiplier, global"),
                     ("L_domestic", "Industry multiplier, domestic")]:
        sd = d[lv].std()
        for spec, fe in [("country FE", ("code",)),
                         ("country FE + industry FE (strict)", ("code", "sector"))]:
            y = d.rpc.to_numpy(float)
            X = design(d, lv, [], fe)
            g = d.code.to_numpy()
            b, t = cluster_t(y, X, 1, g)
            record(test="D price mechanism", dataset="WIOD", window="2000-2014",
                   spec=spec, measure=mlab, beta=b, beta_sd=b * sd, t=t,
                   p_analytic=pval_from_t(t, d.code.nunique() - 1),
                   p_resample=wcb_p(y, X, 1, g, t), n=len(y))
    d[["code", "sector", "L_global", "L_domestic", "rpc"]].to_csv("price_test_sample.csv", index=False)


if __name__ == "__main__":
    test_A()
    test_B()
    test_C()
    test_D()
    out = pd.DataFrame(RESULTS)
    out.round(5).to_csv("robustness_results.csv", index=False)
    print(f"\nsaved robustness_results.csv ({len(out)} estimates)")
