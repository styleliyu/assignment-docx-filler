from __future__ import annotations

import argparse

from assignment_docx_filler.build import build_submission


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a filled assignment submission copy.")
    parser.add_argument("--template", required=True)
    parser.add_argument("--slot-map", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = build_submission(args.template, args.slot_map, args.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

