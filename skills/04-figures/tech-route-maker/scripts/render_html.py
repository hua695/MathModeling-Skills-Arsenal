import json
import sys

from render_svg import make_svg
from route_common import html_escape, load_route, normalize_route, save_text


def make_html(route):
    route = normalize_route(route)
    svg = make_svg(route)
    data = json.dumps(route, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_escape(route["title"])}</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: #1f2937; background: #f8fafc; }}
    .wrap {{ display: grid; grid-template-columns: minmax(0, 1fr) 340px; min-height: 100vh; }}
    .diagram {{ overflow: auto; padding: 24px; background: #ffffff; }}
    .panel {{ border-left: 1px solid #e5e7eb; padding: 20px; background: #f8fafc; }}
    .panel h2 {{ margin: 0 0 8px; font-size: 18px; }}
    .panel p {{ line-height: 1.45; }}
    .evidence {{ margin-top: 12px; padding: 10px; border: 1px solid #e5e7eb; background: #fff; border-radius: 8px; }}
    .muted {{ color: #64748b; font-size: 13px; }}
    svg {{ max-width: none; }}
  </style>
</head>
<body>
<div class="wrap">
  <main class="diagram">{svg}</main>
  <aside class="panel">
    <h2 id="node-title">Select a node</h2>
    <p id="node-detail" class="muted">Click any diagram node to inspect its detail and evidence.</p>
    <div id="node-evidence"></div>
  </aside>
</div>
<script>
const route = {data};
const nodes = {{}};
for (const stage of route.stages) {{
  for (const node of stage.nodes) {{
    nodes[node.id] = node;
  }}
}}
document.querySelectorAll("[data-node]").forEach(el => {{
  el.addEventListener("click", () => {{
    const node = nodes[el.dataset.node];
    if (!node) return;
    document.getElementById("node-title").textContent = node.label;
    document.getElementById("node-detail").textContent = node.detail || "No detail recorded.";
    const evidence = node.evidence || [];
    document.getElementById("node-evidence").innerHTML = evidence.map(item => {{
      const path = item.path ? `<div><b>Path:</b> ${{item.path}}</div>` : "";
      const symbol = item.symbol ? `<div><b>Symbol:</b> ${{item.symbol}}</div>` : "";
      const note = item.note ? `<div><b>Note:</b> ${{item.note}}</div>` : "";
      return `<div class="evidence"><div><b>Kind:</b> ${{item.kind || "unknown"}}</div>${{path}}${{symbol}}${{note}}</div>`;
    }}).join("") || '<p class="muted">No evidence recorded.</p>';
  }});
}});
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        print("Usage: python render_html.py <tech-route.json> <output.html>")
        return 2
    save_text(sys.argv[2], make_html(load_route(sys.argv[1])))
    print(f"Wrote {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
