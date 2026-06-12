"""
Structural descriptors of all 30 production networks -> network_descriptors.csv,
then correlations with wealth/growth and archetype means, to surface insights.
"""
import numpy as np
import pandas as pd
import networkx as nx
import community as community_louvain
from trophic import trophic_levels_io, trophic_incoherence
from countries import COUNTRIES

CSV = "icio2023/2019_SML.csv"
RESOURCE = {"A01_02", "A03", "B05_06", "B07_08", "B09", "C19"}   # primary + refining
INTERMED = {"G", "K", "L", "M", "N"}     # trade, finance, real estate, prof, admin svc

header = pd.read_csv(CSV, nrows=0).columns.tolist()
idx = header[0]


def country(code):
    cols_all = [h for h in header if h.startswith(code + "_")]
    df = pd.read_csv(CSV, usecols=[idx] + cols_all).set_index(idx)
    df.index = df.index.astype(str)
    cols = [c for c in cols_all if c in df.index]
    Z = df.loc[cols, cols].to_numpy(float)
    x = df.loc["OUT", cols].to_numpy(float)
    sec = [c.split("_", 1)[1] for c in cols]
    keep = x > 0
    return [s for s, k in zip(sec, keep) if k], Z[np.ix_(keep, keep)], x[keep]


def descriptors(code):
    sec, Z, x = country(code)
    n = len(sec)
    tl = trophic_levels_io(Z, x)
    w = x / x.sum()
    depth = float((w * tl).sum())
    off = Z.copy(); np.fill_diagonal(off, 0)
    # self-flow share of all intermediate transactions
    self_share = float(np.trace(Z) / Z.sum())
    # hub concentration: Herfindahl of throughflow (in+out strength)
    strength = off.sum(0) + off.sum(1)
    s_share = strength / strength.sum()
    hhi = float((s_share ** 2).sum())
    top_hub = sec[int(np.argmax(strength))]
    # communities
    W = off + off.T
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for i in range(n):
        for j in range(i + 1, n):
            if W[i, j] > 0:
                G.add_edge(i, j, weight=W[i, j])
    part = community_louvain.best_partition(G, weight="weight", random_state=1)
    n_comm = len(set(part.values()))
    mod = community_louvain.modularity(part, G, weight="weight")
    # where the mass sits
    mass_low = float(w[tl < 1.25].sum())
    mass_high = float(w[tl > 1.75].sum())
    resource_share = float(sum(w[i] for i in range(n) if sec[i] in RESOURCE))
    interm_share = float(sum(w[i] for i in range(n) if sec[i] in INTERMED))
    return dict(code=code, depth=round(depth, 3), max_level=round(float(tl.max()), 3),
                incoherence=round(trophic_incoherence(Z), 3),
                self_share=round(self_share, 3), hub_hhi=round(hhi, 3),
                top_hub=top_hub, n_comm=n_comm, modularity=round(mod, 3),
                mass_low=round(mass_low, 3), mass_high=round(mass_high, 3),
                resource_share=round(resource_share, 3),
                intermediation_share=round(interm_share, 3))


rows = [descriptors(c) for c, _, _ in COUNTRIES]
d = pd.DataFrame(rows)
meta = pd.read_csv("results_country.csv")[["code", "country", "archetype"]]
gdp = pd.read_csv("gdp_context.csv")[["code", "gdp_pc_ppp", "growth_2010_19"]]
d = d.merge(meta, on="code").merge(gdp, on="code")
d["log_gdppc"] = np.log(d["gdp_pc_ppp"])
d.to_csv("network_descriptors.csv", index=False)

print("=== descriptor correlations with log GDP per capita and 2010-19 growth ===")
num = ["depth", "max_level", "incoherence", "self_share", "hub_hhi", "n_comm",
       "modularity", "mass_low", "mass_high", "resource_share", "intermediation_share"]
for col in num:
    r_w = d[col].corr(d["log_gdppc"])
    r_g = d[col].corr(d["growth_2010_19"])
    print(f"  {col:22s}  vs wealth r={r_w:+.2f}   vs growth r={r_g:+.2f}")

print("\n=== archetype means ===")
print(d.groupby("archetype")[["depth", "self_share", "hub_hhi", "n_comm",
      "mass_low", "intermediation_share"]].mean().round(3).to_string())

print("\n=== most common top hub ===")
print(d["top_hub"].value_counts().to_string())
print("\nsaved network_descriptors.csv")
