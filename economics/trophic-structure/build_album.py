"""
Assemble the 30 single-country network PNGs into one PDF album.
One country per page (full size), ordered by trophic depth, with a title page
and a per-page caption carrying the key structural descriptors.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
import pandas as pd
from countries import COUNTRIES, ARCHETYPE_COLOR

name_of = {c: n for c, n, _ in COUNTRIES}
desc = pd.read_csv("network_descriptors.csv").set_index("code")
cl = pd.read_csv("icio_country_year.csv").query("year == 2019").set_index("code")
order = cl.sort_values("farmer_depth", ascending=False).index.tolist()   # Farmer's chain length

LAB = {"G": "wholesale & retail trade", "F": "construction", "M": "professional services",
       "A01_02": "agriculture", "C10T12": "food processing", "K": "finance"}

OUT = "figures/trophic_networks_album.pdf"
with PdfPages(OUT) as pdf:
    # --- title page ---
    fig = plt.figure(figsize=(11.7, 8.3))   # A4 landscape
    fig.text(0.5, 0.72, "Trophic Networks of 30 Economies", ha="center",
             fontsize=30, weight="bold", color="#222")
    fig.text(0.5, 0.63, "The structure of production, sector by sector", ha="center",
             fontsize=15, color="#666", style="italic")
    fig.text(0.5, 0.45,
             "Each economy is drawn as a production network. Height = production stages\n"
             "behind each sector, counting steps abroad; the hollow dot below each node marks\n"
             "the stages done at home. Fill = share of inputs imported; size = gross output;\n"
             "ring = production community; arrows = largest domestic flows and imports.\n\n"
             "Pages are ordered from the longest production chains to the shortest.",
             ha="center", fontsize=12, color="#333", linespacing=1.6)
    fig.text(0.5, 0.10,
             "Source: OECD ICIO 2023 edition, year 2019.  Method: McNerney et al. (PNAS 2022); "
             "MacKay, Johnson & Sansom (2020).\nIl Divano Color Senape.",
             ha="center", fontsize=8.5, color="#888", linespacing=1.5)
    fig.patch.set_facecolor("white")
    pdf.savefig(fig, facecolor="white")
    plt.close(fig)

    # --- one page per country ---
    for rank, code in enumerate(order, 1):
        d = desc.loc[code]
        fig = plt.figure(figsize=(11.7, 8.3))
        ax = fig.add_axes([0.02, 0.10, 0.96, 0.82])
        ax.imshow(mpimg.imread(f"figures/networks/{code}.png"))
        ax.axis("off")
        col = ARCHETYPE_COLOR[d["archetype"]]
        fig.text(0.04, 0.95, f"{rank}.  {name_of[code]}", fontsize=20, weight="bold",
                 color="#222", va="center")
        fig.text(0.04, 0.915, d["archetype"], fontsize=11, color=col,
                 weight="bold", va="center")
        hub = LAB.get(d["top_hub"], d["top_hub"])
        c2 = cl.loc[code]
        cap = (f"chain length {c2.farmer_depth:.2f} = {c2.home_depth:.2f} at home + "
               f"{c2.abroad_depth:.2f} abroad   ·   "
               f"central hub: {hub}   ·   {int(d['n_comm'])} production communities   ·   "
               f"intermediation {d['intermediation_share']*100:.0f}% of output")
        fig.text(0.5, 0.055, cap, ha="center", fontsize=10, color="#444")
        fig.text(0.98, 0.02, f"{rank}/30", ha="right", fontsize=8, color="#aaa")
        pdf.savefig(fig, facecolor="white")
        plt.close(fig)

    info = pdf.infodict()
    info["Title"] = "Trophic Networks of 30 Economies"
    info["Author"] = "Il Divano Color Senape"

print("saved", OUT)
