"""app.py
-前端UI的主程序接口
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.UI.controller import UIController
from src.UI.popup import TranslationPopup

try:
    from pynput import keyboard
except ImportError:
    keyboard = None


class GlobalHotkeyListener(QObject):
    triggered = Signal()
    status_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._listener = None

    def start(self) -> None:
        if keyboard is None:
            self.status_changed.emit(
                "Global hotkey unavailable, using app shortcut only"
            )
            return

        self._listener = keyboard.GlobalHotKeys(
            {
                "<ctrl>+<shift>+t": self.triggered.emit,
            }
        )
        self._listener.start()
        self.status_changed.emit("Global hotkey active: Ctrl+Shift+T")

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RainyOCR")
        self.resize(420, 220)

        self._popup = TranslationPopup()
        self._controller = UIController(self._popup)
        self._global_hotkey = GlobalHotkeyListener()

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        self._status_label = QLabel("Ready. Step 1: Select Region")
        self._status_label.setWordWrap(True)

        self._select_button = QPushButton("Select Region")
        self._trigger_button = QPushButton("Capture + Translate")
        self._shortcut_hint = QLabel("Shortcut: Ctrl+Shift+T")
        self._shortcut_hint.setAlignment(Qt.AlignRight)

        layout.addWidget(self._status_label)
        layout.addWidget(self._select_button)
        layout.addWidget(self._trigger_button)
        layout.addWidget(self._shortcut_hint)

        self.setCentralWidget(central)

        self._select_button.clicked.connect(self._controller.start_region_selection)
        self._trigger_button.clicked.connect(
            self._controller.trigger_capture_and_translate
        )
        self._controller.status_changed.connect(self._set_status)

        self._shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        self._shortcut.activated.connect(self._controller.trigger_capture_and_translate)

        self._global_hotkey.triggered.connect(
            self._controller.trigger_capture_and_translate,
        )
        self._global_hotkey.status_changed.connect(self._set_status)
        self._global_hotkey.start()

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)

    def closeEvent(self, event) -> None:
        self._global_hotkey.stop()
        self._controller.shutdown()
        super().closeEvent(event)


def run() -> int:
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(run())
