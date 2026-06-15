# Trophic structure of economies — *Il Divano Color Senape*

How deep do a country's production chains run? This project measures the **trophic
structure** of 30 economies from public input-output data and turns it into four
publication-ready figures. Inspired by J. Doyne Farmer, *Making Sense of Chaos* (2024).

![Trophic depth ranking](figures/1_depth_ranking.png)

## The idea

Ecologists rank species by *trophic level*: plants sit at the bottom, herbivores one
step up, their predators above them. The same arithmetic works on an economy's
input-output table. An industry that runs mostly on labour and raw materials sits low;
an industry fed by long chains of *other* producers sits high. Average a country's
industries and you get its **trophic depth** — a one-number summary of how long its
production chains are. Farmer's group showed this is not idle structure: deeper chains
predict faster long-run growth.

We compute two versions:

- **Domestic trophic depth** — chains *inside* the country only.
- **Global trophic depth** — chains including imported intermediates (a country's true
  position in global value chains).

Their difference is the **offshore gap**: how much of a country's production depth is
actually assembled abroad. It cleanly separates self-contained giants (China, the USA)
from assembly-and-holding economies (Vietnam, Ireland, Luxembourg, Singapore).

## Method

- **Trophic level = output multiplier** (McNerney, Savoie, Caravelli, Carvalho & Farmer,
  *PNAS* 2022): a sector's level is `1 +` the input-share-weighted average level of its
  suppliers, with value added as the implicit base. Equals the row sums of the Leontief
  inverse. → `trophic.py:trophic_levels_io`
- **Trophic incoherence** (MacKay, Johnson & Sansom, *Royal Society Open Science* 2020):
  how cleanly the flow network layers vs. how tangled it is. → `trophic.py:trophic_incoherence`

Both functions are validated against networks with known answers — run `python3 trophic.py`.

## Data & provenance

| What | Source | Licence |
|---|---|---|
| Input-output tables | **OECD ICIO, 2023 edition, year 2019** (regular/SML, ISIC Rev.4, 76 economies) | OECD terms of use (free reuse w/ attribution) |
| GDP, GDP per capita, growth | **World Bank** World Development Indicators | CC BY 4.0 |
| Taiwan macro figures | **IMF** World Economic Outlook | per IMF terms |

The raw ICIO CSVs (~66 MB/year) are **not** committed — run `bash download_data.sh` to
fetch them. The newest **2025 edition** (data to 2022) is a drop-in upgrade; see the
script and the OECD page linked there.

> Year 2019 is used deliberately: it is the last pre-pandemic year, so the structure
> isn't distorted by COVID-19 shocks to 2020 input-output flows.

## Reproduce

```bash
pip install -r requirements.txt
bash download_data.sh            # fetch OECD ICIO (2011-2020) into icio2023/

# --- cross-section (one year) ---
python3 trophic.py               # self-tests
python3 build_trophic.py         # -> results_country.csv, results_sectors.csv
python3 fetch_gdp.py             # -> gdp_context.csv  (needs internet)
python3 make_figures.py          # -> figures/1..4 .png

# --- dynamic test (panel) ---
python3 build_panel.py icio2023/20{11,12,13,14,15,16,17,18,19,20}_SML.csv  # -> panel.csv
python3 fetch_growth.py          # -> growth_panel.csv  (needs internet)
python3 dynamic_test.py          # prints the regression table -> dynamic_sample.csv
python3 make_dynamic_figures.py  # -> figures/5..7 .png

# --- network visualizations ---
python3 network_viz.py DEU SAU   # a contrast pair  -> figures/8_network_DEU_SAU.png
python3 network_viz.py --all     # all 30, one file each -> figures/networks/<CODE>.png
python3 montage_networks.py      # contact sheet -> figures/networks_contact_sheet.png
python3 build_album.py           # one-per-page PDF -> figures/trophic_networks_album.pdf

# --- structural descriptors + insights ---
python3 analyze_networks.py      # -> network_descriptors.csv (+ correlations printed)

# --- rebuild the interactive dashboard ---
npm install d3                   # one-off: provides D3 to inline
python3 export_web_data.py       # -> docs/data.json
python3 build_dashboard.py       # inlines D3 + data -> docs/index.html
```

Every step above was verified end-to-end from a fresh clone: `results_country.csv`,
`panel.csv`, and `network_descriptors.csv` regenerate **byte-identical** to the
committed copies, and all figures, the album, and the dashboard rebuild cleanly.

## Interactive dashboard (GitHub Pages)

`docs/index.html` is a fully self-contained network explorer — pick any country, see its
trophic network rendered live, hover sectors, and click the ranking/offshore-gap charts
to cross-navigate. It embeds both its data **and** the D3 library, so the single file
works offline with no internet connection or external dependencies.

Rebuild it after changing the data:

```bash
npm install d3                 # one-off: provides the D3 library to inline
python3 export_web_data.py     # -> docs/data.json
python3 build_dashboard.py     # inlines D3 + data -> docs/index.html
```

**Publish on GitHub Pages:** push the repo, then in *Settings → Pages* set
*Source = Deploy from a branch*, *Branch = main*, *Folder = /docs*. Your explorer goes
live at `https://<user>.github.io/<repo>/`. (You can also just double-click
`docs/index.html` to open it locally — it works offline.)

## The dynamic test — does Farmer's claim actually hold?

Farmer argues deeper production chains *cause* faster growth. A single year can't
test that, so we built a **10-year panel** (trophic depth × 30 countries, 2011–2020)
and asked whether depth predicts *subsequent* 3-year GDP growth. Standard errors are
clustered by country.

| Specification | Effect of depth on next-3-yr growth | p |
|---|---|---|
| Raw correlation | +1.3 | 0.64 |
| + catch-up control (income level) | −0.7 | 0.82 |
| + year fixed effects | −0.7 | 0.82 |
| **Within-country** (country fixed effects) | **+4.3** | 0.25 |
| **Deepening** (Δdepth over prior 3 yrs) | **+8.7** | **0.09** |

The naive "deeper economies grow faster" **fails** — it's an artifact of where countries
sit, and it vanishes once you control for catch-up. But the *dynamic* version Farmer
actually makes survives: **when a country deepens its own chains, it tends to grow faster
afterward** (marginally significant, p≈0.09). Suggestive, not conclusive, on a short
panel — but pointing his way. See `figures/5–7`.

> Honest caveats: 10 years is short for a long-horizon claim; depth is persistent so
> windows overlap; 29 countries (Taiwan dropped — no World Bank series); marginal
> significance. A multi-decade panel (older ICIO bundles, fetched manually) is the
> natural strengthening.

## What the figures show

1. **`1_depth_ranking.png`** — trophic depth, ranked. China deepest (2.36); Ireland
   shallowest (1.14) — its multinational-inflated output barely chains domestically.
2. **`2_offshore_gap.png`** — domestic vs global depth. China and the USA hug the
   diagonal (self-contained); Vietnam, Luxembourg, Ireland and Singapore float far above
   it (their chains live abroad).
3. **`3_trophic_profiles.png`** — the full distribution of output across trophic levels
   for eight economies. Saudi Arabia's mass sits low; China's and Czechia's sit high.
4. **`4_depth_vs_growth.png`** — Farmer's claim, tested loosely on the cross-section
   (r ≈ 0.34), with the catch-up confound shown via bubble size. The *proper* test is
   the panel below.
5. **`5_depth_trajectories.png`** — how each economy's trophic depth moved 2011–2020.
   Vietnam deepened sharply; China rose then partly reversed; mature economies sat flat.
6. **`6_deepening_vs_growth.png`** — the key result: countries that deepened their chains
   then grew faster.
7. **`7_specification_curve.png`** — the honesty plot: the growth link appears *only* in
   the dynamic, within-country specifications, not the naive correlation.
8. **`8_network_DEU_SAU.png`** — the production network itself, Farmer-style. Sectors are
   stacked vertically by trophic level; node size = output, inner pink = self-flow, outer
   green = throughflow, ring colour = production community, arrows = the heaviest flows.
   Germany spreads up the chain; Saudi Arabia sits on one giant low-trophic mining node.
   Run `network_viz.py` with any country codes to render others.

## Caveats

- A single cross-section can't properly test a dynamic claim about growth; figure 4 is
  illustrative, not confirmatory.
- "Trophic depth" here is the Type-I output multiplier; it captures chain *length*, not
  technological sophistication. It is a cousin of, not identical to, the Economic
  Complexity Index.

## References

- McNerney, Savoie, Caravelli, Carvalho & Farmer, "How production networks amplify
  economic growth", *PNAS* 119 (2022). https://www.pnas.org/doi/10.1073/pnas.2106031118
- MacKay, Johnson & Sansom, "How directed is a directed network?", *Royal Society Open
  Science* 7:201138 (2020). https://royalsocietypublishing.org/rsos/article/7/9/201138
- J. Doyne Farmer, *Making Sense of Chaos* (2024).
- OECD ICIO: https://www.oecd.org/en/data/datasets/inter-country-input-output-tables.html
