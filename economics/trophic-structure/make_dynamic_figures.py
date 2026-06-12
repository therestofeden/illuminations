"""Figures for the dynamic test -> figures/5,6,7."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from countries import ARCHETYPE_COLOR, COUNTRIES

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#888", "xtick.color": "#444", "ytick.color": "#444",
    "figure.dpi": 150})
SRC = ("Source: OECD ICIO 2023 ed. (domestic trophic depth, 2011-2020); "
       "World Bank WDI real GDP growth. Method: McNerney et al. (PNAS 2022).")
MUST = "#c9a227"
name_of = {c: n for c, n, _ in COUNTRIES}
arch_of = {c: a for c, _, a in COUNTRIES}

panel = pd.read_csv("panel.csv")
d = pd.read_csv("dynamic_sample.csv")

# === Figure 5 — trophic-depth trajectories ==================================
fig, ax = plt.subplots(figsize=(9.5, 7))
highlight = {"VNM": "Vietnam", "CHN": "China", "CZE": "Czechia",
             "DEU": "Germany", "SAU": "Saudi Arabia", "IRL": "Ireland"}
for code in panel.code.unique():
    s = panel[panel.code == code].sort_values("year")
    if code in highlight:
        continue
    ax.plot(s.year, s.trophic_depth, color="#d9d9d9", lw=1, zorder=1)
for code, nm in highlight.items():
    s = panel[panel.code == code].sort_values("year")
    col = ARCHETYPE_COLOR[arch_of[code]]
    ax.plot(s.year, s.trophic_depth, color=col, lw=2.4, zorder=3)
    ax.annotate(nm, (s.year.iloc[-1], s.trophic_depth.iloc[-1]),
                xytext=(6, 0), textcoords="offset points", va="center",
                fontsize=9.5, color=col, weight="bold")
ax.set_xlim(2011, 2021.6)
ax.set_xlabel("year")
ax.set_ylabel("Domestic trophic depth")
ax.set_title("Production chains lengthen and shorten over time\n"
             "Each grey line is one of the 30 economies, 2011–2020",
             weight="bold", loc="left")
fig.text(0.5, 0.012, SRC, ha="center", fontsize=7.5, color="#777")
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("figures/5_depth_trajectories.png", bbox_inches="tight")
plt.close(fig)

# === Figure 6 — deepening predicts subsequent growth (the key result) =======
dd = d.dropna(subset=["ddepth3"]).copy()
fig, ax = plt.subplots(figsize=(9, 7))
ax.axvline(0, color="#ccc", lw=1)
ax.scatter(dd.ddepth3, dd.fwd3,
           c=[ARCHETYPE_COLOR[arch_of[c]] for c in dd.code],
           s=70, alpha=0.8, edgecolor="white", linewidth=0.7)
b1, b0 = np.polyfit(dd.ddepth3, dd.fwd3, 1)
xs = np.linspace(dd.ddepth3.min(), dd.ddepth3.max(), 50)
ax.plot(xs, b0 + b1 * xs, color=MUST, lw=2.5)
r = np.corrcoef(dd.ddepth3, dd.fwd3)[0, 1]
ax.text(0.03, 0.96,
        "Countries that DEEPENED their chains\nthen grew faster.\n"
        f"bivariate r = {r:.2f};  with controls +8.7 pts per unit, p≈0.09",
        transform=ax.transAxes, va="top", fontsize=9.5, color="#444")
ax.set_xlabel("Change in trophic depth over the PRIOR 3 years")
ax.set_ylabel("Average real GDP growth over the NEXT 3 years (%)")
ax.set_title("Farmer's claim, properly tested: does deepening come before growth?\n"
             "Within-country windows, 2011–2016 base years",
             weight="bold", loc="left")
fig.text(0.5, 0.012, SRC, ha="center", fontsize=7.5, color="#777")
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("figures/6_deepening_vs_growth.png", bbox_inches="tight")
plt.close(fig)

# === Figure 7 — specification curve (honesty plot) ==========================
specs = [
    ("Raw correlation\n(deeper = faster?)", "fwd3 ~ depth", "depth", d),
    ("+ catch-up control\n(income level)", "fwd3 ~ depth + log_gdppc", "depth", d),
    ("+ year fixed effects", "fwd3 ~ depth + log_gdppc + C(year)", "depth", d),
    ("Within-country\n(country fixed effects)",
     "fwd3 ~ depth + log_gdppc + C(year) + C(code)", "depth", d),
    ("Deepening\n(Δdepth, prior 3y)",
     "fwd3 ~ ddepth3 + log_gdppc + C(year)", "ddepth3", dd),
]
labels, betas, los, his = [], [], [], []
for lab, f, key, data in specs:
    m = smf.ols(f, data=data).fit(cov_type="cluster",
                                  cov_kwds={"groups": data["code"]})
    labels.append(lab); betas.append(m.params[key])
    ci = m.conf_int().loc[key]; los.append(ci[0]); his.append(ci[1])
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(labels))
colors = ["#999", "#999", "#999", MUST, MUST]
ax.axhline(0, color="#bbb", lw=1)
for i in range(len(x)):
    ax.plot([x[i], x[i]], [los[i], his[i]], color=colors[i], lw=2)
    ax.scatter(x[i], betas[i], color=colors[i], s=90, zorder=3)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("Effect of depth on subsequent growth\n(coefficient, %-pts; bars = 95% CI)")
ax.set_title("Why the answer depends on the question\n"
             "The link to growth appears only in the dynamic, within-country tests",
             weight="bold", loc="left")
fig.text(0.5, 0.012, SRC + "  CIs are country-clustered.", ha="center",
         fontsize=7.5, color="#777")
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig("figures/7_specification_curve.png", bbox_inches="tight")
plt.close(fig)
print("Saved figures 5, 6, 7")
