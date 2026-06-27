from __future__ import annotations

import argparse
import json

from assignment_docx_filler.analyze import analyze_template


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze DOCX or PDF assignment answer slots.")
    parser.add_argument("template")
    parser.add_argument("--work-dir", required=True)
    args = parser.parse_args()
    result = analyze_template(args.template, args.work_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

