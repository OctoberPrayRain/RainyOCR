"""popup.py
-翻译结果的展示窗口
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.UI.style import add_soft_shadow
from src.UI.window_chrome import (
    WindowDragController,
    enable_translucent_frameless_window,
    is_macos,
)


logger = logging.getLogger("rainyocr.ui.popup")


class TranslationPopup(QWidget):
    def __init__(self) -> None:
        super().__init__()
        logger.info("Initializing translation popup; macOS=%s", is_macos())
        self.setWindowTitle("RainyOCR Translation")
        window_flags = Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        if not is_macos():
            window_flags |= Qt.WindowType.FramelessWindowHint

        self.setWindowFlags(window_flags)
        logger.info("Translation popup window flags set: %s", int(window_flags))
        enable_translucent_frameless_window(self)
        self.setObjectName("translationPopup")
        self.resize(440, 260)
        self._drag_controller = WindowDragController(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        card = QFrame(self)
        card.setObjectName("translationCard")
        add_soft_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 20)
        card_layout.setSpacing(10)

        self._title = QLabel("Translation")
        self._title.setObjectName("popupTitle")
        self._close_button = QPushButton("×")
        self._close_button.setObjectName("windowCloseButton")
        self._close_button.setToolTip("Close")
        self._close_button.setFixedSize(42, 42)
        self._close_button.clicked.connect(self.close)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.addWidget(self._title)
        title_row.addStretch()
        title_row.addWidget(self._close_button)
        subtitle = QLabel("OCR result translated into your target language")
        subtitle.setObjectName("popupSubtitle")
        self._content = QTextEdit()
        self._content.setObjectName("translationText")
        self._content.setReadOnly(True)
        card_layout.addLayout(title_row)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self._content)

        layout.addWidget(card)

    def set_text(self, text: str) -> None:
        logger.info("Translation popup text updated; length=%s", len(text))
        self._content.setPlainText(text)

    def set_title(self, title: str) -> None:
        logger.info("Translation popup title updated: %s", title)
        self._title.setText(title)
        self.setWindowTitle(f"RainyOCR {title}")

    def set_translation_font_size(self, font_size: int) -> None:
        logger.info("Translation popup font size updated: %s", font_size)
        font = QFont(self._content.font())
        font.setPointSize(font_size)
        self._content.setFont(font)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._drag_controller.handle_mouse_press(event):
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_controller.handle_mouse_move(event):
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._drag_controller.handle_mouse_release(event):
            return

        super().mouseReleaseEvent(event)
