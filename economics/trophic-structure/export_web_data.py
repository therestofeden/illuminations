"""
Precompute everything the browser dashboard needs -> docs/data.json
Node positions reuse the exact Python beeswarm layout so the web view matches
the static figures. Edges are thresholded to keep the payload small.
"""
import os
import json
import numpy as np
import pandas as pd
from trophic import trophic_levels_io, trophic_incoherence
from network_viz import load_country, layout
from isic_labels import label
from countries import COUNTRIES, ARCHETYPE_COLOR

os.makedirs("docs", exist_ok=True)
desc = pd.read_csv("network_descriptors.csv").set_index("code")
res = pd.read_csv("results_country.csv").set_index("code")
gdp = pd.read_csv("gdp_context.csv").set_index("code")

countries_json = {}
for code, name, arch in COUNTRIES:
    sec, Z, x = load_country(code)
    n = len(sec)
    tl = trophic_levels_io(Z, x)
    self_flow = np.diag(Z).copy()
    radii = 0.035 + 0.13 * np.sqrt(x / x.max())
    xs, ys, comm, _ = layout(Z, tl * 3.0, radii)
    nodes = []
    for i in range(n):
        nodes.append(dict(
            code=sec[i], name=label(sec[i]),
            x=round(float(xs[i]), 3), level=round(float(tl[i]), 3),
            out=float(x[i]), selfFrac=round(float(min(self_flow[i] / x[i], 1.0)), 3),
            comm=int(comm[i])))
    off = Z.copy(); np.fill_diagonal(off, 0)
    wmax = off.max()
    edges = []
    for i in range(n):
        for j in range(n):
            if off[i, j] > 0.01 * wmax:               # keep meaningful flows only
                edges.append([i, j, round(float(off[i, j] / wmax), 3)])
    countries_json[code] = dict(
        name=name, archetype=arch,
        depth=float(res.loc[code, "trophic_depth"]),
        depth_global=float(res.loc[code, "trophic_depth_global"]),
        offshore_gap=float(res.loc[code, "offshore_gap"]),
        incoherence=float(desc.loc[code, "incoherence"]),
        top_hub=label(desc.loc[code, "top_hub"]),
        n_comm=int(desc.loc[code, "n_comm"]),
        intermediation=float(desc.loc[code, "intermediation_share"]),
        nodes=nodes, edges=edges)

ranking = (res.reset_index()[["code", "country", "archetype", "trophic_depth",
            "trophic_depth_global", "offshore_gap"]]
           .sort_values("trophic_depth", ascending=False))
ranking = ranking.assign(gdp=[float(gdp.loc[c, "gdp_usd"]) for c in ranking.code]
                         ).to_dict(orient="records")

out = dict(
    meta=dict(year=2019, edition="OECD ICIO 2023 edition",
              archetype_color=ARCHETYPE_COLOR),
    countries=countries_json, ranking=ranking)

with open("docs/data.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))
sz = os.path.getsize("docs/data.json") / 1024
print(f"saved docs/data.json  ({sz:.0f} KB, {len(countries_json)} countries)")
