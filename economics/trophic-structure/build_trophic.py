"""
Compute trophic structure for the 30 economies from one ICIO year.

Outputs:
  results_country.csv  - one row per country (depth, incoherence, max level, ...)
  results_sectors.csv  - one row per (country, sector): trophic level + output share

Data: OECD ICIO 2023 edition, year 2019 (regular/SML, ISIC Rev.4).
Source host: stats.oecd.org. See README for provenance.
"""

import sys
import numpy as np
import pandas as pd
from trophic import trophic_levels_io, trophic_incoherence
from countries import COUNTRIES

CSV = sys.argv[1] if len(sys.argv) > 1 else "icio2023/2019_SML.csv"
YEAR = 2019
EDITION = "OECD ICIO 2023 edition"

codes = [c for c, _, _ in COUNTRIES]

# ---- figure out which columns we need, then read only those -----------------
df = pd.read_csv(CSV).set_index(pd.read_csv(CSV, nrows=0).columns[0])
df.index = df.index.astype(str)
sector_cols = {c: [h for h in df.columns if h.startswith(c + "_")] for c in codes}

# ---- GLOBAL network: trophic level of every sector in the full ICIO ---------
# A sector's suppliers include FOREIGN sectors, so chains are not truncated at
# the border. This is the McNerney/Farmer global-value-chain trophic level.
all_sectors = [s for s in df.columns if s in df.index]      # intermediate cells
Zg = df.loc[all_sectors, all_sectors].to_numpy(float)
xg = df.loc["OUT", all_sectors].to_numpy(float)
tg = trophic_levels_io(Zg, xg)
global_level = dict(zip(all_sectors, tg))


def country_network(code):
    # intermediate sectors = labels that are BOTH a row and a column
    cols = [c for c in sector_cols[code] if c in df.index]
    Z = df.loc[cols, cols].to_numpy(float)             # domestic block only
    output = df.loc["OUT", cols].to_numpy(float)
    levels = trophic_levels_io(Z, output)              # domestic chain depth
    glob = np.array([global_level[c] for c in cols])   # global chain depth
    F0 = trophic_incoherence(Z)
    w = output / output.sum()
    depth = float(np.sum(w * levels))
    depth_g = float(np.sum(w * glob))
    return dict(cols=cols, levels=levels, glob=glob, output=output,
                depth=depth, depth_global=depth_g, incoherence=F0,
                max_level=float(levels.max()),
                spread=float(np.sqrt(np.sum(w * (levels - depth) ** 2))))


rows_c, rows_s = [], []
for code, name, arch in COUNTRIES:
    r = country_network(code)
    rows_c.append(dict(code=code, country=name, archetype=arch,
                       trophic_depth=round(r["depth"], 4),
                       trophic_depth_global=round(r["depth_global"], 4),
                       offshore_gap=round(r["depth_global"] - r["depth"], 4),
                       incoherence=round(r["incoherence"], 4),
                       max_level=round(r["max_level"], 4),
                       spread=round(r["spread"], 4)))
    wshare = r["output"] / r["output"].sum()
    for sec, lv, gl, ws in zip(r["cols"], r["levels"], r["glob"], wshare):
        rows_s.append(dict(code=code, country=name, archetype=arch,
                           sector=sec.split("_", 1)[1],
                           level=round(float(lv), 4),
                           level_global=round(float(gl), 4),
                           output_share=round(float(ws), 6)))

cdf = pd.DataFrame(rows_c).sort_values("trophic_depth", ascending=False)
sdf = pd.DataFrame(rows_s)
cdf.to_csv("results_country.csv", index=False)
sdf.to_csv("results_sectors.csv", index=False)

print(f"{EDITION}, year {YEAR}  —  {len(cdf)} economies\n")
print(cdf[["country", "archetype", "trophic_depth", "trophic_depth_global",
           "offshore_gap", "incoherence"]].to_string(index=False))
