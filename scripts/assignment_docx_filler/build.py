from __future__ import annotations

from pathlib import Path

from .common import read_json, sha256_file
from .docx_ops import build_docx
from .errors import MappingError
from .pdf_ops import build_pdf


def build_submission(
    template: str | Path, slot_map_path: str | Path, output: str | Path
) -> Path:
    template = Path(template).resolve()
    slot_map_path = Path(slot_map_path).resolve()
    output = Path(output).resolve()
    slot_map = read_json(slot_map_path)
    locations_path = slot_map_path.with_name("locations.json")
    if not locations_path.exists():
        raise MappingError("locations.json must remain beside slot-map.json")
    locations = read_json(locations_path)
    expected_hash = slot_map["template"]["sha256"]
    if sha256_file(template) != expected_hash:
        raise MappingError("Template hash differs from the analyzed original")
    if template == output:
        raise MappingError("Refusing to overwrite the original template")

    mode = slot_map["template"]["mode"]
    if mode == "docx":
        if output.suffix.lower() != ".docx":
            raise MappingError("DOCX mode requires a .docx output")
        return build_docx(template, slot_map, locations, output)
    if mode == "pdf":
        if output.suffix.lower() != ".pdf":
            raise MappingError("PDF fallback mode requires a .pdf output")
        return build_pdf(template, slot_map, locations, output)
    raise MappingError(f"Unsupported slot map mode: {mode}")

