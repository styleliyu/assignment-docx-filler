from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import question_number_from_name, read_json, write_json

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def _indexed_files(directory: Path | None, images: bool) -> dict[int, list[Path]]:
    result: dict[int, list[Path]] = {}
    if directory is None or not directory.exists():
        return result
    for path in directory.iterdir():
        if not path.is_file():
            continue
        is_image = path.suffix.lower() in IMAGE_SUFFIXES
        if is_image != images:
            continue
        number = question_number_from_name(path.name)
        if number is not None:
            result.setdefault(number, []).append(path.resolve())
    def natural_key(path: Path) -> list[int | str]:
        return [
            int(part) if part.isdigit() else part
            for part in re.split(r"(\d+)", path.name.lower())
        ]

    for values in result.values():
        values.sort(key=natural_key)
    return result


def map_materials(
    slot_map_path: str | Path,
    answers_dir: str | Path | None = None,
    screenshots_dir: str | Path | None = None,
) -> dict[str, Any]:
    slot_map_path = Path(slot_map_path).resolve()
    answers = _indexed_files(Path(answers_dir).resolve() if answers_dir else None, images=False)
    screenshots = _indexed_files(
        Path(screenshots_dir).resolve() if screenshots_dir else None, images=True
    )
    slot_map = read_json(slot_map_path)
    unresolved = [item for item in slot_map.get("unresolved", []) if item.get("reason") != "missing-material"]

    for question in slot_map["questions"]:
        number = int(question["id"].removeprefix("q"))
        for slot in question["slots"]:
            candidates = answers.get(number, []) if slot["kind"] == "code" else screenshots.get(number, [])
            if slot["kind"] == "code":
                if len(candidates) == 1:
                    slot["source"] = str(candidates[0])
                elif len(candidates) > 1:
                    slot["candidates"] = [str(path) for path in candidates]
            else:
                if candidates:
                    slot["sources"] = [str(path) for path in candidates]

            if slot["status"] in {"needs_confirmation", "unsupported"}:
                continue
            if not candidates:
                slot["status"] = "missing-material"
                unresolved.append({"slot_id": slot["id"], "reason": "missing-material"})
            elif slot["kind"] == "code" and len(candidates) > 1:
                slot["status"] = "needs_confirmation"
                unresolved.append({"slot_id": slot["id"], "reason": "multiple-answer-files"})
            else:
                slot["status"] = "confirmed"

    slot_map["unresolved"] = unresolved
    write_json(slot_map_path, slot_map)
    return slot_map
