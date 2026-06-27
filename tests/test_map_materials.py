from pathlib import Path

from scripts.assignment_docx_filler.analyze import analyze_template
from scripts.assignment_docx_filler.materials import map_materials


def test_map_materials_prefers_numbered_user_files(
    docx_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"
    analyze_template(docx_template, work_dir)
    answers, screenshots = answer_dirs

    slot_map = map_materials(work_dir / "slot-map.json", answers, screenshots)

    q1_code, q1_screenshots = slot_map["questions"][0]["slots"]
    assert q1_code["status"] == "confirmed"
    assert q1_code["source"].endswith("q1.py")
    assert q1_screenshots["status"] == "confirmed"
    assert [Path(path).name for path in q1_screenshots["sources"]] == ["q1-1.png"]
    assert slot_map["questions"][1]["slots"][0]["status"] == "missing-material"


def test_map_materials_sorts_multiple_screenshots_by_numeric_suffix(
    docx_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"
    analyze_template(docx_template, work_dir)
    answers, screenshots = answer_dirs
    (screenshots / "q1-10.png").write_bytes((screenshots / "q1-1.png").read_bytes())
    (screenshots / "q1-2.png").write_bytes((screenshots / "q1-1.png").read_bytes())

    slot_map = map_materials(work_dir / "slot-map.json", answers, screenshots)

    screenshot_slot = slot_map["questions"][0]["slots"][1]
    assert [Path(path).name for path in screenshot_slot["sources"]] == [
        "q1-1.png",
        "q1-2.png",
        "q1-10.png",
    ]
