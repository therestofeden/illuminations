"""The 30 economies, grouped by archetype (drives colour + narrative)."""

COUNTRIES = [
    # code, name, archetype
    ("DEU", "Germany",        "Deep manufacturing"),
    ("JPN", "Japan",          "Deep manufacturing"),
    ("KOR", "South Korea",    "Deep manufacturing"),
    ("CHN", "China",          "Deep manufacturing"),
    ("ITA", "Italy",          "Deep manufacturing"),
    ("CZE", "Czechia",        "Deep manufacturing"),
    ("SAU", "Saudi Arabia",   "Resource & extraction"),
    ("NOR", "Norway",         "Resource & extraction"),
    ("AUS", "Australia",      "Resource & extraction"),
    ("RUS", "Russia",         "Resource & extraction"),
    ("CHL", "Chile",          "Resource & extraction"),
    ("SGP", "Singapore",      "Financial / service hub"),
    ("CHE", "Switzerland",    "Financial / service hub"),
    ("NLD", "Netherlands",    "Financial / service hub"),
    ("GBR", "United Kingdom", "Financial / service hub"),
    ("LUX", "Luxembourg",     "Financial / service hub"),
    ("IRL", "Ireland",        "Financial / service hub"),
    ("USA", "United States",  "Large diversified"),
    ("FRA", "France",         "Large diversified"),
    ("CAN", "Canada",         "Large diversified"),
    ("ESP", "Spain",          "Large diversified"),
    ("IND", "India",          "Emerging industrializer"),
    ("IDN", "Indonesia",      "Emerging industrializer"),
    ("VNM", "Vietnam",        "Emerging industrializer"),
    ("MEX", "Mexico",         "Emerging industrializer"),
    ("TUR", "Turkey",         "Emerging industrializer"),
    ("POL", "Poland",         "Emerging industrializer"),
    ("BRA", "Brazil",         "Emerging industrializer"),
    ("TWN", "Taiwan",         "Edge case"),
    ("ZAF", "South Africa",   "Edge case"),
]

ARCHETYPE_COLOR = {
    "Deep manufacturing":      "#c9a227",  # senape / mustard (house colour)
    "Resource & extraction":   "#7a5c3e",  # brown
    "Financial / service hub": "#3d6b7d",  # slate blue
    "Large diversified":       "#5a7d5a",  # green
    "Emerging industrializer": "#c1672d",  # terracotta
    "Edge case":               "#8a8a8a",  # grey
}
