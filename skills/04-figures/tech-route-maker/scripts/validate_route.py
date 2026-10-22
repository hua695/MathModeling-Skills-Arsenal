import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tech_route_maker.validator import format_validation_result, validate_file  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_route.py <tech-route.json>")
        return 2
    route, errors, warnings, report = validate_file(sys.argv[1])
    print(format_validation_result(route, errors, warnings, report))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
