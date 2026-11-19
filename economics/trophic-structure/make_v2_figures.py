"""v2 figures -> figures/9..12 ("does it hold?").

Needs: icio_country_year.csv, wiod_country_year.csv, pwt_growth.csv,
       robustness_results.csv, price_test_sample.csv
Palette checked with a colour-vision validator: mustard / blue / brick pass CVD
and normal-vision separation; mustard is low-contrast on white, so every mustard
mark is direct-labelled.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from countries import COUNTRIES

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#888", "xtick.color": "#444", "ytick.color": "#444",
    "figure.dpi": 150})
MUST, BLUE, BRICK = "#c9a227", "#2b6cb0", "#c1572d"
GREY, INK, MUTED = "#c8c8c8", "#222222", "#666666"
name_of = {c: n for c, n, _ in COUNTRIES}
CONVERGERS = {"CHN", "VNM", "CZE", "EST", "HUN", "LVA", "LTU", "POL", "SVK", "SVN",
              "CYP", "MLT", "BGR", "ROU", "HRV"}

icio = pd.read_csv("icio_country_year.csv")
wiod = pd.read_csv("wiod_country_year.csv")
pwt = pd.read_csv("pwt_growth.csv").set_index(["code", "year"])
res = pd.read_csv("robustness_results.csv")


def footer(fig, text):
    fig.text(0.01, 0.005, text, ha="left", fontsize=7.5, color="#777")


def growth(code, y0, y1):
    try:
        return 100 * (pwt.loc[(code, y1), "log_gdp_hour"] - pwt.loc[(code, y0), "log_gdp_hour"]) / (y1 - y0)
    except KeyError:
        return np.nan


# === 9. Same data, two definitions: the ranking reshuffles ====================
d = icio[icio.year == 2019].copy()
d["r_dom"] = d.domestic_depth.rank(ascending=False)
d["r_far"] = d.farmer_depth.rank(ascending=False)
movers = {"IRL", "LUX", "SGP", "AUS", "ZAF", "USA", "VNM", "CHN", "DEU", "SAU"}
fig, ax = plt.subplots(figsize=(8.5, 9.5))
for r in d.itertuples():
    hot = r.code in movers
    up = r.r_far < r.r_dom
    same = r.r_far == r.r_dom
    col = ("#555555" if same else MUST if up else BLUE) if hot else GREY
    ax.plot([0, 1], [r.r_dom, r.r_far], color=col, lw=2.2 if hot else 1, zorder=3 if hot else 1)
    for x, rk, ha, dx in [(0, r.r_dom, "right", -0.03), (1, r.r_far, "left", 0.03)]:
        ax.scatter([x], [rk], s=28 if hot else 12, color=col, zorder=4,
                   edgecolor="white", linewidth=1.5)
        ax.text(x + dx, rk, f"{int(rk)}  {name_of[r.code]}" if x == 1 else f"{name_of[r.code]}  {int(rk)}",
                ha=ha, va="center", fontsize=8.8 if hot else 7.8,
                color=INK if hot else MUTED, weight="bold" if hot else "normal")
ax.set_ylim(30.8, 0.2)
ax.set_xlim(-0.55, 1.55)
ax.axis("off")
ax.text(0, -0.4, "v1: domestic chains only\n(output-weighted)", ha="center", fontsize=10, weight="bold")
ax.text(1, -0.4, "Farmer's definition: global chains\n(final-demand-weighted)", ha="center", fontsize=10, weight="bold")
fig.suptitle("Same data, two definitions of 'depth': the ranking reshuffles",
             x=0.02, ha="left", weight="bold", fontsize=13)
fig.text(0.02, 0.935, "Rank of 30 economies by production-chain depth, 2019. Rank correlation "
         f"between the two: {d[['r_dom', 'r_far']].corr('spearman').iloc[0, 1]:.2f}. "
         "Mustard = rises under Farmer's measure, blue = falls, dark grey = unchanged.", fontsize=8.8, color=MUTED)
footer(fig, "Source: OECD ICIO 2023 ed. Measures: McNerney, Savoie, Caravelli, Carvalho & Farmer (PNAS 2022).")
fig.tight_layout(rect=[0, 0.02, 1, 0.92])
fig.savefig("figures/9_measure_rerank.png", bbox_inches="tight")
plt.close(fig)

# === 10. The replication: two datasets, two decades ===========================
panels = [("OECD ICIO: depth in 2011 vs growth 2011–2019", icio, 2011, 2019),
          ("WIOD: depth in 2000 vs growth 2000–2019", wiod, 2000, 2019)]
fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), sharey=True)
for ax, (title, panel, y0, y1) in zip(axes, panels):
    s = panel[panel.year == y0].copy()
    s["g"] = [growth(c, y0, y1) for c in s.code]
    s = s.dropna(subset=["g"])
    conv = s.code.isin(CONVERGERS)
    ax.scatter(s.farmer_depth[~conv], s.g[~conv], s=46, color=BLUE,
               edgecolor="white", linewidth=1.5, zorder=3, label="other economies")
    ax.scatter(s.farmer_depth[conv], s.g[conv], s=46, color=BRICK, marker="D",
               edgecolor="white", linewidth=1.5, zorder=3,
               label="fast convergers (China, Vietnam, EU entrants since 2004)")
    xs = np.linspace(s.farmer_depth.min(), s.farmer_depth.max(), 50)
    b1, b0 = np.polyfit(s.farmer_depth, s.g, 1)
    ax.plot(xs, b0 + b1 * xs, color=MUST, lw=2.2, zorder=2)
    c1, c0 = np.polyfit(s.farmer_depth[~conv], s.g[~conv], 1)
    ax.plot(xs, c0 + c1 * xs, color=MUST, lw=1.6, ls=(0, (4, 3)), zorder=2)
    ax.text(xs[-1], b0 + b1 * xs[-1], "  all", va="center", fontsize=8.5, color=INK)
    ax.text(xs[-1], c0 + c1 * xs[-1], "  without\n  convergers", va="center", fontsize=8.5, color=INK)
    r_all = np.corrcoef(s.farmer_depth, s.g)[0, 1]
    r_ex = np.corrcoef(s.farmer_depth[~conv], s.g[~conv])[0, 1]
    ax.text(0.02, 0.97, f"r = {r_all:+.2f} (n = {len(s)})\nwithout convergers r = {r_ex:+.2f} (n = {int((~conv).sum())})",
            transform=ax.transAxes, va="top", fontsize=9, color=INK)
    lab = s.sort_values("g").code.tolist()
    for c in set(lab[-4:] + lab[:2] + s.nlargest(3, "farmer_depth").code.tolist() + ["USA", "DEU", "IRL"]):
        if c in set(s.code):
            r = s[s.code == c].iloc[0]
            ax.annotate(name_of.get(c, c), (r.farmer_depth, r.g), xytext=(5, 4),
                        textcoords="offset points", fontsize=8, color=MUTED)
    ax.axhline(0, color="#e2e2e2", lw=1, zorder=0)
    ax.set_title(title, loc="left", fontsize=10.5, weight="bold")
    ax.set_xlabel("Average production-chain length (Farmer's L̄)")
axes[0].set_ylabel("Real GDP per hour worked, average growth (% a year)")
fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=2, fontsize=8.5,
           frameon=False, bbox_to_anchor=(0.5, 0.025))
fig.suptitle("Longer production chains, faster productivity growth: the pattern replicates",
             x=0.01, ha="left", weight="bold", fontsize=13.5)
fig.text(0.01, 0.905, "Two independent input-output databases, different decades. Dashed line: without the fast "
         "convergers. The raw slope flattens, but once catch-up growth is controlled for\nthe effect is "
         "about as large as in the full sample, though with fewer countries only borderline significant "
         "(p ≈ 0.05–0.09; figure 11).", fontsize=9, color=MUTED, va="top")
footer(fig, "Sources: OECD ICIO 2023 ed.; WIOD 2016 release (Timmer et al.); Penn World Table 11.0 "
       "(GDP per hour). Method: McNerney et al. (PNAS 2022). The paper reports r = 0.53 on WIOD, 1995–2009.")
fig.tight_layout(rect=[0, 0.065, 1, 0.86])
fig.savefig("figures/10_replication.png", bbox_inches="tight")
plt.close(fig)

# === 11. Does it hold? every test on one scale ================================
F = res.measure.str.startswith("Farmer")
rows = [
    ("Across countries", None),
    ("ICIO 2011→2019, catch-up control", (res.dataset == "ICIO") & res.spec.eq("2011->2019 + catch-up") & F),
    ("ICIO 2011→2023 (incl. COVID)", (res.dataset == "ICIO") & res.spec.eq("2011->2023 + catch-up") & F),
    ("WIOD 2000→2014", (res.dataset == "WIOD") & res.spec.eq("2000->2014 + catch-up") & F),
    ("WIOD 2000→2019", (res.dataset == "WIOD") & res.spec.eq("2000->2019 + catch-up") & F),
    ("WIOD 2000→2023", (res.dataset == "WIOD") & res.spec.eq("2000->2023 + catch-up") & F),
    ("ICIO + import-intensity control, per capita", (res.dataset == "ICIO") & res.spec.eq("2011->2019 + catch-up + import int., per-capita") & F),
    ("WIOD + import-intensity control, per capita", (res.dataset == "WIOD") & res.spec.eq("2000->2019 + catch-up + import int., per-capita") & F),
    ("ICIO without fast convergers", (res.dataset == "ICIO") & res.spec.eq("2011->2019 + catch-up, excl. fast convergers") & F),
    ("WIOD without fast convergers", (res.dataset == "WIOD") & res.spec.eq("2000->2019 + catch-up, excl. fast convergers") & F),
    ("Pooled 4–5-year windows", None),
    ("WIOD, 3 windows, period effects", (res.dataset == "WIOD") & res.spec.str.startswith("pooled") & F),
    ("ICIO, 2 windows, period effects", (res.dataset == "ICIO") & res.spec.str.startswith("pooled") & F),
    ("Same country over time", None),
    ("WIOD, within-country", (res.dataset == "WIOD") & res.spec.str.startswith("within") & F),
    ("ICIO, within-country", (res.dataset == "ICIO") & res.spec.str.startswith("within") & F),
    ("WIOD, deepening → next 3 years", (res.dataset == "WIOD") & res.spec.str.contains("momentum") & F),
    ("ICIO, deepening → next 3 years", (res.dataset == "ICIO") & res.spec.str.contains("momentum") & F),
    ("v1 result: ICIO domestic deepening (in sample)", (res.dataset == "ICIO") & res.spec.str.contains("momentum") & ~F & res.test.str.startswith("C")),
    ("v1 result re-run on WIOD (out of sample)", (res.dataset == "WIOD") & res.spec.str.contains("momentum") & ~F & res.test.str.startswith("C")),
]
fig, ax = plt.subplots(figsize=(10, 9.5))
y = 0
ticks, labels, heads = [], [], []
for lab, mask in rows:
    if mask is None:
        y += 0.5
        ticks.append(y)
        labels.append(lab)
        heads.append(len(ticks) - 1)
        y += 1
        continue
    r = res[mask].iloc[0]
    se = abs(r.beta_sd / r.t)
    sig = r.p_resample < 0.05
    col = MUST if sig else BLUE
    ax.plot([r.beta_sd - 1.96 * se, r.beta_sd + 1.96 * se], [y, y], color=col, lw=2.2,
            solid_capstyle="round", zorder=2)
    ax.scatter([r.beta_sd], [y], s=60, color=col if sig else "white", edgecolor=col,
               linewidth=2, zorder=3)
    ax.text(2.95, y, f"p = {r.p_resample:.3f}" if r.p_resample >= 0.001 else "p < 0.001",
            fontsize=8.5, color=INK if sig else MUTED, va="center", ha="left")
    ticks.append(y)
    labels.append(lab)
    y += 1
ax.axvline(0, color="#999", lw=1, zorder=1)
ax.set_yticks(ticks, labels, fontsize=9)
for i in heads:
    t = ax.get_yticklabels()[i]
    t.set_weight("bold")
    t.set_fontsize(10)
    t.set_color(INK)
ax.tick_params(axis="y", length=0)
ax.set_ylim(y - 0.4, -0.2)
ax.set_xlim(-1.6, 3.6)
ax.grid(axis="x", color="#eeeeee", lw=0.8, zorder=0)
ax.set_xlabel("Extra growth of GDP per hour (percentage points a year)\n"
              "per 1 SD of chain length (or of its change)")
ax.spines["left"].set_visible(False)
fig.suptitle("Does it hold? Yes across countries, not (yet) within them",
             x=0.01, ha="left", weight="bold", fontsize=13.5)
fig.text(0.01, 0.945, "Each row is one test of Farmer's claim with his measure. Lines are 95% intervals (analytic).\n"
         "Filled mustard = significant at 5% by resampling (permutation / wild-cluster bootstrap, the p shown); hollow blue = not.",
         fontsize=8.8, color=MUTED, va="top")
footer(fig, "Sources: OECD ICIO 2023 ed.; WIOD 2016; Penn World Table 11.0. Cross-country rows control for "
       "initial productivity; within-country rows use country fixed effects.\nScript: robustness_tests.py "
       "-> robustness_results.csv.")
fig.tight_layout(rect=[0, 0.04, 1, 0.9])
fig.savefig("figures/11_does_it_hold.png", bbox_inches="tight")
plt.close(fig)

# === 12. The mechanism: price declines along the chain ========================
p = pd.read_csv("price_test_sample.csv")
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.6), sharey=True)
for ax, (title, groups, note) in zip(axes, [
        ("Comparing industries within a country", ["code"],
         "Longer-chain industries saw their prices fall faster\nrelative to wages"),
        ("Comparing the same industry across countries", ["code", "sector"],
         "Within an industry, chain length\nexplains nothing")]):
    q = p.copy()
    for _ in range(25):   # alternating projections = demean by all listed groups
        for gcol in groups:
            q["rpc"] -= q.groupby(gcol).rpc.transform("mean")
            q["L_global"] -= q.groupby(gcol).L_global.transform("mean")
    q["bin"] = pd.qcut(q.L_global, 20, labels=False)
    b = q.groupby("bin")[["L_global", "rpc"]].mean()
    ax.scatter(q.L_global, q.rpc, s=5, color=GREY, alpha=0.35, linewidths=0, zorder=1)
    ax.scatter(b.L_global, b.rpc, s=46, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3,
               label="average of each 5% bin")
    k1, k0 = np.polyfit(q.L_global, q.rpc, 1)
    xs = np.linspace(b.L_global.min(), b.L_global.max(), 20)
    ax.plot(xs, k0 + k1 * xs, color=MUST, lw=2.2, zorder=2)
    ax.text(xs[-1], k0 + k1 * xs[-1], f"  slope {k1:+.2f}", fontsize=8.5, color=INK, va="center")
    ax.axhline(0, color="#e2e2e2", lw=1, zorder=0)
    ax.set_ylim(-3.2, 3.2)
    ax.set_xlim(-0.9, 1.0)
    ax.set_title(title, loc="left", fontsize=10.5, weight="bold")
    ax.text(0.02, 0.97, note, transform=ax.transAxes, va="top", fontsize=9, color=INK)
    ax.set_xlabel("Industry output multiplier, 2000 (deviation from group average)")
axes[0].set_ylabel("Price change relative to wages, 2000–2014\n(% a year, deviation from group average)")
axes[0].legend(loc="lower left", fontsize=8.3, frameon=False)
fig.suptitle("The mechanism: do prices fall faster at the end of long chains?",
             x=0.01, ha="left", weight="bold", fontsize=13.5)
fig.text(0.01, 0.905, f"{len(p):,} industries in {p.code.nunique()} economies. Farmer's first prediction holds between "
         "industry types, but not for the same industry in different countries.", fontsize=9, color=MUTED)
footer(fig, "Source: WIOD 2016 release, tables + Socio-Economic Accounts (gross-output prices, wages). "
       "Price changes winsorised at 1%/99%. Axes clipped to the central range.")
fig.tight_layout(rect=[0, 0.025, 1, 0.89])
fig.savefig("figures/12_price_mechanism.png", bbox_inches="tight")
plt.close(fig)
print("figures 9-12 written")
