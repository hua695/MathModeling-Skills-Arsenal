import sys

from render_mermaid import make_mermaid
from route_common import load_route, normalize_route, save_text


def make_markdown(route):
    route = normalize_route(route)
    lines = [f"# {route['title']}", ""]
    if route.get("subtitle"):
        lines.extend([route["subtitle"], ""])
    lines.extend(["```mermaid", make_mermaid(route).rstrip(), "```", ""])
    lines.append("## Route Evidence")
    lines.append("")
    lines.append("| Stage | Node | Evidence |")
    lines.append("|---|---|---|")
    for stage in route["stages"]:
        for node in stage["nodes"]:
            evidence = []
            for item in node.get("evidence", []):
                parts = [item.get("kind", "unknown")]
                if item.get("path"):
                    parts.append(item["path"])
                if item.get("symbol"):
                    parts.append(item["symbol"])
                if item.get("note"):
                    parts.append(item["note"])
                evidence.append(" - ".join(parts))
            lines.append(f"| {stage['title']} | {node['label']} | {'<br>'.join(evidence) if evidence else 'No evidence recorded'} |")
    lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        print("Usage: python render_markdown.py <tech-route.json> <output.md>")
        return 2
    save_text(sys.argv[2], make_markdown(load_route(sys.argv[1])))
    print(f"Wrote {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
