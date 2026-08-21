"""Settings dialog and persistence helpers for RainyOCR."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QLineEdit,
    QKeySequenceEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

DEFAULT_TRANSLATION_FONT_SIZE = 15
DEFAULT_CAPTURE_SHORTCUT = "Ctrl+Shift+T"

OCR_MODEL_NAME_KEY = "OpenAI_OCR_Model_Name"
OCR_API_KEY_KEY = "OpenAI_OCR_Secret_Key"
OCR_GATEWAY_KEY = "OpenAI_OCR_Node"
USE_LOCAL_OCR_KEY = "RainyOCR_Use_Local_OCR"
TRANSLATE_MODEL_NAME_KEY = "OpenAI_Translate_Model_Name"
TRANSLATE_API_KEY_KEY = "OpenAI_Translate_Secret_Key"
TRANSLATE_GATEWAY_KEY = "OpenAI_Translate_Node"
TRANSLATION_FONT_SIZE_KEY = "RainyOCR_Translation_Font_Size"
CAPTURE_SHORTCUT_KEY = "RainyOCR_Capture_Shortcut"


@dataclass(frozen=True)
class AppSettings:
    ocr_model_name: str = ""
    ocr_api_key: str = ""
    ocr_gateway: str = ""
    use_local_ocr: bool = False
    translate_model_name: str = ""
    translate_api_key: str = ""
    translate_gateway: str = ""
    translation_font_size: int = DEFAULT_TRANSLATION_FONT_SIZE
    capture_shortcut: str = DEFAULT_CAPTURE_SHORTCUT


def load_settings(path: Path | None = None) -> AppSettings:
    values = _read_env_values(path or _env_path())

    return AppSettings(
        ocr_model_name=_setting_value(values, OCR_MODEL_NAME_KEY),
        ocr_api_key=_setting_value(values, OCR_API_KEY_KEY),
        ocr_gateway=_setting_value(values, OCR_GATEWAY_KEY),
        use_local_ocr=_bool_value(_setting_value(values, USE_LOCAL_OCR_KEY)),
        translate_model_name=_setting_value(values, TRANSLATE_MODEL_NAME_KEY),
        translate_api_key=_setting_value(values, TRANSLATE_API_KEY_KEY),
        translate_gateway=_setting_value(values, TRANSLATE_GATEWAY_KEY),
        translation_font_size=_font_size_value(
            _setting_value(values, TRANSLATION_FONT_SIZE_KEY),
        ),
        capture_shortcut=_shortcut_value(_setting_value(values, CAPTURE_SHORTCUT_KEY)),
    )


def save_settings(settings: AppSettings, path: Path | None = None) -> None:
    target = path or _env_path()
    values = {
        TRANSLATE_MODEL_NAME_KEY: settings.translate_model_name,
        TRANSLATE_API_KEY_KEY: settings.translate_api_key,
        TRANSLATE_GATEWAY_KEY: settings.translate_gateway,
        OCR_MODEL_NAME_KEY: settings.ocr_model_name,
        OCR_API_KEY_KEY: settings.ocr_api_key,
        OCR_GATEWAY_KEY: settings.ocr_gateway,
        USE_LOCAL_OCR_KEY: _bool_env_value(settings.use_local_ocr),
        TRANSLATION_FONT_SIZE_KEY: str(settings.translation_font_size),
        CAPTURE_SHORTCUT_KEY: settings.capture_shortcut,
    }

    _write_env_values(target, values, _legacy_openai_key_names())
    os.environ.update(values)


class SettingsDialog(QDialog):
    settings_saved = Signal(AppSettings)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("RainyOCR Settings")
        self.setModal(True)
        self.resize(560, 600)

        self._ocr_model_input = QLineEdit()
        self._ocr_gateway_input = QLineEdit()
        self._ocr_api_key_input = self._secret_input()
        self._use_local_ocr_input = QCheckBox("Use local RapidOCR for OCR")
        self._online_ocr_model_name = ""
        self._online_ocr_gateway = ""
        self._online_ocr_api_key = ""
        self._translate_model_input = QLineEdit()
        self._translate_gateway_input = QLineEdit()
        self._translate_api_key_input = self._secret_input()
        self._font_size_input = QSpinBox()
        self._font_size_input.setRange(10, 32)
        self._font_size_input.setSuffix(" px")
        self._font_size_input.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self._shortcut_input = QKeySequenceEdit()

        self._build_ui()
        self.set_settings(load_settings())

    def set_settings(self, settings: AppSettings) -> None:
        self._ocr_model_input.setText(settings.ocr_model_name)
        self._ocr_gateway_input.setText(settings.ocr_gateway)
        self._ocr_api_key_input.setText(settings.ocr_api_key)
        self._remember_online_ocr_fields(settings)
        self._use_local_ocr_input.setChecked(settings.use_local_ocr)
        self._apply_local_ocr_state(settings.use_local_ocr, remember_current=False)
        self._translate_model_input.setText(settings.translate_model_name)
        self._translate_gateway_input.setText(settings.translate_gateway)
        self._translate_api_key_input.setText(settings.translate_api_key)
        self._font_size_input.setValue(settings.translation_font_size)
        self._shortcut_input.setKeySequence(QKeySequence(settings.capture_shortcut))

    def settings(self) -> AppSettings:
        ocr_model_name = self._ocr_model_input.text().strip()
        ocr_api_key = self._ocr_api_key_input.text().strip()
        ocr_gateway = self._ocr_gateway_input.text().strip()
        if self._use_local_ocr_input.isChecked():
            ocr_model_name = self._online_ocr_model_name
            ocr_api_key = self._online_ocr_api_key
            ocr_gateway = self._online_ocr_gateway

        return AppSettings(
            ocr_model_name=ocr_model_name,
            ocr_api_key=ocr_api_key,
            ocr_gateway=ocr_gateway,
            use_local_ocr=self._use_local_ocr_input.isChecked(),
            translate_model_name=self._translate_model_input.text().strip(),
            translate_api_key=self._translate_api_key_input.text().strip(),
            translate_gateway=self._translate_gateway_input.text().strip(),
            translation_font_size=self._font_size_input.value(),
            capture_shortcut=self._shortcut_text(),
        )

    def accept(self) -> None:
        settings = self.settings()
        save_settings(settings)
        self.settings_saved.emit(settings)
        super().accept()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        card = QFrame(self)
        card.setObjectName("settingsCard")
        self._apply_card_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 22)
        card_layout.setSpacing(14)

        title = QLabel("Model Settings")
        title.setObjectName("settingsTitle")
        close_button = QPushButton("×")
        close_button.setObjectName("windowCloseButton")
        close_button.setToolTip("Close")
        close_button.setFixedSize(42, 42)
        close_button.clicked.connect(self.reject)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(close_button)
        subtitle = QLabel(
            "Configure OpenAI-compatible endpoints for OCR and translation. "
            "Saved changes apply to the next capture."
        )
        subtitle.setObjectName("settingsSubtitle")
        subtitle.setWordWrap(True)

        card_layout.addLayout(title_row)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(
            self._settings_group(
                "OCR Model",
                [
                    ("Model name", self._ocr_model_row()),
                    ("Gateway URL", self._ocr_gateway_input),
                    ("API Key", self._secret_row(self._ocr_api_key_input)),
                ],
            ),
        )
        card_layout.addWidget(
            self._settings_group(
                "Translate Model",
                [
                    ("Model name", self._translate_model_input),
                    ("Gateway URL", self._translate_gateway_input),
                    ("API Key", self._secret_row(self._translate_api_key_input)),
                ],
            ),
        )
        card_layout.addWidget(
            self._settings_group(
                "Display",
                [("Translation font size", self._font_size_row())],
            ),
        )
        card_layout.addWidget(
            self._settings_group(
                "Shortcut",
                [("Capture shortcut", self._shortcut_row())],
            ),
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        card_layout.addWidget(buttons)
        layout.addWidget(card)

    def _settings_group(
        self,
        title: str,
        rows: list[tuple[str, QWidget]],
    ) -> QGroupBox:
        group = QGroupBox(title)
        group.setObjectName("settingsGroup")
        form = QFormLayout(group)
        form.setContentsMargins(18, 20, 18, 18)
        form.setSpacing(12)
        for label, widget in rows:
            form.addRow(label, widget)

        return group

    def _secret_input(self) -> QLineEdit:
        input_widget = QLineEdit()
        input_widget.setEchoMode(QLineEdit.EchoMode.Password)
        return input_widget

    def _font_size_row(self) -> QWidget:
        row = QWidget()
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        hint = QLabel("Maximum font size is 32px.")
        hint.setObjectName("settingsHint")
        layout.addWidget(self._font_size_input)
        layout.addWidget(hint)

        return row

    def _ocr_model_row(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._use_local_ocr_input.setToolTip(
            "When enabled, OCR runs locally with RapidOCR; translation still uses the online translate model.",
        )
        self._use_local_ocr_input.toggled.connect(
            lambda enabled: self._apply_local_ocr_state(enabled),
        )
        layout.addWidget(self._ocr_model_input)
        layout.addWidget(self._use_local_ocr_input)

        return row

    def _remember_online_ocr_fields(self, settings: AppSettings | None = None) -> None:
        if settings is not None:
            self._online_ocr_model_name = settings.ocr_model_name
            self._online_ocr_gateway = settings.ocr_gateway
            self._online_ocr_api_key = settings.ocr_api_key
            return

        self._online_ocr_model_name = self._ocr_model_input.text().strip()
        self._online_ocr_gateway = self._ocr_gateway_input.text().strip()
        self._online_ocr_api_key = self._ocr_api_key_input.text().strip()

    def _apply_local_ocr_state(
        self,
        enabled: bool,
        remember_current: bool = True,
    ) -> None:
        if enabled:
            if remember_current:
                self._remember_online_ocr_fields()
            self._ocr_model_input.setText("Local")
            self._ocr_gateway_input.clear()
            self._ocr_api_key_input.clear()
        else:
            self._restore_online_ocr_fields_from_saved_settings_if_empty()
            self._ocr_model_input.setText(self._online_ocr_model_name)
            self._ocr_gateway_input.setText(self._online_ocr_gateway)
            self._ocr_api_key_input.setText(self._online_ocr_api_key)

        for input_widget in (
            self._ocr_model_input,
            self._ocr_gateway_input,
            self._ocr_api_key_input,
        ):
            input_widget.setEnabled(not enabled)

    def _restore_online_ocr_fields_from_saved_settings_if_empty(self) -> None:
        if (
            self._online_ocr_model_name
            or self._online_ocr_gateway
            or self._online_ocr_api_key
        ):
            return

        settings = load_settings()
        self._remember_online_ocr_fields(settings)

    def _apply_card_shadow(self, card: QFrame) -> None:
        style = QApplication.style()
        if style is not None:
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card.setFrameShadow(QFrame.Shadow.Raised)
            card.setLineWidth(style.pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth))

    def _shortcut_row(self) -> QWidget:
        row = QWidget()
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        hint = QLabel("Used for both the app shortcut and the global hotkey.")
        hint.setObjectName("settingsHint")
        layout.addWidget(self._shortcut_input)
        layout.addWidget(hint)

        return row

    def _shortcut_text(self) -> str:
        text = self._shortcut_input.keySequence().toString(
            QKeySequence.SequenceFormat.PortableText,
        )
        return _shortcut_value(text)

    def _secret_row(self, input_widget: QLineEdit) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        toggle = QPushButton("Show")
        toggle.setObjectName("secondaryButton")
        toggle.setCheckable(True)
        toggle.toggled.connect(
            lambda checked: self._toggle_secret(input_widget, toggle, checked),
        )
        layout.addWidget(input_widget)
        layout.addWidget(toggle)
        return row

    def _toggle_secret(
        self,
        input_widget: QLineEdit,
        toggle: QPushButton,
        checked: bool,
    ) -> None:
        if checked:
            input_widget.setEchoMode(QLineEdit.EchoMode.Normal)
            toggle.setText("Hide")
            return

        input_widget.setEchoMode(QLineEdit.EchoMode.Password)
        toggle.setText("Show")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)


def _setting_value(values: dict[str, str], key: str) -> str:
    return os.getenv(key) or values.get(key, "")


def _font_size_value(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        return DEFAULT_TRANSLATION_FONT_SIZE

    return min(max(parsed, 10), 32)


def _bool_value(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "on"}


def _bool_env_value(value: bool) -> str:
    return "true" if value else "false"


def _shortcut_value(value: str) -> str:
    shortcut = value.split(",", 1)[0].strip()
    if not shortcut:
        return DEFAULT_CAPTURE_SHORTCUT

    return shortcut


def _read_env_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = _parse_env_line(line)
        if key:
            values[key] = value

    return values


def _env_path() -> Path:
    return Path.cwd() / ".env"


def _legacy_openai_key_names() -> set[str]:
    old_prefix = "Google_"
    return {
        f"{old_prefix}Translate_Model_Name",
        f"{old_prefix}Translate_Secret_Key",
        f"{old_prefix}Translate_Node",
        f"{old_prefix}OCR_Model_Name",
        f"{old_prefix}OCR_Secret_Key",
        f"{old_prefix}OCR_Node",
    }


def _write_env_values(
    path: Path,
    values: dict[str, str],
    removed_keys: set[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    removed_keys = removed_keys or set()
    updated_keys: set[str] = set()
    next_lines: list[str] = []

    for line in lines:
        key, _ = _parse_env_line(line)
        if key in values:
            next_lines.append(f'{key} = "{_escape_env_value(values[key])}"')
            updated_keys.add(key)
        elif key in removed_keys:
            continue
        else:
            next_lines.append(line)

    for key, value in values.items():
        if key not in updated_keys:
            next_lines.append(f'{key} = "{_escape_env_value(value)}"')

    path.write_text("\n".join(next_lines) + "\n", encoding="utf-8")


def _parse_env_line(line: str) -> tuple[str, str]:
    if "=" not in line:
        return "", ""

    key, raw_value = line.split("=", 1)
    key = key.strip()
    if not key or key.startswith("#"):
        return "", ""

    return key, _unquote_env_value(raw_value.strip())


def _unquote_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]

    return value.replace('\\"', '"').replace("\\'", "'").replace("\\\\", "\\")


def _escape_env_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
