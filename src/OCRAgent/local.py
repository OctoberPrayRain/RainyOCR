"""Local RapidOCR adapter for image OCR."""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Protocol

from src.utils.errors import file_not_exist_error


class _RapidOCREngine(Protocol):
    def __call__(self, img_content: str) -> object: ...


_ENGINE: _RapidOCREngine | None = None


class _TextOutput(Protocol):
    txts: tuple[str, ...] | None


def ocr(path: str) -> str:
    """Run local RapidOCR against an image path and return plain text."""
    if not os.path.exists(path):
        raise file_not_exist_error(path)

    result = _engine()(path)
    return extract_text(_result_txts(result))


def extract_text(txts: object) -> str:
    """Normalize RapidOCR text lines into RainyOCR's plain-text OCR output."""
    if txts is None:
        return ""

    if isinstance(txts, str):
        return txts.strip()

    if not isinstance(txts, Iterable):
        return ""

    lines = [line.strip() for line in txts if isinstance(line, str) and line.strip()]
    return "\n".join(lines)


def _engine() -> _RapidOCREngine:
    global _ENGINE
    engine = _ENGINE
    if engine is None:
        from rapidocr import RapidOCR

        engine = RapidOCR()
        _ENGINE = engine

    return engine


def _result_txts(result: object) -> object:
    return getattr(result, "txts", None)
