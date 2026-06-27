from __future__ import annotations

import argparse
import json

from assignment_docx_filler.validation import validate_submission


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a filled assignment submission.")
    parser.add_argument("--template", required=True)
    parser.add_argument("--submission", required=True)
    parser.add_argument("--slot-map", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--template-render")
    parser.add_argument("--submission-render")
    args = parser.parse_args()
    report = validate_submission(
        args.template,
        args.submission,
        args.slot_map,
        args.report,
        args.template_render,
        args.submission_render,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["deliverable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
