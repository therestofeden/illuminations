"""
Fetch GDP context data from the World Bank Open Data API (CC BY 4.0).

  NY.GDP.MKTP.CD     GDP, current US$ (2019)             -> bubble size
  NY.GDP.PCAP.PP.KD  GDP per capita, PPP const 2021$ (2019) -> wealth level
  NY.GDP.MKTP.KD.ZG  Real GDP growth %, 2010-2019 mean   -> Farmer's growth test

Taiwan (TWN) is not a World Bank member; its figures are taken from the IMF
World Economic Outlook and flagged separately in the output.
"""

import json
import urllib.request
import pandas as pd
from countries import COUNTRIES

WB = "https://api.worldbank.org/v2/country/{cty}/indicator/{ind}?date={date}&format=json&per_page=20000"
codes = [c for c, _, _ in COUNTRIES if c != "TWN"]
ctry = ";".join(codes)


def fetch(ind, date):
    url = WB.format(cty=ctry, ind=ind, date=date)
    with urllib.request.urlopen(url, timeout=40) as r:
        data = json.load(r)[1]
    out = {}
    for row in data:
        iso, val = row["countryiso3code"], row["value"]
        if val is None:
            continue
        out.setdefault(iso, {})[int(row["date"])] = val
    return out

gdp = fetch("NY.GDP.MKTP.CD", "2019")
pcap = fetch("NY.GDP.PCAP.PP.KD", "2019")
grow = fetch("NY.GDP.MKTP.KD.ZG", "2010:2019")

rows = []
for code, name, _ in COUNTRIES:
    if code == "TWN":
        # IMF World Economic Outlook (Oct 2024): 2019 GDP ~US$611bn;
        # GDP per capita PPP 2019 ~US$55,800; 2010-19 mean real growth ~3.2%.
        rows.append(dict(code="TWN", gdp_usd=611_390e6, gdp_pc_ppp=55800,
                         growth_2010_19=3.2, gdp_source="IMF WEO 2024"))
        continue
    g = gdp.get(code, {}).get(2019)
    p = pcap.get(code, {}).get(2019)
    gr = grow.get(code, {})
    grm = sum(gr.values()) / len(gr) if gr else None
    rows.append(dict(code=code, gdp_usd=g, gdp_pc_ppp=p,
                     growth_2010_19=round(grm, 3) if grm else None,
                     gdp_source="World Bank WDI"))

gdf = pd.DataFrame(rows)
gdf.to_csv("gdp_context.csv", index=False)
print(gdf.to_string(index=False))
print("\nsaved gdp_context.csv  (rows:", len(gdf), ")")
