from __future__ import annotations

from typing import Any, Dict, Optional


def _stringify(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def extract_document_metadata(doc, file_name: Optional[str], file_size_bytes: Optional[int], mime_type: Optional[str]) -> Dict[str, Any]:
    core = getattr(doc, "core_properties", None)
    return {
        "file_name": file_name,
        "file_size_bytes": file_size_bytes,
        "mime_type": mime_type,
        "created": getattr(core, "created", None).isoformat() if getattr(core, "created", None) else None,
        "modified": getattr(core, "modified", None).isoformat() if getattr(core, "modified", None) else None,
        "author": _stringify(getattr(core, "author", None)),
        "title": _stringify(getattr(core, "title", None)),
        "subject": _stringify(getattr(core, "subject", None)),
        "category": _stringify(getattr(core, "category", None)),
        "language": _stringify(getattr(core, "language", None)),
        "revision": _stringify(getattr(core, "revision", None)),
        "version": _stringify(getattr(core, "version", None)),
        "source_format": "docx" if (file_name or "").lower().endswith(".docx") else "doc",
    }
