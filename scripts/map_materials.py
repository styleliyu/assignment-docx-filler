from __future__ import annotations

import argparse
import json

from assignment_docx_filler.materials import map_materials


def main() -> int:
    parser = argparse.ArgumentParser(description="Map answer files and screenshots to slots.")
    parser.add_argument("slot_map")
    parser.add_argument("--answers")
    parser.add_argument("--screenshots")
    args = parser.parse_args()
    result = map_materials(args.slot_map, args.answers, args.screenshots)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

