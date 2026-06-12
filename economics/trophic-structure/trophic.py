"""
Trophic structure of an economy from an input-output matrix.

Method: MacKay, Johnson & Sansom, "How directed is a directed network?"
Royal Society Open Science 7:201138 (2020). The "improved" trophic level is
defined for ANY weighted directed network (no basal node required) by solving a
single weighted-Laplacian linear system. Trophic incoherence falls out of the
same quantities.

Convention used here: an edge i -> j carries the weight of goods that supplier i
sells to user j. Trophic level then increases DOWNSTREAM: primary inputs sit low,
final-goods sectors sit high. This matches the "production depth" notion in
McNerney, Savoie, Caravelli, Carvalho & Farmer, "How production networks amplify
economic growth", PNAS 119 (2022).
"""

import numpy as np


def trophic_levels(W):
    """Improved (MacKay et al. 2020) trophic levels of a weighted digraph.

    Parameters
    ----------
    W : (n, n) array; W[i, j] = weight of edge i -> j (supplier i to user j).

    Returns
    -------
    h : (n,) array of trophic levels, gauge-fixed so min(h) == 0.
    """
    W = np.asarray(W, dtype=float)
    s_out = W.sum(axis=1)          # out-strength (sells)
    s_in = W.sum(axis=0)           # in-strength  (buys)
    u = s_in + s_out               # total strength
    v = s_in - s_out               # imbalance
    Lap = np.diag(u) - W - W.T     # weighted Laplacian (symmetric, singular)
    # Lap is rank-deficient (one null direction per connected component, plus
    # isolated nodes). Least-squares gives the minimum-norm solution, which is
    # well defined within each component; re-gauge so the minimum level is 0.
    h, *_ = np.linalg.lstsq(Lap, v, rcond=None)
    return h - h.min()


def trophic_levels_io(Z, x):
    """McNerney/Farmer production trophic level = total output multiplier.

    A sector's level is 1 + the input-share-weighted average level of its
    suppliers, with labour / value added as the implicit basal input. Sectors
    that buy only primary inputs sit at level 1; sectors fed by long chains of
    other producers sit higher. Equals row sums of the Leontief inverse, i.e.
    the output multiplier (McNerney et al., PNAS 2022).

    Parameters
    ----------
    Z : (n, n) intermediate-flow matrix, Z[i, j] = supplier i -> user j.
    x : (n,) gross output per sector.

    Returns
    -------
    t : (n,) trophic levels (>= 1).
    """
    Z = np.asarray(Z, dtype=float)
    x = np.asarray(x, dtype=float)
    n = Z.shape[0]
    active = x > 0                  # inactive (zero-output) sectors are basal
    xs = np.where(active, x, 1.0)
    A = Z / xs                      # technical coefficients: A[i, j] = Z[i,j]/x_j
    # An inactive sector has no production recipe and ships nothing real: drop
    # its column (no inputs) and row (no sales) so it can't corrupt the system.
    A[~active, :] = 0.0
    A[:, ~active] = 0.0
    t = np.linalg.solve(np.eye(n) - A.T, np.ones(n))
    return t


def trophic_incoherence(W, h=None):
    """Trophic incoherence F0: weighted variance of edge stretch (h_j - h_i - 1).

    0 = perfectly coherent (every edge climbs exactly one level); larger = more
    tangled / less hierarchical.
    """
    W = np.asarray(W, dtype=float)
    if h is None:
        h = trophic_levels(W)
    tot = W.sum()
    if tot == 0:
        return np.nan
    ii, jj = np.nonzero(W)
    stretch = h[jj] - h[ii] - 1.0
    return float(np.sum(W[ii, jj] * stretch ** 2) / tot)


# --- self-test on networks with known answers -------------------------------
if __name__ == "__main__":
    # 1) Simple chain A->B->C: levels 0,1,2 and perfect coherence.
    chain = np.array([[0, 1, 0],
                      [0, 0, 1],
                      [0, 0, 0]], float)
    h = trophic_levels(chain)
    assert np.allclose(h, [0, 1, 2]), h
    assert abs(trophic_incoherence(chain, h)) < 1e-12
    print("chain levels      :", h, " incoherence:", trophic_incoherence(chain, h))

    # 2) Diamond A->B, A->C, B->D, C->D: A=0, B=C=1, D=2, still coherent.
    diamond = np.array([[0, 1, 1, 0],
                        [0, 0, 0, 1],
                        [0, 0, 0, 1],
                        [0, 0, 0, 0]], float)
    h = trophic_levels(diamond)
    assert np.allclose(h, [0, 1, 1, 2]), h
    assert abs(trophic_incoherence(diamond, h)) < 1e-12
    print("diamond levels    :", h, " incoherence:", trophic_incoherence(diamond, h))

    # 3) Feedback loop adds incoherence: A->B->C plus a back-edge C->A.
    loop = np.array([[0, 1, 0],
                     [0, 0, 1],
                     [1, 0, 0]], float)
    h = trophic_levels(loop)
    print("loop levels       :", h, " incoherence:", trophic_incoherence(loop, h))
    assert trophic_incoherence(loop, h) > 0.5

    # 4) IO multiplier trophic level on a chain raw->mid->final, each buyer
    #    spending 100% on its single supplier: levels should be 1, 2, 3.
    Z = np.array([[0, 100, 0],    # raw -> mid
                  [0, 0, 100],    # mid -> final
                  [0, 0, 0]], float)
    x = np.array([100, 100, 100], float)  # outputs
    t = trophic_levels_io(Z, x)
    assert np.allclose(t, [1, 2, 3]), t
    print("io-chain levels   :", t)
    print("ALL SELF-TESTS PASSED")
