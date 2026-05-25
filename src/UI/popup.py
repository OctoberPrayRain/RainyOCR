"""popup.py
-翻译结果的展示窗口
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QFrame, QTextEdit, QVBoxLayout, QWidget

from src.UI.style import add_soft_shadow


class TranslationPopup(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RainyOCR Translation")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setObjectName("translationPopup")
        self.resize(440, 260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        card = QFrame(self)
        card.setObjectName("translationCard")
        add_soft_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 20)
        card_layout.setSpacing(10)

        self._title = QLabel("Translation")
        self._title.setObjectName("popupTitle")
        subtitle = QLabel("OCR result translated into your target language")
        subtitle.setObjectName("popupSubtitle")
        self._content = QTextEdit()
        self._content.setObjectName("translationText")
        self._content.setReadOnly(True)
        card_layout.addWidget(self._title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self._content)

        layout.addWidget(card)

    def set_text(self, text: str) -> None:
        self._content.setPlainText(text)

    def set_title(self, title: str) -> None:
        self._title.setText(title)
        self.setWindowTitle(f"RainyOCR {title}")

    def set_translation_font_size(self, font_size: int) -> None:
        font = QFont(self._content.font())
        font.setPointSize(font_size)
        self._content.setFont(font)
