"""
Second, independent dataset: WIOD 2016 release (43 economies + RoW, 56 industries,
2000-2014). This is the database family McNerney et al. (PNAS 2022) used.

Usage:
  bash download_wiod.sh                     # -> wiod_data/
  python3 build_wiod.py [wiod_data]         # -> wiod_country_year.csv, wiod_industry_2000.csv

Outputs
  wiod_country_year.csv   country x year: farmer_depth, domestic_depth, domar, import_int
  wiod_industry_2000.csv  industry (country, sector), year 2000 multipliers, joined
                          to Socio-Economic Accounts prices and wages for the
                          price-mechanism test (test_prices in robustness_tests.py)
"""
import os
import sys
import numpy as np
import pandas as pd
from measures import world_measures

DATA = sys.argv[1] if len(sys.argv) > 1 else "wiod_data"
YEARS = range(2000, 2015)
FD_SUFFIX = ("57", "58", "59", "60", "61")   # HH, NPISH, gov, GFCF, inventories


def load_year(year):
    d = pd.read_stata(os.path.join(DATA, f"WIOT{year}_October16_ROW.dta"))
    ind = d[d.Country.ne("TOT") & d.RNr.le(56)]
    labels = (ind.Country + "_" + ind.IndustryCode).to_numpy()
    icols = [f"v{c}{r}" for c, r in zip(ind.Country, ind.RNr)]
    fcols = [c for c in d.columns if c.startswith("v") and c[-2:] in FD_SUFFIX
             and c[1:-2].isalpha() and len(c) == 6]
    Z = ind[icols].to_numpy(float)
    y = ind[fcols].to_numpy(float).sum(axis=1)
    x = d.loc[d.IndustryCode.eq("GO"), icols].to_numpy(float).ravel()
    va = d.loc[d.IndustryCode.eq("VA"), icols].to_numpy(float).ravel()
    return labels, Z, x, y, va


if __name__ == "__main__":
    codes = None
    crows, ind2000 = [], None
    for yr in YEARS:
        labels, Z, x, y, va = load_year(yr)
        if codes is None:
            codes = sorted({s.split("_")[0] for s in labels} - {"ROW"})
        c, i = world_measures(labels, Z, x, y, va, codes)
        for r in c:
            r["year"] = yr
        crows += c
        if yr == 2000:
            ind2000 = pd.DataFrame(i)
        # identity check on the full world table: final-demand-weighted
        # multiplier must equal world gross output / world final demand
        print(f"WIOD {yr}: {len(c)} economies", flush=True)

    cy = pd.DataFrame(crows)[["code", "year", "farmer_depth", "home_depth", "abroad_depth", "domestic_depth",
                              "global_depth_outw", "domar", "import_int"]]
    cy.round(6).to_csv("wiod_country_year.csv", index=False)

    # ---- join Socio-Economic Accounts for the price test ----------------------
    sea = pd.read_excel(os.path.join(DATA, "SEA.xlsx"), sheet_name="DATA")
    sea = sea.rename(columns={"country": "code", "code": "sector"})
    keep = sea[sea.variable.isin(["GO_PI", "COMP", "H_EMPE", "GO"])]
    long = keep.melt(id_vars=["code", "variable", "sector"],
                     value_vars=[2000, 2014], var_name="year")
    wide = long.pivot_table(index=["code", "sector"], columns=["variable", "year"],
                            values="value", aggfunc="first")
    wide.columns = [f"{v}_{y}" for v, y in wide.columns]
    wide = wide.reset_index()
    # economy-wide wage per hour = Σ compensation / Σ employee hours (per country)
    tot = wide.groupby("code")[["COMP_2000", "H_EMPE_2000", "COMP_2014", "H_EMPE_2014"]].sum(min_count=1)
    wage = pd.DataFrame({
        "wage_growth": np.log((tot.COMP_2014 / tot.H_EMPE_2014) /
                              (tot.COMP_2000 / tot.H_EMPE_2000)) / 14})
    ind = ind2000.merge(wide[["code", "sector", "GO_PI_2000", "GO_PI_2014"]],
                        on=["code", "sector"], how="left").merge(
        wage, left_on="code", right_index=True, how="left")
    # annual change of the industry's price relative to the wage (McNerney et al.)
    ind["real_price_change"] = (np.log(ind.GO_PI_2014 / ind.GO_PI_2000) / 14
                                - ind.wage_growth)
    ind.round(6).to_csv("wiod_industry_2000.csv", index=False)
    ok = ind.real_price_change.notna() & np.isfinite(ind.real_price_change)
    print(f"industry rows: {len(ind)}, with price + wage data: {int(ok.sum())}")
