import json
from pathlib import Path

import fitz

from scripts.assignment_docx_filler.analyze import analyze_template
from scripts.assignment_docx_filler.build import build_submission
from scripts.assignment_docx_filler.materials import map_materials
from scripts.assignment_docx_filler.validation import validate_submission


def test_validate_docx_reports_structural_pass_and_missing_material_warning(
    docx_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"
    analyze_template(docx_template, work_dir)
    answers, screenshots = answer_dirs
    map_materials(work_dir / "slot-map.json", answers, screenshots)
    output = tmp_path / "assignment_completed.docx"
    build_submission(docx_template, work_dir / "slot-map.json", output)
    report_path = tmp_path / "diagnostics.json"

    report = validate_submission(
        docx_template, output, work_dir / "slot-map.json", report_path
    )

    assert report["deliverable"] is True
    assert report["status"] == "warning"
    assert report["checks"]["anchor_order_preserved"] is True
    assert report["checks"]["protected_parts_unchanged"] is True
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8"))["deliverable"] is True


def test_validate_records_rendered_pdf_checks(
    docx_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"
    analyze_template(docx_template, work_dir)
    answers, screenshots = answer_dirs
    map_materials(work_dir / "slot-map.json", answers, screenshots)
    output = tmp_path / "assignment_completed.docx"
    build_submission(docx_template, work_dir / "slot-map.json", output)
    rendered_template = tmp_path / "template.pdf"
    rendered_output = tmp_path / "output.pdf"
    for path, text in ((rendered_template, "HEADER\nBODY\nFOOTER"), (rendered_output, "HEADER\nANSWER\nFOOTER")):
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), text)
        document.save(path)
        document.close()

    report = validate_submission(
        docx_template,
        output,
        work_dir / "slot-map.json",
        tmp_path / "diagnostics.json",
        rendered_template,
        rendered_output,
    )

    assert report["checks"]["word_rendered"] is True
    assert report["checks"]["rendered_pages_nonblank"] is True
    assert not any("has not been recorded" in warning for warning in report["warnings"])

