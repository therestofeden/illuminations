"""Tile the 30 single-country network PNGs into one contact sheet, ordered by
chain length (Farmer's measure, longest first)."""
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from countries import COUNTRIES

name_of = {c: n for c, n, _ in COUNTRIES}
order = (pd.read_csv("icio_country_year.csv").query("year == 2019")
         .sort_values("farmer_depth", ascending=False))
codes = order["code"].tolist()

COLS, THUMB_W = 5, 520
pad, top = 16, 34
imgs = {c: Image.open(f"figures/networks/{c}.png").convert("RGB") for c in codes}
ar = imgs[codes[0]].height / imgs[codes[0]].width
THUMB_H = int(THUMB_W * ar)
rows = (len(codes) + COLS - 1) // COLS
W = COLS * THUMB_W + (COLS + 1) * pad
H = rows * (THUMB_H + top) + pad
sheet = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 19)
except Exception:
    font = ImageFont.load_default()

for k, c in enumerate(codes):
    r, col = divmod(k, COLS)
    x = pad + col * (THUMB_W + pad)
    y = pad + r * (THUMB_H + top)
    d = order[order.code == c].iloc[0]
    draw.text((x + 4, y), f"{name_of[c]}  {d.farmer_depth:.2f} = {d.home_depth:.2f} + {d.abroad_depth:.2f}",
              fill="#222", font=font)
    sheet.paste(imgs[c].resize((THUMB_W, THUMB_H)), (x, y + top))

sheet.save("figures/networks_contact_sheet.png")
print("saved figures/networks_contact_sheet.png", sheet.size)
