from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from typing import Any

import fitz
from lxml import etree

from .analyze import NS, _anchor_kind, _paragraph_text, _question_number
from .common import read_json, sha256_file, write_json

ALLOWED_CHANGED_PARTS = {
    "[Content_Types].xml",
    "word/document.xml",
    "word/_rels/document.xml.rels",
}


def _part_hashes(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as package:
        return {
            name: hashlib.sha256(package.read(name)).hexdigest()
            for name in package.namelist()
        }


def _docx_markers(path: Path) -> list[tuple[str, str]]:
    with zipfile.ZipFile(path) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    markers: list[tuple[str, str]] = []
    for paragraph in root.findall(".//w:body/w:p", NS):
        text = _paragraph_text(paragraph)
        question = _question_number(text)
        if question is not None:
            markers.append(("question", str(question)))
        anchor = _anchor_kind(text)
        if anchor:
            markers.append((anchor, text))
    return markers


def _validate_docx(
    template: Path, submission: Path, slot_map: dict[str, Any]
) -> tuple[dict[str, bool], list[str], list[str]]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    warnings: list[str] = []
    try:
        template_parts = _part_hashes(template)
        submission_parts = _part_hashes(submission)
        with zipfile.ZipFile(submission) as package:
            etree.fromstring(package.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, etree.XMLSyntaxError) as error:
        return {"package_opens": False}, [f"Invalid submission package: {error}"], warnings

    checks["package_opens"] = True
    changed_protected = [
        name
        for name, digest in template_parts.items()
        if name not in ALLOWED_CHANGED_PARTS and submission_parts.get(name) != digest
    ]
    missing_parts = [name for name in template_parts if name not in submission_parts]
    checks["protected_parts_unchanged"] = not changed_protected and not missing_parts
    if changed_protected:
        errors.append("Protected DOCX parts changed: " + ", ".join(changed_protected))
    if missing_parts:
        errors.append("Original DOCX parts are missing: " + ", ".join(missing_parts))

    try:
        checks["anchor_order_preserved"] = _docx_markers(template) == _docx_markers(submission)
    except Exception as error:
        checks["anchor_order_preserved"] = False
        errors.append(f"Cannot compare question and anchor order: {error}")
    if not checks["anchor_order_preserved"] and not any("anchor order" in item for item in errors):
        errors.append("Question or answer-anchor order changed")

    with zipfile.ZipFile(submission) as package:
        document_text = "".join(
            etree.fromstring(package.read("word/document.xml")).itertext()
        )
        media_hashes = {
            hashlib.sha256(package.read(name)).hexdigest()
            for name in package.namelist()
            if name.startswith("word/media/")
        }
    all_materials_present = True
    for question in slot_map["questions"]:
        for slot in question["slots"]:
            if slot["status"] == "missing-material":
                warnings.append(f"Missing material for {slot['id']}")
                continue
            if slot["status"] != "confirmed":
                if slot.get("source") or slot.get("sources"):
                    errors.append(f"Material exists but slot is not confirmed: {slot['id']}")
                    all_materials_present = False
                continue
            if slot["kind"] == "code":
                source_text = Path(slot["source"]).read_text(encoding="utf-8-sig").strip()
                if source_text not in document_text:
                    errors.append(f"Code material is missing from {slot['id']}")
                    all_materials_present = False
            else:
                for source in slot.get("sources", []):
                    digest = hashlib.sha256(Path(source).read_bytes()).hexdigest()
                    if digest not in media_hashes:
                        errors.append(f"Screenshot material is missing from {slot['id']}: {source}")
                        all_materials_present = False
    checks["confirmed_materials_present"] = all_materials_present
    warnings.append("Microsoft Word visual validation has not been recorded in this report")
    return checks, errors, warnings


def _validate_pdf(
    template: Path, submission: Path, slot_map: dict[str, Any]
) -> tuple[dict[str, bool], list[str], list[str]]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    warnings = ["PDF fallback cannot provide DOCX template fidelity"]
    try:
        with fitz.open(template) as original, fitz.open(submission) as completed:
            checks["package_opens"] = True
            checks["page_count_preserved"] = original.page_count == completed.page_count
    except Exception as error:
        return {"package_opens": False}, [f"Cannot open PDF output: {error}"], warnings
    if not checks["page_count_preserved"]:
        errors.append("PDF page count changed")
    for question in slot_map["questions"]:
        for slot in question["slots"]:
            if slot["status"] == "missing-material":
                warnings.append(f"Missing material for {slot['id']}")
    return checks, errors, warnings


def _validate_renders(
    template_render: Path, submission_render: Path
) -> tuple[dict[str, bool], list[str], list[str]]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    warnings: list[str] = []
    try:
        original = fitz.open(template_render)
        completed = fitz.open(submission_render)
    except Exception as error:
        return {"word_rendered": False}, [f"Cannot open rendered PDF: {error}"], warnings
    try:
        checks["word_rendered"] = True
        completed_sizes = [(round(page.rect.width, 2), round(page.rect.height, 2)) for page in completed]
        checks["rendered_page_sizes_valid"] = bool(completed_sizes) and all(
            width > 0 and height > 0 for width, height in completed_sizes
        )
        nonblank = []
        for page in completed:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25), colorspace=fitz.csGRAY)
            nonblank.append(bool(page.get_text().strip()) or min(pixmap.samples, default=255) < 250)
        checks["rendered_pages_nonblank"] = bool(nonblank) and all(nonblank)
        if not checks["rendered_pages_nonblank"]:
            errors.append("Word rendering contains a blank page")
        if original.page_count != completed.page_count:
            warnings.append(
                f"Word pagination changed from {original.page_count} to {completed.page_count} pages"
            )
        if original.page_count and completed.page_count:
            original_size = (round(original[0].rect.width, 2), round(original[0].rect.height, 2))
            if completed_sizes[0] != original_size:
                errors.append("Rendered page size changed")
                checks["rendered_page_size_preserved"] = False
            else:
                checks["rendered_page_size_preserved"] = True
    finally:
        original.close()
        completed.close()
    return checks, errors, warnings


def validate_submission(
    template: str | Path,
    submission: str | Path,
    slot_map_path: str | Path,
    report_path: str | Path,
    template_render: str | Path | None = None,
    submission_render: str | Path | None = None,
) -> dict[str, Any]:
    template = Path(template).resolve()
    submission = Path(submission).resolve()
    slot_map = read_json(Path(slot_map_path).resolve())
    errors: list[str] = []
    warnings: list[str] = []

    template_hash_matches = sha256_file(template) == slot_map["template"]["sha256"]
    if not template_hash_matches:
        errors.append("Original template hash no longer matches the analyzed template")
    output_is_separate = template != submission
    if not output_is_separate:
        errors.append("Submission overwrote the original template")
    if not submission.exists():
        errors.append("Submission file does not exist")
        checks = {
            "template_hash_matches": template_hash_matches,
            "output_is_separate": output_is_separate,
        }
    else:
        mode = slot_map["template"]["mode"]
        if mode == "docx":
            mode_checks, mode_errors, mode_warnings = _validate_docx(
                template, submission, slot_map
            )
        else:
            mode_checks, mode_errors, mode_warnings = _validate_pdf(
                template, submission, slot_map
            )
        checks = {
            "template_hash_matches": template_hash_matches,
            "output_is_separate": output_is_separate,
            **mode_checks,
        }
        errors.extend(mode_errors)
        warnings.extend(mode_warnings)

    if template_render is not None and submission_render is not None:
        render_checks, render_errors, render_warnings = _validate_renders(
            Path(template_render).resolve(), Path(submission_render).resolve()
        )
        checks.update(render_checks)
        errors.extend(render_errors)
        warnings = [
            warning
            for warning in warnings
            if "has not been recorded" not in warning
        ]
        warnings.extend(render_warnings)
    elif template_render is not None or submission_render is not None:
        warnings.append("Both template and submission renders are required for visual checks")

    status = "fail" if errors else "warning" if warnings else "pass"
    report = {
        "schema_version": 1,
        "status": status,
        "deliverable": not errors,
        "template": str(template),
        "submission": str(submission),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }
    write_json(Path(report_path).resolve(), report)
    return report
