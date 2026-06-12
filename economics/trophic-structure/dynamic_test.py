"""
The dynamic test of Farmer's claim: do deeper / deepening production chains
predict faster SUBSEQUENT GDP growth?

Panel: domestic trophic depth, 30 economies, 2011-2020 (OECD ICIO 2023 ed.).
Growth: World Bank real GDP growth. Forward window = mean growth over the next
3 years. To keep the dependent variable clean we use base years t = 2011..2016,
so the 3-year growth window ends by 2019 (pre-COVID).

Three specifications, all with country-clustered standard errors:
  M1  pooled:        fwd3 ~ depth + log(GDPpc)        (+ year effects)
  M2  within-country: fwd3 ~ depth + country FE       (+ year effects)   <-- key
  M3  change:        fwd3 ~ Δdepth(prior 3y) + log(GDPpc)(+ year effects)
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

panel = pd.read_csv("panel.csv")
g = pd.read_csv("growth_panel.csv")
gmap = {(r.code, r.year): r.growth for r in g.itertuples()}
pcmap = {(r.code, r.year): r.gdp_pc_ppp for r in g.itertuples()}
depth = {(r.code, r.year): r.trophic_depth for r in panel.itertuples()}

H = 3
rows = []
for code in panel.code.unique():
    for t in range(2011, 2017):                       # base years
        d_t = depth.get((code, t))
        pc = pcmap.get((code, t))
        fwd = [gmap.get((code, t + k)) for k in range(1, H + 1)]
        if d_t is None or pc is None or any(v is None for v in fwd):
            continue
        d_lag = depth.get((code, t - 3))
        rows.append(dict(code=code, year=t, depth=d_t,
                         log_gdppc=np.log(pc),
                         fwd3=float(np.mean(fwd)),
                         ddepth3=(d_t - d_lag) if d_lag is not None else np.nan))

d = pd.DataFrame(rows)
print(f"Analysis sample: {len(d)} country-year windows, "
      f"{d.code.nunique()} countries, base years {d.year.min()}-{d.year.max()}\n")


def run(formula, data, label):
    m = smf.ols(formula, data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data["code"]})
    key = [p for p in m.params.index if p in ("depth", "ddepth3")][0]
    b, se, p = m.params[key], m.bse[key], m.pvalues[key]
    print(f"{label:46s}  {key}: {b:+.3f}  (SE {se:.3f}, p={p:.3f}, "
          f"n={int(m.nobs)}, R2={m.rsquared:.2f})")
    return m


print("Dependent variable: average real GDP growth over the next 3 years (%)\n")
run("fwd3 ~ depth", d, "Raw (no controls)")
run("fwd3 ~ depth + log_gdppc", d, "M1a: + catch-up control")
run("fwd3 ~ depth + log_gdppc + C(year)", d, "M1: + catch-up + year FE")
run("fwd3 ~ depth + log_gdppc + C(year) + C(code)", d, "M2: within-country (country FE)  KEY")
dd = d.dropna(subset=["ddepth3"])
run("fwd3 ~ ddepth3 + log_gdppc + C(year)", dd, "M3: deepening (Δdepth, prior 3y)")

d.to_csv("dynamic_sample.csv", index=False)
print("\nsaved dynamic_sample.csv")
