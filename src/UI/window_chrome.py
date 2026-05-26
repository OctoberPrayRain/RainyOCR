"""Shared frameless window helpers for RainyOCR UI windows."""

from __future__ import annotations

import sys
import logging

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QKeySequenceEdit,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QWidget,
)


logger = logging.getLogger("rainyocr.ui.window_chrome")


INTERACTIVE_WIDGETS = (
    QPushButton,
    QTextEdit,
    QLineEdit,
    QSpinBox,
    QKeySequenceEdit,
    QDialogButtonBox,
)


def enable_translucent_frameless_window(widget: QWidget) -> None:
    """Use custom chrome while keeping rounded card edges transparent."""

    if is_macos():
        logger.info(
            "Skipping translucent frameless window on macOS for %s",
            widget.__class__.__name__,
        )
        return

    logger.info(
        "Enabling translucent frameless window for %s",
        widget.__class__.__name__,
    )
    widget.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)


def is_macos() -> bool:
    return sys.platform == "darwin"


class WindowDragController:
    """Move a frameless window by dragging non-interactive surface areas."""

    def __init__(self, window: QWidget) -> None:
        self._window = window
        self._drag_offset: QPoint | None = None

    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        if self._event_targets_interactive_widget(event):
            return False

        self._drag_offset = (
            event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
        )
        event.accept()
        return True

    def handle_mouse_move(self, event: QMouseEvent) -> bool:
        if self._drag_offset is None:
            return False
        if not event.buttons() & Qt.MouseButton.LeftButton:
            return False

        self._window.move(event.globalPosition().toPoint() - self._drag_offset)
        event.accept()
        return True

    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        if self._drag_offset is None:
            return False

        self._drag_offset = None
        event.accept()
        return True

    def _event_targets_interactive_widget(self, event: QMouseEvent) -> bool:
        child = self._window.childAt(event.position().toPoint())
        while child is not None:
            if isinstance(child, INTERACTIVE_WIDGETS):
                return True
            child = child.parentWidget()

        return False
