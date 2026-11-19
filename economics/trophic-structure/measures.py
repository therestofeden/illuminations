"""
v2 depth measures, shared by the OECD ICIO and WIOD pipelines.

The key change from v1: the headline country measure now follows the definition
in McNerney, Savoie, Caravelli, Carvalho & Farmer (PNAS 2022, eq. 5):

    L      = (I - A^T)^-1 1                (output multiplier of every industry,
                                            solved on the WORLD table)
    L̄_c    = Σ_{i in c} θ_i L_i,  θ_i = y_i / Σ_{j in c} y_j

where y_i is final demand (households, government, NPISH, investment, inventories,
from every country) for industry i's output. v1 used output weights and cut the
chain at the national border ("domestic depth"); that number is kept as a
secondary metric because it answers a different question ("how much of the chain
does the country own?").

Also exposed:
  domar          gross output / value added. A closed-economy identity makes it
                 equal to L̄; in open economies it tracks L̄ closely and is easy
                 to explain ("euros of sales per euro of value added").
  import_int     imported intermediate inputs / gross output. The obvious
                 confounder: a country can have long chains simply because it is
                 plugged into foreign supply chains.
"""

import numpy as np


def multipliers(Z, x):
    """Output multipliers L = (I - A^T)^-1 1 (column sums of the Leontief inverse).

    Zero-output industries have no production recipe; their rows and columns are
    dropped from A so they cannot corrupt the solve (they get L = 1, weight 0).
    """
    Z = np.asarray(Z, float)
    x = np.asarray(x, float)
    n = len(x)
    act = x > 0
    A = Z / np.where(act, x, 1.0)
    A[~act, :] = 0.0
    A[:, ~act] = 0.0
    return np.linalg.solve(np.eye(n) - A.T, np.ones(n))


def world_measures(labels, Z, x, y, va, codes):
    """Country-level measures from one world input-output table.

    labels : industry labels "CCC_sector" (country prefix + "_")
    Z      : (n, n) intermediate flows, supplier row -> user column
    x, y, va : gross output, total final demand, value added per industry
    codes  : countries to report

    Returns (country_rows, industry_rows) as lists of dicts.
    """
    labels = np.asarray(labels)
    with np.errstate(divide="ignore", invalid="ignore"):
        return _world_measures(labels, Z, x, y, va, codes)


def _world_measures(labels, Z, x, y, va, codes):
    Lg = multipliers(Z, x)
    prefix = np.array([s.split("_", 1)[0] for s in labels])
    crow, irow = [], []
    for c in codes:
        k = np.flatnonzero(prefix == c)
        if len(k) == 0:
            continue
        xc = x[k]
        Ld = multipliers(Z[np.ix_(k, k)], xc)
        wx = xc / xc.sum()
        yc = np.clip(y[k], 0, None)
        wy = yc / yc.sum()
        foreign = np.flatnonzero(prefix != c)
        crow.append(dict(
            code=c,
            farmer_depth=float(wy @ Lg[k]),          # headline (PNAS eq. 5)
            domestic_depth=float(wx @ Ld),           # v1 headline
            global_depth_outw=float(wx @ Lg[k]),     # v1 "global" number
            domar=float(xc.sum() / va[k].sum()),
            import_int=float(Z[np.ix_(foreign, k)].sum() / xc.sum()),
        ))
        for j, kk in enumerate(k):
            irow.append(dict(code=c, sector=labels[kk].split("_", 1)[1],
                             L_global=float(Lg[kk]), L_domestic=float(Ld[j]),
                             output=float(xc[j]), final_demand=float(y[kk])))
    return crow, irow


if __name__ == "__main__":
    # Self-test 1: a closed 3-stage chain, all final demand at the top.
    # raw -> mid -> final; multipliers 1, 2, 3; L̄ = 3 = gross output / VA.
    Z = np.array([[0, 100, 0], [0, 0, 100], [0, 0, 0]], float)
    x = np.array([100, 100, 100], float)
    y = np.array([0, 0, 100], float)
    va = x - Z.sum(axis=0)
    c, _ = world_measures(["AAA_r", "AAA_m", "AAA_f"], Z, x, y, va, ["AAA"])
    assert np.isclose(c[0]["farmer_depth"], 3) and np.isclose(c[0]["domar"], 3), c
    # Self-test 2: split the chain across a border. Country B's final stage buys
    # from country A, so B's domestic depth is 1 but its global depth is 3.
    c, _ = world_measures(["AAA_r", "AAA_m", "BBB_f"], Z, x, y, va, ["AAA", "BBB"])
    b = {r["code"]: r for r in c}["BBB"]
    assert np.isclose(b["farmer_depth"], 3) and np.isclose(b["domestic_depth"], 1), b
    assert np.isclose(b["import_int"], 1.0), b
    print("measures.py self-tests passed")
