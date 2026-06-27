from __future__ import annotations

import copy
import locale
import mimetypes
import os
import re
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree
from PIL import Image

from .analyze import NS, PLACEHOLDERS, W_NS, W_TAG
from .common import normalize_text
from .errors import MappingError, UnsafeTemplateError

R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
XML_NS = "http://www.w3.org/XML/1998/namespace"
EMU_PER_TWIP = 635


def _paragraph_text(element: etree._Element) -> str:
    return "".join(element.itertext())


def _replaceable(text: str) -> bool:
    value = normalize_text(text).strip("()（）[]【】")
    return not value or value in PLACEHOLDERS


def _clear_paragraph(paragraph: etree._Element) -> None:
    for child in list(paragraph):
        if child.tag != W_TAG + "pPr":
            paragraph.remove(child)


def _new_paragraph_like(anchor: etree._Element) -> etree._Element:
    paragraph = etree.Element(W_TAG + "p", nsmap=anchor.nsmap)
    properties = anchor.find("w:pPr", NS)
    if properties is not None:
        paragraph.append(copy.deepcopy(properties))
    return paragraph


def _read_answer(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        encoding = locale.getpreferredencoding(False)
        return path.read_text(encoding=encoding)


def _append_code(paragraph: etree._Element, code: str) -> None:
    run = etree.SubElement(paragraph, W_TAG + "r")
    paragraph_style = paragraph.find("w:pPr/w:pStyle", NS)
    if paragraph_style is None:
        run_properties = etree.SubElement(run, W_TAG + "rPr")
        fonts = etree.SubElement(run_properties, W_TAG + "rFonts")
        for attribute in ("ascii", "hAnsi", "eastAsia"):
            fonts.set(W_TAG + attribute, "Consolas")
    lines = code.rstrip("\r\n").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for index, line in enumerate(lines):
        if index:
            etree.SubElement(run, W_TAG + "br")
        text = etree.SubElement(run, W_TAG + "t")
        if line.startswith(" ") or line.endswith(" "):
            text.set(f"{{{XML_NS}}}space", "preserve")
        text.text = line


def _next_relationship_id(relationships: etree._Element) -> str:
    numbers = []
    for relationship in relationships:
        match = re.fullmatch(r"rId(\d+)", relationship.get("Id", ""))
        if match:
            numbers.append(int(match.group(1)))
    return f"rId{max(numbers, default=0) + 1}"


def _next_media_name(existing_names: set[str], suffix: str) -> str:
    index = 1
    while f"word/media/assignment-image-{index}{suffix}" in existing_names:
        index += 1
    return f"word/media/assignment-image-{index}{suffix}"


def _ensure_content_type(content_types: etree._Element, suffix: str) -> None:
    extension = suffix.lstrip(".").lower()
    existing = content_types.xpath(
        "./ct:Default[translate(@Extension, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')=$extension]",
        namespaces={"ct": CT_NS},
        extension=extension,
    )
    if existing:
        return
    mime = mimetypes.types_map.get(suffix.lower(), "image/jpeg")
    default = etree.SubElement(content_types, f"{{{CT_NS}}}Default")
    default.set("Extension", extension)
    default.set("ContentType", mime)


def _text_width_emu(root: etree._Element) -> int:
    section = root.find(".//w:body/w:sectPr", NS)
    if section is None:
        section = root.find(".//w:pPr/w:sectPr", NS)
    page_width = 12240
    left = right = 1440
    if section is not None:
        page_size = section.find("w:pgSz", NS)
        margins = section.find("w:pgMar", NS)
        if page_size is not None:
            page_width = int(page_size.get(W_TAG + "w", page_width))
        if margins is not None:
            left = int(margins.get(W_TAG + "left", left))
            right = int(margins.get(W_TAG + "right", right))
    return max(1440, page_width - left - right) * EMU_PER_TWIP


def _image_extent(path: Path, max_width: int) -> tuple[int, int]:
    with Image.open(path) as image:
        width_px, height_px = image.size
        dpi_x, dpi_y = image.info.get("dpi", (96, 96))
    width = int(width_px / max(float(dpi_x), 1.0) * 914400)
    height = int(height_px / max(float(dpi_y), 1.0) * 914400)
    if width > max_width:
        scale = max_width / width
        width = max_width
        height = int(height * scale)
    return max(width, 1), max(height, 1)


def _drawing(relationship_id: str, name: str, width: int, height: int, doc_pr_id: int) -> etree._Element:
    xml = f"""
    <w:drawing xmlns:w="{W_NS}" xmlns:r="{R_NS}"
      xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
      <wp:inline distT="0" distB="0" distL="0" distR="0">
        <wp:extent cx="{width}" cy="{height}"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:docPr id="{doc_pr_id}" name="{name}"/>
        <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
        <a:graphic>
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic>
              <pic:nvPicPr><pic:cNvPr id="0" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>
              <pic:blipFill><a:blip r:embed="{relationship_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
              <pic:spPr>
                <a:xfrm><a:off x="0" y="0"/><a:ext cx="{width}" cy="{height}"/></a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
    """
    return etree.fromstring(xml.encode("utf-8"))


def _append_images(
    paragraph: etree._Element,
    image_paths: list[Path],
    document_root: etree._Element,
    relationships: etree._Element,
    content_types: etree._Element,
    package_parts: dict[str, bytes],
) -> None:
    max_width = _text_width_emu(document_root)
    existing_names = set(package_parts)
    doc_pr_ids = [
        int(value)
        for value in document_root.xpath(".//wp:docPr/@id", namespaces={"wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"})
        if str(value).isdigit()
    ]
    doc_pr_id = max(doc_pr_ids, default=0) + 1
    for index, image_path in enumerate(image_paths):
        suffix = image_path.suffix.lower()
        media_name = _next_media_name(existing_names, suffix)
        existing_names.add(media_name)
        package_parts[media_name] = image_path.read_bytes()
        relationship_id = _next_relationship_id(relationships)
        relationship = etree.SubElement(relationships, f"{{{REL_NS}}}Relationship")
        relationship.set("Id", relationship_id)
        relationship.set(
            "Type",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
        )
        relationship.set("Target", f"media/{Path(media_name).name}")
        _ensure_content_type(content_types, suffix)
        width, height = _image_extent(image_path, max_width)
        run = etree.SubElement(paragraph, W_TAG + "r")
        run.append(_drawing(relationship_id, image_path.name, width, height, doc_pr_id))
        doc_pr_id += 1
        if index + 1 < len(image_paths):
            etree.SubElement(run, W_TAG + "br")


def build_docx(
    template: Path,
    slot_map: dict[str, Any],
    locations: dict[str, Any],
    output: Path,
) -> Path:
    with zipfile.ZipFile(template) as package:
        infos = {info.filename: info for info in package.infolist()}
        parts = {info.filename: package.read(info.filename) for info in package.infolist()}

    try:
        root = etree.fromstring(parts["word/document.xml"])
        relationships = etree.fromstring(parts["word/_rels/document.xml.rels"])
        content_types = etree.fromstring(parts["[Content_Types].xml"])
    except (KeyError, etree.XMLSyntaxError) as error:
        raise MappingError(f"Invalid DOCX package: {error}") from error
    body = root.find("w:body", NS)
    if body is None:
        raise MappingError("DOCX document body is missing")

    edits: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    for question in slot_map["questions"]:
        for slot in question["slots"]:
            has_material = bool(slot.get("source") or slot.get("sources"))
            if not has_material:
                continue
            if slot["status"] != "confirmed":
                raise UnsafeTemplateError(f"Slot {slot['id']} is not confirmed")
            location = locations["slots"].get(slot["id"])
            if not location:
                raise MappingError(f"Missing private location for {slot['id']}")
            edits.append((int(location["body_start"]), slot, location))

    for _, slot, location in sorted(edits, key=lambda item: item[0], reverse=True):
        children = list(body)
        anchor_index = int(location["anchor_body_index"])
        start = int(location["body_start"])
        end = int(location["body_end"])
        if anchor_index >= len(children) or start > len(children):
            raise MappingError(f"Stale location for {slot['id']}")
        anchor = children[anchor_index]
        region = children[start:end]
        paragraphs = [element for element in region if element.tag == W_TAG + "p"]
        unsupported = [element for element in region if element.tag != W_TAG + "p"]
        if unsupported:
            raise UnsafeTemplateError(f"Slot {slot['id']} contains an unsupported structure")
        nonreplaceable = [
            _paragraph_text(paragraph)
            for paragraph in paragraphs
            if not _replaceable(_paragraph_text(paragraph))
        ]
        if nonreplaceable and not slot.get("allow_nonempty_region"):
            raise UnsafeTemplateError(f"Slot {slot['id']} contains teacher content")

        if paragraphs:
            target = paragraphs[0]
            _clear_paragraph(target)
            for extra in paragraphs[1:]:
                body.remove(extra)
        else:
            target = _new_paragraph_like(anchor)
            insert_before = children[end] if end < len(children) else None
            if insert_before is None:
                body.append(target)
            else:
                insert_before.addprevious(target)

        if slot["kind"] == "code":
            source = Path(slot["source"])
            _append_code(target, _read_answer(source))
        else:
            image_paths = [Path(path) for path in slot.get("sources", [])]
            _append_images(target, image_paths, root, relationships, content_types, parts)

    parts["word/document.xml"] = etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    parts["word/_rels/document.xml.rels"] = etree.tostring(
        relationships, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    parts["[Content_Types].xml"] = etree.tostring(
        content_types, xml_declaration=True, encoding="UTF-8", standalone=True
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w") as package:
        for name, data in parts.items():
            info = infos.get(name)
            if info is None:
                package.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
            else:
                package.writestr(info, data)
    os.replace(temporary, output)
    return output
