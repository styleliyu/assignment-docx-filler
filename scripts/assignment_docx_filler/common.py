from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("：", ":").replace("，", ",").replace("．", ".")
    return re.sub(r"\s+", "", value).strip()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def question_number_from_name(name: str) -> int | None:
    stem = Path(name).stem.lower()
    patterns = (
        r"^(?:q|question[-_ ]?)?(\d+)(?:[-_ ].*)?$",
        r".*?(?:q|question[-_ ]?)(\d+)(?:\D.*)?$",
    )
    for pattern in patterns:
        match = re.match(pattern, stem)
        if match:
            return int(match.group(1))
    return None

