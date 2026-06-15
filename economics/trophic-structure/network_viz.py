"""
Farmer-style trophic production networks from OECD ICIO.

For one country: nodes = sectors, stacked VERTICALLY by trophic level (raw inputs
low, final-facing sectors high). Each node is drawn as in Farmer's book:
  - outer ring  -> community membership (Louvain on the flow network)
  - green disk   -> throughflow (gross output)
  - inner pink   -> self-flow (a sector buying its own output, Z[i,i])
Directed green edges carry intermediate flows; the heaviest are drawn as arrows.

Usage: python3 network_viz.py DEU SAU
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
import matplotlib.patheffects as pe
import networkx as nx
import community as community_louvain
from trophic import trophic_levels_io
from isic_labels import label
from countries import COUNTRIES

CSV = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".csv") else "icio2023/2019_SML.csv"
ARGS = [a for a in sys.argv[1:] if not a.endswith(".csv")]
GREEN, PINK = "#3aa86b", "#e76b86"
COMM_PALETTE = ["#c9a227", "#7a5c3e", "#3d6b7d", "#5a7d5a", "#c1672d",
                "#8a5fa3", "#cf4f4f", "#4f9d9d", "#9d8b4f"]
name_of = {c: n for c, n, _ in COUNTRIES}


def load_country(code):
    header = pd.read_csv(CSV, nrows=0).columns.tolist()
    idx = header[0]
    cols_all = [h for h in header if h.startswith(code + "_")]
    df = pd.read_csv(CSV, usecols=[idx] + cols_all).set_index(idx)
    df.index = df.index.astype(str)
    cols = [c for c in cols_all if c in df.index]
    Z = df.loc[cols, cols].to_numpy(float)
    x = df.loc["OUT", cols].to_numpy(float)
    codes = [c.split("_", 1)[1] for c in cols]
    # keep sectors that have output AND are connected to the production network
    off = Z.copy(); np.fill_diagonal(off, 0)
    connected = (off.sum(0) + off.sum(1)) > 0
    keep = (x > 0) & connected
    return ([c for c, k in zip(codes, keep) if k],
            Z[np.ix_(keep, keep)], x[keep])


def layout(Z, tl, radii):
    """Beeswarm: y = exact trophic level, x = spread to remove overlaps."""
    n = len(tl)
    W = Z + Z.T
    np.fill_diagonal(W, 0)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for i in range(n):
        for j in range(i + 1, n):
            if W[i, j] > 0:
                G.add_edge(i, j, weight=W[i, j])
    part = community_louvain.best_partition(G, weight="weight", random_state=1)
    comm = np.array([part[i] for i in range(n)])
    rng = np.random.RandomState(1)
    xs = rng.uniform(-0.1, 0.1, n)
    ys = tl.copy()
    for _ in range(900):
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                dx, dy = xs[i] - xs[j], ys[i] - ys[j]
                d = np.hypot(dx, dy)
                mind = radii[i] + radii[j] + 0.09
                if d < mind:
                    if abs(dx) < 1e-6:
                        dx = rng.uniform(-1, 1)
                    sh = (mind - d) / 2 + 1e-3
                    s = 1.0 if dx >= 0 else -1.0
                    xs[i] += s * sh
                    xs[j] -= s * sh
                    moved = True
        if not moved:
            break
    xs -= xs.mean()
    return xs, ys, comm, G


def render(code, ax):
    codes, Z, x = load_country(code)
    n = len(codes)
    tl = trophic_levels_io(Z, x)
    self_flow = np.diag(Z).copy()
    radii = 0.035 + 0.13 * np.sqrt(x / x.max())         # node radius (data units)
    VSCALE = 3.0                                         # stretch trophic axis
    xs, ys, comm, G = layout(Z, tl * VSCALE, radii)

    A = Z.copy()
    np.fill_diagonal(A, 0)
    wmax = A.max()
    # faint web: every non-trivial flow
    floor = 0.004 * wmax
    for i in range(n):
        for j in range(n):
            if A[i, j] > floor:
                ax.plot([xs[i], xs[j]], [ys[i], ys[j]], color=GREEN,
                        lw=0.15 + 1.3 * A[i, j] / wmax, alpha=0.12, zorder=1)
    # heavy flows as arrows
    flat = [(A[i, j], i, j) for i in range(n) for j in range(n) if A[i, j] > 0]
    flat.sort(reverse=True)
    for w, i, j in flat[:28]:
        ar = FancyArrowPatch((xs[i], ys[i]), (xs[j], ys[j]),
                             connectionstyle="arc3,rad=0.12",
                             arrowstyle="-|>", mutation_scale=8 + 16 * w / wmax,
                             lw=0.6 + 5.0 * w / wmax, color=GREEN, alpha=0.55,
                             shrinkA=2, shrinkB=2, zorder=2)
        ax.add_patch(ar)
    # nodes
    for i in range(n):
        cc = COMM_PALETTE[comm[i] % len(COMM_PALETTE)]
        ax.add_patch(Circle((xs[i], ys[i]), radii[i], facecolor=GREEN,
                            edgecolor=cc, lw=3.2, zorder=5))
        fr = np.sqrt(min(self_flow[i] / x[i], 1.0)) if x[i] > 0 else 0
        if fr > 0:
            ax.add_patch(Circle((xs[i], ys[i]), radii[i] * fr, facecolor=PINK,
                                edgecolor="none", zorder=6))
    # labels — put them on the outward side to reduce collisions
    midx = np.median(xs)
    order = np.argsort(-x)
    for rank, i in enumerate(order):
        fs = 10 if rank < 8 else (8.3 if rank < 20 else 6.8)
        if xs[i] <= midx:
            tx, ha = xs[i] - radii[i] - 0.05, "right"
        else:
            tx, ha = xs[i] + radii[i] + 0.05, "left"
        ax.text(tx, ys[i], label(codes[i]), fontsize=fs,
                va="center", ha=ha, color="#222", zorder=7,
                path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])

    ax.set_aspect("equal")
    ax.set_xlim(xs.min() - 2.4, xs.max() + 2.4)
    ax.set_ylim(min(ys) - 0.5, max(ys) + 0.55)
    ax.set_xticks([])
    # y ticks labelled in true trophic level (undo the VSCALE stretch)
    tmin, tmax = np.floor(tl.min() * 4) / 4, np.ceil(tl.max() * 4) / 4
    ticks = np.arange(tmin, tmax + 0.01, 0.25)
    ax.set_yticks(ticks * VSCALE)
    ax.set_yticklabels([f"{t:.2f}" for t in ticks], fontsize=8)
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#bbb")
    ax.set_ylabel("Trophic level  →  deeper in the supply chain", fontsize=10)
    depth = float(np.sum(x / x.sum() * tl))
    ax.set_title(f"{name_of.get(code, code)}   ·   mean trophic depth {depth:.2f}",
                 fontsize=14, weight="bold", loc="left")
    return x


def size_legend(ax, xmax):
    """Anatomy + size/arrow key, drawn in axis-fraction space."""
    ax.text(0.5, 0.97, "node = sector", transform=ax.transAxes, fontsize=8.5,
            ha="center", color="#555")
    # anatomy glyph
    import matplotlib.patches as mp
    tf = ax.transAxes
    ax.add_patch(mp.Circle((0.12, 0.92), 0.018, facecolor=GREEN, edgecolor="#888",
                           lw=2, transform=tf, zorder=10, clip_on=False))
    ax.add_patch(mp.Circle((0.12, 0.92), 0.009, facecolor=PINK, edgecolor="none",
                           transform=tf, zorder=11, clip_on=False))


def main():
    codes = ARGS if ARGS else ["DEU", "SAU"]
    fig, axes = plt.subplots(len(codes), 1, figsize=(19, 7.6 * len(codes)))
    if len(codes) == 1:
        axes = [axes]
    xs_all = [render(c, ax) for c, ax in zip(codes, axes)]

    # shared legend on the first axis (data is in millions USD -> $ scale)
    ax = axes[0]
    leg = ("Node size = gross output    inner pink = self-flow   outer green = throughflow\n"
           "Ring colour = production community (Louvain)    arrows = largest inter-sector flows")
    fig.text(0.5, 0.045, leg, ha="center", fontsize=10, color="#444")
    fig.text(0.5, 0.012,
             "Source: OECD ICIO 2023 edition, year 2019 (values in million USD). "
             "Trophic level: McNerney et al. (PNAS 2022). Communities: Louvain.",
             ha="center", fontsize=8, color="#777")
    fig.suptitle("Trophic structure as a production network",
                 fontsize=17, weight="bold", y=0.98)
    fig.tight_layout(rect=[0, 0.06, 1, 0.96])
    out = "figures/8_network_" + "_".join(codes) + ".png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print("saved", out)


def render_single(code, outdir="figures/networks"):
    import os
    os.makedirs(outdir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 11))
    render(code, ax)
    leg = ("Node size = gross output    inner pink = self-flow   outer green = throughflow\n"
           "Ring colour = production community (Louvain)    arrows = largest inter-sector flows")
    fig.text(0.5, 0.045, leg, ha="center", fontsize=9.5, color="#444")
    fig.text(0.5, 0.013,
             "Source: OECD ICIO 2023 edition, year 2019 (values in million USD). "
             "Trophic level: McNerney et al. (PNAS 2022). Communities: Louvain.",
             ha="center", fontsize=8, color="#777")
    fig.suptitle("Trophic structure as a production network",
                 fontsize=16, weight="bold", y=0.98)
    fig.tight_layout(rect=[0, 0.06, 1, 0.96])
    out = f"{outdir}/{code}.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    if "--all" in sys.argv:
        for c, _, _ in COUNTRIES:
            render_single(c)
    else:
        main()
