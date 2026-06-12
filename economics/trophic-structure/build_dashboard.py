"""Inject docs/data.json into the template -> docs/index.html (self-contained)."""
import json
import os

tpl = open("dashboard_template.html").read()
data = open("docs/data.json").read()
d3 = open("node_modules/d3/dist/d3.min.js").read()      # inline D3 (no CDN needed)
html = tpl.replace("__D3__", d3).replace("__DATA_JSON__", data)
with open("docs/index.html", "w") as f:
    f.write(html)
print(f"saved docs/index.html ({os.path.getsize('docs/index.html')/1024:.0f} KB)")
