"""
Pull every number the paper quotes from the result files, so nothing is typed
by hand. Writes:
  paper/numbers.tex          \\newcommand macros used in the text
  paper/tables/*.tex         tables (main results, amplification, forecast,
                             full appendix of estimates)

Run from economics/trophic-structure/:  python3 paper/make_numbers.py
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd())
from robustness_tests import growth          # noqa: E402

OUT = "paper"
os.makedirs(os.path.join(OUT, "tables"), exist_ok=True)
macros = {}


def m(name, value):
    assert name.isalpha(), name
    macros[name] = value


def f2(x):
    return f"{x:.2f}"


def fp(p):
    return r"$<0.001$" if p < 0.001 else f"{p:.3f}"


def fp_text(p):
    """p for running text: 'p < 0.001' or 'p = 0.012'."""
    return r"$p<0.001$" if p < 0.001 else rf"$p={p:.3f}$"


icio = pd.read_csv("icio_country_year.csv")
wiod = pd.read_csv("wiod_country_year.csv")
res = pd.read_csv("robustness_results.csv")
amp = pd.read_csv("amplification_results.csv")
fc = pd.read_csv("forecast_results.csv").set_index("forecast")
far = res.measure.str.startswith("Farmer")
dom = res.measure.str.startswith("v1")


def row(test, dataset, spec, measure_mask, exact=True):
    mask = res.test.str.startswith(test) & (res.dataset == dataset) & measure_mask
    mask &= res.spec.eq(spec) if exact else res.spec.str.contains(spec, regex=False)
    r = res[mask]
    assert len(r) == 1, (test, dataset, spec, len(r))
    return r.iloc[0]


# ---- data coverage -----------------------------------------------------------
m("NIcio", str(icio.code.nunique()))
m("NWiod", str(wiod.code.nunique()))
m("NEstimates", str(len(res)))

# ---- re-ranking ---------------------------------------------------------------
d19 = icio[icio.year == 2019].copy()
d19["rd"] = d19.domestic_depth.rank(ascending=False).astype(int)
d19["rf"] = d19.farmer_depth.rank(ascending=False).astype(int)
m("RankCorr", f2(d19[["rd", "rf"]].corr("spearman").iloc[0, 1]))
r = d19.set_index("code")
for c, nm in [("IRL", "Ireland"), ("LUX", "Luxembourg"), ("USA", "Usa"), ("AUS", "Australia")]:
    m(f"Rank{nm}Dom", str(r.loc[c, "rd"]))
    m(f"Rank{nm}Far", str(r.loc[c, "rf"]))
w19 = icio[icio.year == 2019]
# weights alone (both global): output weights vs final-demand weights
m("SpearWeights", f2(w19.global_depth_outw.corr(w19.farmer_depth, method="spearman")))

# ---- raw correlations (Farmer measure vs GDP per hour growth) ---------------
def raw_r(panel, y0, y1, col="farmer_depth"):
    d = panel[panel.year == y0].copy()
    d["g"] = [growth(c, y0, y1) for c in d.code]
    d = d.dropna(subset=["g"])
    return np.corrcoef(d[col], d.g)[0, 1]


rr = [raw_r(icio, 2011, 2019), raw_r(icio, 2011, 2023), raw_r(wiod, 2000, 2014),
      raw_r(wiod, 2000, 2019), raw_r(wiod, 2000, 2023)]
m("RawRMin", f2(min(rr)))
m("RawRMax", f2(max(rr)))

# ---- A. cross-section ---------------------------------------------------------
catch = [row("A", "ICIO", "2011->2019 + catch-up", far), row("A", "ICIO", "2011->2023 + catch-up", far),
         row("A", "WIOD", "2000->2014 + catch-up", far), row("A", "WIOD", "2000->2019 + catch-up", far),
         row("A", "WIOD", "2000->2023 + catch-up", far)]
m("CatchBetaMin", f2(min(c.beta_sd for c in catch)))
m("CatchBetaMax", f2(max(c.beta_sd for c in catch)))
m("CatchPMax", f"{max(c.p_resample for c in catch):.3f}")
m("CatchLooMin", f2(min(c.loo_min_sd for c in catch)))
dI = row("A", "ICIO", "2011->2019 + catch-up", dom)
m("DomIcioBeta", f2(dI.beta_sd))
m("DomIcioP", fp_text(dI.p_resample))
dW = [row("A", "WIOD", f"2000->{y} + catch-up", dom) for y in (2014, 2019, 2023)]
m("DomWiodBetaMin", f2(min(x.beta_sd for x in dW)))
m("DomWiodBetaMax", f2(max(x.beta_sd for x in dW)))
m("DomWiodPMin", f"{min(x.p_resample for x in dW):.3f}")
m("DomWiodPMax", f"{max(x.p_resample for x in dW):.3f}")
impW = [row("A", "WIOD", f"2000->{y} {s}", far) for y in (2014, 2019, 2023)
        for s in ("+ catch-up + import intensity", "+ catch-up + import int., per-capita")]
m("ImpWiodPMax", f"{max(x.p_resample for x in impW):.3f}")
impIh = [row("A", "ICIO", f"2011->{y} + catch-up + import intensity", far) for y in (2019, 2023)]
impIc = [row("A", "ICIO", f"2011->{y} + catch-up + import int., per-capita", far) for y in (2019, 2023)]
m("ImpIcioHourPMin", f"{min(x.p_resample for x in impIh):.2f}")
m("ImpIcioHourPMax", f"{max(x.p_resample for x in impIh):.2f}")
m("ImpIcioPcPMin", f"{min(x.p_resample for x in impIc):.2f}")
m("ImpIcioPcPMax", f"{max(x.p_resample for x in impIc):.2f}")
conv = [row("A", ds, f"{y0}->{y} + catch-up, excl. fast convergers", far)
        for ds, y0, ys in [("ICIO", 2011, (2019, 2023)), ("WIOD", 2000, (2014, 2019, 2023))] for y in ys]
m("ConvBetaMin", f2(min(x.beta_sd for x in conv)))
m("ConvBetaMax", f2(max(x.beta_sd for x in conv)))
m("ConvPMin", f"{min(x.p_resample for x in conv):.3f}")
m("ConvPMax", f"{max(x.p_resample for x in conv):.3f}")

# ---- B / C ----------------------------------------------------------------------
for ds in ("WIOD", "ICIO"):
    p = row("B", ds, "pooled + period FE + catch-up", far)
    w = row("B", ds, "within-country (country + period FE)", far)
    m(f"Pooled{ds.title()}Beta", f2(p.beta_sd))
    m(f"Pooled{ds.title()}P", fp_text(p.p_resample))
    m(f"Within{ds.title()}P", f"{w.p_resample:.2f}")
    c = row("C", ds, "momentum", far, exact=False)
    m(f"Deep{ds.title()}P", f"{c.p_resample:.2f}")
    v = row("C", ds, "momentum", dom, exact=False)
    m(f"DeepDom{ds.title()}P", f"{v.p_resample:.3f}")

# ---- D -----------------------------------------------------------------------
dg = res[res.test.str.startswith("D") & res.measure.str.contains("global")]
dd = res[res.test.str.startswith("D") & res.measure.str.contains("domestic")]
cfe = dg[dg.spec == "country FE"].iloc[0]
ife = dg[dg.spec.str.contains("industry FE")].iloc[0]
m("PriceN", f"{int(cfe.n):,}".replace(",", "{,}"))
m("PriceBeta", "$" + f2(cfe.beta_sd) + "$")
m("PriceP", fp_text(cfe.p_resample))
m("PriceIndBeta", "$" + f2(ife.beta_sd) + "$")
m("PriceIndP", f"{ife.p_resample:.2f}")
m("PriceDomBeta", "$" + f2(dd[dd.spec == "country FE"].iloc[0].beta_sd) + "$")
m("PriceDomP", fp_text(dd[dd.spec == "country FE"].iloc[0].p_resample))
m("PriceDomIndP", f"{dd[dd.spec.str.contains('industry FE')].iloc[0].p_resample:.2f}")

# ---- amplification -------------------------------------------------------------
def arow(prefix, variant="all 43"):
    r = amp[(amp.variant == variant) & amp.spec.str.startswith(prefix)]
    assert len(r) == 1, (prefix, variant)
    return r.iloc[0]


b1, b2 = arow("1 "), arow("2 ")
m("AmpN", str(int(b1.n)))
m("AmpBaseB", f2(b1.b_L_bar))
m("AmpCtrlB", f2(b2.b_L_bar))
m("AmpCtrlP", fp_text(b2.pperm_L_bar))
m("AmpShare", f"{100 * (1 - b2.b_L_bar / b1.b_L_bar):.0f}")
m("AmpGammaB", f2(b2.b_gamma_tilde))
m("AmpCorr", f2(amp[amp.spec.str.startswith("corr")].iloc[0]["corr"]))
b3, b4 = arow("3 "), arow("4 ")
m("ModelSlope", f2(b3.b_pred_network))
m("ModelRsq", f2(b3.r2))
m("NetPartB", f2(b4.b_network_part))
m("NetPartP", fp_text(b4.pperm_network_part))
m("FinalPartB", f2(b4.b_pred_no_network))
m("FinalPartP", f"{b4.pperm_pred_no_network:.2f}")
k1, k2 = arow("1 ", "γ net of capital"), arow("2 ", "γ net of capital")
m("AmpShareK", f"{100 * (1 - k2.b_L_bar / k1.b_L_bar):.0f}")
r1, r2 = arow("1 ", "excl. Russia (41% imputed)"), arow("2 ", "excl. Russia (41% imputed)")
m("AmpShareNoRus", f"{100 * (1 - r2.b_L_bar / r1.b_L_bar):.0f}")
F = fc.loc["Farmer: L̄(2007) x γ̃(2000-07)"]
S = fc.loc["same γ̃, average chain length"]
P = fc.loc["past growth 2000-07 (persistence)"]
C = fc.loc["everyone grows at the 2000-07 average"]
m("FcCorr", f2(F["corr"]))
m("FcRmse", f2(F.rmse))
m("FcSameCorr", f2(S["corr"]))
m("FcSameRmse", f2(S.rmse))
m("FcPastCorr", f2(P["corr"]))
m("FcPastRmse", f2(P.rmse))
m("FcConstRmse", f2(C.rmse))
m("FcN", str(int(F.n)))

# ---- H2: home vs abroad --------------------------------------------------------
hyp = pd.read_csv("hypotheses_results.csv")


def hrow(test, ds, win, spec):
    r = hyp[(hyp.test == test) & (hyp.dataset == ds) & (hyp.window == win) & (hyp.spec == spec)]
    assert len(r) == 1, (test, ds, win, spec)
    return r.iloc[0]


ha = {ds: [hrow("cross-section", ds, w, "home + abroad") for w in wins]
      for ds, wins in [("WIOD", ["2000-2014", "2000-2019", "2000-2023"]),
                       ("ICIO", ["2011-2019", "2011-2023"])]}
for ds, rows_ in ha.items():
    t = ds.title()
    m(f"Home{t}BetaMin", f2(min(r.bsd_home_depth for r in rows_)))
    m(f"Home{t}BetaMax", f2(max(r.bsd_home_depth for r in rows_)))
    m(f"Home{t}PMin", f"{min(r.pres_home_depth for r in rows_):.3f}")
    m(f"Home{t}PMax", f"{max(r.pres_home_depth for r in rows_):.3f}")
    m(f"Abroad{t}BetaMin", f2(min(r.bsd_abroad_depth for r in rows_)))
    m(f"Abroad{t}BetaMax", f2(max(r.bsd_abroad_depth for r in rows_)))
    m(f"Abroad{t}PMax", f"{max(r.pres_abroad_depth for r in rows_):.3f}")
h2 = {ds: [hrow("cross-section", ds, w, "H2: total + home") for w in wins]
      for ds, wins in [("WIOD", ["2000-2014", "2000-2019", "2000-2023"]),
                       ("ICIO", ["2011-2019", "2011-2023"])]}
allh2 = h2["WIOD"] + h2["ICIO"]
m("HtwoPMin", f"{min(r.pres_home_depth for r in allh2):.2f}")
m("HtwoPMax", f"{max(r.pres_home_depth for r in allh2):.2f}")
prem = [(r.b_home_depth / r.b_farmer_depth,
         (r.b_home_depth - 1.96 * abs(r.b_home_depth / r.t_home_depth)) / r.b_farmer_depth,
         (r.b_home_depth + 1.96 * abs(r.b_home_depth / r.t_home_depth)) / r.b_farmer_depth)
        for r in h2["WIOD"]]
m("PremMin", f"{100 * min(p[0] for p in prem):.0f}")
m("PremMax", f"{100 * max(p[0] for p in prem):.0f}")
m("PremLoMin", "$" + f"{100 * min(p[1] for p in prem):.0f}" + "$")
m("PremHiMax", f"{100 * max(p[2] for p in prem):.0f}")
m("CorrHomeAbroadWiod", f2(wiod.home_depth.corr(wiod.abroad_depth)))
pw = hrow("windows", "WIOD", "3 windows", "pooled windows: home + abroad")
m("PoolHomeWiod", f2(pw.bsd_home_depth))
m("PoolHomeWiodP", fp_text(pw.pres_home_depth))
m("PoolAbroadWiod", f2(pw.bsd_abroad_depth))
m("PoolAbroadWiodP", fp_text(pw.pres_abroad_depth))
pc = hrow("prices", "WIOD", "2000-2014", "prices: country FE")
pi_ = hrow("prices", "WIOD", "2000-2014", "prices: + industry FE")
m("PriceHomeBeta", "$" + f2(pc.bsd_L_home) + "$")
m("PriceHomeP", f"{pc.pres_L_home:.2f}")
m("PriceAbroadBeta", "$" + f2(pc.bsd_L_abroad) + "$")
m("PriceAbroadP", fp_text(pc.pres_L_abroad))
m("PriceAbroadIndP", f"{pi_.pres_L_abroad:.2f}")
it = icio[(icio.code == "ITA") & (icio.year == 2019)].iloc[0]
m("ItaTotal", f2(it.farmer_depth))
m("ItaHome", f2(it.home_depth))
m("ItaAbroad", f2(it.abroad_depth))
ie = icio[(icio.code == "IRL") & (icio.year == 2019)].iloc[0]
m("IrlHome", f2(ie.home_depth))
m("IrlAbroad", f2(ie.abroad_depth))

lines = [r"\begin{tabular}{llrrrr}", r"\toprule",
         r" & & \multicolumn{2}{c}{Steps at home} & \multicolumn{2}{c}{Steps abroad} \\",
         r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
         r"Data & Window & $\beta$/SD & $p$ & $\beta$/SD & $p$ \\", r"\midrule"]
for ds, wins in [("ICIO", ["2011-2019", "2011-2023"]), ("WIOD", ["2000-2014", "2000-2019", "2000-2023"])]:
    for w in wins:
        r = hrow("cross-section", ds, w, "home + abroad")
        lines.append(f"{ds} & {w.replace('-', '--')} & {r.bsd_home_depth:+.2f} & {fp(r.pres_home_depth)} & "
                     f"{r.bsd_abroad_depth:+.2f} & {fp(r.pres_abroad_depth)} \\\\")
for ds, w in [("WIOD", "3 windows"), ("ICIO", "2 windows")]:
    r = hrow("windows", ds, w, "pooled windows: home + abroad")
    lines.append(f"{ds} & {w}, pooled & {r.bsd_home_depth:+.2f} & {fp(r.pres_home_depth)} & "
                 f"{r.bsd_abroad_depth:+.2f} & {fp(r.pres_abroad_depth)} \\\\")
lines += [r"\midrule", r"\multicolumn{6}{l}{\emph{H2 directly: extra effect of a home step, given total length}} \\"]
for ds, wins in [("ICIO", ["2011-2019", "2011-2023"]), ("WIOD", ["2000-2014", "2000-2019", "2000-2023"])]:
    for w in wins:
        r = hrow("cross-section", ds, w, "H2: total + home")
        lines.append(f"{ds} & {w.replace('-', '--')} & {r.bsd_home_depth:+.2f} & {fp(r.pres_home_depth)} & & \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(OUT, "tables", "hypotheses.tex"), "w").write("\n".join(lines) + "\n")

with open(os.path.join(OUT, "numbers.tex"), "w") as fh:
    fh.write("% generated by paper/make_numbers.py -- do not edit by hand\n")
    for k, v in sorted(macros.items()):
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

# ---- tables ---------------------------------------------------------------------
def esc(s):
    return (s.replace("->", r"$\to$").replace("Δ", r"$\Delta$").replace("&", r"\&")
             .replace("%", r"\%").replace("_", r"\_").replace("γ", r"$\gamma$"))


main_specs = [
    ("ICIO", "2011->2019 + catch-up", "ICIO, 2011--2019"),
    ("ICIO", "2011->2023 + catch-up", "ICIO, 2011--2023"),
    ("WIOD", "2000->2014 + catch-up", "WIOD, 2000--2014"),
    ("WIOD", "2000->2019 + catch-up", "WIOD, 2000--2019"),
    ("WIOD", "2000->2023 + catch-up", "WIOD, 2000--2023"),
]
lines = [r"\begin{tabular}{lrrrrr}", r"\toprule",
         r" & \multicolumn{2}{c}{Farmer's $\bar L$ (global)} & \multicolumn{2}{c}{Domestic depth (v1)} & \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
         r"Sample & $\beta$/SD & $p$ & $\beta$/SD & $p$ & $n$ \\", r"\midrule"]
for ds, spec, lab in main_specs:
    a = row("A", ds, spec, far)
    b = row("A", ds, spec, dom)
    lines.append(f"{lab} & {a.beta_sd:+.2f} & {fp(a.p_resample)} & {b.beta_sd:+.2f} & "
                 f"{fp(b.p_resample)} & {int(a.n)} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(OUT, "tables", "main.tex"), "w").write("\n".join(lines) + "\n")

lines = [r"\begin{tabular}{llrrr}", r"\toprule",
         r"Specification & Coefficient & Estimate & $p$ (perm.) & $R^2$ \\", r"\midrule"]
labels = {"L_bar": r"$\bar L$", "gamma_tilde": r"$\tilde\gamma$",
          "pred_network": r"$\theta'(I-A^\top)^{-1}\gamma$",
          "pred_no_network": r"final-stage part $\theta'\gamma$",
          "network_part": r"network part"}
specs = [("1 ", "(1) chain length"), ("2 ", r"(2) $+$ industry productivity $\tilde\gamma$"),
         ("3 ", "(3) full model prediction"), ("4 ", "(4) final-stage $+$ network part")]
for pre, lab in specs:
    r_ = arow(pre)
    first = True
    for key in ("L_bar", "gamma_tilde", "pred_network", "pred_no_network", "network_part"):
        if f"b_{key}" in r_ and not pd.isna(r_[f"b_{key}"]):
            lines.append(f"{lab if first else ''} & {labels[key]} & {r_[f'b_{key}']:+.2f} & "
                         f"{fp(r_[f'pperm_{key}'])} & {f2(r_.r2) if first else ''} \\\\")
            first = False
lines += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(OUT, "tables", "amplification.tex"), "w").write("\n".join(lines) + "\n")

lines = [r"\begin{tabular}{lrr}", r"\toprule", r"Forecast of 2007--2014 growth & Correlation & RMSE \\",
         r"\midrule"]
fl = {"Farmer: L̄(2007) x γ̃(2000-07)": r"Farmer: $\bar L_{2007}\times\tilde\gamma_{2000\text{--}07}$",
      "same γ̃, average chain length": r"Same $\tilde\gamma$, average chain length",
      "past growth 2000-07 (persistence)": "Past growth continues (2000--07)",
      "everyone grows at the 2000-07 average": "Everyone grows at the 2000--07 mean"}
for k, lab in fl.items():
    x = fc.loc[k]
    cr = "--" if (pd.isna(x["corr"]) or abs(x["corr"]) < 1e-9) else f"{x['corr']:.2f}"
    lines.append(f"{lab} & {cr} & {x.rmse:.2f} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(OUT, "tables", "forecast.tex"), "w").write("\n".join(lines) + "\n")

lines = [r"\begin{longtable}{ll>{\raggedright\arraybackslash}p{4.6cm}lrrrr}", r"\toprule",
         r"Test & Data & Specification & Measure & $\beta$/SD & $p$ (an.) & $p$ (res.) & $n$ \\",
         r"\midrule", r"\endhead"]
for x in res.itertuples():
    meas = "Farmer" if x.measure.startswith("Farmer") else ("v1 dom." if x.measure.startswith("v1")
                                                          else ("ind. $L$ glob." if "global" in x.measure
                                                                else "ind. $L$ dom."))
    lines.append(f"{x.test.split()[0]} & {x.dataset} & {esc(x.spec)} & {meas} & {x.beta_sd:+.2f} & "
                 f"{fp(x.p_analytic)} & {fp(x.p_resample)} & {int(x.n)} \\\\")
lines += [r"\bottomrule", r"\end{longtable}"]
open(os.path.join(OUT, "tables", "appendix_all.tex"), "w").write("\n".join(lines) + "\n")
print(f"wrote {len(macros)} macros and 5 tables")
