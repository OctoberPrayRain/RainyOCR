"""OCR provider routing for RainyOCR."""

from __future__ import annotations

import os

from src.OCRAgent.openai_ocr import ocr as openai_ocr
from src.utils.get_env import get_env


_TRUTHY_VALUES = {"true", "1", "yes", "on"}
USE_LOCAL_OCR_KEY = "RainyOCR_Use_Local_OCR"


def ocr(path: str) -> str:
    """Run OCR using local RapidOCR when enabled, otherwise OpenAI-compatible OCR."""
    if use_local_ocr():
        from src.OCRAgent.local import ocr as local_ocr

        return local_ocr(path)

    return openai_ocr(path)


def use_local_ocr() -> bool:
    """Read the local OCR switch from environment or .env with a false default."""
    return _local_ocr_value().strip().lower() in _TRUTHY_VALUES


def _local_ocr_value() -> str:
    value = os.getenv(USE_LOCAL_OCR_KEY)
    if value is not None:
        return value

    try:
        return get_env(USE_LOCAL_OCR_KEY)
    except ValueError:
        return "false"
