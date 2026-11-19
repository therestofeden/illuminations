"""
Farmer-style production networks from OECD ICIO, showing both halves of every
chain: the steps done at home and the steps done abroad.

For one country, each sector is a node:
  height          total production stages behind one unit of the sector's output,
                  counting steps abroad (output multiplier on the WORLD table,
                  McNerney et al. 2022). Higher = more stages behind it.
  hollow marker   the same count with the chain cut at the border (home stages
                  only). The dashed line between the two = steps done abroad.
  fill colour     share of the sector's intermediate inputs that are imported
                  (light = mostly domestic, dark = mostly imported).
  size            gross output.
  ring colour     production community (Louvain on domestic flows); colours have
                  no fixed meaning.
  pink centre     share of output the sector buys from itself.
Green arrows are the largest flows between domestic sectors; blue arrows the
largest imports, drawn from a "Rest of world" node. Left-right position only
avoids overlaps and carries no information.

Usage:
  python3 network_viz.py DEU SAU        # contrast pair -> figures/8_network_DEU_SAU.png
  python3 network_viz.py --all          # all 30 -> figures/networks/<CODE>.png
  (optional first argument: path to an ICIO csv; default icio2023/2019_SML.csv)
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.patheffects as pe
import networkx as nx
import community as community_louvain
from measures import multipliers
from isic_labels import label
from countries import COUNTRIES

CSV = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".csv") else "icio2023/2019_SML.csv"
ARGS = [a for a in sys.argv[1:] if not a.endswith(".csv") and not a.startswith("--")]
GREEN, PINK, IMPORT_BLUE, GHOST = "#3aa86b", "#e76b86", "#2b6cb0", "#555555"
COMM_PALETTE = ["#c9a227", "#7a5c3e", "#3d6b7d", "#5a7d5a", "#c1672d",
                "#8a5fa3", "#cf4f4f", "#4f9d9d", "#9d8b4f"]
# single-hue sequential ramp for import share (light -> dark)
IMPORT_CMAP = LinearSegmentedColormap.from_list("imports", ["#eef4fa", "#9ec3e6", "#2b6cb0", "#0b2f5e"])
FD = ("HFCE", "NPISH", "GGFC", "GFCF", "INVNT", "DPABR")
TOTALS = {"OUT", "VA", "TLS"}
name_of = {c: n for c, n, _ in COUNTRIES}
_WORLD = {}


def world():
    """Load the world table once: sectors, flows, output, final demand, global L."""
    if not _WORLD:
        df = pd.read_csv(CSV, index_col=0)
        df.index = df.index.astype(str)
        sectors = [c for c in df.columns if c in df.index and c not in TOTALS and "_" in c]
        fd_cols = [c for c in df.columns if c.split("_")[-1] in FD]
        Z = df.loc[sectors, sectors].to_numpy(float)
        x = df.loc["OUT", sectors].to_numpy(float)
        y = df.loc[sectors, fd_cols].to_numpy(float).sum(axis=1)
        _WORLD.update(sectors=np.array(sectors), Z=Z, x=x, y=y, L=multipliers(Z, x),
                      prefix=np.array([s.split("_", 1)[0] for s in sectors]))
    return _WORLD


def load_country(code):
    W = world()
    k_all = np.flatnonzero(W["prefix"] == code)
    Zd = W["Z"][np.ix_(k_all, k_all)]
    xd = W["x"][k_all]
    Ld = multipliers(Zd, xd)                        # home stages only
    foreign = np.flatnonzero(W["prefix"] != code)
    imp = W["Z"][np.ix_(foreign, k_all)]            # imported intermediates, by supplier
    imp_tot = imp.sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        imp_share = np.where(Zd.sum(axis=0) + imp_tot > 0, imp_tot / (Zd.sum(axis=0) + imp_tot), 0)
    # chain-length summary for the title (final-demand weights, as in the paper)
    yc = np.clip(W["y"][k_all], 0, None)
    th = yc / yc.sum()
    Lg_all = W["L"][k_all]
    summary = dict(total=float(th @ Lg_all), home=float(th @ Ld))
    summary["abroad"] = summary["total"] - summary["home"]
    # level of what is imported: flow-weighted global level of foreign suppliers
    imp_level = float((imp.sum(axis=1) @ W["L"][foreign]) / imp.sum()) if imp.sum() > 0 else 1.0
    # keep sectors with output that are connected to the domestic network
    off = Zd.copy()
    np.fill_diagonal(off, 0)
    keep = (xd > 0) & ((off.sum(0) + off.sum(1)) > 0)
    codes = [s.split("_", 1)[1] for s in W["sectors"][k_all][keep]]
    return dict(codes=codes, Z=Zd[np.ix_(keep, keep)], x=xd[keep], L_home=Ld[keep],
                L_global=Lg_all[keep], imp_share=imp_share[keep], imp_tot=imp_tot[keep],
                imp_level=imp_level, summary=summary)


def layout(Z, tl, radii):
    """Beeswarm: y = exact level, x = spread to remove overlaps (no meaning)."""
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
                mind = radii[i] + radii[j] + 0.22
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
    return xs, ys, comm


VSCALE = 2.2      # stretch the vertical axis so levels are readable


def render(code, ax):
    c = load_country(code)
    Z, x, codes = c["Z"], c["x"], c["codes"]
    n = len(codes)
    radii = 0.03 + 0.11 * np.sqrt(x / x.max())
    ys_home = c["L_home"] * VSCALE
    xs, ys, comm = layout(Z, c["L_global"] * VSCALE, radii)

    # rest-of-world node: at the level of what is imported, left of the network
    row_x = xs.min() - 1.3
    row_y = c["imp_level"] * VSCALE
    row_r = 0.03 + 0.11 * np.sqrt(min(c["imp_tot"].sum() / x.max(), 4.0))

    A = Z.copy()
    np.fill_diagonal(A, 0)
    wmax = max(A.max(), c["imp_tot"].max())
    floor = 0.004 * wmax
    for i in range(n):
        for j in range(n):
            if A[i, j] > floor:
                ax.plot([xs[i], xs[j]], [ys[i], ys[j]], color=GREEN,
                        lw=0.15 + 1.3 * A[i, j] / wmax, alpha=0.12, zorder=1)
    flat = sorted(((A[i, j], i, j) for i in range(n) for j in range(n) if A[i, j] > 0), reverse=True)
    for w, i, j in flat[:24]:
        ax.add_patch(FancyArrowPatch((xs[i], ys[i]), (xs[j], ys[j]), connectionstyle="arc3,rad=0.12",
                                     arrowstyle="-|>", mutation_scale=8 + 16 * w / wmax,
                                     lw=0.6 + 5.0 * w / wmax, color=GREEN, alpha=0.55,
                                     shrinkA=2, shrinkB=2, zorder=2))
    for j in np.argsort(-c["imp_tot"])[:8]:          # largest imports
        w = c["imp_tot"][j]
        ax.add_patch(FancyArrowPatch((row_x, row_y), (xs[j], ys[j]), connectionstyle="arc3,rad=-0.15",
                                     arrowstyle="-|>", mutation_scale=8 + 16 * w / wmax,
                                     lw=0.6 + 5.0 * w / wmax, color=IMPORT_BLUE, alpha=0.45,
                                     shrinkA=10, shrinkB=2, zorder=2))
    # home-only level: hollow marker + dashed stem up to the global level
    for i in range(n):
        if ys[i] - ys_home[i] > 0.02:
            ax.plot([xs[i], xs[i]], [ys_home[i], ys[i] - radii[i]], color="#9a9a9a", lw=0.7,
                    ls=(0, (2, 2)), zorder=3)
        ax.add_patch(Circle((xs[i], ys_home[i]), 0.022, facecolor="white", edgecolor=GHOST,
                            lw=0.9, zorder=4))
    norm = Normalize(0, 0.6)
    for i in range(n):
        cc = COMM_PALETTE[comm[i] % len(COMM_PALETTE)]
        ax.add_patch(Circle((xs[i], ys[i]), radii[i], facecolor=IMPORT_CMAP(norm(c["imp_share"][i])),
                            edgecolor=cc, lw=3.2, zorder=5))
        fr = np.sqrt(min(np.diag(Z)[i] / x[i], 1.0)) if x[i] > 0 else 0
        if fr > 0:
            ax.add_patch(Circle((xs[i], ys[i]), radii[i] * fr, facecolor=PINK, edgecolor="none", zorder=6))
    ax.add_patch(Circle((row_x, row_y), row_r, facecolor="#d9d9d9", edgecolor=IMPORT_BLUE, lw=2.5,
                        ls=(0, (3, 2)), zorder=5))
    ax.text(row_x, row_y - row_r - 0.12, "Rest of world\n(imported inputs)", ha="center", va="top",
            fontsize=9, color="#222", zorder=7,
            path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])
    midx = np.median(xs)
    for rank, i in enumerate(np.argsort(-x)):
        fs = 10 if rank < 8 else (8.3 if rank < 20 else 6.8)
        tx, ha = ((xs[i] - radii[i] - 0.05, "right") if xs[i] <= midx
                  else (xs[i] + radii[i] + 0.05, "left"))
        ax.text(tx, ys[i], label(codes[i]), fontsize=fs, va="center", ha=ha, color="#222", zorder=7,
                path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])

    ax.set_aspect("equal")
    ax.set_xlim(row_x - 1.0, xs.max() + 1.6)
    lo = min(ys_home.min(), row_y) - 0.5
    ax.set_ylim(lo, max(ys) + 0.55)
    ax.set_xticks([])
    tmin, tmax = np.floor(lo / VSCALE * 4) / 4, np.ceil(max(ys) / VSCALE * 4) / 4
    ticks = np.arange(max(tmin, 1.0), tmax + 0.01, 0.25)
    ax.set_yticks(ticks * VSCALE)
    ax.set_yticklabels([f"{t:.2f}" for t in ticks], fontsize=8)
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#bbb")
    ax.set_ylabel("Production stages behind each unit of output  (higher = longer chain)", fontsize=10)
    s = c["summary"]
    ax.set_title(f"{name_of.get(code, code)}   ·   chain length {s['total']:.2f}  "
                 f"=  {s['home']:.2f} at home  +  {s['abroad']:.2f} abroad",
                 fontsize=13.5, weight="bold", loc="left")
    return ax


def legend(fig, y0=0.065):
    txt = ("Height = production stages behind the sector, counting steps abroad   ·   hollow dot = stages "
           "at home only (dashed line = steps abroad)\n"
           "Size = gross output   ·   fill = share of inputs imported   ·   ring = production community "
           "(colours have no fixed meaning)   ·   pink = sector's purchases from itself\n"
           "Green arrows = largest flows between domestic sectors   ·   blue arrows = largest imports   ·   "
           "left-right position carries no information")
    fig.text(0.5, y0, txt, ha="center", va="top", fontsize=8.8, color="#444", linespacing=1.6)
    cax = fig.add_axes([0.80, 0.905, 0.15, 0.012])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(0, 0.6), cmap=IMPORT_CMAP), cax=cax,
                      orientation="horizontal")
    cb.set_ticks([0, 0.2, 0.4, 0.6])
    cb.set_ticklabels(["0%", "20%", "40%", "60%+"])
    cb.ax.tick_params(labelsize=7.5, length=2)
    cb.outline.set_visible(False)
    cax.set_title("fill: share of inputs imported", fontsize=8, color="#444", pad=3)
    fig.text(0.5, 0.0, "Source: OECD ICIO 2023 edition, year 2019. Production stages = output multipliers "
             "(McNerney et al., PNAS 2022) on the world table and on the country's own block. "
             "Communities: Louvain.", ha="center", fontsize=7.5, color="#777")


def main():
    codes = ARGS if ARGS else ["DEU", "SAU"]
    fig, axes = plt.subplots(len(codes), 1, figsize=(19, 8.2 * len(codes)))
    axes = np.atleast_1d(axes)
    for code, ax in zip(codes, axes):
        render(code, ax)
    fig.suptitle("Production networks: how long the chains are, and how much of them happens at home",
                 fontsize=16, weight="bold", y=0.985)
    fig.tight_layout(rect=[0, 0.075, 1, 0.95])
    legend(fig, y0=0.06)
    out = "figures/8_network_" + "_".join(codes) + ".png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print("saved", out)


def render_single(code, outdir="figures/networks"):
    os.makedirs(outdir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(15, 11))
    render(code, ax)
    fig.suptitle("Production network: how long the chains are, and how much happens at home",
                 fontsize=14.5, weight="bold", y=0.985)
    fig.tight_layout(rect=[0, 0.11, 1, 0.95])
    legend(fig, y0=0.095)
    out = f"{outdir}/{code}.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    if "--all" in sys.argv:
        for code, _, _ in COUNTRIES:
            render_single(code)
    else:
        main()
