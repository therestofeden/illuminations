#!/usr/bin/env bash
# Download the OECD ICIO input-output tables used by this project.
#
# Default: 2023 edition, regular ("small") tables, bundle 2016-2020.
# The pipeline uses year 2019 (last clean pre-COVID year).
#
# Source page (and the newer 2025 edition, data to 2022):
#   https://www.oecd.org/en/data/datasets/inter-country-input-output-tables.html
# OECD data are free to reuse with attribution under the OECD terms of use.
set -euo pipefail

mkdir -p icio2023

# Two bundles still served on stats.oecd.org cover 2011-2020 — the years used by
# the cross-section (2019) and the dynamic panel (2011-2020). Older bundles
# (pre-2011) have been retired from this host; fetch them from the OECD page
# below if you want a longer panel.
declare -A BUNDLES=(
  ["2011-2015"]="1f791bc6-befb-45c5-8b34-668d08a1702a"
  ["2016-2020"]="d1ab2315-298c-4e93-9a81-c6f2273139fe"
)
for b in "${!BUNDLES[@]}"; do
  echo "Downloading ICIO 2023 edition, ${b} bundle (~85 MB)..."
  curl -L --fail -o "icio2023/${b}_SML.zip" \
    "https://stats.oecd.org/wbos/fileview2.aspx?IDFile=${BUNDLES[$b]}"
  unzip -o "icio2023/${b}_SML.zip" -d icio2023 >/dev/null
done
echo "Done. CSVs in icio2023/ (2011_SML.csv ... 2020_SML.csv)."
echo
echo "To use the newest 2025 edition (to 2022) instead, download"
echo "  2016-2022_SML.zip from the OECD page above and unzip it into icio2023/,"
echo "  then run:  python3 build_trophic.py icio2023/2022_SML.csv"
