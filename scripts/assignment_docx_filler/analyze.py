from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

import fitz
from lxml import etree

from .common import normalize_text, sha256_file, write_json
from .errors import UnsupportedTemplateError

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W_TAG = f"{{{W_NS}}}"

CODE_ANCHORS = {"代码", "源代码", "程序", "程序代码"}
SCREENSHOT_ANCHORS = {"运行结果", "实验结果", "执行结果", "截图"}
PLACEHOLDERS = {
    "在此填写代码",
    "在此粘贴代码",
    "请填写代码",
    "请粘贴代码",
    "在此插入截图",
    "请插入截图",
    "粘贴运行结果",
}
QUESTION_RE = re.compile(r"^第([一二三四五六七八九十百\d]+)题")
NUMBERED_RE = re.compile(r"^(\d+)[、.\)]")


def _paragraph_text(element: etree._Element) -> str:
    values: list[str] = []
    for node in element.iter():
        if node.tag == W_TAG + "t" and node.text:
            values.append(node.text)
        elif node.tag in {W_TAG + "tab"}:
            values.append("\t")
        elif node.tag in {W_TAG + "br", W_TAG + "cr"}:
            values.append("\n")
    return "".join(values)


def _chinese_number(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if value == "十":
        return 10
    if "十" in value:
        left, right = value.split("十", 1)
        return digits.get(left, 1) * 10 + digits.get(right, 0)
    return digits.get(value)


def _question_number(text: str) -> int | None:
    normalized = normalize_text(text)
    match = QUESTION_RE.match(normalized)
    if match:
        return _chinese_number(match.group(1))
    match = NUMBERED_RE.match(normalized)
    return int(match.group(1)) if match else None


def _anchor_kind(text: str) -> str | None:
    normalized = normalize_text(text).rstrip(":")
    if normalized in CODE_ANCHORS:
        return "code"
    if normalized in SCREENSHOT_ANCHORS:
        return "screenshots"
    return None


def _is_replaceable(text: str) -> bool:
    normalized = normalize_text(text).strip("()（）[]【】")
    return not normalized or normalized in PLACEHOLDERS


def _validate_docx(path: Path) -> tuple[zipfile.ZipFile, etree._Element]:
    if path.suffix.lower() == ".docm":
        raise UnsupportedTemplateError("DOCM templates are not supported")
    try:
        package = zipfile.ZipFile(path)
        names = set(package.namelist())
        if "word/document.xml" not in names or "[Content_Types].xml" not in names:
            package.close()
            raise UnsupportedTemplateError("The file is not a valid DOCX package")
        if any(name.lower().endswith("vbaproject.bin") for name in names):
            package.close()
            raise UnsupportedTemplateError("Macro-enabled templates are not supported")
        root = etree.fromstring(package.read("word/document.xml"))
    except (zipfile.BadZipFile, etree.XMLSyntaxError) as error:
        raise UnsupportedTemplateError(f"Damaged DOCX package: {error}") from error
    revisions = root.xpath(".//w:ins | .//w:del | .//w:moveFrom | .//w:moveTo", namespaces=NS)
    if revisions:
        package.close()
        raise UnsupportedTemplateError("Resolve tracked changes before filling the template")
    return package, root


def _analyze_docx(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    package, root = _validate_docx(path)
    package.close()
    body = root.find("w:body", NS)
    if body is None:
        raise UnsupportedTemplateError("DOCX document body is missing")

    children = list(body)
    document_end = next(
        (index for index, child in enumerate(children) if child.tag == W_TAG + "sectPr"),
        len(children),
    )
    paragraph_rows: list[dict[str, Any]] = []
    unsupported_indexes: set[int] = set()
    for body_index, child in enumerate(children):
        if child.tag == W_TAG + "p":
            paragraph_rows.append(
                {"body_index": body_index, "text": _paragraph_text(child), "element": child}
            )
        elif child.tag == W_TAG + "tbl":
            table_text = _paragraph_text(child)
            if _anchor_kind(table_text):
                unsupported_indexes.add(body_index)

    headings: list[dict[str, Any]] = []
    anchors: list[dict[str, Any]] = []
    for row in paragraph_rows:
        number = _question_number(row["text"])
        if number is not None:
            headings.append({**row, "number": number})
        kind = _anchor_kind(row["text"])
        if kind:
            anchors.append({**row, "kind": kind})

    if not anchors:
        raise UnsupportedTemplateError("No supported answer anchors were found")

    questions_by_number: dict[int, dict[str, Any]] = {}
    locations: dict[str, Any] = {"schema_version": 1, "mode": "docx", "slots": {}}
    unresolved: list[dict[str, Any]] = []
    for anchor_position, anchor in enumerate(anchors):
        preceding = [item for item in headings if item["body_index"] < anchor["body_index"]]
        heading = preceding[-1] if preceding else None
        number = heading["number"] if heading else len(questions_by_number) + 1
        question = questions_by_number.setdefault(
            number,
            {
                "id": f"q{number}",
                "label": heading["text"] if heading else f"第{number}题",
                "slots": [],
            },
        )
        next_anchor_index = anchors[anchor_position + 1]["body_index"] if anchor_position + 1 < len(anchors) else document_end
        next_headings = [item["body_index"] for item in headings if item["body_index"] > anchor["body_index"]]
        next_heading_index = min(next_headings) if next_headings else document_end
        region_end = min(next_anchor_index, next_heading_index)
        region_start = anchor["body_index"] + 1
        region_rows = [
            row for row in paragraph_rows if region_start <= row["body_index"] < region_end
        ]
        nonreplaceable = [row["text"] for row in region_rows if not _is_replaceable(row["text"])]
        crosses_table = any(region_start <= index < region_end for index in unsupported_indexes)
        slot_id = f"q{number}-{'code' if anchor['kind'] == 'code' else 'screenshots'}"
        confidence = 0.96 if heading and region_rows else 0.82
        status = "analyzed"
        if nonreplaceable:
            status = "needs_confirmation"
            unresolved.append(
                {"slot_id": slot_id, "reason": "nonempty-region", "content": nonreplaceable}
            )
        elif crosses_table:
            status = "unsupported"
            unresolved.append({"slot_id": slot_id, "reason": "table-region"})
        elif confidence < 0.85:
            status = "needs_confirmation"
            unresolved.append({"slot_id": slot_id, "reason": "low-confidence"})

        slot = {
            "id": slot_id,
            "kind": anchor["kind"],
            "anchor": anchor["text"],
            "confidence": confidence,
            "status": status,
        }
        question["slots"].append(slot)
        locations["slots"][slot_id] = {
            "anchor_body_index": anchor["body_index"],
            "body_start": region_start,
            "body_end": region_end,
        }

    questions = [questions_by_number[number] for number in sorted(questions_by_number)]
    return questions, unresolved, locations


def _pdf_lines(document: fitz.Document) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page_number, page in enumerate(document):
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                text = "".join(span.get("text", "") for span in line.get("spans", []))
                if text.strip():
                    rows.append(
                        {"page": page_number, "bbox": list(line["bbox"]), "text": text.strip()}
                    )
    return rows


def _analyze_pdf(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    try:
        document = fitz.open(path)
    except Exception as error:
        raise UnsupportedTemplateError(f"Cannot open PDF: {error}") from error
    if document.needs_pass:
        document.close()
        raise UnsupportedTemplateError("Encrypted PDF templates are not supported")
    rows = _pdf_lines(document)
    page_rects = [list(page.rect) for page in document]
    document.close()
    headings = [{**row, "number": _question_number(row["text"])} for row in rows]
    headings = [row for row in headings if row["number"] is not None]
    anchors = [{**row, "kind": _anchor_kind(row["text"])} for row in rows]
    anchors = [row for row in anchors if row["kind"]]
    if not anchors:
        raise UnsupportedTemplateError("No supported answer anchors were found in the PDF")

    questions_by_number: dict[int, dict[str, Any]] = {}
    locations: dict[str, Any] = {"schema_version": 1, "mode": "pdf", "slots": {}}
    unresolved: list[dict[str, Any]] = []
    for index, anchor in enumerate(anchors):
        preceding = [
            row
            for row in headings
            if (row["page"], row["bbox"][1]) < (anchor["page"], anchor["bbox"][1])
        ]
        heading = preceding[-1] if preceding else None
        number = heading["number"] if heading else len(questions_by_number) + 1
        question = questions_by_number.setdefault(
            number,
            {"id": f"q{number}", "label": heading["text"] if heading else f"第{number}题", "slots": []},
        )
        slot_id = f"q{number}-{'code' if anchor['kind'] == 'code' else 'screenshots'}"
        page_number = anchor["page"]
        page_bottom = page_rects[page_number][3] - 36
        following = [
            row
            for row in anchors[index + 1 :] + headings
            if row["page"] == page_number and row["bbox"][1] > anchor["bbox"][3]
        ]
        bottom = min((row["bbox"][1] - 4 for row in following), default=page_bottom)
        top = anchor["bbox"][3] + 4
        confidence = 0.9 if heading and bottom > top + 20 else 0.78
        status = "analyzed" if confidence >= 0.85 else "needs_confirmation"
        if status != "analyzed":
            unresolved.append({"slot_id": slot_id, "reason": "low-confidence"})
        question["slots"].append(
            {
                "id": slot_id,
                "kind": anchor["kind"],
                "anchor": anchor["text"],
                "confidence": confidence,
                "status": status,
            }
        )
        locations["slots"][slot_id] = {
            "page": page_number,
            "rect": [max(36, anchor["bbox"][0]), top, page_rects[page_number][2] - 36, bottom],
        }
    questions = [questions_by_number[number] for number in sorted(questions_by_number)]
    return questions, unresolved, locations


def analyze_template(template: str | Path, work_dir: str | Path) -> dict[str, Any]:
    template = Path(template).resolve()
    work_dir = Path(work_dir).resolve()
    suffix = template.suffix.lower()
    if suffix == ".docx":
        questions, unresolved, locations = _analyze_docx(template)
        mode, fidelity = "docx", "high"
    elif suffix == ".pdf":
        questions, unresolved, locations = _analyze_pdf(template)
        mode, fidelity = "pdf", "fallback"
    else:
        raise UnsupportedTemplateError("Only DOCX and PDF templates are supported")

    slot_map = {
        "schema_version": 1,
        "template": {
            "path": str(template),
            "sha256": sha256_file(template),
            "mode": mode,
            "fidelity": fidelity,
        },
        "questions": questions,
        "unresolved": unresolved,
    }
    write_json(work_dir / "slot-map.json", slot_map)
    write_json(work_dir / "locations.json", locations)
    return slot_map
