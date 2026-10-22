import sys
from pathlib import Path

from render_drawio import make_drawio
from route_common import load_route


def main():
    if len(sys.argv) != 3:
        print("Usage: python render_drawio_code.py <tech-route.json> <output.drawio-code.xml>")
        return 2

    route = load_route(sys.argv[1])
    output = Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(make_drawio(route))
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
