"""
Build the four publication figures from results_country.csv, results_sectors.csv
and gdp_context.csv. Outputs PNGs into figures/.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from countries import ARCHETYPE_COLOR

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#888", "axes.labelcolor": "#222",
    "xtick.color": "#444", "ytick.color": "#444", "figure.dpi": 150,
})
SRC = ("Source: OECD ICIO 2023 edition, year 2019 (CC-licensed). "
       "GDP: World Bank WDI / IMF WEO. Method: McNerney et al. (PNAS 2022); "
       "MacKay, Johnson & Sansom (2020).")
MUSTARD = "#c9a227"
import os
os.makedirs("figures", exist_ok=True)

c = pd.read_csv("results_country.csv")
s = pd.read_csv("results_sectors.csv")
g = pd.read_csv("gdp_context.csv")
c = c.merge(g, on="code")


def caption(fig):
    fig.text(0.5, 0.012, SRC, ha="center", fontsize=7.5, color="#777")


def legend(ax):
    handles = [Line2D([0], [0], marker="o", ls="", mfc=col, mec="none", ms=9, label=a)
               for a, col in ARCHETYPE_COLOR.items()]
    ax.legend(handles=handles, frameon=False, fontsize=8.5,
              loc="lower right", handletextpad=0.2)


# === Figure 1 — ranked trophic depth ========================================
d = c.sort_values("trophic_depth")
fig, ax = plt.subplots(figsize=(9, 9))
ax.barh(d["country"], d["trophic_depth"],
        color=[ARCHETYPE_COLOR[a] for a in d["archetype"]], height=0.7)
for y, (v, n) in enumerate(zip(d["trophic_depth"], d["country"])):
    ax.text(v + 0.012, y, f"{v:.2f}", va="center", fontsize=8.5, color="#333")
ax.set_xlim(1.0, 2.5)
ax.set_xlabel("Trophic depth  (output-weighted mean position in the domestic supply chain)")
ax.set_title("How deep do domestic production chains run?\n"
             "Trophic structure of 30 economies, 2019", weight="bold", loc="left")
ax.margins(y=0.01)
legend(ax)
caption(fig)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("figures/1_depth_ranking.png", bbox_inches="tight")
plt.close(fig)

# === Figure 2 — domestic vs global depth (the offshore gap) ==================
fig, ax = plt.subplots(figsize=(9, 8))
lo, hi = 1.0, 3.2
ax.plot([lo, hi], [lo, hi], color="#bbb", ls="--", lw=1, zorder=0)
ax.text(2.9, 2.78, "self-contained\n(chain is domestic)", color="#999",
        fontsize=8.5, ha="center", rotation=33, va="bottom")
sizes = 60 + 1500 * (c["gdp_usd"] / c["gdp_usd"].max()) ** 0.5
ax.scatter(c["trophic_depth"], c["trophic_depth_global"], s=sizes,
           c=[ARCHETYPE_COLOR[a] for a in c["archetype"]],
           alpha=0.78, edgecolor="white", linewidth=0.7, zorder=3)
label_pts = ["Vietnam", "Ireland", "Luxembourg", "Singapore", "China",
             "United States", "Saudi Arabia", "Germany", "Czechia", "Taiwan", "Mexico"]
for _, r in c.iterrows():
    if r["country"] in label_pts:
        ax.annotate(r["country"], (r["trophic_depth"], r["trophic_depth_global"]),
                    xytext=(5, 4), textcoords="offset points", fontsize=8.5, color="#333")
ax.set_xlabel("Domestic trophic depth  (chain length inside the country)")
ax.set_ylabel("Global trophic depth  (chain length including imported inputs)")
ax.set_title("The offshore gap: whose production chains live abroad?\n"
             "Points far above the line assemble long chains they don't own at home",
             weight="bold", loc="left")
legend(ax)
caption(fig)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("figures/2_offshore_gap.png", bbox_inches="tight")
plt.close(fig)

# === Figure 3 — small-multiple trophic profiles ==============================
show = ["China", "Germany", "Vietnam", "United States",
        "Saudi Arabia", "Ireland", "Singapore", "Czechia"]
bins = np.linspace(1, 3.2, 18)
fig, axes = plt.subplots(2, 4, figsize=(13, 6.4), sharex=True, sharey=True)
for ax, name in zip(axes.ravel(), show):
    sub = s[s.country == name]
    arch = sub["archetype"].iloc[0]
    ax.hist(sub["level_global"], bins=bins, weights=sub["output_share"],
            color=ARCHETYPE_COLOR[arch], edgecolor="white", linewidth=0.4)
    depth = (sub["level_global"] * sub["output_share"]).sum()
    ax.axvline(depth, color="#222", ls="--", lw=1)
    ax.set_title(name, fontsize=10.5)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False, labelleft=False)
for ax in axes[-1]:
    ax.set_xlabel("global trophic level", fontsize=9)
fig.suptitle("Trophic profiles: where each economy's output sits in the global chain\n"
             "(area = share of gross output; dashed line = mean depth)",
             weight="bold", x=0.5, ha="center")
caption(fig)
fig.tight_layout(rect=[0, 0.03, 1, 0.96])
fig.savefig("figures/3_trophic_profiles.png", bbox_inches="tight")
plt.close(fig)

# === Figure 4 — Farmer's claim: depth vs growth (with the convergence caveat)=
fig, ax = plt.subplots(figsize=(9.5, 7.2))
sc = ax.scatter(c["trophic_depth_global"], c["growth_2010_19"],
                s=70 + 0.0035 * c["gdp_pc_ppp"],
                c=[ARCHETYPE_COLOR[a] for a in c["archetype"]],
                alpha=0.8, edgecolor="white", linewidth=0.7)
# OLS fit line (illustrative only)
x, y = c["trophic_depth_global"], c["growth_2010_19"]
b1, b0 = np.polyfit(x, y, 1)
xs = np.linspace(x.min(), x.max(), 50)
ax.plot(xs, b0 + b1 * xs, color=MUSTARD, lw=2)
r = np.corrcoef(x, y)[0, 1]
ax.text(0.03, 0.96, f"slope +{b1:.2f}  ·  r = {r:.2f}\n(illustrative cross-section)",
        transform=ax.transAxes, va="top", fontsize=9, color="#555")
for _, row in c.iterrows():
    if row["country"] in ["China", "Vietnam", "Ireland", "India", "Saudi Arabia",
                          "United States", "Japan", "Luxembourg"]:
        ax.annotate(row["country"], (row["trophic_depth_global"], row["growth_2010_19"]),
                    xytext=(5, 3), textcoords="offset points", fontsize=8.5, color="#333")
ax.set_xlabel("Global trophic depth, 2019")
ax.set_ylabel("Average real GDP growth, 2010–2019 (%)")
ax.set_title("Do deeper chains grow faster? Farmer's claim, tested loosely\n"
             "Bubble size = GDP per capita — note the poorer, deeper economies also "
             "grow via catch-up", weight="bold", loc="left")
legend(ax)
caption(fig)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("figures/4_depth_vs_growth.png", bbox_inches="tight")
plt.close(fig)

print("Saved 4 figures to figures/")
for f in sorted(os.listdir("figures")):
    print(" ", f)
