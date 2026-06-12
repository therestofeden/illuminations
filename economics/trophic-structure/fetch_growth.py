"""Annual real GDP growth (%) and GDP per capita (PPP) 2010-2023, World Bank WDI.
Saves growth_panel.csv (code, year, growth, gdp_pc_ppp). Taiwan omitted (not WB)."""
import json, urllib.request
import pandas as pd
from countries import COUNTRIES

codes = [c for c, _, _ in COUNTRIES if c != "TWN"]
ctry = ";".join(codes)
URL = "https://api.worldbank.org/v2/country/{c}/indicator/{i}?date=2010:2023&format=json&per_page=20000"

def fetch(ind):
    req = urllib.request.Request(URL.format(c=ctry, i=ind),
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.load(r)[1]
    return {(row["countryiso3code"], int(row["date"])): row["value"]
            for row in data if row["value"] is not None}

growth = fetch("NY.GDP.MKTP.KD.ZG")
pcap = fetch("NY.GDP.PCAP.PP.KD")
rows = [dict(code=c, year=y, growth=growth[(c, y)], gdp_pc_ppp=pcap.get((c, y)))
        for (c, y) in growth]
df = pd.DataFrame(rows).sort_values(["code", "year"])
df.to_csv("growth_panel.csv", index=False)
print("rows", len(df), "| years", df.year.min(), "-", df.year.max(),
      "| countries", df.code.nunique())
