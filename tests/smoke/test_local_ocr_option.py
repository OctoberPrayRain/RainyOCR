"""Smoke tests for the local OCR switch."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtWidgets import QApplication

from src.OCRAgent import provider
from src.OCRAgent.local import extract_text
from src.UI.settings import (
    AppSettings,
    SettingsDialog,
    USE_LOCAL_OCR_KEY,
    load_settings,
    save_settings,
)


def test_settings_load_save_bool_persistence() -> None:
    original_env = os.environ.get(USE_LOCAL_OCR_KEY)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(f'{USE_LOCAL_OCR_KEY} = "yes"\n', encoding="utf-8")
            os.environ.pop(USE_LOCAL_OCR_KEY, None)

            loaded = load_settings(env_file)
            assert loaded.use_local_ocr is True

            save_settings(AppSettings(use_local_ocr=False), env_file)
            saved_text = env_file.read_text(encoding="utf-8")
            assert f'{USE_LOCAL_OCR_KEY} = "false"' in saved_text
            assert os.environ[USE_LOCAL_OCR_KEY] == "false"

            save_settings(AppSettings(use_local_ocr=True), env_file)
            saved_text = env_file.read_text(encoding="utf-8")
            assert f'{USE_LOCAL_OCR_KEY} = "true"' in saved_text
            assert os.environ[USE_LOCAL_OCR_KEY] == "true"
    finally:
        if original_env is None:
            os.environ.pop(USE_LOCAL_OCR_KEY, None)
        else:
            os.environ[USE_LOCAL_OCR_KEY] = original_env


def test_provider_routes_by_env_without_real_ocr() -> None:
    original_env = os.environ.get(USE_LOCAL_OCR_KEY)
    original_openai_ocr = provider.openai_ocr
    calls: list[str] = []

    def fake_openai_ocr(path: str) -> str:
        calls.append(f"openai:{path}")
        return "online"

    try:
        provider.openai_ocr = fake_openai_ocr

        os.environ[USE_LOCAL_OCR_KEY] = "false"
        assert provider.ocr("image.png") == "online"
        assert calls == ["openai:image.png"]

        os.environ[USE_LOCAL_OCR_KEY] = "on"
        from src.OCRAgent import local

        original_local_ocr = local.ocr

        try:
            local.ocr = lambda path: f"local:{path}"
            assert provider.ocr("image.png") == "local:image.png"
        finally:
            local.ocr = original_local_ocr
    finally:
        provider.openai_ocr = original_openai_ocr
        if original_env is None:
            os.environ.pop(USE_LOCAL_OCR_KEY, None)
        else:
            os.environ[USE_LOCAL_OCR_KEY] = original_env


def test_local_extract_text_normalizes_rapidocr_txts() -> None:
    assert extract_text(("a", " b ", "")) == "a\nb"


def test_settings_dialog_local_toggle_masks_and_restores_online_ocr() -> None:
    _app()
    dialog = SettingsDialog()
    dialog.set_settings(
        AppSettings(
            ocr_model_name="qwen-vl",
            ocr_gateway="https://example.test/v1",
            ocr_api_key="secret",
            use_local_ocr=False,
        ),
    )

    dialog._use_local_ocr_input.setChecked(True)
    assert dialog._ocr_model_input.text() == "Local"
    assert dialog._ocr_gateway_input.text() == ""
    assert dialog._ocr_api_key_input.text() == ""
    assert dialog._ocr_model_input.isEnabled() is False
    assert dialog._ocr_gateway_input.isEnabled() is False
    assert dialog._ocr_api_key_input.isEnabled() is False
    assert dialog.settings().ocr_model_name == "qwen-vl"
    assert dialog.settings().ocr_gateway == "https://example.test/v1"
    assert dialog.settings().ocr_api_key == "secret"
    assert dialog.settings().use_local_ocr is True

    dialog._use_local_ocr_input.setChecked(False)
    assert dialog._ocr_model_input.text() == "qwen-vl"
    assert dialog._ocr_gateway_input.text() == "https://example.test/v1"
    assert dialog._ocr_api_key_input.text() == "secret"
    assert dialog._ocr_model_input.isEnabled() is True
    assert dialog._ocr_gateway_input.isEnabled() is True
    assert dialog._ocr_api_key_input.isEnabled() is True


def test_settings_dialog_local_initial_state_unchecks_to_saved_ocr_values() -> None:
    _app()
    dialog = SettingsDialog()
    dialog.set_settings(
        AppSettings(
            ocr_model_name="saved-model",
            ocr_gateway="https://saved.example/v1",
            ocr_api_key="saved-key",
            use_local_ocr=True,
        ),
    )

    assert dialog._ocr_model_input.text() == "Local"
    assert dialog._ocr_gateway_input.text() == ""
    assert dialog._ocr_api_key_input.text() == ""

    dialog._use_local_ocr_input.setChecked(False)
    assert dialog._ocr_model_input.text() == "saved-model"
    assert dialog._ocr_gateway_input.text() == "https://saved.example/v1"
    assert dialog._ocr_api_key_input.text() == "saved-key"


def test_settings_dialog_uncheck_falls_back_to_saved_ocr_values() -> None:
    _app()
    dialog = SettingsDialog()
    dialog.set_settings(AppSettings(use_local_ocr=True))
    dialog._online_ocr_model_name = ""
    dialog._online_ocr_gateway = ""
    dialog._online_ocr_api_key = ""

    saved_settings = AppSettings(
        ocr_model_name="env-model",
        ocr_gateway="https://env.example/v1",
        ocr_api_key="env-key",
        use_local_ocr=True,
    )
    with patch("src.UI.settings.load_settings", return_value=saved_settings):
        dialog._use_local_ocr_input.setChecked(False)

    assert dialog._ocr_model_input.text() == "env-model"
    assert dialog._ocr_gateway_input.text() == "https://env.example/v1"
    assert dialog._ocr_api_key_input.text() == "env-key"


def _app() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app

    return QApplication([])


if __name__ == "__main__":
    test_settings_load_save_bool_persistence()
    test_provider_routes_by_env_without_real_ocr()
    test_local_extract_text_normalizes_rapidocr_txts()
    test_settings_dialog_local_toggle_masks_and_restores_online_ocr()
    test_settings_dialog_local_initial_state_unchecks_to_saved_ocr_values()
    test_settings_dialog_uncheck_falls_back_to_saved_ocr_values()
    print("local OCR option smoke tests passed")
