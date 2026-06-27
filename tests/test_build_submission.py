import hashlib
import zipfile
from pathlib import Path

import fitz
import pytest
from lxml import etree

from scripts.assignment_docx_filler.analyze import analyze_template
from scripts.assignment_docx_filler.build import build_submission
from scripts.assignment_docx_filler.errors import UnsafeTemplateError
from scripts.assignment_docx_filler.materials import map_materials


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _document_text(path: Path) -> str:
    with zipfile.ZipFile(path) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    return "".join(root.itertext())


def test_build_docx_inserts_code_and_screenshot_without_changing_template(
    docx_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    original_hash = _sha256(docx_template)
    work_dir = tmp_path / "work"
    analyze_template(docx_template, work_dir)
    answers, screenshots = answer_dirs
    map_materials(work_dir / "slot-map.json", answers, screenshots)
    output = tmp_path / "output" / "assignment_completed.docx"

    result = build_submission(docx_template, work_dir / "slot-map.json", output)

    assert result == output
    assert _sha256(docx_template) == original_hash
    assert 'print("hello")' in _document_text(output)
    with zipfile.ZipFile(output) as package:
        assert any(name.startswith("word/media/") for name in package.namelist())
        assert package.read("word/header1.xml") == zipfile.ZipFile(docx_template).read(
            "word/header1.xml"
        )


def test_build_refuses_unconfirmed_nonempty_teacher_content(
    unsafe_docx_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"
    analyze_template(unsafe_docx_template, work_dir)
    answers, screenshots = answer_dirs
    map_materials(work_dir / "slot-map.json", answers, screenshots)

    with pytest.raises(UnsafeTemplateError, match="q1-code"):
        build_submission(
            unsafe_docx_template,
            work_dir / "slot-map.json",
            tmp_path / "unsafe_completed.docx",
        )


def test_build_pdf_fallback_preserves_page_count_and_adds_answer(
    pdf_template: Path, answer_dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    work_dir = tmp_path / "work"
    analyze_template(pdf_template, work_dir)
    answers, screenshots = answer_dirs
    map_materials(work_dir / "slot-map.json", answers, screenshots)
    output = tmp_path / "assignment_completed.pdf"

    build_submission(pdf_template, work_dir / "slot-map.json", output)

    with fitz.open(pdf_template) as original, fitz.open(output) as completed:
        assert completed.page_count == original.page_count
        assert 'print("hello")' in completed[0].get_text()

