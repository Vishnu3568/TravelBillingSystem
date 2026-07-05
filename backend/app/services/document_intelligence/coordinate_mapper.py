from __future__ import annotations

from typing import Optional


def build_source_path(*parts: object) -> str:
    cleaned = [str(part) for part in parts if part is not None and str(part) != ""]
    return "/".join(cleaned)


def make_node_id(prefix: str, page_number: int, position: int, extra: Optional[str] = None) -> str:
    if extra:
        return f"{prefix}-p{page_number}-{position}-{extra}"
    return f"{prefix}-p{page_number}-{position}"


def make_coordinate_id(object_type: str, source_id: str) -> str:
    return f"coord-{object_type}-{source_id}"
