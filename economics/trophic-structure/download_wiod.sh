#!/usr/bin/env bash
# Download the WIOD 2016 release (Timmer et al.) used by the v2 replication.
#   - World Input-Output Tables 2000-2014, Stata format (~640 MB zip, ~830 MB unpacked)
#   - Socio-Economic Accounts (prices, wages, hours; ~5 MB)
# Dataset: https://doi.org/10.34894/PJ2M1C  (Groningen Growth and Development Centre)
# Licence: CC BY 4.0.
#
# The Dataverse host sometimes answers with an anti-bot web page instead of the
# file; the checks below catch that. Don't send a browser User-Agent.
set -euo pipefail
mkdir -p wiod_data
cd wiod_data

fetch () {   # fetch <datafile id> <output> <expected magic bytes>
  for attempt in 1 2 3 4 5; do
    curl -sSL --fail -o "$2" "https://dataverse.nl/api/access/datafile/$1"
    if head -c 2 "$2" | grep -q "$3"; then return 0; fi
    echo "  got a web page instead of $2, retrying in $((attempt * 20))s..."
    sleep $((attempt * 20))
  done
  echo "Could not download $2" >&2; exit 1
}

echo "Socio-Economic Accounts..."
fetch 199095 SEA.xlsx PK
echo "World Input-Output Tables 2000-2014 (Stata, ~640 MB)..."
fetch 199103 WIOTS_STATA.zip PK
unzip -o -q WIOTS_STATA.zip && rm WIOTS_STATA.zip
echo "Done: wiod_data/WIOT2000_October16_ROW.dta ... WIOT2014_October16_ROW.dta, SEA.xlsx"
