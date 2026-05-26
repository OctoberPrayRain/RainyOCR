"""tray.py
-系统托盘
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon, QWidget


logger = logging.getLogger("rainyocr.ui.tray")


class RainyTray(QObject):
    def __init__(
        self,
        parent: QWidget,
        show_main: Callable[[], None],
        show_translation: Callable[[], None],
        show_settings: Callable[[], None],
        capture_translation: Callable[[], None],
        quit_app: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        logger.info("Initializing system tray")
        self._show_main = show_main
        self._show_translation = show_translation
        self._show_settings = show_settings
        self._capture_translation = capture_translation
        self._quit_app = quit_app

        self._menu = QMenu(parent)
        self._show_main_action = QAction("Show Main Window", self)
        self._show_translation_action = QAction("Show Translation", self)
        self._settings_action = QAction("Settings", self)
        self._capture_action = QAction("Capture + Translate", self)
        self._quit_action = QAction("Quit RainyOCR", self)

        self._menu.addAction(self._show_main_action)
        self._menu.addAction(self._show_translation_action)
        self._menu.addAction(self._settings_action)
        self._menu.addSeparator()
        self._menu.addAction(self._capture_action)
        self._menu.addSeparator()
        self._menu.addAction(self._quit_action)

        self._tray = QSystemTrayIcon(self._tray_icon(), self)
        self._tray.setToolTip("RainyOCR")
        self._tray.setContextMenu(self._menu)

        self._show_main_action.triggered.connect(self._show_main)
        self._show_translation_action.triggered.connect(self._show_translation)
        self._settings_action.triggered.connect(self._show_settings)
        self._capture_action.triggered.connect(self._capture_translation)
        self._quit_action.triggered.connect(self._quit_app)
        self._tray.activated.connect(self._on_activated)

    def show(self) -> None:
        if self.is_available():
            self._tray.show()
            logger.info("System tray shown")
            return

        logger.warning("System tray is unavailable")

    def hide(self) -> None:
        logger.info("System tray hidden")
        self._tray.hide()

    def is_available(self) -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show_hidden_message(self) -> None:
        if not self.is_available():
            logger.info("Skip hidden message because tray is unavailable")
            return

        logger.info("Showing tray hidden message")
        self._tray.showMessage(
            "RainyOCR is still running",
            "Main window was hidden to tray. Use the tray icon to restore it.",
            QSystemTrayIcon.MessageIcon.Information,
            2600,
        )

    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        logger.info("Tray activated: %s", reason.name)
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self._show_main()

    def _tray_icon(self) -> QIcon:
        icon_path = (
            Path(__file__).resolve().parents[2] / "images" / "rainyocr_tray_icon.svg"
        )
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            logger.info("Loaded tray icon: %s", icon_path)
            return icon

        logger.warning("Tray icon failed to load, using system fallback: %s", icon_path)
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
