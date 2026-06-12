"""
Append domestic trophic depth (+ incoherence) for every country to panel.csv,
for each ICIO year CSV passed on the command line.

Usage: python3 build_panel.py icio2023/2016_SML.csv icio2023/2017_SML.csv ...
"""

import os
import re
import sys
import numpy as np
import pandas as pd
from trophic import trophic_levels_io, trophic_incoherence
from countries import COUNTRIES

PANEL = "panel.csv"
codes = [c for c, _, _ in COUNTRIES]


def year_from_name(path):
    m = re.search(r"(\d{4})", os.path.basename(path))
    return int(m.group(1))


def metrics_for_csv(path):
    year = year_from_name(path)
    header = pd.read_csv(path, nrows=0).columns.tolist()
    idx = header[0]
    sec = {c: [h for h in header if h.startswith(c + "_")] for c in codes}
    df = pd.read_csv(path, usecols=[idx] + sum(sec.values(), [])).set_index(idx)
    df.index = df.index.astype(str)
    rows = []
    for code, name, arch in COUNTRIES:
        cols = [c for c in sec[code] if c in df.index]
        if not cols:
            continue
        Z = df.loc[cols, cols].to_numpy(float)
        x = df.loc["OUT", cols].to_numpy(float)
        lv = trophic_levels_io(Z, x)
        w = x / x.sum()
        rows.append(dict(code=code, country=name, archetype=arch, year=year,
                         trophic_depth=round(float(np.sum(w * lv)), 5),
                         incoherence=round(float(trophic_incoherence(Z)), 5)))
    return rows


all_rows = []
for path in sys.argv[1:]:
    r = metrics_for_csv(path)
    all_rows += r
    print(f"{os.path.basename(path)}: {len(r)} countries")

new = pd.DataFrame(all_rows)
if os.path.exists(PANEL):
    old = pd.read_csv(PANEL)
    new = pd.concat([old, new]).drop_duplicates(["code", "year"], keep="last")
new.sort_values(["code", "year"]).to_csv(PANEL, index=False)
print(f"panel.csv now has {len(new)} country-year rows, "
      f"years {new.year.min()}-{new.year.max()}")
