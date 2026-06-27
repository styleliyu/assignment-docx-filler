import json
from pathlib import Path

from scripts.assignment_docx_filler.analyze import analyze_template


def test_analyze_docx_creates_question_slots_and_private_locations(
    docx_template: Path, tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"

    slot_map = analyze_template(docx_template, work_dir)

    assert slot_map["schema_version"] == 1
    assert slot_map["template"]["mode"] == "docx"
    assert slot_map["template"]["fidelity"] == "high"
    assert [question["id"] for question in slot_map["questions"]] == ["q1", "q2"]
    assert [slot["kind"] for slot in slot_map["questions"][0]["slots"]] == [
        "code",
        "screenshots",
    ]
    assert all(slot["confidence"] >= 0.85 for slot in slot_map["questions"][0]["slots"])
    assert (work_dir / "slot-map.json").exists()
    locations = json.loads((work_dir / "locations.json").read_text(encoding="utf-8"))
    assert "q1-code" in locations["slots"]
    assert "body_start" in locations["slots"]["q1-code"]


def test_analyze_marks_nonempty_teacher_region_unresolved(
    unsafe_docx_template: Path, tmp_path: Path
) -> None:
    slot_map = analyze_template(unsafe_docx_template, tmp_path / "work")

    code_slot = slot_map["questions"][0]["slots"][0]
    assert code_slot["status"] == "needs_confirmation"
    assert slot_map["unresolved"][0]["reason"] == "nonempty-region"


def test_analyze_pdf_uses_lower_fidelity_fallback(pdf_template: Path, tmp_path: Path) -> None:
    slot_map = analyze_template(pdf_template, tmp_path / "work")

    assert slot_map["template"]["mode"] == "pdf"
    assert slot_map["template"]["fidelity"] == "fallback"
    assert [slot["kind"] for slot in slot_map["questions"][0]["slots"]] == [
        "code",
        "screenshots",
    ]

