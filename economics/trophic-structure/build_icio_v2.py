"""
v2 measures on the OECD ICIO (2023 edition), one row per country-year.

Usage: python3 build_icio_v2.py icio2023/20{11..20}_SML.csv   -> icio_country_year.csv

Fixes a latent v1 bug: "intermediate sectors = labels that are both a row and a
column" also catches the "OUT" total, which slipped into the global solve. It was
harmless only because OUT x OUT is zero; here it is filtered explicitly.
"""
import os
import re
import sys
import pandas as pd
from measures import world_measures
from countries import COUNTRIES

FD = ("HFCE", "NPISH", "GGFC", "GFCF", "INVNT", "DPABR")
TOTALS = {"OUT", "VA", "TLS"}


def load(path):
    df = pd.read_csv(path, index_col=0)
    df.index = df.index.astype(str)
    sectors = [c for c in df.columns if c in df.index and c not in TOTALS and "_" in c]
    fd_cols = [c for c in df.columns if c.split("_")[-1] in FD]
    Z = df.loc[sectors, sectors].to_numpy(float)
    x = df.loc["OUT", sectors].to_numpy(float)
    va = df.loc["VA", sectors].to_numpy(float)
    y = df.loc[sectors, fd_cols].to_numpy(float).sum(axis=1)
    return sectors, Z, x, y, va


if __name__ == "__main__":
    codes = [c for c, _, _ in COUNTRIES]
    rows = []
    for path in sys.argv[1:]:
        year = int(re.search(r"(\d{4})", os.path.basename(path)).group(1))
        c, _ = world_measures(*load(path), codes)
        for r in c:
            r["year"] = year
        rows += c
        print(f"ICIO {year}: {len(c)} economies", flush=True)
    out = pd.DataFrame(rows)[["code", "year", "farmer_depth", "home_depth", "abroad_depth", "domestic_depth",
                              "global_depth_outw", "domar", "import_int"]]
    out.sort_values(["code", "year"]).round(6).to_csv("icio_country_year.csv", index=False)
