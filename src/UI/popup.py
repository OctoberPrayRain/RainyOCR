"""popup.py
-翻译结果的展示窗口
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class TranslationPopup(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RainyOCR Translation")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.resize(420, 240)

        layout = QVBoxLayout(self)
        title = QLabel("Translation")
        self._content = QTextEdit()
        self._content.setReadOnly(True)
        layout.addWidget(title)
        layout.addWidget(self._content)

    def set_text(self, text: str) -> None:
        self._content.setPlainText(text)
