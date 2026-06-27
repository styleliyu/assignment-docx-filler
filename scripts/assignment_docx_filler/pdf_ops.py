from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz

from .errors import UnsafeTemplateError


def _read_answer(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text()


def build_pdf(
    template: Path,
    slot_map: dict[str, Any],
    locations: dict[str, Any],
    output: Path,
) -> Path:
    document = fitz.open(template)
    try:
        for question in slot_map["questions"]:
            for slot in question["slots"]:
                has_material = bool(slot.get("source") or slot.get("sources"))
                if not has_material:
                    continue
                if slot["status"] != "confirmed":
                    raise UnsafeTemplateError(f"Slot {slot['id']} is not confirmed")
                location = locations["slots"][slot["id"]]
                page = document[int(location["page"])]
                rectangle = fitz.Rect(location["rect"])
                if rectangle.is_empty or rectangle.height < 12:
                    raise UnsafeTemplateError(f"Slot {slot['id']} has no usable PDF area")
                if slot["kind"] == "code":
                    code = _read_answer(Path(slot["source"]))
                    remaining = -1.0
                    for font_size in (9, 8, 7, 6, 5):
                        remaining = page.insert_textbox(
                            rectangle,
                            code,
                            fontname="cour",
                            fontsize=font_size,
                            color=(0, 0, 0),
                            overlay=True,
                        )
                        if remaining >= 0:
                            break
                    if remaining < 0:
                        raise UnsafeTemplateError(f"Code does not fit PDF slot {slot['id']}")
                else:
                    paths = [Path(value) for value in slot.get("sources", [])]
                    gap = 6
                    height = (rectangle.height - gap * max(0, len(paths) - 1)) / max(1, len(paths))
                    for index, path in enumerate(paths):
                        top = rectangle.y0 + index * (height + gap)
                        image_rect = fitz.Rect(rectangle.x0, top, rectangle.x1, top + height)
                        page.insert_image(image_rect, filename=str(path), keep_proportion=True, overlay=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        document.save(output, garbage=4, deflate=True)
    finally:
        document.close()
    return output

