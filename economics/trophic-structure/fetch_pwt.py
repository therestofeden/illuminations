"""
Growth outcomes from the Penn World Table 11.0 (Feenstra, Inklaar & Timmer;
Groningen Growth and Development Centre). CC BY 4.0.

McNerney et al. measure growth as real GDP per hour worked, so v2 does too
(v1 used total real GDP growth, which mixes in population growth).
Growth rates use rgdpna (constant national prices); the catch-up control uses
rgdpo (chained PPPs), per the PWT user guide: rgdpna for growth, rgdpo for
cross-country level comparisons.

Usage: python3 fetch_pwt.py   -> pwt_growth.csv (code, year, log levels)
The PWT "Excel" file is downloaded from the GGDC Dataverse.
"""
import io
import time
import urllib.request
import numpy as np
import pandas as pd

URL = "https://dataverse.nl/api/access/datafile/554105"   # PWT 11.0 main file, pwt110.xlsx
# (dataset doi:10.34894/FABVLR)

# NB: no browser User-Agent: the Dataverse anti-bot page challenges browser UAs,
# and it occasionally challenges scripts too, so retry a few times.
for attempt in range(5):
    with urllib.request.urlopen(URL, timeout=120) as r:
        raw = r.read()
    if raw.startswith(b"PK"):
        break
    time.sleep(20 * (attempt + 1))
else:
    raise SystemExit("Dataverse kept returning a web page instead of the xlsx; retry later")
p = pd.read_excel(io.BytesIO(raw), sheet_name="Data")
# rgdpna = real GDP at constant 2021 national prices (the PWT series for growth rates)
# rgdpo  = output-side real GDP at chained PPPs: the PWT series for comparing
#          LEVELS across countries (used for the catch-up control)
p = p[["countrycode", "year", "rgdpna", "rgdpo", "pop", "emp", "avh"]].rename(
    columns={"countrycode": "code", "rgdpna": "q_gdp"})
p["log_gdp_hour"] = np.log(p.q_gdp / (p.emp * p.avh))
p["log_gdp_pc"] = np.log(p.q_gdp / p["pop"])
p["log_gdp_worker"] = np.log(p.q_gdp / p.emp)
p["log_level_hour"] = np.log(p.rgdpo / (p.emp * p.avh))     # PPP level, cross-country
p = p[(p.year >= 1995) & (p.year <= 2023)]
p[["code", "year", "log_gdp_hour", "log_gdp_pc", "log_gdp_worker", "log_level_hour"]].round(6).to_csv(
    "pwt_growth.csv", index=False)
print("pwt_growth.csv:", len(p), "rows,", p.code.nunique(), "economies,",
      "hours available for", p.dropna(subset=["log_gdp_hour"]).code.nunique())
