import sys

from route_common import layout_family, load_route, normalize_route, save_text


def m_id(value):
    return str(value).replace("-", "_").replace(".", "_")


def m_label(value):
    return str(value or "").replace('"', "'")


def make_mermaid(route):
    route = normalize_route(route)
    direction = "TB" if layout_family(route.get("layout")) in {"vertical", "a4-stage"} else "LR"
    lines = [f"flowchart {direction}", f'  title["{m_label(route["title"])}"]']
    for stage in route["stages"]:
        lines.append(f'  subgraph {m_id(stage["id"])}["{m_label(stage["title"])}"]')
        for node in stage["nodes"]:
            label = m_label(node["label"])
            lines.append(f'    {m_id(node["id"])}["{label}"]')
        lines.append("  end")
    for edge in route["edges"]:
        if not edge.get("valid", True):
            continue
        lines.append(f'  {m_id(edge["from"])} -->|{m_label(edge.get("label", "next"))}| {m_id(edge["to"])}')
    lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        print("Usage: python render_mermaid.py <tech-route.json> <output.mmd>")
        return 2
    route = load_route(sys.argv[1])
    save_text(sys.argv[2], make_mermaid(route))
    print(f"Wrote {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
