from __future__ import annotations

import argparse
import json

from assignment_docx_filler.pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze, fill, render, and validate an assignment template in one command."
    )
    parser.add_argument("template")
    parser.add_argument("--answers")
    parser.add_argument("--screenshots")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument(
        "--no-word-render",
        action="store_true",
        help="Skip Microsoft Word COM rendering and visual checks.",
    )
    parser.add_argument(
        "--confirm",
        action="append",
        default=[],
        metavar="SLOT_ID",
        help="Confirm a reviewed non-empty or low-confidence paragraph slot.",
    )
    args = parser.parse_args()
    result = run_pipeline(
        args.template,
        args.answers,
        args.screenshots,
        args.output_dir,
        render_word=False if args.no_word_render else None,
        confirmed_slots=args.confirm,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "needs-confirmation":
        return 2
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
