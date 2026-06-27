from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from collections.abc import Iterable
from typing import Any

from .analyze import analyze_template
from .build import build_submission
from .common import write_json
from .materials import map_materials
from .validation import validate_submission


def _render_word(input_path: Path, output_path: Path) -> None:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        raise RuntimeError("PowerShell is not available")
    script = Path(__file__).parents[1] / "render_word.ps1"
    subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Input",
            str(input_path),
            "-Output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def run_pipeline(
    template: str | Path,
    answers_dir: str | Path | None,
    screenshots_dir: str | Path | None,
    output_dir: str | Path,
    *,
    render_word: bool | None = None,
    confirmed_slots: Iterable[str] = (),
) -> dict[str, Any]:
    template = Path(template).resolve()
    output_dir = Path(output_dir).resolve()
    work_dir = output_dir / "work"
    output_dir.mkdir(parents=True, exist_ok=True)

    analyze_template(template, work_dir)
    slot_map_path = work_dir / "slot-map.json"
    slot_map = map_materials(slot_map_path, answers_dir, screenshots_dir)
    confirmations = set(confirmed_slots)
    confirmed_ids: set[str] = set()
    for question in slot_map["questions"]:
        for slot in question["slots"]:
            if slot["id"] not in confirmations:
                continue
            if slot["status"] == "needs_confirmation" and (
                slot.get("source") or slot.get("sources") or slot.get("candidates")
            ):
                if slot.get("candidates") and not slot.get("source"):
                    continue
                slot["status"] = "confirmed"
                slot["allow_nonempty_region"] = True
                confirmed_ids.add(slot["id"])
    slot_map["unresolved"] = [
        item for item in slot_map["unresolved"] if item.get("slot_id") not in confirmed_ids
    ]
    if confirmed_ids:
        write_json(slot_map_path, slot_map)
    blocking_slots = [
        slot["id"]
        for question in slot_map["questions"]
        for slot in question["slots"]
        if slot["status"] in {"needs_confirmation", "unsupported"}
        and (slot.get("source") or slot.get("sources") or slot.get("candidates"))
    ]
    if blocking_slots:
        return {
            "status": "needs-confirmation",
            "slot_map": str(slot_map_path),
            "blocking_slots": blocking_slots,
        }

    suffix = ".docx" if slot_map["template"]["mode"] == "docx" else ".pdf"
    submission = output_dir / f"{template.stem}_completed{suffix}"
    build_submission(template, slot_map_path, submission)

    if render_word is None:
        render_word = platform.system() == "Windows" and suffix == ".docx"
    render_warning: str | None = None
    template_render: Path | None = None
    submission_render: Path | None = None
    if render_word and suffix == ".docx":
        template_render = work_dir / "template-render.pdf"
        submission_render = work_dir / "submission-render.pdf"
        try:
            _render_word(template, template_render)
            _render_word(submission, submission_render)
        except Exception as error:
            template_render = submission_render = None
            render_warning = f"Word rendering failed: {error}"

    diagnostics = output_dir / "diagnostics.json"
    report = validate_submission(
        template,
        submission,
        slot_map_path,
        diagnostics,
        template_render,
        submission_render,
    )
    if render_warning:
        report["warnings"].append(render_warning)
        report["status"] = "warning" if report["deliverable"] else "fail"
        write_json(diagnostics, report)
    return {
        "status": report["status"],
        "submission": str(submission),
        "slot_map": str(slot_map_path),
        "diagnostics": str(diagnostics),
        "rendered_pdf": str(submission_render) if submission_render else None,
    }
