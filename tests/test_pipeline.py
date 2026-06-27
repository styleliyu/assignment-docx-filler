from pathlib import Path

from scripts.assignment_docx_filler.pipeline import run_pipeline


def test_pipeline_builds_submission_with_one_call(
    docx_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    answers, screenshots = answer_dirs

    result = run_pipeline(
        docx_template,
        answers,
        screenshots,
        tmp_path / "output",
        render_word=False,
    )

    assert result["status"] == "warning"
    assert Path(result["submission"]).exists()
    assert Path(result["slot_map"]).exists()
    assert Path(result["diagnostics"]).exists()


def test_pipeline_stops_before_unsafe_teacher_content(
    unsafe_docx_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    answers, screenshots = answer_dirs

    result = run_pipeline(
        unsafe_docx_template,
        answers,
        screenshots,
        tmp_path / "output",
        render_word=False,
    )

    assert result["status"] == "needs-confirmation"
    assert result["blocking_slots"] == ["q1-code"]
    assert "submission" not in result

    confirmed = run_pipeline(
        unsafe_docx_template,
        answers,
        screenshots,
        tmp_path / "confirmed-output",
        render_word=False,
        confirmed_slots={"q1-code"},
    )

    assert confirmed["status"] == "warning"
    assert Path(confirmed["submission"]).exists()
